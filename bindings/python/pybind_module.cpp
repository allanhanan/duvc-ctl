/**
 * @file pybind_module.cpp
 * @brief Complete pybind11 bindings for duvc-ctl library - FINAL WORKING VERSION
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/buffer_info.h>
#include <pybind11/numpy.h>
#include <pybind11/chrono.h>
#include <pybind11/complex.h>
#include <pybind11/iostream.h>

#include <string>
#include <vector>
#include <memory>
#include <sstream>
#include <iomanip>
#include <functional>
#include <optional>
#include <variant>
#include <system_error>

#ifdef _WIN32
// Windows-specific includes with collision avoidance
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <objbase.h>
#include <comdef.h>
#include <dshow.h>
// Avoid macro collisions
#ifdef DeviceCapabilities
#undef DeviceCapabilities
#endif
#ifdef DeviceCapabilitiesW
#undef DeviceCapabilitiesW
#endif
#endif // _WIN32

// duvc-ctl headers
#include "duvc-ctl/duvc.hpp"

#ifdef _WIN32
#include "duvc-ctl/platform/windows/ks_properties.h"
#include "duvc-ctl/platform/windows/connection_pool.h"
#include "duvc-ctl/platform/windows/directshow.h"
#include "duvc-ctl/vendor/logitech.h"
#include "duvc-ctl/vendor/constants.h"
#include "duvc-ctl/utils/error_decoder.h"
#endif

namespace py = pybind11;
using namespace duvc;

// =============================================================================
// String Conversion Helpers
// =============================================================================

/// Convert wide string to UTF-8 string
static std::string wstring_to_utf8(const std::wstring& wstr) {
#ifdef _WIN32
    if (wstr.empty()) return std::string();
    int size = WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), -1, nullptr, 0, nullptr, nullptr);
    if (size <= 0) return std::string();
    std::string result(size - 1, '\0');  // -1 to exclude null terminator counted by WideCharToMultiByte
    WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), -1, &result[0], size, nullptr, nullptr);
    return result;
#else
    // Simple fallback for non-Windows platforms
    std::string result;
    result.reserve(wstr.size());
    for (wchar_t wc : wstr) {
        result.push_back(static_cast<char>(wc & 0xFF));
    }
    return result;
#endif
}

/// Convert UTF-8 string to wide string
static std::wstring utf8_to_wstring(const std::string& str) {
#ifdef _WIN32
    if (str.empty()) return std::wstring();
    int size = MultiByteToWideChar(CP_UTF8, 0, str.c_str(), -1, nullptr, 0);
    if (size <= 0) return std::wstring();
    std::wstring result(size - 1, L'\0');  // -1 to exclude null terminator
    MultiByteToWideChar(CP_UTF8, 0, str.c_str(), -1, &result[0], size);
    return result;
#else
    // Simple fallback for non-Windows platforms
    std::wstring result;
    result.reserve(str.size());
    for (char c : str) {
        result.push_back(static_cast<wchar_t>(static_cast<unsigned char>(c)));
    }
    return result;
#endif
}

// =============================================================================
// Error Handling Helpers
// =============================================================================

/// Throw a Python-accessible exception using duvc::Error information
static void throw_duvc_error(const duvc::Error& error) {
    throw std::runtime_error("duvc error (" + std::to_string(static_cast<int>(error.code())) + "): " + error.description());
}

/// Unwrap Result<T> or throw exception
template<typename T>
static T unwrap_or_throw(const duvc::Result<T>& result) {
    if (result.is_ok()) {
        return result.value();
    }
    throw_duvc_error(result.error());
}

/// Unwrap Result<T>&& (move version) or throw exception
template<typename T>
static T unwrap_or_throw(duvc::Result<T>&& result) {
    if (result.is_ok()) {
        return std::move(result).value();
    }
    throw_duvc_error(result.error());
}

/// Unwrap void Result or throw exception
static void unwrap_void_or_throw(const duvc::Result<void>& result) {
    if (!result.is_ok()) {
        throw_duvc_error(result.error());
    }
}

// =============================================================================
// Abstract Interface Trampoline Classes
// =============================================================================

/// Trampoline class for IPlatformInterface to allow Python inheritance
class PyIPlatformInterface : public IPlatformInterface {
public:
    using IPlatformInterface::IPlatformInterface;

    Result<std::vector<Device>> list_devices() override {
        PYBIND11_OVERRIDE_PURE(
            Result<std::vector<Device>>,
            IPlatformInterface,
            list_devices,
        );
    }

    Result<bool> is_device_connected(const Device& device) override {
        PYBIND11_OVERRIDE_PURE(
            Result<bool>,
            IPlatformInterface,
            is_device_connected,
            device
        );
    }

    Result<std::unique_ptr<IDeviceConnection>> create_connection(const Device& device) override {
        PYBIND11_OVERRIDE_PURE(
            Result<std::unique_ptr<IDeviceConnection>>,
            IPlatformInterface,
            create_connection,
            device
        );
    }
};

/// Trampoline class for IDeviceConnection to allow Python inheritance
class PyIDeviceConnection : public IDeviceConnection {
public:
    using IDeviceConnection::IDeviceConnection;

    bool is_valid() const override {
        PYBIND11_OVERRIDE_PURE(
            bool,
            IDeviceConnection,
            is_valid,
        );
    }

    Result<PropSetting> get_camera_property(CamProp prop) override {
        PYBIND11_OVERRIDE_PURE(
            Result<PropSetting>,
            IDeviceConnection,
            get_camera_property,
            prop
        );
    }

    Result<void> set_camera_property(CamProp prop, const PropSetting& setting) override {
        PYBIND11_OVERRIDE_PURE(
            Result<void>,
            IDeviceConnection,
            set_camera_property,
            prop, setting
        );
    }

    Result<PropRange> get_camera_property_range(CamProp prop) override {
        PYBIND11_OVERRIDE_PURE(
            Result<PropRange>,
            IDeviceConnection,
            get_camera_property_range,
            prop
        );
    }

    Result<PropSetting> get_video_property(VidProp prop) override {
        PYBIND11_OVERRIDE_PURE(
            Result<PropSetting>,
            IDeviceConnection,
            get_video_property,
            prop
        );
    }

    Result<void> set_video_property(VidProp prop, const PropSetting& setting) override {
        PYBIND11_OVERRIDE_PURE(
            Result<void>,
            IDeviceConnection,
            set_video_property,
            prop, setting
        );
    }

    Result<PropRange> get_video_property_range(VidProp prop) override {
        PYBIND11_OVERRIDE_PURE(
            Result<PropRange>,
            IDeviceConnection,
            get_video_property_range,
            prop
        );
    }
};

#ifdef _WIN32
// =============================================================================
// Windows GUID Helper Class
// =============================================================================

/// @brief GUID wrapper for Windows vendor properties
/// 
/// Provides flexible GUID handling for vendor-specific camera properties,
/// supporting multiple input formats including Python uuid.UUID objects,
/// string representations, and raw byte arrays.
struct PyGUID {
    GUID guid;
    
    /// Default constructor - creates null GUID
    PyGUID() : guid{0} {}
    
    /// Construct from string representation
    /// @param guid_str String representation of GUID (with or without braces)
    explicit PyGUID(const std::string& guid_str) : guid{0} {
        if (!parse_from_string(guid_str)) {
            throw std::invalid_argument("Invalid GUID string format");
        }
    }

    /// Convert GUID to string representation
    /// @return String representation in format {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}
    std::string to_string() const {
        char buffer[40];
        snprintf(buffer, sizeof(buffer), 
            "{%08lX-%04hX-%04hX-%02hhX%02hhX-%02hhX%02hhX%02hhX%02hhX%02hhX%02hhX}",
            guid.Data1, guid.Data2, guid.Data3,
            guid.Data4[0], guid.Data4[1], guid.Data4[2], guid.Data4[3],
            guid.Data4[4], guid.Data4[5], guid.Data4[6], guid.Data4[7]);
        return std::string(buffer);
    }

    /// Parse GUID from string representation
    /// @param guid_str String representation (flexible format support)
    /// @return True if parsing successful, false otherwise
    bool parse_from_string(const std::string& guid_str) {
        // Remove braces and convert to lowercase for flexible parsing
        std::string clean_str;
        for (char c : guid_str) {
            if (c != '{' && c != '}') {
                clean_str += static_cast<char>(std::tolower(c));
            }
        }

        // Support both formats: with and without dashes
        if (clean_str.length() == 32) {
            // Format: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
            clean_str = clean_str.substr(0, 8) + "-" + clean_str.substr(8, 4) + "-" + 
                       clean_str.substr(12, 4) + "-" + clean_str.substr(16, 4) + "-" + 
                       clean_str.substr(20, 12);
        }

        if (clean_str.length() != 36 || 
            clean_str[8] != '-' || clean_str[13] != '-' || 
            clean_str[18] != '-' || clean_str[23] != '-') {
            return false;
        }

        // Parse components
        unsigned long data1;
        unsigned int data2, data3;
        unsigned int data4[8];
        
        int matches = sscanf(clean_str.c_str(), 
            "%8lx-%4x-%4x-%2x%2x-%2x%2x%2x%2x%2x%2x",
            &data1, &data2, &data3,
            &data4[0], &data4[1], &data4[2], &data4[3],
            &data4[4], &data4[5], &data4[6], &data4[7]);
        
        if (matches != 11) return false;

        guid.Data1 = static_cast<ULONG>(data1);
        guid.Data2 = static_cast<USHORT>(data2);
        guid.Data3 = static_cast<USHORT>(data3);
        for (int i = 0; i < 8; ++i) {
            guid.Data4[i] = static_cast<UCHAR>(data4[i]);
        }
        return true;
    }
};

/// Convert flexible Python GUID inputs to native GUID
/// @param obj Python object that could be PyGUID, uuid.UUID, str, or bytes
/// @return Native Windows GUID structure
/// @throws std::invalid_argument if conversion fails
static GUID guid_from_pyobj(py::handle obj) {
    // Direct PyGUID instance
    if (py::isinstance<PyGUID>(obj)) {
        return obj.cast<PyGUID&>().guid;
    }

    // Python uuid.UUID object
    try {
        py::module_ uuid_module = py::module_::import("uuid");
        py::object uuid_class = uuid_module.attr("UUID");
        if (py::isinstance(obj, uuid_class)) {
            std::string hex_str = obj.attr("hex").cast<std::string>();
            if (hex_str.length() != 32) {
                throw std::invalid_argument("Invalid UUID hex length");
            }
            PyGUID py_guid;
            if (py_guid.parse_from_string(hex_str)) {
                return py_guid.guid;
            }
        }
    } catch (const py::error_already_set&) {
        PyErr_Clear();
    }

    // String representation
    if (py::isinstance<py::str>(obj)) {
        std::string guid_str = obj.cast<std::string>();
        PyGUID py_guid;
        if (py_guid.parse_from_string(guid_str)) {
            return py_guid.guid;
        }
        throw std::invalid_argument("Invalid GUID string format");
    }

    // Raw bytes (must be exactly 16 bytes) - FIXED: Convert py::handle to py::object first
    if (py::isinstance<py::bytes>(obj) || py::isinstance<py::bytearray>(obj)) {
        py::object obj_as_object = py::reinterpret_borrow<py::object>(obj);  // Convert handle to object
        py::buffer_info info = py::buffer(obj_as_object).request();
        if (info.size * info.itemsize == 16) {
            GUID result;
            std::memcpy(&result, info.ptr, 16);
            return result;
        } else {
            // Try interpreting bytes as string
            std::string str_repr = py::str(obj).cast<std::string>();
            PyGUID py_guid;
            if (py_guid.parse_from_string(str_repr)) {
                return py_guid.guid;
            }
        }
    }

    throw std::invalid_argument("Unsupported GUID input type. Expected PyGUID, uuid.UUID, string, or 16-byte buffer");
}
#endif // _WIN32

// =============================================================================
// Main Python Module Definition
// =============================================================================

PYBIND11_MODULE(_duvc_ctl, m) {
    m.doc() = R"pbdoc(
        duvc-ctl Python bindings

        DirectShow UVC Camera Control Library providing comprehensive control over
        UVC-compatible cameras on Windows systems.

        Features:
        - PTZ (Pan/Tilt/Zoom) camera control with precise positioning
        - Video property adjustment (brightness, contrast, exposure, etc.)
        - Device capability detection and real-time monitoring
        - Vendor-specific extensions (Logitech, etc.)
        - Result-based error handling with detailed diagnostics
        - Thread-safe callback system for device hotplug events
        - Flexible GUID handling for vendor properties

        Example basic usage:
            import duvc_ctl
            
            devices = duvc_ctl.list_devices()
            if devices:
                camera = duvc_ctl.open_camera(devices[0])
                if camera.is_valid():
                    # Get current pan value
                    result = camera.get(duvc_ctl.CamProp.Pan)
                    if result.is_ok():
                        print(f"Pan: {result.value().value}")
                    
                    # Set pan to center position
                    setting = duvc_ctl.PropSetting(0, duvc_ctl.CamMode.Manual)
                    camera.set(duvc_ctl.CamProp.Pan, setting)
    )pbdoc";

    // =========================================================================
    // Core Enums (All Values Must Be Exposed)
    // =========================================================================
    
    /// @brief Camera control properties (IAMCameraControl)
    /// 
    /// These properties control physical camera movement and capture settings.
    /// Not all cameras support all properties - use device capabilities to check.
    py::enum_<CamProp>(m, "CamProp", "Camera control properties (IAMCameraControl)")
        .value("Pan", CamProp::Pan, "Horizontal camera rotation")
        .value("Tilt", CamProp::Tilt, "Vertical camera rotation")
        .value("Roll", CamProp::Roll, "Camera roll rotation around optical axis")
        .value("Zoom", CamProp::Zoom, "Optical zoom level")
        .value("Exposure", CamProp::Exposure, "Exposure time/shutter speed")
        .value("Iris", CamProp::Iris, "Aperture/iris diameter setting")
        .value("Focus", CamProp::Focus, "Focus distance position")
        .value("ScanMode", CamProp::ScanMode, "Scan mode (progressive/interlaced)")
        .value("Privacy", CamProp::Privacy, "Privacy mode on/off")
        .value("PanRelative", CamProp::PanRelative, "Relative pan movement")
        .value("TiltRelative", CamProp::TiltRelative, "Relative tilt movement")
        .value("RollRelative", CamProp::RollRelative, "Relative roll movement")
        .value("ZoomRelative", CamProp::ZoomRelative, "Relative zoom adjustment")
        .value("ExposureRelative", CamProp::ExposureRelative, "Relative exposure adjustment")
        .value("IrisRelative", CamProp::IrisRelative, "Relative iris adjustment")
        .value("FocusRelative", CamProp::FocusRelative, "Relative focus adjustment")
        .value("PanTilt", CamProp::PanTilt, "Combined pan/tilt control")
        .value("PanTiltRelative", CamProp::PanTiltRelative, "Relative pan/tilt movement")
        .value("FocusSimple", CamProp::FocusSimple, "Simple focus control (near/far)")
        .value("DigitalZoom", CamProp::DigitalZoom, "Digital zoom level")
        .value("DigitalZoomRelative", CamProp::DigitalZoomRelative, "Relative digital zoom")
        .value("BacklightCompensation", CamProp::BacklightCompensation, "Backlight compensation")
        .value("Lamp", CamProp::Lamp, "Camera lamp/LED control")
        .export_values();

    /// @brief Video processing properties (IAMVideoProcAmp)
    /// 
    /// These properties control image processing and color adjustment.
    /// Most USB cameras support brightness and contrast at minimum.
    py::enum_<VidProp>(m, "VidProp", "Video processing properties (IAMVideoProcAmp)")
        .value("Brightness", VidProp::Brightness, "Image brightness level")
        .value("Contrast", VidProp::Contrast, "Image contrast level")
        .value("Hue", VidProp::Hue, "Color hue adjustment")
        .value("Saturation", VidProp::Saturation, "Color saturation level")
        .value("Sharpness", VidProp::Sharpness, "Image sharpness enhancement")
        .value("Gamma", VidProp::Gamma, "Gamma correction value")
        .value("ColorEnable", VidProp::ColorEnable, "Color vs monochrome mode")
        .value("WhiteBalance", VidProp::WhiteBalance, "White balance temperature")
        .value("BacklightCompensation", VidProp::BacklightCompensation, "Backlight compensation level")
        .value("Gain", VidProp::Gain, "Sensor gain/amplification")
        .export_values();

    /// @brief Property control mode
    /// 
    /// Determines whether property is controlled automatically by camera
    /// or manually by application.
    py::enum_<CamMode>(m, "CamMode", "Property control mode")
        .value("Auto", CamMode::Auto, "Automatic control by camera")
        .value("Manual", CamMode::Manual, "Manual control by application")
        .export_values();

    /// @brief Error codes for library operations
    /// 
    /// Used in Result<T> objects to indicate specific failure types.
    py::enum_<ErrorCode>(m, "ErrorCode", "duvc-ctl error codes")
        .value("Success", ErrorCode::Success, "Operation succeeded")
        .value("DeviceNotFound", ErrorCode::DeviceNotFound, "Device not found or disconnected")
        .value("DeviceBusy", ErrorCode::DeviceBusy, "Device is busy or in use by another application")
        .value("PropertyNotSupported", ErrorCode::PropertyNotSupported, "Property not supported by this device")
        .value("InvalidValue", ErrorCode::InvalidValue, "Property value out of valid range")
        .value("PermissionDenied", ErrorCode::PermissionDenied, "Insufficient permissions to access device")
        .value("SystemError", ErrorCode::SystemError, "System/platform-specific error")
        .value("InvalidArgument", ErrorCode::InvalidArgument, "Invalid function argument provided")
        .value("NotImplemented", ErrorCode::NotImplemented, "Feature not implemented on this platform")
        .export_values();

    /// @brief Logging severity levels
    /// 
    /// Used with logging callback system for diagnostic output.
    py::enum_<LogLevel>(m, "LogLevel", "Logging severity levels")
        .value("Debug", LogLevel::Debug, "Detailed debugging information")
        .value("Info", LogLevel::Info, "General informational messages")
        .value("Warning", LogLevel::Warning, "Warning conditions")
        .value("Error", LogLevel::Error, "Error conditions")
        .value("Critical", LogLevel::Critical, "Critical error conditions")
        .export_values();

#ifdef _WIN32
    /// @brief Logitech vendor-specific properties (Windows only)
    /// 
    /// Extended properties available on supported Logitech cameras.
    /// Use supports_logitech_properties() to check availability.
    py::enum_<duvc::logitech::LogitechProperty>(m, "LogitechProperty", "Logitech vendor-specific properties")
        .value("RightLight", duvc::logitech::LogitechProperty::RightLight, "RightLight automatic exposure optimization")
        .value("RightSound", duvc::logitech::LogitechProperty::RightSound, "RightSound audio processing")
        .value("FaceTracking", duvc::logitech::LogitechProperty::FaceTracking, "Face tracking enable/disable")
        .value("LedIndicator", duvc::logitech::LogitechProperty::LedIndicator, "LED indicator control")
        .value("ProcessorUsage", duvc::logitech::LogitechProperty::ProcessorUsage, "Processor usage optimization")
        .value("RawDataBits", duvc::logitech::LogitechProperty::RawDataBits, "Raw sensor data bit depth")
        .value("FocusAssist", duvc::logitech::LogitechProperty::FocusAssist, "Focus assist beam control")
        .value("VideoStandard", duvc::logitech::LogitechProperty::VideoStandard, "Video standard selection")
        .value("DigitalZoomROI", duvc::logitech::LogitechProperty::DigitalZoomROI, "Digital zoom region of interest")
        .value("TiltPan", duvc::logitech::LogitechProperty::TiltPan, "Combined tilt/pan control")
        .export_values();
#endif

    // =========================================================================
    // Core Structs/Classes (All With py::module_local())
    // =========================================================================

    /// @brief Represents a camera device
    /// 
    /// Contains identifying information for a camera device including
    /// human-readable name and unique system path. Device objects are
    /// lightweight and can be copied freely.
    py::class_<Device>(m, "Device", py::module_local(), "Represents a camera device")
        .def(py::init<>(), "Create empty device")
        .def(py::init([](const std::string& name, const std::string& path) {
            return Device(utf8_to_wstring(name), utf8_to_wstring(path));
        }), "Create device with name and path", py::arg("name"), py::arg("path"))
        .def_property_readonly("name",
            [](const Device& d) { return wstring_to_utf8(d.name); },
            "Human-readable device name (UTF-8)")
        .def_property_readonly("path",
            [](const Device& d) { return wstring_to_utf8(d.path); },
            "Unique device path/identifier (UTF-8)")
        .def("is_valid", &Device::is_valid,
            "Check if device has valid identifying information")
        .def("get_id",
            [](const Device& d) { return wstring_to_utf8(d.get_id()); },
            "Get stable identifier for this device")
        .def("__repr__", [](const Device& d) {
            return "<Device name='" + wstring_to_utf8(d.name) + "' path='" + wstring_to_utf8(d.path) + "'>";
        });

    /// @brief Property setting with value and control mode
    /// 
    /// Represents the value and control mode for a camera or video property.
    /// The mode determines whether the property is controlled automatically
    /// by the camera or manually by the application.
    py::class_<PropSetting>(m, "PropSetting", py::module_local(), "Property setting with value and control mode")
        .def(py::init<>(), "Create default property setting")
        .def(py::init<int, CamMode>(), "Create property setting",
            py::arg("value"), py::arg("mode"))
        .def_readwrite("value", &PropSetting::value, "Property value")
        .def_readwrite("mode", &PropSetting::mode, "Control mode (auto/manual)")
        .def("__repr__", [](const PropSetting& p) {
            return "<PropSetting value=" + std::to_string(p.value) + " mode=" + 
                   (p.mode == CamMode::Auto ? "Auto" : "Manual") + ">";
        });

    /// @brief Property range and default information
    /// 
    /// Describes the valid range of values for a property, including
    /// minimum, maximum, step size, and default values.
    py::class_<PropRange>(m, "PropRange", py::module_local(), "Property range and default information")
        .def(py::init<>(), "Create default property range")
        .def_readwrite("min", &PropRange::min, "Minimum supported value")
        .def_readwrite("max", &PropRange::max, "Maximum supported value")
        .def_readwrite("step", &PropRange::step, "Step size between valid values")
        .def_readwrite("default_val", &PropRange::default_val, "Default value")
        .def_readwrite("default_mode", &PropRange::default_mode, "Default control mode")
        .def("is_valid", &PropRange::is_valid,
            "Check if a value is valid for this range", py::arg("value"))
        .def("clamp", &PropRange::clamp,
            "Clamp value to valid range", py::arg("value"))
        .def("__repr__", [](const PropRange& r) {
            return "<PropRange min=" + std::to_string(r.min) + " max=" + std::to_string(r.max) + 
                   " step=" + std::to_string(r.step) + " default=" + std::to_string(r.default_val) + ">";
        });

    /// @brief Property capability information
    /// 
    /// Contains complete information about a property's support status,
    /// valid range, and current value for a specific device.
    py::class_<PropertyCapability>(m, "PropertyCapability", py::module_local(), "Property capability information")
        .def_readwrite("supported", &PropertyCapability::supported, "Property is supported by device")
        .def_readwrite("range", &PropertyCapability::range, "Valid range for property")
        .def_readwrite("current", &PropertyCapability::current, "Current property value")
        .def("supports_auto", &PropertyCapability::supports_auto, "Check if property supports automatic mode")
        .def("__repr__", [](const PropertyCapability& c) {
            return "<PropertyCapability supported=" + std::to_string(c.supported) + ">";
        });

    /// @brief Error information with context (renamed from "Error" to avoid conflicts)
    /// 
    /// Contains error code and descriptive message for failed operations.
    /// Used within Result<T> objects to provide detailed failure information.
    py::class_<Error>(m, "DuvcError", py::module_local(), "Error information with context")
        .def(py::init<ErrorCode, std::string>(), py::arg("code"), py::arg("message") = "", 
             "Create error with ErrorCode and message")
        .def(py::init([](int error_code, const std::string& message) {
            std::error_code ec = std::make_error_code(static_cast<std::errc>(error_code));
            return Error(ec, message);
        }), py::arg("error_code"), py::arg("message") = "", 
             "Create error with std::error_code and message")
        .def("code", &Error::code, "Get error code")
        .def("message", &Error::message, "Get error message")
        .def("description", &Error::description, "Get full error description")
        .def("__repr__", [](const Error& e) {
            return "<DuvcError(code=" + std::to_string(static_cast<int>(e.code())) +
                   ", description='" + e.description() + "')>";
        });

    // =========================================================================
    // Result Types (All Specializations) - FINAL FIX WITH CORRECT SIGNATURES
    // =========================================================================

    py::class_<Result<PropSetting>>(m, "PropSettingResult", py::module_local(), "Result containing PropSetting or error")
        .def("is_ok", &Result<PropSetting>::is_ok, "Check if result contains a value (success)")
        .def("is_error", &Result<PropSetting>::is_error, "Check if result contains an error")
        .def("value", [](const Result<PropSetting>& r) -> const PropSetting& { return r.value(); }, 
             "Get the value (assumes success)", py::return_value_policy::reference_internal)
        .def("error", [](const Result<PropSetting>& r) -> const Error& { return r.error(); }, 
             "Get the error (assumes error)", py::return_value_policy::reference_internal)
        .def("value_or", [](const Result<PropSetting>& r, const PropSetting& default_value) { return r.value_or(default_value); }, 
             py::arg("default_value"), "Get value or default if error")
        .def("__bool__", [](const Result<PropSetting>& r) { return r.is_ok(); }, "Boolean conversion (true if success)");

    py::class_<Result<PropRange>>(m, "PropRangeResult", py::module_local(), "Result containing PropRange or error")
        .def("is_ok", &Result<PropRange>::is_ok, "Check if result contains a value (success)")
        .def("is_error", &Result<PropRange>::is_error, "Check if result contains an error")
        .def("value", [](const Result<PropRange>& r) -> const PropRange& { return r.value(); }, 
             "Get the value (assumes success)", py::return_value_policy::reference_internal)
        .def("error", [](const Result<PropRange>& r) -> const Error& { return r.error(); }, 
             "Get the error (assumes error)", py::return_value_policy::reference_internal)
        .def("value_or", [](const Result<PropRange>& r, const PropRange& default_value) { return r.value_or(default_value); }, 
             py::arg("default_value"), "Get value or default if error")
        .def("__bool__", [](const Result<PropRange>& r) { return r.is_ok(); }, "Boolean conversion (true if success)");

    py::class_<Result<void>>(m, "VoidResult", py::module_local(), "Result for operations that don't return values")
        .def("is_ok", &Result<void>::is_ok, "Check if result indicates success")
        .def("is_error", &Result<void>::is_error, "Check if result indicates error")
        .def("error", [](const Result<void>& r) -> const Error& { return r.error(); }, 
             "Get the error (assumes error)", py::return_value_policy::reference_internal)
        .def("__bool__", [](const Result<void>& r) { return r.is_ok(); }, "Boolean conversion (true if success)");

    py::class_<Result<Camera>>(m, "CameraResult", py::module_local(), "Result containing Camera or error")
        .def("is_ok", &Result<Camera>::is_ok, "Check if result contains a camera (success)")
        .def("is_error", &Result<Camera>::is_error, "Check if result contains an error")
        .def("value", [](const Result<Camera>& r) -> const Camera& { return r.value(); }, 
             "Get the camera (assumes success)", py::return_value_policy::reference_internal)
        .def("error", [](const Result<Camera>& r) -> const Error& { return r.error(); }, 
             "Get the error (assumes error)", py::return_value_policy::reference_internal)
        .def("__bool__", [](const Result<Camera>& r) { return r.is_ok(); }, "Boolean conversion (true if success)");

    py::class_<Result<DeviceCapabilities>>(m, "DeviceCapabilitiesResult", py::module_local(), "Result containing DeviceCapabilities or error")
        .def("is_ok", &Result<DeviceCapabilities>::is_ok, "Check if result contains capabilities (success)")
        .def("is_error", &Result<DeviceCapabilities>::is_error, "Check if result contains an error")
        .def("value", [](const Result<DeviceCapabilities>& r) -> const DeviceCapabilities& { return r.value(); }, 
             "Get the capabilities (assumes success)", py::return_value_policy::reference_internal)
        .def("error", [](const Result<DeviceCapabilities>& r) -> const Error& { return r.error(); }, 
             "Get the error (assumes error)", py::return_value_policy::reference_internal)
        .def("__bool__", [](const Result<DeviceCapabilities>& r) { return r.is_ok(); }, "Boolean conversion (true if success)");

    // Additional Result specializations with lambda wrappers for correct signatures
    py::class_<Result<std::vector<Device>>>(m, "DeviceListResult", py::module_local(), "Result containing device list or error")
        .def("is_ok", &Result<std::vector<Device>>::is_ok, "Check if result contains devices (success)")
        .def("is_error", &Result<std::vector<Device>>::is_error, "Check if result contains an error")
        .def("value", [](const Result<std::vector<Device>>& r) -> const std::vector<Device>& { return r.value(); }, 
             "Get the device list (assumes success)", py::return_value_policy::reference_internal)
        .def("error", [](const Result<std::vector<Device>>& r) -> const Error& { return r.error(); }, 
             "Get the error (assumes error)", py::return_value_policy::reference_internal)
        .def("__bool__", [](const Result<std::vector<Device>>& r) { return r.is_ok(); });

    py::class_<Result<std::unique_ptr<IDeviceConnection>>>(m, "DeviceConnectionResult", py::module_local(), "Result containing device connection or error")
        .def("is_ok", &Result<std::unique_ptr<IDeviceConnection>>::is_ok, "Check if result contains connection (success)")
        .def("is_error", &Result<std::unique_ptr<IDeviceConnection>>::is_error, "Check if result contains an error")
        .def("value", [](Result<std::unique_ptr<IDeviceConnection>>& r) {
            // IMPORTANT: This moves the unique_ptr out of the Result, invalidating it
            return std::move(r).value();
        }, "Get the connection (assumes success) - WARNING: this moves the connection out and invalidates the Result")
        .def("error", [](const Result<std::unique_ptr<IDeviceConnection>>& r) -> const Error& { 
            return r.error(); 
        }, "Get the error (assumes error)", py::return_value_policy::reference_internal)
        .def("__bool__", [](const Result<std::unique_ptr<IDeviceConnection>>& r) { return r.is_ok(); });


    py::class_<Result<bool>>(m, "BoolResult", py::module_local(), "Result containing bool or error")
        .def("is_ok", &Result<bool>::is_ok, "Check if result contains a value (success)")
        .def("is_error", &Result<bool>::is_error, "Check if result contains an error")
        .def("value", [](const Result<bool>& r) -> bool { return r.value(); }, 
             "Get the boolean value (assumes success)")
        .def("error", [](const Result<bool>& r) -> const Error& { return r.error(); }, 
             "Get the error (assumes error)", py::return_value_policy::reference_internal)
        .def("__bool__", [](const Result<bool>& r) { return r.is_ok(); }, "Boolean conversion (true if success)");

    py::class_<Result<uint32_t>>(m, "Uint32Result", py::module_local(), "Result containing uint32_t or error")
        .def("is_ok", &Result<uint32_t>::is_ok, "Check if result contains a value (success)")
        .def("is_error", &Result<uint32_t>::is_error, "Check if result contains an error")
        .def("value", [](const Result<uint32_t>& r) -> uint32_t { return r.value(); }, 
             "Get the uint32 value (assumes success)")
        .def("error", [](const Result<uint32_t>& r) -> const Error& { return r.error(); }, 
             "Get the error (assumes error)", py::return_value_policy::reference_internal)
        .def("__bool__", [](const Result<uint32_t>& r) { return r.is_ok(); }, "Boolean conversion (true if success)");

    py::class_<Result<std::vector<uint8_t>>>(m, "VectorUint8Result", py::module_local(), "Result containing vector<uint8_t> or error")
        .def("is_ok", &Result<std::vector<uint8_t>>::is_ok, "Check if result contains data (success)")
        .def("is_error", &Result<std::vector<uint8_t>>::is_error, "Check if result contains an error")
        .def("value", [](const Result<std::vector<uint8_t>>& r) -> const std::vector<uint8_t>& { return r.value(); }, 
             "Get the data (assumes success)", py::return_value_policy::reference_internal)
        .def("error", [](const Result<std::vector<uint8_t>>& r) -> const Error& { return r.error(); }, 
             "Get the error (assumes error)", py::return_value_policy::reference_internal)
        .def("__bool__", [](const Result<std::vector<uint8_t>>& r) { return r.is_ok(); }, "Boolean conversion (true if success)");

    // =========================================================================
    // Abstract Interface Classes
    // =========================================================================

    /// @brief Abstract platform interface
    /// 
    /// Defines the interface for platform-specific device enumeration and connection.
    /// Can be subclassed in Python for custom implementations.
    py::class_<IPlatformInterface, PyIPlatformInterface>(m, "IPlatformInterface", py::module_local(), "Abstract platform interface")
        .def(py::init<>(), "Create platform interface")
        .def("list_devices", &IPlatformInterface::list_devices, "Enumerate devices")
        .def("is_device_connected", &IPlatformInterface::is_device_connected, py::arg("device"), "Check device connection")
        .def("create_connection", &IPlatformInterface::create_connection, py::arg("device"), "Create device connection");

    /// @brief Abstract device connection interface
    /// 
    /// Defines the interface for low-level device property access.
    /// Can be subclassed in Python for custom device implementations.
    py::class_<IDeviceConnection, PyIDeviceConnection>(m, "IDeviceConnection", py::module_local(), "Abstract device connection")
        .def(py::init<>(), "Create device connection")
        .def("is_valid", &IDeviceConnection::is_valid, "Check if connection is valid")
        .def("get_camera_property", &IDeviceConnection::get_camera_property, py::arg("prop"), "Get camera property")
        .def("set_camera_property", &IDeviceConnection::set_camera_property, py::arg("prop"), py::arg("setting"), "Set camera property")
        .def("get_camera_property_range", &IDeviceConnection::get_camera_property_range, py::arg("prop"), "Get camera property range")
        .def("get_video_property", &IDeviceConnection::get_video_property, py::arg("prop"), "Get video property")
        .def("set_video_property", &IDeviceConnection::set_video_property, py::arg("prop"), py::arg("setting"), "Set video property")
        .def("get_video_property_range", &IDeviceConnection::get_video_property_range, py::arg("prop"), "Get video property range");

    /// @brief RAII camera handle for device control
    /// 
    /// Provides safe, convenient access to camera properties with automatic
    /// resource management. Camera objects use move semantics and cannot be copied.
    /// All property operations return Result<T> for robust error handling.
    py::class_<Camera, std::shared_ptr<Camera>>(m, "Camera", py::module_local(), "RAII camera handle for device control")
        .def(py::init([](const Device& device) {
            return std::make_shared<Camera>(device);
        }), py::arg("device"), "Create camera handle for device")
        .def(py::init([](int device_index) {
            return std::make_shared<Camera>(device_index);
        }), py::arg("device_index"), "Create camera handle by device index")
        .def("is_valid", &Camera::is_valid, "Check if camera is valid and connected")
        .def("is_ok", &Camera::is_valid, "Alias for is_valid() - check if camera is valid and connected")
        .def("device", &Camera::device, py::return_value_policy::reference_internal, "Get the underlying device information")
        // Camera property operations
        .def("get", py::overload_cast<CamProp>(&Camera::get), py::arg("prop"),
            "Get camera property value")
        .def("set", py::overload_cast<CamProp, const PropSetting&>(&Camera::set), 
            py::arg("prop"), py::arg("setting"),
            "Set camera property value")
        .def("get_range", py::overload_cast<CamProp>(&Camera::get_range), py::arg("prop"),
            "Get camera property range")
        // Video property operations  
        .def("get", py::overload_cast<VidProp>(&Camera::get), py::arg("prop"),
            "Get video processing property value")
        .def("set", py::overload_cast<VidProp, const PropSetting&>(&Camera::set),
            py::arg("prop"), py::arg("setting"),
            "Set video processing property value")
        .def("get_range", py::overload_cast<VidProp>(&Camera::get_range), py::arg("prop"),
            "Get video processing property range")
        .def("__repr__", [](const Camera& c) {
            return "<Camera valid=" + std::to_string(c.is_valid()) + ">";
        });

    /// @brief Complete device capability snapshot
    /// 
    /// Provides comprehensive information about all supported properties
    /// for a specific device, including current values and valid ranges.
    py::class_<DeviceCapabilities>(m, "DeviceCapabilities", py::module_local(), "Complete device capability snapshot")
        .def(py::init<const Device&>(), py::arg("device"), "Create capabilities snapshot for device")
        .def("get_camera_capability", &DeviceCapabilities::get_camera_capability, 
            py::return_value_policy::reference_internal, py::arg("prop"),
            "Get camera property capability")
        .def("get_video_capability", &DeviceCapabilities::get_video_capability,
            py::return_value_policy::reference_internal, py::arg("prop"),
            "Get video property capability")
        .def("supports_camera_property", &DeviceCapabilities::supports_camera_property, py::arg("prop"),
            "Check if camera property is supported")
        .def("supports_video_property", &DeviceCapabilities::supports_video_property, py::arg("prop"),
            "Check if video property is supported")
        .def("supported_camera_properties", &DeviceCapabilities::supported_camera_properties,
            "Get list of supported camera properties")
        .def("supported_video_properties", &DeviceCapabilities::supported_video_properties,
            "Get list of supported video properties")
        .def("device", &DeviceCapabilities::device, py::return_value_policy::reference_internal,
            "Get the device this capability snapshot is for")
        .def("is_device_accessible", &DeviceCapabilities::is_device_accessible,
            "Check if device is connected and accessible")
        .def("refresh", &DeviceCapabilities::refresh, "Refresh capability snapshot from device")
        .def("__repr__", [](const DeviceCapabilities& c) {
            return "<DeviceCapabilities accessible=" + std::to_string(c.is_device_accessible()) + ">";
        });

#ifdef _WIN32
    /// @brief Vendor-specific property data (Windows only)
    /// 
    /// Encapsulates vendor-specific property information including
    /// property set GUID, property ID, and associated data payload.
    py::class_<VendorProperty>(m, "VendorProperty", py::module_local(), "Vendor-specific property data")
        .def(py::init<>(), "Default constructor")
        .def(py::init([](const PyGUID& property_set, uint32_t property_id, const std::vector<uint8_t>& data) {
            return VendorProperty(property_set.guid, static_cast<ULONG>(property_id), data);
        }), py::arg("property_set"), py::arg("property_id"), py::arg("data") = std::vector<uint8_t>(),
             "Construct vendor property")
        .def_property("property_set", 
            [](const VendorProperty& vp) { 
                PyGUID pg; 
                pg.guid = vp.property_set; 
                return pg; 
            },
            [](VendorProperty& vp, const PyGUID& pg) { 
                vp.property_set = pg.guid; 
            }, "Property set GUID")
        .def_readwrite("property_id", &VendorProperty::property_id, "Property ID within property set")
        .def_readwrite("data", &VendorProperty::data, "Property data payload");

    /// @brief GUID wrapper for Windows vendor properties
    /// 
    /// Provides flexible GUID handling supporting multiple input formats
    /// including string representations and Python uuid.UUID objects.
    py::class_<PyGUID>(m, "PyGUID", py::module_local(), "GUID wrapper for vendor properties")
        .def(py::init<>(), "Default constructor")
        .def(py::init<const std::string&>(), py::arg("guid_str"), "Construct from string")
        .def("to_string", &PyGUID::to_string, "Convert to string representation")
        .def("parse_from_string", &PyGUID::parse_from_string, py::arg("guid_str"), "Parse GUID from string")
        .def("__str__", &PyGUID::to_string)
        .def("__repr__", [](const PyGUID& g) { 
            return "<PyGUID " + g.to_string() + ">"; 
        });

    /// @brief Windows-specific device connection (Windows only)
    /// 
    /// Direct access to Windows DirectShow interfaces for advanced control.
    /// Provides lower-level access than the Camera class with manual resource management.
    py::class_<DeviceConnection>(m, "DeviceConnection", py::module_local(), "Windows-specific device connection")
        .def(py::init<const Device&>(), py::arg("device"), "Create connection to specified device")
        .def("get", [](DeviceConnection& conn, CamProp prop) {
            PropSetting setting;
            bool success = conn.get(prop, setting);
            return py::make_tuple(success, setting);
        }, py::arg("prop"), "Get current value of a camera control property")
        .def("set", [](DeviceConnection& conn, CamProp prop, const PropSetting& setting) {
            return conn.set(prop, setting);
        }, py::arg("prop"), py::arg("setting"), "Set value of a camera control property")
        .def("get_range", [](DeviceConnection& conn, CamProp prop) {
            PropRange range;
            bool success = conn.get_range(prop, range);
            return py::make_tuple(success, range);
        }, py::arg("prop"), "Get valid range for a camera control property")
        .def("get", [](DeviceConnection& conn, VidProp prop) {
            PropSetting setting;
            bool success = conn.get(prop, setting);
            return py::make_tuple(success, setting);
        }, py::arg("prop"), "Get current value of a video processing property")
        .def("set", [](DeviceConnection& conn, VidProp prop, const PropSetting& setting) {
            return conn.set(prop, setting);
        }, py::arg("prop"), py::arg("setting"), "Set value of a video processing property")
        .def("get_range", [](DeviceConnection& conn, VidProp prop) {
            PropRange range;
            bool success = conn.get_range(prop, range);
            return py::make_tuple(success, range);
        }, py::arg("prop"), "Get valid range for a video processing property")
        .def("is_valid", &DeviceConnection::is_valid, "Check if connection is valid");

    /// @brief KsPropertySet wrapper for vendor properties (Windows only)
    /// 
    /// Provides access to Windows KsProperty interface for vendor-specific
    /// camera properties not exposed through standard DirectShow interfaces.
    py::class_<KsPropertySet>(m, "KsPropertySet", py::module_local(), "KsPropertySet wrapper for vendor properties")
        .def(py::init<const Device&>(), py::arg("device"), "Create KsPropertySet from device")
        .def("is_valid", &KsPropertySet::is_valid, "Check if property set is valid")
        .def("query_support", [](KsPropertySet& ks, const py::object& guid_obj, uint32_t prop_id) {
            GUID guid = guid_from_pyobj(guid_obj);
            return ks.query_support(guid, prop_id);
        }, py::arg("property_set"), py::arg("property_id"), "Query property support capabilities")
        .def("get_property", [](KsPropertySet& ks, const py::object& guid_obj, uint32_t prop_id) {
            GUID guid = guid_from_pyobj(guid_obj);
            return ks.get_property(guid, prop_id);
        }, py::arg("property_set"), py::arg("property_id"), "Get property data as raw bytes")
        .def("set_property", [](KsPropertySet& ks, const py::object& guid_obj, uint32_t prop_id, const std::vector<uint8_t>& data) {
            GUID guid = guid_from_pyobj(guid_obj);
            return ks.set_property(guid, prop_id, data);
        }, py::arg("property_set"), py::arg("property_id"), py::arg("data"), "Set property data from raw bytes")
        // Template function specializations for common types
        .def("get_property_int", [](KsPropertySet& ks, const py::object& guid_obj, uint32_t prop_id) {
            GUID guid = guid_from_pyobj(guid_obj);
            return ks.get_property_typed<int>(guid, prop_id);
        }, py::arg("property_set"), py::arg("property_id"), "Get property as integer")
        .def("set_property_int", [](KsPropertySet& ks, const py::object& guid_obj, uint32_t prop_id, int value) {
            GUID guid = guid_from_pyobj(guid_obj);
            return ks.set_property_typed<int>(guid, prop_id, value);
        }, py::arg("property_set"), py::arg("property_id"), py::arg("value"), "Set property from integer")
        .def("get_property_uint32", [](KsPropertySet& ks, const py::object& guid_obj, uint32_t prop_id) {
            GUID guid = guid_from_pyobj(guid_obj);
            return ks.get_property_typed<uint32_t>(guid, prop_id);
        }, py::arg("property_set"), py::arg("property_id"), "Get property as uint32")
        .def("set_property_uint32", [](KsPropertySet& ks, const py::object& guid_obj, uint32_t prop_id, uint32_t value) {
            GUID guid = guid_from_pyobj(guid_obj);
            return ks.set_property_typed<uint32_t>(guid, prop_id, value);
        }, py::arg("property_set"), py::arg("property_id"), py::arg("value"), "Set property from uint32")
        .def("get_property_bool", [](KsPropertySet& ks, const py::object& guid_obj, uint32_t prop_id) {
            GUID guid = guid_from_pyobj(guid_obj);
            return ks.get_property_typed<bool>(guid, prop_id);
        }, py::arg("property_set"), py::arg("property_id"), "Get property as boolean")
        .def("set_property_bool", [](KsPropertySet& ks, const py::object& guid_obj, uint32_t prop_id, bool value) {
            GUID guid = guid_from_pyobj(guid_obj);
            return ks.set_property_typed<bool>(guid, prop_id, value);
        }, py::arg("property_set"), py::arg("property_id"), py::arg("value"), "Set property from boolean");
#endif

    // =========================================================================
    // Core Functions (All Must Be Bound)
    // =========================================================================

    // Device Management Functions
    m.def("list_devices", &list_devices, 
        "Enumerate all available video input devices");
    m.def("is_device_connected", &is_device_connected, py::arg("device"), 
        "Check if a device is currently connected and accessible");

    // Device change callbacks with proper GIL management
    m.def("register_device_change_callback", [](py::function callback) {
        static py::function stored_callback;  // Keep callback alive
        stored_callback = callback;
        register_device_change_callback([](bool added, const std::wstring& device_path) {
            py::gil_scoped_acquire gil;
            try {
                stored_callback(added, wstring_to_utf8(device_path));
            } catch (const py::error_already_set&) {
                PyErr_Clear();  // Clear Python exception state
            }
        });
    }, py::arg("callback"), "Register callback for device hotplug events");
    
    m.def("unregister_device_change_callback", &unregister_device_change_callback,
        "Unregister device change callback");

    // Camera Operations
    m.def("open_camera", py::overload_cast<int>(&open_camera), py::arg("device_index"),
        "Create camera handle from device index");
    m.def("open_camera", py::overload_cast<const Device&>(&open_camera), py::arg("device"),
        "Create camera handle from device object");

    // Capability Operations  
    m.def("get_device_capabilities", py::overload_cast<const Device&>(&get_device_capabilities), py::arg("device"),
        "Create device capability snapshot");
    m.def("get_device_capabilities", py::overload_cast<int>(&get_device_capabilities), py::arg("device_index"),
        "Create device capability snapshot by index");

    // String Conversion Functions
    m.def("to_string", py::overload_cast<CamProp>(&to_string), py::arg("prop"), 
        "Convert camera property enum to string");
    m.def("to_string", py::overload_cast<VidProp>(&to_string), py::arg("prop"), 
        "Convert video property enum to string");
    m.def("to_string", py::overload_cast<CamMode>(&to_string), py::arg("mode"), 
        "Convert camera mode enum to string");
    m.def("to_string", py::overload_cast<ErrorCode>(&to_string), py::arg("code"), 
        "Convert error code enum to string");
    m.def("to_string", py::overload_cast<LogLevel>(&to_string), py::arg("level"), 
        "Convert log level enum to string");

    // Wide string conversion functions (FIXED - return UTF-8 properly)
    m.def("to_wstring_cam_prop", [](CamProp prop) { 
        return wstring_to_utf8(to_wstring(prop)); 
    }, py::arg("prop"), "Convert camera property enum to wide string (returned as UTF-8)");
    
    m.def("to_wstring_vid_prop", [](VidProp prop) { 
        return wstring_to_utf8(to_wstring(prop)); 
    }, py::arg("prop"), "Convert video property enum to wide string (returned as UTF-8)");
    
    m.def("to_wstring_cam_mode", [](CamMode mode) { 
        return wstring_to_utf8(to_wstring(mode)); 
    }, py::arg("mode"), "Convert camera mode enum to wide string (returned as UTF-8)");

    // UTF-8 conversion utilities
    m.def("to_utf8", [](const std::string& input) -> std::string {
        std::wstring ws = utf8_to_wstring(input);
        return duvc::to_utf8(ws);
    }, py::arg("wide_string_as_utf8"), "Convert wide string to UTF-8");

    // Logging API with GIL management
    m.def("set_log_callback", [](py::function callback) {
        static py::function stored_log_callback;  // Keep callback alive
        stored_log_callback = callback;
        set_log_callback([](LogLevel level, const std::string& message) {
            py::gil_scoped_acquire gil;
            try {
                stored_log_callback(level, message);
            } catch (const py::error_already_set&) {
                PyErr_Clear();
            }
        });
    }, py::arg("callback"), "Set global log callback function");
    
    m.def("set_log_level", &set_log_level, py::arg("level"), "Set minimum log level");
    m.def("get_log_level", &get_log_level, "Get current minimum log level");
    m.def("log_message", &log_message, py::arg("level"), py::arg("message"), "Log a message at specified level");
    m.def("log_debug", &log_debug, py::arg("message"), "Log debug message");
    m.def("log_info", &log_info, py::arg("message"), "Log info message");
    m.def("log_warning", &log_warning, py::arg("message"), "Log warning message");
    m.def("log_error", &log_error, py::arg("message"), "Log error message");
    m.def("log_critical", &log_critical, py::arg("message"), "Log critical message");

    // Logging macro equivalents
    m.def("DUVC_LOG_DEBUG", [](const std::string& msg) { log_debug(msg); }, py::arg("message"), "Debug log macro equivalent");
    m.def("DUVC_LOG_INFO", [](const std::string& msg) { log_info(msg); }, py::arg("message"), "Info log macro equivalent");
    m.def("DUVC_LOG_WARNING", [](const std::string& msg) { log_warning(msg); }, py::arg("message"), "Warning log macro equivalent");  
    m.def("DUVC_LOG_ERROR", [](const std::string& msg) { log_error(msg); }, py::arg("message"), "Error log macro equivalent");
    m.def("DUVC_LOG_CRITICAL", [](const std::string& msg) { log_critical(msg); }, py::arg("message"), "Critical log macro equivalent");

    // Error Decoding Functions
    m.def("decode_system_error", &decode_system_error, py::arg("error_code"),
        "Decode system error code to human-readable string");
    m.def("get_diagnostic_info", &get_diagnostic_info, 
        "Get comprehensive diagnostic information for troubleshooting");

#ifdef _WIN32
    // Windows-specific error decoding
    m.def("decode_hresult", &decode_hresult, py::arg("hresult"), 
        "Decode Windows HRESULT to human-readable string");
    m.def("get_hresult_details", &get_hresult_details, py::arg("hresult"), 
        "Get detailed HRESULT information");
    m.def("is_device_error", &is_device_error, py::arg("hresult"), 
        "Check if HRESULT indicates a device-related error");
    m.def("is_permission_error", &is_permission_error, py::arg("hresult"), 
        "Check if HRESULT indicates permission/access error");
#endif

    // Platform Interface
    m.def("create_platform_interface", &create_platform_interface, 
        "Get platform-specific interface implementation");

    // Quick API convenience functions (return tuples for Python-friendly usage)
    m.def("get_camera_property_direct", [](const Device& device, CamProp prop) {
        PropSetting setting;
        bool success = duvc::get(device, prop, setting);
        return py::make_tuple(success, setting);
    }, py::arg("device"), py::arg("prop"), "Get camera property value (quick API, returns tuple)");
    
    m.def("set_camera_property_direct", [](const Device& device, CamProp prop, const PropSetting& setting) {
        return duvc::set(device, prop, setting);
    }, py::arg("device"), py::arg("prop"), py::arg("setting"), "Set camera property value (quick API)");
    
    m.def("get_camera_property_range_direct", [](const Device& device, CamProp prop) {
        PropRange range;
        bool success = duvc::get_range(device, prop, range);
        return py::make_tuple(success, range);
    }, py::arg("device"), py::arg("prop"), "Get camera property range (quick API, returns tuple)");
    
    m.def("get_video_property_direct", [](const Device& device, VidProp prop) {
        PropSetting setting;
        bool success = duvc::get(device, prop, setting);
        return py::make_tuple(success, setting);
    }, py::arg("device"), py::arg("prop"), "Get video property value (quick API, returns tuple)");
    
    m.def("set_video_property_direct", [](const Device& device, VidProp prop, const PropSetting& setting) {
        return duvc::set(device, prop, setting);
    }, py::arg("device"), py::arg("prop"), py::arg("setting"), "Set video property value (quick API)");
    
    m.def("get_video_property_range_direct", [](const Device& device, VidProp prop) {
        PropRange range;
        bool success = duvc::get_range(device, prop, range);
        return py::make_tuple(success, range);
    }, py::arg("device"), py::arg("prop"), "Get video property range (quick API, returns tuple)");

#ifdef _WIN32
    // Vendor Property Functions (Windows only)
    m.def("get_vendor_property", [](const Device& device, const py::object& guid_obj, uint32_t property_id) {
        GUID guid = guid_from_pyobj(guid_obj);
        std::vector<uint8_t> data;
        bool success = get_vendor_property(device, guid, static_cast<ULONG>(property_id), data);
        py::bytes result_bytes;
        if (success && !data.empty()) {
            result_bytes = py::bytes(reinterpret_cast<const char*>(data.data()), data.size());
        }
        return py::make_tuple(success, result_bytes);
    }, py::arg("device"), py::arg("property_set"), py::arg("property_id"), 
       "Get vendor property data (accepts PyGUID, uuid.UUID, str, or 16-byte buffer)");

    m.def("set_vendor_property", [](const Device& device, const py::object& guid_obj, uint32_t property_id, const py::bytes& data) {
        GUID guid = guid_from_pyobj(guid_obj);
        std::string data_str = static_cast<std::string>(data);
        std::vector<uint8_t> data_vec(reinterpret_cast<const uint8_t*>(data_str.data()),
                                      reinterpret_cast<const uint8_t*>(data_str.data() + data_str.size()));
        return set_vendor_property(device, guid, static_cast<ULONG>(property_id), data_vec);
    }, py::arg("device"), py::arg("property_set"), py::arg("property_id"), py::arg("data"), 
       "Set vendor property data");

    m.def("query_vendor_property_support", [](const Device& device, const py::object& guid_obj, uint32_t property_id) {
        GUID guid = guid_from_pyobj(guid_obj);
        return query_vendor_property_support(device, guid, static_cast<ULONG>(property_id));
    }, py::arg("device"), py::arg("property_set"), py::arg("property_id"), 
       "Query vendor property support");

    // Logitech Extensions (Windows only)
    m.def("get_logitech_property", &duvc::logitech::get_logitech_property, py::arg("device"), py::arg("property"), 
        "Get Logitech vendor property data");
    m.def("set_logitech_property", &duvc::logitech::set_logitech_property, py::arg("device"), py::arg("property"), py::arg("data"), 
        "Set Logitech vendor property data");
    m.def("supports_logitech_properties", &duvc::logitech::supports_logitech_properties, py::arg("device"), 
        "Check if device supports Logitech vendor properties");

    // Logitech template function specializations for common types
    m.def("get_logitech_property_int", [](const Device& device, duvc::logitech::LogitechProperty prop) {
        return duvc::logitech::get_logitech_property_typed<int>(device, prop);
    }, py::arg("device"), py::arg("property"), "Get Logitech property as integer");

    m.def("set_logitech_property_int", [](const Device& device, duvc::logitech::LogitechProperty prop, int value) {
        return duvc::logitech::set_logitech_property_typed<int>(device, prop, value);
    }, py::arg("device"), py::arg("property"), py::arg("value"), "Set Logitech property from integer");

    m.def("get_logitech_property_uint32", [](const Device& device, duvc::logitech::LogitechProperty prop) {
        return duvc::logitech::get_logitech_property_typed<uint32_t>(device, prop);
    }, py::arg("device"), py::arg("property"), "Get Logitech property as uint32");

    m.def("set_logitech_property_uint32", [](const Device& device, duvc::logitech::LogitechProperty prop, uint32_t value) {
        return duvc::logitech::set_logitech_property_typed<uint32_t>(device, prop, value);
    }, py::arg("device"), py::arg("property"), py::arg("value"), "Set Logitech property from uint32");

    m.def("get_logitech_property_bool", [](const Device& device, duvc::logitech::LogitechProperty prop) {
        return duvc::logitech::get_logitech_property_typed<bool>(device, prop);
    }, py::arg("device"), py::arg("property"), "Get Logitech property as boolean");

    m.def("set_logitech_property_bool", [](const Device& device, duvc::logitech::LogitechProperty prop, bool value) {
        return duvc::logitech::set_logitech_property_typed<bool>(device, prop, value);
    }, py::arg("device"), py::arg("property"), py::arg("value"), "Set Logitech property from boolean");

    // DirectShow Helper Functions (Windows only) 
    m.def("create_dev_enum", &create_dev_enum, "Create DirectShow device enumerator");
    
    m.def("enum_video_devices", [](py::capsule dev_enum) {
        ICreateDevEnum* dev = static_cast<ICreateDevEnum*>(dev_enum.get_pointer());
        auto result = enum_video_devices(dev);
        return py::capsule(result.get(), "IEnumMoniker");
    }, py::arg("dev_enum"), "Enumerate video devices");

    m.def("read_friendly_name", [](py::capsule moniker) {
        IMoniker* mon = static_cast<IMoniker*>(moniker.get_pointer());
        return wstring_to_utf8(read_friendly_name(mon));
    }, py::arg("moniker"), "Read friendly name from device moniker");
    
    m.def("read_device_path", [](py::capsule moniker) {
        IMoniker* mon = static_cast<IMoniker*>(moniker.get_pointer());
        return wstring_to_utf8(read_device_path(mon));
    }, py::arg("moniker"), "Read device path from moniker");
    
    m.def("is_same_device", [](const Device& device, const std::string& name, const std::string& path) {
        return is_same_device(device, utf8_to_wstring(name), utf8_to_wstring(path));
    }, py::arg("device"), py::arg("name"), py::arg("path"), "Check if device matches name and path");

    m.def("open_device_filter", [](const Device& device) {
        auto result = open_device_filter(device);
        return py::capsule(result.get(), "IBaseFilter");
    }, py::arg("device"), "Open device filter");

    // GUID helper functions
    m.def("guid_from_uuid", [](const py::object& uuid_obj) {
        GUID guid = guid_from_pyobj(uuid_obj);
        PyGUID py_guid;
        py_guid.guid = guid;
        return py_guid;
    }, py::arg("uuid"), "Convert Python uuid.UUID to PyGUID");

    // Logitech Constants
    m.attr("LOGITECH_PROPERTY_SET") = py::cast([]() {
        PyGUID py_guid;
        py_guid.guid = duvc::logitech::LOGITECH_PROPERTY_SET;
        return py_guid;
    }(), py::return_value_policy::copy);
#endif

    // Result Helper Functions - Only for copyable types (NO Camera or DeviceCapabilities)
    m.def("Ok_PropSetting", [](const PropSetting& value) { return Ok(value); }, py::arg("value"), 
        "Create successful PropSetting result");
    m.def("Ok_PropRange", [](const PropRange& value) { return Ok(value); }, py::arg("value"), 
        "Create successful PropRange result");
    m.def("Ok_void", []() { return Ok(); }, "Create successful void result");
    // NOTE: Camera and DeviceCapabilities are NOT copyable - removed these helpers
    // m.def("Ok_Camera", [](const Camera& value) { return Ok(value); }, py::arg("value"), 
    //     "Create successful Camera result");
    // m.def("Ok_DeviceCapabilities", [](const DeviceCapabilities& value) { return Ok(value); }, py::arg("value"), 
    //     "Create successful DeviceCapabilities result");
    m.def("Ok_bool", [](bool value) { return Ok(value); }, py::arg("value"), 
        "Create successful bool result");
    m.def("Ok_uint32", [](uint32_t value) { return Ok(value); }, py::arg("value"), 
        "Create successful uint32_t result");
    m.def("Ok_vector_uint8", [](const std::vector<uint8_t>& value) { return Ok(value); }, py::arg("value"), 
        "Create successful vector<uint8_t> result");
    
    // Error helper functions for all types
    m.def("Err_PropSetting", [](ErrorCode code, const std::string& message) { 
        return Err<PropSetting>(code, message); 
    }, py::arg("code"), py::arg("message") = "", "Create error PropSetting result");
    m.def("Err_PropRange", [](ErrorCode code, const std::string& message) { 
        return Err<PropRange>(code, message); 
    }, py::arg("code"), py::arg("message") = "", "Create error PropRange result");
    m.def("Err_void", [](ErrorCode code, const std::string& message) { 
        return Err<void>(code, message); 
    }, py::arg("code"), py::arg("message") = "", "Create error void result");
    // NOTE: Camera and DeviceCapabilities error helpers are also removed for consistency
    // m.def("Err_Camera", [](ErrorCode code, const std::string& message) { 
    //     return Err<Camera>(code, message); 
    // }, py::arg("code"), py::arg("message") = "", "Create error Camera result");
    // m.def("Err_DeviceCapabilities", [](ErrorCode code, const std::string& message) { 
    //     return Err<DeviceCapabilities>(code, message); 
    // }, py::arg("code"), py::arg("message") = "", "Create error DeviceCapabilities result");
    m.def("Err_bool", [](ErrorCode code, const std::string& message) { 
        return Err<bool>(code, message); 
    }, py::arg("code"), py::arg("message") = "", "Create error bool result");
    m.def("Err_uint32", [](ErrorCode code, const std::string& message) { 
        return Err<uint32_t>(code, message); 
    }, py::arg("code"), py::arg("message") = "", "Create error uint32_t result");
    m.def("Err_vector_uint8", [](ErrorCode code, const std::string& message) { 
        return Err<std::vector<uint8_t>>(code, message); 
    }, py::arg("code"), py::arg("message") = "", "Create error vector<uint8_t> result");

    // Python convenience wrappers that throw exceptions instead of returning Results
    m.def("open_camera_or_throw", [](int index) {
        auto result = open_camera(index);
        if (result.is_ok()) {
            // Move the camera instead of copying
            return std::make_shared<Camera>(std::move(result).value());
        } else {
            throw_duvc_error(result.error());
        }
    }, py::arg("index"), "Open camera by index (throws exception on error)");

    m.def("open_camera_or_throw", [](const Device& device) {
        auto result = open_camera(device);
        if (result.is_ok()) {
            // Move the camera instead of copying
            return std::make_shared<Camera>(std::move(result).value());
        } else {
            throw_duvc_error(result.error());
        }
    }, py::arg("device"), "Open camera by device (throws exception on error)");

    m.def("get_device_capabilities_or_throw", [](const Device& device) {
        auto result = get_device_capabilities(device);
        if (result.is_ok()) {
            // Move the DeviceCapabilities instead of copying
            return std::move(result).value();
        } else {
            throw_duvc_error(result.error());
        }
    }, py::arg("device"), "Get device capabilities (throws exception on error)");

    m.def("get_device_capabilities_or_throw", [](int device_index) {
        auto result = get_device_capabilities(device_index);
        if (result.is_ok()) {
            // Move the DeviceCapabilities instead of copying
            return std::move(result).value();
        } else {
            throw_duvc_error(result.error());
        }
    }, py::arg("device_index"), "Get device capabilities by index (throws exception on error)");

    // =========================================================================
    // Module Metadata and Type Aliases
    // =========================================================================

    // Module metadata
    m.attr("__version__") = "2.0.0";
    m.attr("__author__") = "allanhanan";
    m.attr("__email__") = "allan.hanan04@gmail.com";

    // Type aliases documentation
    m.attr("__type_aliases__") = py::dict(
        py::arg("DeviceChangeCallback") = "function(bool added, str device_path)", 
        py::arg("LogCallback") = "function(LogLevel level, str message)");

    // Logging macro constants
    m.attr("LOG_DEBUG_ENABLED") = true;
    m.attr("LOG_INFO_ENABLED") = true;
    m.attr("LOG_WARNING_ENABLED") = true;
    m.attr("LOG_ERROR_ENABLED") = true;
    m.attr("LOG_CRITICAL_ENABLED") = true;

    // Exception registration
    py::register_exception<std::runtime_error>(m, "DuvcRuntimeError");

    // Platform identification
#ifdef _WIN32
    m.attr("_is_windows") = true;
#else
    m.attr("_is_windows") = false;
#endif

    // Usage example documentation
    m.def("__example_usage", []() {
        return R"(
import duvc_ctl

# List all devices
devices = duvc_ctl.list_devices()
if not devices:
    print("No cameras found")
    exit()

# Open first camera  
camera_result = duvc_ctl.open_camera(devices[0])
if camera_result.is_ok():
    camera = camera_result.value()
    
    if camera.is_valid():
        # Get current pan value
        pan_result = camera.get(duvc_ctl.CamProp.Pan)
        if pan_result.is_ok():
            setting = pan_result.value()
            print(f"Pan: {setting.value} (mode: {duvc_ctl.to_string(setting.mode)})

        # Set pan to center position
        center_setting = duvc_ctl.PropSetting(0, duvc_ctl.CamMode.Manual)
        set_result = camera.set(duvc_ctl.CamProp.Pan, center_setting)
        if set_result.is_ok():
            print("Pan centered successfully")
        else:
            print(f"Failed to set pan: {set_result.error().description()}")

        # Use device capabilities
        caps_result = duvc_ctl.get_device_capabilities(devices[0])
        if caps_result.is_ok():
            caps = caps_result.value()
            supported_props = caps.supported_camera_properties()
            print(f"Supported camera properties: {[duvc_ctl.to_string(p) for p in supported_props]}")
    else:
        print("Camera not valid")
else:
    print(f"Failed to open camera: {camera_result.error().description()}")
)";
    }, "Get example usage code");
}
