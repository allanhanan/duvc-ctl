#pragma once
/**
 * @file api.h
 * @brief Complete C ABI for duvc-ctl with comprehensive API coverage
 *
 * Provides stable interface for C and language bindings with full functionality
 * matching the modern C++ core API with Result-based error handling.
 */
#ifdef __cplusplus
extern "C" {
#endif
#include <stdint.h>
#include <stddef.h>

/* ========================================================================
 * Version and ABI Constants
 * ======================================================================== */
#define DUVC_VERSION_MAJOR 1
#define DUVC_VERSION_MINOR 0
#define DUVC_VERSION_PATCH 0
#define DUVC_ABI_VERSION ((DUVC_VERSION_MAJOR << 16) | (DUVC_VERSION_MINOR << 8) | DUVC_VERSION_PATCH)

/* ========================================================================
 * Core Enumerations
 * ======================================================================== */
/**
 * @brief Result codes for duvc operations
 */
typedef enum {
    DUVC_SUCCESS = 0,                    /**< Operation completed successfully */
    DUVC_ERROR_NOT_IMPLEMENTED,          /**< Feature not implemented on this platform */
    DUVC_ERROR_INVALID_ARGUMENT,         /**< Invalid function argument provided */
    DUVC_ERROR_DEVICE_NOT_FOUND,         /**< Device not found or disconnected */
    DUVC_ERROR_DEVICE_BUSY,              /**< Device is busy or in use by another process */
    DUVC_ERROR_PROPERTY_NOT_SUPPORTED,   /**< Property not supported by device */
    DUVC_ERROR_INVALID_VALUE,            /**< Property value out of valid range */
    DUVC_ERROR_PERMISSION_DENIED,        /**< Insufficient permissions to access device */
    DUVC_ERROR_SYSTEM_ERROR,             /**< System/platform error occurred */
    DUVC_ERROR_CONNECTION_FAILED,        /**< Failed to establish device connection */
    DUVC_ERROR_TIMEOUT,                  /**< Operation timed out */
    DUVC_ERROR_BUFFER_TOO_SMALL          /**< Provided buffer is too small for data */
} duvc_result_t;

/**
 * @brief Camera control properties
 */
typedef enum {
    DUVC_CAM_PROP_PAN = 0,               /**< Horizontal camera rotation */
    DUVC_CAM_PROP_TILT,                  /**< Vertical camera rotation */
    DUVC_CAM_PROP_ROLL,                  /**< Camera roll rotation */
    DUVC_CAM_PROP_ZOOM,                  /**< Optical zoom level */
    DUVC_CAM_PROP_EXPOSURE,              /**< Exposure time */
    DUVC_CAM_PROP_IRIS,                  /**< Aperture/iris setting */
    DUVC_CAM_PROP_FOCUS,                 /**< Focus position */
    DUVC_CAM_PROP_SCAN_MODE,             /**< Scan mode (progressive/interlaced) */
    DUVC_CAM_PROP_PRIVACY,               /**< Privacy mode on/off */
    DUVC_CAM_PROP_PAN_RELATIVE,          /**< Relative pan movement */
    DUVC_CAM_PROP_TILT_RELATIVE,         /**< Relative tilt movement */
    DUVC_CAM_PROP_ROLL_RELATIVE,         /**< Relative roll movement */
    DUVC_CAM_PROP_ZOOM_RELATIVE,         /**< Relative zoom movement */
    DUVC_CAM_PROP_EXPOSURE_RELATIVE,     /**< Relative exposure adjustment */
    DUVC_CAM_PROP_IRIS_RELATIVE,         /**< Relative iris adjustment */
    DUVC_CAM_PROP_FOCUS_RELATIVE,        /**< Relative focus adjustment */
    DUVC_CAM_PROP_PAN_TILT,              /**< Combined pan/tilt control */
    DUVC_CAM_PROP_PAN_TILT_RELATIVE,     /**< Relative pan/tilt movement */
    DUVC_CAM_PROP_FOCUS_SIMPLE,          /**< Simple focus control */
    DUVC_CAM_PROP_DIGITAL_ZOOM,          /**< Digital zoom level */
    DUVC_CAM_PROP_DIGITAL_ZOOM_RELATIVE, /**< Relative digital zoom */
    DUVC_CAM_PROP_BACKLIGHT_COMPENSATION,/**< Backlight compensation */
    DUVC_CAM_PROP_LAMP                   /**< Camera lamp/flash control */
} duvc_cam_prop_t;

/**
 * @brief Video processing properties
 */
typedef enum {
    DUVC_VID_PROP_BRIGHTNESS = 0,        /**< Image brightness level */
    DUVC_VID_PROP_CONTRAST,              /**< Image contrast level */
    DUVC_VID_PROP_HUE,                   /**< Color hue adjustment */
    DUVC_VID_PROP_SATURATION,            /**< Color saturation level */
    DUVC_VID_PROP_SHARPNESS,             /**< Image sharpness level */
    DUVC_VID_PROP_GAMMA,                 /**< Gamma correction value */
    DUVC_VID_PROP_COLOR_ENABLE,          /**< Color vs. monochrome mode */
    DUVC_VID_PROP_WHITE_BALANCE,         /**< White balance adjustment */
    DUVC_VID_PROP_BACKLIGHT_COMPENSATION,/**< Backlight compensation level */
    DUVC_VID_PROP_GAIN                   /**< Sensor gain level */
} duvc_vid_prop_t;

/**
 * @brief Camera control modes
 */
typedef enum {
    DUVC_CAM_MODE_AUTO = 0,              /**< Automatic control by camera */
    DUVC_CAM_MODE_MANUAL                 /**< Manual control by application */
} duvc_cam_mode_t;

/**
 * @brief Log levels
 */
typedef enum {
    DUVC_LOG_DEBUG = 0,                  /**< Debug information */
    DUVC_LOG_INFO,                       /**< Informational messages */
    DUVC_LOG_WARNING,                    /**< Warning messages */
    DUVC_LOG_ERROR,                      /**< Error messages */
    DUVC_LOG_CRITICAL                    /**< Critical errors */
} duvc_log_level_t;

/**
 * @brief Logitech vendor-specific properties
 */
typedef enum {
    DUVC_LOGITECH_PROP_RIGHT_LIGHT = 1,  /**< RightLight auto-exposure */
    DUVC_LOGITECH_PROP_RIGHT_SOUND,      /**< RightSound audio processing */
    DUVC_LOGITECH_PROP_FACE_TRACKING,    /**< Face tracking enable/disable */
    DUVC_LOGITECH_PROP_LED_INDICATOR,    /**< LED indicator control */
    DUVC_LOGITECH_PROP_PROCESSOR_USAGE,  /**< Processor usage optimization */
    DUVC_LOGITECH_PROP_RAW_DATA_BITS,    /**< Raw data bit depth */
    DUVC_LOGITECH_PROP_FOCUS_ASSIST,     /**< Focus assist beam */
    DUVC_LOGITECH_PROP_VIDEO_STANDARD,   /**< Video standard selection */
    DUVC_LOGITECH_PROP_DIGITAL_ZOOM_ROI, /**< Digital zoom region of interest */
    DUVC_LOGITECH_PROP_TILT_PAN          /**< Combined tilt/pan control */
} duvc_logitech_prop_t;

/* ========================================================================
 * Core Data Structures
 * ======================================================================== */
/**
 * @brief Property setting with value and mode
 */
typedef struct {
    int32_t value;                       /**< Property value */
    duvc_cam_mode_t mode;                /**< Control mode (auto/manual) */
} duvc_prop_setting_t;

/**
 * @brief Property range information
 */
typedef struct {
    int32_t min;                         /**< Minimum supported value */
    int32_t max;                         /**< Maximum supported value */
    int32_t step;                        /**< Step size between valid values */
    int32_t default_val;                 /**< Default value */
    duvc_cam_mode_t default_mode;        /**< Default control mode */
} duvc_prop_range_t;

/**
 * @brief Vendor property container
 */
typedef struct {
    char property_set_guid[39];          /**< GUID as string {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx} */
    uint32_t property_id;                /**< Property ID within set */
    void* data;                          /**< Property data payload */
    size_t data_size;                    /**< Size of data in bytes */
} duvc_vendor_property_t;

/**
 * @brief Opaque device handle
 */
typedef struct duvc_device_t duvc_device_t;

/**
 * @brief Opaque camera connection handle
 */
typedef struct duvc_connection_t duvc_connection_t;

/**
 * @brief Opaque device capabilities handle
 */
typedef struct duvc_device_capabilities_t duvc_device_capabilities_t;

/* ========================================================================
 * Callback Types
 * ======================================================================== */
/**
 * @brief Log message callback
 * @param level Log level of the message
 * @param message Null-terminated log message string
 * @param user_data User-provided context data
 */
typedef void (*duvc_log_callback)(duvc_log_level_t level, const char* message, void* user_data);

/**
 * @brief Device hotplug callback
 * @param added 1 if device was added, 0 if removed
 * @param device_path Null-terminated device path string
 * @param user_data User-provided context data
 */
typedef void (*duvc_device_change_callback)(int added, const char* device_path, void* user_data);

/* ========================================================================
 * Constants
 * ======================================================================== */
/**
 * @brief Logitech property set GUID string
 */
extern const char DUVC_LOGITECH_PROPERTY_SET_GUID[39];

/* ========================================================================
 * Version and ABI Management
 * ======================================================================== */
/**
 * @brief Get library version
 * @return Combined version number as returned by DUVC_ABI_VERSION macro
 */
uint32_t duvc_get_version(void);

/**
 * @brief Get library version string
 * @return Null-terminated version string (e.g., "1.0.0")
 * @note Returned string is statically allocated and should not be freed
 */
const char* duvc_get_version_string(void);

/**
 * @brief Check ABI compatibility
 * @param compiled_version Version the application was compiled with (use DUVC_ABI_VERSION)
 * @return 1 if compatible, 0 if incompatible
 */
int duvc_check_abi_compatibility(uint32_t compiled_version);

/* ========================================================================
 * Library Lifecycle
 * ======================================================================== */
/**
 * @brief Initialize library
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_initialize(void);

/**
 * @brief Shutdown library
 * @note Cleans up all resources and connections
 */
void duvc_shutdown(void);

/**
 * @brief Check if library is initialized
 * @return 1 if initialized, 0 if not
 */
int duvc_is_initialized(void);

/* ========================================================================
 * Logging System
 * ======================================================================== */
/**
 * @brief Set log callback
 * @param callback Log callback function (NULL to disable logging)
 * @param user_data User data passed to callback
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_log_callback(duvc_log_callback callback, void* user_data);

/**
 * @brief Set minimum log level
 * @param level Minimum level to log
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_log_level(duvc_log_level_t level);

/**
 * @brief Get current log level
 * @param[out] level Current minimum log level
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_log_level(duvc_log_level_t* level);

/**
 * @brief Log message at specific level
 * @param level Log level
 * @param message Message to log
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_log_message(duvc_log_level_t level, const char* message);

/**
 * @brief Log debug message
 * @param message Debug message to log
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_log_debug(const char* message);

/**
 * @brief Log info message
 * @param message Info message to log
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_log_info(const char* message);

/**
 * @brief Log warning message
 * @param message Warning message to log
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_log_warning(const char* message);

/**
 * @brief Log error message
 * @param message Error message to log
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_log_error(const char* message);

/**
 * @brief Log critical message
 * @param message Critical message to log
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_log_critical(const char* message);

/* ========================================================================
 * Device Management
 * ======================================================================== */
/**
 * @brief List all connected devices
 * @param[out] devices Pointer to receive device array
 * @param[out] count Number of devices found
 * @return DUVC_SUCCESS on success, error code on failure
 * 
 * @note Caller must free with duvc_free_device_list()
 */
duvc_result_t duvc_list_devices(duvc_device_t*** devices, size_t* count);

/**
 * @brief Free device list
 * @param devices Device array to free
 * @param count Number of devices in array
 */
void duvc_free_device_list(duvc_device_t** devices, size_t count);

/**
 * @brief Check if device is connected
 * @param device Device to check
 * @param[out] connected 1 if connected, 0 if not
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_is_device_connected(const duvc_device_t* device, int* connected);

/**
 * @brief Get device name
 * @param device Device to query
 * @param[out] buffer Buffer to receive name
 * @param buffer_size Size of buffer in bytes
 * @param[out] required Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_device_name(const duvc_device_t* device, char* buffer, size_t buffer_size, size_t* required);

/**
 * @brief Get device path
 * @param device Device to query
 * @param[out] buffer Buffer to receive path
 * @param buffer_size Size of buffer in bytes
 * @param[out] required Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_device_path(const duvc_device_t* device, char* buffer, size_t buffer_size, size_t* required);

/**
 * @brief Get device ID
 * @param device Device to query
 * @param[out] buffer Buffer to receive ID
 * @param buffer_size Size of buffer in bytes
 * @param[out] required Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_device_id(const duvc_device_t* device, char* buffer, size_t buffer_size, size_t* required);

/**
 * @brief Check if device is valid
 * @param device Device to check
 * @param[out] valid 1 if valid, 0 if not
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_device_is_valid(const duvc_device_t* device, int* valid);

/* ========================================================================
 * Device Change Monitoring
 * ======================================================================== */
/**
 * @brief Register device change callback
 * @param callback Callback function to register
 * @param user_data User data to pass to callback
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_register_device_change_callback(duvc_device_change_callback callback, void* user_data);

/**
 * @brief Unregister device change callback
 * @note Stops monitoring device changes and cleans up resources
 */
void duvc_unregister_device_change_callback(void);

/* ========================================================================
 * Camera Connections
 * ======================================================================== */
/**
 * @brief Open camera by device index
 * @param device_index Index from duvc_list_devices()
 * @param[out] conn Pointer to receive connection handle
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_open_camera_by_index(int device_index, duvc_connection_t** conn);

/**
 * @brief Open camera by device handle
 * @param device Device to connect to
 * @param[out] conn Pointer to receive connection handle
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_open_camera(const duvc_device_t* device, duvc_connection_t** conn);

/**
 * @brief Close camera connection
 * @param conn Connection to close
 */
void duvc_close_camera(duvc_connection_t* conn);

/**
 * @brief Check if camera connection is valid
 * @param conn Connection to check
 * @return 1 if valid, 0 if not
 */
int duvc_camera_is_valid(const duvc_connection_t* conn);

/* ========================================================================
 * Property Access - Single Properties
 * ======================================================================== */
/**
 * @brief Get camera property value
 * @param conn Camera connection
 * @param prop Camera property to query
 * @param[out] setting Property setting (value and mode)
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_camera_property(duvc_connection_t* conn, duvc_cam_prop_t prop, duvc_prop_setting_t* setting);

/**
 * @brief Set camera property value
 * @param conn Camera connection
 * @param prop Camera property to set
 * @param setting Property setting to apply
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_camera_property(duvc_connection_t* conn, duvc_cam_prop_t prop, const duvc_prop_setting_t* setting);

/**
 * @brief Get camera property range
 * @param conn Camera connection
 * @param prop Camera property to query
 * @param[out] range Property range information
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_camera_property_range(duvc_connection_t* conn, duvc_cam_prop_t prop, duvc_prop_range_t* range);

/**
 * @brief Get video property value
 * @param conn Camera connection
 * @param prop Video property to query
 * @param[out] setting Property setting (value and mode)
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_video_property(duvc_connection_t* conn, duvc_vid_prop_t prop, duvc_prop_setting_t* setting);

/**
 * @brief Set video property value
 * @param conn Camera connection
 * @param prop Video property to set
 * @param setting Property setting to apply
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_video_property(duvc_connection_t* conn, duvc_vid_prop_t prop, const duvc_prop_setting_t* setting);

/**
 * @brief Get video property range
 * @param conn Camera connection
 * @param prop Video property to query
 * @param[out] range Property range information
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_video_property_range(duvc_connection_t* conn, duvc_vid_prop_t prop, duvc_prop_range_t* range);

/* ========================================================================
 * Property Access - Multiple Properties
 * ======================================================================== */
/**
 * @brief Get multiple camera properties
 * @param conn Camera connection
 * @param props Array of camera properties to query
 * @param[out] settings Array to receive property settings
 * @param count Number of properties in arrays
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_multiple_camera_properties(duvc_connection_t* conn, const duvc_cam_prop_t* props, duvc_prop_setting_t* settings, size_t count);

/**
 * @brief Set multiple camera properties
 * @param conn Camera connection
 * @param props Array of camera properties to set
 * @param settings Array of property settings to apply
 * @param count Number of properties in arrays
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_multiple_camera_properties(duvc_connection_t* conn, const duvc_cam_prop_t* props, const duvc_prop_setting_t* settings, size_t count);

/**
 * @brief Get multiple video properties
 * @param conn Camera connection
 * @param props Array of video properties to query
 * @param[out] settings Array to receive property settings
 * @param count Number of properties in arrays
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_multiple_video_properties(duvc_connection_t* conn, const duvc_vid_prop_t* props, duvc_prop_setting_t* settings, size_t count);

/**
 * @brief Set multiple video properties
 * @param conn Camera connection
 * @param props Array of video properties to set
 * @param settings Array of property settings to apply
 * @param count Number of properties in arrays
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_multiple_video_properties(duvc_connection_t* conn, const duvc_vid_prop_t* props, const duvc_prop_setting_t* settings, size_t count);

/* ========================================================================
 * Quick API - Direct Device Access
 * ======================================================================== */
/**
 * @brief Quick get camera property (creates temporary connection)
 * @param device Device to query
 * @param prop Camera property to get
 * @param[out] setting Property setting (value and mode)
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_quick_get_camera_property(const duvc_device_t* device, duvc_cam_prop_t prop, duvc_prop_setting_t* setting);

/**
 * @brief Quick set camera property (creates temporary connection)
 * @param device Device to modify
 * @param prop Camera property to set
 * @param setting Property setting to apply
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_quick_set_camera_property(const duvc_device_t* device, duvc_cam_prop_t prop, const duvc_prop_setting_t* setting);

/**
 * @brief Quick get camera property range
 * @param device Device to query
 * @param prop Camera property to query
 * @param[out] range Property range information
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_quick_get_camera_property_range(const duvc_device_t* device, duvc_cam_prop_t prop, duvc_prop_range_t* range);

/**
 * @brief Quick get video property
 * @param device Device to query
 * @param prop Video property to get
 * @param[out] setting Property setting (value and mode)
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_quick_get_video_property(const duvc_device_t* device, duvc_vid_prop_t prop, duvc_prop_setting_t* setting);

/**
 * @brief Quick set video property
 * @param device Device to modify
 * @param prop Video property to set
 * @param setting Property setting to apply
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_quick_set_video_property(const duvc_device_t* device, duvc_vid_prop_t prop, const duvc_prop_setting_t* setting);

/**
 * @brief Quick get video property range
 * @param device Device to query
 * @param prop Video property to query
 * @param[out] range Property range information
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_quick_get_video_property_range(const duvc_device_t* device, duvc_vid_prop_t prop, duvc_prop_range_t* range);

/* ========================================================================
 * Device Capability Snapshots
 * ======================================================================== */
/**
 * @brief Get device capabilities snapshot
 * @param device Device to analyze
 * @param[out] caps Pointer to receive capabilities handle
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_device_capabilities(const duvc_device_t* device, duvc_device_capabilities_t** caps);

/**
 * @brief Get device capabilities by index
 * @param device_index Device index from duvc_list_devices()
 * @param[out] caps Pointer to receive capabilities handle
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_device_capabilities_by_index(int device_index, duvc_device_capabilities_t** caps);

/**
 * @brief Free device capabilities
 * @param caps Capabilities handle to free
 */
void duvc_free_device_capabilities(duvc_device_capabilities_t* caps);

/**
 * @brief Refresh capabilities snapshot
 * @param caps Capabilities handle to refresh
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_refresh_device_capabilities(duvc_device_capabilities_t* caps);

/* ========================================================================
 * Capability Queries
 * ======================================================================== */
/**
 * @brief Get camera property capability
 * @param caps Device capabilities handle
 * @param prop Camera property to query
 * @param[out] range Property range (can be NULL if not needed)
 * @param[out] current Current property value (can be NULL if not needed)
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_camera_capability(const duvc_device_capabilities_t* caps, duvc_cam_prop_t prop, duvc_prop_range_t* range, duvc_prop_setting_t* current);

/**
 * @brief Get video property capability
 * @param caps Device capabilities handle
 * @param prop Video property to query
 * @param[out] range Property range (can be NULL if not needed)
 * @param[out] current Current property value (can be NULL if not needed)
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_video_capability(const duvc_device_capabilities_t* caps, duvc_vid_prop_t prop, duvc_prop_range_t* range, duvc_prop_setting_t* current);

/**
 * @brief Check if camera property is supported
 * @param caps Device capabilities handle
 * @param prop Camera property to check
 * @param[out] supported 1 if supported, 0 if not
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_supports_camera_property(const duvc_device_capabilities_t* caps, duvc_cam_prop_t prop, int* supported);

/**
 * @brief Check if video property is supported
 * @param caps Device capabilities handle
 * @param prop Video property to check
 * @param[out] supported 1 if supported, 0 if not
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_supports_video_property(const duvc_device_capabilities_t* caps, duvc_vid_prop_t prop, int* supported);

/**
 * @brief Get list of supported camera properties
 * @param caps Device capabilities handle
 * @param[out] props Array to receive supported properties
 * @param max_count Maximum number of properties that can be stored
 * @param[out] actual_count Actual number of supported properties
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if array too small
 */
duvc_result_t duvc_get_supported_camera_properties(const duvc_device_capabilities_t* caps, duvc_cam_prop_t* props, size_t max_count, size_t* actual_count);

/**
 * @brief Get list of supported video properties
 * @param caps Device capabilities handle
 * @param[out] props Array to receive supported properties
 * @param max_count Maximum number of properties that can be stored
 * @param[out] actual_count Actual number of supported properties
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if array too small
 */
duvc_result_t duvc_get_supported_video_properties(const duvc_device_capabilities_t* caps, duvc_vid_prop_t* props, size_t max_count, size_t* actual_count);

/**
 * @brief Check if device is accessible
 * @param caps Device capabilities handle
 * @param[out] accessible 1 if accessible, 0 if not
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_capabilities_is_device_accessible(const duvc_device_capabilities_t* caps, int* accessible);

/* ========================================================================
 * Property Range Utilities
 * ======================================================================== */
/**
 * @brief Check if value is valid for range
 * @param range Property range to check against
 * @param value Value to validate
 * @param[out] valid 1 if valid, 0 if not
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_prop_range_is_valid(const duvc_prop_range_t* range, int32_t value, int* valid);

/**
 * @brief Clamp value to valid range
 * @param range Property range to clamp to
 * @param value Value to clamp
 * @param[out] clamped_value Clamped value within range
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_prop_range_clamp(const duvc_prop_range_t* range, int32_t value, int32_t* clamped_value);

/**
 * @brief Check if property supports auto mode
 * @param range Property range to check
 * @param[out] supports_auto 1 if auto mode supported, 0 if not
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_prop_capability_supports_auto(const duvc_prop_range_t* range, int* supports_auto);

/* ========================================================================
 * Generic Vendor Properties
 * ======================================================================== */
/**
 * @brief Get vendor-specific property
 * @param device Target device
 * @param property_set_guid Property set GUID as string
 * @param property_id Property ID within set
 * @param[out] data Buffer to receive property data
 * @param data_size Size of data buffer
 * @param[out] bytes_returned Actual bytes returned
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_vendor_property(const duvc_device_t* device, const char* property_set_guid, uint32_t property_id, void* data, size_t data_size, size_t* bytes_returned);

/**
 * @brief Set vendor-specific property
 * @param device Target device
 * @param property_set_guid Property set GUID as string
 * @param property_id Property ID within set
 * @param data Property data to set
 * @param data_size Size of property data
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_vendor_property(const duvc_device_t* device, const char* property_set_guid, uint32_t property_id, const void* data, size_t data_size);

/**
 * @brief Query vendor property support
 * @param device Target device
 * @param property_set_guid Property set GUID as string
 * @param property_id Property ID within set
 * @param[out] supported 1 if supported, 0 if not
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_query_vendor_property_support(const duvc_device_t* device, const char* property_set_guid, uint32_t property_id, int* supported);

/* ========================================================================
 * Logitech Vendor Extensions
 * ======================================================================== */
/**
 * @brief Get Logitech vendor property
 * @param device Target device
 * @param prop Logitech property to get
 * @param[out] data Buffer to receive property data
 * @param data_size Size of data buffer
 * @param[out] bytes_returned Actual bytes returned
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_logitech_property(const duvc_device_t* device, duvc_logitech_prop_t prop, void* data, size_t data_size, size_t* bytes_returned);

/**
 * @brief Set Logitech vendor property
 * @param device Target device
 * @param prop Logitech property to set
 * @param data Property data to set
 * @param data_size Size of property data
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_logitech_property(const duvc_device_t* device, duvc_logitech_prop_t prop, const void* data, size_t data_size);

/**
 * @brief Check Logitech vendor property support
 * @param device Target device
 * @param[out] supported 1 if Logitech properties supported, 0 if not
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_supports_logitech_properties(const duvc_device_t* device, int* supported);

/* ========================================================================
 * String Conversions
 * ======================================================================== */
/**
 * @brief Convert camera property to string
 * @param prop Camera property to convert
 * @return Null-terminated property name string (statically allocated)
 */
const char* duvc_cam_prop_to_string(duvc_cam_prop_t prop);

/**
 * @brief Convert video property to string
 * @param prop Video property to convert
 * @return Null-terminated property name string (statically allocated)
 */
const char* duvc_vid_prop_to_string(duvc_vid_prop_t prop);

/**
 * @brief Convert camera mode to string
 * @param mode Camera mode to convert
 * @return Null-terminated mode name string (statically allocated)
 */
const char* duvc_cam_mode_to_string(duvc_cam_mode_t mode);

/**
 * @brief Convert error code to string
 * @param code Error code to convert
 * @return Null-terminated error description string (statically allocated)
 */
const char* duvc_error_code_to_string(duvc_result_t code);

/**
 * @brief Convert log level to string
 * @param level Log level to convert
 * @return Null-terminated log level name string (statically allocated)
 */
const char* duvc_log_level_to_string(duvc_log_level_t level);

/* ========================================================================
 * Wide String Conversions (Windows Support)
 * ======================================================================== */
/**
 * @brief Convert camera property to wide string
 * @param prop Camera property to convert
 * @param[out] buffer Buffer to receive wide string
 * @param buffer_size Size of buffer in wide characters
 * @param[out] required Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_cam_prop_to_wstring(duvc_cam_prop_t prop, wchar_t* buffer, size_t buffer_size, size_t* required);

/**
 * @brief Convert video property to wide string
 * @param prop Video property to convert
 * @param[out] buffer Buffer to receive wide string
 * @param buffer_size Size of buffer in wide characters
 * @param[out] required Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_vid_prop_to_wstring(duvc_vid_prop_t prop, wchar_t* buffer, size_t buffer_size, size_t* required);

/**
 * @brief Convert camera mode to wide string
 * @param mode Camera mode to convert
 * @param[out] buffer Buffer to receive wide string
 * @param buffer_size Size of buffer in wide characters
 * @param[out] required Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_cam_mode_to_wstring(duvc_cam_mode_t mode, wchar_t* buffer, size_t buffer_size, size_t* required);

/* ========================================================================
 * Error Handling and Diagnostics
 * ======================================================================== */
/**
 * @brief Get last error details
 * @param[out] buffer Buffer to receive error details
 * @param buffer_size Size of buffer in bytes
 * @param[out] required_size Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_last_error_details(char* buffer, size_t buffer_size, size_t* required_size);

/**
 * @brief Get diagnostic information
 * @param[out] buffer Buffer to receive diagnostic info
 * @param buffer_size Size of buffer in bytes
 * @param[out] required_size Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_diagnostic_info(char* buffer, size_t buffer_size, size_t* required_size);

/**
 * @brief Check if error is device-related
 * @param result Error code to check
 * @return 1 if device-related error, 0 if not
 */
int duvc_is_device_error(duvc_result_t result);

/**
 * @brief Check if error is permission-related
 * @param result Error code to check
 * @return 1 if permission-related error, 0 if not
 */
int duvc_is_permission_error(duvc_result_t result);

/**
 * @brief Clear last error information
 * @note Clears any stored error details from previous operations
 */
void duvc_clear_last_error(void);

/* ========================================================================
 * Windows-Specific Error Diagnostics
 * ======================================================================== */
#ifdef _WIN32
/**
 * @brief Decode system error code to string
 * @param error_code Windows system error code
 * @param[out] buffer Buffer to receive error description
 * @param buffer_size Size of buffer in bytes
 * @param[out] required Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_decode_system_error(unsigned long error_code, char* buffer, size_t buffer_size, size_t* required);

/**
 * @brief Decode HRESULT to string
 * @param hr HRESULT value to decode
 * @param[out] buffer Buffer to receive error description
 * @param buffer_size Size of buffer in bytes
 * @param[out] required Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_decode_hresult(int32_t hr, char* buffer, size_t buffer_size, size_t* required);

/**
 * @brief Get detailed HRESULT information
 * @param hr HRESULT value to analyze
 * @param[out] buffer Buffer to receive detailed information
 * @param buffer_size Size of buffer in bytes
 * @param[out] required Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_hresult_details(int32_t hr, char* buffer, size_t buffer_size, size_t* required);

/**
 * @brief Check if HRESULT indicates device error
 * @param hr HRESULT value to check
 * @return 1 if device-related error, 0 if not
 */
int duvc_is_hresult_device_error(int32_t hr);

/**
 * @brief Check if HRESULT indicates permission error
 * @param hr HRESULT value to check
 * @return 1 if permission-related error, 0 if not
 */
int duvc_is_hresult_permission_error(int32_t hr);
#endif

/* ========================================================================
 * Convenience Macros for Logging
 * ======================================================================== */
#define DUVC_LOG_DEBUG(msg) duvc_log_debug(msg)
#define DUVC_LOG_INFO(msg) duvc_log_info(msg)
#define DUVC_LOG_WARNING(msg) duvc_log_warning(msg)
#define DUVC_LOG_ERROR(msg) duvc_log_error(msg)
#define DUVC_LOG_CRITICAL(msg) duvc_log_critical(msg)

/* ========================================================================
 * Additional Platform Utilities
 * ======================================================================== */
/**
 * @brief Check if current process has camera permissions
 * @param[out] has_permissions 1 if has permissions, 0 if not
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_has_camera_permissions(int* has_permissions);

/**
 * @brief Get platform information
 * @param[out] buffer Buffer to receive platform info
 * @param buffer_size Size of buffer in bytes
 * @param[out] required Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_platform_info(char* buffer, size_t buffer_size, size_t* required);

#ifdef __cplusplus
}
#endif
