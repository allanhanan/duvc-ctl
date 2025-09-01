/**
 * @file connection_pool.cpp
 * @brief Windows DirectShow connection pooling implementation
 */

#ifdef _WIN32

#include <duvc-ctl/platform/windows/connection_pool.h>
#include <duvc-ctl/detail/com_helpers.h>
#include <duvc-ctl/core/device.h>
#include <mutex>
#include <unordered_map>
#include <memory>

#include <dshow.h>
#include <strmif.h>

// DirectShow control interfaces
#ifndef __AMCAMERACONTROL__
#define CameraControl_Pan 0L
#define CameraControl_Tilt 1L
#define CameraControl_Roll 2L
#define CameraControl_Zoom 3L
#define CameraControl_Exposure 4L
#define CameraControl_Iris 5L
#define CameraControl_Focus 6L
#define CameraControl_ScanMode 7L
#define CameraControl_Privacy 8L
#define CameraControl_PanRelative 9L
#define CameraControl_TiltRelative 10L
#define CameraControl_RollRelative 11L
#define CameraControl_ZoomRelative 12L
#define CameraControl_ExposureRelative 13L
#define CameraControl_IrisRelative 14L
#define CameraControl_FocusRelative 15L
#define CameraControl_PanTilt 16L
#define CameraControl_PanTiltRelative 17L
#define CameraControl_FocusSimple 18L
#define CameraControl_DigitalZoom 19L
#define CameraControl_DigitalZoomRelative 20L
#define CameraControl_BacklightCompensation 21L
#define CameraControl_Lamp 22L
#define CameraControl_Flags_Auto 0x0001
#define CameraControl_Flags_Manual 0x0002
#endif

#ifndef __AMVIDEOPROCAMP__
#define VideoProcAmp_Brightness 0
#define VideoProcAmp_Contrast 1
#define VideoProcAmp_Hue 2
#define VideoProcAmp_Saturation 3
#define VideoProcAmp_Sharpness 4
#define VideoProcAmp_Gamma 5
#define VideoProcAmp_ColorEnable 6
#define VideoProcAmp_WhiteBalance 7
#define VideoProcAmp_BacklightCompensation 8
#define VideoProcAmp_Gain 9
#define VideoProcAmp_Flags_Auto 0x0001
#define VideoProcAmp_Flags_Manual 0x0002
#endif

#ifdef _MSC_VER
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "oleaut32.lib")
#pragma comment(lib, "strmiids.lib")
#endif

namespace duvc {

using namespace detail;

// Connection cache globals
static std::mutex g_cache_mutex;
static std::unordered_map<std::wstring, std::unique_ptr<DeviceConnection>> g_connection_cache;

// Forward declarations for DirectShow enumeration
extern com_ptr<ICreateDevEnum> create_dev_enum();
extern com_ptr<IEnumMoniker> enum_video_devices(ICreateDevEnum* dev);
extern std::wstring read_friendly_name(IMoniker* mon);
extern std::wstring read_device_path(IMoniker* mon);
extern bool is_same_device(const Device& d, const std::wstring& name, const std::wstring& path);

// DirectShow interface helpers
static com_ptr<IBaseFilter> bind_to_filter(IMoniker* mon) {
    com_ptr<IBaseFilter> f;
    HRESULT hr = mon->BindToObject(nullptr, nullptr, IID_IBaseFilter, 
                                   reinterpret_cast<void**>(f.put()));
    if (FAILED(hr)) throw_hr(hr, "BindToObject(IBaseFilter)");
    return f;
}

static com_ptr<IAMCameraControl> get_cam_ctrl(IBaseFilter* f) {
    com_ptr<IAMCameraControl> cam;
    if (FAILED(f->QueryInterface(IID_IAMCameraControl, reinterpret_cast<void**>(cam.put())))) {
        return {};
    }
    return cam;
}

static com_ptr<IAMVideoProcAmp> get_vproc(IBaseFilter* f) {
    com_ptr<IAMVideoProcAmp> vp;
    if (FAILED(f->QueryInterface(IID_IAMVideoProcAmp, reinterpret_cast<void**>(vp.put())))) {
        return {};
    }
    return vp;
}

static com_ptr<IBaseFilter> open_device_filter(const Device& dev) {
    extern com_ptr<ICreateDevEnum> create_dev_enum();
    extern com_ptr<IEnumMoniker> enum_video_devices(ICreateDevEnum* dev);
    
    auto de = create_dev_enum();
    auto en = enum_video_devices(de.get());
    if (!en) throw std::runtime_error("No video devices available");
    
    ULONG fetched = 0;
    com_ptr<IMoniker> mon;
    while (en->Next(1, mon.put(), &fetched) == S_OK && fetched) {
        auto fname = read_friendly_name(mon.get());
        auto dpath = read_device_path(mon.get());
        if (is_same_device(dev, fname, dpath)) {
            return bind_to_filter(mon.get());
        }
        mon.reset();
    }
    
    throw std::runtime_error("Device not found");
}

// Property mapping helpers
static long camprop_to_dshow(CamProp p) {
    switch (p) {
        case CamProp::Pan: return CameraControl_Pan;
        case CamProp::Tilt: return CameraControl_Tilt;
        case CamProp::Roll: return CameraControl_Roll;
        case CamProp::Zoom: return CameraControl_Zoom;
        case CamProp::Exposure: return CameraControl_Exposure;
        case CamProp::Iris: return CameraControl_Iris;
        case CamProp::Focus: return CameraControl_Focus;
        case CamProp::ScanMode: return CameraControl_ScanMode;
        case CamProp::Privacy: return CameraControl_Privacy;
        case CamProp::PanRelative: return CameraControl_PanRelative;
        case CamProp::TiltRelative: return CameraControl_TiltRelative;
        case CamProp::RollRelative: return CameraControl_RollRelative;
        case CamProp::ZoomRelative: return CameraControl_ZoomRelative;
        case CamProp::ExposureRelative: return CameraControl_ExposureRelative;
        case CamProp::IrisRelative: return CameraControl_IrisRelative;
        case CamProp::FocusRelative: return CameraControl_FocusRelative;
        case CamProp::PanTilt: return CameraControl_PanTilt;
        case CamProp::PanTiltRelative: return CameraControl_PanTiltRelative;
        case CamProp::FocusSimple: return CameraControl_FocusSimple;
        case CamProp::DigitalZoom: return CameraControl_DigitalZoom;
        case CamProp::DigitalZoomRelative: return CameraControl_DigitalZoomRelative;
        case CamProp::BacklightCompensation: return CameraControl_BacklightCompensation;
        case CamProp::Lamp: return CameraControl_Lamp;
        default: return -1;
    }
}

static long vidprop_to_dshow(VidProp p) {
    switch (p) {
        case VidProp::Brightness: return VideoProcAmp_Brightness;
        case VidProp::Contrast: return VideoProcAmp_Contrast;
        case VidProp::Hue: return VideoProcAmp_Hue;
        case VidProp::Saturation: return VideoProcAmp_Saturation;
        case VidProp::Sharpness: return VideoProcAmp_Sharpness;
        case VidProp::Gamma: return VideoProcAmp_Gamma;
        case VidProp::ColorEnable: return VideoProcAmp_ColorEnable;
        case VidProp::WhiteBalance: return VideoProcAmp_WhiteBalance;
        case VidProp::BacklightCompensation: return VideoProcAmp_BacklightCompensation;
        case VidProp::Gain: return VideoProcAmp_Gain;
        default: return -1;
    }
}

static long to_flag(CamMode m, bool is_camera_control) {
    if (is_camera_control) {
        return (m == CamMode::Auto) ? CameraControl_Flags_Auto : CameraControl_Flags_Manual;
    } else {
        return (m == CamMode::Auto) ? VideoProcAmp_Flags_Auto : VideoProcAmp_Flags_Manual;
    }
}

static CamMode from_flag(long flag, bool is_camera_control) {
    if (is_camera_control) {
        return (flag & CameraControl_Flags_Auto) ? CamMode::Auto : CamMode::Manual;
    } else {
        return (flag & VideoProcAmp_Flags_Auto) ? CamMode::Auto : CamMode::Manual;
    }
}

// DeviceConnection implementation
DeviceConnection::DeviceConnection(const Device& dev)
    : com_(std::make_unique<com_apartment>())
    , filter_(nullptr)
    , cam_ctrl_(nullptr)
    , vid_proc_(nullptr) {
    
    try {
        auto filter = open_device_filter(dev);
        if (filter) {
            auto cam_ctrl = get_cam_ctrl(filter.get());
            auto vid_proc = get_vproc(filter.get());
            
            // Store as raw pointers but keep references
            filter_ = new com_ptr<IBaseFilter>(std::move(filter));
            cam_ctrl_ = new com_ptr<IAMCameraControl>(std::move(cam_ctrl));
            vid_proc_ = new com_ptr<IAMVideoProcAmp>(std::move(vid_proc));
        }
    } catch (...) {
        filter_ = nullptr;
    }
}

DeviceConnection::~DeviceConnection() {
    delete static_cast<com_ptr<IBaseFilter>*>(filter_);
    delete static_cast<com_ptr<IAMCameraControl>*>(cam_ctrl_);
    delete static_cast<com_ptr<IAMVideoProcAmp>*>(vid_proc_);
}

bool DeviceConnection::get(CamProp prop, PropSetting& val) {
    auto* cam_ctrl = static_cast<com_ptr<IAMCameraControl>*>(cam_ctrl_);
    if (!cam_ctrl || !*cam_ctrl) return false;
    
    long pid = camprop_to_dshow(prop);
    if (pid < 0) return false;
    
    long value = 0, flags = 0;
    HRESULT hr = (*cam_ctrl)->Get(pid, &value, &flags);
    if (FAILED(hr)) return false;
    
    val.value = static_cast<int>(value);
    val.mode = from_flag(flags, true);
    return true;
}

bool DeviceConnection::set(CamProp prop, const PropSetting& val) {
    auto* cam_ctrl = static_cast<com_ptr<IAMCameraControl>*>(cam_ctrl_);
    if (!cam_ctrl || !*cam_ctrl) return false;
    
    long pid = camprop_to_dshow(prop);
    if (pid < 0) return false;
    
    long flags = to_flag(val.mode, true);
    HRESULT hr = (*cam_ctrl)->Set(pid, static_cast<long>(val.value), flags);
    return SUCCEEDED(hr);
}

bool DeviceConnection::get(VidProp prop, PropSetting& val) {
    auto* vid_proc = static_cast<com_ptr<IAMVideoProcAmp>*>(vid_proc_);
    if (!vid_proc || !*vid_proc) return false;
    
    long pid = vidprop_to_dshow(prop);
    if (pid < 0) return false;
    
    long value = 0, flags = 0;
    HRESULT hr = (*vid_proc)->Get(pid, &value, &flags);
    if (FAILED(hr)) return false;
    
    val.value = static_cast<int>(value);
    val.mode = from_flag(flags, false);
    return true;
}

bool DeviceConnection::set(VidProp prop, const PropSetting& val) {
    auto* vid_proc = static_cast<com_ptr<IAMVideoProcAmp>*>(vid_proc_);
    if (!vid_proc || !*vid_proc) return false;
    
    long pid = vidprop_to_dshow(prop);
    if (pid < 0) return false;
    
    long flags = to_flag(val.mode, false);
    HRESULT hr = (*vid_proc)->Set(pid, static_cast<long>(val.value), flags);
    return SUCCEEDED(hr);
}

bool DeviceConnection::get_range(CamProp prop, PropRange& range) {
    auto* cam_ctrl = static_cast<com_ptr<IAMCameraControl>*>(cam_ctrl_);
    if (!cam_ctrl || !*cam_ctrl) return false;
    
    long pid = camprop_to_dshow(prop);
    if (pid < 0) return false;
    
    long min = 0, max = 0, step = 0, def = 0, flags = 0;
    HRESULT hr = (*cam_ctrl)->GetRange(pid, &min, &max, &step, &def, &flags);
    if (FAILED(hr)) return false;
    
    range.min = static_cast<int>(min);
    range.max = static_cast<int>(max);
    range.step = static_cast<int>(step);
    range.default_val = static_cast<int>(def);
    range.default_mode = from_flag(flags, true);
    return true;
}

bool DeviceConnection::get_range(VidProp prop, PropRange& range) {
    auto* vid_proc = static_cast<com_ptr<IAMVideoProcAmp>*>(vid_proc_);
    if (!vid_proc || !*vid_proc) return false;
    
    long pid = vidprop_to_dshow(prop);
    if (pid < 0) return false;
    
    long min = 0, max = 0, step = 0, def = 0, flags = 0;
    HRESULT hr = (*vid_proc)->GetRange(pid, &min, &max, &step, &def, &flags);
    if (FAILED(hr)) return false;
    
    range.min = static_cast<int>(min);
    range.max = static_cast<int>(max);
    range.step = static_cast<int>(step);
    range.default_val = static_cast<int>(def);
    range.default_mode = from_flag(flags, false);
    return true;
}

// Connection pool management
DeviceConnection* get_cached_connection(const Device& dev) {
    std::lock_guard<std::mutex> lock(g_cache_mutex);
    std::wstring key = dev.path.empty() ? dev.name : dev.path;
    
    auto it = g_connection_cache.find(key);
    if (it != g_connection_cache.end() && it->second->is_valid()) {
        return it->second.get();
    }
    
    // Create new connection
    auto conn = std::make_unique<DeviceConnection>(dev);
    if (!conn->is_valid()) return nullptr;
    
    DeviceConnection* result = conn.get();
    g_connection_cache[key] = std::move(conn);
    return result;
}

void release_cached_connection(const Device& dev) {
    std::lock_guard<std::mutex> lock(g_cache_mutex);
    std::wstring key = dev.path.empty() ? dev.name : dev.path;
    g_connection_cache.erase(key);
}

void clear_connection_cache_impl() {
    std::lock_guard<std::mutex> lock(g_cache_mutex);
    g_connection_cache.clear();
}

} // namespace duvc

#endif // _WIN32
