# duvc-ctl: Windows Camera Control Library

[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](README.md)
[![Language](https://img.shields.io/badge/C%2B%2B-17-blue.svg)](src/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](pyproject.toml)
![Pepy Total Downloads](https://img.shields.io/pepy/dt/duvc-ctl?style=flat&label=pip%20installs)


Windows DirectShow UVC camera control library with C++, Python, and CLI interfaces.&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[<img src="https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png" width="150" alt="Buy Me A Coffee">](https://www.buymeacoffee.com/allanhanan)


## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Build Instructions](#build-instructions)
- [API Reference](#api-reference)
- [Architecture](#architecture)
- [Vendor Extensions](#vendor-extensions)
- [Testing](#testing)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

***

## Overview

duvc-ctl provides direct control over DirectShow API for UVC cameras on Windows. Control PTZ operations, exposure, focus, brightness, and other camera properties without any additional drivers or vendor SDKs

**Key Features:**

**Key Features:**
- UVC camera enumeration and control
- PTZ (Pan/Tilt/Zoom) operations
- Camera properties (exposure, focus, iris)
- Video properties (brightness, contrast, white balance)
- Device monitoring with hotplug detection
- Connection pooling for performance
- C++17, Python, and CLI interfaces

**Supported Camera Operations:**

- PTZ (Pan/Tilt/Zoom) with precise control
- Camera properties (exposure, focus, iris, privacy)
- Video properties (brightness, contrast, white balance, gamma)
- Vendor-specific properties (Logitech RightLight, FaceTracking, etc.)
- Real-time device monitoring and hotplug detection

***

## Installation

### Python Package

```bash
pip install duvc-ctl
```


### Prebuilt Binaries

> **Coming Soon**

```bash
# Chocolatey
choco install duvc-cli
```


### Package Managers

> **In Development**

```bash
# vcpkg
vcpkg install duvc-ctl

# Conan
conan install duvc-ctl/2.0.0@

# conda-forge
conda install -c conda-forge duvc-ctl
```


### Language Bindings

| Language | Package | Status |
| :-- | :-- | :-- |
| **C/C++** | Native | Available |
| **Python** | `pip install duvc-ctl` | Available |
| **Rust** | `cargo add duvc-ctl` | In Development |
| **Go** | `go get github.com/allanhanan/duvc-ctl` | In Development |
| **Node.js** | `npm install duvc-ctl` | In Development |
| **C\#/.NET** | `Install-Package DuvcCtl` | Planned |


***

## Quick Start

<table>
<tr>
<td width="50%">

**C++ Modern API**
```cpp
#include <duvc-ctl/duvc.hpp>

// Initialize library
auto platform = duvc::create_platform_interface();

// List cameras
auto devices_result = platform->list_devices();
if (!devices_result.is_ok()) return;
const auto& devices = devices_result.value();

// Create connection
auto connection_result = platform->create_connection(devices[^0]);
if (!connection_result.is_ok()) return;
auto connection = std::move(connection_result.value());

// Get property range
auto range_result = connection->get_camera_property_range(
    duvc::CamProp::Pan);
if (range_result.is_ok()) {
    const auto& range = range_result.value();
    std::cout << "Pan range: " << range.min 
              << " to " << range.max << std::endl;
}

// Set property
duvc::PropSetting setting{0, duvc::CamMode::Manual};
connection->set_camera_property(duvc::CamProp::Pan, setting);
```

</td>
<td width="50%">

**C API (Stable ABI)**
```c
#include "duvc-ctl/c/api.h"

// Initialize
duvc_initialize();

// List devices
duvc_device_t** devices;
size_t count;
if (duvc_list_devices(&devices, &count) == DUVC_SUCCESS) {
    
    // Get property
    duvc_prop_setting_t setting;
    duvc_get_camera_property(devices[^0], 
        DUVC_CAM_PROP_PAN, &setting);
    
    // Set property
    duvc_prop_setting_t new_setting = {0, DUVC_CAM_MODE_MANUAL};
    duvc_set_camera_property(devices[^0], 
        DUVC_CAM_PROP_PAN, &new_setting);
    
    duvc_free_device_list(devices, count);
}

duvc_shutdown();
```

</td>
</tr>
<tr>
<td width="50%">

**Python Bindings**
```python
import duvc_ctl as duvc

# List cameras
devices = duvc.list_devices()
if not devices:
    return

# Create connection  
with duvc.DeviceConnection(devices[^0]) as conn:
    # Get property range
    range_info = conn.get_camera_property_range(duvc.CamProp.Pan)
    print(f"Pan range: {range_info.min} to {range_info.max}")
    
    # Set property
    setting = duvc.PropSetting(0, duvc.CamMode.Manual)
    conn.set_camera_property(duvc.CamProp.Pan, setting)
    
    # Get current value
    current = conn.get_camera_property(duvc.CamProp.Pan)
    print(f"Current pan: {current.value}")
```

</td>
<td width="50%">

**Command Line Interface**
```bash
# List available cameras
duvc-cli list --detailed

# Get property information
duvc-cli get --device 0 --property pan --camera

# Set property value
duvc-cli set --device 0 --property pan --value 0 --mode manual

# Monitor device changes
duvc-cli monitor --timeout 30 --verbose

# Get property ranges
duvc-cli ranges --device 0 --camera

# Vendor-specific properties
duvc-cli vendor logitech --device 0 --property face-tracking --get
```

</td>
</tr>
</table>

***

## Build Instructions

### Prerequisites

- **Windows 10/11** (Windows 8.1 compatible but not tested)
- **Compiler**: Visual Studio 2019/2022 (preferred) or MinGW-w64 with GCC 9+
- **CMake 3.16+**
- **Python 3.8+** (for Python bindings)
- **Git** (for fetching dependencies)


### Quick Build

```bash
git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl

# Configure with default options
cmake -B build -G "Visual Studio 17 2022" -A x64

# Build all targets
cmake --build build --config Release

# Run tests
cd build && ctest --config Release
```


### Advanced Configuration

```bash
# Full configuration with all options
cmake -B build \
    -G "Visual Studio 17 2022" -A x64 \
    -DDUVC_BUILD_SHARED=ON \
    -DDUVC_BUILD_STATIC=ON \
    -DDUVC_BUILD_C_API=ON \
    -DDUVC_BUILD_CLI=ON \
    -DDUVC_BUILD_PYTHON=ON \
    -DDUVC_BUILD_TESTS=ON \
    -DDUVC_BUILD_EXAMPLES=ON \
    -DDUVC_WARNINGS_AS_ERRORS=OFF \
    -DCMAKE_INSTALL_PREFIX=install

# Build and install
cmake --build build --config Release
cmake --install build --config Release
```


### Build Options Reference

| Option | Default | Description |
| :-- | :--: | :-- |
| `DUVC_BUILD_SHARED` | **ON** | Build shared core library (duvc-core.dll) |
| `DUVC_BUILD_STATIC` | **ON** | Build static core library (duvc-core.lib) |
| `DUVC_BUILD_C_API` | **ON** | Build C API library for language bindings |
| `DUVC_BUILD_CLI` | **ON** | Build command-line interface tool |
| `DUVC_BUILD_PYTHON` | **OFF** | Build Python bindings (requires Python) |
| `DUVC_BUILD_TESTS` | **OFF** | Build comprehensive test suite |
| `DUVC_BUILD_EXAMPLES` | **OFF** | Build example applications |
| `DUVC_WARNINGS_AS_ERRORS` | **OFF** | Treat compiler warnings as errors |
| `DUVC_INSTALL` | **ON** | Enable installation targets |
| `DUVC_INSTALL_CMAKE_CONFIG` | **ON** | Install CMake configuration files |


***

## API Reference

### Core Architecture

The library provides multiple API layers:

```cpp
// Modern C++ API (Recommended)
#include "duvc-ctl/duvc.hpp"
#include "duvc-ctl/platform/interface.h"

// C ABI (Language Bindings)  
#include "duvc-ctl/c/api.h"

// Utilities
#include "duvc-ctl/utils/logging.h"
#include "duvc-ctl/utils/error_decoder.h"

// Vendor Extensions
#include "duvc-ctl/vendor/logitech.h"
```


### Core Types

```cpp
namespace duvc {
    // Device representation
    struct Device {
        std::wstring name;    // Human-readable name
        std::wstring path;    // System device path
        // Equality operators provided
    };
    
    // Property setting
    struct PropSetting {
        int32_t value;        // Property value
        CamMode mode;         // Auto or Manual control
        
        PropSetting() = default;
        PropSetting(int32_t val, CamMode m) : value(val), mode(m) {}
    };
    
    // Property constraints
    struct PropRange {
        int32_t min, max, step;      // Value constraints  
        int32_t default_val;         // Factory default
        CamMode default_mode;        // Default control mode
        
        bool is_valid_value(int32_t val) const;
        int32_t clamp_to_range(int32_t val) const;
    };
    
    // Result type for error handling
    template<typename T>
    class Result {
        bool is_ok() const;
        bool is_error() const;
        const T& value() const;
        const Error& error() const;
        
        static Result ok(T value);
        static Result error(ErrorCode code, std::string description);
    };
}
```


### Camera Properties (IAMCameraControl)

```cpp
enum class CamProp {
    Pan,                    // Horizontal rotation
    Tilt,                   // Vertical rotation  
    Roll,                   // Rotation around optical axis
    Zoom,                   // Optical zoom
    Exposure,               // Exposure time
    Iris,                   // Aperture control
    Focus,                  // Focus distance
    ScanMode,              // Progressive/Interlaced
    Privacy,               // Privacy shutter
    PanRelative,           // Relative pan movement
    TiltRelative,          // Relative tilt movement
    RollRelative,          // Relative roll movement
    ZoomRelative,          // Relative zoom movement
    ExposureRelative,      // Relative exposure adjustment
    IrisRelative,          // Relative iris adjustment
    FocusRelative,         // Relative focus adjustment
    PanTilt,               // Combined pan/tilt
    PanTiltRelative,       // Combined relative pan/tilt
    FocusSimple,           // Simplified focus control
    DigitalZoom,           // Digital zoom factor
    DigitalZoomRelative,   // Relative digital zoom
    BacklightCompensation, // Backlight compensation
    Lamp,                  // Camera lamp/LED
    Brightness             // Camera brightness (alternative path)
};
```


### Video Properties (IAMVideoProcAmp)

```cpp
enum class VidProp {
    Brightness,            // Image brightness
    Contrast,              // Image contrast
    Hue,                   // Color hue
    Saturation,            // Color saturation
    Sharpness,             // Image sharpness
    Gamma,                 // Gamma correction
    ColorEnable,           // Color/monochrome mode
    WhiteBalance,          // White balance
    BacklightCompensation, // Video backlight compensation
    Gain                   // Analog/digital gain
};
```


### Platform Interface

```cpp
class IPlatformInterface {
public:
    virtual Result<std::vector<Device>> list_devices() = 0;
    virtual Result<bool> is_device_connected(const Device& device) = 0;
    virtual Result<std::unique_ptr<IDeviceConnection>> create_connection(const Device& device) = 0;
};

class IDeviceConnection {
public:
    virtual bool is_valid() const = 0;
    virtual Result<PropSetting> get_camera_property(CamProp prop) = 0;
    virtual Result<void> set_camera_property(CamProp prop, const PropSetting& setting) = 0;
    virtual Result<PropRange> get_camera_property_range(CamProp prop) = 0;
    virtual Result<PropSetting> get_video_property(VidProp prop) = 0;
    virtual Result<void> set_video_property(VidProp prop, const PropSetting& setting) = 0;
    virtual Result<PropRange> get_video_property_range(VidProp prop) = 0;
};

// Factory function
std::unique_ptr<IPlatformInterface> create_platform_interface();
```


### Logging and Diagnostics

```cpp
namespace duvc {
    enum class LogLevel { Debug, Info, Warning, Error, Critical };
    
    // Logging configuration
    void set_log_level(LogLevel level);
    void set_log_callback(std::function<void(LogLevel, const std::string&)> callback);
    
    // Logging functions
    void log_debug(const std::string& message);
    void log_info(const std::string& message);  
    void log_warning(const std::string& message);
    void log_error(const std::string& message);
    void log_critical(const std::string& message);
    
    // Diagnostics
    std::string decode_system_error(unsigned long error_code);
    std::string get_diagnostic_info();
    
#ifdef _WIN32
    std::string decode_hresult(HRESULT hr);
    std::string get_hresult_details(HRESULT hr);
    bool is_device_error(HRESULT hr);
    bool is_permission_error(HRESULT hr);
#endif
}
```


***

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Language Bindings                        │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Python API    │    CLI Tool     │   Future Bindings       │
├─────────────────┴─────────────────┴─────────────────────────┤
│                     C API (Stable ABI)                     │
├─────────────────────────────────────────────────────────────┤
│                    C++ Core Library                        │
├─────────────────┬───────────────────┬─────────────────────────┤
│  Platform Impl  │  Vendor Extensions │   Utilities            │
│  - DirectShow   │  - Logitech       │   - Logging            │
│  - Device Mgmt  │  - Future vendors │   - Error Handling     │
│  - Connection   │                   │   - Diagnostics        │
├─────────────────┴───────────────────┴─────────────────────────┤
│                 Windows DirectShow APIs                     │
└─────────────────────────────────────────────────────────────┘
```


### DirectShow Integration

The library integrates deeply with DirectShow APIs:

- **ICreateDevEnum**: Device enumeration and discovery
- **IAMCameraControl**: PTZ and camera-specific properties
- **IAMVideoProcAmp**: Video processing and image properties
- **IKsPropertySet**: Vendor-specific property extensions
- **IBaseFilter**: Device connection and streaming control


### Connection Management

**Connection Pooling**: Automatic caching of DirectShow connections reduces overhead:

```cpp
// First access - creates connection (~50ms)
auto connection1 = platform->create_connection(device);

// Subsequent access - uses cached connection (~1ms)  
auto connection2 = platform->create_connection(device);
```

**Thread Safety**:

- Device enumeration is fully thread-safe
- Multiple devices can be controlled concurrently
- Same device requires external synchronization


### Error Handling Strategy

**Multi-Level Error Information**:

```cpp
// Modern C++ API
auto result = connection->get_camera_property(CamProp::Pan);
if (result.is_error()) {
    const auto& error = result.error();
    std::cout << "Error: " << error.description() << std::endl;
    // Includes detailed HRESULT information on Windows
}

// C API  
duvc_result_t result = duvc_get_camera_property(device, DUVC_CAM_PROP_PAN, &setting);
if (result != DUVC_SUCCESS) {
    char details[^1024];
    size_t needed;
    duvc_get_last_error_details(details, sizeof(details), &needed);
    printf("Error: %s\n", details);
}
```


***

## Vendor Extensions

### Logitech-Specific Properties

duvc-ctl includes comprehensive support for Logitech camera extensions:

```cpp
#include "duvc-ctl/vendor/logitech.h"

namespace duvc::logitech {
    enum class LogitechProperty {
        RightLight,        // Auto-exposure optimization
        RightSound,        // Audio processing  
        FaceTracking,      // Face tracking enable/disable
        LedIndicator,      // LED indicator control
        ProcessorUsage,    // CPU usage optimization
        RawDataBits,       // Raw sensor bit depth
        FocusAssist,       // Focus assist beam
        VideoStandard,     // Video standard selection
        DigitalZoomROI,    // Digital zoom region of interest
        TiltPan            // Combined tilt/pan control
    };
    
    // Check vendor support
    Result<bool> supports_logitech_properties(const Device& device);
    
    // Get/Set vendor properties
    Result<std::vector<uint8_t>> get_logitech_property(const Device& device, LogitechProperty prop);
    Result<void> set_logitech_property(const Device& device, LogitechProperty prop, const std::vector<uint8_t>& data);
    
    // Typed accessors
    template<typename T>
    Result<T> get_logitech_property_typed(const Device& device, LogitechProperty prop);
    template<typename T>  
    Result<void> set_logitech_property_typed(const Device& device, LogitechProperty prop, const T& value);
}

// Usage example
auto supports_result = logitech::supports_logitech_properties(device);
if (supports_result.is_ok() && supports_result.value()) {
    // Enable face tracking
    auto result = logitech::set_logitech_property_typed<bool>(
        device, logitech::LogitechProperty::FaceTracking, true);
}
```


***

## Examples

### Camera Centering

```cpp
// Center PTZ camera
duvc::PropSetting center{0, duvc::CamMode::Manual};
auto pan_result = connection->set_camera_property(duvc::CamProp::Pan, center);
auto tilt_result = connection->set_camera_property(duvc::CamProp::Tilt, center);
```


### Property Validation

```cpp
// Check property range before setting
auto range_result = connection->get_camera_property_range(duvc::CamProp::Zoom);
if (range_result.is_ok()) {
    const auto& range = range_result.value();
    int zoom_value = 50;
    if (range.is_valid_value(zoom_value)) {
        duvc::PropSetting setting{zoom_value, duvc::CamMode::Manual};
        connection->set_camera_property(duvc::CamProp::Zoom, setting);
    }
}
```


### Error Handling with Logging

```cpp
#include "duvc-ctl/utils/logging.h"

// Enable logging
duvc::set_log_level(duvc::LogLevel::Debug);
duvc::set_log_callback([](duvc::LogLevel level, const std::string& msg) {
    std::cout << "[" << duvc::to_string(level) << "] " << msg << std::endl;
});

// Operations will now log detailed information
auto result = connection->get_camera_property(duvc::CamProp::Pan);
if (result.is_error()) {
    duvc::log_error("Failed to get pan: " + result.error().description());
}
```


***

## Testing

### Test Architecture

duvc-ctl includes a comprehensive three-tier test suite:

```
tests/
├── cpp/
│   ├── unit/                    # Component isolation tests
│   │   ├── core_tests.cpp       # Core types and result handling
│   │   ├── platform_tests.cpp   # Platform interface tests
│   │   ├── vendor_tests.cpp     # Vendor extension tests
│   │   └── utils_tests.cpp      # Utility function tests
│   ├── integration/             # Multi-component tests  
│   │   └── device_integration_tests.cpp # Real device interaction
│   └── functional/              # End-to-end workflows
│       └── camera_workflow_tests.cpp   # Complete user scenarios
└── CMakeLists.txt               # Test configuration
```


### Running Tests

**All Tests**:

```bash
cd build
ctest --config Release --output-on-failure
```

**Specific Test Categories**:

```bash
# Unit tests only
ctest --config Release --label-regex "unit"

# Integration tests (requires cameras)
ctest --config Release --label-regex "integration"  

# Functional tests (requires cameras)
ctest --config Release --label-regex "functional"
```


***

## Performance

### Benchmarks

| Operation | Cold Start | Cached | Notes |
| :-- | :-- | :-- | :-- |
| **Device Enumeration** | 50-200ms | 50-200ms | DirectShow limitation |
| **Property Get/Set** | 10-50ms | 1-5ms | Connection pooling benefit |
| **Connection Creation** | 30-100ms | <1ms | 95%+ cache hit rate |
| **Property Range Query** | 5-20ms | <1ms | Cached after first query |

### Threading Performance

```cpp
// Thread-safe device enumeration
std::vector<std::thread> threads;
for (int i = 0; i < 10; ++i) {
    threads.emplace_back([&platform]() {
        auto devices = platform->list_devices();  // Thread-safe
    });
}

// Multiple device control (thread-safe)
auto connection1 = platform->create_connection(device1);  // Thread-safe
auto connection2 = platform->create_connection(device2);  // Thread-safe

// Same device requires synchronization
std::mutex device_mutex;
std::lock_guard<std::mutex> lock(device_mutex);
connection->set_camera_property(CamProp::Pan, setting);
```


***

## Troubleshooting

### Common Issues \& Solutions

#### No Devices Found

**Solutions**:

1. **Check Device Manager**: Camera should appear under "Imaging devices"
2. **Test with Windows Camera App**: Verify camera works with built-in app
3. **Run Diagnostics**:
```cpp
std::string diagnostics = duvc::get_diagnostic_info();
std::cout << diagnostics << std::endl;
```


#### Property Operations Fail

**Solutions**:

1. **Check Support**: Always verify property support first
```cpp
auto range_result = connection->get_camera_property_range(CamProp::Pan);
if (range_result.is_error()) {
    std::cout << "Pan not supported: " << range_result.error().description() << std::endl;
}
```

2. **Enable Detailed Logging**:
```cpp
duvc::set_log_level(duvc::LogLevel::Debug);
```


#### C API / Python Import Failures

**Solutions**:

1. **Install Visual C++ Redistributable 2019/2022**
2. **Check ABI Compatibility**:
```c
if (!duvc_check_abi_compatibility(DUVC_ABI_VERSION)) {
    // ABI mismatch - recompile required
}
```


***

## Contributing

### Development Environment Setup

1. **Clone and Setup**:
```bash
git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl
```

2. **Configure Development Build**:
```bash
cmake -B build \
    -G "Visual Studio 17 2022" -A x64 \
    -DDUVC_BUILD_TESTS=ON \
    -DDUVC_BUILD_EXAMPLES=ON \
    -DDUVC_WARNINGS_AS_ERRORS=ON \
    -DCMAKE_BUILD_TYPE=Debug
```

3. **Build and Test**:
```bash
cmake --build build --config Debug
cd build && ctest --config Debug --output-on-failure
```


### Code Style and Standards

**C++ Guidelines**:

- **C++17** modern features and idioms
- **RAII** for all resource management
- **Thread-safety** documentation required
- **Exception safety** strong guarantee preferred


### Testing Requirements

**All Changes Must Include**:

1. **Unit Tests**: For isolated component functionality
2. **Integration Tests**: For real device interaction (if applicable)
3. **Documentation**: Update README and code comments
4. **Error Handling**: Comprehensive error cases

***

## License

**MIT License** - see [LICENSE](LICENSE) for complete details.

**Summary**: You can use, modify, and distribute this library freely, including in commercial projects, with attribution.

***

## Support and Community

- **Issues**: [GitHub Issues](https://github.com/allanhanan/duvc-ctl/issues)
- **Discussions**: [GitHub Discussions](https://github.com/allanhanan/duvc-ctl/discussions)
- **Documentation**: [Wiki](https://github.com/allanhanan/duvc-ctl/wiki) (coming soon)
- **Examples**: [examples/](examples/) directory (coming soon)

**Commercial Support**: Available for enterprise deployments and custom vendor integrations.
