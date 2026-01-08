## 1. Overview \& Getting Started


### 1.1 Introduction

duvc-ctl is a C++ library for controlling UVC cameras on Windows through the DirectShow API. The library exposes camera properties (pan, tilt, zoom, exposure, focus) and video properties (brightness, contrast, white balance) without requiring vendor-specific drivers or SDKs.

**Supported operations:**

- Device enumeration and connection
- Camera properties: pan, tilt, roll, zoom, exposure, iris, focus, scan mode, privacy, digital zoom, backlight compensation, lamp
- Video properties: brightness, contrast, hue, saturation, sharpness, gamma, color enable, white balance, backlight compensation, gain
- Hot-plug detection and device change notifications
- Vendor-specific extensions (Logitech cameras supported)

**Requirements:**

- Windows 7 SP1 or later (Windows 10/11 recommended)
- C++17 compiler: Visual Studio 2019/2022, or MinGW-w64 with GCC 9+
- CMake 3.16 or later
- DirectShow (included with Windows)

**DirectShow integration:**
The library wraps Windows DirectShow APIs including `ICreateDevEnum` (device enumeration), `IAMCameraControl` (PTZ and camera properties), `IAMVideoProcAmp` (video properties), and `IKsPropertySet` (vendor extensions).

***

### 1.2 Installation \& Setup

#### Prerequisites

- **Compiler**: Visual Studio 2019 or later, or MinGW-w64 with GCC 9+
- **CMake**: Version 3.16 or later
- **Windows SDK**: Included with Visual Studio
- **Git**: For cloning the repository


#### Build from source

```bash
git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl

# Configure
cmake -B build -G "Visual Studio 17 2022" -A x64

# Build
cmake --build build --config Release

# Install (optional)
cmake --install build --config Release
```


#### CMake configuration options

```bash
-DDUVC_BUILD_SHARED=ON   # Build shared library (default: ON)
-DDUVC_BUILD_STATIC=ON   # Build static library (default: ON)
-DDUVC_BUILD_C_API=ON    # Build C API for language bindings (default: ON)
-DDUVC_BUILD_CLI=ON      # Build command-line tool (default: ON)
-DDUVC_BUILD_TESTS=OFF   # Build test suite (default: OFF)
-DDUVC_BUILD_EXAMPLES=OFF # Build examples (default: OFF)
```

**Example with custom options:**

```bash
cmake -B build -G "Visual Studio 17 2022" -A x64 \
  -DDUVC_BUILD_SHARED=ON \
  -DDUVC_BUILD_STATIC=OFF \
  -DDUVC_BUILD_TESTS=ON
```


#### Integration into your project

**CMake find_package:**

```cmake
find_package(duvc-ctl REQUIRED)
target_link_libraries(your_target PRIVATE duvc-ctl::duvc-ctl)
```

**Manual integration:**

```cmake
target_include_directories(your_target PRIVATE path/to/duvc-ctl/include)
target_link_libraries(your_target PRIVATE path/to/duvc-ctl/lib/duvc-core.lib)
```

**Package managers** (Conan planned):

- vcpkg: `vcpkg install duvc-ctl`
- Conan: `conan install duvc-ctl/2.0.0`


#### Include headers

**Single convenience header (recommended):**

```cpp
#include <duvc-ctl/duvc.hpp>
```

**Selective headers:**

```cpp
#include <duvc-ctl/core/camera.h>
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/core/result.h>
#include <duvc-ctl/core/types.h>
```

### 1.3 Quick Start Examples

#### List devices

```cpp
#include <duvc-ctl/duvc.hpp>
#include <iostream>

int main() {
    auto platform = duvc::create_platform_interface();
    
    auto devices_result = platform->list_devices();
    if (!devices_result.is_ok()) {
        std::cerr << "Failed to list devices: " 
                  << devices_result.error().description() << "\n";
        return 1;
    }
    
    const auto& devices = devices_result.value();
    std::wcout << "Found " << devices.size() << " cameras\n";
    
    for (const auto& device : devices) {
        std::wcout << L"  - " << device.name << L"\n";
    }
    
    return 0;
}
```


#### Read property

```cpp
#include <duvc-ctl/duvc.hpp>
#include <iostream>

int main() {
    auto platform = duvc::create_platform_interface();
    
    // Get devices
    auto devices_result = platform->list_devices();
    if (!devices_result.is_ok() || devices_result.value().empty()) {
        std::cerr << "No cameras found\n";
        return 1;
    }
    
    const auto& devices = devices_result.value();
    
    // Create connection to first device
    auto connection_result = platform->create_connection(devices);
    if (!connection_result.is_ok()) {
        std::cerr << "Failed to connect: " 
                  << connection_result.error().description() << "\n";
        return 1;
    }
    
    auto connection = std::move(connection_result.value());
    
    // Get brightness
    auto brightness_result = connection->get_video_property(duvc::VidProp::Brightness);
    if (brightness_result.is_ok()) {
        const auto& setting = brightness_result.value();
        std::cout << "Brightness: " << setting.value 
                  << " (mode: " << (setting.mode == duvc::CamMode::Auto ? "auto" : "manual") 
                  << ")\n";
    } else {
        std::cerr << "Error reading brightness: " 
                  << brightness_result.error().description() << "\n";
    }
    
    return 0;
}
```


#### Set property with range validation

```cpp
#include <duvc-ctl/duvc.hpp>
#include <iostream>

int main() {
    auto platform = duvc::create_platform_interface();
    
    auto devices_result = platform->list_devices();
    if (!devices_result.is_ok() || devices_result.value().empty()) {
        return 1;
    }
    
    auto connection_result = platform->create_connection(devices_result.value());
    if (!connection_result.is_ok()) {
        return 1;
    }
    
    auto connection = std::move(connection_result.value());
    
    // Query range before setting
    auto range_result = connection->get_camera_property_range(duvc::CamProp::Pan);
    if (range_result.is_ok()) {
        const auto& range = range_result.value();
        std::cout << "Pan range: " << range.min << " to " << range.max 
                  << " (step: " << range.step << ")\n";
        
        // Clamp value to valid range
        int target_pan = 45;
        int clamped = range.clamp(target_pan);
        
        // Set property
        duvc::PropSetting setting{clamped, duvc::CamMode::Manual};
        auto set_result = connection->set_camera_property(duvc::CamProp::Pan, setting);
        
        if (set_result.is_ok()) {
            std::cout << "Pan set to " << clamped << "\n";
        } else {
            std::cerr << "Failed: " << set_result.error().description() << "\n";
        }
    }
    
    return 0;
}
```


#### Error handling

```cpp
#include <duvc-ctl/duvc.hpp>
#include <iostream>

int main() {
    auto platform = duvc::create_platform_interface();
    
    auto devices_result = platform->list_devices();
    if (devices_result.is_error()) {
        std::cerr << "Error: " << devices_result.error().description() << "\n";
        return 1;
    }
    
    if (devices_result.value().empty()) {
        std::cerr << "No devices found\n";
        return 1;
    }
    
    auto connection_result = platform->create_connection(devices_result.value());
    if (connection_result.is_error()) {
        const auto& error = connection_result.error();
        std::cerr << "Connection failed: " << error.description() << "\n";
        
        // Handle specific errors
        switch (error.code()) {
            case duvc::ErrorCode::DeviceNotFound:
                std::cerr << "Camera disconnected\n";
                break;
            case duvc::ErrorCode::DeviceBusy:
                std::cerr << "Camera in use by another application\n";
                break;
            case duvc::ErrorCode::PermissionDenied:
                std::cerr << "Check camera permissions in Windows settings\n";
                break;
            default:
                break;
        }
        return 1;
    }
    
    auto connection = std::move(connection_result.value());
    
    // Attempt property operation
    duvc::PropSetting setting{-5, duvc::CamMode::Manual};
    auto result = connection->set_camera_property(duvc::CamProp::Exposure, setting);
    
    if (result.is_error()) {
        const auto& error = result.error();
        
        if (error.code() == duvc::ErrorCode::PropertyNotSupported) {
            std::cerr << "Exposure not supported on this camera\n";
        } else if (error.code() == duvc::ErrorCode::InvalidValue) {
            std::cerr << "Value out of range\n";
        } else {
            std::cerr << "Error: " << error.description() << "\n";
        }
    }
    
    return 0;
}
```


#### Check device capabilities

```cpp
#include <duvc-ctl/duvc.hpp>
#include <duvc-ctl/core/capability.h>
#include <iostream>

int main() {
    auto platform = duvc::create_platform_interface();
    
    auto devices_result = platform->list_devices();
    if (!devices_result.is_ok() || devices_result.value().empty()) {
        return 1;
    }
    
    // Create capabilities object
    duvc::DeviceCapabilities caps(devices_result.value());
    
    // Check camera properties
    std::cout << "Supported camera properties:\n";
    for (const auto& prop : caps.supported_camera_properties()) {
        std::cout << "  - " << static_cast<int>(prop) << "\n";
    }
    
    // Check video properties
    std::cout << "\nSupported video properties:\n";
    for (const auto& prop : caps.supported_video_properties()) {
        std::cout << "  - " << static_cast<int>(prop) << "\n";
    }
    
    // Check specific property
    if (caps.supports_camera_property(duvc::CamProp::Pan)) {
        auto cap_result = caps.get_camera_capability(duvc::CamProp::Pan);
        if (cap_result.is_ok()) {
            const auto& cap = cap_result.value();
            std::cout << "\nPan capability:\n"
                      << "  Range: " << cap.range.min << " to " << cap.range.max << "\n"
                      << "  Step: " << cap.range.step << "\n"
                      << "  Default: " << cap.range.default_val << "\n"
                      << "  Auto mode: " << (cap.supports_auto() ? "yes" : "no") << "\n";
        }
    }
    
    return 0;
}
```

**Next:** See Section 2 for complete API reference.

