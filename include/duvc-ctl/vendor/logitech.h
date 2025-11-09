#pragma once

/**
 * @file logitech.h
 * @brief Logitech-specific vendor property definitions and helpers
 *
 * Provides typed access to Logitech UVC extension unit properties including
 * RightLight, face tracking, LED control, and other vendor-specific features.
 */

#ifdef _WIN32

#include <duvc-ctl/core/result.h>
#include <duvc-ctl/core/types.h>
#include <vector>
#include <windows.h>

namespace duvc::logitech {

/**
 * @brief Logitech vendor-specific property set GUID
 *
 * Identifies Logitech's UVC extension unit for all vendor properties.
 * Defined as inline constexpr for C++17 compatibility without ODR violations.
 *
 * GUID: {82066163-7BD0-43EF-8A6F-5B8905C9A64C}
 */
inline constexpr GUID LOGITECH_PROPERTY_SET = {
    0x82066163,
    0x7BD0,
    0x43EF,
    {0x8A, 0x6F, 0x5B, 0x89, 0x05, 0xC9, 0xA6, 0x4C}};

/**
 * @brief Logitech vendor property IDs
 *
 * Enumeration of supported Logitech extension unit properties.
 * Values correspond to property IDs within LOGITECH_PROPERTY_SET.
 */
enum class LogitechProperty : uint32_t {
  RightLight = 1,     ///< RightLight auto-exposure and brightness optimization
  RightSound = 2,     ///< RightSound audio processing and noise cancellation
  FaceTracking = 3,   ///< Face tracking enable/disable for auto-framing
  LedIndicator = 4,   ///< LED indicator control (on/off/blink modes)
  ProcessorUsage = 5, ///< Processor usage optimization hints
  RawDataBits = 6,    ///< Raw data bit depth configuration
  FocusAssist = 7,    ///< Focus assist beam control
  VideoStandard = 8,  ///< Video standard selection (NTSC/PAL/etc)
  DigitalZoomROI = 9, ///< Digital zoom region of interest coordinates
  TiltPan = 10,       ///< Combined tilt/pan control (absolute positioning)
};

/**
 * @brief Get Logitech vendor property as raw byte vector
 * @param device Target device to query
 * @param prop Logitech property ID to read
 * @return Result containing property data buffer on success, or error on
 * failure
 */
Result<std::vector<uint8_t>> get_logitech_property(const Device &device,
                                                   LogitechProperty prop);

/**
 * @brief Set Logitech vendor property from raw byte vector
 * @param device Target device to modify
 * @param prop Logitech property ID to write
 * @param data Property data buffer (format depends on property type)
 * @return Result indicating success or error
 */
Result<void> set_logitech_property(const Device &device, LogitechProperty prop,
                                   const std::vector<uint8_t> &data);

/**
 * @brief Check if device supports Logitech vendor properties
 * @param device Device to check for Logitech extension unit support
 * @return Result containing true if supported, false otherwise, or error on
 * query failure
 */
Result<bool> supports_logitech_properties(const Device &device);

/**
 * @brief Get typed Logitech property value
 *
 * Template function that reads property data and reinterprets as specified
 * type. Type T must be trivially copyable and match the property's binary
 * layout.
 *
 * @tparam T Property value type (must be trivially copyable)
 * @param device Target device to query
 * @param prop Logitech property ID to read
 * @return Result containing typed value on success, or error on failure
 * @note Caller must ensure T matches the property's actual data format
 */
template <typename T>
Result<T> get_logitech_property_typed(const Device &device,
                                      LogitechProperty prop);

/**
 * @brief Set typed Logitech property value
 *
 * Template function that writes typed value as raw binary property data.
 * Type T must be trivially copyable and match the property's binary layout.
 *
 * @tparam T Property value type (must be trivially copyable)
 * @param device Target device to modify
 * @param prop Logitech property ID to write
 * @param value Property value to set (will be reinterpreted as bytes)
 * @return Result indicating success or error
 * @note Caller must ensure T matches the property's expected data format
 */
template <typename T>
Result<void> set_logitech_property_typed(const Device &device,
                                         LogitechProperty prop, const T &value);

} // namespace duvc::logitech

#endif // _WIN32
