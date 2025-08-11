#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/chrono.h>
#include "duvc-ctl/core.h"
#include "duvc-ctl/defs.h"

namespace py = pybind11;

PYBIND11_MODULE(_duvc_ctl, m) {
    m.doc() = "duvc-ctl: DirectShow UVC Camera Control Library";

    
    // Device struct
    py::class_<duvc::Device>(m, "Device")
        .def(py::init<>())
        .def_readwrite("name", &duvc::Device::name)
        .def_readwrite("path", &duvc::Device::path)
        .def("__repr__", [](const duvc::Device& d) {
            return "<Device(name='" + std::string(d.name.begin(), d.name.end()) + "')>";
        });
    
    // Enums
    py::enum_<duvc::CamMode>(m, "CamMode")
        .value("Auto", duvc::CamMode::Auto)
        .value("Manual", duvc::CamMode::Manual);
    
    py::enum_<duvc::CamProp>(m, "CamProp")
        .value("Pan", duvc::CamProp::Pan)
        .value("Tilt", duvc::CamProp::Tilt)
        .value("Roll", duvc::CamProp::Roll)
        .value("Zoom", duvc::CamProp::Zoom)
        .value("Exposure", duvc::CamProp::Exposure)
        .value("Iris", duvc::CamProp::Iris)
        .value("Focus", duvc::CamProp::Focus)
        .value("ScanMode", duvc::CamProp::ScanMode)
        .value("Privacy", duvc::CamProp::Privacy)
        .value("PanRelative", duvc::CamProp::PanRelative)
        .value("TiltRelative", duvc::CamProp::TiltRelative)
        .value("RollRelative", duvc::CamProp::RollRelative)
        .value("ZoomRelative", duvc::CamProp::ZoomRelative)
        .value("ExposureRelative", duvc::CamProp::ExposureRelative)
        .value("IrisRelative", duvc::CamProp::IrisRelative)
        .value("FocusRelative", duvc::CamProp::FocusRelative)
        .value("PanTilt", duvc::CamProp::PanTilt)
        .value("PanTiltRelative", duvc::CamProp::PanTiltRelative)
        .value("FocusSimple", duvc::CamProp::FocusSimple)
        .value("DigitalZoom", duvc::CamProp::DigitalZoom)
        .value("DigitalZoomRelative", duvc::CamProp::DigitalZoomRelative)
        .value("BacklightCompensation", duvc::CamProp::BacklightCompensation)
        .value("Lamp", duvc::CamProp::Lamp);
    
    py::enum_<duvc::VidProp>(m, "VidProp")
        .value("Brightness", duvc::VidProp::Brightness)
        .value("Contrast", duvc::VidProp::Contrast)
        .value("Hue", duvc::VidProp::Hue)
        .value("Saturation", duvc::VidProp::Saturation)
        .value("Sharpness", duvc::VidProp::Sharpness)
        .value("Gamma", duvc::VidProp::Gamma)
        .value("ColorEnable", duvc::VidProp::ColorEnable)
        .value("WhiteBalance", duvc::VidProp::WhiteBalance)
        .value("BacklightCompensation", duvc::VidProp::BacklightCompensation)
        .value("Gain", duvc::VidProp::Gain);
    
    // Property structs
    py::class_<duvc::PropSetting>(m, "PropSetting")
        .def(py::init<>())
        .def(py::init<int, duvc::CamMode>())
        .def_readwrite("value", &duvc::PropSetting::value)
        .def_readwrite("mode", &duvc::PropSetting::mode)
        .def("__repr__", [](const duvc::PropSetting& p) {
            return "<PropSetting(value=" + std::to_string(p.value) + 
                   ", mode=" + (p.mode == duvc::CamMode::Auto ? "Auto" : "Manual") + ")>";
        });
    
    py::class_<duvc::PropRange>(m, "PropRange")
        .def(py::init<>())
        .def_readwrite("min", &duvc::PropRange::min)
        .def_readwrite("max", &duvc::PropRange::max)
        .def_readwrite("step", &duvc::PropRange::step)
        .def_readwrite("default_val", &duvc::PropRange::default_val)
        .def_readwrite("default_mode", &duvc::PropRange::default_mode)
        .def("__repr__", [](const duvc::PropRange& r) {
            return "<PropRange(min=" + std::to_string(r.min) + 
                   ", max=" + std::to_string(r.max) + 
                   ", step=" + std::to_string(r.step) + 
                   ", default=" + std::to_string(r.default_val) + ")>";
        });

#ifdef _WIN32
    // Windows-only vendor property struct
    py::class_<duvc::VendorProperty>(m, "VendorProperty")
        .def(py::init<>())
        .def_readwrite("data", &duvc::VendorProperty::data);
#endif
    
    // Main API functions
    m.def("list_devices", &duvc::list_devices, "List all available video devices");
    
    // Camera control functions
    m.def("get_range", py::overload_cast<const duvc::Device&, duvc::CamProp, duvc::PropRange&>(&duvc::get_range),
          "Get camera property range", py::arg("device"), py::arg("property"), py::arg("range"));
    m.def("get", py::overload_cast<const duvc::Device&, duvc::CamProp, duvc::PropSetting&>(&duvc::get),
          "Get camera property value", py::arg("device"), py::arg("property"), py::arg("setting"));
    m.def("set", py::overload_cast<const duvc::Device&, duvc::CamProp, const duvc::PropSetting&>(&duvc::set),
          "Set camera property value", py::arg("device"), py::arg("property"), py::arg("setting"));
    
    // Video processing functions
    m.def("get_range", py::overload_cast<const duvc::Device&, duvc::VidProp, duvc::PropRange&>(&duvc::get_range),
          "Get video property range", py::arg("device"), py::arg("property"), py::arg("range"));
    m.def("get", py::overload_cast<const duvc::Device&, duvc::VidProp, duvc::PropSetting&>(&duvc::get),
          "Get video property value", py::arg("device"), py::arg("property"), py::arg("setting"));
    m.def("set", py::overload_cast<const duvc::Device&, duvc::VidProp, const duvc::PropSetting&>(&duvc::set),
          "Set video property value", py::arg("device"), py::arg("property"), py::arg("setting"));
    
    // Device monitoring
    m.def("register_device_change_callback", &duvc::register_device_change_callback,
          "Register callback for device changes", py::arg("callback"));
    m.def("unregister_device_change_callback", &duvc::unregister_device_change_callback,
          "Unregister device change callback");
    m.def("is_device_connected", &duvc::is_device_connected,
          "Check if device is connected", py::arg("device"));
    
    // Performance optimization
    m.def("clear_connection_cache", &duvc::clear_connection_cache,
          "Clear cached device connections");
    
#ifdef _WIN32
    // Windows-only vendor functions
    m.def("get_vendor_property", &duvc::get_vendor_property,
          "Get vendor-specific property", 
          py::arg("device"), py::arg("property_set"), py::arg("property_id"), py::arg("data"));
    m.def("set_vendor_property", &duvc::set_vendor_property,
          "Set vendor-specific property",
          py::arg("device"), py::arg("property_set"), py::arg("property_id"), py::arg("data"));
    m.def("query_vendor_property_support", &duvc::query_vendor_property_support,
          "Query vendor property support",
          py::arg("device"), py::arg("property_set"), py::arg("property_id"));
#endif

    // String conversion utilities
    m.def("cam_prop_to_string", [](duvc::CamProp p) { return duvc::to_string(p); });
    m.def("vid_prop_to_string", [](duvc::VidProp p) { return duvc::to_string(p); });
    m.def("cam_mode_to_string", [](duvc::CamMode m) { return duvc::to_string(m); });
}
