#pragma once

/**
 * @file duvc.hpp
 * @brief Main umbrella header for duvc-ctl library
 * 
 * This header provides both the full-featured RAII API (Camera, Result<T>)
 * and a simplified quick API for common use cases (device enumeration,
 * property get/set, capability snapshots).
 * 
 * Include this single header to access all functionality.
 */

// Core functionality
#include <duvc-ctl/core/types.h>
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/core/camera.h>
#include <duvc-ctl/core/result.h>
#include <duvc-ctl/core/capability.h>

// Utility functions
#include <duvc-ctl/utils/string_conversion.h>
#include <duvc-ctl/utils/logging.h>
#include <duvc-ctl/utils/error_decoder.h>

// Platform interface (advanced users)
#include <duvc-ctl/platform/interface.h>

// Vendor extensions
#include <duvc-ctl/vendor/constants.h>
#ifdef _WIN32
#include <duvc-ctl/vendor/logitech.h>
#endif

namespace duvc {

/**
 * @defgroup core Core Functionality
 * @brief Device enumeration, camera control, and property management.
 * @{
 */
using ::duvc::list_devices;         ///< Enumerate all connected devices
using ::duvc::is_device_connected;  ///< Check if a device is still connected
/// @}

/**
 * @defgroup quickapi Quick API
 * @brief Simplified one-call camera control functions.
 * 
 * These wrappers provide easy access for CLI tools and casual use cases.
 * They internally use the Camera RAII API but expose a simple `bool` interface.
 * For detailed error handling, use the full Camera API.
 * @{
 */

/**
 * @brief Get a camera control property value.
 * @param dev Device to query
 * @param prop Camera property
 * @param out Output property setting
 * @return true if successful
 */
inline bool get(const Device& dev, CamProp prop, PropSetting& out) {
    Camera cam(dev);
    if (!cam.is_valid()) return false;
    auto res = cam.get(prop);
    if (!res.is_ok()) return false;
    out = res.value();
    return true;
}

/**
 * @brief Set a camera control property value.
 * @param dev Device to modify
 * @param prop Camera property
 * @param in New property setting
 * @return true if successful
 */
inline bool set(const Device& dev, CamProp prop, const PropSetting& in) {
    Camera cam(dev);
    if (!cam.is_valid()) return false;
    return cam.set(prop, in).is_ok();
}

/**
 * @brief Get the valid range for a camera control property.
 * @param dev Device to query
 * @param prop Camera property
 * @param out Output property range
 * @return true if successful
 */
inline bool get_range(const Device& dev, CamProp prop, PropRange& out) {
    Camera cam(dev);
    if (!cam.is_valid()) return false;
    auto res = cam.get_range(prop);
    if (!res.is_ok()) return false;
    out = res.value();
    return true;
}

/**
 * @brief Get a video processing property value.
 * @param dev Device to query
 * @param prop Video property
 * @param out Output property setting
 * @return true if successful
 */
inline bool get(const Device& dev, VidProp prop, PropSetting& out) {
    Camera cam(dev);
    if (!cam.is_valid()) return false;
    auto res = cam.get(prop);
    if (!res.is_ok()) return false;
    out = res.value();
    return true;
}

/**
 * @brief Set a video processing property value.
 * @param dev Device to modify
 * @param prop Video property
 * @param in New property setting
 * @return true if successful
 */
inline bool set(const Device& dev, VidProp prop, const PropSetting& in) {
    Camera cam(dev);
    if (!cam.is_valid()) return false;
    return cam.set(prop, in).is_ok();
}

/**
 * @brief Get the valid range for a video processing property.
 * @param dev Device to query
 * @param prop Video property
 * @param out Output property range
 * @return true if successful
 */
inline bool get_range(const Device& dev, VidProp prop, PropRange& out) {
    Camera cam(dev);
    if (!cam.is_valid()) return false;
    auto res = cam.get_range(prop);
    if (!res.is_ok()) return false;
    out = res.value();
    return true;
}
/// @}

/**
 * @defgroup capabilities Capability Snapshots
 * @brief Functions for capturing supported property sets.
 * @{
 */
using ::duvc::get_device_capabilities; ///< Create a snapshot of device capabilities
/// @}

/**
 * @defgroup utils Utilities
 * @brief String conversions and diagnostic helpers.
 * @{
 */
using ::duvc::to_wstring; ///< Convert properties and modes to wide strings
/// @}

} // namespace duvc
