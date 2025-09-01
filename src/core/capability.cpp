/**
 * @file capability.cpp
 * @brief Device capability detection implementation
 */

#include <duvc-ctl/core/capability.h>
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/core/operations.h>

namespace duvc {

// Static empty capability for unsupported properties
const PropertyCapability DeviceCapabilities::empty_capability_ = {};

DeviceCapabilities::DeviceCapabilities(const Device& device) 
    : device_(device), device_accessible_(false) {
    device_accessible_ = is_device_connected(device_);
    if (device_accessible_) {
        scan_capabilities();
    }
}

void DeviceCapabilities::scan_capabilities() {
    // Scan all camera properties
    for (int i = 0; i <= static_cast<int>(CamProp::Lamp); ++i) {
        CamProp prop = static_cast<CamProp>(i);
        PropertyCapability capability;
        
        // Try to get range - if successful, property is supported
        if (get_range(device_, prop, capability.range)) {
            capability.supported = true;
            
            // Try to get current value
            get(device_, prop, capability.current);
            
            camera_capabilities_[prop] = capability;
        }
    }
    
    // Scan all video properties  
    for (int i = 0; i <= static_cast<int>(VidProp::Gain); ++i) {
        VidProp prop = static_cast<VidProp>(i);
        PropertyCapability capability;
        
        // Try to get range - if successful, property is supported
        if (get_range(device_, prop, capability.range)) {
            capability.supported = true;
            
            // Try to get current value
            get(device_, prop, capability.current);
            
            video_capabilities_[prop] = capability;
        }
    }
}

const PropertyCapability& DeviceCapabilities::get_camera_capability(CamProp prop) const {
    auto it = camera_capabilities_.find(prop);
    return it != camera_capabilities_.end() ? it->second : empty_capability_;
}

const PropertyCapability& DeviceCapabilities::get_video_capability(VidProp prop) const {
    auto it = video_capabilities_.find(prop);
    return it != video_capabilities_.end() ? it->second : empty_capability_;
}

bool DeviceCapabilities::supports_camera_property(CamProp prop) const {
    return get_camera_capability(prop).supported;
}

bool DeviceCapabilities::supports_video_property(VidProp prop) const {
    return get_video_capability(prop).supported;
}

std::vector<CamProp> DeviceCapabilities::supported_camera_properties() const {
    std::vector<CamProp> props;
    for (const auto& pair : camera_capabilities_) {
        if (pair.second.supported) {
            props.push_back(pair.first);
        }
    }
    return props;
}

std::vector<VidProp> DeviceCapabilities::supported_video_properties() const {
    std::vector<VidProp> props;
    for (const auto& pair : video_capabilities_) {
        if (pair.second.supported) {
            props.push_back(pair.first);
        }
    }
    return props;
}

Result<void> DeviceCapabilities::refresh() {
    device_accessible_ = is_device_connected(device_);
    if (!device_accessible_) {
        return Err<void>(ErrorCode::DeviceNotFound, "Device not connected");
    }
    
    camera_capabilities_.clear();
    video_capabilities_.clear();
    scan_capabilities();
    return Ok();
}

Result<DeviceCapabilities> get_device_capabilities(const Device& device) {
    if (!device.is_valid()) {
        return Err<DeviceCapabilities>(ErrorCode::InvalidArgument, "Invalid device");
    }
    
    return Ok(DeviceCapabilities(device));
}

Result<DeviceCapabilities> get_device_capabilities(int device_index) {
    auto devices = list_devices();
    if (device_index < 0 || device_index >= static_cast<int>(devices.size())) {
        return Err<DeviceCapabilities>(ErrorCode::DeviceNotFound, "Invalid device index");
    }
    
    return get_device_capabilities(devices[device_index]);
}

} // namespace duvc
