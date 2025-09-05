/**
 * @file device.cpp
 * @brief Device enumeration and management implementation
 */

#include <duvc-ctl/core/device.h>
#include <duvc-ctl/detail/com_helpers.h>

#ifdef _WIN32
#include <duvc-ctl/platform/windows/connection_pool.h>
#include <dshow.h>
#include <dbt.h>

// DirectShow GUIDs - properly declared
EXTERN_C const CLSID CLSID_SystemDeviceEnum;
EXTERN_C const CLSID CLSID_VideoInputDeviceCategory;
EXTERN_C const IID IID_ICreateDevEnum;
EXTERN_C const IID IID_IPropertyBag;

namespace duvc {

using namespace detail;

// Global device monitoring state
DeviceChangeCallback g_device_callback = nullptr;
HWND g_notification_window = nullptr;
HDEVNOTIFY g_device_notify = nullptr;


// DirectShow enumeration helpers - these need to be exported for connection_pool.cpp
com_ptr<ICreateDevEnum> create_dev_enum() {
    com_ptr<ICreateDevEnum> dev;
    HRESULT hr = CoCreateInstance(CLSID_SystemDeviceEnum, nullptr, CLSCTX_INPROC_SERVER,
                                  IID_ICreateDevEnum, reinterpret_cast<void**>(dev.put()));
    if (FAILED(hr)) throw_hr(hr, "CoCreateInstance(SystemDeviceEnum)");
    return dev;
}

com_ptr<IEnumMoniker> enum_video_devices(ICreateDevEnum* dev) {
    com_ptr<IEnumMoniker> e;
    HRESULT hr = dev->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, e.put(), 0);
    if (hr == S_FALSE) return {}; // No devices
    if (FAILED(hr)) throw_hr(hr, "CreateClassEnumerator(VideoInputDeviceCategory)");
    return e;
}

static std::wstring read_prop_bstr(IPropertyBag* bag, const wchar_t* key) {
    VARIANT v; 
    VariantInit(&v);
    std::wstring res;
    
    if (SUCCEEDED(bag->Read(key, &v, nullptr)) && v.vt == VT_BSTR && v.bstrVal) {
        res.assign(v.bstrVal, SysStringLen(v.bstrVal));
    }
    
    VariantClear(&v);
    return res;
}

std::wstring read_friendly_name(IMoniker* mon) {
    com_ptr<IPropertyBag> bag;
    HRESULT hr = mon->BindToStorage(nullptr, nullptr, IID_IPropertyBag, 
                                    reinterpret_cast<void**>(bag.put()));
    if (FAILED(hr)) return L"";
    
    auto name = read_prop_bstr(bag.get(), L"FriendlyName");
    return name.empty() ? L"" : name;
}

std::wstring read_device_path(IMoniker* mon) {
    com_ptr<IPropertyBag> bag;
    if (SUCCEEDED(mon->BindToStorage(nullptr, nullptr, IID_IPropertyBag, 
                                     reinterpret_cast<void**>(bag.put())))) {
        auto dp = read_prop_bstr(bag.get(), L"DevicePath");
        if (!dp.empty()) return dp;
    }
    
    // Fallback to display name
    LPOLESTR disp = nullptr;
    std::wstring res;
    if (SUCCEEDED(mon->GetDisplayName(nullptr, nullptr, &disp)) && disp) {
        res.assign(disp);
        CoTaskMemFree(disp);
    }
    
    return res;
}

bool is_same_device(const Device& d, const std::wstring& name, const std::wstring& path) {
    if (!d.path.empty() && !path.empty()) {
        if (_wcsicmp(d.path.c_str(), path.c_str()) == 0) return true;
    }
    
    if (!d.name.empty() && !name.empty()) {
        if (_wcsicmp(d.name.c_str(), name.c_str()) == 0) return true;
    }
    
    return false;
}

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
                    DeviceConnection conn(dev);
                    return conn.is_valid();
                } catch (...) {
                    // If connection fails, device exists but might be busy
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

} // namespace duvc

#else // _WIN32

// Non-Windows stubs
namespace duvc {

std::vector<Device> list_devices() { 
    return {}; 
}

bool is_device_connected(const Device&) { 
    return false; 
}

void register_device_change_callback(DeviceChangeCallback) {}

void unregister_device_change_callback() {}

} // namespace duvc

#endif // _WIN32
