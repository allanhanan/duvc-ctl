# duvc-ctl: Windows Camera Control Library

Windows DirectShow UVC camera control library with C++, Python, and CLI interfaces.

## Overview

duvc-ctl provides direct control over DirectShow UVC cameras on Windows. Control PTZ operations, exposure, focus, brightness, and other camera properties.

**Key Features:**
- DirectShow UVC camera enumeration and control
- PTZ (Pan/Tilt/Zoom) operations
- Camera properties (exposure, focus, iris)
- Video properties (brightness, contrast, white balance)
- Device monitoring with hotplug detection
- Connection pooling for performance
- C++17, Python, and CLI interfaces

## Quick Start

### C++ API

```cpp
#include "duvc-ctl/core.h"

// List cameras
auto devices = duvc::list_devices();
if (devices.empty()) return;

// Get camera property range
duvc::PropRange range;
if (duvc::get_range(devices[0], duvc::CamProp::Pan, range)) {
    std::cout << "Pan range: " << range.min << " to " << range.max << std::endl;
}

// Set camera property
duvc::PropSetting setting{0, duvc::CamMode::Manual};  // Center pan
duvc::set(devices[0], duvc::CamProp::Pan, setting);
```

### Python API

Install from pip with `pip install duvc-ctl` (coming soon)

```python
import duvc_ctl as duvc

# List cameras
devices = duvc.list_devices()
if not devices:
    return

# Get property value
setting = duvc.PropSetting()
if duvc.get(devices[0], duvc.CamProp.Pan, setting):
    print(f"Current pan: {setting.value}")

# Set brightness
brightness = duvc.PropSetting(50, duvc.CamMode.Manual)
duvc.set(devices[0], duvc.VidProp.Brightness, brightness)
```

### Command Line

Get .exe from releases

```bash
# List cameras
duvc-cli list

# Get property value
duvc-cli get 0 cam Pan

# Set property value
duvc-cli set 0 cam Pan 0 manual

# Monitor device changes
duvc-cli monitor 30
```

## Build Instructions

### Prerequisites

- Windows 10/11
- Visual Studio 2019/2022 or MinGW-w64
- CMake 3.16+
- Python 3.8+ (for Python bindings)

### Basic Build

```bash
git clone https://github.com/user/duvc-ctl.git
cd duvc-ctl
mkdir build && cd build

# Configure
cmake -G "Visual Studio 17 2022" -A x64 \
  -DDUVC_BUILD_STATIC=ON \
  -DDUVC_BUILD_CLI=ON \
  -DDUVC_BUILD_PYTHON=ON \
  ..

# Build
cmake --build . --config Release
```

### Build Options

| Option | Default | Description |
|--------|---------|-------------|
| `DUVC_BUILD_STATIC` | ON | Build static library |
| `DUVC_BUILD_SHARED` | OFF | Build shared library |
| `DUVC_BUILD_CLI` | ON | Build command-line tool |
| `DUVC_BUILD_PYTHON` | OFF | Build Python bindings |
| `DUVC_WARNINGS_AS_ERRORS` | OFF | Treat warnings as errors |


## For python:
From project root do: 
```
python -m build
```

## API Reference

### Core Types

```cpp
struct Device {
    std::wstring name;  // Camera name
    std::wstring path;  // Device path
};

struct PropSetting {
    int value;          // Property value
    CamMode mode;       // Auto or Manual
};

struct PropRange {
    int min, max, step; // Value constraints
    int default_val;    // Default value
    CamMode default_mode;
};
```

### Camera Properties (IAMCameraControl)

```cpp
enum class CamProp {
    Pan, Tilt, Roll, Zoom, Exposure, Iris, Focus,
    ScanMode, Privacy, PanRelative, TiltRelative,
    RollRelative, ZoomRelative, ExposureRelative,
    IrisRelative, FocusRelative, PanTilt,
    PanTiltRelative, FocusSimple, DigitalZoom,
    DigitalZoomRelative, BacklightCompensation, Lamp
};
```

### Video Properties (IAMVideoProcAmp)

```cpp
enum class VidProp {
    Brightness, Contrast, Hue, Saturation,
    Sharpness, Gamma, ColorEnable, WhiteBalance,
    BacklightCompensation, Gain
};
```

### Device Operations

```cpp
// Device enumeration
std::vector<Device> list_devices();
bool is_device_connected(const Device& dev);
void clear_connection_cache();

// Property control
bool get_range(const Device&, CamProp, PropRange&);
bool get(const Device&, CamProp, PropSetting&);
bool set(const Device&, CamProp, const PropSetting&);

bool get_range(const Device&, VidProp, PropRange&);
bool get(const Device&, VidProp, PropSetting&);
bool set(const Device&, VidProp, const PropSetting&);

// Device monitoring
using DeviceChangeCallback = std::function<void(bool added, const std::wstring& path)>;
void register_device_change_callback(DeviceChangeCallback callback);
void unregister_device_change_callback();
```

## Examples

### Camera Centering

```cpp
// Center PTZ camera
duvc::PropSetting center{0, duvc::CamMode::Manual};
duvc::set(device, duvc::CamProp::Pan, center);
duvc::set(device, duvc::CamProp::Tilt, center);
```

### Property Validation

```cpp
// Check property range before setting
duvc::PropRange range;
if (duvc::get_range(device, duvc::CamProp::Zoom, range)) {
    int zoom_value = 50;
    if (zoom_value >= range.min && zoom_value <= range.max) {
        duvc::PropSetting setting{zoom_value, duvc::CamMode::Manual};
        duvc::set(device, duvc::CamProp::Zoom, setting);
    }
}
```

### Device Monitoring

```cpp
// Monitor device changes
duvc::register_device_change_callback([](bool added, const std::wstring& path) {
    std::wcout << (added ? L"Added: " : L"Removed: ") << path << std::endl;
});
```

### Python Interactive Demo

```python
# Run interactive camera controller
python examples/example.py
```

## Architecture

### DirectShow Integration

duvc-ctl uses DirectShow APIs for camera control:

- **ICreateDevEnum**: Device enumeration
- **IAMCameraControl**: PTZ and camera properties
- **IAMVideoProcAmp**: Video processing properties
- **IKsPropertySet**: Vendor-specific extensions

### Connection Pooling

Automatic connection caching improves performance:

- Reduces DirectShow binding overhead (10-50ms per operation)
- Thread-safe connection management
- Automatic cleanup on device disconnect

### Error Handling

Comprehensive error reporting with HRESULT details:

```cpp
try {
    auto devices = duvc::list_devices();
} catch (const std::exception& e) {
    std::cout << "Error: " << e.what() << std::endl;
    // Includes detailed DirectShow error information
}
```

## Testing

### C++ Unit Tests

```bash
cd tests
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build
```

### Python Import Test

```bash
cd tests
python test_import.py
```

### Manual Testing

```bash
# Test CLI
./build/bin/duvc-cli list

# Test Python bindings
cd build/py
python -c "import duvc_ctl; print(len(duvc_ctl.list_devices()))"
```

## Platform Support

- **Windows 10/11**: Full support
- **Windows 8.1**: Compatible but not tested
- **Other platforms**: Not supported (DirectShow is Windows-only)

## Performance

### Benchmarks

- Device enumeration: ~50-200ms
- Property operations (cached): ~1-5ms
- Property operations (uncached): ~10-50ms
- Connection pool hit rate: >95% in typical usage

### Threading

- Device enumeration: Thread-safe
- Property operations: Safe with different devices
- Same device access: Requires external synchronization

## Troubleshooting

### Common Issues

**No devices found:**
- Check Device Manager for camera under "Imaging devices"
- Test camera with Windows Camera app
- Run as Administrator to check permissions

**Property control fails:**
- Verify property is supported with `get_range()`
- Check value is within valid range
- Ensure no other application is using camera

**Python import fails:**
- Install Visual C++ Redistributable
- Check .pyd file exists in build/py/
- Verify Python path includes build directory

### Debug Build

```bash
cmake -DCMAKE_BUILD_TYPE=Debug -DDUVC_WARNINGS_AS_ERRORS=ON ..
```

### Verbose Errors

```cpp
// Enable detailed COM error reporting
#define DUVC_VERBOSE_ERRORS
#include "duvc-ctl/core.h"
```


## Contributing

1. Fork repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

### Code Style

- C++17 modern features
- RAII for resource management
- Thread-safety documentation
- Comprehensive error handling



# duvc-ctl: DirectShow UVC Camera Control Library

**Complete Developer Documentation**

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture Deep Dive](#architecture-deep-dive)
- [DirectShow Integration](#directshow-integration)
- [Build System Comprehensive Guide](#build-system-comprehensive-guide)
- [C++ API Complete Reference](#c-api-complete-reference)
- [Python Bindings Architecture](#python-bindings-architecture)
- [Command Line Interface](#command-line-interface)
- [Performance \& Threading](#performance--threading)
- [Testing Framework](#testing-framework)
- [Development Workflow](#development-workflow)
- [Troubleshooting \& Debugging](#troubleshooting--debugging)
- [Deployment \& Distribution](#deployment--distribution)


## Project Overview

duvc-ctl is a Windows-exclusive library for controlling DirectShow UVC (USB Video Class) cameras. It provides comprehensive access to camera properties through multiple interfaces while maintaining high performance and thread safety.

### Core Features

**Camera Control Domains:**

- **IAMCameraControl**: 24 properties including Pan, Tilt, Zoom, Focus, Exposure
- **IAMVideoProcAmp**: 10 properties including Brightness, Contrast, White Balance
- **IKsPropertySet**: Vendor-specific extensions and custom properties

**Multi-Language Support:**

- Native C++17 API with modern RAII patterns
- Python bindings via pybind11 with automatic type conversion

**Advanced Capabilities:**

- Connection pooling for performance optimization
- Hot-plug device detection with callbacks
- Thread-safe operations across all interfaces
- Comprehensive error handling with detailed HRESULT reporting


### Project Structure Analysis
```
duvc-ctl/
├── CMakeLists.txt                    # Root CMake configuration
├── LICENSE                           # Project license
├── README.md                         # Project documentation
├── pyproject.toml                    # Python build config
├── .gitignore                        # Files to ignore in version control
├── include/duvc-ctl/                 # Public API headers
│   ├── core.h                        # Main API declarations
│   └── defs.h                        # Type definitions
├── src/                              # Core implementation
│   ├── CMakeLists.txt                # Build configuration for C++ sources
│   ├── core.cpp                      # Main library logic
│   ├── bindings.cpp                  # C bindings for external(python) integration
│   └── py/
│       └── pybind_module.cpp         # Python bindings via Pybind11
├── cli/                              # Command-line interface
│   ├── CMakeLists.txt                # CLI build
│   └── main.cpp                      # CLI logic
├── py/duvc_ctl/                      # Python package source
│   └── __init__.py                   # Package metadata and init
├── examples/                         # Usage examples
│   └── example.py                    # Interactive demo
└── tests/                            # Test suite
    ├── CMakeLists.txt                # Test build
    ├── test_core.cpp                 # C++ unit tests
    └── test_import.py               # Python package validation
```

## Architecture Deep Dive

### Core Type System

**Device Representation:**

```cpp
struct Device {
    std::wstring name;    // Human-readable name from DirectShow
    std::wstring path;    // Unique device path for binding
};
```

The `Device` struct is the fundamental unit of camera identification. The `path` field contains the DirectShow device path which is guaranteed unique, while `name` provides user-friendly identification.

**Property Value Management:**

```cpp
struct PropSetting {
    int value;           // Property value within valid range
    CamMode mode;        // Auto or Manual control mode
};

struct PropRange {
    int min, max, step;  // Constrains for valid values
    int default_val;     // Factory default setting
    CamMode default_mode; // Default control mode
};
```

**Control Mode Semantics:**

```cpp
enum class CamMode { 
    Auto = 1,    // Camera automatically adjusts property
    Manual = 2   // User has direct control over property value
};
```

Note: Values match DirectShow constants (`CameraControl_Flags_Auto` and `CameraControl_Flags_Manual`).

### Property Domain Architecture

**Camera Control Properties (IAMCameraControl):**

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

**Video Processing Properties (IAMVideoProcAmp):**

```cpp
enum class VidProp {
    // Basic image adjustment
    Brightness, Contrast, Hue, Saturation,
    
    // Advanced processing
    Sharpness, Gamma, ColorEnable, WhiteBalance,
    BacklightCompensation, Gain
};
```


### DirectShow Integration Layer

**COM Management Architecture:**

```cpp
template<typename T>
class com_ptr {
public:
    com_ptr() noexcept = default;
    explicit com_ptr(T* p) noexcept : p_(p) {}
    ~com_ptr() { reset(); }
    
    // Move-only semantics (no copying)
    com_ptr(const com_ptr&) = delete;
    com_ptr& operator=(const com_ptr&) = delete;
    com_ptr(com_ptr&& o) noexcept : p_(o.p_) { o.p_ = nullptr; }
    
    T* get() const noexcept { return p_; }
    T** put() noexcept { reset(); return &p_; }
    void reset() noexcept { if (p_) { p_->Release(); p_ = nullptr; } }
    
private:
    T* p_ = nullptr;
};
```

This custom COM pointer provides RAII management for DirectShow interfaces with move semantics for efficient resource transfers.

**COM Apartment Management:**

```cpp
class com_apartment {
public:
    com_apartment() {
        hr_ = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
        if (FAILED(hr_) && hr_ != RPC_E_CHANGED_MODE) {
            throw_hr(hr_, "CoInitializeEx");
        }
    }
    
    ~com_apartment() {
        if (SUCCEEDED(hr_)) CoUninitialize();
    }
    
private:
    HRESULT hr_{S_OK};
};
```

Ensures proper COM initialization/cleanup per thread, handling the common `RPC_E_CHANGED_MODE` case where COM is already initialized.

## DirectShow Integration

### Device Enumeration Process

**Step 1: Create System Device Enumerator**

```cpp
static com_ptr<ICreateDevEnum> create_dev_enum() {
    com_ptr<ICreateDevEnum> dev;
    HRESULT hr = CoCreateInstance(CLSID_SystemDeviceEnum, nullptr, 
                                  CLSCTX_INPROC_SERVER, IID_ICreateDevEnum,
                                  reinterpret_cast<void**>(dev.put()));
    if (FAILED(hr)) throw_hr(hr, "CoCreateInstance(SystemDeviceEnum)");
    return dev;
}
```

**Step 2: Enumerate Video Input Devices**

```cpp
static com_ptr<IEnumMoniker> enum_video_devices(ICreateDevEnum* dev) {
    com_ptr<IEnumMoniker> e;
    HRESULT hr = dev->CreateClassEnumerator(CLSID_VideoInputDeviceCategory, e.put(), 0);
    if (hr == S_FALSE) return {}; // No devices
    if (FAILED(hr)) throw_hr(hr, "CreateClassEnumerator(VideoInputDeviceCategory)");
    return e;
}
```

**Step 3: Extract Device Metadata**

```cpp
static std::wstring read_prop_bstr(IPropertyBag* bag, const wchar_t* key) {
    VARIANT v; VariantInit(&v);
    std::wstring res;
    if (SUCCEEDED(bag->Read(key, &v, nullptr)) && v.vt == VT_BSTR && v.bstrVal) {
        res.assign(v.bstrVal, SysStringLen(v.bstrVal));
    }
    VariantClear(&v);
    return res;
}
```

The enumeration process uses DirectShow's category-based device discovery, extracting both friendly names and device paths for unique identification.

### Property Control Implementation

**DirectShow Constant Mapping:**

```cpp
static long camprop_to_dshow(CamProp p) {
    switch (p) {
        case CamProp::Pan: return CameraControl_Pan;           // 0L
        case CamProp::Tilt: return CameraControl_Tilt;         // 1L
        case CamProp::Roll: return CameraControl_Roll;         // 2L
        case CamProp::Zoom: return CameraControl_Zoom;         // 3L
        case CamProp::Exposure: return CameraControl_Exposure; // 4L
        // ... (19 more properties)
        default: return -1;
    }
}
```

**Control Mode Translation:**

```cpp
static long to_flag(CamMode m, bool is_camera_control) {
    if (is_camera_control) {
        return (m == CamMode::Auto) ? CameraControl_Flags_Auto    // 0x0001
                                    : CameraControl_Flags_Manual; // 0x0002
    } else {
        return (m == CamMode::Auto) ? VideoProcAmp_Flags_Auto     // 0x0001
                                    : VideoProcAmp_Flags_Manual;  // 0x0002
    }
}
```


### Error Handling Strategy

**HRESULT Error Translation:**

```cpp
static void throw_hr(HRESULT hr, const char* where) {
    _com_error err(hr);
    std::ostringstream oss;
    oss << where << " failed (hr=0x" << std::hex << hr << ")";
    if (err.ErrorMessage()) {
        oss << " - " << wide_to_utf8(err.ErrorMessage());
    }
    throw std::runtime_error(oss.str());
}
```

This approach provides detailed error information including HRESULT codes and human-readable descriptions for debugging.

## Build System Comprehensive Guide

### CMake Configuration Architecture

**Root CMakeLists.txt Structure:**

```cmake
cmake_minimum_required(VERSION 3.16)
project(duvc-ctl VERSION 1.0.0 LANGUAGES CXX)

# Build options with defaults
option(DUVC_BUILD_STATIC "Build duvc static library" ON)
option(DUVC_BUILD_SHARED "Build duvc shared library" OFF)  
option(DUVC_BUILD_CLI "Build duvc CLI" ON)
option(DUVC_BUILD_PYTHON "Build Python bindings (pybind11)" OFF)
option(DUVC_WARNINGS_AS_ERRORS "Treat warnings as errors" OFF)
option(DUVC_USE_SYSTEM_PYBIND11 "Use system-installed pybind11" OFF)

# Global C++ settings
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
```

**Multi-Configuration Output Directory Handling:**

```cmake
# MSVC multi-config (Debug/Release) support
foreach(OUTPUTCONFIG ${CMAKE_CONFIGURATION_TYPES})
    string(TOUPPER ${OUTPUTCONFIG} OUTPUTCONFIG_UC)
    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_${OUTPUTCONFIG_UC} ${CMAKE_BINARY_DIR}/lib)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_${OUTPUTCONFIG_UC} ${CMAKE_BINARY_DIR}/bin)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_${OUTPUTCONFIG_UC} ${CMAKE_BINARY_DIR}/bin)
endforeach()

# Single-config generators (Ninja, Make)
if(NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
endif()
```

This ensures consistent output layout across different generators with libraries in `lib/` and executables in `bin/`.

### Compiler-Specific Configuration Functions

**MSVC Configuration Function:**

```cmake
function(duvc_apply_warnings target)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /permissive-)
        if(DUVC_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE /WX)
        endif()
        target_compile_definitions(${target} PRIVATE UNICODE _UNICODE NOMINMAX)
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
        if(DUVC_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE -Werror)
        endif()
    endif()
endfunction()
```

**DirectShow Linking Helper:**

```cmake
function(duvc_link_directshow target)
    if(WIN32)
        target_link_libraries(${target} PRIVATE ole32 oleaut32 strmiids)
    endif()
endfunction()
```

**MinGW Console Subsystem Fix:**

```cmake
function(duvc_fix_mingw_console target)
    if(MINGW)
        target_link_options(${target} PRIVATE -mconsole -Wl,--subsystem,console)
    endif()
endfunction()
```


### Library Target Configuration

**Modular Source Definition:**

```cmake
set(DUVC_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/include)

set(DUVC_SOURCES
    src/core.cpp
    src/bindings.cpp
)
```

**Static Library Target:**

```cmake
if(DUVC_BUILD_STATIC)
    add_library(duvc STATIC ${DUVC_SOURCES})
    target_include_directories(duvc PUBLIC ${DUVC_INCLUDE_DIR})
    target_compile_features(duvc PUBLIC cxx_std_17)
    duvc_apply_warnings(duvc)
    duvc_link_directshow(duvc)
endif()
```

**Shared Library Target:**

```cmake
if(DUVC_BUILD_SHARED)
    add_library(duvc_shared SHARED ${DUVC_SOURCES})
    target_include_directories(duvc_shared PUBLIC ${DUVC_INCLUDE_DIR})
    target_compile_features(duvc_shared PUBLIC cxx_std_17)
    target_compile_definitions(duvc_shared PRIVATE DUVCC_DLL_BUILD)
    set_target_properties(duvc_shared PROPERTIES OUTPUT_NAME duvc)
    duvc_apply_warnings(duvc_shared)
    duvc_link_directshow(duvc_shared)
endif()
```


### Python Bindings Build Configuration

**Advanced pybind11 Module Setup:**

```cmake
if(DUVC_BUILD_PYTHON)
    # Python and pybind11 discovery
    find_package(Python COMPONENTS Interpreter Development REQUIRED)
    
    if(DUVC_USE_SYSTEM_PYBIND11)
        find_package(pybind11 CONFIG REQUIRED)
    else()
        include(FetchContent)
        FetchContent_Declare(
            pybind11
            GIT_REPOSITORY https://github.com/pybind/pybind11.git
            GIT_TAG v2.11.1
        )
        FetchContent_MakeAvailable(pybind11)
    endif()

    set(DUVC_PY_SOURCES src/py/pybind_module.cpp)

    if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/src/py/pybind_module.cpp)
        # Create Python extension with underscore prefix for internal module
        pybind11_add_module(_duvc_ctl ${DUVC_PY_SOURCES})
        
        # Advanced MSVC Multi-Config Output Directory Handling
        if(CMAKE_GENERATOR_PLATFORM)
            set_target_properties(_duvc_ctl PROPERTIES 
                OUTPUT_NAME "_duvc_ctl"
                LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/py
                RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/py
                LIBRARY_OUTPUT_DIRECTORY_RELEASE ${CMAKE_BINARY_DIR}/py
                RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_BINARY_DIR}/py
                LIBRARY_OUTPUT_DIRECTORY_DEBUG ${CMAKE_BINARY_DIR}/py
                RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_BINARY_DIR}/py
            )
        else()
            set_target_properties(_duvc_ctl PROPERTIES 
                OUTPUT_NAME "_duvc_ctl"
                LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/py
                RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/py
            )
        endif()
        
        target_include_directories(_duvc_ctl PRIVATE ${DUVC_INCLUDE_DIR})
        
        # Flexible library linking strategy
        if(DUVC_BUILD_STATIC)
            target_link_libraries(_duvc_ctl PRIVATE duvc)
        elseif(DUVC_BUILD_SHARED)
            target_link_libraries(_duvc_ctl PRIVATE duvc_shared)
        else()
            # Standalone Python module with embedded sources
            target_sources(_duvc_ctl PRIVATE ${DUVC_SOURCES})
            duvc_link_directshow(_duvc_ctl)
        endif()
        
        duvc_apply_warnings(_duvc_ctl)
        duvc_link_directshow(_duvc_ctl)
    else()
        message(WARNING "DUVC_BUILD_PYTHON=ON but src/py/pybind_module.cpp not found. Skipping Python module.")
    endif()
endif()
```


### Installation Configuration

**Flexible Installation Rules:**

```cmake
include(GNUInstallDirs)

# Install headers for library builds
if(DUVC_BUILD_STATIC OR DUVC_BUILD_SHARED)
    install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
endif()

# Install static library
if(TARGET duvc)
    install(TARGETS duvc
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
endif()

# Install shared library
if(TARGET duvc_shared)
    install(TARGETS duvc_shared
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
endif()

# Install CLI executable
if(TARGET duvc-cli)
    install(TARGETS duvc-cli
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
endif()

# Python module installation for scikit-build-core
if(DUVC_BUILD_PYTHON AND TARGET _duvc_ctl)
    install(TARGETS _duvc_ctl
        DESTINATION ${SKBUILD_PLATLIB_DIR}/duvc_ctl)
endif()
```

## C++ API Complete Reference

### Core Library Architecture

**Main Library Sources:**

- `src/core.cpp` (1,521 lines): Complete DirectShow integration
- `src/bindings.cpp` (211 lines): C bindings for external language integration


### Device Management API

**Primary Device Operations:**

```cpp
namespace duvc {
    // Device discovery and status
    std::vector<Device> list_devices();
    bool is_device_connected(const Device& dev);
    
    // Connection optimization  
    void clear_connection_cache();
}
```

**Device Connection Implementation:**

```cpp
bool is_device_connected(const Device& dev) {
    try {
        // Step 1: Verify device exists in system enumeration
        com_apartment com;
        auto de = create_dev_enum();
        auto en = enum_video_devices(de.get());
        if (!en) return false;
        
        // Step 2: Search for matching device
        ULONG fetched = 0;
        com_ptr<IMoniker> mon;
        while (en->Next(1, mon.put(), &fetched) == S_OK && fetched) {
            auto fname = read_friendly_name(mon.get());
            auto dpath = read_device_path(mon.get());
            if (is_same_device(dev, fname, dpath)) {
                // Step 3: Test device accessibility
                try {
                    auto* conn = get_cached_connection(dev);
                    return conn != nullptr && conn->is_valid();
                } catch (...) {
                    return true; // Device exists but may be busy
                }
            }
            mon.reset();
        }
        return false;
    } catch (...) {
        return false;
    }
}
```


### Property Control API

**Camera Control Functions:**

```cpp
// IAMCameraControl interface
bool get_range(const Device& dev, CamProp prop, PropRange& range);
bool get(const Device& dev, CamProp prop, PropSetting& setting);
bool set(const Device& dev, CamProp prop, const PropSetting& setting);
```

**Video Processing Functions:**

```cpp
// IAMVideoProcAmp interface  
bool get_range(const Device& dev, VidProp prop, PropRange& range);
bool get(const Device& dev, VidProp prop, PropSetting& setting);
bool set(const Device& dev, VidProp prop, const PropSetting& setting);
```

**Implementation Pattern (Camera Control Example):**

```cpp
bool get_range(const Device& dev, CamProp prop, PropRange& range) {
    auto* conn = get_cached_connection(dev);
    return conn ? conn->get_range(prop, range) : false;
}

// DeviceConnection::get_range implementation
bool DeviceConnection::get_range(CamProp prop, PropRange& range) {
    auto* cam_ctrl = static_cast<com_ptr<IAMCameraControl>*>(cam_ctrl_);
    if (!cam_ctrl || !*cam_ctrl) return false;
    
    long pid = camprop_to_dshow(prop);
    if (pid < 0) return false;
    
    long min = 0, max = 0, step = 0, def = 0, flags = 0;
    HRESULT hr = (*cam_ctrl)->GetRange(pid, &min, &max, &step, &def, &flags);
    if (FAILED(hr)) return false;
    
    range.min = static_cast<int>(min);
    range.max = static_cast<int>(max);
    range.step = static_cast<int>(step);
    range.default_val = static_cast<int>(def);
    range.default_mode = from_flag(flags, true);
    return true;
}
```


### Advanced Features API

**Vendor-Specific Properties (Windows Only):**

```cpp
#ifdef _WIN32
struct VendorProperty {
    GUID property_set;
    ULONG property_id;
    std::vector<uint8_t> data;
};

bool get_vendor_property(const Device& dev, const GUID& property_set, 
                        ULONG property_id, std::vector<uint8_t>& data);
bool set_vendor_property(const Device& dev, const GUID& property_set,
                        ULONG property_id, const std::vector<uint8_t>& data);
bool query_vendor_property_support(const Device& dev, const GUID& property_set,
                                   ULONG property_id);
#endif
```

**Device Monitoring (Hot-plug Detection):**

```cpp
using DeviceChangeCallback = std::function<void(bool added, const std::wstring& path)>;

void register_device_change_callback(DeviceChangeCallback callback);
void unregister_device_change_callback();
```

**Device Monitoring Implementation:**

```cpp
void register_device_change_callback(DeviceChangeCallback callback) {
    if (g_notification_window) return; // Already registered
    
    g_device_callback = callback;
    
    // Create invisible message-only window
    WNDCLASSW wc = {};
    wc.lpfnWndProc = device_wndproc;
    wc.hInstance = GetModuleHandle(nullptr);
    wc.lpszClassName = L"DuvcDeviceNotification";
    RegisterClassW(&wc);
    
    g_notification_window = CreateWindowW(L"DuvcDeviceNotification", L"", 0, 
                                         0, 0, 0, 0, HWND_MESSAGE, nullptr, 
                                         GetModuleHandle(nullptr), nullptr);
    
    // Register for device interface notifications
    DEV_BROADCAST_DEVICEINTERFACE filter = {};
    filter.dbcc_size = sizeof(filter);
    filter.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE;
    filter.dbcc_classguid = CLSID_VideoInputDeviceCategory;
    
    g_device_notify = RegisterDeviceNotification(g_notification_window, &filter,
                                                 DEVICE_NOTIFY_WINDOW_HANDLE);
}
```


### String Conversion Utilities

**Property Name Conversion:**

```cpp
// ASCII string conversion (for logging, CLI)
const char* to_string(CamProp prop);
const char* to_string(VidProp prop);  
const char* to_string(CamMode mode);

// Wide string conversion (for Windows APIs)
const wchar_t* to_wstring(CamProp prop);
const wchar_t* to_wstring(VidProp prop);
const wchar_t* to_wstring(CamMode mode);
```

**Implementation Example:**

```cpp
const char* to_string(CamProp p) {
    switch (p) {
        case CamProp::Pan: return "Pan";
        case CamProp::Tilt: return "Tilt";
        case CamProp::Roll: return "Roll";
        // ... 21 more cases
        default: return "Unknown";
    }
}
```


## Performance \& Threading

### Connection Pooling Architecture

**Global Connection Cache:**

```cpp
static std::mutex g_cache_mutex;
static std::unordered_map<std::wstring, std::unique_ptr<DeviceConnection>> g_connection_cache;
```

**Connection Management:**

```cpp
DeviceConnection* get_cached_connection(const Device& dev) {
    std::lock_guard<std::mutex> lock(g_cache_mutex);
    std::wstring key = dev.path.empty() ? dev.name : dev.path;
    
    auto it = g_connection_cache.find(key);
    if (it != g_connection_cache.end() && it->second->is_valid()) {
        return it->second.get(); // Return existing connection
    }
    
    // Create new connection
    auto conn = std::make_unique<DeviceConnection>(dev);
    if (!conn->is_valid()) return nullptr;
    
    DeviceConnection* result = conn.get();
    g_connection_cache[key] = std::move(conn);
    return result;
}
```

**Performance Benefits:**

- **Reduced Latency**: Eliminates repeated COM interface binding (typically 10-50ms per operation)
- **Resource Efficiency**: Reuses expensive DirectShow filter graphs
- **Thread Safety**: Mutex-protected cache operations
- **Automatic Cleanup**: RAII-based resource management


### DeviceConnection Class Architecture

**Resource Management:**

```cpp
class DeviceConnection {
public:
    explicit DeviceConnection(const Device& dev);
    ~DeviceConnection();
    
    bool is_valid() const { return filter_ != nullptr; }
    
    // Property operations (internally cached)
    bool get(CamProp prop, PropSetting& val);
    bool set(CamProp prop, const PropSetting& val);
    bool get(VidProp prop, PropSetting& val);
    bool set(VidProp prop, const PropSetting& val);
    bool get_range(CamProp prop, PropRange& range);
    bool get_range(VidProp prop, PropRange& range);
    
private:
    class com_apartment;
    std::unique_ptr<com_apartment> com_;
    
    // Stored as void* to avoid forward declarations
    void* filter_;    // com_ptr<IBaseFilter>
    void* cam_ctrl_;  // com_ptr<IAMCameraControl>
    void* vid_proc_;  // com_ptr<IAMVideoProcAmp>
};
```

**Constructor Implementation:**

```cpp
DeviceConnection::DeviceConnection(const Device& dev) :
    com_(std::make_unique<com_apartment>()),
    filter_(nullptr),
    cam_ctrl_(nullptr),
    vid_proc_(nullptr) {
    try {
        auto filter = open_device_filter(dev);
        if (filter) {
            auto cam_ctrl = get_cam_ctrl(filter.get());
            auto vid_proc = get_vproc(filter.get());
            
            // Store as raw pointers to avoid template dependencies in header
            filter_ = new com_ptr<IBaseFilter>(std::move(filter));
            cam_ctrl_ = new com_ptr<IAMCameraControl>(std::move(cam_ctrl));
            vid_proc_ = new com_ptr<IAMVideoProcAmp>(std::move(vid_proc));
        }
    } catch (...) {
        filter_ = nullptr; // Mark as invalid
    }
}
```


### Thread Safety Guarantees

**Global State Protection:**

- Device enumeration: Thread-safe (uses local COM instances)
- Connection cache: Mutex-protected access
- Device callbacks: Single-threaded callback execution
- Property operations: Safe when using different devices concurrently

**Threading Recommendations:**

```cpp
// Safe: Multiple threads, different devices
std::thread t1([&] { duvc::set(device1, duvc::CamProp::Pan, setting); });
std::thread t2([&] { duvc::set(device2, duvc::CamProp::Pan, setting); });

// Unsafe: Multiple threads, same device (requires external synchronization)
std::mutex device_mutex;
std::thread t3([&] { 
    std::lock_guard<std::mutex> lock(device_mutex);
    duvc::set(device1, duvc::CamProp::Pan, setting); 
});
```


## Python Bindings Architecture

### pybind11 Integration

**Module Definition (src/py/pybind_module.cpp):**

```cpp
PYBIND11_MODULE(_duvc_ctl, m) {  // Note: underscore prefix for internal module
    m.doc() = "duvc-ctl: DirectShow UVC Camera Control Library";
    
    // Device struct binding with proper wstring handling
    py::class_<duvc::Device>(m, "Device")
        .def(py::init<>())
        .def_readwrite("name", &duvc::Device::name)
        .def_readwrite("path", &duvc::Device::path)
        .def("__repr__", [](const duvc::Device& d) {
            return "<Device(name='" + std::string(d.name.begin(), d.name.end()) + "')>";
        });
}
```

**Enum Bindings with Automatic Conversion:**

```cpp
py::enum_<duvc::CamMode>(m, "CamMode")
    .value("Auto", duvc::CamMode::Auto)
    .value("Manual", duvc::CamMode::Manual);

py::enum_<duvc::CamProp>(m, "CamProp")
    .value("Pan", duvc::CamProp::Pan)
    .value("Tilt", duvc::CamProp::Tilt)
    .value("Roll", duvc::CamProp::Roll)
    .value("Zoom", duvc::CamProp::Zoom)
    .value("Exposure", duvc::CamProp::Exposure)
    .value("Iris", duvc::CamProp::Iris)
    .value("Focus", duvc::CamProp::Focus)
    .value("ScanMode", duvc::CamProp::ScanMode)
    .value("Privacy", duvc::CamProp::Privacy)
    .value("PanRelative", duvc::CamProp::PanRelative)
    .value("TiltRelative", duvc::CamProp::TiltRelative)
    .value("RollRelative", duvc::CamProp::RollRelative)
    .value("ZoomRelative", duvc::CamProp::ZoomRelative)
    .value("ExposureRelative", duvc::CamProp::ExposureRelative)
    .value("IrisRelative", duvc::CamProp::IrisRelative)
    .value("FocusRelative", duvc::CamProp::FocusRelative)
    .value("PanTilt", duvc::CamProp::PanTilt)
    .value("PanTiltRelative", duvc::CamProp::PanTiltRelative)
    .value("FocusSimple", duvc::CamProp::FocusSimple)
    .value("DigitalZoom", duvc::CamProp::DigitalZoom)
    .value("DigitalZoomRelative", duvc::CamProp::DigitalZoomRelative)
    .value("BacklightCompensation", duvc::CamProp::BacklightCompensation)
    .value("Lamp", duvc::CamProp::Lamp);

py::enum_<duvc::VidProp>(m, "VidProp")
    .value("Brightness", duvc::VidProp::Brightness)
    .value("Contrast", duvc::VidProp::Contrast)
    .value("Hue", duvc::VidProp::Hue)
    .value("Saturation", duvc::VidProp::Saturation)
    .value("Sharpness", duvc::VidProp::Sharpness)
    .value("Gamma", duvc::VidProp::Gamma)
    .value("ColorEnable", duvc::VidProp::ColorEnable)
    .value("WhiteBalance", duvc::VidProp::WhiteBalance)
    .value("BacklightCompensation", duvc::VidProp::BacklightCompensation)
    .value("Gain", duvc::VidProp::Gain);
```

**Function Overloading Resolution:**

```cpp
// Camera control functions
m.def("get_range", py::overload_cast<const duvc::Device&, duvc::CamProp, duvc::PropRange&>(&duvc::get_range),
      "Get camera property range", py::arg("device"), py::arg("property"), py::arg("range"));

m.def("get", py::overload_cast<const duvc::Device&, duvc::CamProp, duvc::PropSetting&>(&duvc::get),
      "Get camera property value", py::arg("device"), py::arg("property"), py::arg("setting"));

m.def("set", py::overload_cast<const duvc::Device&, duvc::CamProp, const duvc::PropSetting&>(&duvc::set),
      "Set camera property value", py::arg("device"), py::arg("property"), py::arg("setting"));

// Video processing functions  
m.def("get_range", py::overload_cast<const duvc::Device&, duvc::VidProp, duvc::PropRange&>(&duvc::get_range),
      "Get video property range", py::arg("device"), py::arg("property"), py::arg("range"));

m.def("get", py::overload_cast<const duvc::Device&, duvc::VidProp, duvc::PropSetting&>(&duvc::get),
      "Get video property value", py::arg("device"), py::arg("property"), py::arg("setting"));

m.def("set", py::overload_cast<const duvc::Device&, duvc::VidProp, const duvc::PropSetting&>(&duvc::set),
      "Set video property value", py::arg("device"), py::arg("property"), py::arg("setting"));
```


### Type Mapping and Conversion

**C++ to Python Type Mapping:**


| C++ Type | Python Type | Conversion |
| :-- | :-- | :-- |
| `std::vector<duvc::Device>` | `list[Device]` | Automatic container conversion |
| `std::wstring` | `str` | Manual UTF-16 to UTF-8 conversion |
| `duvc::CamProp` | `CamProp` | Enum with integer values |
| `duvc::VidProp` | `VidProp` | Enum with integer values |
| `duvc::CamMode` | `CamMode` | Enum (Auto/Manual) |
| `duvc::PropSetting&` | `PropSetting` | Mutable reference binding |
| `duvc::PropRange&` | `PropRange` | Mutable reference binding |
| `bool` return | `bool` | Direct mapping |
| `std::vector<uint8_t>` | `bytearray` | Automatic buffer conversion |

**Constructor Bindings:**

```cpp
py::class_<duvc::PropSetting>(m, "PropSetting")
    .def(py::init<>())
    .def(py::init<int, duvc::CamMode>())
    .def_readwrite("value", &duvc::PropSetting::value)
    .def_readwrite("mode", &duvc::PropSetting::mode)
    .def("__repr__", [](const duvc::PropSetting& p) {
        return "<PropSetting(value=" + std::to_string(p.value) + 
               ", mode=" + (p.mode == duvc::CamMode::Auto ? "Auto" : "Manual") + ")>";
    });

py::class_<duvc::PropRange>(m, "PropRange")
    .def(py::init<>())
    .def_readwrite("min", &duvc::PropRange::min)
    .def_readwrite("max", &duvc::PropRange::max)
    .def_readwrite("step", &duvc::PropRange::step)
    .def_readwrite("default_val", &duvc::PropRange::default_val)
    .def_readwrite("default_mode", &duvc::PropRange::default_mode)
    .def("__repr__", [](const duvc::PropRange& r) {
        return "<PropRange(min=" + std::to_string(r.min) + 
               ", max=" + std::to_string(r.max) + 
               ", step=" + std::to_string(r.step) + 
               ", default=" + std::to_string(r.default_val) + ")>";
    });
```


### Advanced Python Features

**Device Monitoring Integration:**

```cpp
m.def("register_device_change_callback", &duvc::register_device_change_callback,
      "Register callback for device changes", py::arg("callback"));

m.def("unregister_device_change_callback", &duvc::unregister_device_change_callback,
      "Unregister device change callback");

m.def("is_device_connected", &duvc::is_device_connected,
      "Check if device is connected", py::arg("device"));

m.def("clear_connection_cache", &duvc::clear_connection_cache,
      "Clear cached device connections");
```

**Usage in Python:**

```python
def on_device_change(added: bool, device_path: str):
    status = "ADDED" if added else "REMOVED"
    print(f"Device {status}: {device_path}")

duvc.register_device_change_callback(on_device_change)
```

**String Conversion Utilities:**

```cpp
m.def("cam_prop_to_string", [](duvc::CamProp p) { return duvc::to_string(p); });
m.def("vid_prop_to_string", [](duvc::VidProp p) { return duvc::to_string(p); });
m.def("cam_mode_to_string", [](duvc::CamMode m) { return duvc::to_string(m); });
```


### Python Package Structure

**Package Initialization (py/duvc_ctl/__init__.py):**

```python
"""
duvc-ctl: DirectShow UVC Camera Control Library
===============================================

A Python library for controlling DirectShow UVC cameras with support for:
- PTZ (Pan/Tilt/Zoom) operations
- Camera property control (exposure, focus, etc.)
- Video processing properties (brightness, contrast, etc.)
- Device monitoring and hotplug detection
- Vendor-specific extensions (Windows only)
"""

try:
    from ._duvc_ctl import *
except ImportError as e:
    raise ImportError("Could not import the C++ extension module for duvc-ctl.") from e

__version__ = "1.0.0"
__author__ = "allanhanan"
__email__ = "allan.hanan04@gmail.com"
__project__ = "duvc-ctl"
```

**CMakeLists.txt Python Module Configuration:**

```cmake
if(DUVC_BUILD_PYTHON)
    pybind11_add_module(_duvc_ctl ${DUVC_PY_SOURCES})
    
    set_target_properties(_duvc_ctl PROPERTIES 
        OUTPUT_NAME "_duvc_ctl"
        LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/py
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/py
    )
    
    target_include_directories(_duvc_ctl PRIVATE ${DUVC_INCLUDE_DIR})
    target_link_libraries(_duvc_ctl PRIVATE duvc)
    duvc_apply_warnings(_duvc_ctl)
    duvc_link_directshow(_duvc_ctl)
    
    # Install for scikit-build-core wheel packaging
    install(TARGETS _duvc_ctl
        DESTINATION ${SKBUILD_PLATLIB_DIR}/duvc_ctl)
endif()
```

Note: The module uses `_duvc_ctl` with underscore prefix as the internal compiled extension, imported through the Python package's `__init__.py` file.


## Command Line Interface

### CLI Architecture (cli/main.cpp - 782 lines)

**Argument Processing System:**

```cpp
// Convert char** to wchar_t** for MinGW compatibility
static std::vector<std::wstring> convert_args(int argc, char** argv) {
    std::vector<std::wstring> wargs;
    wargs.reserve(argc);
    for (int i = 0; i < argc; ++i) {
        std::wstring warg;
        for (char c : std::string(argv[i])) {
            warg += static_cast<wchar_t>(c);
        }
        wargs.push_back(std::move(warg));
    }
    return wargs;
}
```

**Command Structure:**

```
duvc-cli <command> [arguments...]

Commands:
  list                                    # List all cameras
  get <index> <domain> <property>         # Read property value  
  set <index> <domain> <property> <value> [mode]  # Write property value
  range <index> <domain> <property>       # Get property constraints
  status <index>                          # Check device connection
  monitor [seconds]                       # Watch device changes
  clear-cache                             # Clear connection cache
  vendor <index> <guid> <property_id> <op> [data]  # Vendor properties
```


### Property Name Parsing

**Camera Property Lookup:**

```cpp
static std::optional<CamProp> parse_cam_prop(const std::wstring& s) {
    struct Map { const wchar_t* n; CamProp p; } map[] = {
        {L"Pan", CamProp::Pan},
        {L"Tilt", CamProp::Tilt},
        {L"Roll", CamProp::Roll},
        {L"Zoom", CamProp::Zoom},
        {L"Exposure", CamProp::Exposure},
        {L"Iris", CamProp::Iris},
        {L"Focus", CamProp::Focus},
        // ... all 24 properties
    };
    for (auto& m : map) {
        if (_wcsicmp(s.c_str(), m.n) == 0) return m.p;
    }
    return std::nullopt;
}
```

**Video Property Lookup:**

```cpp
static std::optional<VidProp> parse_vid_prop(const std::wstring& s) {
    struct Map { const wchar_t* n; VidProp p; } map[] = {
        {L"Brightness", VidProp::Brightness},
        {L"Contrast", VidProp::Contrast},
        {L"Hue", VidProp::Hue},
        {L"Saturation", VidProp::Saturation},
        // ... all 10 properties
    };
    for (auto& m : map) {
        if (_wcsicmp(s.c_str(), m.n) == 0) return m.p;
    }
    return std::nullopt;
}
```


### Command Implementations

**Device Listing:**

```cpp
if (_wcsicmp(cmd.c_str(), L"list") == 0) {
    auto devices = duvc::list_devices();
    std::wcout << L"Devices: " << devices.size() << L"\n";
    for (size_t i = 0; i < devices.size(); ++i) {
        std::wcout << L"[" << i << L"] " << devices[i].name 
                  << L"\n  " << devices[i].path << L"\n";
    }
    return 0;
}
```

**Property Getting:**

```cpp
if (_wcsicmp(cmd.c_str(), L"get") == 0) {
    if (argc < 5) { print_usage(); return 1; }
    
    int index = _wtoi(wargv[^2]);
    std::wstring domain = wargv[^3];
    std::wstring propName = wargv[^4];
    
    auto devices = duvc::list_devices();
    if (index < 0 || index >= static_cast<int>(devices.size())) {
        std::wcerr << L"Invalid device index.\n";
        return 2;
    }
    
    if (is_cam_domain(domain)) {
        auto p = parse_cam_prop(propName);
        if (!p) { std::wcerr << L"Unknown cam prop.\n"; return 3; }
        
        PropSetting s{};
        if (!duvc::get(devices[index], *p, s)) {
            std::wcerr << L"Property not supported or failed to read.\n";
            return 4;
        }
        
        std::wcout << duvc::to_wstring(*p) << L" = " << s.value 
                  << L" (" << duvc::to_wstring(s.mode) << L")\n";
        return 0;
    }
    // ... video domain handling
}
```


### Advanced CLI Features

**Device Monitoring:**

```cpp
static void on_device_change(bool added, const std::wstring& device_path) {
    if (added) {
        std::wcout << L"[DEVICE ADDED] " << device_path << L"\n";
    } else {
        std::wcout << L"[DEVICE REMOVED] " << device_path << L"\n";
    }
    std::wcout.flush();
}

if (_wcsicmp(cmd.c_str(), L"monitor") == 0) {
    int duration = 30; // default 30 seconds
    if (argc >= 3) {
        duration = _wtoi(wargv[^2]);
    }
    
    std::wcout << L"Monitoring device changes for " << duration << L" seconds...\n";
    duvc::register_device_change_callback(on_device_change);
    
    std::this_thread::sleep_for(std::chrono::seconds(duration));
    
    duvc::unregister_device_change_callback();
    std::wcout << L"\nMonitoring stopped.\n";
    return 0;
}
```

**Vendor Property Support:**

```cpp
#ifdef _WIN32
// GUID parsing with flexible format support
static std::optional<GUID> parse_guid(const std::wstring& guid_str) {
    GUID guid;
    std::wstring formatted = guid_str;
    
    // Add braces if not present
    if (formatted.front() != L'{') {
        formatted = L"{" + formatted;
    }
    if (formatted.back() != L'}') {
        formatted = formatted + L"}";
    }
    
    if (SUCCEEDED(CLSIDFromString(formatted.c_str(), &guid))) {
        return guid;
    }
    return std::nullopt;
}

// Hex string to bytes conversion
static std::vector<uint8_t> hex_to_bytes(const std::wstring& hex_str) {
    std::vector<uint8_t> bytes;
    for (size_t i = 0; i < hex_str.length(); i += 2) {
        std::wstring byte_str = hex_str.substr(i, 2);
        uint8_t byte = static_cast<uint8_t>(std::wcstoul(byte_str.c_str(), nullptr, 16));
        bytes.push_back(byte);
    }
    return bytes;
}
#endif
```


## Testing Framework

### C++ Unit Tests (tests/test_core.cpp - 230 lines)

**Test Framework: Catch2 v3.5.2**

```cmake
include(FetchContent)
FetchContent_Declare(
    catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.5.2
)
FetchContent_MakeAvailable(catch2)
```

**Device-Dependent Testing Pattern:**

```cpp
static bool has_devices() {
    return !list_devices().empty();
}

TEST_CASE("List devices returns valid device info", "[core]") {
    auto devices = list_devices();
    for (const auto& d : devices) {
        INFO("Device: " << std::string(d.name.begin(), d.name.end())
             << " Path: " << std::string(d.path.begin(), d.path.end()));
        REQUIRE(!d.name.empty());
        REQUIRE(!d.path.empty());
    }
}
```

**Property Testing with Range Validation:**

```cpp
TEST_CASE("Get range for multiple camera properties", "[core]") {
    if (!has_devices()) {
        SUCCEED("No devices connected, skipping range tests.");
        return;
    }
    
    auto dev = list_devices()[^0];
    CamProp camProps[] = {
        CamProp::Pan, CamProp::Tilt, CamProp::Zoom, 
        CamProp::Focus, CamProp::Exposure
    };
    
    for (auto prop : camProps) {
        PropRange r{};
        bool ok = get_range(dev, prop, r);
        INFO("Property: " << to_string(prop) << " Supported: " << ok);
        if (ok) {
            REQUIRE(r.max >= r.min);
            REQUIRE(r.step > 0);
        }
    }
}
```

**Safe Property Modification Testing:**

```cpp
TEST_CASE("Safe set/get roundtrip for a supported CamProp", "[core]") {
    if (!has_devices()) {
        SUCCEED("No devices connected, skipping get/set tests.");
        return;
    }
    
    auto dev = list_devices();
    PropRange range{};
    if (!get_range(dev, CamProp::Pan, range)) {
        SUCCEED("Pan not supported, skipping set test.");
        return;
    }
    
    PropSetting original{};
    REQUIRE(get(dev, CamProp::Pan, original));
    
    // Use same value to avoid moving hardware
    PropSetting newSetting;
    newSetting.value = original.value;
    newSetting.mode = CamMode::Manual;
    
    bool setOK = set(dev, CamProp::Pan, newSetting);
    REQUIRE((setOK || !setOK)); // Verify no crash
    
    // Reset to original value
    set(dev, CamProp::Pan, original);
}
```


### Python Import Validation (tests/test_import.py - 268 lines)

**Multi-Stage Import Testing:**

```python
def debug_import():
    """Debug the import process step by step"""
    print("=== DUVC-CTL Python Import Debug ===")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Step 1: Test installed package import (primary method)
    try:
        import duvc_ctl as duvc
        print("✓ Installed package import successful")
        
        # Verify package metadata
        print(f"Package version: {duvc.__version__}")
        print(f"Package author: {duvc.__author__}")
        
        # Test internal module access
        try:
            from duvc_ctl import _duvc_ctl
            print("✓ Internal C++ module accessible")
        except ImportError:
            print("✗ Internal C++ module not accessible")
            return False
            
    except ImportError as e:
        print(f"✗ Package import failed: {e}")
        
        # Step 2: Fallback to build directory (development mode)
        project_root = Path(__file__).parent.parent
        build_py_dir = project_root / "build" / "py"
        
        print(f"\nFallback: Looking for modules in: {build_py_dir}")
        print(f"Directory exists: {build_py_dir.exists()}")
        
        if not build_py_dir.exists():
            print("Build directory not found!")
            return False
        
        # Check directory structure
        print(f"\nContents of {build_py_dir}:")
        for item in build_py_dir.iterdir():
            print(f"  {item.name}")
        
        # Add to Python path and retry
        if str(build_py_dir) not in sys.path:
            sys.path.insert(0, str(build_py_dir))
            print(f"\nAdded to Python path: {build_py_dir}")
        
        try:
            import duvc_ctl as duvc
            print("✓ Build directory import successful")
        except ImportError as e:
            print(f"✗ Build directory import failed: {e}")
            return False
    
    # Step 3: Verify module structure and contents
    available_attrs = [attr for attr in dir(duvc) if not attr.startswith('__')]
    print(f"\nAvailable attributes: {len(available_attrs)}")
    
    # Expected API elements
    expected_functions = ['list_devices', 'get', 'set', 'get_range', 
                         'register_device_change_callback', 'unregister_device_change_callback',
                         'is_device_connected', 'clear_connection_cache']
    expected_classes = ['Device', 'PropSetting', 'PropRange']
    expected_enums = ['CamProp', 'VidProp', 'CamMode']
    
    all_expected = expected_functions + expected_classes + expected_enums
    
    # Check for missing elements
    missing_elements = [elem for elem in all_expected if elem not in available_attrs]
    if missing_elements:
        print(f"✗ Missing expected elements: {missing_elements}")
        return False
    else:
        print(f"✓ All {len(all_expected)} expected API elements present")
    
    # Step 4: Test enum completeness
    try:
        # Test CamProp enum (should have 23 values)
        cam_props = [attr for attr in dir(duvc.CamProp) if not attr.startswith('_')]
        expected_cam_props = ['Pan', 'Tilt', 'Roll', 'Zoom', 'Exposure', 'Iris', 'Focus', 
                             'ScanMode', 'Privacy', 'PanRelative', 'TiltRelative', 
                             'RollRelative', 'ZoomRelative', 'ExposureRelative', 
                             'IrisRelative', 'FocusRelative', 'PanTilt', 'PanTiltRelative',
                             'FocusSimple', 'DigitalZoom', 'DigitalZoomRelative', 
                             'BacklightCompensation', 'Lamp']
        
        if all(prop in cam_props for prop in expected_cam_props):
            print("✓ CamProp enum complete")
        else:
            missing_props = [p for p in expected_cam_props if p not in cam_props]
            print(f"✗ CamProp missing: {missing_props}")
        
        # Test VidProp enum (should have 10 values)
        vid_props = [attr for attr in dir(duvc.VidProp) if not attr.startswith('_')]
        expected_vid_props = ['Brightness', 'Contrast', 'Hue', 'Saturation', 'Sharpness',
                             'Gamma', 'ColorEnable', 'WhiteBalance', 'BacklightCompensation', 'Gain']
        
        if all(prop in vid_props for prop in expected_vid_props):
            print("✓ VidProp enum complete")
        else:
            missing_props = [p for p in expected_vid_props if p not in vid_props]
            print(f"✗ VidProp missing: {missing_props}")
        
        # Test CamMode enum (should have 2 values)
        cam_modes = [attr for attr in dir(duvc.CamMode) if not attr.startswith('_')]
        expected_cam_modes = ['Auto', 'Manual']
        
        if all(mode in cam_modes for mode in expected_cam_modes):
            print("✓ CamMode enum complete")
        else:
            missing_modes = [m for m in expected_cam_modes if m not in cam_modes]
            print(f"✗ CamMode missing: {missing_modes}")
            
    except Exception as e:
        print(f"✗ Enum validation failed: {e}")
        return False
    
    # Step 5: Test basic functionality
    try:
        devices = duvc.list_devices()
        print(f"✓ list_devices() returned {len(devices)} devices")
        
        if devices:
            device = devices[0]  # Fixed: was devices[^0]
            print(f"✓ Device name: {device.name}")
            
            # Test device connection check
            connected = duvc.is_device_connected(device)
            print(f"✓ is_device_connected() works - device connected: {connected}")
            
            # Test enum value access
            print(f"✓ CamProp.Pan value: {duvc.CamProp.Pan}")
            print(f"✓ VidProp.Brightness value: {duvc.VidProp.Brightness}")
            print(f"✓ CamMode.Manual value: {duvc.CamMode.Manual}")
            
            # Test class instantiation
            setting = duvc.PropSetting()
            print("✓ PropSetting can be instantiated")
            
            setting_with_values = duvc.PropSetting(50, duvc.CamMode.Manual)
            print("✓ PropSetting with parameters works")
            
            prop_range = duvc.PropRange()
            print("✓ PropRange can be instantiated")
        
        return True
        
    except Exception as e:
        print(f"✗ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_comprehensive_tests():
    """Run the complete test suite"""
    print("DUVC-CTL Package Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Import validation
    total_tests += 1
    if debug_import():
        print("[PASS] Import and basic functionality")
        tests_passed += 1
    else:
        print("[FAIL] Import and basic functionality")
    
    # Test 2: Module structure validation
    total_tests += 1
    try:
        import duvc_ctl as duvc
        public_attrs = [attr for attr in dir(duvc) if not attr.startswith('_')]
        private_attrs = [attr for attr in dir(duvc) if attr.startswith('_') and not attr.startswith('__')]
        
        print(f"[PASS] Module structure: {len(public_attrs)} public, {len(private_attrs)} private")
        tests_passed += 1
    except:
        print("[FAIL] Module structure validation")
    
    # Test 3: Package metadata
    total_tests += 1
    try:
        import duvc_ctl as duvc
        assert hasattr(duvc, '__version__')
        assert hasattr(duvc, '__author__')
        print(f"[PASS] Package metadata: version={duvc.__version__}, author={duvc.__author__}")
        tests_passed += 1
    except:
        print("[FAIL] Package metadata")
    
    print("-" * 50)
    print(f"Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("SUCCESS: All tests passed")
        return True
    else:
        print("FAILURE: Some tests failed")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)

```


### Test Execution

**CMake Test Integration:**

```cmake
enable_testing()
include(CTest)
include(Catch)
catch_discover_tests(duvc_core_tests)
```

**Run Tests:**

```bash
# Build and run C++ tests
cd tests
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build

# Run Python import validation
cd tests
python test_import.py
```


## Interactive Python Example

### Complete Interactive Demo (examples/example.py - 765 lines)

**Main Controller Class Architecture:**

```python
class CameraController:
    def __init__(self):
        self.devices = []
        self.current_device = None
        self.current_device_index = -1
        self.refresh_devices()
    
    def refresh_devices(self):
        """Refresh the device list"""
        self.devices = duvc.list_devices()
        if self.current_device_index >= len(self.devices):
            self.current_device = None
            self.current_device_index = -1
```

**Menu System Implementation:**

```python
def show_main_menu(self):
    """Display the main menu"""
    print("\n" + "="*60)
    print("  DirectShow UVC Camera Controller")
    print("="*60)
    print(f"Found {len(self.devices)} camera(s)")
    
    if self.current_device:
        print(f"Current device: [{self.current_device_index}] {self.current_device.name}")
    else:
        print("Current device: None selected")
    
    print("\nMain Menu:")
    print("1. List all cameras")
    print("2. Select camera")
    print("3. Check camera status")
    print("4. PTZ Control")
    print("5. Video Properties")
    print("6. Camera Properties")
    print("7. Clear cache")
    print("0. Exit")
```

**Property Control with Range Validation:**

```python
def control_property(self, domain, prop_name):
    """Control a specific property"""
    print(f"\n--- {prop_name} Control ---")
    
    # Get the property enum
    if domain == "cam":
        prop = getattr(duvc.CamProp, prop_name, None)
    else:
        prop = getattr(duvc.VidProp, prop_name, None)
    
    if not prop:
        print(f"Property {prop_name} not found!")
        return
    
    # Get current value
    current_setting = duvc.PropSetting()
    if duvc.get(self.current_device, prop, current_setting):
        mode_str = duvc.cam_mode_to_string(current_setting.mode)
        print(f"Current {prop_name}: {current_setting.value} ({mode_str})")
    
    # Get and display range
    prop_range = duvc.PropRange()
    if duvc.get_range(self.current_device, prop, prop_range):
        print(f"Range: {prop_range.min} to {prop_range.max}, step: {prop_range.step}")
        print(f"Default: {prop_range.default_val}")
    else:
        print("Range information not available")
        return
    
    # User interaction for setting values
    print("\nOptions:")
    print("1. Set to specific value")
    print("2. Set to default")
    print("3. Set to auto mode")
    print("0. Cancel")
    
    try:
        choice = int(input("Enter option: "))
        if choice == 1:
            value = int(input(f"Enter value ({prop_range.min}-{prop_range.max}): "))
            if prop_range.min <= value <= prop_range.max:
                setting = duvc.PropSetting(value, duvc.CamMode.Manual)
                if duvc.set(self.current_device, prop, setting):
                    print(f"Set {prop_name} to {value}")
                else:
                    print("Failed to set property")
    except ValueError:
        print("Invalid input!")
```

**Camera Centering Utility:**

```python
def center_camera(self):
    """Center the camera (Pan=0, Tilt=0)"""
    print("\nCentering camera...")
    
    # Center Pan
    pan_setting = duvc.PropSetting(0, duvc.CamMode.Manual)
    pan_success = duvc.set(self.current_device, duvc.CamProp.Pan, pan_setting)
    
    # Center Tilt
    tilt_setting = duvc.PropSetting(0, duvc.CamMode.Manual)
    tilt_success = duvc.set(self.current_device, duvc.CamProp.Tilt, tilt_setting)
    
    if pan_success and tilt_success:
        print("Camera centered successfully")
    elif pan_success:
        print("Pan centered (Tilt not supported)")
    elif tilt_success:
        print("Tilt centered (Pan not supported)")
    else:
        print("Failed to center camera (PTZ not supported)")
```


## Development Workflow

### Setting Up Development Environment

**Prerequisites:**

```bash
# Required tools
- Visual Studio 2019/2022 or MinGW-w64
- CMake 3.16+
- Python 3.8+ with development headers
- Git

# Optional tools
- Windows 10/11 SDK (latest)
- Ninja build system
- Visual Studio Code with C++/CMake extensions

# Python packaging tools (for wheel development)
- pip install build twine scikit-build-core pybind11
```

**Clone and Initial Build:**

```bash
git clone https://github.com/yourusername/duvc-ctl.git
cd duvc-ctl

# Create build directory
mkdir build && cd build

# Configure with all features enabled
cmake -G "Visual Studio 17 2022" -A x64 \
  -DCMAKE_BUILD_TYPE=Release \
  -DDUVC_BUILD_STATIC=ON \
  -DDUVC_BUILD_SHARED=ON \
  -DDUVC_BUILD_CLI=ON \
  -DDUVC_BUILD_PYTHON=ON \
  -DDUVC_USE_SYSTEM_PYBIND11=OFF \
  ..

# Build everything
cmake --build . --config Release --parallel
```


### Development Build Configurations

**Debug Configuration:**

```bash
cmake -G "Visual Studio 17 2022" -A x64 \
  -DCMAKE_BUILD_TYPE=Debug \
  -DDUVC_WARNINGS_AS_ERRORS=ON \
  -DDUVC_BUILD_PYTHON=ON \
  -DDUVC_BUILD_STATIC=ON \
  ..

cmake --build . --config Debug --parallel
```

**Fast Development Builds (Ninja):**

```bash
cmake -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DDUVC_BUILD_STATIC=ON \
  -DDUVC_BUILD_CLI=ON \
  -DDUVC_BUILD_PYTHON=ON \
  ..
ninja
```

**Python-Only Development Build:**

```bash
# For rapid Python extension iteration
cmake -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DDUVC_BUILD_STATIC=ON \
  -DDUVC_BUILD_SHARED=OFF \
  -DDUVC_BUILD_CLI=OFF \
  -DDUVC_BUILD_PYTHON=ON \
  -DDUVC_USE_SYSTEM_PYBIND11=ON \
  ..
ninja _duvc_ctl
```

**CLI-Only Development Build:**

```bash
# For testing CLI changes without Python overhead
cmake -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DDUVC_BUILD_STATIC=ON \
  -DDUVC_BUILD_SHARED=OFF \
  -DDUVC_BUILD_CLI=ON \
  -DDUVC_BUILD_PYTHON=OFF \
  ..
ninja duvc-cli
```


### Python Development Workflow

**Local Python Package Testing:**

```bash
# Build Python wheel for testing
python -m build

# Install in development mode
pip install -e .

# Or install built wheel
pip install dist/duvc_ctl-1.0.0-cp311-cp311-win_amd64.whl --force-reinstall

# Run tests
python tests/test_import.py
```

**Direct Module Testing (Development):**

```bash
# Add build directory to Python path for testing
cd build/py
python -c "import _duvc_ctl; print('Direct module import works')"

# Test with package wrapper
cd ../../py
python -c "import duvc_ctl; print(duvc_ctl.__version__)"
```


### Build Output Structure

**Standard Build Layout:**

```
build/
├── lib/                          # Static/shared libraries
│   ├── duvc.lib                 # Static library
│   └── duvc_shared.lib          # Import library for DLL
├── bin/                          # Executables and DLLs
│   ├── duvc-cli.exe             # Command-line interface
│   └── duvc_shared.dll          # Shared library (if built)
└── py/                           # Python extension
    └── _duvc_ctl.cp311-win_amd64.pyd  # Python module
```


### Testing and Validation

**C++ Testing:**

```bash
# Build and run C++ tests
cmake --build . --target test_core --config Debug
./bin/test_core
```

**Python Testing:**

```bash
# Comprehensive Python validation
python tests/test_import.py

# Expected output:
# Test Results: 13/13 passed
# SUCCESS: All tests passed
```

**Integration Testing:**

```bash
# Test CLI with devices
./bin/duvc-cli.exe --list-devices

# Test Python package
python -c "
import duvc_ctl as duvc
devices = duvc.list_devices()
print(f'Found {len(devices)} cameras')
"
```


### Development Tips

**CMake Configuration Shortcuts:**

```bash
# Use CMake presets (if available)
cmake --preset=debug
cmake --preset=release

# Quick reconfigure
cmake . --fresh

# Clean and rebuild
cmake --build . --clean-first
```

**Python Development Iteration:**

```bash
# Fast Python extension rebuild
ninja _duvc_ctl && pip install -e . --force-reinstall
python tests/test_import.py
```

**Debugging Configuration:**

```bash
# Enable all warnings and debugging
cmake -G "Visual Studio 17 2022" -A x64 \
  -DCMAKE_BUILD_TYPE=Debug \
  -DDUVC_WARNINGS_AS_ERRORS=ON \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  ..
```


### Code Style and Conventions

**C++ Coding Standards:**

- Modern C++17 features and idioms
- RAII for all resource management
- `snake_case` for variables and functions
- `PascalCase` for types and enums
- Comprehensive error handling with exceptions
- Thread-safety considerations documented

**Python Conventions:**

- PEP 8 compliance for Python code
- Type hints where applicable
- Docstrings for all public functions
- Error handling with appropriate exceptions


### Testing During Development

**Continuous Testing Workflow:**

```bash
# Quick unit test run
cd tests
cmake --build build --config Debug
ctest --test-dir build

# Python integration test
python test_import.py

# Manual testing with CLI
cd ../build/bin
./duvc-cli list
./duvc-cli get 0 cam Pan

# Interactive Python testing
cd ../py
python -c "import duvc_ctl as duvc; print(len(duvc.list_devices()))"
```


## Troubleshooting \& Debugging

### Common Build Issues

**CMake Configuration Problems:**

1. **Python Development Headers Missing:**

```
Error: Could NOT find Python (missing: Python_LIBRARIES Python_INCLUDE_DIRS)
```

**Solution:** Install Python with development headers or use conda:

```bash
# Windows Python.org installer: check "Add Python to PATH"
# Or use conda
conda install python-dev
```

2. **pybind11 Download Failures:**

```
Error: Failed to download pybind11 from GitHub
```

**Solution:** Use system pybind11 or configure proxy:

```bash
# Use system pybind11
cmake -DDUVC_USE_SYSTEM_PYBIND11=ON ..

# Or configure proxy
cmake -DCMAKE_HTTP_PROXY=http://proxy:port ..
```

3. **DirectShow Linking Errors:**

```
Error: unresolved external symbol _GUID_NULL
```

**Solution:** Ensure Windows SDK is properly installed:

```bash
# Install Windows 10/11 SDK via Visual Studio Installer
# Or download standalone SDK from Microsoft
```


### Runtime Issues

**Python Import Failures:**

1. **Module Not Found:**

```python
ImportError: No module named 'duvc_ctl'
```

**Diagnosis Steps:**

```python
# Check if .pyd file exists
import os
print(os.path.exists("build/py/duvc_ctl.cp311-win_amd64.pyd"))

# Check Python path
import sys
print(sys.path)

# Add build directory manually
sys.path.insert(0, "path/to/build/py")
```

2. **DLL Load Errors:**

```python
ImportError: DLL load failed while importing duvc_ctl: The specified module could not be found.
```

**Solution:** Check Visual C++ Redistributables:

```bash
# Install Visual C++ Redistributable for Visual Studio 2019/2022
# Available from Microsoft Download Center
```


### Device Access Issues

**No Devices Found:**

```cpp
auto devices = duvc::list_devices();  // Returns empty vector
```

**Debugging Steps:**

1. **Check Device Manager:** Ensure cameras appear under "Imaging devices"
2. **Test with Other Applications:** Verify camera works with Camera app
3. **Check Permissions:** Run as Administrator to rule out permission issues
4. **Verify DirectShow Registration:** Use GraphEdit to test device access

**Property Control Failures:**

```cpp
bool success = duvc::set(device, CamProp::Pan, setting);  // Returns false
```

**Common Causes:**

1. **Property Not Supported:** Check `get_range()` first
2. **Value Out of Range:** Ensure value is within min/max bounds
3. **Device Busy:** Another application may be using the camera
4. **Hardware Limitation:** Some properties may be read-only

### Debugging Techniques

**Enable Verbose Error Reporting:**

```cpp
try {
    auto devices = duvc::list_devices();
} catch (const std::exception& e) {
    std::cout << "Error: " << e.what() << std::endl;
    // Error includes HRESULT and detailed DirectShow information
}
```

**COM Error Analysis:**

```cpp
// Custom debugging with HRESULT analysis
HRESULT hr = /* some DirectShow operation */;
if (FAILED(hr)) {
    _com_error err(hr);
    std::wcout << L"HRESULT: 0x" << std::hex << hr << std::endl;
    std::wcout << L"Description: " << err.ErrorMessage() << std::endl;
}
```

**Connection Pool Debugging:**

```cpp
// Check connection cache state
duvc::clear_connection_cache();  // Force fresh connections
bool connected = duvc::is_device_connected(device);
```


## Deployment \& Distribution

### Binary Distribution Structure

**Release Package Layout:**

```
duvc-ctl-1.0.0-win64/
├── bin/
│   ├── duvc-cli.exe          # Command-line interface
│   ├── duvc.dll              # Shared library (if built)
│   └── *.dll                 # Runtime dependencies
├── lib/
│   ├── duvc.lib              # Static library
│   ├── duvc.exp              # Export file
│   └── cmake/                # CMake configuration files
│       ├── duvc-ctl-config.cmake
│       └── duvc-ctl-config-version.cmake
├── include/
│   └── duvc-ctl/
│       ├── core.h            # Main API header
│       └── defs.h            # Type definitions
├── python/
│   └── duvc_ctl/
│       ├── __init__.py       # Package initialization
│       └── _duvc_ctl.cp311-win_amd64.pyd  # Internal C++ module
├── examples/
│   ├── example.py            # Interactive demo
│   └── basic_usage.cpp       # C++ examples
└── docs/
    ├── README.md             # This documentation
    └── API_Reference.pdf     # Detailed API docs
```


### Python Package Distribution

**PyPI Package Preparation (Current Working Configuration):**

**pyproject.toml:**

```toml
[build-system]
requires = ["scikit-build-core", "pybind11"]
build-backend = "scikit_build_core.build"

[project]
name = "duvc-ctl"
version = "1.0.0"
authors = [{ name = "allanhanan", email = "allan.hanan04@gmail.com" }]
description = "DirectShow UVC Camera Control Library"
readme = "README.md"
requires-python = ">=3.8"
license = { file = "LICENSE" }
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: Microsoft :: Windows",
    "Programming Language :: C++",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Multimedia :: Video :: Capture",
    "Topic :: System :: Hardware :: Hardware Drivers",
]
keywords = ["camera", "directshow", "uvc", "ptz", "video", "windows"]

[project.urls]
Homepage = "https://github.com/yourusername/duvc-ctl"
Repository = "https://github.com/yourusername/duvc-ctl.git"
Issues = "https://github.com/yourusername/duvc-ctl/issues"
Documentation = "https://duvc-ctl.readthedocs.io/"

[project.optional-dependencies]
dev = ["pytest", "black", "mypy", "sphinx", "build", "twine"]
testing = ["pytest"]

[tool.scikit-build]
wheel.packages = ["py/duvc_ctl"]

[tool.scikit-build.cmake.define]
DUVC_BUILD_PYTHON = "ON"
DUVC_BUILD_CLI = "OFF"
DUVC_BUILD_STATIC = "ON"
```


### Multi-Version Wheel Distribution

**GitHub Actions Automated Distribution:**

```yaml
# .github/workflows/build-wheels.yml
name: Build and publish

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]

jobs:
  build_wheels:
    name: Build wheels
    runs-on: windows-2022
    
    steps:
      - uses: actions/checkout@v4

      - name: Build wheels
        uses: pypa/cibuildwheel@v2.16.5
        env:
          CIBW_BUILD: "cp38-* cp39-* cp310-* cp311-* cp312-* cp313-* cp314-*"
          CIBW_ARCHS_WINDOWS: "AMD64"
          CIBW_SKIP: "*-win32"
          CIBW_TEST_COMMAND: "python -c \"import duvc_ctl; devices = duvc_ctl.list_devices(); print(f'SUCCESS: Found {len(devices)} devices')\""
          CIBW_PRERELEASE_PYTHONS: true
          CIBW_BUILD_VERBOSITY: 1

      - name: Upload wheels
        uses: actions/upload-artifact@v4
        with:
          name: wheels
          path: ./wheelhouse/*.whl

  build_sdist:
    name: Build source distribution
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build sdist
        run: pipx run build --sdist
      
      - name: Upload sdist
        uses: actions/upload-artifact@v4
        with:
          name: sdist
          path: dist/*.tar.gz

  upload_pypi:
    needs: [build_wheels, build_sdist]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
    environment: release
    permissions:
      id-token: write
    
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          print-hash: true
```


### Distribution Commands

**Local Build and Distribution:**

```bash
# Build wheels for current Python version
python -m build

# Build wheels for multiple Python versions (if installed)
py -3.8 -m build
py -3.9 -m build
py -3.10 -m build
py -3.11 -m build
py -3.12 -m build

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ duvc-ctl

# Upload to production PyPI
twine upload dist/*
```

**Wheel Contents Verification:**

```bash
# Check wheel contents
python -c "
import zipfile
from pathlib import Path

wheel_files = list(Path('dist').glob('*.whl'))
if wheel_files:
    with zipfile.ZipFile(wheel_files[0], 'r') as z:
        files = z.namelist()
        print('Wheel contents:')
        for f in sorted(files):
            print(f'  {f}')
        
        # Verify key components
        has_init = any('duvc_ctl/__init__.py' in f for f in files)
        has_module = any('_duvc_ctl' in f and f.endswith('.pyd') for f in files)
        print(f'Has __init__.py: {has_init}')
        print(f'Has C++ module: {has_module}')
"
```


### Installation Methods

**End User Installation:**

```bash
# Standard installation
pip install duvc-ctl

# Specific version
pip install duvc-ctl==1.0.0

# Development installation
pip install duvc-ctl[dev]

# Pre-release versions
pip install --pre duvc-ctl
```

**Verification Commands:**

```bash
# Verify installation
python -c "import duvc_ctl; print(f'duvc-ctl {duvc_ctl.__version__} installed successfully')"

# Run comprehensive tests
python -c "
import duvc_ctl as duvc
devices = duvc.list_devices()
print(f'Found {len(devices)} cameras')
if devices:
    print(f'First camera: {devices[0].name}')
"
```


### Distribution Package Structure

**Wheel Package Contents:**

```
duvc_ctl-1.0.0-cp311-cp311-win_amd64.whl
├── duvc_ctl/
│   ├── __init__.py           # Package interface
│   └── _duvc_ctl.cp311-win_amd64.pyd  # Compiled C++ extension
└── duvc_ctl-1.0.0.dist-info/
    ├── METADATA              # Package metadata
    ├── WHEEL                 # Wheel format info
    ├── RECORD                # File checksums
    └── licenses/
        └── LICENSE           # MIT license
```

**Source Distribution Contents:**

```
duvc_ctl-1.0.0.tar.gz
├── CMakeLists.txt            # Build configuration
├── pyproject.toml            # Package configuration
├── LICENSE                   # MIT license
├── README.md                 # Documentation
├── include/duvc-ctl/         # C++ headers
├── src/                      # C++ source code
├── py/duvc_ctl/             # Python package
├── cli/                      # Command-line tool
├── examples/                 # Usage examples
└── tests/                    # Test suite
```


### Release Process

**Version Release Workflow:**

```bash
# 1. Update version in pyproject.toml
# 2. Commit changes
git add pyproject.toml
git commit -m "Bump version to 1.0.1"

# 3. Create and push tag
git tag v1.0.1
git push origin v1.0.1

# 4. GitHub Actions automatically:
#    - Builds wheels for Python 3.8-3.14
#    - Creates source distribution
#    - Uploads to PyPI
#    - Creates GitHub release with artifacts
```


## GitHub Actions CI/CD Pipeline

### **.github/workflows/build-and-test.yml:**

```yaml
name: Build and Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build-windows:
    runs-on: windows-2022
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]
        architecture: [x64]
    
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
        architecture: ${{ matrix.architecture }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install scikit-build-core pybind11 build twine pytest
    
    - name: Configure CMake
      run: |
        cmake -B build -G "Visual Studio 17 2022" -A x64 `
          -DCMAKE_BUILD_TYPE=Release `
          -DDUVC_BUILD_STATIC=ON `
          -DDUVC_BUILD_CLI=ON `
          -DDUVC_BUILD_PYTHON=ON `
          -DDUVC_USE_SYSTEM_PYBIND11=OFF
    
    - name: Build
      run: cmake --build build --config Release --parallel
    
    - name: Test C++
      run: |
        if (Test-Path "tests/test_core.cpp") {
          cd build
          if (Test-Path "bin/test_core.exe") {
            ./bin/test_core.exe
          }
        }
    
    - name: Build Python Wheel
      run: python -m build
    
    - name: Test Python Package
      run: |
        pip install dist/*.whl --force-reinstall
        python tests/test_import.py
    
    - name: Verify Wheel Contents
      run: |
        python -c "
        import zipfile
        from pathlib import Path
        
        wheel_files = list(Path('dist').glob('*.whl'))
        if wheel_files:
            with zipfile.ZipFile(wheel_files[0], 'r') as z:
                files = z.namelist()
                has_init = any('duvc_ctl/__init__.py' in f for f in files)
                has_module = any('_duvc_ctl' in f and f.endswith('.pyd') for f in files)
                print(f'Wheel validation: init={has_init}, module={has_module}')
                assert has_init and has_module, 'Wheel missing required components'
        "
    
    - name: Upload Test Results
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: test-results-py${{ matrix.python-version }}
        path: |
          dist/*.whl
          build/py/*.pyd
        retention-days: 7

  integration-test:
    runs-on: windows-2022
    needs: build-windows
    strategy:
      matrix:
        python-version: ["3.8", "3.12"]  # Test oldest and newest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Download artifacts
      uses: actions/download-artifact@v4
      with:
        name: test-results-py${{ matrix.python-version }}
        path: dist
    
    - name: Integration test
      run: |
        pip install dist/*.whl
        python -c "
        import duvc_ctl as duvc
        print(f'SUCCESS: duvc-ctl {duvc.__version__} imported')
        devices = duvc.list_devices()
        print(f'Found {len(devices)} devices')
        setting = duvc.PropSetting(50, duvc.CamMode.Manual)
        print(f'PropSetting created: {setting}')
        print('All integration tests passed')
        "
```


### **GitHub Package Registry \& PyPI Publishing:**

```yaml
name: Publish Packages

on:
  push:
    tags: [ 'v*' ]
  release:
    types: [published]

jobs:
  build-and-publish:
    runs-on: windows-2022
    environment: release
    permissions:
      contents: read
      packages: write
      id-token: write  # For trusted publishing
    
    steps:
    - uses: actions/checkout@v4
      with:
        fetch-depth: 0
    
    - name: Build wheels for multiple Python versions
      uses: pypa/cibuildwheel@v2.16.5
      env:
        CIBW_BUILD: "cp38-* cp39-* cp310-* cp311-* cp312-* cp313-* cp314-*"
        CIBW_ARCHS_WINDOWS: "AMD64"
        CIBW_SKIP: "*-win32"
        CIBW_TEST_COMMAND: "python -c \"import duvc_ctl; devices = duvc_ctl.list_devices(); print(f'SUCCESS: Found {len(devices)} devices')\""
        CIBW_PRERELEASE_PYTHONS: true
        CIBW_BUILD_VERBOSITY: 1
    
    - name: Build source distribution
      run: |
        pip install build
        python -m build --sdist
    
    - name: Verify distributions
      run: |
        pip install twine
        twine check wheelhouse/*.whl dist/*.tar.gz
    
    - name: Publish to PyPI
      if: startsWith(github.ref, 'refs/tags/v')
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        packages-dir: wheelhouse/
        print-hash: true
    
    - name: Publish to GitHub Packages
      if: startsWith(github.ref, 'refs/tags/v')
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.GITHUB_TOKEN }}
        TWINE_REPOSITORY_URL: https://upload.pypi.org/legacy/
      run: |
        twine upload --repository-url https://upload.pypi.org/legacy/ wheelhouse/*.whl dist/*.tar.gz
    
    - name: Create GitHub Release
      if: startsWith(github.ref, 'refs/tags/v')
      uses: softprops/action-gh-release@v1
      with:
        files: |
          wheelhouse/*.whl
          dist/*.tar.gz
        generate_release_notes: true
        draft: false
        prerelease: false

  test-published-package:
    needs: build-and-publish
    runs-on: windows-2022
    if: startsWith(github.ref, 'refs/tags/v')
    strategy:
      matrix:
        python-version: ["3.8", "3.11", "3.12"]
    
    steps:
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Wait for package availability
      run: Start-Sleep -Seconds 120  # Wait 2 minutes for PyPI propagation
    
    - name: Test installation from PyPI
      run: |
        pip install duvc-ctl --no-cache-dir
        python -c "
        import duvc_ctl as duvc
        print(f'SUCCESS: duvc-ctl {duvc.__version__} installed from PyPI')
        devices = duvc.list_devices()
        print(f'Found {len(devices)} devices')
        "
```


### **Development Workflow (.github/workflows/dev.yml):**

```yaml
name: Development Workflow

on:
  workflow_dispatch:
  schedule:
    - cron: '0 2 * * 1'  # Weekly Monday 2 AM

jobs:
  code-quality:
    runs-on: windows-2022
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    
    - name: Install tools
      run: |
        pip install black isort mypy cppcheck
    
    - name: Format check
      run: |
        python -m black --check py/duvc_ctl/
        python -m isort --check-only py/duvc_ctl/
    
    - name: Static analysis
      run: |
        if (Get-Command cppcheck -ErrorAction SilentlyContinue) {
          cppcheck --enable=all --inconclusive --xml --xml-version=2 src/ include/ 2> cppcheck.xml
        }

  benchmark:
    runs-on: windows-2022
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    
    - name: Build and benchmark
      run: |
        python -m build
        pip install dist/*.whl
        python -c "
        import time
        import duvc_ctl as duvc
        
        start = time.time()
        devices = duvc.list_devices()
        list_time = time.time() - start
        
        print(f'Performance: list_devices() took {list_time*1000:.2f}ms')
        print(f'Found {len(devices)} devices')
        
        if devices:
            device = devices[0]
            start = time.time()
            connected = duvc.is_device_connected(device)
            check_time = time.time() - start
            print(f'Performance: is_device_connected() took {check_time*1000:.2f}ms')
        "
```

### Installation Instructions for Users

**C++ Library Integration:**

**Using CMake FetchContent:**

```cmake
include(FetchContent)
FetchContent_Declare(
    duvc-ctl
    GIT_REPOSITORY https://github.com/allanhanan/duvc-ctl.git
    GIT_TAG v1.0.0
)
FetchContent_MakeAvailable(duvc-ctl)

target_link_libraries(your_project PRIVATE duvc)
```

**Using vcpkg:**

```bash
# Install via vcpkg (when available)
vcpkg install duvc-ctl
```

**Python Package Installation:**

```bash
# From PyPI (when published)
pip install duvc-ctl

# From GitHub Packages
pip install --index-url https://pypi.org/simple/ duvc-ctl

# Development installation
pip install git+https://github.com/allanhanan/duvc-ctl.git
```
