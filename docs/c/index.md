# duvc-ctl C API Documentation

Complete documentation for the duvc-ctl C ABI (Application Binary Interface), providing stable C-compatible access to UVC camera control functionality.

## Table of Contents

1. [C API Overview](#c-api-overview)
2. [Functions and Types Reference](#functions-and-types-reference)
3. [Examples](#examples)

***

## Introduction

The duvc-ctl C API provides a stable, platform-agnostic interface for controlling USB Video Class (UVC) cameras. This C ABI ensures compatibility across different compilers, programming languages, and runtime environments while maintaining full access to the library's capabilities.

### Key Features

- **Stable ABI**: Versioned interface with backward compatibility guarantees
- **Cross-Language Compatibility**: Usable from C, C++, Python, Rust, Go, and other languages
- **Comprehensive Functionality**: Full access to camera properties, device management, and vendor extensions
- **Error Handling**: Robust error reporting with detailed diagnostics
- **Memory Management**: Clear ownership semantics and proper resource cleanup
- **Thread Safety**: Safe for concurrent access from multiple threads


### Architecture

The C API acts as a bridge between client applications and the underlying C++ implementation:

```
Client Application
       ↓
   C API (api.h)
       ↓  
C++ Implementation
       ↓
Platform Layer (DirectShow)
       ↓
UVC Hardware
```


## Getting Started

### Prerequisites

- **Platform**: Windows 10+ (x64)
- **Compiler**: Any C99-compatible compiler
- **Dependencies**: None (self-contained)


### Basic Usage Pattern

```c
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
```


### Compilation

Link against the duvc-ctl library:

```bash
gcc -o myapp myapp.c -lduvc-ctl
```


## Core Concepts

### Result Codes

All operations return `duvc_result_t` status codes:

- `DUVC_SUCCESS` (0): Operation succeeded
- `DUVC_ERROR_*`: Various error conditions with detailed meanings


### Device Handles

Devices are represented as opaque `duvc_device_t*` pointers managed by the library. Always use library functions to enumerate and access devices.

### Property System

Camera properties use value-mode pairs:

```c
typedef struct {
    int32_t value;              // Property value
    duvc_cam_mode_t mode;       // DUVC_CAM_MODE_AUTO or DUVC_CAM_MODE_MANUAL
} duvc_prop_setting_t;
```


### Connection Management

For efficiency, create persistent connections for multiple operations:

```c
duvc_connection_t* conn;
duvc_create_connection(device, &conn);
// ... multiple operations ...
duvc_close_connection(conn);
```


## ABI Versioning

### Version Checking

```c
// Check compatibility at runtime
if (!duvc_check_abi_compatibility(DUVC_ABI_VERSION)) {
    fprintf(stderr, "ABI version mismatch\n");
    return 1;
}

printf("Library version: %s\n", duvc_get_version_string());
```


### Compatibility Rules

- **Major Version**: Must match exactly (breaking changes)
- **Minor Version**: Runtime ≥ compiled (backward compatible additions)
- **Patch Version**: Any (bug fixes only)


## Error Handling

### Basic Error Handling

```c
duvc_result_t result = duvc_some_operation();
if (result != DUVC_SUCCESS) {
    fprintf(stderr, "Error: %s\n", duvc_get_error_string(result));
    
    // Get detailed error information
    char details[^1024];
    size_t required;
    if (duvc_get_last_error_details(details, sizeof(details), &required) == DUVC_SUCCESS) {
        fprintf(stderr, "Details: %s\n", details);
    }
}
```


### Advanced Error Analysis

```c
// Check error classification
if (duvc_is_device_error(result)) {
    // Handle device-related errors
} else if (duvc_is_permission_error(result)) {
    // Handle permission errors
}

// Check if operation should be retried
if (duvc_should_retry_operation(result)) {
    // Implement retry logic
}
```


***

## Functions and Types Reference

## Version and ABI Management

### Functions

#### `duvc_get_version`

```c
uint32_t duvc_get_version(void);
```

**Description**: Get runtime library version as integer
**Returns**: Version number in format `(major << 16) | (minor << 8) | patch`

#### `duvc_get_version_string`

```c
const char* duvc_get_version_string(void);
```

**Description**: Get runtime library version as string
**Returns**: Null-terminated version string (e.g., "2.0.0")
**Note**: Returned string is statically allocated

#### `duvc_check_abi_compatibility`

```c
int duvc_check_abi_compatibility(uint32_t compiled_version);
```

**Description**: Check ABI compatibility between compiled and runtime versions
**Parameters**:

- `compiled_version`: Version application was compiled with (use `DUVC_ABI_VERSION`)
**Returns**: 1 if compatible, 0 if incompatible


## Library Management

#### `duvc_initialize`

```c
duvc_result_t duvc_initialize(void);
```

**Description**: Initialize the duvc library. Must be called before other functions.
**Returns**: `DUVC_SUCCESS` on success, error code on failure
**Thread Safety**: Not thread-safe, call from main thread only

#### `duvc_shutdown`

```c
void duvc_shutdown(void);
```

**Description**: Shutdown library and cleanup resources
**Thread Safety**: Not thread-safe, call from main thread only

#### `duvc_is_initialized`

```c
int duvc_is_initialized(void);
```

**Description**: Check if library is initialized
**Returns**: 1 if initialized, 0 if not

## Core Types and Enumerations

### Result Codes

```c
typedef enum {
    DUVC_SUCCESS = 0,                    /**< Operation succeeded */
    DUVC_ERROR_DEVICE_NOT_FOUND,        /**< Device not found or disconnected */
    DUVC_ERROR_DEVICE_BUSY,             /**< Device is busy or in use */
    DUVC_ERROR_PROPERTY_NOT_SUPPORTED,  /**< Property not supported by device */
    DUVC_ERROR_INVALID_VALUE,           /**< Property value out of range */
    DUVC_ERROR_PERMISSION_DENIED,       /**< Insufficient permissions */
    DUVC_ERROR_SYSTEM_ERROR,            /**< System/platform error */
    DUVC_ERROR_INVALID_ARGUMENT,        /**< Invalid function argument */
    DUVC_ERROR_NOT_IMPLEMENTED,         /**< Feature not implemented */
    DUVC_ERROR_CONNECTION_FAILED,       /**< Failed to establish connection */
    DUVC_ERROR_TIMEOUT,                 /**< Operation timed out */
    DUVC_ERROR_BUFFER_TOO_SMALL         /**< Provided buffer too small */
} duvc_result_t;
```


### Camera Properties

```c
typedef enum {
    DUVC_CAM_PROP_PAN = 0,              /**< Horizontal camera rotation */
    DUVC_CAM_PROP_TILT,                 /**< Vertical camera rotation */
    DUVC_CAM_PROP_ROLL,                 /**< Camera roll rotation */
    DUVC_CAM_PROP_ZOOM,                 /**< Optical zoom level */
    DUVC_CAM_PROP_EXPOSURE,             /**< Exposure time */
    DUVC_CAM_PROP_IRIS,                 /**< Aperture/iris setting */
    DUVC_CAM_PROP_FOCUS,                /**< Focus position */
    DUVC_CAM_PROP_SCAN_MODE,            /**< Scan mode */
    DUVC_CAM_PROP_PRIVACY,              /**< Privacy mode */
    DUVC_CAM_PROP_PAN_RELATIVE,         /**< Relative pan movement */
    DUVC_CAM_PROP_TILT_RELATIVE,        /**< Relative tilt movement */
    DUVC_CAM_PROP_ROLL_RELATIVE,        /**< Relative roll movement */
    DUVC_CAM_PROP_ZOOM_RELATIVE,        /**< Relative zoom movement */
    DUVC_CAM_PROP_EXPOSURE_RELATIVE,    /**< Relative exposure adjustment */
    DUVC_CAM_PROP_IRIS_RELATIVE,        /**< Relative iris adjustment */
    DUVC_CAM_PROP_FOCUS_RELATIVE,       /**< Relative focus adjustment */
    DUVC_CAM_PROP_PAN_TILT,             /**< Combined pan/tilt control */
    DUVC_CAM_PROP_PAN_TILT_RELATIVE,    /**< Relative pan/tilt movement */
    DUVC_CAM_PROP_FOCUS_SIMPLE,         /**< Simple focus control */
    DUVC_CAM_PROP_DIGITAL_ZOOM,         /**< Digital zoom level */
    DUVC_CAM_PROP_DIGITAL_ZOOM_RELATIVE, /**< Relative digital zoom */
    DUVC_CAM_PROP_BACKLIGHT_COMPENSATION, /**< Backlight compensation */
    DUVC_CAM_PROP_LAMP                  /**< Camera lamp/flash control */
} duvc_cam_prop_t;
```


### Video Properties

```c
typedef enum {
    DUVC_VID_PROP_BRIGHTNESS = 0,       /**< Image brightness level */
    DUVC_VID_PROP_CONTRAST,             /**< Image contrast level */
    DUVC_VID_PROP_HUE,                  /**< Color hue adjustment */
    DUVC_VID_PROP_SATURATION,           /**< Color saturation level */
    DUVC_VID_PROP_SHARPNESS,            /**< Image sharpness level */
    DUVC_VID_PROP_GAMMA,                /**< Gamma correction value */
    DUVC_VID_PROP_COLOR_ENABLE,         /**< Color vs. monochrome mode */
    DUVC_VID_PROP_WHITE_BALANCE,        /**< White balance adjustment */
    DUVC_VID_PROP_BACKLIGHT_COMPENSATION, /**< Backlight compensation level */
    DUVC_VID_PROP_GAIN                  /**< Sensor gain level */
} duvc_vid_prop_t;
```


### Property Structures

```c
typedef struct {
    int32_t value;                      /**< Property value */
    duvc_cam_mode_t mode;               /**< Control mode (auto/manual) */
} duvc_prop_setting_t;

typedef struct {
    int32_t min;                        /**< Minimum supported value */
    int32_t max;                        /**< Maximum supported value */
    int32_t step;                       /**< Step size between valid values */
    int32_t default_val;                /**< Default value */
    duvc_cam_mode_t default_mode;       /**< Default control mode */
} duvc_prop_range_t;
```


### Control Modes

```c
typedef enum {
    DUVC_CAM_MODE_AUTO = 0,             /**< Automatic control by camera */
    DUVC_CAM_MODE_MANUAL                /**< Manual control by application */
} duvc_cam_mode_t;
```


### Opaque Handle Types

```c
typedef struct duvc_device_t duvc_device_t;           /**< Device handle */
typedef struct duvc_connection_t duvc_connection_t;   /**< Connection handle */
```


## Device Management

#### `duvc_list_devices`

```c
duvc_result_t duvc_list_devices(duvc_device_t*** devices, size_t* count);
```

**Description**: Enumerate all available camera devices
**Parameters**:

- `devices`: Output array of device pointers (caller must free with `duvc_free_device_list`)
- `count`: Number of devices in the array
**Returns**: `DUVC_SUCCESS` on success, error code on failure


#### `duvc_free_device_list`

```c
void duvc_free_device_list(duvc_device_t** devices, size_t count);
```

**Description**: Free device list returned by `duvc_list_devices`
**Parameters**:

- `devices`: Device array to free
- `count`: Number of devices in the array


#### `duvc_is_device_connected`

```c
duvc_result_t duvc_is_device_connected(const duvc_device_t* device, int* connected);
```

**Description**: Check if device is currently connected
**Parameters**:

- `device`: Device to check
- `connected`: Output - 1 if connected, 0 if not
**Returns**: `DUVC_SUCCESS` on success, error code on failure


#### `duvc_get_device_name`

```c
duvc_result_t duvc_get_device_name(const duvc_device_t* device,
                                   char* name_buffer,
                                   size_t buffer_size,
                                   size_t* required_size);
```

**Description**: Get device name as UTF-8 string
**Parameters**:

- `device`: Target device
- `name_buffer`: Buffer to receive name (can be NULL to query size)
- `buffer_size`: Size of name_buffer in bytes
- `required_size`: Required buffer size including null terminator
**Returns**: `DUVC_SUCCESS` on success, `DUVC_ERROR_BUFFER_TOO_SMALL` if buffer too small


#### `duvc_get_device_path`

```c
duvc_result_t duvc_get_device_path(const duvc_device_t* device,
                                   char* path_buffer,
                                   size_t buffer_size,
                                   size_t* required_size);
```

**Description**: Get device path as UTF-8 string
**Parameters**: Same as `duvc_get_device_name`
**Returns**: Same as `duvc_get_device_name`

## Connection Management

#### `duvc_create_connection`

```c
duvc_result_t duvc_create_connection(const duvc_device_t* device, 
                                     duvc_connection_t** connection);
```

**Description**: Create persistent connection to device for efficient operations
**Parameters**:

- `device`: Device to connect to
- `connection`: Output connection handle
**Returns**: `DUVC_SUCCESS` on success, error code on failure


#### `duvc_close_connection`

```c
duvc_result_t duvc_close_connection(duvc_connection_t* connection);
```

**Description**: Close device connection
**Parameters**:

- `connection`: Connection to close
**Returns**: `DUVC_SUCCESS` on success, error code on failure


#### `duvc_is_connection_valid`

```c
duvc_result_t duvc_is_connection_valid(const duvc_connection_t* connection, int* valid);
```

**Description**: Check if connection is valid
**Parameters**:

- `connection`: Connection to check
- `valid`: Output - 1 if valid, 0 if invalid
**Returns**: `DUVC_SUCCESS` on success, error code on failure


## Property Operations

### Direct Device Access

#### `duvc_get_camera_property`

```c
duvc_result_t duvc_get_camera_property(const duvc_device_t* device,
                                       duvc_cam_prop_t prop,
                                       duvc_prop_setting_t* setting);
```

**Description**: Get current camera property value
**Parameters**:

- `device`: Target device
- `prop`: Camera property to query
- `setting`: Output current property setting
**Returns**: `DUVC_SUCCESS` on success, error code on failure


#### `duvc_set_camera_property`

```c
duvc_result_t duvc_set_camera_property(const duvc_device_t* device,
                                       duvc_cam_prop_t prop,
                                       const duvc_prop_setting_t* setting);
```

**Description**: Set camera property value
**Parameters**:

- `device`: Target device
- `prop`: Camera property to set
- `setting`: New property setting
**Returns**: `DUVC_SUCCESS` on success, error code on failure


#### `duvc_get_camera_property_range`

```c
duvc_result_t duvc_get_camera_property_range(const duvc_device_t* device,
                                             duvc_cam_prop_t prop,
                                             duvc_prop_range_t* range);
```

**Description**: Get valid range for camera property
**Parameters**:

- `device`: Target device
- `prop`: Camera property to query
- `range`: Output property range information
**Returns**: `DUVC_SUCCESS` on success, error code on failure


### Connection-Based Access (More Efficient)

#### `duvc_connection_get_camera_property`

```c
duvc_result_t duvc_connection_get_camera_property(duvc_connection_t* connection,
                                                  duvc_cam_prop_t prop,
                                                  duvc_prop_setting_t* setting);
```

**Description**: Get camera property using persistent connection
**Parameters**: Similar to direct access but uses connection handle
**Performance**: More efficient for multiple operations on same device

## Vendor Properties

#### `duvc_get_vendor_property`

```c
duvc_result_t duvc_get_vendor_property(const duvc_device_t* device,
                                       const char* property_set_guid,
                                       uint32_t property_id,
                                       void* data,
                                       size_t* data_size);
```

**Description**: Get vendor-specific property data
**Parameters**:

- `device`: Target device
- `property_set_guid`: Property set GUID as string (e.g., "{12345678-1234-1234-1234-123456789ABC}")
- `property_id`: Property ID within set
- `data`: Buffer to receive property data (can be NULL to query size)
- `data_size`: Input: buffer size, Output: actual data size
**Returns**: `DUVC_SUCCESS` on success, `DUVC_ERROR_BUFFER_TOO_SMALL` if buffer too small


#### `duvc_set_vendor_property`

```c
duvc_result_t duvc_set_vendor_property(const duvc_device_t* device,
                                       const char* property_set_guid,
                                       uint32_t property_id,
                                       const void* data,
                                       size_t data_size);
```

**Description**: Set vendor-specific property data
**Parameters**: Similar to get but with input data
**Returns**: `DUVC_SUCCESS` on success, error code on failure

### Logitech Vendor Properties

#### `duvc_supports_logitech_properties`

```c
duvc_result_t duvc_supports_logitech_properties(const duvc_device_t* device, int* supported);
```

**Description**: Check if device supports Logitech vendor properties
**Returns**: 1 if supported, 0 if not supported

#### `duvc_get_logitech_property_int32`

```c
duvc_result_t duvc_get_logitech_property_int32(const duvc_device_t* device,
                                               duvc_logitech_prop_t prop,
                                               int32_t* value);
```

**Description**: Get Logitech property as 32-bit integer
**Parameters**:

- `prop`: Logitech property (e.g., `DUVC_LOGITECH_PROP_RIGHT_LIGHT`)
- `value`: Output property value


## Error Handling

#### `duvc_get_error_string`

```c
const char* duvc_get_error_string(duvc_result_t result);
```

**Description**: Get human-readable error description
**Returns**: Null-terminated error string (statically allocated)

#### `duvc_get_last_error_details`

```c
duvc_result_t duvc_get_last_error_details(char* buffer, 
                                          size_t buffer_size, 
                                          size_t* required_size);
```

**Description**: Get detailed error information from last operation
**Parameters**: Standard buffer pattern - can pass NULL buffer to query required size

#### `duvc_is_device_error`

```c
int duvc_is_device_error(duvc_result_t result);
```

**Description**: Check if error is device-related
**Returns**: 1 if device-related, 0 otherwise

## Utility Functions

#### `duvc_is_value_valid`

```c
int duvc_is_value_valid(const duvc_prop_range_t* range, int32_t value);
```

**Description**: Check if property value is valid for given range
**Returns**: 1 if valid, 0 if invalid

#### `duvc_clamp_value`

```c
int32_t duvc_clamp_value(const duvc_prop_range_t* range, int32_t value);
```

**Description**: Clamp value to valid range with step alignment
**Returns**: Nearest valid value within range

***

## Examples

### Basic Device Enumeration

```c
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
        char name[^256];
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
```


### Camera Property Control

```c
#include "duvc-ctl/c/api.h"
#include <stdio.h>
#include <stdlib.h>

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
            new_zoom.value = duvc_clamp_value(&zoom_range, new_zoom.value); // Ensure valid
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
    
    // Pan control
    duvc_prop_setting_t pan_setting = {0, DUVC_CAM_MODE_MANUAL}; // Center pan
    result = duvc_connection_set_camera_property(conn, DUVC_CAM_PROP_PAN, &pan_setting);
    if (result == DUVC_SUCCESS) {
        printf("Pan centered\n");
    } else if (result != DUVC_ERROR_PROPERTY_NOT_SUPPORTED) {
        fprintf(stderr, "Failed to set pan: %s\n", duvc_get_error_string(result));
    }
    
    // Tilt control
    duvc_prop_setting_t tilt_setting = {0, DUVC_CAM_MODE_MANUAL}; // Center tilt
    result = duvc_connection_set_camera_property(conn, DUVC_CAM_PROP_TILT, &tilt_setting);
    if (result == DUVC_SUCCESS) {
        printf("Tilt centered\n");
    } else if (result != DUVC_ERROR_PROPERTY_NOT_SUPPORTED) {
        fprintf(stderr, "Failed to set tilt: %s\n", duvc_get_error_string(result));
    }
    
    duvc_close_connection(conn);
}

int main() {
    duvc_initialize();
    
    duvc_device_t** devices;
    size_t count;
    if (duvc_list_devices(&devices, &count) == DUVC_SUCCESS && count > 0) {
        demonstrate_ptz_control(devices[^0]);
        duvc_free_device_list(devices, count);
    } else {
        printf("No devices found\n");
    }
    
    duvc_shutdown();
    return 0;
}
```


### Video Property Management

```c
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

int main() {
    duvc_initialize();
    
    duvc_device_t** devices;
    size_t count;
    if (duvc_list_devices(&devices, &count) == DUVC_SUCCESS && count > 0) {
        adjust_video_properties(devices[^0]);
        duvc_free_device_list(devices, count);
    }
    
    duvc_shutdown();
    return 0;
}
```


### Error Handling and Diagnostics

```c
#include "duvc-ctl/c/api.h"
#include <stdio.h>

void demonstrate_error_handling() {
    duvc_result_t result;
    
    // Attempt operation that might fail
    duvc_device_t** devices;
    size_t count;
    result = duvc_list_devices(&devices, &count);
    
    if (result != DUVC_SUCCESS) {
        // Basic error information
        fprintf(stderr, "Error: %s\n", duvc_get_error_string(result));
        
        // Detailed error information
        char details[^1024];
        size_t required;
        if (duvc_get_last_error_details(details, sizeof(details), &required) == DUVC_SUCCESS) {
            fprintf(stderr, "Details: %s\n", details);
        }
        
        // Error classification
        if (duvc_is_device_error(result)) {
            fprintf(stderr, "This is a device-related error\n");
        }
        
        if (duvc_is_permission_error(result)) {
            fprintf(stderr, "This is a permission error - try running as administrator\n");
        }
        
        // Check if retry might help
        if (duvc_should_retry_operation(result)) {
            fprintf(stderr, "Operation might succeed if retried\n");
        }
        
        // Get diagnostic information
        char diagnostic[^2048];
        if (duvc_get_diagnostic_info(diagnostic, sizeof(diagnostic), &required) == DUVC_SUCCESS) {
            fprintf(stderr, "Diagnostic info:\n%s\n", diagnostic);
        }
        
        return;
    }
    
    // Success case
    printf("Found %zu devices\n", count);
    duvc_free_device_list(devices, count);
}

int main() {
    if (duvc_initialize() != DUVC_SUCCESS) {
        fprintf(stderr, "Failed to initialize library\n");
        return 1;
    }
    
    demonstrate_error_handling();
    duvc_shutdown();
    return 0;
}
```


### Vendor Property Access

```c
#include "duvc-ctl/c/api.h"
#include <stdio.h>
#include <string.h>

void demonstrate_vendor_properties(duvc_device_t* device) {
    duvc_result_t result;
    
    // Check for Logitech support
    int logitech_supported;
    result = duvc_supports_logitech_properties(device, &logitech_supported);
    if (result == DUVC_SUCCESS && logitech_supported) {
        printf("Device supports Logitech properties\n");
        
        // Get RightLight setting
        int32_t rightlight_value;
        result = duvc_get_logitech_property_int32(device, DUVC_LOGITECH_PROP_RIGHT_LIGHT, &rightlight_value);
        if (result == DUVC_SUCCESS) {
            printf("RightLight value: %d\n", rightlight_value);
        }
        
        // Enable face tracking
        result = duvc_set_logitech_property_int32(device, DUVC_LOGITECH_PROP_FACE_TRACKING, 1);
        if (result == DUVC_SUCCESS) {
            printf("Face tracking enabled\n");
        }
    }
    
    // Generic vendor property example
    const char* vendor_guid = "{12345678-1234-5678-9ABC-123456789ABC}"; // Example GUID
    uint32_t property_id = 1;
    
    // Query property size first
    size_t data_size = 0;
    result = duvc_get_vendor_property(device, vendor_guid, property_id, NULL, &data_size);
    if (result == DUVC_ERROR_BUFFER_TOO_SMALL && data_size > 0) {
        // Allocate buffer and get data
        void* data = malloc(data_size);
        if (data) {
            result = duvc_get_vendor_property(device, vendor_guid, property_id, data, &data_size);
            if (result == DUVC_SUCCESS) {
                printf("Got vendor property: %zu bytes\n", data_size);
                // Process vendor data...
            }
            free(data);
        }
    } else if (result == DUVC_ERROR_PROPERTY_NOT_SUPPORTED) {
        printf("Vendor property not supported\n");
    }
}

int main() {
    duvc_initialize();
    
    duvc_device_t** devices;
    size_t count;
    if (duvc_list_devices(&devices, &count) == DUVC_SUCCESS && count > 0) {
        demonstrate_vendor_properties(devices[^0]);
        duvc_free_device_list(devices, count);
    }
    
    duvc_shutdown();
    return 0;
}
```


### Multi-Device Management

```c
#include "duvc-ctl/c/api.h"
#include <stdio.h>

void manage_multiple_devices() {
    duvc_device_t** devices;
    size_t count;
    duvc_result_t result;
    
    result = duvc_list_devices(&devices, &count);
    if (result != DUVC_SUCCESS || count == 0) {
        printf("No devices available\n");
        return;
    }
    
    printf("Managing %zu devices:\n", count);
    
    // Create connections to all devices
    duvc_connection_t** connections = calloc(count, sizeof(duvc_connection_t*));
    if (!connections) {
        duvc_free_device_list(devices, count);
        return;
    }
    
    // Connect to each device
    for (size_t i = 0; i < count; i++) {
        char name[^256];
        size_t name_size;
        duvc_get_device_name(devices[i], name, sizeof(name), &name_size);
        
        result = duvc_create_connection(devices[i], &connections[i]);
        if (result == DUVC_SUCCESS) {
            printf("Connected to device %zu: %s\n", i, name);
        } else {
            printf("Failed to connect to device %zu: %s\n", i, duvc_get_error_string(result));
            connections[i] = NULL;
        }
    }
    
    // Perform operations on all connected devices
    for (size_t i = 0; i < count; i++) {
        if (connections[i]) {
            // Set all devices to auto-exposure
            duvc_prop_setting_t auto_exposure = {0, DUVC_CAM_MODE_AUTO};
            result = duvc_connection_set_camera_property(connections[i], DUVC_CAM_PROP_EXPOSURE, &auto_exposure);
            if (result == DUVC_SUCCESS) {
                printf("Device %zu: Set to auto-exposure\n", i);
            }
            
            // Center pan/tilt on PTZ cameras
            duvc_prop_setting_t center = {0, DUVC_CAM_MODE_MANUAL};
            duvc_connection_set_camera_property(connections[i], DUVC_CAM_PROP_PAN, &center);
            duvc_connection_set_camera_property(connections[i], DUVC_CAM_PROP_TILT, &center);
        }
    }
    
    // Cleanup connections
    for (size_t i = 0; i < count; i++) {
        if (connections[i]) {
            duvc_close_connection(connections[i]);
        }
    }
    
    free(connections);
    duvc_free_device_list(devices, count);
}

int main() {
    duvc_initialize();
    manage_multiple_devices();
    duvc_shutdown();
    return 0;
}
```


### Property Validation and Range Checking

```c
#include "duvc-ctl/c/api.h"
#include <stdio.h>

void safe_property_setting(duvc_device_t* device) {
    duvc_connection_t* conn;
    duvc_result_t result;
    
    result = duvc_create_connection(device, &conn);
    if (result != DUVC_SUCCESS) {
        return;
    }
    
    // Safe zoom adjustment with validation
    duvc_prop_range_t zoom_range;
    result = duvc_connection_get_camera_property_range(conn, DUVC_CAM_PROP_ZOOM, &zoom_range);
    if (result == DUVC_SUCCESS) {
        printf("Zoom range: %d to %d (step: %d)\n", zoom_range.min, zoom_range.max, zoom_range.step);
        
        // Test various zoom values
        int32_t test_values[] = {100, 200, 300, 999, -50};
        size_t num_tests = sizeof(test_values) / sizeof(test_values[^0]);
        
        for (size_t i = 0; i < num_tests; i++) {
            int32_t original_value = test_values[i];
            
            // Check if value is valid
            if (duvc_is_value_valid(&zoom_range, original_value)) {
                printf("Value %d is valid\n", original_value);
            } else {
                printf("Value %d is invalid, ", original_value);
                
                // Clamp to valid range
                int32_t clamped_value = duvc_clamp_value(&zoom_range, original_value);
                printf("clamped to %d\n", clamped_value);
                
                // Use the clamped value
                duvc_prop_setting_t zoom_setting = {clamped_value, DUVC_CAM_MODE_MANUAL};
                result = duvc_connection_set_camera_property(conn, DUVC_CAM_PROP_ZOOM, &zoom_setting);
                if (result == DUVC_SUCCESS) {
                    printf("Successfully set zoom to %d\n", clamped_value);
                }
            }
        }
        
        // Demonstrate stepping through values
        duvc_prop_setting_t current_zoom;
        result = duvc_connection_get_camera_property(conn, DUVC_CAM_PROP_ZOOM, &current_zoom);
        if (result == DUVC_SUCCESS) {
            printf("Current zoom: %d\n", current_zoom.value);
            
            // Get next valid value up
            int32_t next_value;
            result = duvc_get_next_valid_value(&zoom_range, current_zoom.value, 1, &next_value);
            if (result == DUVC_SUCCESS) {
                printf("Next zoom value would be: %d\n", next_value);
            } else if (result == DUVC_ERROR_INVALID_VALUE) {
                printf("Already at maximum zoom\n");
            }
        }
    }
    
    duvc_close_connection(conn);
}

int main() {
    duvc_initialize();
    
    duvc_device_t** devices;
    size_t count;
    if (duvc_list_devices(&devices, &count) == DUVC_SUCCESS && count > 0) {
        safe_property_setting(devices[^0]);
        duvc_free_device_list(devices, count);
    }
    
    duvc_shutdown();
    return 0;
}
```