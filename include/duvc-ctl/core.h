#pragma once

#include "defs.h"
#include <vector>
#include <functional>
#include <memory>
#include <cstdint>

#ifdef _WIN32
#include <windows.h>
#endif

namespace duvc {

std::vector<Device> list_devices();

bool get_range(const Device&, CamProp, PropRange&);
bool get(const Device&, CamProp, PropSetting&);
bool set(const Device&, CamProp, const PropSetting&);

bool get_range(const Device&, VidProp, PropRange&);
bool get(const Device&, VidProp, PropSetting&);
bool set(const Device&, VidProp, const PropSetting&);

const char* to_string(CamProp);
const char* to_string(VidProp);
const char* to_string(CamMode);

const wchar_t* to_wstring(CamProp);
const wchar_t* to_wstring(VidProp);
const wchar_t* to_wstring(CamMode);

// Device monitoring (hotplug detection)
using DeviceChangeCallback = std::function<void(bool device_added, const std::wstring& device_path)>;
void register_device_change_callback(DeviceChangeCallback callback);
void unregister_device_change_callback();
bool is_device_connected(const Device& dev);

#ifdef _WIN32
// Extended vendor-specific controls (Windows only)
struct VendorProperty {
    GUID property_set;
    ULONG property_id;
    std::vector<uint8_t> data;
};

bool get_vendor_property(const Device& dev, const GUID& property_set, ULONG property_id, 
                        std::vector<uint8_t>& data);
bool set_vendor_property(const Device& dev, const GUID& property_set, ULONG property_id, 
                        const std::vector<uint8_t>& data);
bool query_vendor_property_support(const Device& dev, const GUID& property_set, ULONG property_id);
#endif

// Performance optimizations - Connection pooling
class DeviceConnection {
public:
    explicit DeviceConnection(const Device& dev);
    ~DeviceConnection();
    
    bool get(CamProp prop, PropSetting& val);
    bool set(CamProp prop, const PropSetting& val);
    bool get(VidProp prop, PropSetting& val);
    bool set(VidProp prop, const PropSetting& val);
    bool get_range(CamProp prop, PropRange& range);
    bool get_range(VidProp prop, PropRange& range);
    
    bool is_valid() const { return filter_ != nullptr; }
    
private:
    class com_apartment;
    std::unique_ptr<com_apartment> com_;
    void* filter_;  // com_ptr<IBaseFilter> - using void* to avoid forward declaration issues
    void* cam_ctrl_; // com_ptr<IAMCameraControl>
    void* vid_proc_; // com_ptr<IAMVideoProcAmp>
};

// Connection pool management
DeviceConnection* get_cached_connection(const Device& dev);
void release_cached_connection(const Device& dev);
void clear_connection_cache();

} // namespace duvc
