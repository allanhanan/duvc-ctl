# duvc-ctl C++ Documentation

## Table of Contents

- [C++ API Overview](#c-api-overview)
    - [Core Concepts](#core-concepts)
    - [Quick Start](#quick-start)
    - [Library Structure](#library-structure)
    - [Build Requirements](#build-requirements)
    - [Threading Model](#threading-model)
    - [Error Handling](#error-handling)
    - [Performance Considerations](#performance-considerations)
- [C++ API Classes \& Functions](#c-api-classes--functions)
    - [Core Types](#core-types)
    - [Property Enumerations](#property-enumerations)
    - [Core Functions](#core-functions)
    - [High-Performance Classes](#high-performance-classes)
    - [Vendor Extensions](#vendor-extensions)
    - [Utility Functions](#utility-functions)
    - [Result<T> Type](#resultt-type)
    - [Platform Interfaces](#platform-interfaces)
    - [Thread Safety](#thread-safety)
    - [Memory Management](#memory-management)
- [C++ API Examples](#c-api-examples)
    - [Basic Device Control](#basic-device-control)
    - [Advanced Property Control](#advanced-property-control)
    - [High-Performance Connection Management](#high-performance-connection-management)
    - [Vendor-Specific Extensions](#vendor-specific-extensions)
    - [Error Handling and Logging](#error-handling-and-logging)
    - [Building the Examples](#building-the-examples)

***

## C++ API Overview

duvc-ctl is a Windows-exclusive C++17 library for controlling UVC (USB Video Class) cameras through the DirectShow API. It provides comprehensive access to camera properties with high performance and thread safety.

### Core Concepts

#### Device Management

- **Device Discovery**: Enumerate connected UVC cameras through DirectShow
- **Connection Pooling**: Efficient device connection management with automatic caching
- **Hot-plug Detection**: Real-time device change notifications via Windows APIs


#### Property Control

- **Camera Control Properties**: 24 properties including Pan, Tilt, Zoom, Focus, Exposure
- **Video Processing Properties**: 10 properties including Brightness, Contrast, White Balance
- **Vendor-specific Properties**: Extended functionality through IKsPropertySet interface


#### Architecture Highlights

- Modern C++17 with RAII patterns and move semantics
- Thread-safe operations across all interfaces
- Comprehensive error handling with detailed HRESULT reporting
- Modular design with clear separation of concerns


### Quick Start

#### Basic Usage

```cpp
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/core/types.h>
#include <duvc-ctl/utils/string_conversion.h>
#include <iostream>

int main() {
    try {
        // List available devices
        auto devices = duvc::list_devices();
        if (devices.empty()) {
            std::cout << "No cameras found\n";
            return 1;
        }
        
        // Use first device
        auto& device = devices[^0];
        std::wcout << L"Using device: " << device.name << L"\n";
        
        // Get current brightness
        duvc::PropSetting brightness;
        if (duvc::get(device, duvc::VidProp::Brightness, brightness)) {
            std::cout << "Current brightness: " << brightness.value 
                     << " (mode: " << duvc::to_string(brightness.mode) << ")\n";
        }
        
        // Set brightness to manual mode
        duvc::PropSetting newBrightness{128, duvc::CamMode::Manual};
        if (duvc::set(device, duvc::VidProp::Brightness, newBrightness)) {
            std::cout << "Brightness set successfully\n";
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    
    return 0;
}
```


### Library Structure

#### Core Headers

| Header | Purpose |
| :-- | :-- |
| `core/device.h` | Device enumeration and management |
| `core/types.h` | Fundamental types and enums |
| `core/connection_pool.h` | High-performance connection management |
| `vendors/logitech.h` | Logitech-specific camera extensions |
| `vendors/constants.h` | Vendor property definitions |
| `utils/logging.h` | Structured logging interface |
| `utils/error_decoder.h` | HRESULT error diagnostics |
| `utils/string_conversion.h` | Enum to string utilities |
| `platform/ks_properties.h` | Low-level vendor property access |

#### Legacy Compatibility

The library maintains backward compatibility:

```cpp
// Legacy (still supported)
#include <duvc-ctl/core.h>
#include <duvc-ctl/defs.h>

// New (recommended)
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/core/types.h>
```


### Build Requirements

- **Platform**: Windows only (DirectShow dependency)
- **Compiler**: MSVC 2019+ or GCC 8+ with Windows SDK
- **CMake**: 3.16 or later
- **C++ Standard**: C++17 or later
- **Dependencies**: Windows SDK, DirectShow libraries (ole32, oleaut32, strmiids)


### Threading Model

The library is designed for multi-threaded environments:

- **Thread-safe**: All public APIs can be called from multiple threads
- **Connection Pooling**: Automatic per-thread COM apartment management
- **No Global State**: Each device connection is independent
- **RAII**: Automatic resource cleanup ensures no leaks


### Error Handling

All operations use comprehensive error handling:

```cpp
// Basic boolean return for success/failure
if (!duvc::get(device, prop, value)) {
    // Handle error - check logs for details
}

// Advanced error handling with Result<T> types (vendor extensions)
auto result = duvc::logitech::get_logitech_property_typed<uint32_t>(device, prop);
if (result.is_ok()) {
    uint32_t value = result.value();
} else {
    std::cout << "Error: " << result.error().message << "\n";
}
```


### Performance Considerations

- **Connection Caching**: Device connections are cached automatically for performance
- **Bulk Operations**: Use `DeviceConnection` directly for multiple operations
- **Memory Management**: RAII ensures proper resource cleanup
- **COM Optimization**: Efficient DirectShow interface management

***

## C++ API Classes \& Functions

Complete reference for all classes, functions, and types in duvc-ctl.

### Core Types

#### Device Structure

```cpp
struct Device {
    std::wstring name;    // Human-readable device name from DirectShow
    std::wstring path;    // Unique device path for identification
};
```

Represents a UVC camera device. The `path` field is the primary identifier used for device binding, while `name` provides user-friendly identification.

#### Property Management

```cpp
struct PropSetting {
    int value;           // Property value within valid range
    CamMode mode;        // Control mode (Auto/Manual)
};

struct PropRange {
    int min, max, step;  // Valid value constraints  
    int default_val;     // Factory default value
    CamMode default_mode; // Default control mode
};

enum class CamMode {
    Auto = 1,           // Camera automatically adjusts property
    Manual = 2          // User has direct control
};
```


### Property Enumerations

#### Camera Control Properties

```cpp
enum class CamProp {
    // Basic PTZ controls
    Pan, Tilt, Roll, Zoom,
    
    // Image control
    Exposure, Iris, Focus,
    
    // Advanced features
    ScanMode, Privacy,
    
    // Relative controls (delta adjustments)
    PanRelative, TiltRelative, RollRelative, ZoomRelative,
    ExposureRelative, IrisRelative, FocusRelative,
    
    // Composite controls
    PanTilt, PanTiltRelative,
    
    // Specialized controls
    FocusSimple, DigitalZoom, DigitalZoomRelative,
    BacklightCompensation, Lamp
};
```


#### Video Processing Properties

```cpp
enum class VidProp {
    Brightness,              // Image brightness adjustment
    Contrast,                // Image contrast adjustment
    Hue,                     // Color hue adjustment
    Saturation,              // Color saturation adjustment
    Sharpness,               // Image sharpness
    Gamma,                   // Gamma correction
    ColorEnable,             // Color enable/disable
    WhiteBalance,            // White balance adjustment
    BacklightCompensation,   // Backlight compensation
    Gain                     // Signal gain adjustment
};
```


### Core Functions

#### Device Management

##### duvc::list_devices()

```cpp
std::vector<Device> list_devices();
```

**Returns**: Vector of all connected UVC devices
**Throws**: `std::runtime_error` on DirectShow enumeration failure

**Example**:

```cpp
auto devices = duvc::list_devices();
for (const auto& dev : devices) {
    std::wcout << L"Device: " << dev.name << L"\n";
}
```


##### duvc::is_device_connected()

```cpp
bool is_device_connected(const Device& device);
```

**Parameters**:

- `device`: Device to check for connectivity

**Returns**: `true` if device is connected and accessible

##### duvc::clear_connection_cache()

```cpp
void clear_connection_cache();
```

Clears all cached device connections. Use when devices have been physically disconnected.

#### Property Operations

##### duvc::get() - Camera Properties

```cpp
bool get(const Device& device, CamProp property, PropSetting& setting);
```

**Parameters**:

- `device`: Target camera device
- `property`: Camera property to retrieve
- `setting`: Output parameter for current property value and mode

**Returns**: `true` if property was successfully retrieved

##### duvc::get() - Video Properties

```cpp
bool get(const Device& device, VidProp property, PropSetting& setting);
```

Same interface as camera properties, but for video processing controls.

##### duvc::set() - Camera Properties

```cpp
bool set(const Device& device, CamProp property, const PropSetting& setting);
```

**Parameters**:

- `device`: Target camera device
- `property`: Camera property to modify
- `setting`: New property value and control mode

**Returns**: `true` if property was successfully set

##### duvc::set() - Video Properties

```cpp
bool set(const Device& device, VidProp property, const PropSetting& setting);
```

Same interface as camera properties, but for video processing controls.

##### duvc::get_range() - Property Ranges

```cpp
bool get_range(const Device& device, CamProp property, PropRange& range);
bool get_range(const Device& device, VidProp property, PropRange& range);
```

**Parameters**:

- `device`: Target camera device
- `property`: Property to query range for
- `range`: Output parameter for property constraints

**Returns**: `true` if range information was retrieved

### High-Performance Classes

#### DeviceConnection Class

For scenarios with multiple property operations on the same device:

```cpp
class DeviceConnection {
public:
    explicit DeviceConnection(const Device& device);
    ~DeviceConnection();
    
    // Non-copyable, movable
    DeviceConnection(DeviceConnection&&) = default;
    DeviceConnection& operator=(DeviceConnection&&) = default;
    
    // Property operations (same interface as global functions)
    bool get(CamProp prop, PropSetting& val);
    bool set(CamProp prop, const PropSetting& val);
    bool get(VidProp prop, PropSetting& val);
    bool set(VidProp prop, const PropSetting& val);
    bool get_range(CamProp prop, PropRange& range);
    bool get_range(VidProp prop, PropRange& range);
    
    bool is_valid() const;
};
```

**Usage**:

```cpp
DeviceConnection conn(device);
if (!conn.is_valid()) {
    // Handle connection failure
    return;
}

// Multiple operations without re-connecting
PropSetting brightness, contrast;
conn.get(VidProp::Brightness, brightness);
conn.get(VidProp::Contrast, contrast);
```


### Vendor Extensions

#### Logitech Support

```cpp
namespace duvc::logitech {
    enum class LogitechProperty : uint32_t {
        RightLight = 1,        // RightLight auto-exposure
        RightSound = 2,        // RightSound audio processing
        FaceTracking = 3,      // Face tracking enable/disable
        LedIndicator = 4,      // LED indicator control
        ProcessorUsage = 5,    // Processor usage optimization
        RawDataBits = 6,       // Raw data bit depth
        FocusAssist = 7,       // Focus assist beam
        VideoStandard = 8,     // Video standard selection
        DigitalZoomROI = 9,    // Digital zoom region of interest
        TiltPan = 10          // Combined tilt/pan control
    };
    
    // Property operations with Result<T> error handling
    Result<std::vector<uint8_t>> get_logitech_property(
        const Device& device, LogitechProperty prop);
        
    Result<void> set_logitech_property(
        const Device& device, LogitechProperty prop, 
        const std::vector<uint8_t>& data);
        
    Result<bool> supports_logitech_properties(const Device& device);
    
    // Typed property operations
    template<typename T>
    Result<T> get_logitech_property_typed(
        const Device& device, LogitechProperty prop);
        
    template<typename T>
    Result<void> set_logitech_property_typed(
        const Device& device, LogitechProperty prop, const T& value);
}
```


#### KsPropertySet Class

For advanced vendor property access:

```cpp
class KsPropertySet {
public:
    explicit KsPropertySet(const Device& device);
    
    bool is_valid() const;
    
    Result<uint32_t> query_support(const GUID& property_set, uint32_t property_id);
    Result<std::vector<uint8_t>> get_property(const GUID& property_set, uint32_t property_id);
    Result<void> set_property(const GUID& property_set, uint32_t property_id, 
                             const std::vector<uint8_t>& data);
    
    template<typename T>
    Result<T> get_property_typed(const GUID& property_set, uint32_t property_id);
    
    template<typename T>
    Result<void> set_property_typed(const GUID& property_set, uint32_t property_id, 
                                   const T& value);
};
```


#### Vendor Property Utilities

```cpp
namespace duvc {
    // Generic vendor property access
    bool get_vendor_property(const Device& dev, const GUID& property_set, 
                            ULONG property_id, std::vector<uint8_t>& data);
                            
    bool set_vendor_property(const Device& dev, const GUID& property_set, 
                            ULONG property_id, const std::vector<uint8_t>& data);
                            
    bool query_vendor_property_support(const Device& dev, const GUID& property_set, 
                                      ULONG property_id);
}
```


### Utility Functions

#### String Conversion

```cpp
namespace duvc {
    // Convert enums to strings
    const char* to_string(CamProp prop);
    const char* to_string(VidProp prop);
    const char* to_string(CamMode mode);
    
    // Convert enums to wide strings
    const wchar_t* to_wstring(CamProp prop);
    const wchar_t* to_wstring(VidProp prop);
    const wchar_t* to_wstring(CamMode mode);
}
```


#### Logging Interface

```cpp
namespace duvc {
    enum class LogLevel {
        Debug = 0, Info = 1, Warning = 2, Error = 3, Critical = 4
    };
    
    using LogCallback = std::function<void(LogLevel, const std::string&)>;
    
    void set_log_callback(LogCallback callback);
    void set_log_level(LogLevel level);
    LogLevel get_log_level();
    
    // Logging functions
    void log_debug(const std::string& message);
    void log_info(const std::string& message);
    void log_warning(const std::string& message);
    void log_error(const std::string& message);
    void log_critical(const std::string& message);
    
    // Convert log level to string
    const char* to_string(LogLevel level);
}
```


#### Error Handling

```cpp
namespace duvc {
    // System error decoding
    std::string decode_system_error(unsigned long error_code);
    std::string decode_hresult(HRESULT hr);
    std::string get_hresult_details(HRESULT hr);
    
    // Error classification
    bool is_device_error(HRESULT hr);
    bool is_permission_error(HRESULT hr);
    
    // Diagnostics
    std::string get_diagnostic_info();
}
```


### Result<T> Type

For advanced error handling in vendor extensions:

```cpp
template<typename T>
class Result {
public:
    bool is_ok() const;
    bool is_err() const;
    
    const T& value() const;          // Only valid if is_ok()
    const Error& error() const;      // Only valid if is_err()
};

enum class ErrorCode {
    Success,
    PropertyNotSupported,
    DeviceNotFound,
    SystemError,
    InvalidValue,
    PermissionDenied
};
```


### Platform Interfaces

#### Abstract Interfaces

```cpp
class IPlatformInterface {
public:
    virtual ~IPlatformInterface() = default;
    virtual Result<std::vector<Device>> list_devices() = 0;
    virtual Result<bool> is_device_connected(const Device& device) = 0;
    virtual Result<std::unique_ptr<IDeviceConnection>> create_connection(const Device& device) = 0;
};

class IDeviceConnection {
public:
    virtual ~IDeviceConnection() = default;
    virtual bool is_valid() const = 0;
    virtual Result<PropSetting> get_camera_property(CamProp prop) = 0;
    virtual Result<void> set_camera_property(CamProp prop, const PropSetting& setting) = 0;
    virtual Result<PropRange> get_camera_property_range(CamProp prop) = 0;
    virtual Result<PropSetting> get_video_property(VidProp prop) = 0;
    virtual Result<void> set_video_property(VidProp prop, const PropSetting& setting) = 0;
    virtual Result<PropRange> get_video_property_range(VidProp prop) = 0;
};

std::unique_ptr<IPlatformInterface> create_platform_interface();
```


### Thread Safety

All public APIs are thread-safe:

- Global functions can be called from any thread simultaneously
- `DeviceConnection` objects are not thread-safe individually but multiple instances can be used concurrently
- COM apartment management is handled automatically per thread
- Connection pooling uses internal synchronization


### Memory Management

The library uses RAII throughout:

- All COM interfaces are managed automatically via smart pointers
- Device connections are cached and cleaned up automatically
- No manual resource management required in user code
- Move semantics used for efficient resource transfers

***

## C++ API Examples

Complete sample programs demonstrating various aspects of the duvc-ctl library.

### Basic Device Control

#### Example 1: List and Display Device Information

```cpp
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/core/types.h>
#include <duvc-ctl/utils/string_conversion.h>
#include <iostream>

int main() {
    try {
        // Enumerate all connected UVC devices
        auto devices = duvc::list_devices();
        
        if (devices.empty()) {
            std::cout << "No UVC cameras found.\n";
            return 1;
        }
        
        std::cout << "Found " << devices.size() << " camera(s):\n\n";
        
        for (size_t i = 0; i < devices.size(); ++i) {
            const auto& device = devices[i];
            
            std::wcout << L"Device " << (i + 1) << L":\n";
            std::wcout << L"  Name: " << device.name << L"\n";
            std::wcout << L"  Path: " << device.path << L"\n";
            std::wcout << L"  Connected: " << (duvc::is_device_connected(device) ? L"Yes" : L"No") << L"\n\n";
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    
    return 0;
}
```


#### Example 2: Basic Property Control

```cpp
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/core/types.h>
#include <duvc-ctl/utils/string_conversion.h>
#include <iostream>

void demonstrate_brightness_control(const duvc::Device& device) {
    std::wcout << L"\n=== Brightness Control Demo ===\n";
    std::wcout << L"Device: " << device.name << L"\n\n";
    
    // Get current brightness setting
    duvc::PropSetting current_brightness;
    if (!duvc::get(device, duvc::VidProp::Brightness, current_brightness)) {
        std::cout << "Failed to get brightness property\n";
        return;
    }
    
    std::cout << "Current brightness: " << current_brightness.value 
              << " (mode: " << duvc::to_string(current_brightness.mode) << ")\n";
    
    // Get brightness range
    duvc::PropRange brightness_range;
    if (duvc::get_range(device, duvc::VidProp::Brightness, brightness_range)) {
        std::cout << "Brightness range: " << brightness_range.min 
                  << " to " << brightness_range.max 
                  << " (step: " << brightness_range.step << ")\n";
        std::cout << "Default: " << brightness_range.default_val 
                  << " (mode: " << duvc::to_string(brightness_range.default_mode) << ")\n";
    }
    
    // Set brightness to 75% of maximum (manual mode)
    int target_brightness = brightness_range.min + 
        static_cast<int>(0.75 * (brightness_range.max - brightness_range.min));
    
    duvc::PropSetting new_brightness{target_brightness, duvc::CamMode::Manual};
    
    if (duvc::set(device, duvc::VidProp::Brightness, new_brightness)) {
        std::cout << "Successfully set brightness to " << target_brightness << "\n";
        
        // Verify the change
        duvc::PropSetting verified_brightness;
        if (duvc::get(device, duvc::VidProp::Brightness, verified_brightness)) {
            std::cout << "Verified brightness: " << verified_brightness.value << "\n";
        }
    } else {
        std::cout << "Failed to set brightness\n";
    }
    
    // Restore original brightness
    if (duvc::set(device, duvc::VidProp::Brightness, current_brightness)) {
        std::cout << "Restored original brightness\n";
    }
}

int main() {
    try {
        auto devices = duvc::list_devices();
        if (devices.empty()) {
            std::cout << "No cameras found\n";
            return 1;
        }
        
        demonstrate_brightness_control(devices[^0]);
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    
    return 0;
}
```


### Advanced Property Control

#### Example 3: Complete Camera Property Survey

```cpp
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/core/types.h>
#include <duvc-ctl/utils/string_conversion.h>
#include <iostream>
#include <iomanip>

void survey_camera_properties(const duvc::Device& device) {
    std::wcout << L"\n=== Camera Properties Survey ===\n";
    std::wcout << L"Device: " << device.name << L"\n\n";
    
    // List of camera properties to check
    duvc::CamProp camera_props[] = {
        duvc::CamProp::Pan, duvc::CamProp::Tilt, duvc::CamProp::Roll, 
        duvc::CamProp::Zoom, duvc::CamProp::Exposure, duvc::CamProp::Iris,
        duvc::CamProp::Focus, duvc::CamProp::BacklightCompensation
    };
    
    std::cout << std::left;
    std::cout << std::setw(20) << "Property" 
              << std::setw(10) << "Current" 
              << std::setw(8) << "Mode"
              << std::setw(8) << "Min" 
              << std::setw(8) << "Max" 
              << std::setw(8) << "Step" 
              << std::setw(10) << "Default\n";
    std::cout << std::string(70, '-') << "\n";
    
    for (auto prop : camera_props) {
        const char* prop_name = duvc::to_string(prop);
        
        // Try to get current value
        duvc::PropSetting current;
        bool has_current = duvc::get(device, prop, current);
        
        // Try to get range
        duvc::PropRange range;
        bool has_range = duvc::get_range(device, prop, range);
        
        std::cout << std::setw(20) << prop_name;
        
        if (has_current) {
            std::cout << std::setw(10) << current.value
                      << std::setw(8) << (current.mode == duvc::CamMode::Auto ? "AUTO" : "MANUAL");
        } else {
            std::cout << std::setw(18) << "N/A";
        }
        
        if (has_range) {
            std::cout << std::setw(8) << range.min
                      << std::setw(8) << range.max
                      << std::setw(8) << range.step
                      << std::setw(10) << range.default_val;
        } else {
            std::cout << std::setw(34) << "N/A";
        }
        
        std::cout << "\n";
    }
}

void survey_video_properties(const duvc::Device& device) {
    std::wcout << L"\n=== Video Properties Survey ===\n";
    
    duvc::VidProp video_props[] = {
        duvc::VidProp::Brightness, duvc::VidProp::Contrast, duvc::VidProp::Hue,
        duvc::VidProp::Saturation, duvc::VidProp::Sharpness, duvc::VidProp::Gamma,
        duvc::VidProp::WhiteBalance, duvc::VidProp::Gain
    };
    
    std::cout << std::left;
    std::cout << std::setw(20) << "Property" 
              << std::setw(10) << "Current" 
              << std::setw(8) << "Mode"
              << std::setw(8) << "Min" 
              << std::setw(8) << "Max" 
              << std::setw(8) << "Step" 
              << std::setw(10) << "Default\n";
    std::cout << std::string(70, '-') << "\n";
    
    for (auto prop : video_props) {
        const char* prop_name = duvc::to_string(prop);
        
        duvc::PropSetting current;
        bool has_current = duvc::get(device, prop, current);
        
        duvc::PropRange range;
        bool has_range = duvc::get_range(device, prop, range);
        
        std::cout << std::setw(20) << prop_name;
        
        if (has_current) {
            std::cout << std::setw(10) << current.value
                      << std::setw(8) << (current.mode == duvc::CamMode::Auto ? "AUTO" : "MANUAL");
        } else {
            std::cout << std::setw(18) << "N/A";
        }
        
        if (has_range) {
            std::cout << std::setw(8) << range.min
                      << std::setw(8) << range.max
                      << std::setw(8) << range.step
                      << std::setw(10) << range.default_val;
        }
        
        std::cout << "\n";
    }
}

int main() {
    try {
        auto devices = duvc::list_devices();
        if (devices.empty()) {
            std::cout << "No cameras found\n";
            return 1;
        }
        
        for (const auto& device : devices) {
            survey_camera_properties(device);
            survey_video_properties(device);
            std::cout << "\n" << std::string(80, '=') << "\n";
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    
    return 0;
}
```


### High-Performance Connection Management

#### Example 4: Bulk Property Operations with DeviceConnection

```cpp
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/core/connection_pool.h>
#include <duvc-ctl/utils/string_conversion.h>
#include <iostream>
#include <chrono>

void demonstrate_connection_performance(const duvc::Device& device) {
    std::wcout << L"\n=== Connection Performance Demo ===\n";
    std::wcout << L"Device: " << device.name << L"\n\n";
    
    const int num_operations = 50;
    
    // Method 1: Using global functions (creates connection each time)
    auto start = std::chrono::high_resolution_clock::now();
    
    for (int i = 0; i < num_operations; ++i) {
        duvc::PropSetting brightness;
        duvc::get(device, duvc::VidProp::Brightness, brightness);
        
        duvc::PropSetting contrast;
        duvc::get(device, duvc::VidProp::Contrast, contrast);
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration1 = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    std::cout << "Global functions (" << num_operations << " iterations): " 
              << duration1.count() << " ms\n";
    
    // Method 2: Using DeviceConnection (reuses connection)
    start = std::chrono::high_resolution_clock::now();
    
    {
        duvc::DeviceConnection conn(device);
        if (!conn.is_valid()) {
            std::cout << "Failed to create device connection\n";
            return;
        }
        
        for (int i = 0; i < num_operations; ++i) {
            duvc::PropSetting brightness;
            conn.get(duvc::VidProp::Brightness, brightness);
            
            duvc::PropSetting contrast;
            conn.get(duvc::VidProp::Contrast, contrast);
        }
    }
    
    end = std::chrono::high_resolution_clock::now();
    auto duration2 = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    
    std::cout << "DeviceConnection (" << num_operations << " iterations): " 
              << duration2.count() << " ms\n";
    
    if (duration1.count() > 0) {
        double speedup = static_cast<double>(duration1.count()) / duration2.count();
        std::cout << "Speedup: " << std::fixed << std::setprecision(1) << speedup << "x\n";
    }
}

void batch_property_update(const duvc::Device& device) {
    std::wcout << L"\n=== Batch Property Update ===\n";
    
    duvc::DeviceConnection conn(device);
    if (!conn.is_valid()) {
        std::cout << "Failed to create device connection\n";
        return;
    }
    
    // Save current settings
    std::cout << "Saving current settings...\n";
    duvc::PropSetting original_brightness, original_contrast, original_saturation;
    
    bool has_brightness = conn.get(duvc::VidProp::Brightness, original_brightness);
    bool has_contrast = conn.get(duvc::VidProp::Contrast, original_contrast);
    bool has_saturation = conn.get(duvc::VidProp::Saturation, original_saturation);
    
    // Apply new settings batch
    std::cout << "Applying new settings...\n";
    
    if (has_brightness) {
        duvc::PropSetting new_brightness{original_brightness.value + 10, duvc::CamMode::Manual};
        conn.set(duvc::VidProp::Brightness, new_brightness);
    }
    
    if (has_contrast) {
        duvc::PropSetting new_contrast{original_contrast.value + 5, duvc::CamMode::Manual};
        conn.set(duvc::VidProp::Contrast, new_contrast);
    }
    
    if (has_saturation) {
        duvc::PropSetting new_saturation{original_saturation.value - 5, duvc::CamMode::Manual};
        conn.set(duvc::VidProp::Saturation, new_saturation);
    }
    
    std::cout << "Settings applied. Press Enter to restore original values...";
    std::cin.get();
    
    // Restore original settings
    std::cout << "Restoring original settings...\n";
    
    if (has_brightness) conn.set(duvc::VidProp::Brightness, original_brightness);
    if (has_contrast) conn.set(duvc::VidProp::Contrast, original_contrast);
    if (has_saturation) conn.set(duvc::VidProp::Saturation, original_saturation);
    
    std::cout << "Original settings restored.\n";
}

int main() {
    try {
        auto devices = duvc::list_devices();
        if (devices.empty()) {
            std::cout << "No cameras found\n";
            return 1;
        }
        
        demonstrate_connection_performance(devices[^0]);
        batch_property_update(devices[^0]);
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    
    return 0;
}
```


### Vendor-Specific Extensions

#### Example 5: Logitech Camera Control

```cpp
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/vendors/logitech.h>
#include <duvc-ctl/utils/string_conversion.h>
#include <iostream>

void demonstrate_logitech_features(const duvc::Device& device) {
    std::wcout << L"\n=== Logitech Features Demo ===\n";
    std::wcout << L"Device: " << device.name << L"\n\n";
    
    // Check if device supports Logitech extensions
    auto support_result = duvc::logitech::supports_logitech_properties(device);
    if (!support_result.is_ok() || !support_result.value()) {
        std::cout << "Device does not support Logitech vendor extensions\n";
        return;
    }
    
    std::cout << "Device supports Logitech vendor extensions!\n\n";
    
    // Try to get RightLight setting
    auto rightlight_result = duvc::logitech::get_logitech_property_typed<uint32_t>(
        device, duvc::logitech::LogitechProperty::RightLight);
    
    if (rightlight_result.is_ok()) {
        uint32_t rightlight_value = rightlight_result.value();
        std::cout << "RightLight current value: " << rightlight_value << "\n";
        
        // Toggle RightLight
        uint32_t new_value = rightlight_value ? 0 : 1;
        auto set_result = duvc::logitech::set_logitech_property_typed<uint32_t>(
            device, duvc::logitech::LogitechProperty::RightLight, new_value);
            
        if (set_result.is_ok()) {
            std::cout << "RightLight toggled to: " << new_value << "\n";
            
            // Restore original value
            duvc::logitech::set_logitech_property_typed<uint32_t>(
                device, duvc::logitech::LogitechProperty::RightLight, rightlight_value);
            std::cout << "RightLight restored to original value\n";
        } else {
            std::cout << "Failed to set RightLight: " << set_result.error().message << "\n";
        }
    } else {
        std::cout << "Failed to get RightLight: " << rightlight_result.error().message << "\n";
    }
    
    // Try LED indicator control
    auto led_result = duvc::logitech::get_logitech_property_typed<uint32_t>(
        device, duvc::logitech::LogitechProperty::LedIndicator);
        
    if (led_result.is_ok()) {
        std::cout << "LED Indicator current value: " << led_result.value() << "\n";
    } else {
        std::cout << "LED Indicator not supported or failed to read\n";
    }
}

int main() {
    try {
        auto devices = duvc::list_devices();
        if (devices.empty()) {
            std::cout << "No cameras found\n";
            return 1;
        }
        
        // Try each device for Logitech features
        for (const auto& device : devices) {
            demonstrate_logitech_features(device);
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << "\n";
        return 1;
    }
    
    return 0;
}
```


### Error Handling and Logging

#### Example 6: Comprehensive Error Handling

```cpp
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/utils/logging.h>
#include <duvc-ctl/utils/error_decoder.h>
#include <iostream>

void setup_logging() {
    // Set up custom logging callback
    duvc::set_log_callback([](duvc::LogLevel level, const std::string& message) {
        const char* level_str = duvc::to_string(level);
        std::cout << "[" << level_str << "] " << message << "\n";
    });
    
    // Set log level to show all messages
    duvc::set_log_level(duvc::LogLevel::Debug);
}

void safe_property_operation(const duvc::Device& device) {
    std::wcout << L"\n=== Safe Property Operations ===\n";
    std::wcout << L"Device: " << device.name << L"\n\n";
    
    // Always check device connectivity first
    if (!duvc::is_device_connected(device)) {
        duvc::log_error("Device is not connected");
        return;
    }
    
    duvc::log_info("Device is connected, proceeding with operations");
    
    // Get property with error checking
    duvc::PropSetting exposure;
    if (duvc::get(device, duvc::CamProp::Exposure, exposure)) {
        duvc::log_info("Successfully retrieved exposure: " + std::to_string(exposure.value));
        
        // Check if we can get the range (property might be read-only)
        duvc::PropRange exposure_range;
        if (duvc::get_range(device, duvc::CamProp::Exposure, exposure_range)) {
            duvc::log_info("Exposure range: " + std::to_string(exposure_range.min) + 
                          " to " + std::to_string(exposure_range.max));
            
            // Validate current value is within range
            if (exposure.value < exposure_range.min || exposure.value > exposure_range.max) {
                duvc::log_warning("Current exposure value is outside reported range!");
            }
            
            // Try to set a safe value (within range)
            int safe_value = std::max(exposure_range.min, 
                            std::min(exposure_range.max, exposure.value));
            
            duvc::PropSetting new_exposure{safe_value, duvc::CamMode::Manual};
            
            if (duvc::set(device, duvc::CamProp::Exposure, new_exposure)) {
                duvc::log_info("Successfully set exposure to " + std::to_string(safe_value));
                
                // Verify the setting took effect
                duvc::PropSetting verified;
                if (duvc::get(device, duvc::CamProp::Exposure, verified)) {
                    if (verified.value == safe_value) {
                        duvc::log_info("Exposure setting verified successfully");
                    } else {
                        duvc::log_warning("Exposure value differs from set value: " + 
                                        std::to_string(verified.value));
                    }
                }
                
                // Restore original setting
                if (duvc::set(device, duvc::CamProp::Exposure, exposure)) {
                    duvc::log_info("Original exposure restored");
                } else {
                    duvc::log_error("Failed to restore original exposure");
                }
            } else {
                duvc::log_error("Failed to set exposure property");
            }
        } else {
            duvc::log_warning("Could not retrieve exposure range - property may be read-only");
        }
    } else {
        duvc::log_error("Failed to get exposure property - not supported on this device");
    }
}

void demonstrate_diagnostics() {
    std::cout << "\n=== System Diagnostics ===\n";
    
    // Get diagnostic information
    std::string diag_info = duvc::get_diagnostic_info();
    std::cout << "Diagnostic Info:\n" << diag_info << "\n";
    
    // Demonstrate error decoding (simulate some HRESULTs)
    HRESULT test_results[] = {
        S_OK,
        E_INVALIDARG,
        E_NOTIMPL,
        E_ACCESSDENIED,
        0x80070002  // ERROR_FILE_NOT_FOUND
    };
    
    std::cout << "\nError Code Decoding:\n";
    for (HRESULT hr : test_results) {
        std::cout << "HRESULT 0x" << std::hex << hr << ": " 
                  << duvc::decode_hresult(hr) << "\n";
        
        if (duvc::is_device_error(hr)) {
            std::cout << "  -> This is a device-related error\n";
        }
        
        if (duvc::is_permission_error(hr)) {
            std::cout << "  -> This is a permission error\n";
        }
    }
}

int main() {
    try {
        setup_logging();
        
        duvc::log_info("Starting duvc-ctl error handling demo");
        
        auto devices = duvc::list_devices();
        if (devices.empty()) {
            duvc::log_warning("No cameras found");
            return 1;
        }
        
        duvc::log_info("Found " + std::to_string(devices.size()) + " device(s)");
        
        for (const auto& device : devices) {
            safe_property_operation(device);
        }
        
        demonstrate_diagnostics();
        
        duvc::log_info("Demo completed successfully");
        
    } catch (const std::exception& e) {
        duvc::log_critical("Unhandled exception: " + std::string(e.what()));
        return 1;
    }
    
    return 0;
}
```


### Building the Examples

#### CMakeLists.txt for Examples

```cmake
cmake_minimum_required(VERSION 3.16)
project(DuvcExamples)

find_package(duvc-ctl REQUIRED)

# Example executables
add_executable(list_devices example1_list_devices.cpp)
target_link_libraries(list_devices duvc::duvc)

add_executable(property_control example2_property_control.cpp)
target_link_libraries(property_control duvc::duvc)

add_executable(property_survey example3_property_survey.cpp)
target_link_libraries(property_survey duvc::duvc)

add_executable(performance_demo example4_performance.cpp)
target_link_libraries(performance_demo duvc::duvc)

add_executable(logitech_demo example5_logitech.cpp)
target_link_libraries(logitech_demo duvc::duvc)

add_executable(error_handling example6_error_handling.cpp)
target_link_libraries(error_handling duvc::duvc)
```


#### Compilation Commands

```bash
# Configure and build examples
mkdir build && cd build
cmake .. -DCMAKE_PREFIX_PATH=/path/to/duvc-install
cmake --build . --config Release

# Run examples
./list_devices
./property_control
./property_survey
./performance_demo
./logitech_demo
./error_handling
```


#### Integration Tips

1. **Always check device connectivity** before performing operations
2. **Use DeviceConnection** for multiple operations on the same device
3. **Check property ranges** before setting values
4. **Handle errors gracefully** - not all properties are supported on all devices
5. **Enable logging** during development for better debugging
6. **Clear connection cache** if devices are disconnected/reconnected
7. **Use vendor extensions** only after checking support
8. **Test with multiple camera models** to ensure compatibility
