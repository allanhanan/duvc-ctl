/**
 * @file directshow_impl.cpp
 * @brief DirectShow implementation details
 */

#ifdef _WIN32

#include <duvc-ctl/detail/directshow_impl.h>
#include <duvc-ctl/utils/logging.h>
#include <duvc-ctl/platform/interface.h>  
#include <duvc-ctl/core/result.h>
#include <duvc-ctl/utils/error_decoder.h>

namespace duvc::detail {

// DirectShow property mapping implementation
long DirectShowMapper::map_camera_property(CamProp prop) {
    switch (prop) {
        case CamProp::Pan: return 0L; // CameraControl_Pan
        case CamProp::Tilt: return 1L; // CameraControl_Tilt
        case CamProp::Roll: return 2L; // CameraControl_Roll
        case CamProp::Zoom: return 3L; // CameraControl_Zoom
        case CamProp::Exposure: return 4L; // CameraControl_Exposure
        case CamProp::Iris: return 5L; // CameraControl_Iris
        case CamProp::Focus: return 6L; // CameraControl_Focus
        case CamProp::ScanMode: return 7L; // CameraControl_ScanMode
        case CamProp::Privacy: return 8L; // CameraControl_Privacy
        case CamProp::PanRelative: return 9L; // CameraControl_PanRelative
        case CamProp::TiltRelative: return 10L; // CameraControl_TiltRelative
        case CamProp::RollRelative: return 11L; // CameraControl_RollRelative
        case CamProp::ZoomRelative: return 12L; // CameraControl_ZoomRelative
        case CamProp::ExposureRelative: return 13L; // CameraControl_ExposureRelative
        case CamProp::IrisRelative: return 14L; // CameraControl_IrisRelative
        case CamProp::FocusRelative: return 15L; // CameraControl_FocusRelative
        case CamProp::PanTilt: return 16L; // CameraControl_PanTilt
        case CamProp::PanTiltRelative: return 17L; // CameraControl_PanTiltRelative
        case CamProp::FocusSimple: return 18L; // CameraControl_FocusSimple
        case CamProp::DigitalZoom: return 19L; // CameraControl_DigitalZoom
        case CamProp::DigitalZoomRelative: return 20L; // CameraControl_DigitalZoomRelative
        case CamProp::BacklightCompensation: return 21L; // CameraControl_BacklightCompensation
        case CamProp::Lamp: return 22L; // CameraControl_Lamp
        default: return -1;
    }
}

long DirectShowMapper::map_video_property(VidProp prop) {
    switch (prop) {
        case VidProp::Brightness: return 0L; // VideoProcAmp_Brightness
        case VidProp::Contrast: return 1L; // VideoProcAmp_Contrast
        case VidProp::Hue: return 2L; // VideoProcAmp_Hue
        case VidProp::Saturation: return 3L; // VideoProcAmp_Saturation
        case VidProp::Sharpness: return 4L; // VideoProcAmp_Sharpness
        case VidProp::Gamma: return 5L; // VideoProcAmp_Gamma
        case VidProp::ColorEnable: return 6L; // VideoProcAmp_ColorEnable
        case VidProp::WhiteBalance: return 7L; // VideoProcAmp_WhiteBalance
        case VidProp::BacklightCompensation: return 8L; // VideoProcAmp_BacklightCompensation
        case VidProp::Gain: return 9L; // VideoProcAmp_Gain
        default: return -1;
    }
}

long DirectShowMapper::map_camera_mode_to_flags(CamMode mode, bool is_camera_control) {
    if (is_camera_control) {
        return (mode == CamMode::Auto) ? 0x0001L : 0x0002L; // Auto : Manual flags
    } else {
        return (mode == CamMode::Auto) ? 0x0001L : 0x0002L; // Auto : Manual flags
    }
}

CamMode DirectShowMapper::map_flags_to_camera_mode(long flags, bool is_camera_control) {
    (void)is_camera_control; // Same logic for both
    return (flags & 0x0001L) ? CamMode::Auto : CamMode::Manual;
}

// DirectShow enumerator implementation
DirectShowEnumerator::DirectShowEnumerator() : com_() {
    HRESULT hr = CoCreateInstance(CLSID_SystemDeviceEnum, nullptr, CLSCTX_INPROC_SERVER,
                                  IID_ICreateDevEnum, reinterpret_cast<void**>(dev_enum_.put()));
    if (FAILED(hr)) {
        DUVC_LOG_ERROR("Failed to create DirectShow device enumerator");
        throw std::runtime_error("Failed to create DirectShow device enumerator");
    }
}

DirectShowEnumerator::~DirectShowEnumerator() = default;

std::vector<Device> DirectShowEnumerator::enumerate_devices() {
    std::vector<Device> devices;
    
    if (!dev_enum_) {
        return devices;
    }
    
    com_ptr<IEnumMoniker> enum_moniker;
    HRESULT hr = dev_enum_->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, 
                                                 enum_moniker.put(), 0);
    
    if (hr == S_FALSE || !enum_moniker) {
        // No devices available
        return devices;
    }
    
    if (FAILED(hr)) {
        DUVC_LOG_ERROR("Failed to create video device enumerator");
        return devices;
    }
    
    ULONG fetched = 0;
    com_ptr<IMoniker> moniker;
    while (enum_moniker->Next(1, moniker.put(), &fetched) == S_OK && fetched > 0) {
        try {
            Device device = read_device_info(moniker.get());
            if (!device.name.empty() || !device.path.empty()) {
                devices.push_back(std::move(device));
            }
        } catch (const std::exception& e) {
            DUVC_LOG_WARNING("Failed to read device info: " + std::string(e.what()));
        }
        
        moniker.reset();
    }
    
    DUVC_LOG_INFO("Enumerated " + std::to_string(devices.size()) + " video devices");
    return devices;
}

bool DirectShowEnumerator::is_device_available(const Device& device) {
    auto devices = enumerate_devices();
    
    for (const auto& dev : devices) {
        // Match by path first (more reliable), then by name
        if (!device.path.empty() && !dev.path.empty()) {
            if (_wcsicmp(device.path.c_str(), dev.path.c_str()) == 0) {
                return true;
            }
        } else if (!device.name.empty() && !dev.name.empty()) {
            if (_wcsicmp(device.name.c_str(), dev.name.c_str()) == 0) {
                return true;
            }
        }
    }
    
    return false;
}

Device DirectShowEnumerator::read_device_info(IMoniker* moniker) {
    Device device;
    
    com_ptr<IPropertyBag> prop_bag;
    HRESULT hr = moniker->BindToStorage(nullptr, nullptr, IID_IPropertyBag,
                                       reinterpret_cast<void**>(prop_bag.put()));
    
    if (SUCCEEDED(hr) && prop_bag) {
        // Read friendly name
        VARIANT var;
        VariantInit(&var);
        
        if (SUCCEEDED(prop_bag->Read(L"FriendlyName", &var, nullptr))) {
            if (var.vt == VT_BSTR && var.bstrVal) {
                device.name.assign(var.bstrVal, SysStringLen(var.bstrVal));
            }
        }
        VariantClear(&var);
        
        // Try to read device path
        if (SUCCEEDED(prop_bag->Read(L"DevicePath", &var, nullptr))) {
            if (var.vt == VT_BSTR && var.bstrVal) {
                device.path.assign(var.bstrVal, SysStringLen(var.bstrVal));
            }
        }
        VariantClear(&var);
    }
    
    // If no device path from property bag, try display name
    if (device.path.empty()) {
        LPOLESTR display_name = nullptr;
        if (SUCCEEDED(moniker->GetDisplayName(nullptr, nullptr, &display_name)) && display_name) {
            device.path.assign(display_name);
            CoTaskMemFree(display_name);
        }
    }
    
    return device;
}

// DirectShow filter implementation
DirectShowFilter::DirectShowFilter(const Device& device) : com_() {
    filter_ = create_filter(device);
}

DirectShowFilter::~DirectShowFilter() = default;

bool DirectShowFilter::is_valid() const {
    return static_cast<bool>(filter_);
}

com_ptr<IAMCameraControl> DirectShowFilter::get_camera_control() {
    if (!filter_) return {};
    
    com_ptr<IAMCameraControl> camera_control;
    HRESULT hr = filter_->QueryInterface(IID_IAMCameraControl,
                                       reinterpret_cast<void**>(camera_control.put()));
    
    if (SUCCEEDED(hr)) {
        return std::move(camera_control);
    }
    return {};
}


com_ptr<IAMVideoProcAmp> DirectShowFilter::get_video_proc_amp() {
    if (!filter_) return {};
    
    com_ptr<IAMVideoProcAmp> video_proc_amp;
    HRESULT hr = filter_->QueryInterface(IID_IAMVideoProcAmp,
                                       reinterpret_cast<void**>(video_proc_amp.put()));
    
    if (SUCCEEDED(hr)) {
        return std::move(video_proc_amp);
    }
    return {};
}


com_ptr<IKsPropertySet> DirectShowFilter::get_property_set() {
    if (!filter_) return {};
    
    com_ptr<IKsPropertySet> property_set;
    HRESULT hr = filter_->QueryInterface(IID_IKsPropertySet,
                                       reinterpret_cast<void**>(property_set.put()));
    
    if (SUCCEEDED(hr)) {
        return std::move(property_set);
    }
    return {};
}


com_ptr<IBaseFilter> DirectShowFilter::create_filter(const Device& device) {
    DirectShowEnumerator enumerator;
    
    com_ptr<IEnumMoniker> enum_moniker;
    HRESULT hr = enumerator.dev_enum_->CreateClassEnumerator(CLSID_VideoInputDeviceCategory,
                                                            enum_moniker.put(), 0);
    
    if (FAILED(hr) || !enum_moniker) {
        return {};
    }
    
    ULONG fetched = 0;
    com_ptr<IMoniker> moniker;
    while (enum_moniker->Next(1, moniker.put(), &fetched) == S_OK && fetched > 0) {
        Device current_device = enumerator.read_device_info(moniker.get());
        
        // Check if this is the device we're looking for
        bool match = false;
        if (!device.path.empty() && !current_device.path.empty()) {
            match = (_wcsicmp(device.path.c_str(), current_device.path.c_str()) == 0);
        } else if (!device.name.empty() && !current_device.name.empty()) {
            match = (_wcsicmp(device.name.c_str(), current_device.name.c_str()) == 0);
        }
        
        if (match) {
            // Found the device - bind to filter
            com_ptr<IBaseFilter> filter;
            hr = moniker->BindToObject(nullptr, nullptr, IID_IBaseFilter,
                                      reinterpret_cast<void**>(filter.put()));
            
            if (SUCCEEDED(hr)) {
                return filter;
            }
        }
        
        moniker.reset();
    }
    
    return {}; // Device not found
}

/**
 * @brief DirectShow device connection implementation for platform interface
 */
class DirectShowDeviceConnection : public IDeviceConnection {
public:
    explicit DirectShowDeviceConnection(const Device& device) 
        : filter_(device) {}
    
    bool is_valid() const override {
        return filter_.is_valid();
    }
    
    Result<PropSetting> get_camera_property(CamProp prop) override {
        auto cam_ctrl = filter_.get_camera_control();
        if (!cam_ctrl) {
            return Err<PropSetting>(ErrorCode::PropertyNotSupported, "Camera control not available");
        }
        
        long prop_id = DirectShowMapper::map_camera_property(prop);
        if (prop_id < 0) {
            return Err<PropSetting>(ErrorCode::PropertyNotSupported, "Property not supported");
        }
        
        long value = 0, flags = 0;
        HRESULT hr = cam_ctrl->Get(prop_id, &value, &flags);
        
        if (FAILED(hr)) {
            return Err<PropSetting>(ErrorCode::SystemError, "Failed to get camera property");
        }
        
        PropSetting setting;
        setting.value = static_cast<int>(value);
        setting.mode = DirectShowMapper::map_flags_to_camera_mode(flags, true);
        
        return Ok(setting);
    }
    
    Result<void> set_camera_property(CamProp prop, const PropSetting& setting) override {
        auto cam_ctrl = filter_.get_camera_control();
        if (!cam_ctrl) {
            return Err<void>(ErrorCode::PropertyNotSupported, "Camera control not available");
        }
        
        long prop_id = DirectShowMapper::map_camera_property(prop);
        if (prop_id < 0) {
            return Err<void>(ErrorCode::PropertyNotSupported, "Property not supported");
        }
        
        long flags = DirectShowMapper::map_camera_mode_to_flags(setting.mode, true);
        HRESULT hr = cam_ctrl->Set(prop_id, static_cast<long>(setting.value), flags);
        
        if (FAILED(hr)) {
            return Err<void>(ErrorCode::SystemError, "Failed to set camera property");
        }
        
        return Ok();
    }
    
    Result<PropRange> get_camera_property_range(CamProp prop) override {
        auto cam_ctrl = filter_.get_camera_control();
        if (!cam_ctrl) {
            return Err<PropRange>(ErrorCode::PropertyNotSupported, "Camera control not available");
        }
        
        long prop_id = DirectShowMapper::map_camera_property(prop);
        if (prop_id < 0) {
            return Err<PropRange>(ErrorCode::PropertyNotSupported, "Property not supported");
        }
        
        long min = 0, max = 0, step = 0, default_val = 0, flags = 0;
        HRESULT hr = cam_ctrl->GetRange(prop_id, &min, &max, &step, &default_val, &flags);
        
        if (FAILED(hr)) {
            return Err<PropRange>(ErrorCode::SystemError, "Failed to get camera property range");
        }
        
        PropRange range;
        range.min = static_cast<int>(min);
        range.max = static_cast<int>(max);
        range.step = static_cast<int>(step);
        range.default_val = static_cast<int>(default_val);
        range.default_mode = DirectShowMapper::map_flags_to_camera_mode(flags, true);
        
        return Ok(range);
    }
    
    Result<PropSetting> get_video_property(VidProp prop) override {
        auto vid_proc = filter_.get_video_proc_amp();
        if (!vid_proc) {
            return Err<PropSetting>(ErrorCode::PropertyNotSupported, "Video processing not available");
        }
        
        long prop_id = DirectShowMapper::map_video_property(prop);
        if (prop_id < 0) {
            return Err<PropSetting>(ErrorCode::PropertyNotSupported, "Property not supported");
        }
        
        long value = 0, flags = 0;
        HRESULT hr = vid_proc->Get(prop_id, &value, &flags);
        
        if (FAILED(hr)) {
            return Err<PropSetting>(ErrorCode::SystemError, "Failed to get video property");
        }
        
        PropSetting setting;
        setting.value = static_cast<int>(value);
        setting.mode = DirectShowMapper::map_flags_to_camera_mode(flags, false);
        
        return Ok(setting);
    }
    
    Result<void> set_video_property(VidProp prop, const PropSetting& setting) override {
        auto vid_proc = filter_.get_video_proc_amp();
        if (!vid_proc) {
            return Err<void>(ErrorCode::PropertyNotSupported, "Video processing not available");
        }
        
        long prop_id = DirectShowMapper::map_video_property(prop);
        if (prop_id < 0) {
            return Err<void>(ErrorCode::PropertyNotSupported, "Property not supported");
        }
        
        long flags = DirectShowMapper::map_camera_mode_to_flags(setting.mode, false);
        HRESULT hr = vid_proc->Set(prop_id, static_cast<long>(setting.value), flags);
        
        if (FAILED(hr)) {
            return Err<void>(ErrorCode::SystemError, "Failed to set video property");
        }
        
        return Ok();
    }
    
    Result<PropRange> get_video_property_range(VidProp prop) override {
        auto vid_proc = filter_.get_video_proc_amp();
        if (!vid_proc) {
            return Err<PropRange>(ErrorCode::PropertyNotSupported, "Video processing not available");
        }
        
        long prop_id = DirectShowMapper::map_video_property(prop);
        if (prop_id < 0) {
            return Err<PropRange>(ErrorCode::PropertyNotSupported, "Property not supported");
        }
        
        long min = 0, max = 0, step = 0, default_val = 0, flags = 0;
        HRESULT hr = vid_proc->GetRange(prop_id, &min, &max, &step, &default_val, &flags);
        
        if (FAILED(hr)) {
            return Err<PropRange>(ErrorCode::SystemError, "Failed to get video property range");
        }
        
        PropRange range;
        range.min = static_cast<int>(min);
        range.max = static_cast<int>(max);
        range.step = static_cast<int>(step);
        range.default_val = static_cast<int>(default_val);
        range.default_mode = DirectShowMapper::map_flags_to_camera_mode(flags, false);
        
        return Ok(range);
    }
    
private:
    DirectShowFilter filter_;
};

std::unique_ptr<IDeviceConnection> create_directshow_connection(const Device& device) {
    auto connection = std::make_unique<DirectShowDeviceConnection>(device);
    if (connection->is_valid()) {
        return std::move(connection);
    }
    return nullptr;
}

} // namespace duvc::detail

// -----------------------------------------------------------------------------
// Public helper needed by vendor utilities
// -----------------------------------------------------------------------------
namespace duvc {

detail::com_ptr<IBaseFilter> open_device_filter(const Device& dev)
{
    detail::DirectShowFilter f(dev);
    if (f.is_valid())
        return f.extract();          //  <-- move, no copy
    return {};
}

}

#endif // _WIN32
