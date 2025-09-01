#pragma once

/**
 * @file directshow.h
 * @brief DirectShow-specific declarations and helpers
 */

#ifdef _WIN32

#include <duvc-ctl/detail/com_helpers.h>
#include <duvc-ctl/core/types.h>
#include <dshow.h>

namespace duvc {

// Forward declarations for DirectShow interfaces
using namespace detail;

/**
 * @brief Create DirectShow device enumerator
 * @return COM pointer to ICreateDevEnum
 */
com_ptr<ICreateDevEnum> create_dev_enum();

/**
 * @brief Enumerate video input devices
 * @param dev Device enumerator
 * @return COM pointer to IEnumMoniker for video devices
 */
com_ptr<IEnumMoniker> enum_video_devices(ICreateDevEnum* dev);

/**
 * @brief Read friendly name from device moniker
 * @param mon Device moniker
 * @return Device friendly name
 */
std::wstring read_friendly_name(IMoniker* mon);

/**
 * @brief Read device path from moniker
 * @param mon Device moniker  
 * @return Device path
 */
std::wstring read_device_path(IMoniker* mon);

/**
 * @brief Check if two device identifiers refer to same device
 * @param d Device structure to compare
 * @param name Device name from enumeration
 * @param path Device path from enumeration
 * @return true if same device
 */
bool is_same_device(const Device& d, const std::wstring& name, const std::wstring& path);

/**
 * @brief Create DirectShow filter from device
 * @param dev Device to open
 * @return COM pointer to IBaseFilter
 */
com_ptr<IBaseFilter> open_device_filter(const Device& dev);

} // namespace duvc

#endif // _WIN32
