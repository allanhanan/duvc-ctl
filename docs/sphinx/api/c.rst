C API Reference
===============

The duvc-ctl C API provides a stable, platform-agnostic interface for controlling USB Video Class (UVC) cameras. This C ABI ensures compatibility across different compilers, programming languages, and runtime environments while maintaining full access to the library's capabilities.

Overview
--------

The C API acts as a bridge between client applications and the underlying C++ implementation, providing:

- **Stable ABI**: Versioned interface with backward compatibility guarantees
- **Cross-Language Compatibility**: Usable from C, C++, Python, Rust, Go, and other languages
- **Comprehensive Functionality**: Full access to camera properties, device management, and vendor extensions
- **Error Handling**: Robust error reporting with detailed diagnostics
- **Memory Management**: Clear ownership semantics and proper resource cleanup
- **Thread Safety**: Safe for concurrent access from multiple threads

Architecture
~~~~~~~~~~~~

.. code-block:: text

    Client Application
           ↓
       C API (api.h)
           ↓  
    C++ Implementation
           ↓
    Platform Layer (DirectShow)
           ↓
    UVC Hardware

Basic Usage Pattern
~~~~~~~~~~~~~~~~~~~

.. code-block:: c

    #include "duvc-ctl/c/api.h"

    int main() {
        // Initialize library
        duvc_result_t result = duvc_initialize();
        if (result != DUVC_SUCCESS) {
            return 1;
        }
        
        // Use camera functionality
        duvc_device_t** devices;
        size_t count;
        result = duvc_list_devices(&devices, &count);
        
        // ... camera operations ...
        
        // Cleanup
        duvc_free_device_list(devices, count);
        duvc_shutdown();
        return 0;
    }

Version and ABI Management
--------------------------

Functions
~~~~~~~~~

.. c:function:: uint32_t duvc_get_version(void)

   Get runtime library version as integer.

   :returns: Version number in format ``(major << 16) | (minor << 8) | patch``

.. c:function:: const char* duvc_get_version_string(void)

   Get runtime library version as string.

   :returns: Null-terminated version string (e.g., "2.0.0")
   :note: Returned string is statically allocated and should not be freed

.. c:function:: int duvc_check_abi_compatibility(uint32_t compiled_version)

   Check ABI compatibility between compiled and runtime versions.

   :param compiled_version: Version application was compiled with (use ``DUVC_ABI_VERSION``)
   :returns: 1 if compatible, 0 if incompatible

ABI Versioning
~~~~~~~~~~~~~~

.. code-block:: c

    // Check compatibility at runtime
    if (!duvc_check_abi_compatibility(DUVC_ABI_VERSION)) {
        fprintf(stderr, "ABI version mismatch\n");
        return 1;
    }

    printf("Library version: %s\n", duvc_get_version_string());

Compatibility Rules:

- **Major Version**: Must match exactly (breaking changes)
- **Minor Version**: Runtime ≥ compiled (backward compatible additions)
- **Patch Version**: Any (bug fixes only)

Core Types and Enumerations
----------------------------

Result Codes
~~~~~~~~~~~~

.. c:type:: duvc_result_t

   Result codes for all duvc operations.

   .. c:enumerator:: DUVC_SUCCESS

      Operation succeeded

   .. c:enumerator:: DUVC_ERROR_DEVICE_NOT_FOUND

      Device not found or disconnected

   .. c:enumerator:: DUVC_ERROR_DEVICE_BUSY

      Device is busy or in use

   .. c:enumerator:: DUVC_ERROR_PROPERTY_NOT_SUPPORTED

      Property not supported by device

   .. c:enumerator:: DUVC_ERROR_INVALID_VALUE

      Property value out of range

   .. c:enumerator:: DUVC_ERROR_PERMISSION_DENIED

      Insufficient permissions

   .. c:enumerator:: DUVC_ERROR_SYSTEM_ERROR

      System/platform error

   .. c:enumerator:: DUVC_ERROR_INVALID_ARGUMENT

      Invalid function argument

   .. c:enumerator:: DUVC_ERROR_NOT_IMPLEMENTED

      Feature not implemented on this platform

   .. c:enumerator:: DUVC_ERROR_CONNECTION_FAILED

      Failed to establish device connection

   .. c:enumerator:: DUVC_ERROR_TIMEOUT

      Operation timed out

   .. c:enumerator:: DUVC_ERROR_BUFFER_TOO_SMALL

      Provided buffer is too small

Camera Properties
~~~~~~~~~~~~~~~~~

.. c:type:: duvc_cam_prop_t

   Camera control properties.

   .. c:enumerator:: DUVC_CAM_PROP_PAN

      Horizontal camera rotation

   .. c:enumerator:: DUVC_CAM_PROP_TILT

      Vertical camera rotation

   .. c:enumerator:: DUVC_CAM_PROP_ROLL

      Camera roll rotation

   .. c:enumerator:: DUVC_CAM_PROP_ZOOM

      Optical zoom level

   .. c:enumerator:: DUVC_CAM_PROP_EXPOSURE

      Exposure time

   .. c:enumerator:: DUVC_CAM_PROP_IRIS

      Aperture/iris setting

   .. c:enumerator:: DUVC_CAM_PROP_FOCUS

      Focus position

   .. c:enumerator:: DUVC_CAM_PROP_SCAN_MODE

      Scan mode (progressive/interlaced)

   .. c:enumerator:: DUVC_CAM_PROP_PRIVACY

      Privacy mode on/off

   .. c:enumerator:: DUVC_CAM_PROP_PAN_RELATIVE

      Relative pan movement

   .. c:enumerator:: DUVC_CAM_PROP_TILT_RELATIVE

      Relative tilt movement

   .. c:enumerator:: DUVC_CAM_PROP_ROLL_RELATIVE

      Relative roll movement

   .. c:enumerator:: DUVC_CAM_PROP_ZOOM_RELATIVE

      Relative zoom movement

   .. c:enumerator:: DUVC_CAM_PROP_EXPOSURE_RELATIVE

      Relative exposure adjustment

   .. c:enumerator:: DUVC_CAM_PROP_IRIS_RELATIVE

      Relative iris adjustment

   .. c:enumerator:: DUVC_CAM_PROP_FOCUS_RELATIVE

      Relative focus adjustment

   .. c:enumerator:: DUVC_CAM_PROP_PAN_TILT

      Combined pan/tilt control

   .. c:enumerator:: DUVC_CAM_PROP_PAN_TILT_RELATIVE

      Relative pan/tilt movement

   .. c:enumerator:: DUVC_CAM_PROP_FOCUS_SIMPLE

      Simple focus control

   .. c:enumerator:: DUVC_CAM_PROP_DIGITAL_ZOOM

      Digital zoom level

   .. c:enumerator:: DUVC_CAM_PROP_DIGITAL_ZOOM_RELATIVE

      Relative digital zoom

   .. c:enumerator:: DUVC_CAM_PROP_BACKLIGHT_COMPENSATION

      Backlight compensation

   .. c:enumerator:: DUVC_CAM_PROP_LAMP

      Camera lamp/flash control

Video Properties
~~~~~~~~~~~~~~~~

.. c:type:: duvc_vid_prop_t

   Video processing properties.

   .. c:enumerator:: DUVC_VID_PROP_BRIGHTNESS

      Image brightness level

   .. c:enumerator:: DUVC_VID_PROP_CONTRAST

      Image contrast level

   .. c:enumerator:: DUVC_VID_PROP_HUE

      Color hue adjustment

   .. c:enumerator:: DUVC_VID_PROP_SATURATION

      Color saturation level

   .. c:enumerator:: DUVC_VID_PROP_SHARPNESS

      Image sharpness level

   .. c:enumerator:: DUVC_VID_PROP_GAMMA

      Gamma correction value

   .. c:enumerator:: DUVC_VID_PROP_COLOR_ENABLE

      Color vs. monochrome mode

   .. c:enumerator:: DUVC_VID_PROP_WHITE_BALANCE

      White balance adjustment

   .. c:enumerator:: DUVC_VID_PROP_BACKLIGHT_COMPENSATION

      Backlight compensation level

   .. c:enumerator:: DUVC_VID_PROP_GAIN

      Sensor gain level

Property Structures
~~~~~~~~~~~~~~~~~~~

.. c:type:: duvc_prop_setting_t

   Property setting with value and control mode.

   .. c:member:: int32_t value

      Property value

   .. c:member:: duvc_cam_mode_t mode

      Control mode (auto/manual)

.. c:type:: duvc_prop_range_t

   Property range and default information.

   .. c:member:: int32_t min

      Minimum supported value

   .. c:member:: int32_t max

      Maximum supported value

   .. c:member:: int32_t step

      Step size between valid values

   .. c:member:: int32_t default_val

      Default value

   .. c:member:: duvc_cam_mode_t default_mode

      Default control mode

Control Modes
~~~~~~~~~~~~~

.. c:type:: duvc_cam_mode_t

   Property control mode.

   .. c:enumerator:: DUVC_CAM_MODE_AUTO

      Automatic control by camera

   .. c:enumerator:: DUVC_CAM_MODE_MANUAL

      Manual control by application

Vendor Properties
~~~~~~~~~~~~~~~~~

.. c:type:: duvc_logitech_prop_t

   Logitech vendor-specific properties.

   .. c:enumerator:: DUVC_LOGITECH_PROP_RIGHT_LIGHT

      RightLight auto-exposure

   .. c:enumerator:: DUVC_LOGITECH_PROP_RIGHT_SOUND

      RightSound audio processing

   .. c:enumerator:: DUVC_LOGITECH_PROP_FACE_TRACKING

      Face tracking enable/disable

   .. c:enumerator:: DUVC_LOGITECH_PROP_LED_INDICATOR

      LED indicator control

   .. c:enumerator:: DUVC_LOGITECH_PROP_PROCESSOR_USAGE

      Processor usage optimization

   .. c:enumerator:: DUVC_LOGITECH_PROP_RAW_DATA_BITS

      Raw data bit depth

   .. c:enumerator:: DUVC_LOGITECH_PROP_FOCUS_ASSIST

      Focus assist beam

   .. c:enumerator:: DUVC_LOGITECH_PROP_VIDEO_STANDARD

      Video standard selection

   .. c:enumerator:: DUVC_LOGITECH_PROP_DIGITAL_ZOOM_ROI

      Digital zoom region of interest

   .. c:enumerator:: DUVC_LOGITECH_PROP_TILT_PAN

      Combined tilt/pan control

.. c:type:: duvc_vendor_property_t

   Vendor property data container.

   .. c:member:: char property_set_guid[39]

      Property set GUID as string

   .. c:member:: uint32_t property_id

      Property ID within set

   .. c:member:: void* data

      Property data payload

   .. c:member:: size_t data_size

      Size of data in bytes

Opaque Handle Types
~~~~~~~~~~~~~~~~~~~

.. c:type:: duvc_device_t

   Opaque device handle.

.. c:type:: duvc_connection_t

   Opaque connection handle for efficient property operations.

Callback Types
~~~~~~~~~~~~~~

.. c:type:: duvc_log_callback_t

   Log message callback function.

   .. code-block:: c

       typedef void (*duvc_log_callback_t)(duvc_log_level_t level, 
                                           const char* message, 
                                           void* user_data);

.. c:type:: duvc_hotplug_callback_t

   Device hotplug event callback function.

   .. code-block:: c

       typedef void (*duvc_hotplug_callback_t)(const duvc_device_t* device, 
                                               int connected, 
                                               void* user_data);

Library Management
------------------

.. c:function:: duvc_result_t duvc_initialize(void)

   Initialize the duvc library. Must be called before other functions.

   :returns: ``DUVC_SUCCESS`` on success, error code on failure
   :thread safety: Not thread-safe, call from main thread only

.. c:function:: void duvc_shutdown(void)

   Shutdown library and cleanup resources.

   :thread safety: Not thread-safe, call from main thread only

.. c:function:: int duvc_is_initialized(void)

   Check if library is initialized.

   :returns: 1 if initialized, 0 if not

Device Management
-----------------

.. c:function:: duvc_result_t duvc_list_devices(duvc_device_t*** devices, size_t* count)

   Enumerate all available camera devices.

   :param devices: Output array of device pointers (caller must free with :c:func:`duvc_free_device_list`)
   :param count: Number of devices in the array
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: void duvc_free_device_list(duvc_device_t** devices, size_t count)

   Free device list returned by :c:func:`duvc_list_devices`.

   :param devices: Device array to free
   :param count: Number of devices in the array

.. c:function:: duvc_result_t duvc_is_device_connected(const duvc_device_t* device, int* connected)

   Check if device is currently connected.

   :param device: Device to check
   :param connected: Output - 1 if connected, 0 if not
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_get_device_name(const duvc_device_t* device, char* name_buffer, size_t buffer_size, size_t* required_size)

   Get device name as UTF-8 string.

   :param device: Target device
   :param name_buffer: Buffer to receive name (can be NULL to query size)
   :param buffer_size: Size of name_buffer in bytes
   :param required_size: Required buffer size including null terminator
   :returns: ``DUVC_SUCCESS`` on success, ``DUVC_ERROR_BUFFER_TOO_SMALL`` if buffer too small

.. c:function:: duvc_result_t duvc_get_device_path(const duvc_device_t* device, char* path_buffer, size_t buffer_size, size_t* required_size)

   Get device path as UTF-8 string.

   :param device: Target device
   :param path_buffer: Buffer to receive path (can be NULL to query size)
   :param buffer_size: Size of path_buffer in bytes
   :param required_size: Required buffer size including null terminator
   :returns: ``DUVC_SUCCESS`` on success, ``DUVC_ERROR_BUFFER_TOO_SMALL`` if buffer too small

Connection Management
---------------------

.. c:function:: duvc_result_t duvc_create_connection(const duvc_device_t* device, duvc_connection_t** connection)

   Create persistent connection to device for efficient operations.

   :param device: Device to connect to
   :param connection: Output connection handle
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_close_connection(duvc_connection_t* connection)

   Close device connection.

   :param connection: Connection to close
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_is_connection_valid(const duvc_connection_t* connection, int* valid)

   Check if connection is valid.

   :param connection: Connection to check
   :param valid: Output - 1 if valid, 0 if invalid
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

Camera Property Operations
--------------------------

Direct Operations
~~~~~~~~~~~~~~~~~

.. c:function:: duvc_result_t duvc_get_camera_property(const duvc_device_t* device, duvc_cam_prop_t prop, duvc_prop_setting_t* setting)

   Get current value of a camera control property.

   :param device: Target device
   :param prop: Camera property to query
   :param setting: Output current property setting
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_set_camera_property(const duvc_device_t* device, duvc_cam_prop_t prop, const duvc_prop_setting_t* setting)

   Set value of a camera control property.

   :param device: Target device
   :param prop: Camera property to set
   :param setting: New property setting
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_get_camera_property_range(const duvc_device_t* device, duvc_cam_prop_t prop, duvc_prop_range_t* range)

   Get valid range for a camera control property.

   :param device: Target device
   :param prop: Camera property to query
   :param range: Output property range information
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

Batch Operations
~~~~~~~~~~~~~~~~

.. c:function:: duvc_result_t duvc_get_multiple_camera_properties(const duvc_device_t* device, const duvc_cam_prop_t* props, duvc_prop_setting_t* settings, size_t count)

   Get multiple camera properties efficiently using a single connection.

   :param device: Target device
   :param props: Array of camera properties to query
   :param settings: Output array of property settings
   :param count: Number of properties to query
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_set_multiple_camera_properties(const duvc_device_t* device, const duvc_cam_prop_t* props, const duvc_prop_setting_t* settings, size_t count)

   Set multiple camera properties efficiently using a single connection.

   :param device: Target device
   :param props: Array of camera properties to set
   :param settings: Array of property settings to apply
   :param count: Number of properties to set
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

Connection-Based Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. c:function:: duvc_result_t duvc_connection_get_camera_property(duvc_connection_t* connection, duvc_cam_prop_t prop, duvc_prop_setting_t* setting)

   Get camera property using existing connection.

   :param connection: Active device connection
   :param prop: Camera property to query
   :param setting: Output current property setting
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_connection_set_camera_property(duvc_connection_t* connection, duvc_cam_prop_t prop, const duvc_prop_setting_t* setting)

   Set camera property using existing connection.

   :param connection: Active device connection
   :param prop: Camera property to set
   :param setting: New property setting
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_connection_get_camera_property_range(duvc_connection_t* connection, duvc_cam_prop_t prop, duvc_prop_range_t* range)

   Get camera property range using existing connection.

   :param connection: Active device connection
   :param prop: Camera property to query
   :param range: Output property range information
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

Video Property Operations
-------------------------

Direct Operations
~~~~~~~~~~~~~~~~~

.. c:function:: duvc_result_t duvc_get_video_property(const duvc_device_t* device, duvc_vid_prop_t prop, duvc_prop_setting_t* setting)

   Get current value of a video processing property.

   :param device: Target device
   :param prop: Video property to query
   :param setting: Output current property setting
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_set_video_property(const duvc_device_t* device, duvc_vid_prop_t prop, const duvc_prop_setting_t* setting)

   Set value of a video processing property.

   :param device: Target device
   :param prop: Video property to set
   :param setting: New property setting
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_get_video_property_range(const duvc_device_t* device, duvc_vid_prop_t prop, duvc_prop_range_t* range)

   Get valid range for a video processing property.

   :param device: Target device
   :param prop: Video property to query
   :param range: Output property range information
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

Batch Operations
~~~~~~~~~~~~~~~~

.. c:function:: duvc_result_t duvc_get_multiple_video_properties(const duvc_device_t* device, const duvc_vid_prop_t* props, duvc_prop_setting_t* settings, size_t count)

   Get multiple video properties efficiently using a single connection.

   :param device: Target device
   :param props: Array of video properties to query
   :param settings: Output array of property settings
   :param count: Number of properties to query
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_set_multiple_video_properties(const duvc_device_t* device, const duvc_vid_prop_t* props, const duvc_prop_setting_t* settings, size_t count)

   Set multiple video properties efficiently using a single connection.

   :param device: Target device
   :param props: Array of video properties to set
   :param settings: Array of property settings to apply
   :param count: Number of properties to set
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

Connection-Based Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. c:function:: duvc_result_t duvc_connection_get_video_property(duvc_connection_t* connection, duvc_vid_prop_t prop, duvc_prop_setting_t* setting)

   Get video property using existing connection.

   :param connection: Active device connection
   :param prop: Video property to query
   :param setting: Output current property setting
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_connection_set_video_property(duvc_connection_t* connection, duvc_vid_prop_t prop, const duvc_prop_setting_t* setting)

   Set video property using existing connection.

   :param connection: Active device connection
   :param prop: Video property to set
   :param setting: New property setting
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_connection_get_video_property_range(duvc_connection_t* connection, duvc_vid_prop_t prop, duvc_prop_range_t* range)

   Get video property range using existing connection.

   :param connection: Active device connection
   :param prop: Video property to query
   :param range: Output property range information
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

Error Handling
--------------

Basic Error Functions
~~~~~~~~~~~~~~~~~~~~~

.. c:function:: const char* duvc_get_error_string(duvc_result_t result)

   Get human-readable error description.

   :param result: Error code to convert
   :returns: Null-terminated error string (statically allocated)

.. c:function:: duvc_result_t duvc_get_last_error_details(char* buffer, size_t buffer_size, size_t* required_size)

   Get detailed error information from last operation.

   :param buffer: Buffer to receive error details (can be NULL to query size)
   :param buffer_size: Size of buffer in bytes
   :param required_size: Required buffer size including null terminator
   :returns: ``DUVC_SUCCESS`` on success, ``DUVC_ERROR_BUFFER_TOO_SMALL`` if buffer too small

Error Classification
~~~~~~~~~~~~~~~~~~~~

.. c:function:: int duvc_is_temporary_error(duvc_result_t result)

   Check if error might be resolved by retrying.

   :param result: Error code to check
   :returns: 1 if temporary error, 0 otherwise

.. c:function:: int duvc_is_user_error(duvc_result_t result)

   Check if error is caused by incorrect usage.

   :param result: Error code to check
   :returns: 1 if user error, 0 otherwise

.. c:function:: int duvc_should_retry_operation(duvc_result_t result)

   Check if operation should be retried.

   :param result: Error code to analyze
   :returns: 1 if retry recommended, 0 otherwise

Advanced Error Handling
~~~~~~~~~~~~~~~~~~~~~~~

.. c:function:: duvc_result_t duvc_set_error_context(const char* operation, const char* device_info)

   Set error context for detailed reporting.

   :param operation: Operation being performed
   :param device_info: Device information (optional)
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_get_error_statistics(char* buffer, size_t buffer_size, size_t* required_size)

   Get error statistics for debugging.

   :param buffer: Buffer to receive statistics (can be NULL to query size)
   :param buffer_size: Size of buffer in bytes
   :param required_size: Required buffer size including null terminator
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_suggest_error_resolution(duvc_result_t error_code, char* buffer, size_t buffer_size, size_t* required_size)

   Get suggested resolution for error code.

   :param error_code: Error code to get suggestions for
   :param buffer: Buffer to receive suggestions (can be NULL to query size)
   :param buffer_size: Size of buffer in bytes
   :param required_size: Required buffer size including null terminator
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: void duvc_reset_error_statistics(void)

   Reset error statistics counters.

Logging System
--------------

Log Levels
~~~~~~~~~~

.. c:type:: duvc_log_level_t

   Log levels for diagnostic output.

   .. c:enumerator:: DUVC_LOG_DEBUG

      Debug information

   .. c:enumerator:: DUVC_LOG_INFO

      Informational messages

   .. c:enumerator:: DUVC_LOG_WARNING

      Warning messages

   .. c:enumerator:: DUVC_LOG_ERROR

      Error messages

   .. c:enumerator:: DUVC_LOG_CRITICAL

      Critical errors

Logging Functions
~~~~~~~~~~~~~~~~~

.. c:function:: duvc_result_t duvc_set_log_callback(duvc_log_callback_t callback, void* user_data)

   Set global log callback function.

   :param callback: Log callback function (NULL to disable logging)
   :param user_data: User data passed to callback
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_set_log_level(duvc_log_level_t level)

   Set minimum log level.

   :param level: Minimum level to log
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_get_log_level(duvc_log_level_t* level)

   Get current minimum log level.

   :param level: Output current minimum log level
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_log_message(duvc_log_level_t level, const char* message)

   Log a message at specified level.

   :param level: Log level
   :param message: Message to log
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

Hotplug Monitoring
------------------

.. c:function:: duvc_result_t duvc_enable_hotplug_monitoring(duvc_hotplug_callback_t callback, void* user_data)

   Enable device hotplug monitoring.

   :param callback: Callback function for hotplug events
   :param user_data: User data passed to callback
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_disable_hotplug_monitoring(void)

   Disable device hotplug monitoring.

   :returns: ``DUVC_SUCCESS`` on success, error code on failure

Utility Functions
-----------------

.. c:function:: int duvc_is_value_valid(const duvc_prop_range_t* range, int32_t value)

   Check if property value is valid for given range.

   :param range: Property range constraints
   :param value: Value to check
   :returns: 1 if valid, 0 if invalid

.. c:function:: int32_t duvc_clamp_value(const duvc_prop_range_t* range, int32_t value)

   Clamp value to valid range with step alignment.

   :param range: Property range constraints
   :param value: Value to clamp
   :returns: Nearest valid value within range

.. c:function:: duvc_result_t duvc_is_camera_property_supported(const duvc_device_t* device, duvc_cam_prop_t prop, int* supported)

   Check if device supports specific camera property.

   :param device: Target device
   :param prop: Camera property to check
   :param supported: Output - 1 if supported, 0 if not supported
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_is_video_property_supported(const duvc_device_t* device, duvc_vid_prop_t prop, int* supported)

   Check if device supports specific video property.

   :param device: Target device
   :param prop: Video property to check
   :param supported: Output - 1 if supported, 0 if not supported
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

Vendor Extensions
-----------------

Logitech Properties
~~~~~~~~~~~~~~~~~~~

.. c:function:: duvc_result_t duvc_get_logitech_property(const duvc_device_t* device, duvc_logitech_prop_t prop, duvc_vendor_property_t* property)

   Get Logitech vendor-specific property.

   :param device: Target device
   :param prop: Logitech property to get
   :param property: Output vendor property data
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_set_logitech_property(const duvc_device_t* device, duvc_logitech_prop_t prop, const duvc_vendor_property_t* property)

   Set Logitech vendor-specific property.

   :param device: Target device
   :param prop: Logitech property to set
   :param property: Vendor property data to set
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_query_logitech_property_support(const duvc_device_t* device, duvc_logitech_prop_t prop, int* supported)

   Check if device supports specific Logitech property.

   :param device: Target device
   :param prop: Logitech property to check
   :param supported: Output - 1 if supported, 0 if not supported
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

Generic Vendor Properties
~~~~~~~~~~~~~~~~~~~~~~~~~

.. c:function:: duvc_result_t duvc_get_vendor_property(const duvc_device_t* device, const char* property_set_guid, uint32_t property_id, duvc_vendor_property_t* property)

   Get generic vendor property by GUID and ID.

   :param device: Target device
   :param property_set_guid: Property set GUID as string
   :param property_id: Property ID within set
   :param property: Output vendor property data
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

.. c:function:: duvc_result_t duvc_set_vendor_property(const duvc_device_t* device, const char* property_set_guid, uint32_t property_id, const duvc_vendor_property_t* property)

   Set generic vendor property by GUID and ID.

   :param device: Target device
   :param property_set_guid: Property set GUID as string
   :param property_id: Property ID within set
   :param property: Vendor property data to set
   :returns: ``DUVC_SUCCESS`` on success, error code on failure

Examples
--------

Basic Device Enumeration
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

    #include "duvc-ctl/c/api.h"
    #include <stdio.h>
    #include <stdlib.h>

    int main() {
        // Initialize library
        duvc_result_t result = duvc_initialize();
        if (result != DUVC_SUCCESS) {
            fprintf(stderr, "Failed to initialize: %s\n", duvc_get_error_string(result));
            return 1;
        }
        
        // Check version compatibility
        if (!duvc_check_abi_compatibility(DUVC_ABI_VERSION)) {
            fprintf(stderr, "ABI version mismatch\n");
            duvc_shutdown();
            return 1;
        }
        
        printf("duvc-ctl version: %s\n", duvc_get_version_string());
        
        // List devices
        duvc_device_t** devices;
        size_t count;
        result = duvc_list_devices(&devices, &count);
        if (result != DUVC_SUCCESS) {
            fprintf(stderr, "Failed to list devices: %s\n", duvc_get_error_string(result));
            duvc_shutdown();
            return 1;
        }
        
        printf("Found %zu devices:\n", count);
        
        for (size_t i = 0; i < count; i++) {
            // Get device name
            char name[256];
            size_t name_size;
            result = duvc_get_device_name(devices[i], name, sizeof(name), &name_size);
            if (result == DUVC_SUCCESS) {
                printf("  [%zu] %s\n", i, name);
                
                // Check if connected
                int connected;
                if (duvc_is_device_connected(devices[i], &connected) == DUVC_SUCCESS) {
                    printf("       Status: %s\n", connected ? "Connected" : "Disconnected");
                }
            }
        }
        
        // Cleanup
        duvc_free_device_list(devices, count);
        duvc_shutdown();
        return 0;
    }

Camera Property Control
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

    #include "duvc-ctl/c/api.h"
    #include <stdio.h>

    void demonstrate_ptz_control(duvc_device_t* device) {
        duvc_connection_t* conn;
        duvc_result_t result;
        
        printf("Demonstrating PTZ control...\n");
        
        // Create connection for efficient operations
        result = duvc_create_connection(device, &conn);
        if (result != DUVC_SUCCESS) {
            fprintf(stderr, "Failed to create connection: %s\n", duvc_get_error_string(result));
            return;
        }
        
        // Get current zoom settings
        duvc_prop_setting_t zoom_setting;
        result = duvc_connection_get_camera_property(conn, DUVC_CAM_PROP_ZOOM, &zoom_setting);
        if (result == DUVC_SUCCESS) {
            printf("Current zoom: %d (%s)\n", 
                   zoom_setting.value,
                   zoom_setting.mode == DUVC_CAM_MODE_AUTO ? "Auto" : "Manual");
            
            // Get zoom range
            duvc_prop_range_t zoom_range;
            result = duvc_connection_get_camera_property_range(conn, DUVC_CAM_PROP_ZOOM, &zoom_range);
            if (result == DUVC_SUCCESS) {
                printf("Zoom range: %d to %d (step: %d, default: %d)\n",
                       zoom_range.min, zoom_range.max, zoom_range.step, zoom_range.default_val);
                
                // Set zoom to middle of range
                duvc_prop_setting_t new_zoom;
                new_zoom.value = (zoom_range.min + zoom_range.max) / 2;
                new_zoom.value = duvc_clamp_value(&zoom_range, new_zoom.value);
                new_zoom.mode = DUVC_CAM_MODE_MANUAL;
                
                result = duvc_connection_set_camera_property(conn, DUVC_CAM_PROP_ZOOM, &new_zoom);
                if (result == DUVC_SUCCESS) {
                    printf("Set zoom to: %d\n", new_zoom.value);
                } else {
                    fprintf(stderr, "Failed to set zoom: %s\n", duvc_get_error_string(result));
                }
            }
        } else if (result == DUVC_ERROR_PROPERTY_NOT_SUPPORTED) {
            printf("Zoom not supported on this device\n");
        } else {
            fprintf(stderr, "Failed to get zoom: %s\n", duvc_get_error_string(result));
        }
        
        // Pan and Tilt control
        duvc_prop_setting_t center_setting = {0, DUVC_CAM_MODE_MANUAL};
        
        result = duvc_connection_set_camera_property(conn, DUVC_CAM_PROP_PAN, &center_setting);
        if (result == DUVC_SUCCESS) {
            printf("Pan centered\n");
        }
        
        result = duvc_connection_set_camera_property(conn, DUVC_CAM_PROP_TILT, &center_setting);
        if (result == DUVC_SUCCESS) {
            printf("Tilt centered\n");
        }
        
        duvc_close_connection(conn);
    }

    int main() {
        duvc_initialize();
        
        duvc_device_t** devices;
        size_t count;
        if (duvc_list_devices(&devices, &count) == DUVC_SUCCESS && count > 0) {
            demonstrate_ptz_control(devices[0]);
            duvc_free_device_list(devices, count);
        } else {
            printf("No devices found\n");
        }
        
        duvc_shutdown();
        return 0;
    }

Video Property Management
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

    #include "duvc-ctl/c/api.h"
    #include <stdio.h>

    void adjust_video_properties(duvc_device_t* device) {
        duvc_connection_t* conn;
        duvc_result_t result;
        
        printf("Adjusting video properties...\n");
        
        result = duvc_create_connection(device, &conn);
        if (result != DUVC_SUCCESS) {
            fprintf(stderr, "Failed to create connection\n");
            return;
        }
        
        // Brightness control
        duvc_prop_range_t brightness_range;
        result = duvc_connection_get_video_property_range(conn, DUVC_VID_PROP_BRIGHTNESS, &brightness_range);
        if (result == DUVC_SUCCESS) {
            printf("Brightness range: %d to %d\n", brightness_range.min, brightness_range.max);
            
            // Set brightness to 75% of range
            int32_t target_brightness = brightness_range.min + 
                (int32_t)((brightness_range.max - brightness_range.min) * 0.75);
            target_brightness = duvc_clamp_value(&brightness_range, target_brightness);
            
            duvc_prop_setting_t brightness_setting = {target_brightness, DUVC_CAM_MODE_MANUAL};
            result = duvc_connection_set_video_property(conn, DUVC_VID_PROP_BRIGHTNESS, &brightness_setting);
            if (result == DUVC_SUCCESS) {
                printf("Set brightness to: %d\n", target_brightness);
            }
        }
        
        // Auto white balance
        duvc_prop_setting_t wb_setting = {0, DUVC_CAM_MODE_AUTO};
        result = duvc_connection_set_video_property(conn, DUVC_VID_PROP_WHITE_BALANCE, &wb_setting);
        if (result == DUVC_SUCCESS) {
            printf("Enabled auto white balance\n");
        } else if (result == DUVC_ERROR_PROPERTY_NOT_SUPPORTED) {
            printf("White balance not supported\n");
        }
        
        duvc_close_connection(conn);
    }

Batch Operations
~~~~~~~~~~~~~~~~

.. code-block:: c

    #include "duvc-ctl/c/api.h"
    #include <stdio.h>

    void batch_property_operations(duvc_device_t* device) {
        printf("Demonstrating batch operations...\n");
        
        // Properties to read
        duvc_cam_prop_t cam_props[] = {
            DUVC_CAM_PROP_PAN,
            DUVC_CAM_PROP_TILT,
            DUVC_CAM_PROP_ZOOM
        };
        duvc_prop_setting_t cam_settings[3];
        
        // Get multiple camera properties at once
        duvc_result_t result = duvc_get_multiple_camera_properties(
            device, cam_props, cam_settings, 3);
        
        if (result == DUVC_SUCCESS) {
            printf("Current camera settings:\n");
            printf("  Pan: %d (%s)\n", cam_settings[0].value, 
                   cam_settings[0].mode == DUVC_CAM_MODE_AUTO ? "Auto" : "Manual");
            printf("  Tilt: %d (%s)\n", cam_settings[1].value,
                   cam_settings[1].mode == DUVC_CAM_MODE_AUTO ? "Auto" : "Manual");
            printf("  Zoom: %d (%s)\n", cam_settings[2].value,
                   cam_settings[2].mode == DUVC_CAM_MODE_AUTO ? "Auto" : "Manual");
        }
        
        // Set multiple properties
        duvc_prop_setting_t new_settings[] = {
            {0, DUVC_CAM_MODE_MANUAL},  // Center pan
            {0, DUVC_CAM_MODE_MANUAL},  // Center tilt
            {100, DUVC_CAM_MODE_MANUAL} // Set zoom
        };
        
        result = duvc_set_multiple_camera_properties(device, cam_props, new_settings, 3);
        if (result == DUVC_SUCCESS) {
            printf("Updated camera properties successfully\n");
        }
    }

Error Handling Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

    #include "duvc-ctl/c/api.h"
    #include <stdio.h>

    int safe_camera_operation(duvc_device_t* device) {
        duvc_result_t result;
        
        // Check device connectivity first
        int connected;
        result = duvc_is_device_connected(device, &connected);
        if (result != DUVC_SUCCESS || !connected) {
            fprintf(stderr, "Device not available\n");
            return 0;
        }
        
        // Check property support before attempting to use
        int supported;
        result = duvc_is_camera_property_supported(device, DUVC_CAM_PROP_ZOOM, &supported);
        if (result != DUVC_SUCCESS || !supported) {
            printf("Zoom not supported, skipping zoom control\n");
            return 1;
        }
        
        // Get property range to validate values
        duvc_prop_range_t zoom_range;
        result = duvc_get_camera_property_range(device, DUVC_CAM_PROP_ZOOM, &zoom_range);
        if (result != DUVC_SUCCESS) {
            char error_details[512];
            size_t required;
            if (duvc_get_last_error_details(error_details, sizeof(error_details), &required) == DUVC_SUCCESS) {
                fprintf(stderr, "Failed to get zoom range: %s\n", error_details);
            }
            return 0;
        }
        
        // Validate and set zoom
        int32_t desired_zoom = 100;
        if (!duvc_is_value_valid(&zoom_range, desired_zoom)) {
            desired_zoom = duvc_clamp_value(&zoom_range, desired_zoom);
            printf("Clamped zoom value to: %d\n", desired_zoom);
        }
        
        duvc_prop_setting_t zoom_setting = {desired_zoom, DUVC_CAM_MODE_MANUAL};
        result = duvc_set_camera_property(device, DUVC_CAM_PROP_ZOOM, &zoom_setting);
        
        if (result != DUVC_SUCCESS) {
            // Check if we should retry
            if (duvc_should_retry_operation(result)) {
                printf("Retrying zoom operation...\n");
                result = duvc_set_camera_property(device, DUVC_CAM_PROP_ZOOM, &zoom_setting);
            }
            
            if (result != DUVC_SUCCESS) {
                // Get resolution suggestions
                char suggestions[1024];
                size_t required;
                if (duvc_suggest_error_resolution(result, suggestions, sizeof(suggestions), &required) == DUVC_SUCCESS) {
                    printf("Error resolution suggestions:\n%s\n", suggestions);
                }
                return 0;
            }
        }
        
        printf("Zoom set successfully to %d\n", desired_zoom);
        return 1;
    }

Logging and Diagnostics
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: c

    #include "duvc-ctl/c/api.h"
    #include <stdio.h>

    void log_callback(duvc_log_level_t level, const char* message, void* user_data) {
        const char* level_str;
        switch (level) {
            case DUVC_LOG_DEBUG: level_str = "DEBUG"; break;
            case DUVC_LOG_INFO: level_str = "INFO"; break;
            case DUVC_LOG_WARNING: level_str = "WARNING"; break;
            case DUVC_LOG_ERROR: level_str = "ERROR"; break;
            case DUVC_LOG_CRITICAL: level_str = "CRITICAL"; break;
            default: level_str = "UNKNOWN"; break;
        }
        printf("[%s] %s\n", level_str, message);
    }

    int main() {
        // Initialize with logging
        duvc_initialize();
        
        // Enable detailed logging
        duvc_set_log_level(DUVC_LOG_DEBUG);
        duvc_set_log_callback(log_callback, NULL);
        
        // Operations will now be logged
        duvc_device_t** devices;
        size_t count;
        duvc_result_t result = duvc_list_devices(&devices, &count);
        
        if (result == DUVC_SUCCESS) {
            printf("Found %zu devices\n", count);
            duvc_free_device_list(devices, count);
        } else {
            printf("Failed to list devices: %s\n", duvc_get_error_string(result));
        }
        
        // Get error statistics
        char stats[2048];
        size_t required;
        if (duvc_get_error_statistics(stats, sizeof(stats), &required) == DUVC_SUCCESS) {
            printf("\nError Statistics:\n%s\n", stats);
        }
        
        duvc_shutdown();
        return 0;
    }

Thread Safety
-------------

The C API is designed for multi-threaded environments with the following guarantees:

- **Library initialization/shutdown**: Must be called from main thread only
- **Device enumeration**: Thread-safe, can be called from any thread
- **Property operations**: Thread-safe across different devices
- **Connection handles**: Not thread-safe, use separate connections per thread
- **Error handling**: Thread-local error state for detailed error information

Example of safe multi-threaded usage:

.. code-block:: c

    #include "duvc-ctl/c/api.h"
    #include <pthread.h>

    void* device_control_thread(void* arg) {
        duvc_device_t* device = (duvc_device_t*)arg;
        
        // Each thread creates its own connection
        duvc_connection_t* conn;
        if (duvc_create_connection(device, &conn) == DUVC_SUCCESS) {
            // Thread-safe operations on this connection
            duvc_prop_setting_t setting = {0, DUVC_CAM_MODE_MANUAL};
            duvc_connection_set_camera_property(conn, DUVC_CAM_PROP_PAN, &setting);
            duvc_close_connection(conn);
        }
        
        return NULL;
    }

    int main() {
        duvc_initialize(); // Main thread only
        
        duvc_device_t** devices;
        size_t count;
        duvc_list_devices(&devices, &count); // Thread-safe
        
        if (count >= 2) {
            pthread_t thread1, thread2;
            pthread_create(&thread1, NULL, device_control_thread, devices[0]);
            pthread_create(&thread2, NULL, device_control_thread, devices[1]);
            
            pthread_join(thread1, NULL);
            pthread_join(thread2, NULL);
        }
        
        duvc_free_device_list(devices, count);
        duvc_shutdown(); // Main thread only
        return 0;
    }

Compilation and Linking
-----------------------

To use the C API, compile and link against the duvc-ctl C library:

**Windows (MSVC):**

.. code-block:: batch

   cl /I"path\to\duvc-ctl\include" myapp.c duvc-c.lib

**Windows (MinGW):**

.. code-block:: bash

   gcc -I/path/to/duvc-ctl/include myapp.c -lduvc-c

**CMake Integration:**

.. code-block:: cmake

   find_package(duvc REQUIRED)
   target_link_libraries(myapp duvc::c-api)

The C API requires:

- Windows 10 or later
- Visual C++ Redistributable 2019/2022 (runtime dependency)
- DirectShow components (included with Windows)
