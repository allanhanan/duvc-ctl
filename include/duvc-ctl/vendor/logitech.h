#pragma once

/**
 * @file logitech.h
 * @brief Logitech-specific property definitions and helpers
 */

#ifdef _WIN32
#include <windows.h>
#include <vector>
#include <duvc-ctl/core/types.h>
#include <duvc-ctl/core/result.h>

namespace duvc::logitech {

/**
 * @brief Logitech vendor-specific property set GUID
 */
extern const GUID LOGITECH_PROPERTY_SET;

/**
 * @brief Logitech vendor property IDs
 */
enum class LogitechProperty : uint32_t {
    RightLight = 1,           ///< RightLight auto-exposure
    RightSound = 2,           ///< RightSound audio processing  
    FaceTracking = 3,         ///< Face tracking enable/disable
    LedIndicator = 4,         ///< LED indicator control
    ProcessorUsage = 5,       ///< Processor usage optimization
    RawDataBits = 6,          ///< Raw data bit depth
    FocusAssist = 7,          ///< Focus assist beam
    VideoStandard = 8,        ///< Video standard selection
    DigitalZoomROI = 9,       ///< Digital zoom region of interest
    TiltPan = 10,             ///< Combined tilt/pan control
};

/**
 * @brief Get Logitech vendor property
 * @param device Target device
 * @param prop Logitech property ID
 * @return Result containing property data or error
 */
Result<std::vector<uint8_t>> get_logitech_property(const Device& device, LogitechProperty prop);

/**
 * @brief Set Logitech vendor property
 * @param device Target device
 * @param prop Logitech property ID
 * @param data Property data to set
 * @return Result indicating success or error
 */
Result<void> set_logitech_property(const Device& device, LogitechProperty prop, 
                                  const std::vector<uint8_t>& data);

/**
 * @brief Check if device supports Logitech vendor properties
 * @param device Device to check
 * @return Result containing support status or error
 */
Result<bool> supports_logitech_properties(const Device& device);

/**
 * @brief Get typed Logitech property value
 * @tparam T Property value type
 * @param device Target device
 * @param prop Logitech property ID
 * @return Result containing typed value or error
 */
template<typename T>
Result<T> get_logitech_property_typed(const Device& device, LogitechProperty prop);

/**
 * @brief Set typed Logitech property value
 * @tparam T Property value type
 * @param device Target device
 * @param prop Logitech property ID
 * @param value Property value to set
 * @return Result indicating success or error
 */
template<typename T>
Result<void> set_logitech_property_typed(const Device& device, LogitechProperty prop, const T& value);

} // namespace duvc::logitech

#endif // _WIN32
