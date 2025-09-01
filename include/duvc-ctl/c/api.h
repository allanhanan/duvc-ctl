#pragma once

/**
 * @file api.h
 * @brief Complete C ABI interface for duvc-ctl
 * 
 * This header provides a comprehensive C-compatible interface to the duvc-ctl library,
 * covering all functionality including device management, property control, vendor extensions,
 * logging, error diagnostics, and etc...
 */

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ========================================================================
 * Version and ABI Management
 * ======================================================================== */

/**
 * @brief Get runtime library version
 * @return Combined version number as returned by DUVC_ABI_VERSION macro
 */
uint32_t duvc_get_version(void);

/**
 * @brief Get runtime library version string
 * @return Null-terminated version string (e.g., "2.0.0")
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
 * Core Types and Enumerations
 * ======================================================================== */

/**
 * @brief Result codes for all duvc operations
 */
typedef enum {
    DUVC_SUCCESS = 0,                      /**< Operation succeeded */
    DUVC_ERROR_DEVICE_NOT_FOUND,           /**< Device not found or disconnected */
    DUVC_ERROR_DEVICE_BUSY,                /**< Device is busy or in use */
    DUVC_ERROR_PROPERTY_NOT_SUPPORTED,     /**< Property not supported by device */
    DUVC_ERROR_INVALID_VALUE,              /**< Property value out of range */
    DUVC_ERROR_PERMISSION_DENIED,          /**< Insufficient permissions */
    DUVC_ERROR_SYSTEM_ERROR,               /**< System/platform error */
    DUVC_ERROR_INVALID_ARGUMENT,           /**< Invalid function argument */
    DUVC_ERROR_NOT_IMPLEMENTED,            /**< Feature not implemented on this platform */
    DUVC_ERROR_CONNECTION_FAILED,          /**< Failed to establish device connection */
    DUVC_ERROR_TIMEOUT,                    /**< Operation timed out */
    DUVC_ERROR_BUFFER_TOO_SMALL            /**< Provided buffer is too small */
} duvc_result_t;

/**
 * @brief Camera control properties
 */
typedef enum {
    DUVC_CAM_PROP_PAN = 0,                 /**< Horizontal camera rotation */
    DUVC_CAM_PROP_TILT,                    /**< Vertical camera rotation */
    DUVC_CAM_PROP_ROLL,                    /**< Camera roll rotation */
    DUVC_CAM_PROP_ZOOM,                    /**< Optical zoom level */
    DUVC_CAM_PROP_EXPOSURE,                /**< Exposure time */
    DUVC_CAM_PROP_IRIS,                    /**< Aperture/iris setting */
    DUVC_CAM_PROP_FOCUS,                   /**< Focus position */
    DUVC_CAM_PROP_SCAN_MODE,               /**< Scan mode (progressive/interlaced) */
    DUVC_CAM_PROP_PRIVACY,                 /**< Privacy mode on/off */
    DUVC_CAM_PROP_PAN_RELATIVE,            /**< Relative pan movement */
    DUVC_CAM_PROP_TILT_RELATIVE,           /**< Relative tilt movement */
    DUVC_CAM_PROP_ROLL_RELATIVE,           /**< Relative roll movement */
    DUVC_CAM_PROP_ZOOM_RELATIVE,           /**< Relative zoom movement */
    DUVC_CAM_PROP_EXPOSURE_RELATIVE,       /**< Relative exposure adjustment */
    DUVC_CAM_PROP_IRIS_RELATIVE,           /**< Relative iris adjustment */
    DUVC_CAM_PROP_FOCUS_RELATIVE,          /**< Relative focus adjustment */
    DUVC_CAM_PROP_PAN_TILT,                /**< Combined pan/tilt control */
    DUVC_CAM_PROP_PAN_TILT_RELATIVE,       /**< Relative pan/tilt movement */
    DUVC_CAM_PROP_FOCUS_SIMPLE,            /**< Simple focus control */
    DUVC_CAM_PROP_DIGITAL_ZOOM,            /**< Digital zoom level */
    DUVC_CAM_PROP_DIGITAL_ZOOM_RELATIVE,   /**< Relative digital zoom */
    DUVC_CAM_PROP_BACKLIGHT_COMPENSATION,  /**< Backlight compensation */
    DUVC_CAM_PROP_LAMP                     /**< Camera lamp/flash control */
} duvc_cam_prop_t;

/**
 * @brief Video processing properties
 */
typedef enum {
    DUVC_VID_PROP_BRIGHTNESS = 0,          /**< Image brightness level */
    DUVC_VID_PROP_CONTRAST,                /**< Image contrast level */
    DUVC_VID_PROP_HUE,                     /**< Color hue adjustment */
    DUVC_VID_PROP_SATURATION,              /**< Color saturation level */
    DUVC_VID_PROP_SHARPNESS,               /**< Image sharpness level */
    DUVC_VID_PROP_GAMMA,                   /**< Gamma correction value */
    DUVC_VID_PROP_COLOR_ENABLE,            /**< Color vs. monochrome mode */
    DUVC_VID_PROP_WHITE_BALANCE,           /**< White balance adjustment */
    DUVC_VID_PROP_BACKLIGHT_COMPENSATION,  /**< Backlight compensation level */
    DUVC_VID_PROP_GAIN                     /**< Sensor gain level */
} duvc_vid_prop_t;

/**
 * @brief Property control mode
 */
typedef enum {
    DUVC_CAM_MODE_AUTO = 0,                /**< Automatic control by camera */
    DUVC_CAM_MODE_MANUAL                   /**< Manual control by application */
} duvc_cam_mode_t;

/**
 * @brief Log levels for diagnostic output
 */
typedef enum {
    DUVC_LOG_DEBUG = 0,                    /**< Debug information */
    DUVC_LOG_INFO = 1,                     /**< Informational messages */
    DUVC_LOG_WARNING = 2,                  /**< Warning messages */
    DUVC_LOG_ERROR = 3,                    /**< Error messages */
    DUVC_LOG_CRITICAL = 4                  /**< Critical errors */
} duvc_log_level_t;

/**
 * @brief Logitech vendor-specific properties
 */
typedef enum {
    DUVC_LOGITECH_PROP_RIGHT_LIGHT = 1,    /**< RightLight auto-exposure */
    DUVC_LOGITECH_PROP_RIGHT_SOUND = 2,    /**< RightSound audio processing */
    DUVC_LOGITECH_PROP_FACE_TRACKING = 3,  /**< Face tracking enable/disable */
    DUVC_LOGITECH_PROP_LED_INDICATOR = 4,  /**< LED indicator control */
    DUVC_LOGITECH_PROP_PROCESSOR_USAGE = 5, /**< Processor usage optimization */
    DUVC_LOGITECH_PROP_RAW_DATA_BITS = 6,  /**< Raw data bit depth */
    DUVC_LOGITECH_PROP_FOCUS_ASSIST = 7,   /**< Focus assist beam */
    DUVC_LOGITECH_PROP_VIDEO_STANDARD = 8, /**< Video standard selection */
    DUVC_LOGITECH_PROP_DIGITAL_ZOOM_ROI = 9, /**< Digital zoom region of interest */
    DUVC_LOGITECH_PROP_TILT_PAN = 10       /**< Combined tilt/pan control */
} duvc_logitech_prop_t;

/**
 * @brief Property setting with value and control mode
 */
typedef struct {
    int32_t value;                         /**< Property value */
    duvc_cam_mode_t mode;                  /**< Control mode (auto/manual) */
} duvc_prop_setting_t;

/**
 * @brief Property range and default information
 */
typedef struct {
    int32_t min;                           /**< Minimum supported value */
    int32_t max;                           /**< Maximum supported value */
    int32_t step;                          /**< Step size between valid values */
    int32_t default_val;                   /**< Default value */
    duvc_cam_mode_t default_mode;          /**< Default control mode */
} duvc_prop_range_t;

/**
 * @brief Vendor property data container
 */
typedef struct {
    char property_set_guid[39];            /**< Property set GUID as string */
    uint32_t property_id;                  /**< Property ID within set */
    void* data;                            /**< Property data payload */
    size_t data_size;                      /**< Size of data in bytes */
} duvc_vendor_property_t;

/**
 * @brief Opaque device handle
 */
typedef struct duvc_device_t duvc_device_t;

/**
 * @brief Opaque connection handle for efficient property operations
 */
typedef struct duvc_connection_t duvc_connection_t;

/**
 * @brief Log message callback function
 * @param level Log level
 * @param message Null-terminated log message
 * @param user_data User-provided context data
 */
typedef void (*duvc_log_callback_t)(duvc_log_level_t level, const char* message, void* user_data);

/**
 * @brief Device hotplug event callback function
 * @param device Device that was added or removed (null if removal)
 * @param connected 1 if device connected, 0 if disconnected
 * @param user_data User-provided context data
 */
typedef void (*duvc_hotplug_callback_t)(const duvc_device_t* device, int connected, void* user_data);

/* ========================================================================
 * Library Management
 * ======================================================================== */

/**
 * @brief Initialize the duvc library
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_initialize(void);

/**
 * @brief Shutdown the duvc library
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
 * @brief Set global log callback function
 * @param callback Log callback function (NULL to disable logging)
 * @param user_data User data passed to callback
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_log_callback(duvc_log_callback_t callback, void* user_data);

/**
 * @brief Set minimum log level
 * @param level Minimum level to log
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_log_level(duvc_log_level_t level);

/**
 * @brief Get current minimum log level
 * @param[out] level Current minimum log level
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_log_level(duvc_log_level_t* level);

/**
 * @brief Log a message at specified level
 * @param level Log level
 * @param message Message to log
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_log_message(duvc_log_level_t level, const char* message);

/* ========================================================================
 * Device Enumeration and Management
 * ======================================================================== */

/**
 * @brief Enumerate all available camera devices
 * @param[out] devices Array of device pointers (caller must free with duvc_free_device_list)
 * @param[out] count Number of devices in the array
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_list_devices(duvc_device_t*** devices, size_t* count);

/**
 * @brief Free device list returned by duvc_list_devices
 * @param devices Device array to free
 * @param count Number of devices in the array
 */
void duvc_free_device_list(duvc_device_t** devices, size_t count);

/**
 * @brief Check if a device is currently connected
 * @param device Device to check
 * @param[out] connected 1 if connected, 0 if not connected
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_is_device_connected(const duvc_device_t* device, int* connected);

/**
 * @brief Get device name as UTF-8 string
 * @param device Target device
 * @param[out] name_buffer Buffer to receive name (null-terminated UTF-8)
 * @param buffer_size Size of name_buffer in bytes
 * @param[out] required_size Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_device_name(const duvc_device_t* device, 
                                   char* name_buffer, 
                                   size_t buffer_size,
                                   size_t* required_size);

/**
 * @brief Get device path as UTF-8 string
 * @param device Target device
 * @param[out] path_buffer Buffer to receive path (null-terminated UTF-8)
 * @param buffer_size Size of path_buffer in bytes
 * @param[out] required_size Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_device_path(const duvc_device_t* device,
                                   char* path_buffer,
                                   size_t buffer_size,
                                   size_t* required_size);

/**
 * @brief Enable device hotplug monitoring
 * @param callback Callback function for hotplug events
 * @param user_data User data passed to callback
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_enable_hotplug_monitoring(duvc_hotplug_callback_t callback, void* user_data);

/**
 * @brief Disable device hotplug monitoring
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_disable_hotplug_monitoring(void);

/* ========================================================================
 * Connection Management
 * ======================================================================== */

/**
 * @brief Create a persistent connection to a device
 * @param device Device to connect to
 * @param[out] connection Connection handle
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_create_connection(const duvc_device_t* device, duvc_connection_t** connection);

/**
 * @brief Close a device connection
 * @param connection Connection to close
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_close_connection(duvc_connection_t* connection);

/**
 * @brief Check if connection is valid
 * @param connection Connection to check
 * @param[out] valid 1 if valid, 0 if invalid
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_is_connection_valid(const duvc_connection_t* connection, int* valid);

/* ========================================================================
 * Camera Property Operations
 * ======================================================================== */

/**
 * @brief Get current value of a camera control property
 * @param device Target device
 * @param prop Camera property to query
 * @param[out] setting Current property setting
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_camera_property(const duvc_device_t* device,
                                       duvc_cam_prop_t prop,
                                       duvc_prop_setting_t* setting);

/**
 * @brief Set value of a camera control property
 * @param device Target device
 * @param prop Camera property to set
 * @param setting New property setting
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_camera_property(const duvc_device_t* device,
                                       duvc_cam_prop_t prop,
                                       const duvc_prop_setting_t* setting);

/**
 * @brief Get valid range for a camera control property
 * @param device Target device
 * @param prop Camera property to query
 * @param[out] range Property range information
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_camera_property_range(const duvc_device_t* device,
                                             duvc_cam_prop_t prop,
                                             duvc_prop_range_t* range);

/**
 * @brief Get multiple camera properties efficiently
 * @param device Target device
 * @param props Array of camera properties to query
 * @param[out] settings Array of property settings (same order as props)
 * @param count Number of properties
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_multiple_camera_properties(const duvc_device_t* device,
                                                  const duvc_cam_prop_t* props,
                                                  duvc_prop_setting_t* settings,
                                                  size_t count);

/**
 * @brief Set multiple camera properties efficiently
 * @param device Target device
 * @param props Array of camera properties to set
 * @param settings Array of property settings
 * @param count Number of properties
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_multiple_camera_properties(const duvc_device_t* device,
                                                  const duvc_cam_prop_t* props,
                                                  const duvc_prop_setting_t* settings,
                                                  size_t count);

/* ========================================================================
 * Connection-Based Camera Property Operations (More Efficient)
 * ======================================================================== */

/**
 * @brief Get camera property using connection
 * @param connection Device connection
 * @param prop Camera property to query
 * @param[out] setting Current property setting
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_connection_get_camera_property(duvc_connection_t* connection,
                                                  duvc_cam_prop_t prop,
                                                  duvc_prop_setting_t* setting);

/**
 * @brief Set camera property using connection
 * @param connection Device connection
 * @param prop Camera property to set
 * @param setting New property setting
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_connection_set_camera_property(duvc_connection_t* connection,
                                                  duvc_cam_prop_t prop,
                                                  const duvc_prop_setting_t* setting);

/**
 * @brief Get camera property range using connection
 * @param connection Device connection
 * @param prop Camera property to query
 * @param[out] range Property range information
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_connection_get_camera_property_range(duvc_connection_t* connection,
                                                        duvc_cam_prop_t prop,
                                                        duvc_prop_range_t* range);

/* ========================================================================
 * Video Processing Property Operations
 * ======================================================================== */

/**
 * @brief Get current value of a video processing property
 * @param device Target device
 * @param prop Video property to query
 * @param[out] setting Current property setting
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_video_property(const duvc_device_t* device,
                                      duvc_vid_prop_t prop,
                                      duvc_prop_setting_t* setting);

/**
 * @brief Set value of a video processing property
 * @param device Target device
 * @param prop Video property to set
 * @param setting New property setting
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_video_property(const duvc_device_t* device,
                                      duvc_vid_prop_t prop,
                                      const duvc_prop_setting_t* setting);

/**
 * @brief Get valid range for a video processing property
 * @param device Target device
 * @param prop Video property to query
 * @param[out] range Property range information
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_video_property_range(const duvc_device_t* device,
                                            duvc_vid_prop_t prop,
                                            duvc_prop_range_t* range);

/**
 * @brief Get multiple video properties efficiently
 * @param device Target device
 * @param props Array of video properties to query
 * @param[out] settings Array of property settings (same order as props)
 * @param count Number of properties
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_multiple_video_properties(const duvc_device_t* device,
                                                 const duvc_vid_prop_t* props,
                                                 duvc_prop_setting_t* settings,
                                                 size_t count);

/**
 * @brief Set multiple video properties efficiently
 * @param device Target device
 * @param props Array of video properties to set
 * @param settings Array of property settings
 * @param count Number of properties
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_multiple_video_properties(const duvc_device_t* device,
                                                 const duvc_vid_prop_t* props,
                                                 const duvc_prop_setting_t* settings,
                                                 size_t count);

/* ========================================================================
 * Connection-Based Video Property Operations (More Efficient)
 * ======================================================================== */

/**
 * @brief Get video property using connection
 * @param connection Device connection
 * @param prop Video property to query
 * @param[out] setting Current property setting
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_connection_get_video_property(duvc_connection_t* connection,
                                                 duvc_vid_prop_t prop,
                                                 duvc_prop_setting_t* setting);

/**
 * @brief Set video property using connection
 * @param connection Device connection
 * @param prop Video property to set
 * @param setting New property setting
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_connection_set_video_property(duvc_connection_t* connection,
                                                 duvc_vid_prop_t prop,
                                                 const duvc_prop_setting_t* setting);

/**
 * @brief Get video property range using connection
 * @param connection Device connection
 * @param prop Video property to query
 * @param[out] range Property range information
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_connection_get_video_property_range(duvc_connection_t* connection,
                                                       duvc_vid_prop_t prop,
                                                       duvc_prop_range_t* range);

/* ========================================================================
 * Vendor Property Operations
 * ======================================================================== */

/**
 * @brief Get vendor-specific property data
 * @param device Target device
 * @param property_set_guid Property set GUID as string
 * @param property_id Property ID within set
 * @param[out] data Buffer to receive property data
 * @param[in,out] data_size Input: buffer size, Output: actual data size
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_vendor_property(const duvc_device_t* device,
                                       const char* property_set_guid,
                                       uint32_t property_id,
                                       void* data,
                                       size_t* data_size);

/**
 * @brief Set vendor-specific property data
 * @param device Target device
 * @param property_set_guid Property set GUID as string
 * @param property_id Property ID within set
 * @param data Property data to set
 * @param data_size Size of data in bytes
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_vendor_property(const duvc_device_t* device,
                                       const char* property_set_guid,
                                       uint32_t property_id,
                                       const void* data,
                                       size_t data_size);

/**
 * @brief Query support for vendor-specific property
 * @param device Target device
 * @param property_set_guid Property set GUID as string
 * @param property_id Property ID within set
 * @param[out] supported 1 if supported, 0 if not supported
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_query_vendor_property_support(const duvc_device_t* device,
                                                  const char* property_set_guid,
                                                  uint32_t property_id,
                                                  int* supported);

/* ========================================================================
 * Logitech Vendor Properties (Convenience Functions)
 * ======================================================================== */

/**
 * @brief Check if device supports Logitech vendor properties
 * @param device Device to check
 * @param[out] supported 1 if supported, 0 if not supported
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_supports_logitech_properties(const duvc_device_t* device, int* supported);

/**
 * @brief Get Logitech vendor property (32-bit value)
 * @param device Target device
 * @param prop Logitech property ID
 * @param[out] value Property value
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_get_logitech_property_int32(const duvc_device_t* device,
                                               duvc_logitech_prop_t prop,
                                               int32_t* value);

/**
 * @brief Set Logitech vendor property (32-bit value)
 * @param device Target device
 * @param prop Logitech property ID
 * @param value Property value to set
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_logitech_property_int32(const duvc_device_t* device,
                                               duvc_logitech_prop_t prop,
                                               int32_t value);

/**
 * @brief Get Logitech vendor property (raw data)
 * @param device Target device
 * @param prop Logitech property ID
 * @param[out] data Buffer to receive property data
 * @param[in,out] data_size Input: buffer size, Output: actual data size
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_logitech_property_data(const duvc_device_t* device,
                                              duvc_logitech_prop_t prop,
                                              void* data,
                                              size_t* data_size);

/**
 * @brief Set Logitech vendor property (raw data)
 * @param device Target device
 * @param prop Logitech property ID
 * @param data Property data to set
 * @param data_size Size of data in bytes
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_set_logitech_property_data(const duvc_device_t* device,
                                              duvc_logitech_prop_t prop,
                                              const void* data,
                                              size_t data_size);

/* ========================================================================
 * Advanced Error Handling and Diagnostics
 * ======================================================================== */

/**
 * @brief Get human-readable description of error code
 * @param result Error code to describe
 * @return Null-terminated error description string (statically allocated)
 */
const char* duvc_get_error_string(duvc_result_t result);

/**
 * @brief Get detailed error information from last operation
 * @param[out] buffer Buffer to receive detailed error information
 * @param buffer_size Size of buffer in bytes
 * @param[out] required_size Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_last_error_details(char* buffer, size_t buffer_size, size_t* required_size);

/**
 * @brief Get diagnostic information for troubleshooting
 * @param[out] buffer Buffer to receive diagnostic information
 * @param buffer_size Size of buffer in bytes
 * @param[out] required_size Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_diagnostic_info(char* buffer, size_t buffer_size, size_t* required_size);

/**
 * @brief Check if error is device-related
 * @param result Error code to check
 * @return 1 if device-related error, 0 otherwise
 */
int duvc_is_device_error(duvc_result_t result);

/**
 * @brief Check if error is permission-related
 * @param result Error code to check
 * @return 1 if permission error, 0 otherwise
 */
int duvc_is_permission_error(duvc_result_t result);

/**
 * @brief Clear last error information
 */
void duvc_clear_last_error(void);

/* ========================================================================
 * String Conversion Utilities
 * ======================================================================== */

/**
 * @brief Get human-readable name of camera property
 * @param prop Camera property
 * @return Null-terminated property name string (statically allocated)
 */
const char* duvc_get_camera_property_name(duvc_cam_prop_t prop);

/**
 * @brief Get human-readable name of video property
 * @param prop Video property
 * @return Null-terminated property name string (statically allocated)
 */
const char* duvc_get_video_property_name(duvc_vid_prop_t prop);

/**
 * @brief Get human-readable name of camera mode
 * @param mode Camera mode
 * @return Null-terminated mode name string (statically allocated)
 */
const char* duvc_get_camera_mode_name(duvc_cam_mode_t mode);

/**
 * @brief Get human-readable name of log level
 * @param level Log level
 * @return Null-terminated level name string (statically allocated)
 */
const char* duvc_get_log_level_name(duvc_log_level_t level);

/**
 * @brief Get human-readable name of Logitech property
 * @param prop Logitech property
 * @return Null-terminated property name string (statically allocated)
 */
const char* duvc_get_logitech_property_name(duvc_logitech_prop_t prop);

/* ========================================================================
 * Value Validation and Utility Functions
 * ======================================================================== */

/**
 * @brief Check if property value is valid for given range
 * @param range Property range
 * @param value Value to check
 * @return 1 if valid, 0 if invalid
 */
int duvc_is_value_valid(const duvc_prop_range_t* range, int32_t value);

/**
 * @brief Clamp value to valid range
 * @param range Property range
 * @param value Value to clamp
 * @return Nearest valid value within range
 */
int32_t duvc_clamp_value(const duvc_prop_range_t* range, int32_t value);

/**
 * @brief Get the next valid value in range
 * @param range Property range
 * @param current_value Current value
 * @param increment 1 to increment, 0 to decrement
 * @param[out] next_value Next valid value
 * @return DUVC_SUCCESS if next value found, DUVC_ERROR_INVALID_VALUE if at limit
 */
duvc_result_t duvc_get_next_valid_value(const duvc_prop_range_t* range,
                                        int32_t current_value,
                                        int increment,
                                        int32_t* next_value);

/* ========================================================================
 * Capability and Device Information
 * ======================================================================== */

/**
 * @brief Get comprehensive device capabilities
 * @param device Target device
 * @param[out] buffer JSON string buffer containing device capabilities
 * @param buffer_size Size of buffer in bytes
 * @param[out] required_size Required buffer size (including null terminator)
 * @return DUVC_SUCCESS on success, DUVC_ERROR_BUFFER_TOO_SMALL if buffer too small
 */
duvc_result_t duvc_get_device_capabilities(const duvc_device_t* device,
                                           char* buffer,
                                           size_t buffer_size,
                                           size_t* required_size);

/**
 * @brief Check if device supports specific camera property
 * @param device Target device
 * @param prop Camera property to check
 * @param[out] supported 1 if supported, 0 if not supported
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_is_camera_property_supported(const duvc_device_t* device,
                                                duvc_cam_prop_t prop,
                                                int* supported);

/**
 * @brief Check if device supports specific video property
 * @param device Target device
 * @param prop Video property to check
 * @param[out] supported 1 if supported, 0 if not supported
 * @return DUVC_SUCCESS on success, error code on failure
 */
duvc_result_t duvc_is_video_property_supported(const duvc_device_t* device,
                                               duvc_vid_prop_t prop,
                                               int* supported);

#ifdef __cplusplus
}
#endif
