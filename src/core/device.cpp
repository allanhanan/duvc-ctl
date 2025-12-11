/**
 * @file device.cpp
 * @brief Device enumeration and management implementation
 */

#include <duvc-ctl/core/device.h>
#include <duvc-ctl/detail/com_helpers.h>

#ifdef _WIN32
#include <comdef.h>
#include <dbt.h>
#include <dshow.h>
#include <duvc-ctl/platform/windows/connection_pool.h>
#include <duvc-ctl/utils/string_conversion.h>

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

// DirectShow enumeration helpers - these need to be exported for
// connection_pool.cpp
com_ptr<ICreateDevEnum> create_dev_enum() {
  com_ptr<ICreateDevEnum> dev;
  HRESULT hr = CoCreateInstance(CLSID_SystemDeviceEnum, nullptr,
                                CLSCTX_INPROC_SERVER, IID_ICreateDevEnum,
                                reinterpret_cast<void **>(dev.put()));
  if (FAILED(hr))
    throw_hr(hr, "CoCreateInstance(SystemDeviceEnum)");
  return dev;
}

com_ptr<IEnumMoniker> enum_video_devices(ICreateDevEnum *dev) {
  com_ptr<IEnumMoniker> e;
  HRESULT hr =
      dev->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, e.put(), 0);
  if (hr == S_FALSE)
    return {}; // No devices
  if (FAILED(hr))
    throw_hr(hr, "CreateClassEnumerator(VideoInputDeviceCategory)");
  return e;
}

static std::wstring read_prop_bstr(IPropertyBag *bag, const wchar_t *key) {
    if (!bag || !key) {
        return L"";
    }

    VARIANT v;
    VariantInit(&v);
    std::wstring res;

    HRESULT hr = bag->Read(key, &v, nullptr);
    if (SUCCEEDED(hr) && v.vt == VT_BSTR && v.bstrVal) {
        _bstr_t bstr(v.bstrVal); // manages lifetime
        const wchar_t *ptr = static_cast<const wchar_t*>(bstr);
        if (ptr) {
            size_t len = bstr.length();
            if (len > 0 && len < 2048) {
                res.assign(ptr, len);
            }
        }
        VariantClear(&v);
    }

    return res;
}

std::wstring read_friendly_name(IMoniker *mon) {
    if (!mon) {
        return L"";
    }

    com_ptr<IPropertyBag> bag;
    HRESULT hr = mon->BindToStorage(
        nullptr,
        nullptr,
        IID_IPropertyBag,
        reinterpret_cast<void**>(bag.put())
    );
    if (FAILED(hr) || !bag) {
        return L"";
    }

    return read_prop_bstr(bag.get(), L"FriendlyName");
}

std::wstring read_device_path(IMoniker *mon) {
    if (!mon) {
        return L"";
    }

    com_ptr<IPropertyBag> bag;
    HRESULT hr = mon->BindToStorage(
        nullptr,
        nullptr,
        IID_IPropertyBag,
        reinterpret_cast<void**>(bag.put())
    );
    if (SUCCEEDED(hr) && bag) {
        auto dp = read_prop_bstr(bag.get(), L"DevicePath");
        if (!dp.empty()) {
            return dp;
        }
    }

    // Fallback: IMoniker::GetDisplayName
    LPOLESTR disp = nullptr;
    std::wstring res;

    if (SUCCEEDED(mon->GetDisplayName(nullptr, nullptr, &disp)) && disp) {
        _bstr_t bstr(disp); // safe wrapper around LPOLESTR
        const wchar_t *ptr = static_cast<const wchar_t*>(bstr);
        if (ptr) {
            size_t len = bstr.length();
            if (len > 0 && len < 512) {
                res.assign(ptr, len);
            }
        }
        CoTaskMemFree(disp);

        if (!res.empty()) {
            // Trim trailing whitespace / control chars
            res.erase(res.find_last_not_of(L"\r\n \t\0") + 1);
        }
    }

    return res;
}

bool is_same_device(const Device &d, const std::wstring &name,
                    const std::wstring &path) {
  if (!d.path.empty() && !path.empty()) {
    if (_wcsicmp(d.path.c_str(), path.c_str()) == 0)
      return true;
  }

  if (!d.name.empty() && !name.empty()) {
    if (_wcsicmp(d.name.c_str(), name.c_str()) == 0)
      return true;
  }

  return false;
}

std::vector<Device> list_devices() {
  com_apartment com;
  std::vector<Device> out;
  
  auto de = create_dev_enum();
  auto en = enum_video_devices(de.get());
  if (!en)
    return out;

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

bool is_device_connected(const Device &dev) {
  try {
    // First try: Check if device still exists in enumeration
    com_apartment com;
    auto de = create_dev_enum();
    auto en = enum_video_devices(de.get());
    if (!en)
      return false;

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

Device duvc::find_device_by_path(const std::wstring &device_path) {
    if (device_path.empty()) {
        throw std::runtime_error("Device path cannot be empty");
    }
    com_apartment com;
    com_ptr<ICreateDevEnum> de;
    HRESULT hr = CoCreateInstance(CLSID_SystemDeviceEnum, nullptr, CLSCTX_INPROC_SERVER,
                                  IID_ICreateDevEnum, reinterpret_cast<void**>(de.put()));
    if (FAILED(hr)) {
        throw_hr(hr, "CoCreateInstance(SystemDeviceEnum)");
    }
    com_ptr<IEnumMoniker> en;
    hr = de->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, reinterpret_cast<IEnumMoniker**>(en.put()), 0);
    if (FAILED(hr)) {
        if (hr == S_FALSE) {
            throw std::runtime_error("No video devices available");
        }
        throw_hr(hr, "CreateClassEnumerator(VideoInputDeviceCategory)");
    }
    ULONG fetched = 0;
    com_ptr<IMoniker> mon;
    while (en->Next(1, reinterpret_cast<IMoniker**>(mon.put()), &fetched) == S_OK && fetched) {
        std::wstring dpath = read_device_path(mon.get());
        if (!dpath.empty()) {
            dpath.erase(dpath.find_last_not_of(L"\r\n \t\0") + 1);
        }
        std::wstring fname = read_friendly_name(mon.get());
        if (dpath == device_path || _wcsicmp(dpath.c_str(), device_path.c_str()) == 0) {
            Device result;
            result.name = std::move(fname);
            result.path = std::move(dpath);
            return result;
        }
    }
    throw std::runtime_error(
        "Device with specified path not found. Ensure the device is connected and the path is valid.");
}

} // namespace duvc

#else // _WIN32

// Non-Windows stubs
namespace duvc {

std::vector<Device> list_devices() { return {}; }

bool is_device_connected(const Device &) { return false; }

void register_device_change_callback(DeviceChangeCallback) {}

void unregister_device_change_callback() {}

} // namespace duvc

#endif // _WIN32
