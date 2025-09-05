// pybind_module.cpp
// Full pybind11 bindings for duvc-ctl
// Hardened for MSVC / pybind11 usage on Windows (avoids macro collisions, careful
// py::buffer/py::object conversions, and provides python-friendly Result wrappers).


#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>
#include <pybind11/numpy.h>
#include <pybind11/iostream.h>

#include <vector>
#include <string>
#include <sstream>
#include <mutex>
#include <atomic>
#include <memory>
#include <cstring>
#include <stdexcept>
#include <cctype>
#include <algorithm>
#include <iomanip>

#ifdef _WIN32
// Minimize footprint and avoid NOMINMAX collisions
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif

#include <windows.h>
#include <objbase.h>
#include <guiddef.h>
#include <combaseapi.h>

// Avoid macro collisions with Windows headers (DeviceCapabilitiesW etc.)
#ifdef DeviceCapabilities
#undef DeviceCapabilities
#endif
#ifdef DeviceCapabilitiesW
#undef DeviceCapabilitiesW
#endif

#endif // _WIN32

#include "duvc-ctl/duvc.hpp"            // umbrella C++ header (types & functions)
#ifdef _WIN32
#include "duvc-ctl/platform/windows/ks_properties.h"
#include "duvc-ctl/platform/windows/connection_pool.h"
#include "duvc-ctl/platform/windows/directshow.h"
#endif

namespace py = pybind11;
using namespace std;    
using namespace duvc;   

#ifdef _WIN32
using duvc::Device; // for clarity in some places below where duvc:: is used heavily
#endif

// -----------------------------------------------------------------------------
// Utilities
// -----------------------------------------------------------------------------
// Lightweight UTF8 <-> wstring helpers (windows usage)
static std::string wstring_to_utf8(const std::wstring &w) {
#ifdef _WIN32
    if (w.empty()) return {};
    int n = ::WideCharToMultiByte(CP_UTF8, 0, w.data(), (int)w.size(), nullptr, 0, nullptr, nullptr);
    if (n <= 0) return {};
    std::string s(n, '\0');
    ::WideCharToMultiByte(CP_UTF8, 0, w.data(), (int)w.size(), &s[0], n, nullptr, nullptr);
    return s;
#else
    std::string s;
    s.reserve(w.size());
    for (wchar_t wc : w) s.push_back(static_cast<char>(wc & 0xFF));
    return s;
#endif
}

static std::wstring utf8_to_wstring(const std::string &s) {
#ifdef _WIN32
    if (s.empty()) return {};
    int n = ::MultiByteToWideChar(CP_UTF8, 0, s.data(), (int)s.size(), nullptr, 0);
    if (n <= 0) return {};
    std::wstring w(n, L'\0');
    ::MultiByteToWideChar(CP_UTF8, 0, s.data(), (int)s.size(), &w[0], n);
    return w;
#else
    std::wstring w;
    w.reserve(s.size());
    for (char c : s) w.push_back(static_cast<wchar_t>(c));
    return w;
#endif
}

// Throw a Python-accessible runtime_error using duvc::Error info
static void throw_duvc_error(const duvc::Error &e) {
    std::ostringstream ss;
    ss << "duvc error (" << static_cast<int>(e.code()) << "): " << e.description();
    throw std::runtime_error(ss.str());
}

// Unwrap helpers used by pythonic convenience wrappers
template<typename T>
static T unwrap_or_throw(const duvc::Result<T> &r) {
    if (r.is_ok()) return r.value();
    throw_duvc_error(r.error());
}

static void unwrap_void_or_throw(const duvc::Result<void> &r) {
    if (!r.is_ok()) throw_duvc_error(r.error());
}

// -----------------------------------------------------------------------------
// Windows GUID helpers (robust parsing from bytes/str/uuid.UUID/PyGUID exposed below)
// -----------------------------------------------------------------------------
#ifdef _WIN32

// A small Py-visible GUID wrapper to avoid binding native GUID aggregate directly
struct PyGUID {
    GUID guid;
    PyGUID() { std::memset(&guid, 0, sizeof(guid)); }
    explicit PyGUID(const std::string &s) { // accept textual GUID forms
        if (!parse_from_string(s)) throw std::invalid_argument("Invalid GUID string");
    }
    std::string to_string() const {
        char buf[64];
        snprintf(buf, sizeof(buf),
                 "{%08lX-%04hX-%04hX-%02hhX%02hhX-%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX}",
                 static_cast<unsigned long>(guid.Data1),
                 static_cast<unsigned short>(guid.Data2),
                 static_cast<unsigned short>(guid.Data3),
                 guid.Data4[0], guid.Data4[1],
                 guid.Data4[2], guid.Data4[3], guid.Data4[4], guid.Data4[5], guid.Data4[6], guid.Data4[7]);
        return std::string(buf);
    }

    static std::string normalize(const std::string &in) {
        std::string s;
        s.reserve(in.size());
        for (char c : in) {
            if (c == '{' || c == '}') continue;
            s.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(c))));
        }
        return s;
    }

    bool parse_from_string(const std::string &in) {
        std::string s = normalize(in);
        if (s.size() == 32) {
            s = s.substr(0,8) + "-" + s.substr(8,4) + "-" + s.substr(12,4) + "-" + s.substr(16,4) + "-" + s.substr(20,12);
        }
        if (s.size() != 36 || s[8] != '-' || s[13] != '-' || s[18] != '-' || s[23] != '-') return false;

        unsigned a=0, b=0, c=0;
        unsigned d[8] = {0};
        int matched = std::sscanf(s.c_str(), "%8x-%4x-%4x-%2x%2x-%2x%2x%2x%2x%2x%2x",
                                  &a, &b, &c,
                                  &d[0], &d[1], &d[2], &d[3], &d[4], &d[5], &d[6], &d[7]);
        if (matched != 11) return false;
        guid.Data1 = static_cast<unsigned long>(a);
        guid.Data2 = static_cast<unsigned short>(b);
        guid.Data3 = static_cast<unsigned short>(c);
        for (int i = 0; i < 8; ++i) guid.Data4[i] = static_cast<unsigned char>(d[i] & 0xFF);
        return true;
    }
};

// Convert flexible Python GUID-like inputs to native GUID
static GUID guid_from_pyobj(py::handle obj) {
    // If user provided our exposed PyGUID instance, cast directly.
    if (py::isinstance<PyGUID>(obj)) {
        PyGUID &pg = obj.cast<PyGUID&>();
        return pg.guid;
    }

    // Try uuid.UUID (we check by importing uuid and comparing types at runtime).
    try {
        py::module uuid = py::module::import("uuid");
        py::object UUIDcls = uuid.attr("UUID");
        if (py::isinstance(obj, UUIDcls)) {
            // uuid.UUID.hex returns 32 hex characters (no hyphens)
            std::string hex = obj.attr("hex").cast<std::string>();
            if (hex.size() != 32) throw std::invalid_argument("uuid.UUID.hex unexpected length");
            std::string hy = hex.substr(0,8) + "-" + hex.substr(8,4) + "-" + hex.substr(12,4) + "-" + hex.substr(16,4) + "-" + hex.substr(20,12);
            PyGUID pg(hy);
            return pg.guid;
        }
    } catch (const py::error_already_set&) {
        PyErr_Clear(); // ignore and continue with other cases
    }

    // If it's a string-like, parse textual GUID
    if (py::isinstance<py::str>(obj)) {
        std::string s = obj.cast<std::string>();
        PyGUID pg;
        if (!pg.parse_from_string(s)) {
            throw std::invalid_argument("String could not be parsed as GUID");
        }
        return pg.guid;
    }

    // If bytes/bytearray/buffer-like of length 16, copy raw bytes directly.
    if (py::isinstance<py::bytes>(obj) || py::isinstance<py::bytearray>(obj) || py::isinstance<py::buffer>(obj)) {
        // Convert handle to object to satisfy py::buffer ctor overloads on MSVC
        py::object o = py::reinterpret_borrow<py::object>(obj);
        py::buffer b(o);
        py::buffer_info info = b.request();
        size_t size_bytes = (info.size * info.itemsize);
        if (size_bytes != 16) {
            // bytes may contain textual guid -> try parse
            if (py::isinstance<py::bytes>(o) || py::isinstance<py::bytearray>(o)) {
                std::string s = py::bytes(o).cast<std::string>();
                PyGUID pg;
                if (pg.parse_from_string(s)) return pg.guid;
            }
            throw std::invalid_argument("Buffer/bytes must be 16 bytes for raw GUID");
        }
        GUID g;
        std::memcpy(&g, info.ptr, 16);
        return g;
    }

    // fallback: try to stringify
    try {
        std::string s = py::str(obj).cast<std::string>();
        PyGUID pg;
        if (pg.parse_from_string(s)) return pg.guid;
    } catch (...) {
        // ignore
    }

    throw std::invalid_argument("Unsupported GUID input type. Expected PyGUID, uuid.UUID, str, or 16-byte buffer.");
}

#endif // _WIN32

// -----------------------------------------------------------------------------
// Bindings
// -----------------------------------------------------------------------------
PYBIND11_MODULE(_duvc_ctl, m) {
    m.doc() = R"pbdoc(
        duvc-ctl Python bindings (windows).
        Provides cameras, devices, properties, and Result-based error handling.
    )pbdoc";

    // Exceptions
    py::register_exception<std::runtime_error>(m, "DuvcError");
    py::register_exception<std::invalid_argument>(m, "DuvcInvalidArgument");

    // Expose enums that come from your headers
    // (adjust if your headers have different enum names)
    py::enum_<duvc::CamMode>(m, "CamMode")
        .value("Auto", duvc::CamMode::Auto)
        .value("Manual", duvc::CamMode::Manual)
        .export_values();

    // CamProp and VidProp: expose values based on your headers
    py::enum_<duvc::CamProp>(m, "CamProp")
        .value("Pan", duvc::CamProp::Pan).value("Tilt", duvc::CamProp::Tilt)
        .value("Roll", duvc::CamProp::Roll).value("Zoom", duvc::CamProp::Zoom)
        .value("Exposure", duvc::CamProp::Exposure).value("Iris", duvc::CamProp::Iris)
        .value("Focus", duvc::CamProp::Focus)
        .export_values();

    py::enum_<duvc::VidProp>(m, "VidProp")
        .value("Brightness", duvc::VidProp::Brightness).value("Contrast", duvc::VidProp::Contrast)
        .value("Hue", duvc::VidProp::Hue).value("Saturation", duvc::VidProp::Saturation)
        .value("Sharpness", duvc::VidProp::Sharpness).value("Gamma", duvc::VidProp::Gamma)
        .export_values();


    // Add ErrorCode enum (corrected syntax - qualified enumerators)
    py::enum_<duvc::ErrorCode>(m, "ErrorCode")
        .value("Success", duvc::ErrorCode::Success)
        .value("DeviceNotFound", duvc::ErrorCode::DeviceNotFound)
        .value("DeviceBusy", duvc::ErrorCode::DeviceBusy)
        .value("PropertyNotSupported", duvc::ErrorCode::PropertyNotSupported)
        .value("InvalidValue", duvc::ErrorCode::InvalidValue)
        .value("PermissionDenied", duvc::ErrorCode::PermissionDenied)
        .value("SystemError", duvc::ErrorCode::SystemError)
        .value("InvalidArgument", duvc::ErrorCode::InvalidArgument)
        .value("NotImplemented", duvc::ErrorCode::NotImplemented)
        .export_values();

    // Basic types: Device, PropSetting, PropRange, Error
    py::class_<duvc::Device>(m, "Device")
        .def(py::init<>())
        .def_property_readonly("name", [](const duvc::Device &d){ return wstring_to_utf8(d.name); })
        .def_property_readonly("path", [](const duvc::Device &d){ return wstring_to_utf8(d.path); })
        .def("is_valid", &duvc::Device::is_valid)
        .def("__repr__", [](const duvc::Device &d){ return "<Device name='" + wstring_to_utf8(d.name) + "' path='" + wstring_to_utf8(d.path) + "'>"; });

    py::class_<duvc::PropSetting>(m, "PropSetting")
        .def(py::init<>())
        .def(py::init<int, duvc::CamMode>(), py::arg("value"), py::arg("mode"))
        .def_readwrite("value", &duvc::PropSetting::value)
        .def_readwrite("mode", &duvc::PropSetting::mode)
        .def("__repr__", [](const duvc::PropSetting &p) {
            std::ostringstream ss;
            ss << "<PropSetting value=" << p.value << " mode=" << (p.mode == duvc::CamMode::Auto ? "Auto" : "Manual") << ">";
            return ss.str();
        });

    py::class_<duvc::PropRange>(m, "PropRange")
        .def(py::init<>())
        .def_readwrite("min", &duvc::PropRange::min)
        .def_readwrite("max", &duvc::PropRange::max)
        .def_readwrite("step", &duvc::PropRange::step)
        .def_readwrite("default_val", &duvc::PropRange::default_val)
        .def("clamp", [](const duvc::PropRange &r, int v) {
            if (v < r.min) return r.min;
            if (v > r.max) return r.max;
            // align to step if step > 0
            if (r.step > 0) {
                int delta = (v - r.min) % r.step;
                if (delta != 0) v -= delta;
            }
            return v;
        }, py::arg("value"))
        .def("__repr__", [](const duvc::PropRange& r) {
            std::ostringstream ss;
            ss << "<PropRange min=" << r.min << " max=" << r.max << " step=" << r.step << " default=" << r.default_val << ">";
            return ss.str();
        });

    // Error and Result<T> wrappers
    py::class_<duvc::Error>(m, "CppError")
        .def("code", &duvc::Error::code)
        .def("message", &duvc::Error::message)
        .def("description", &duvc::Error::description)
        .def("__repr__", [](const duvc::Error &e) {
            std::ostringstream ss;
            ss << "<Error code=" << static_cast<int>(e.code()) << " message='" << e.message() << "'>";
            return ss.str();
        });

    // Result specializations commonly used
    py::class_<duvc::Result<duvc::PropSetting>>(m, "PropSettingResult")
        .def("is_ok", &duvc::Result<duvc::PropSetting>::is_ok)
        .def("is_error", &duvc::Result<duvc::PropSetting>::is_error)
        .def("value", [](const duvc::Result<duvc::PropSetting> &r){ if (!r.is_ok()) throw_duvc_error(r.error()); return r.value(); })
        .def("error", [](const duvc::Result<duvc::PropSetting> &r){ if (r.is_ok()) throw std::runtime_error("Result contains value"); return r.error(); })
        .def("__bool__", &duvc::Result<duvc::PropSetting>::is_ok);

    py::class_<duvc::Result<duvc::PropRange>>(m, "PropRangeResult")
        .def("is_ok", &duvc::Result<duvc::PropRange>::is_ok)
        .def("is_error", &duvc::Result<duvc::PropRange>::is_error)
        .def("value", [](const duvc::Result<duvc::PropRange> &r){ if (!r.is_ok()) throw_duvc_error(r.error()); return r.value(); })
        .def("error", [](const duvc::Result<duvc::PropRange> &r){ if (r.is_ok()) throw std::runtime_error("Result contains value"); return r.error(); })
        .def("__bool__", &duvc::Result<duvc::PropRange>::is_ok);

    py::class_<duvc::Result<void>>(m, "VoidResult")
        .def("is_ok", &duvc::Result<void>::is_ok)
        .def("is_error", &duvc::Result<void>::is_error)
        .def("error", [](const duvc::Result<void> &r){ if (r.is_ok()) throw std::runtime_error("Result contains no error"); return r.error(); })
        .def("__bool__", &duvc::Result<void>::is_ok);

    py::class_<duvc::Result<duvc::Camera>>(m, "CameraResult")
        .def("is_ok", &duvc::Result<duvc::Camera>::is_ok)
        .def("is_error", &duvc::Result<duvc::Camera>::is_error)
        .def("value", [](duvc::Result<duvc::Camera> &r) {
            if (!r.is_ok()) throw_duvc_error(r.error());
            return std::make_shared<duvc::Camera>(std::move(r).value());
        })
        .def("error", [](const duvc::Result<duvc::Camera> &r){ if (r.is_ok()) throw std::runtime_error("Result contains value"); return r.error(); })
        .def("__bool__", &duvc::Result<duvc::Camera>::is_ok);

    py::class_<duvc::Result<duvc::DeviceCapabilities>>(m, "DeviceCapabilitiesResult")
        .def("is_ok", &duvc::Result<duvc::DeviceCapabilities>::is_ok)
        .def("is_error", &duvc::Result<duvc::DeviceCapabilities>::is_error)
        .def("value", [](duvc::Result<duvc::DeviceCapabilities> &r){ if (!r.is_ok()) throw_duvc_error(r.error()); return std::move(r).value(); })
        .def("error", [](const duvc::Result<duvc::DeviceCapabilities> &r){ if (r.is_ok()) throw std::runtime_error("Result contains value"); return r.error(); })
        .def("__bool__", &duvc::Result<duvc::DeviceCapabilities>::is_ok);

    // DeviceCapabilities / PropertyCapability wrappers (assumes your types match)
    py::class_<duvc::PropertyCapability>(m, "PropertyCapability")
        .def_readwrite("supported", &duvc::PropertyCapability::supported)
        .def_readwrite("range", &duvc::PropertyCapability::range)
        .def_readwrite("current", &duvc::PropertyCapability::current)
        .def("supports_auto", &duvc::PropertyCapability::supports_auto);

    py::class_<duvc::DeviceCapabilities>(m, "DeviceCapabilities")
        .def(py::init<const duvc::Device&>())
        .def("supports_camera_property", &duvc::DeviceCapabilities::supports_camera_property)
        .def("supports_video_property", &duvc::DeviceCapabilities::supports_video_property)
        .def("supported_camera_properties", &duvc::DeviceCapabilities::supported_camera_properties)
        .def("supported_video_properties", &duvc::DeviceCapabilities::supported_video_properties)
        .def("get_camera_capability", &duvc::DeviceCapabilities::get_camera_capability, py::return_value_policy::reference_internal)
        .def("get_video_capability", &duvc::DeviceCapabilities::get_video_capability, py::return_value_policy::reference_internal)
        .def("device", &duvc::DeviceCapabilities::device, py::return_value_policy::reference_internal)
        .def("is_device_accessible", &duvc::DeviceCapabilities::is_device_accessible)
        .def("refresh", &duvc::DeviceCapabilities::refresh);

    // Camera RAII wrapper (use shared_ptr holder so non-copyable Camera works)
    py::class_<duvc::Camera, std::shared_ptr<duvc::Camera>>(m, "Camera")
        .def(py::init<const duvc::Device&>(), py::arg("device"))
        .def(py::init<int>(), py::arg("device_index"))
        .def("is_valid", &duvc::Camera::is_valid)
        .def("device", &duvc::Camera::device, py::return_value_policy::reference_internal)
        // raw API methods (Result-based)
        .def("get", py::overload_cast<duvc::CamProp>(&duvc::Camera::get), "Get camera property (Result<PropSetting>)")
        .def("get_vid", py::overload_cast<duvc::VidProp>(&duvc::Camera::get), "Get video property (Result<PropSetting>)")
        .def("set", py::overload_cast<duvc::CamProp, const duvc::PropSetting&>(&duvc::Camera::set), "Set camera property (Result<void>)")
        .def("set_vid", py::overload_cast<duvc::VidProp, const duvc::PropSetting&>(&duvc::Camera::set), "Set video property (Result<void>)")
        .def("get_range", py::overload_cast<duvc::CamProp>(&duvc::Camera::get_range), "Get camera range (Result<PropRange>)")
        .def("get_range_vid", py::overload_cast<duvc::VidProp>(&duvc::Camera::get_range), "Get video range (Result<PropRange>)")
        // python-friendly helpers that throw on error
        .def("get_camera_property", [](duvc::Camera &c, duvc::CamProp p) { return unwrap_or_throw<duvc::PropSetting>(c.get(p)); })
        .def("set_camera_property", [](duvc::Camera &c, duvc::CamProp p, const duvc::PropSetting &s) { unwrap_void_or_throw(c.set(p, s)); return true; })
        .def("get_camera_property_range", [](duvc::Camera &c, duvc::CamProp p) { return unwrap_or_throw<duvc::PropRange>(c.get_range(p)); })
        .def("get_video_property", [](duvc::Camera &c, duvc::VidProp p) { return unwrap_or_throw<duvc::PropSetting>(c.get(p)); })
        .def("set_video_property", [](duvc::Camera &c, duvc::VidProp p, const duvc::PropSetting &s) { unwrap_void_or_throw(c.set(p, s)); return true; })
        .def("get_video_property_range", [](duvc::Camera &c, duvc::VidProp p) { return unwrap_or_throw<duvc::PropRange>(c.get_range(p)); });

#ifdef _WIN32
    // Expose PyGUID wrapper
    py::class_<PyGUID>(m, "PyGUID")
        .def(py::init<>())
        .def(py::init<const std::string &>(), py::arg("guid_string"))
        .def("to_string", &PyGUID::to_string)
        .def("__repr__", [](const PyGUID &g) {
            return "<PyGUID " + g.to_string() + ">";
        });

    // Utility: construct PyGUID from uuid.UUID
    m.def("guid_from_uuid", [](py::object uuid_obj) {
        GUID g = guid_from_pyobj(uuid_obj);
        PyGUID pg;
        pg.guid = g;
        return pg;
    }, py::arg("uuid_obj"), "Convert a uuid.UUID into a PyGUID");
#endif


    // DeviceConnection & connection pool (if present)
#ifdef _WIN32
    py::class_<duvc::DeviceConnection>(m, "DeviceConnection")
        .def(py::init<const duvc::Device&>())
        .def("is_valid", &duvc::DeviceConnection::is_valid)
        .def("get_camera_property", [](duvc::DeviceConnection &conn, duvc::CamProp p){
            duvc::PropSetting s; bool ok = conn.get(p, s); return py::make_tuple(ok, s);
        })
        .def("set_camera_property", [](duvc::DeviceConnection &conn, duvc::CamProp p, const duvc::PropSetting &s){ return conn.set(p, s); })
        .def("get_video_property", [](duvc::DeviceConnection &conn, duvc::VidProp p){
            duvc::PropSetting s; bool ok = conn.get(p, s); return py::make_tuple(ok, s);
        })
        .def("set_video_property", [](duvc::DeviceConnection &conn, duvc::VidProp p, const duvc::PropSetting &s){ return conn.set(p, s); })
        .def("get_camera_property_range", [](duvc::DeviceConnection &conn, duvc::CamProp p){
            duvc::PropRange r; bool ok = conn.get_range(p, r); return py::make_tuple(ok, r);
        })
        .def("get_video_property_range", [](duvc::DeviceConnection &conn, duvc::VidProp p){
            duvc::PropRange r; bool ok = conn.get_range(p, r); return py::make_tuple(ok, r);
        });

#endif

    // Top-level functions
    m.def("list_devices", []() {
        return duvc::list_devices();
    }, "Enumerate video input devices (returns std::vector<Device>)");

    m.def("is_device_connected", &duvc::is_device_connected, "Check if a device is connected", py::arg("device"));

    // Old-style operations wrappers (operations.h) mapping bool-returning calls to (ok, value) tuples
    m.def("get_camera_property_direct", [](const duvc::Device &dev, duvc::CamProp p){
        duvc::PropSetting s; bool ok = duvc::get(dev, p, s); return py::make_tuple(ok, s);
    }, py::arg("device"), py::arg("prop"));

    m.def("get_camera_property_range_direct", [](const duvc::Device &dev, duvc::CamProp p){
        duvc::PropRange r; bool ok = duvc::get_range(dev, p, r); return py::make_tuple(ok, r);
    }, py::arg("device"), py::arg("prop"));

    // Device capabilities getters (overloads by device or index if present)
    m.def("get_device_capabilities", py::overload_cast<const duvc::Device&>(&duvc::get_device_capabilities), py::arg("device"));
    m.def("get_device_capabilities_by_index", py::overload_cast<int>(&duvc::get_device_capabilities), py::arg("index"));

    // Device-change callback registration (keeps Python callback alive)
    // The C++ API should provide register_device_change_callback/unregister_device_change_callback
    // We wrap to hold a shared_ptr to the python callable and keep it on module attribute
    if (py::hasattr(m, "__dict__")) {
        // ensure module attribute exists
    }
    // register_device_change_callback wrapper
    try {
        m.def("register_device_change_callback", [m](py::function cb) {
            auto cb_holder = std::make_shared<py::function>(cb);
            duvc::register_device_change_callback([cb_holder](bool added, const std::wstring &wpath) {
                try {
                    py::gil_scoped_acquire gil;
                    (*cb_holder)(added, wstring_to_utf8(wpath));
                } catch (const py::error_already_set &) {
                    PyErr_Clear();
                }
            });
            m.attr("__device_change_cb_holder__") = cb;
        }, "Register device hotplug callback (callback(added: bool, path: str))", py::arg("callback"));

        m.def("unregister_device_change_callback", [m]() {
            duvc::unregister_device_change_callback();
            if (py::hasattr(m, "__device_change_cb_holder__")) m.attr("__device_change_cb_holder__") = py::none();
        }, "Unregister device hotplug callback");
    } catch (...) {
        // If the C API does not provide these callbacks, ignore and continue.
        PyErr_Clear();
    }

#ifdef _WIN32
    // helper lambda to convert vector<uint8_t> -> py::bytes
    auto vec_to_bytes = [](const std::vector<uint8_t> &v) -> py::bytes {
        if (v.empty()) return py::bytes();
        return py::bytes(reinterpret_cast<const char*>(v.data()), static_cast<py::ssize_t>(v.size()));
    };

    // Bind read/get vendor property using the existing API:
    // bool get_vendor_property(const Device& dev, const GUID& property_set, ULONG property_id, std::vector<uint8_t>& data);
    m.def("read_vendor_property",
          [vec_to_bytes](const duvc::Device &d, const py::object &guid_obj, uint32_t prop_id) {
              GUID g = guid_from_pyobj(guid_obj);
              std::vector<uint8_t> out;
              bool ok = duvc::get_vendor_property(d, g, static_cast<ULONG>(prop_id), out);
              return py::make_tuple(ok, vec_to_bytes(out));
          },
          py::arg("device"), py::arg("guid"), py::arg("prop_id"),
          "Read a vendor property. Returns (ok: bool, data: bytes). Accepts PyGUID, uuid.UUID, str, or 16-byte buffer for guid.");

    // Bind write/set vendor property using the existing API:
    // bool set_vendor_property(const Device& dev, const GUID& property_set, ULONG property_id, const std::vector<uint8_t>& data);
    m.def("write_vendor_property",
          [](const duvc::Device &d, const py::object &guid_obj, uint32_t prop_id, const py::bytes &payload) -> bool {
              GUID g = guid_from_pyobj(guid_obj);
              std::string s = static_cast<std::string>(payload);
              std::vector<uint8_t> data(reinterpret_cast<const uint8_t*>(s.data()),
                                        reinterpret_cast<const uint8_t*>(s.data() + s.size()));
              bool ok = duvc::set_vendor_property(d, g, static_cast<ULONG>(prop_id), data);
              return ok;
          },
          py::arg("device"), py::arg("guid"), py::arg("prop_id"), py::arg("payload"),
          "Write a vendor property. payload: bytes. Returns bool success.");
#endif // _WIN32



    // If you prefer "py-friendly" open/open_camera convenience that throws on error
    try {
        m.def("open_camera", [](int index) -> std::shared_ptr<duvc::Camera> {
            auto r = duvc::open_camera(index);
            if (!r.is_ok()) throw_duvc_error(r.error());
            // move the Camera into a heap shared_ptr
            return std::make_shared<duvc::Camera>(std::move(r).value());
        }, py::arg("index"));
    } catch (...) {
        PyErr_Clear();
    }


    // Final module docstring or helper attributes
    m.attr("__version__") = (std::string) "1.1.0-duvc-bindings";
}
