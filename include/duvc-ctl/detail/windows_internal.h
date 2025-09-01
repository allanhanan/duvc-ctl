#pragma once

/**
 * @file windows_internal.h
 * @brief Windows-specific internal utilities and constants
 * 
 * @internal This header contains implementation details and should not be used directly.
 */

#ifdef _WIN32

#include <windows.h>
#include <string>

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
    constexpr long CAMERA_CONTROL_PAN = 0L;
    constexpr long CAMERA_CONTROL_TILT = 1L;
    constexpr long CAMERA_CONTROL_ROLL = 2L;
    constexpr long CAMERA_CONTROL_ZOOM = 3L;
    constexpr long CAMERA_CONTROL_EXPOSURE = 4L;
    constexpr long CAMERA_CONTROL_IRIS = 5L;
    constexpr long CAMERA_CONTROL_FOCUS = 6L;
    constexpr long CAMERA_CONTROL_SCANMODE = 7L;
    constexpr long CAMERA_CONTROL_PRIVACY = 8L;
    
    // Video proc amp property constants (fallback definitions)
    constexpr long VIDEOPROCAMP_BRIGHTNESS = 0L;
    constexpr long VIDEOPROCAMP_CONTRAST = 1L;
    constexpr long VIDEOPROCAMP_HUE = 2L;
    constexpr long VIDEOPROCAMP_SATURATION = 3L;
    constexpr long VIDEOPROCAMP_SHARPNESS = 4L;
    constexpr long VIDEOPROCAMP_GAMMA = 5L;
    constexpr long VIDEOPROCAMP_COLORENABLE = 6L;
    constexpr long VIDEOPROCAMP_WHITEBALANCE = 7L;
    constexpr long VIDEOPROCAMP_BACKLIGHT_COMPENSATION = 8L;
    constexpr long VIDEOPROCAMP_GAIN = 9L;
    
    // Control flags
    constexpr long FLAGS_AUTO = 0x0001L;
    constexpr long FLAGS_MANUAL = 0x0002L;
}

} // namespace duvc::detail

#endif // _WIN32
