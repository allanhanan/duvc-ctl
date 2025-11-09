#pragma once

/**
 * @file windows_internal.h
 * @brief Windows-specific internal utilities and constants
 *
 * @internal This header contains implementation details and should not be used
 * directly.
 */

#ifdef _WIN32

#include <string>
#include <windows.h>

namespace duvc::detail {

/**
 * @brief Windows-specific utility functions
 *
 * @internal Internal utilities for Windows platform support.
 */
class WindowsUtils {
public:
  /**
   * @brief Check if current process has camera permissions
   * @return true if camera access is allowed
   */
  static bool has_camera_permissions();

  /**
   * @brief Get Windows version information
   * @return Windows version string
   */
  static std::string get_windows_version();

  /**
   * @brief Check if running on Windows 10 or later
   * @return true if Windows 10+
   */
  static bool is_windows_10_or_later();

  /**
   * @brief Get last Windows error as string
   * @return Formatted error message
   */
  static std::string get_last_error_string();

  /**
   * @brief Convert Windows error code to string
   * @param error_code Windows error code
   * @return Formatted error message
   */
  static std::string error_code_to_string(DWORD error_code);
};

/**
 * @brief DirectShow constants and GUIDs
 *
 * @internal DirectShow constants used throughout the implementation.
 */
namespace DirectShowConstants {

// Camera control property constants (fallback definitions)
/** @var CAMERA_CONTROL_PAN
 * @brief Pan control constant for horizontal rotation */
constexpr long CAMERA_CONTROL_PAN = 0L;

/** @var CAMERA_CONTROL_TILT
 * @brief Tilt control constant for vertical rotation */
constexpr long CAMERA_CONTROL_TILT = 1L;

/** @var CAMERA_CONTROL_ROLL
 * @brief Roll control constant for rotational tilt */
constexpr long CAMERA_CONTROL_ROLL = 2L;

/** @var CAMERA_CONTROL_ZOOM
 * @brief Zoom control constant for optical/digital zoom */
constexpr long CAMERA_CONTROL_ZOOM = 3L;

/** @var CAMERA_CONTROL_EXPOSURE
 * @brief Exposure control constant for shutter speed */
constexpr long CAMERA_CONTROL_EXPOSURE = 4L;

/** @var CAMERA_CONTROL_IRIS
 * @brief Iris control constant for aperture adjustment */
constexpr long CAMERA_CONTROL_IRIS = 5L;

/** @var CAMERA_CONTROL_FOCUS
 * @brief Focus control constant for lens focus */
constexpr long CAMERA_CONTROL_FOCUS = 6L;

/** @var CAMERA_CONTROL_SCANMODE
 * @brief Scan mode control constant for interlaced/progressive */
constexpr long CAMERA_CONTROL_SCANMODE = 7L;

/** @var CAMERA_CONTROL_PRIVACY
 * @brief Privacy mode control constant for lens cover/shutter */
constexpr long CAMERA_CONTROL_PRIVACY = 8L;

// Video proc amp property constants (fallback definitions)
/** @var VIDEOPROCAMP_BRIGHTNESS
 * @brief Brightness control constant for luminance adjustment */
constexpr long VIDEOPROCAMP_BRIGHTNESS = 0L;

/** @var VIDEOPROCAMP_CONTRAST
 * @brief Contrast control constant for dynamic range */
constexpr long VIDEOPROCAMP_CONTRAST = 1L;

/** @var VIDEOPROCAMP_HUE
 * @brief Hue control constant for color tint adjustment */
constexpr long VIDEOPROCAMP_HUE = 2L;

/** @var VIDEOPROCAMP_SATURATION
 * @brief Saturation control constant for color intensity */
constexpr long VIDEOPROCAMP_SATURATION = 3L;

/** @var VIDEOPROCAMP_SHARPNESS
 * @brief Sharpness control constant for edge enhancement */
constexpr long VIDEOPROCAMP_SHARPNESS = 4L;

/** @var VIDEOPROCAMP_GAMMA
 * @brief Gamma control constant for mid-tone brightness */
constexpr long VIDEOPROCAMP_GAMMA = 5L;

/** @var VIDEOPROCAMP_COLORENABLE
 * @brief Color enable control constant for color/monochrome mode */
constexpr long VIDEOPROCAMP_COLORENABLE = 6L;

/** @var VIDEOPROCAMP_WHITEBALANCE
 * @brief White balance control constant for color temperature */
constexpr long VIDEOPROCAMP_WHITEBALANCE = 7L;

/** @var VIDEOPROCAMP_BACKLIGHT_COMPENSATION
 * @brief Backlight compensation control constant for exposure adjustment */
constexpr long VIDEOPROCAMP_BACKLIGHT_COMPENSATION = 8L;

/** @var VIDEOPROCAMP_GAIN
 * @brief Gain control constant for sensor sensitivity */
constexpr long VIDEOPROCAMP_GAIN = 9L;

// Control flags
/** @var FLAGS_AUTO
 * @brief Auto mode flag for automatic property control */
constexpr long FLAGS_AUTO = 0x0001L;

/** @var FLAGS_MANUAL
 * @brief Manual mode flag for manual property control */
constexpr long FLAGS_MANUAL = 0x0002L;

} // namespace duvc::detail

#endif // _WIN32
