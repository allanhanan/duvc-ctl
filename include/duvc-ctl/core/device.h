#pragma once

/**
 * @file device.h
 * @brief Device enumeration and management functions
 */

#include <duvc-ctl/core/types.h>
#include <functional>
#include <vector>

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
bool is_device_connected(const Device &dev);

/**
 * @brief Find device by unique Windows device path
 * 
 * Searches the current device enumeration for a device matching the specified
 * Windows device instance path. This provides unambiguous identification when
 * multiple cameras have identical names due to firmware variations.
 * 
 * @param device_path Wide string containing the device path (case-insensitive)
 * @return Device object with matching path
 * @throws std::runtime_error if enumeration fails or device not found
 * 
 * The device path format is: USB\VID_XXXX&PID_XXXX&MI_XX#...#{GUID}
 * 
 * @note Device paths can be obtained from Device::path member
 * @see list_devices() to enumerate all devices with paths
 * 
 * Example:
 * @code
 * auto devices = duvc::list_devices();
 * try {
 *     auto target = duvc::find_device_by_path(devices[0].path);
 *     Camera camera(target);
 * } catch (const std::runtime_error &e) {
 *     // Handle device not found
 * }
 * @endcode
 */
Device find_device_by_path(const std::wstring &device_path);

/**
 * @brief Device change callback function type
 * @param added true if device was added, false if removed
 * @param device_path Path of the device that changed
 */
using DeviceChangeCallback =
    std::function<void(bool added, const std::wstring &device_path)>;

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
