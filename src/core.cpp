#include "duvc-ctl/core.h"
#include "duvc-ctl/defs.h"

#ifdef _WIN32

#ifndef NOMINMAX
#define NOMINMAX
#endif

#include <windows.h>
#include <dshow.h>
#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <stdexcept>
#include <comdef.h>
#include <strmif.h>
#include <control.h>
#include <uuids.h>
#include <dbt.h>
#include <ks.h>
#include <ksproxy.h>
#include <unordered_map>
#include <memory>
#include <mutex>

// Fallback IAMCameraControl (rarely needed but safe)
#ifndef __AMCAMERACONTROL__
#define CameraControl_Pan                     0L
#define CameraControl_Tilt                    1L
#define CameraControl_Roll                    2L
#define CameraControl_Zoom                    3L
#define CameraControl_Exposure                4L
#define CameraControl_Iris                    5L
#define CameraControl_Focus                   6L
#define CameraControl_ScanMode                7L
#define CameraControl_Privacy                 8L
#define CameraControl_PanRelative             9L
#define CameraControl_TiltRelative            10L
#define CameraControl_RollRelative            11L
#define CameraControl_ZoomRelative            12L
#define CameraControl_ExposureRelative        13L
#define CameraControl_IrisRelative            14L
#define CameraControl_FocusRelative           15L
#define CameraControl_PanTilt                 16L
#define CameraControl_PanTiltRelative         17L
#define CameraControl_FocusSimple             18L
#define CameraControl_DigitalZoom             19L
#define CameraControl_DigitalZoomRelative     20L
#define CameraControl_BacklightCompensation   21L
#define CameraControl_Lamp                    22L
#define CameraControl_Flags_Auto              0x0001
#define CameraControl_Flags_Manual            0x0002
#endif

// Fallback IAMVideoProcAmp
#ifndef __AMVIDEOPROCAMP__
#define VideoProcAmp_Brightness               0
#define VideoProcAmp_Contrast                 1
#define VideoProcAmp_Hue                      2
#define VideoProcAmp_Saturation               3
#define VideoProcAmp_Sharpness                4
#define VideoProcAmp_Gamma                    5
#define VideoProcAmp_ColorEnable              6
#define VideoProcAmp_WhiteBalance             7
#define VideoProcAmp_BacklightCompensation    8
#define VideoProcAmp_Gain                     9
#define VideoProcAmp_Flags_Auto               0x0001
#define VideoProcAmp_Flags_Manual             0x0002
#endif

#ifdef _MSC_VER
#pragma comment(lib, "ole32.lib")
#pragma comment(lib, "oleaut32.lib")
#pragma comment(lib, "strmiids.lib")
#endif

namespace duvc {

template<typename T>
class com_ptr {
public:
    com_ptr() noexcept = default;
    explicit com_ptr(T* p) noexcept : p_(p) {}
    ~com_ptr() { reset(); }
    
    com_ptr(const com_ptr&) = delete;
    com_ptr& operator=(const com_ptr&) = delete;
    
    com_ptr(com_ptr&& o) noexcept : p_(o.p_) { o.p_ = nullptr; }
    com_ptr& operator=(com_ptr&& o) noexcept {
        if (this != &o) { reset(); p_ = o.p_; o.p_ = nullptr; }
        return *this;
    }
    
    T* get() const noexcept { return p_; }
    T** put() noexcept { reset(); return &p_; }
    T* operator->() const noexcept { return p_; }
    explicit operator bool() const noexcept { return p_ != nullptr; }
    void reset() noexcept { if (p_) { p_->Release(); p_ = nullptr; } }
    
private:
    T* p_ = nullptr;
};

[[maybe_unused]] static std::string wide_to_utf8(const wchar_t* ws) {
    if (!ws) return {};
    int sz = WideCharToMultiByte(CP_UTF8, 0, ws, -1, nullptr, 0, nullptr, nullptr);
    std::string out(sz > 0 ? sz - 1 : 0, '\0');
    if (sz > 0) WideCharToMultiByte(CP_UTF8, 0, ws, -1, out.data(), sz, nullptr, nullptr);
    return out;
}

static void throw_hr(HRESULT hr, const char* where) {
    _com_error err(hr);
    std::ostringstream oss;
    oss << where << " failed (hr=0x" << std::hex << hr << ")";
    if (err.ErrorMessage()) {
        #ifdef UNICODE
        oss << " - " << wide_to_utf8(err.ErrorMessage());
        #else
        oss << " - " << err.ErrorMessage();
        #endif
    }
    throw std::runtime_error(oss.str());
}

class com_apartment {
public:
    com_apartment() {
        hr_ = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
        if (FAILED(hr_) && hr_ != RPC_E_CHANGED_MODE) {
            throw_hr(hr_, "CoInitializeEx");
        }
    }
    
    ~com_apartment() {
        if (SUCCEEDED(hr_)) CoUninitialize();
    }
    
private:
    HRESULT hr_{ S_OK };
};

// Device monitoring globals
static DeviceChangeCallback g_device_callback = nullptr;
static HWND g_notification_window = nullptr;
static HDEVNOTIFY g_device_notify = nullptr;

// Connection pool globals
static std::mutex g_cache_mutex;
static std::unordered_map<std::wstring, std::unique_ptr<DeviceConnection>> g_connection_cache;

// Window procedure for device notifications
static LRESULT CALLBACK device_wndproc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    if (msg == WM_DEVICECHANGE && g_device_callback) {
        if (wParam == DBT_DEVICEARRIVAL || wParam == DBT_DEVICEREMOVECOMPLETE) {
            PDEV_BROADCAST_HDR hdr = reinterpret_cast<PDEV_BROADCAST_HDR>(lParam);
            if (hdr && hdr->dbch_devicetype == DBT_DEVTYP_DEVICEINTERFACE) {
                PDEV_BROADCAST_DEVICEINTERFACE dev = reinterpret_cast<PDEV_BROADCAST_DEVICEINTERFACE>(lParam);
                bool added = (wParam == DBT_DEVICEARRIVAL);
                std::wstring device_path = dev->dbcc_name;
                g_device_callback(added, device_path);
            }
        }
    }
    return DefWindowProc(hwnd, msg, wParam, lParam);
}



static com_ptr<ICreateDevEnum> create_dev_enum() {
    com_ptr<ICreateDevEnum> dev;
    HRESULT hr = CoCreateInstance(CLSID_SystemDeviceEnum, nullptr, CLSCTX_INPROC_SERVER,
                                  IID_ICreateDevEnum, reinterpret_cast<void**>(dev.put()));
    if (FAILED(hr)) throw_hr(hr, "CoCreateInstance(SystemDeviceEnum)");
    return dev;
}

static com_ptr<IEnumMoniker> enum_video_devices(ICreateDevEnum* dev) {
    com_ptr<IEnumMoniker> e;
    HRESULT hr = dev->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, e.put(), 0);
    if (hr == S_FALSE) return {}; // none
    if (FAILED(hr)) throw_hr(hr, "CreateClassEnumerator(VideoInputDeviceCategory)");
    return e;
}

static std::wstring read_prop_bstr(IPropertyBag* bag, const wchar_t* key) {
    VARIANT v; VariantInit(&v);
    std::wstring res;
    if (SUCCEEDED(bag->Read(key, &v, nullptr)) && v.vt == VT_BSTR && v.bstrVal) {
        res.assign(v.bstrVal, SysStringLen(v.bstrVal));
    }
    VariantClear(&v);
    return res;
}

static std::wstring read_friendly_name(IMoniker* mon) {
    com_ptr<IPropertyBag> bag;
    HRESULT hr = mon->BindToStorage(nullptr, nullptr, IID_IPropertyBag, reinterpret_cast<void**>(bag.put()));
    if (FAILED(hr)) return L"";
    auto name = read_prop_bstr(bag.get(), L"FriendlyName");
    return name.empty() ? L"" : name;
}

static std::wstring read_device_path(IMoniker* mon) {
    com_ptr<IPropertyBag> bag;
    if (SUCCEEDED(mon->BindToStorage(nullptr, nullptr, IID_IPropertyBag, reinterpret_cast<void**>(bag.put())))) {
        auto dp = read_prop_bstr(bag.get(), L"DevicePath");
        if (!dp.empty()) return dp;
    }
    
    LPOLESTR disp = nullptr;
    std::wstring res;
    if (SUCCEEDED(mon->GetDisplayName(nullptr, nullptr, &disp)) && disp) {
        res.assign(disp);
        CoTaskMemFree(disp);
    }
    return res;
}

static com_ptr<IBaseFilter> bind_to_filter(IMoniker* mon) {
    com_ptr<IBaseFilter> f;
    HRESULT hr = mon->BindToObject(nullptr, nullptr, IID_IBaseFilter, reinterpret_cast<void**>(f.put()));
    if (FAILED(hr)) throw_hr(hr, "BindToObject(IBaseFilter)");
    return f;
}

static com_ptr<IAMCameraControl> get_cam_ctrl(IBaseFilter* f) {
    com_ptr<IAMCameraControl> cam;
    if (FAILED(f->QueryInterface(IID_IAMCameraControl, reinterpret_cast<void**>(cam.put())))) return {};
    return cam;
}

static com_ptr<IAMVideoProcAmp> get_vproc(IBaseFilter* f) {
    com_ptr<IAMVideoProcAmp> vp;
    if (FAILED(f->QueryInterface(IID_IAMVideoProcAmp, reinterpret_cast<void**>(vp.put())))) return {};
    return vp;
}

static com_ptr<IKsPropertySet> get_property_set(IBaseFilter* f) {
    com_ptr<IKsPropertySet> props;
    if (FAILED(f->QueryInterface(IID_IKsPropertySet, reinterpret_cast<void**>(props.put())))) {
        return {};
    }
    return props;
}

static bool is_same_device(const Device& d, const std::wstring& name, const std::wstring& path) {
    if (!d.path.empty() && !path.empty()) {
        if (_wcsicmp(d.path.c_str(), path.c_str()) == 0) return true;
    }
    if (!d.name.empty() && !name.empty()) {
        if (_wcsicmp(d.name.c_str(), name.c_str()) == 0) return true;
    }
    return false;
}

static com_ptr<IBaseFilter> open_device_filter(const Device& dev) {
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

// Mapping helpers
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
class DeviceConnection::com_apartment {
public:
    com_apartment() {
        hr_ = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
        if (FAILED(hr_) && hr_ != RPC_E_CHANGED_MODE) {
            throw_hr(hr_, "CoInitializeEx");
        }
    }
    
    ~com_apartment() {
        if (SUCCEEDED(hr_)) CoUninitialize();
    }
    
private:
    HRESULT hr_{ S_OK };
};

DeviceConnection::DeviceConnection(const Device& dev) : 
    com_(std::make_unique<com_apartment>()),
    filter_(nullptr), 
    cam_ctrl_(nullptr), 
    vid_proc_(nullptr) {
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

void clear_connection_cache() {
    std::lock_guard<std::mutex> lock(g_cache_mutex);
    g_connection_cache.clear();
}

// Device monitoring implementation
void register_device_change_callback(DeviceChangeCallback callback) {
    if (g_notification_window) return; // Already registered
    
    g_device_callback = callback;
    
    // Create invisible window for notifications
    WNDCLASSW wc = {};  // Use WNDCLASSW for Unicode
    wc.lpfnWndProc = device_wndproc;
    wc.hInstance = GetModuleHandle(nullptr);
    wc.lpszClassName = L"DuvcDeviceNotification";
    RegisterClassW(&wc);  // Use RegisterClassW
    
    g_notification_window = CreateWindowW(L"DuvcDeviceNotification", L"", 0, 0, 0, 0, 0,  // Use CreateWindowW
                                        HWND_MESSAGE, nullptr, GetModuleHandle(nullptr), nullptr);
    
    // Register for device interface notifications
    DEV_BROADCAST_DEVICEINTERFACE filter = {};
    filter.dbcc_size = sizeof(filter);
    filter.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE;
    filter.dbcc_classguid = CLSID_VideoInputDeviceCategory;
    
    g_device_notify = RegisterDeviceNotification(g_notification_window, &filter, 
                                                DEVICE_NOTIFY_WINDOW_HANDLE);
}


void unregister_device_change_callback() {
    if (g_device_notify) {
        UnregisterDeviceNotification(g_device_notify);
        g_device_notify = nullptr;
    }
    if (g_notification_window) {
        DestroyWindow(g_notification_window);
        g_notification_window = nullptr;
    }
    g_device_callback = nullptr;
}

bool is_device_connected(const Device& dev) {
    try {
        // First try: Check if device still exists in enumeration
        com_apartment com;
        auto de = create_dev_enum();
        auto en = enum_video_devices(de.get());
        if (!en) return false;
        
        ULONG fetched = 0;
        com_ptr<IMoniker> mon;
        while (en->Next(1, mon.put(), &fetched) == S_OK && fetched) {
            auto fname = read_friendly_name(mon.get());
            auto dpath = read_device_path(mon.get());
            if (is_same_device(dev, fname, dpath)) {
                // Found in enumeration - now try lightweight access test
                try {
                    // Try to create a cached connection (uses existing connection if available)
                    auto* conn = get_cached_connection(dev);
                    return conn != nullptr && conn->is_valid();
                } catch (...) {
                    // If cached connection fails, device exists but might be busy
                    // Since it's enumerated, consider it "connected" but potentially busy
                    return true;
                }
            }
            mon.reset();
        }
        return false; // Not found in enumeration
    } catch (...) {
        return false;
    }
}


// Vendor property implementation
bool get_vendor_property(const Device& dev, const GUID& property_set, ULONG property_id, 
                        std::vector<uint8_t>& data) {
    com_apartment com;
    auto filter = open_device_filter(dev);
    auto props = get_property_set(filter.get());
    if (!props) return false;
    
    ULONG bytes_returned = 0;
    HRESULT hr = props->Get(property_set, property_id, nullptr, 0, 
                           nullptr, 0, &bytes_returned);
    if (FAILED(hr) || bytes_returned == 0) return false;
    
    data.resize(bytes_returned);
    hr = props->Get(property_set, property_id, nullptr, 0, 
                   data.data(), bytes_returned, &bytes_returned);
    return SUCCEEDED(hr);
}

bool set_vendor_property(const Device& dev, const GUID& property_set, ULONG property_id, 
                        const std::vector<uint8_t>& data) {
    com_apartment com;
    auto filter = open_device_filter(dev);
    auto props = get_property_set(filter.get());
    if (!props) return false;
    
    HRESULT hr = props->Set(property_set, property_id, nullptr, 0, 
                           const_cast<uint8_t*>(data.data()), data.size());
    return SUCCEEDED(hr);
}

bool query_vendor_property_support(const Device& dev, const GUID& property_set, ULONG property_id) {
    com_apartment com;
    auto filter = open_device_filter(dev);
    auto props = get_property_set(filter.get());
    if (!props) return false;
    
    ULONG type_support = 0;
    HRESULT hr = props->QuerySupported(property_set, property_id, &type_support);
    return SUCCEEDED(hr) && (type_support & (KSPROPERTY_SUPPORT_GET | KSPROPERTY_SUPPORT_SET));
}

// Public API: enumeration
std::vector<Device> list_devices() {
    com_apartment com;
    std::vector<Device> out;
    
    auto de = create_dev_enum();
    auto en = enum_video_devices(de.get());
    if (!en) return out;
    
    ULONG fetched = 0;
    com_ptr<IMoniker> mon;
    while (en->Next(1, mon.put(), &fetched) == S_OK && fetched) {
        Device d;
        d.name = read_friendly_name(mon.get());
        d.path = read_device_path(mon.get());
        out.emplace_back(std::move(d));
        mon.reset();
    }
    return out;
}

// Updated public API functions to use cached connections
bool get_range(const Device& dev, CamProp prop, PropRange& range) {
    auto* conn = get_cached_connection(dev);
    return conn ? conn->get_range(prop, range) : false;
}

bool get(const Device& dev, CamProp prop, PropSetting& val) {
    auto* conn = get_cached_connection(dev);
    return conn ? conn->get(prop, val) : false;
}

bool set(const Device& dev, CamProp prop, const PropSetting& val) {
    auto* conn = get_cached_connection(dev);
    return conn ? conn->set(prop, val) : false;
}

bool get_range(const Device& dev, VidProp prop, PropRange& range) {
    auto* conn = get_cached_connection(dev);
    return conn ? conn->get_range(prop, range) : false;
}

bool get(const Device& dev, VidProp prop, PropSetting& val) {
    auto* conn = get_cached_connection(dev);
    return conn ? conn->get(prop, val) : false;
}

bool set(const Device& dev, VidProp prop, const PropSetting& val) {
    auto* conn = get_cached_connection(dev);
    return conn ? conn->set(prop, val) : false;
}

// String helpers
const char* to_string(CamProp p) {
    switch (p) {
        case CamProp::Pan: return "Pan";
        case CamProp::Tilt: return "Tilt";
        case CamProp::Roll: return "Roll";
        case CamProp::Zoom: return "Zoom";
        case CamProp::Exposure: return "Exposure";
        case CamProp::Iris: return "Iris";
        case CamProp::Focus: return "Focus";
        case CamProp::ScanMode: return "ScanMode";
        case CamProp::Privacy: return "Privacy";
        case CamProp::PanRelative: return "PanRelative";
        case CamProp::TiltRelative: return "TiltRelative";
        case CamProp::RollRelative: return "RollRelative";
        case CamProp::ZoomRelative: return "ZoomRelative";
        case CamProp::ExposureRelative: return "ExposureRelative";
        case CamProp::IrisRelative: return "IrisRelative";
        case CamProp::FocusRelative: return "FocusRelative";
        case CamProp::PanTilt: return "PanTilt";
        case CamProp::PanTiltRelative: return "PanTiltRelative";
        case CamProp::FocusSimple: return "FocusSimple";
        case CamProp::DigitalZoom: return "DigitalZoom";
        case CamProp::DigitalZoomRelative: return "DigitalZoomRelative";
        case CamProp::BacklightCompensation: return "BacklightCompensation";
        case CamProp::Lamp: return "Lamp";
        default: return "Unknown";
    }
}

const wchar_t* to_wstring(CamProp p) {
    switch (p) {
        case CamProp::Pan: return L"Pan";
        case CamProp::Tilt: return L"Tilt";
        case CamProp::Roll: return L"Roll";
        case CamProp::Zoom: return L"Zoom";
        case CamProp::Exposure: return L"Exposure";
        case CamProp::Iris: return L"Iris";
        case CamProp::Focus: return L"Focus";
        case CamProp::ScanMode: return L"ScanMode";
        case CamProp::Privacy: return L"Privacy";
        case CamProp::PanRelative: return L"PanRelative";
        case CamProp::TiltRelative: return L"TiltRelative";
        case CamProp::RollRelative: return L"RollRelative";
        case CamProp::ZoomRelative: return L"ZoomRelative";
        case CamProp::ExposureRelative: return L"ExposureRelative";
        case CamProp::IrisRelative: return L"IrisRelative";
        case CamProp::FocusRelative: return L"FocusRelative";
        case CamProp::PanTilt: return L"PanTilt";
        case CamProp::PanTiltRelative: return L"PanTiltRelative";
        case CamProp::FocusSimple: return L"FocusSimple";
        case CamProp::DigitalZoom: return L"DigitalZoom";
        case CamProp::DigitalZoomRelative: return L"DigitalZoomRelative";
        case CamProp::BacklightCompensation: return L"BacklightCompensation";
        case CamProp::Lamp: return L"Lamp";
        default: return L"Unknown";
    }
}

const char* to_string(VidProp p) {
    switch (p) {
        case VidProp::Brightness: return "Brightness";
        case VidProp::Contrast: return "Contrast";
        case VidProp::Hue: return "Hue";
        case VidProp::Saturation: return "Saturation";
        case VidProp::Sharpness: return "Sharpness";
        case VidProp::Gamma: return "Gamma";
        case VidProp::ColorEnable: return "ColorEnable";
        case VidProp::WhiteBalance: return "WhiteBalance";
        case VidProp::BacklightCompensation: return "BacklightCompensation";
        case VidProp::Gain: return "Gain";
        default: return "Unknown";
    }
}

const wchar_t* to_wstring(VidProp p) {
    switch (p) {
        case VidProp::Brightness: return L"Brightness";
        case VidProp::Contrast: return L"Contrast";
        case VidProp::Hue: return L"Hue";
        case VidProp::Saturation: return L"Saturation";
        case VidProp::Sharpness: return L"Sharpness";
        case VidProp::Gamma: return L"Gamma";
        case VidProp::ColorEnable: return L"ColorEnable";
        case VidProp::WhiteBalance: return L"WhiteBalance";
        case VidProp::BacklightCompensation: return L"BacklightCompensation";
        case VidProp::Gain: return L"Gain";
        default: return L"Unknown";
    }
}

const char* to_string(CamMode m) {
    return (m == CamMode::Auto) ? "AUTO" : "MANUAL";
}

const wchar_t* to_wstring(CamMode m) {
    return (m == CamMode::Auto) ? L"AUTO" : L"MANUAL";
}

} // namespace duvc

#else // _WIN32

// Non-Windows stubs to allow inclusion without linking errors
namespace duvc {

std::vector<Device> list_devices() { return {}; }
bool get_range(const Device&, CamProp, PropRange&) { return false; }
bool get(const Device&, CamProp, PropSetting&) { return false; }
bool set(const Device&, CamProp, const PropSetting&) { return false; }
bool get_range(const Device&, VidProp, PropRange&) { return false; }
bool get(const Device&, VidProp, PropSetting&) { return false; }
bool set(const Device&, VidProp, const PropSetting&) { return false; }

const char* to_string(CamProp) { return "Unknown"; }
const char* to_string(VidProp) { return "Unknown"; }
const char* to_string(CamMode) { return "MANUAL"; }

const wchar_t* to_wstring(CamProp) { return L"Unknown"; }
const wchar_t* to_wstring(VidProp) { return L"Unknown"; }
const wchar_t* to_wstring(CamMode) { return L"MANUAL"; }

// Stubs for new functionality
void register_device_change_callback(DeviceChangeCallback) {}
void unregister_device_change_callback() {}
bool is_device_connected(const Device&) { return false; }

bool get_vendor_property(const Device&, const GUID&, ULONG, std::vector<uint8_t>&) { return false; }
bool set_vendor_property(const Device&, const GUID&, ULONG, const std::vector<uint8_t>&) { return false; }
bool query_vendor_property_support(const Device&, const GUID&, ULONG) { return false; }

DeviceConnection* get_cached_connection(const Device&) { return nullptr; }
void release_cached_connection(const Device&) {}
void clear_connection_cache() {}

} // namespace duvc

#endif // _WIN32
