/**
 * @file capability.cpp
 * @brief Device capability detection implementation using Camera API
 */

#include <duvc-ctl/core/camera.h>
#include <duvc-ctl/core/capability.h>
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/core/result.h>

#include <duvc-ctl/utils/logging.h>
#include <duvc-ctl/utils/string_conversion.h>

namespace duvc {

// Static empty capability for unsupported properties
const PropertyCapability DeviceCapabilities::empty_capability_ = {};

DeviceCapabilities::DeviceCapabilities(const Device &device)
    : device_(device), device_accessible_(false) {
  device_accessible_ = is_device_connected(device_);
  if (device_accessible_) {
    scan_capabilities();
  }
}

void DeviceCapabilities::scan_capabilities() {
  camera_capabilities_.clear();
  video_capabilities_.clear();

  // Create camera instance for property access
  Camera camera(device_);
  if (!camera.is_valid()) {
    DUVC_LOG_WARNING("Device not accessible during capability scan");
    device_accessible_ = false;
    return;
  }

  // Scan all camera properties
  for (int i = 0; i <= static_cast<int>(CamProp::Lamp); ++i) {
    CamProp prop = static_cast<CamProp>(i);
    PropertyCapability capability;

    // Try to get range - if successful, property is supported
    auto range_result = camera.get_range(prop);
    if (range_result.is_ok()) {
      capability.supported = true;
      capability.range = range_result.value();

      // Try to get current value
      auto current_result = camera.get(prop);
      if (current_result.is_ok()) {
        capability.current = current_result.value();
      } else {
        DUVC_LOG_WARNING("Failed to get current camera property value for " +
                         std::string(to_string(prop)));
      }

      camera_capabilities_[prop] = capability;
    }
  }

  // Scan all video properties
  for (int i = 0; i <= static_cast<int>(VidProp::Gain); ++i) {
    VidProp prop = static_cast<VidProp>(i);
    PropertyCapability capability;

    // Try to get range - if successful, property is supported
    auto range_result = camera.get_range(prop);
    if (range_result.is_ok()) {
      capability.supported = true;
      capability.range = range_result.value();

      // Try to get current value
      auto current_result = camera.get(prop);
      if (current_result.is_ok()) {
        capability.current = current_result.value();
      } else {
        DUVC_LOG_WARNING("Failed to get current video property value for " +
                         std::string(to_string(prop)));
      }

      video_capabilities_[prop] = capability;
    }
  }
}

const PropertyCapability &
DeviceCapabilities::get_camera_capability(CamProp prop) const {
  auto it = camera_capabilities_.find(prop);
  return it != camera_capabilities_.end() ? it->second : empty_capability_;
}

const PropertyCapability &
DeviceCapabilities::get_video_capability(VidProp prop) const {
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
  for (const auto &pair : camera_capabilities_) {
    if (pair.second.supported) {
      props.push_back(pair.first);
    }
  }
  return props;
}

std::vector<VidProp> DeviceCapabilities::supported_video_properties() const {
  std::vector<VidProp> props;
  for (const auto &pair : video_capabilities_) {
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

Result<DeviceCapabilities> get_device_capabilities(const Device &device) {
    // Defensive validation: check if device strings are accessible
    // This prevents crashes from corrupted Device objects passed from Python
    try {
        // Validate device before use
        if (!device.is_valid()) {
            return Err<DeviceCapabilities>(ErrorCode::InvalidArgument, "Invalid device");
        }
        
        // Force access to string internals to catch corruption early
        // If strings are corrupted (e.g., from bad pybind11 copy), this will throw
        const auto* name_ptr = device.name.data();
        const auto* path_ptr = device.path.data();
        size_t name_len = device.name.size();
        size_t path_len = device.path.size();
        
        // Validate pointers are not null if strings are non-empty
        if ((name_len > 0 && !name_ptr) || (path_len > 0 && !path_ptr)) {
            return Err<DeviceCapabilities>(ErrorCode::InvalidArgument, 
                       "Device has corrupted string data (null pointer with non-zero size)");
        }
        
        // Validate we can actually read the strings without crashing
        // This will fault if the internal string buffer pointer is invalid
        if (!device.name.empty()) {
            [[maybe_unused]] volatile wchar_t first_char = device.name[0];
        }
        if (!device.path.empty()) {
            [[maybe_unused]] volatile wchar_t first_char = device.path[0];
        }
        
    } catch (const std::exception& e) {
        return Err<DeviceCapabilities>(ErrorCode::InvalidArgument, 
                   std::string("Device object has corrupted memory: ") + e.what());
    } catch (...) {
        return Err<DeviceCapabilities>(ErrorCode::InvalidArgument, 
                   "Device object has corrupted memory (unknown exception)");
    }

    // Device validation passed - safe to proceed
    DeviceCapabilities capabilities(device);
    if (!capabilities.is_device_accessible()) {
        return Err<DeviceCapabilities>(ErrorCode::DeviceNotFound, "Device not accessible");
    }

    return Ok(std::move(capabilities));
}

Result<DeviceCapabilities> get_device_capabilities(int device_index) {
  auto devices = list_devices();
  if (device_index < 0 || device_index >= static_cast<int>(devices.size())) {
    return Err<DeviceCapabilities>(ErrorCode::DeviceNotFound,
                                   "Invalid device index");
  }
  return get_device_capabilities(devices[device_index]);
}

} // namespace duvc
