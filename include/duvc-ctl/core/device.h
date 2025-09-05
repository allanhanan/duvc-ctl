#pragma once

/**
 * @file device.h
 * @brief Device enumeration and management functions
 */

#include <duvc-ctl/core/types.h>
#include <vector>
#include <functional>

namespace duvc {

/**
 * @brief Enumerate all available video input devices
 * @return Vector of detected devices
 * @throws std::runtime_error if device enumeration fails
 */
std::vector<Device> list_devices();

/**
 * @brief Check if a device is currently connected and accessible
 * @param dev Device to check
 * @return true if device is connected and can be opened
 * 
 * This performs a lightweight check to determine if the device
 * still exists and can be accessed.
 */
bool is_device_connected(const Device& dev);

/**
 * @brief Device change callback function type
 * @param added true if device was added, false if removed
 * @param device_path Path of the device that changed
 */
using DeviceChangeCallback = std::function<void(bool added, const std::wstring& device_path)>;

/**
 * @brief Register callback for device hotplug events
 * @param callback Function to call when devices are added/removed
 * 
 * Only one callback can be registered at a time. Calling this
 * multiple times will replace the previous callback.
 */
void register_device_change_callback(DeviceChangeCallback callback);

/**
 * @brief Unregister device change callback
 * 
 * Stops monitoring device changes and cleans up resources.
 */
void unregister_device_change_callback();

} // namespace duvc
