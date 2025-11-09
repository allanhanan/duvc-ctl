#pragma once

/**
 * @file types.h
 * @brief Core data types and enumerations for duvc-ctl
 */

#include <string>

namespace duvc {

/**
 * @brief Camera control properties (IAMCameraControl interface)
 *
 * These properties correspond to DirectShow's IAMCameraControl interface
 * and control physical camera mechanisms.
 */
enum class CamProp {
  Pan,                   ///< Horizontal camera rotation
  Tilt,                  ///< Vertical camera rotation
  Roll,                  ///< Camera roll rotation
  Zoom,                  ///< Optical zoom level
  Exposure,              ///< Exposure time
  Iris,                  ///< Aperture/iris setting
  Focus,                 ///< Focus position
  ScanMode,              ///< Scan mode (progressive/interlaced)
  Privacy,               ///< Privacy mode on/off
  PanRelative,           ///< Relative pan movement
  TiltRelative,          ///< Relative tilt movement
  RollRelative,          ///< Relative roll movement
  ZoomRelative,          ///< Relative zoom movement
  ExposureRelative,      ///< Relative exposure adjustment
  IrisRelative,          ///< Relative iris adjustment
  FocusRelative,         ///< Relative focus adjustment
  PanTilt,               ///< Combined pan/tilt control
  PanTiltRelative,       ///< Relative pan/tilt movement
  FocusSimple,           ///< Simple focus control
  DigitalZoom,           ///< Digital zoom level
  DigitalZoomRelative,   ///< Relative digital zoom
  BacklightCompensation, ///< Backlight compensation
  Lamp                   ///< Camera lamp/flash control
};

/**
 * @brief Video processing properties (IAMVideoProcAmp interface)
 *
 * These properties correspond to DirectShow's IAMVideoProcAmp interface
 * and control image processing parameters.
 */
enum class VidProp {
  Brightness,            ///< Image brightness level
  Contrast,              ///< Image contrast level
  Hue,                   ///< Color hue adjustment
  Saturation,            ///< Color saturation level
  Sharpness,             ///< Image sharpness level
  Gamma,                 ///< Gamma correction value
  ColorEnable,           ///< Color vs. monochrome mode
  WhiteBalance,          ///< White balance adjustment
  BacklightCompensation, ///< Backlight compensation level
  Gain                   ///< Sensor gain level
};

/**
 * @brief Property control mode
 */
enum class CamMode {
  Auto,  ///< Automatic control by camera
  Manual ///< Manual control by application
};

/**
 * @brief Property setting with value and control mode
 */
struct PropSetting {
  int value;    ///< Property value
  CamMode mode; ///< Control mode (auto/manual)

  /// Default constructor
  PropSetting() = default;

  /**
   * @brief Construct property setting
   * @param v Property value
   * @param m Control mode
   */
  PropSetting(int v, CamMode m) : value(v), mode(m) {}
};

/**
 * @brief Property range and default information
 */
struct PropRange {
  int min;              ///< Minimum supported value
  int max;              ///< Maximum supported value
  int step;             ///< Step size between valid values
  int default_val;      ///< Default value
  CamMode default_mode; ///< Default control mode

  /// Default constructor
  PropRange() = default;

  /**
   * @brief Check if a value is valid for this range
   * @param value Value to check
   * @return true if value is within range and aligned to step
   */
  bool is_valid(int value) const {
    return value >= min && value <= max && ((value - min) % step == 0);
  }

  /**
   * @brief Clamp value to valid range
   * @param value Value to clamp
   * @return Nearest valid value within range
   */
  int clamp(int value) const {
    if (value <= min)
      return min;
    if (value >= max)
      return max;

    // Round to nearest step
    int steps = (value - min + step / 2) / step;
    return min + steps * step;
  }
};

/**
 * @brief Represents a camera device
 */
struct Device {
  std::wstring name; ///< Human-readable device name
  std::wstring path; ///< Unique device path/identifier

  /// Default constructor
  Device() = default;

  /**
   * @brief Construct device with name and path
   * @param n Device name
   * @param p Device path
   */
  Device(std::wstring n, std::wstring p)
      : name(std::move(n)), path(std::move(p)) {}

  /**
   * @brief Check if device has valid identifying information
   * @return true if either name or path is non-empty
   */
  bool is_valid() const { return !name.empty() || !path.empty(); }

  /**
   * @brief Get stable identifier for this device
   * @return Path if available, otherwise name
   */
  const std::wstring &get_id() const { return path.empty() ? name : path; }
};

} // namespace duvc
