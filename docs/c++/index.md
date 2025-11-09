# duvc-ctl C++ API Documentation

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

**Package managers** (planned):

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

## 2. Core API - Public Headers

### 2.1 Device Discovery \& Management

**Header:** `<duvc-ctl/core/device.h>`

#### Device enumeration

```cpp
std::vector<Device> list_devices();
```

Enumerates all video input devices currently connected to the system. Returns a vector of `Device` objects containing name and path information for each camera.

The implementation uses DirectShow's `ICreateDevEnum` interface to query the `CLSID_VideoInputDeviceCategory`. Each discovered device is represented by an `IMoniker` which provides access to device metadata through `IPropertyBag`. The function reads the `FriendlyName` property (human-readable device name) and `DevicePath` property (unique system identifier).

Returns an empty vector when no cameras are present. Throws `std::runtime_error` if DirectShow initialization fails.

```cpp
auto cameras = duvc::list_devices();
std::wcout << "Found " << cameras.size() << " cameras\n";

for (const auto& cam : cameras) {
    std::wcout << "  - " << cam.name << "\n";
}
```

**Implementation notes:**

- Initializes COM apartment automatically if not already initialized
- Device path serves as persistent identifier across sessions
- Case-insensitive comparison used for device matching

***

#### Connection status check

```cpp
bool is_device_connected(const Device& dev);
```

Verifies whether a previously discovered device remains connected and accessible. Performs a lightweight check without the overhead of creating a full device connection.

The function operates in two stages:

1. Re-enumerates devices via DirectShow and searches for a matching device (by path, falling back to name)
2. If found, attempts a lightweight connection test using `DeviceConnection::is_valid()`

Returns `true` if the device exists and is accessible, `false` otherwise.

```cpp
Device saved_camera = /* previously stored */;

if (duvc::is_device_connected(saved_camera)) {
    // Device available, safe to proceed
    auto connection = platform->create_connection(saved_camera);
}
```

**Behavior:**

- Never throws exceptions; returns `false` on any error
- Returns `true` even if another application is using the device
- Only indicates device presence, not exclusive availability

***

#### Hot-plug detection

**Callback signature:**

```cpp
using DeviceChangeCallback = std::function<void(bool added, const std::wstring& device_path)>;
```

**Registration functions:**

```cpp
void register_device_change_callback(DeviceChangeCallback callback);
void unregister_device_change_callback();
```

Enables notification when cameras are connected or disconnected from the system.

The implementation creates a hidden message-only window (`HWND_MESSAGE`) that receives `WM_DEVICECHANGE` notifications from Windows. The window registers for `DBT_DEVTYP_DEVICEINTERFACE` notifications filtered to the video capture device category (`CLSID_VideoInputDeviceCategory`).

When a device change occurs, the callback receives:

- `added`: `true` for device arrival, `false` for removal
- `device_path`: wide-string device identifier

```cpp
duvc::register_device_change_callback([](bool added, const std::wstring& path) {
    if (added) {
        std::wcout << L"Camera connected: " << path << L"\n";
        // Refresh device list
        auto devices = duvc::list_devices();
    } else {
        std::wcout << L"Camera disconnected: " << path << L"\n";
    }
});

// Windows message loop required
MSG msg;
while (GetMessage(&msg, nullptr, 0, 0)) {
    DispatchMessage(&msg);
}
```

**Constraints:**

- Only one callback can be active at a time; subsequent registrations replace the previous callback
- Application must pump Windows messages for notifications to work
- Callback executes on the Windows message thread; heavy operations should be dispatched to worker threads
- Exceptions thrown in the callback are caught and logged internally

**Cleanup:**

```cpp
duvc::unregister_device_change_callback();
```

Stops device monitoring, unregisters from Windows notifications, destroys the hidden window, and clears the callback function pointer.

***

#### Device identification

Each camera has two identifiers:

- **Name**: Human-readable string (e.g., "Logitech HD Webcam C920")
- **Path**: Unique system path assigned by Windows (e.g., `\\?\usb#vid_046d&pid_082d...`)

The device path is more reliable for identifying specific cameras across sessions. Two cameras of the same model share the same name but have different paths.

Device comparison logic:

1. Compare paths using case-insensitive string comparison (`_wcsicmp`)
2. If path comparison fails, fall back to name comparison

***

#### Implementation architecture

**Windows integration:**

- `device.cpp`: Uses COM interfaces (`ICreateDevEnum`, `IEnumMoniker`, `IPropertyBag`)
- `device_monitor.cpp`: Uses Win32 window messages and `RegisterDeviceNotification()`
- All COM operations wrapped in RAII helpers (`com_ptr`, `com_apartment`)

**Error handling:**

- `list_devices()`: Throws `std::runtime_error` on COM initialization failures
- `is_device_connected()`: Returns `false` on any error, never throws
- Hot-plug callbacks: User exceptions caught and logged, do not propagate

**Platform support:** Windows only. On non-Windows platforms, functions exist as stubs that compile but return empty results.

### 2.2 Camera Control Class

**Header:** `<duvc-ctl/core/camera.h>`

The `Camera` class provides RAII-based camera control with automatic resource management. It handles device connections, property access, and cleanup without requiring manual resource tracking.

#### Construction and lifecycle

```cpp
explicit Camera(const Device& device);
explicit Camera(int device_index);
```

Two constructors available:

- **By device reference:** Accepts a `Device` object from `list_devices()`. Stores the device but defers connection until first property access.
- **By index:** Convenience constructor that calls `list_devices()` internally and selects the device at the given index. Invalid indices result in an invalid camera.

The class follows move-only semantics (non-copyable, but supports move construction and move assignment). The destructor automatically releases the device connection.

```cpp
// Create from device list
auto devices = duvc::list_devices();
Camera cam1(devices);

// Create by index
Camera cam2(1);

// Move semantics
Camera cam3 = std::move(cam1);  // cam1 now invalid
```

**Lazy connection:** The underlying `DeviceConnection` is created on first property access, not during construction. This allows creating `Camera` objects without immediately locking the device.

**Validity check:**

```cpp
bool is_valid() const;
```

Returns `true` if the camera is usable (device valid and connected). Always check before property operations.

***

#### Reading properties

```cpp
Result<PropSetting> get(CamProp prop);
Result<PropSetting> get(VidProp prop);
```

Reads the current value and mode (auto/manual) for a camera or video property. Returns `Result<PropSetting>` containing the value on success, or an error code on failure.

```cpp
Camera cam(0);

auto brightness = cam.get(duvc::VidProp::Brightness);
if (brightness.is_ok()) {
    auto setting = brightness.value();
    std::cout << "Brightness: " << setting.value << "\n";
    std::cout << "Mode: " << (setting.mode == duvc::CamMode::Auto ? "auto" : "manual") << "\n";
}
```

**Error cases:**

- `ErrorCode::DeviceNotFound`: Camera disconnected or connection failed
- `ErrorCode::PropertyNotSupported`: Property not available on this device

***

#### Writing properties

```cpp
Result<void> set(CamProp prop, const PropSetting& setting);
Result<void> set(VidProp prop, const PropSetting& setting);
```

Sets a property to a new value and mode. The `PropSetting` struct contains:

- `value`: Integer value (must be within property range)
- `mode`: `CamMode::Auto` or `CamMode::Manual`

```cpp
duvc::PropSetting setting{100, duvc::CamMode::Manual};
auto result = cam.set(duvc::VidProp::Brightness, setting);

if (result.is_error()) {
    std::cerr << "Failed: " << result.error().description() << "\n";
}
```

**Setting auto mode:**

```cpp
// Enable auto exposure
duvc::PropSetting auto_setting{0, duvc::CamMode::Auto};  // value ignored in auto mode
cam.set(duvc::CamProp::Exposure, auto_setting);
```


***

#### Querying property ranges

```cpp
Result<PropRange> get_range(CamProp prop);
Result<PropRange> get_range(VidProp prop);
```

Retrieves the valid range for a property. Returns `PropRange` containing:

- `min`: Minimum valid value
- `max`: Maximum valid value
- `step`: Increment step (typically 1)
- `default_val`: Default value
- `default_mode`: Default mode (auto or manual)

```cpp
auto range_result = cam.get_range(duvc::CamProp::Pan);
if (range_result.is_ok()) {
    auto range = range_result.value();
    std::cout << "Pan: " << range.min << " to " << range.max 
              << " (step " << range.step << ")\n";
    
    // Use clamp() to constrain values
    int safe_value = range.clamp(999);  // Clamps to max if 999 exceeds range
}
```

**Range validation:** Always query ranges before setting properties to avoid `InvalidValue` errors. Use `PropRange::clamp()` to constrain user input.

***

#### Factory functions

```cpp
Result<Camera> open_camera(int device_index);
Result<Camera> open_camera(const Device& device);
```

Alternative to constructors that return `Result<Camera>` for explicit error handling. These verify device validity and connectivity before returning the camera object.

```cpp
auto cam_result = duvc::open_camera(0);
if (cam_result.is_ok()) {
    Camera cam = std::move(cam_result.value());
    // Use cam
} else {
    std::cerr << "Error: " << cam_result.error().description() << "\n";
}
```


***

#### Result type pattern

All property operations return `Result<T>` types instead of throwing exceptions. This enables:

- **Explicit error handling:** Check `is_ok()` or `is_error()` before accessing values
- **Error propagation:** Chain operations and handle errors at appropriate levels
- **Production safety:** No unexpected exceptions in critical code paths

```cpp
auto result = cam.get(duvc::CamProp::Zoom);
if (result.is_ok()) {
    auto setting = result.value();  // Safe access
} else {
    auto error = result.error();
    // Handle error.code() and error.description()
}
```

**See Section 2.5** for complete `Result<T>` documentation.

***

#### Resource management

The `Camera` class uses RAII to manage the underlying `DeviceConnection`:

- Connection created lazily on first property access
- Connection held in `std::unique_ptr` for automatic cleanup
- Destructor releases connection and COM resources
- Move semantics prevent accidental copies

**Thread safety:** Each `Camera` instance is not thread-safe. Use separate instances for concurrent access to different cameras, or add external synchronization.

***

### 2.3 Device Capabilities

**Header:** `<duvc-ctl/core/capability.h>`

The `DeviceCapabilities` class creates a snapshot of all supported properties and their ranges for a camera. This allows checking what features are available before attempting operations.

#### Capability snapshot structure

```cpp
struct PropertyCapability {
    bool supported;           // Property available on device
    PropRange range;          // Valid range (min, max, step, defaults)
    PropSetting current;      // Current value and mode
    
    bool supports_auto() const;  // Auto mode available
};
```

Each property gets a `PropertyCapability` describing its availability, valid range, current state, and whether automatic mode is supported.

***

#### Creating capability snapshots

```cpp
explicit DeviceCapabilities(const Device& device);
```

Constructor creates a snapshot by scanning all camera and video properties. The scan:

1. Attempts to create a `Camera` connection
2. Iterates through all `CamProp` and `VidProp` enum values
3. Calls `get_range()` for each property (supported if successful)
4. Reads current value with `get()` if range query succeeded
5. Stores results in internal maps
```cpp
auto devices = duvc::list_devices();
duvc::DeviceCapabilities caps(devices);

if (caps.is_device_accessible()) {
    // Scan completed successfully
}
```

**Constructor behavior:** Never throws. If the device is inaccessible, `is_device_accessible()` returns `false` and all property queries return "not supported".

***

#### Checking property support

```cpp
bool supports_camera_property(CamProp prop) const;
bool supports_video_property(VidProp prop) const;
```

Quick boolean check if a property is available.

```cpp
if (caps.supports_camera_property(duvc::CamProp::Pan)) {
    // Pan supported, safe to use
}
```

**Listing supported properties:**

```cpp
std::vector<CamProp> supported_camera_properties() const;
std::vector<VidProp> supported_video_properties() const;
```

Returns vectors of all supported property enums.

```cpp
for (auto prop : caps.supported_camera_properties()) {
    std::cout << "Supports: " << static_cast<int>(prop) << "\n";
}
```


***

#### Retrieving capability details

```cpp
const PropertyCapability& get_camera_capability(CamProp prop) const;
const PropertyCapability& get_video_capability(VidProp prop) const;
```

Gets full capability information for a property. Returns a reference to `PropertyCapability` (or an empty one if unsupported).

```cpp
auto cap = caps.get_camera_capability(duvc::CamProp::Zoom);
if (cap.supported) {
    std::cout << "Zoom range: " << cap.range.min << "-" << cap.range.max << "\n";
    std::cout << "Current: " << cap.current.value << "\n";
    std::cout << "Auto available: " << cap.supports_auto() << "\n";
}
```

**Auto mode detection:** `PropertyCapability::supports_auto()` checks if `range.default_mode == CamMode::Auto`.

***

#### Refreshing capabilities

```cpp
Result<void> refresh();
```

Re-scans all properties to update the snapshot. Useful after device reconnection or when capabilities may have changed.

```cpp
auto result = caps.refresh();
if (result.is_error()) {
    std::cerr << "Refresh failed: " << result.error().description() << "\n";
}
```

Returns `ErrorCode::DeviceNotFound` if the device is no longer connected.

***

#### Capability caching

The class stores capability data in internal maps:

- `std::unordered_map<CamProp, PropertyCapability> camera_capabilities_`
- `std::unordered_map<VidProp, PropertyCapability> video_capabilities_`

**Performance:** Scanning all properties takes time (queries every enum value via DirectShow). Create snapshots once and reuse, or cache them per device. Avoid repeated scans in tight loops.

***

#### Factory functions

```cpp
Result<DeviceCapabilities> get_device_capabilities(const Device& device);
Result<DeviceCapabilities> get_device_capabilities(int device_index);
```

Alternative to constructor that returns `Result<DeviceCapabilities>` with explicit error checking.

```cpp
auto caps_result = duvc::get_device_capabilities(0);
if (caps_result.is_ok()) {
    auto caps = caps_result.value();
    // Use caps
}
```

Returns `ErrorCode::DeviceNotFound` if device inaccessible or `ErrorCode::InvalidArgument` for invalid device/index.

***

**Use cases:**

- **UI generation:** Build control panels dynamically based on supported properties
- **Feature detection:** Check capabilities before offering features to users
- **Validation:** Verify ranges before prompting for input
- **Diagnostics:** Log device capabilities for debugging

**See Section 7** for complete property reference with expected ranges and behaviors.

### 2.4 Core Types \& Enumerations

**Header:** `<duvc-ctl/core/types.h>`

#### Device struct

```cpp
struct Device {
    std::wstring name;
    std::wstring path;
    
    Device() = default;
    Device(std::wstring n, std::wstring p);
    
    bool is_valid() const;
    const std::wstring& get_id() const;
};
```

Represents a camera device with identifying information.

**Members:**

- `name`: Human-readable device name (e.g., "Logitech HD Webcam C920")
- `path`: Unique system device path (e.g., `\\?\usb#vid_046d&pid_082d...`)

**Methods:**

- `is_valid()`: Returns `true` if either name or path is non-empty
- `get_id()`: Returns path if available, otherwise name. Use for stable device identification across sessions.

```cpp
Device cam(L"My Camera", L"\\\\?\\usb#vid_1234...");
if (cam.is_valid()) {
    std::wcout << L"ID: " << cam.get_id() << L"\n";  // Prints path
}
```


***

#### PropSetting struct

```cpp
struct PropSetting {
    int value;
    CamMode mode;
    
    PropSetting() = default;
    PropSetting(int v, CamMode m);
};
```

Combines a property value with its control mode.

**Members:**

- `value`: Integer value (meaning depends on property)
- `mode`: `CamMode::Auto` or `CamMode::Manual`

```cpp
PropSetting brightness{100, CamMode::Manual};
PropSetting auto_exposure{0, CamMode::Auto};  // value ignored in auto mode
```


***

#### PropRange struct

```cpp
struct PropRange {
    int min;
    int max;
    int step;
    int default_val;
    CamMode default_mode;
    
    PropRange() = default;
    
    bool is_valid(int value) const;
    int clamp(int value) const;
};
```

Describes valid range and defaults for a property.

**Members:**

- `min`: Minimum supported value
- `max`: Maximum supported value
- `step`: Increment between valid values (typically 1)
- `default_val`: Factory default value
- `default_mode`: Factory default mode (auto or manual)

**Methods:**

`is_valid(int value)`: Checks if value is within range and aligned to step size.

```cpp
PropRange range{-180, 180, 1, 0, CamMode::Manual};
bool valid = range.is_valid(45);   // true
bool invalid = range.is_valid(200); // false (exceeds max)
```

`clamp(int value)`: Constrains value to valid range and rounds to nearest step.

```cpp
int safe = range.clamp(999);  // Returns 180 (max)
int rounded = range.clamp(44); // Returns 44 (aligned to step=1)
```

**Clamping algorithm:**

- Values ≤ min return min
- Values ≥ max return max
- Values between round to nearest step: `min + round((value - min) / step) * step`

***

#### CamProp enum

```cpp
enum class CamProp {
    Pan,                    // Horizontal rotation
    Tilt,                   // Vertical rotation
    Roll,                   // Roll rotation
    Zoom,                   // Optical zoom
    Exposure,               // Exposure time
    Iris,                   // Aperture setting
    Focus,                  // Focus position
    ScanMode,               // Progressive/interlaced
    Privacy,                // Privacy mode
    PanRelative,            // Relative pan
    TiltRelative,           // Relative tilt
    RollRelative,           // Relative roll
    ZoomRelative,           // Relative zoom
    ExposureRelative,       // Relative exposure
    IrisRelative,           // Relative iris
    FocusRelative,          // Relative focus
    PanTilt,                // Combined pan/tilt
    PanTiltRelative,        // Relative pan/tilt
    FocusSimple,            // Simple focus
    DigitalZoom,            // Digital zoom level
    DigitalZoomRelative,    // Relative digital zoom
    BacklightCompensation,  // Backlight compensation
    Lamp                    // Camera lamp/flash
};
```

Camera control properties mapped to DirectShow's `IAMCameraControl` interface. Controls physical camera mechanisms.

**23 total values** (not 22 as initially stated):

- Absolute controls: Pan, Tilt, Roll, Zoom, Exposure, Iris, Focus, ScanMode, Privacy, DigitalZoom, BacklightCompensation, Lamp (12 values)
- Relative controls: PanRelative, TiltRelative, RollRelative, ZoomRelative, ExposureRelative, IrisRelative, FocusRelative, PanTiltRelative, DigitalZoomRelative (9 values)
- Combined/special: PanTilt, FocusSimple (2 values)

**Relative vs. absolute:**

- Absolute properties set exact positions (e.g., `Pan = 45°`)
- Relative properties adjust by delta (e.g., `PanRelative = +10°`)

***

#### VidProp enum

```cpp
enum class VidProp {
    Brightness,             // Brightness level
    Contrast,               // Contrast level
    Hue,                    // Color hue
    Saturation,             // Color saturation
    Sharpness,              // Sharpness level
    Gamma,                  // Gamma correction
    ColorEnable,            // Color vs. monochrome
    WhiteBalance,           // White balance
    BacklightCompensation,  // Backlight compensation
    Gain                    // Sensor gain
};
```

Video processing properties mapped to DirectShow's `IAMVideoProcAmp` interface. Controls image processing parameters.

**10 total values** (confirmed).

**Note:** `BacklightCompensation` appears in both `CamProp` and `VidProp`. This reflects DirectShow's design where the property may be exposed through either interface depending on the camera.

***

#### CamMode enum

```cpp
enum class CamMode {
    Auto,    // Automatic control by camera
    Manual   // Manual control by application
};
```

Control mode for properties. When `Auto`, the camera adjusts the property automatically. When `Manual`, the application sets explicit values.

**Behavior:**

- Auto mode: Camera firmware controls property (e.g., auto-exposure adjusts based on lighting)
- Manual mode: Application specifies exact value (e.g., exposure locked to -5)

Not all properties support auto mode. Check `PropertyCapability::supports_auto()` or `PropRange::default_mode` to determine availability.

***

#### Type relationships

**Property operations use these types together:**

```cpp
// Get property: returns current value and mode
Result<PropSetting> setting = camera.get(CamProp::Zoom);

// Query range: returns valid bounds
Result<PropRange> range = camera.get_range(CamProp::Zoom);

// Validate and set
if (range.is_ok()) {
    int safe_value = range.value().clamp(user_input);
    PropSetting new_setting{safe_value, CamMode::Manual};
    camera.set(CamProp::Zoom, new_setting);
}
```

**Device identification flow:**

```cpp
std::vector<Device> devices = list_devices();
for (const auto& dev : devices) {
    if (dev.is_valid()) {
        std::wcout << dev.name << L" (" << dev.get_id() << L")\n";
    }
}
```


***

**DirectShow mapping:** These enums correspond directly to DirectShow constants:

- `CamProp` → `CameraControlProperty` enum
- `VidProp` → `VideoProcAmpProperty` enum
- `CamMode` → `CameraControlFlags` (0x0001 = Auto, 0x0002 = Manual)

See Section 6.4 for DirectShow integration details.

### 2.5 Result Type \& Error Handling

**Header:** `<duvc-ctl/core/result.h>`

The library uses a `Result<T>` type system for error handling instead of exceptions. All operations that can fail return `Result<T>` containing either a value or an error.

#### Result template

```cpp
template <typename T>
class Result {
public:
    Result(T value);
    Result(Error error);
    Result(ErrorCode code, std::string message = "");
    
    bool is_ok() const;
    bool is_error() const;
    const T& value() const &;
    T&& value() &&;
    const Error& error() const;
    T value_or(const T& default_value) const &;
    T value_or(T&& default_value) &&;
    explicit operator bool() const;
};
```

**Checking results:**

```cpp
auto result = camera.get(duvc::CamProp::Zoom);

if (result.is_ok()) {
    PropSetting setting = result.value();
} else {
    Error err = result.error();
    // Handle error
}
```

**Boolean conversion:**

```cpp
if (result) {  // Equivalent to result.is_ok()
    // Success path
}
```

**Value extraction with default:**

```cpp
PropSetting setting = result.value_or(PropSetting{0, CamMode::Manual});
```

**Move semantics:**
The value can be accessed by const reference (`value() const &`) or moved out (`value() &&`):

```cpp
PropSetting s1 = result.value();              // Copy
PropSetting s2 = std::move(result).value();   // Move
```


***

#### Result<void> specialization

```cpp
template <>
class Result<void> {
public:
    Result();
    Result(Error error);
    Result(ErrorCode code, std::string message = "");
    
    bool is_ok() const;
    bool is_error() const;
    const Error& error() const;
    explicit operator bool() const;
};
```

Operations that return no value (e.g., `set` methods) use `Result<void>`:

```cpp
Result<void> result = camera.set(duvc::CamProp::Pan, setting);

if (result.is_error()) {
    std::cerr << "Failed: " << result.error().description() << "\n";
}
```


***

#### Error class

```cpp
class Error {
public:
    Error(ErrorCode code, std::string message = "");
    Error(std::error_code code, std::string message = "");
    
    ErrorCode code() const;
    const std::string& message() const;
    std::string description() const;
};
```

The `Error` class wraps error information with context.

**Methods:**

- `code()`: Returns the `ErrorCode` enum value
- `message()`: Returns the custom message string (may be empty)
- `description()`: Returns formatted string combining code name and message

**Example usage:**

```cpp
if (result.is_error()) {
    const auto& err = result.error();
    
    std::cerr << "Error code: " << static_cast<int>(err.code()) << "\n";
    std::cerr << "Message: " << err.message() << "\n";
    std::cerr << "Full: " << err.description() << "\n";
}
```


***

#### ErrorCode enum

```cpp
enum class ErrorCode {
    Success,                // Operation succeeded (value 0)
    DeviceNotFound,         // Device not found or disconnected
    DeviceBusy,             // Device is busy or in use
    PropertyNotSupported,   // Property not supported by device
    InvalidValue,           // Property value out of range
    PermissionDenied,       // Insufficient permissions
    SystemError,            // System/platform error
    InvalidArgument,        // Invalid function argument
    NotImplemented          // Feature not implemented on this platform
};
```

**9 error codes total** (including `Success` = 0).

**String conversion:**

```cpp
const char* to_string(ErrorCode code);
```

Returns human-readable description:

- `Success` → "Success"
- `DeviceNotFound` → "Device not found or disconnected"
- `DeviceBusy` → "Device is busy or in use"
- etc.

**Common error scenarios:**


| Error Code | Typical Causes |
| :-- | :-- |
| `DeviceNotFound` | Camera unplugged, connection failed, device path invalid |
| `DeviceBusy` | Another application using camera exclusively |
| `PropertyNotSupported` | Property not available on this camera model |
| `InvalidValue` | Value outside property's min/max range |
| `PermissionDenied` | Windows privacy settings block camera access |
| `SystemError` | DirectShow/COM errors, driver issues |
| `InvalidArgument` | Invalid device index, null pointer |
| `NotImplemented` | Platform-specific feature on wrong OS |


***

#### Helper functions

```cpp
template <typename T>
Result<T> Ok(T value);

Result<void> Ok();

template <typename T>
Result<T> Err(Error error);

template <typename T>
Result<T> Err(ErrorCode code, std::string message = "");
```

Convenience functions for creating results:

```cpp
Result<int> compute() {
    if (error_condition) {
        return Err<int>(ErrorCode::InvalidValue, "Value too large");
    }
    return Ok(42);
}
```


***

#### Error handling patterns

**Early return on error:**

```cpp
auto devices = list_devices();
if (devices.empty()) {
    return Err<PropSetting>(ErrorCode::DeviceNotFound, "No cameras available");
}

Camera cam(devices);
auto result = cam.get(CamProp::Zoom);
if (result.is_error()) {
    return result.error();
}

return Ok(result.value());
```

**Switch on error codes:**

```cpp
if (result.is_error()) {
    switch (result.error().code()) {
        case ErrorCode::DeviceNotFound:
            // Handle disconnection
            break;
        case ErrorCode::PropertyNotSupported:
            // Disable UI control
            break;
        default:
            // Log error
            break;
    }
}
```

**No exceptions thrown:** All library functions return `Result<T>` types. The only exceptions possible are from standard library (e.g., `std::bad_variant_access` if calling `value()` on error result without checking).

***

### 2.6 Main Include Header

**Header:** `<duvc-ctl/duvc.hpp>`

Single convenience header that includes all public APIs.

#### What it includes

```cpp
// Core functionality
#include <duvc-ctl/core/types.h>      // Device, PropSetting, PropRange, enums
#include <duvc-ctl/core/device.h>     // list_devices(), is_device_connected()
#include <duvc-ctl/core/camera.h>     // Camera class
#include <duvc-ctl/core/result.h>     // Result<T>, Error, ErrorCode
#include <duvc-ctl/core/capability.h> // DeviceCapabilities

// Utility functions
#include <duvc-ctl/utils/factory.h>         // open_camera(), get_device_capabilities()
#include <duvc-ctl/utils/string_conversion.h> // to_wstring()
#include <duvc-ctl/utils/error_decoder.h>   // Error decoding

// Platform interface (advanced)
#include <duvc-ctl/platform/interface.h>    // IPlatformInterface

// Vendor extensions
#include <duvc-ctl/vendor/logitech.h>       // Logitech-specific properties

#ifdef _WIN32
#include <duvc-ctl/platform/windows_internal.h> // Windows-specific internals
#endif
```

**Usage:**

```cpp
#include <duvc-ctl/duvc.hpp>

int main() {
    auto devices = duvc::list_devices();
    duvc::Camera cam(devices);
    auto result = cam.get(duvc::CamProp::Zoom);
}
```


***

#### Quick API wrapper functions

The header also provides simplified `bool`-returning wrapper functions for single-call operations:

**Property get/set:**

```cpp
bool get(const Device& dev, CamProp prop, PropSetting& out);
bool set(const Device& dev, CamProp prop, const PropSetting& in);
bool get_range(const Device& dev, CamProp prop, PropRange& out);

// Video property overloads
bool get(const Device& dev, VidProp prop, PropSetting& out);
bool set(const Device& dev, VidProp prop, const PropSetting& in);
bool get_range(const Device& dev, VidProp prop, PropRange& out);
```

These wrappers internally create a `Camera` object, perform the operation, and return `true` on success or `false` on any error. They are implemented as inline functions.

**Example:**

```cpp
auto devices = duvc::list_devices();
duvc::PropSetting brightness;

if (duvc::get(devices, duvc::VidProp::Brightness, brightness)) {
    std::cout << "Brightness: " << brightness.value << "\n";
}
```

**When to use wrappers vs Camera API:**

- **Wrappers:** CLI tools, scripts, simple one-off operations
- **Camera API:** Applications needing detailed error information, multiple operations on same device, RAII resource management

***

#### Namespace organization

All public APIs are in the `duvc` namespace:

```cpp
namespace duvc {
    // Types
    struct Device;
    struct PropSetting;
    struct PropRange;
    enum class CamProp { /* ... */ };
    enum class VidProp { /* ... */ };
    enum class CamMode { /* ... */ };
    
    // Classes
    class Camera;
    class DeviceCapabilities;
    template <typename T> class Result;
    class Error;
    
    // Functions
    std::vector<Device> list_devices();
    bool is_device_connected(const Device&);
    // etc.
}
```

No sub-namespaces exposed in public API. Internal implementation uses `duvc::detail` for private utilities.

***

**Recommended approach:** Include `<duvc-ctl/duvc.hpp>` for general use. Individual headers (`<duvc-ctl/core/camera.h>`, etc.) can be included selectively to reduce compile time if only specific components are needed.

## 3. Utility Functions \& Helpers

### 3.1 Logging System

**Header:** `<duvc-ctl/utils/logging.h>`

The library provides a structured logging system for internal diagnostics and debugging. Applications can hook into this system to capture library events.

#### LogLevel enum

```cpp
enum class LogLevel {
    Debug = 0,      // Verbose debugging information
    Info = 1,       // General informational messages
    Warning = 2,    // Warning messages
    Error = 3,      // Error messages
    Critical = 4    // Critical errors
};
```

**Five severity levels** with numeric ordering (higher = more severe). Used to filter messages and route output.

**String conversion:**

```cpp
const char* to_string(LogLevel level);
```

Returns level name: "DEBUG", "INFO", "WARNING", "ERROR", or "CRITICAL".

***

#### Callback configuration

```cpp
using LogCallback = std::function<void(LogLevel level, const std::string& message)>;

void set_log_callback(LogCallback callback);
```

Registers a callback function to receive all log messages. The callback receives the severity level and message string.

```cpp
duvc::set_log_callback([](duvc::LogLevel level, const std::string& msg) {
    if (level >= duvc::LogLevel::Error) {
        std::cerr << "[DUVC] " << msg << "\n";
    } else {
        std::cout << "[DUVC] " << msg << "\n";
    }
});
```

**Callback behavior:**

- Pass `nullptr` to disable custom logging (reverts to default handler)
- Callback invoked with mutex held (implementation is thread-safe)
- If callback throws an exception, the system catches it and logs an error using the default handler
- Callback should be fast; slow operations may block library threads

**Default handler:** When no callback is set, messages are written to stdout (Debug/Info/Warning) or stderr (Error/Critical) with timestamps:

```
[2025-11-09 20:30:15.123] [INFO] Device enumeration started
[2025-11-09 20:30:15.456] [ERROR] Failed to open device: Device busy
```


***

#### Log level filtering

```cpp
void set_log_level(LogLevel level);
LogLevel get_log_level();
```

Controls the minimum severity level for logged messages. Messages below this threshold are silently discarded.

```cpp
// Only log warnings and above
duvc::set_log_level(duvc::LogLevel::Warning);

// Query current setting
auto level = duvc::get_log_level();
```

**Default level:** `LogLevel::Info` (Debug messages suppressed by default).

**Performance:** Filtering happens before formatting. Setting `LogLevel::Error` eliminates overhead of Debug/Info/Warning messages entirely.

***

#### Logging functions

```cpp
void log_message(LogLevel level, const std::string& message);

void log_debug(const std::string& message);
void log_info(const std::string& message);
void log_warning(const std::string& message);
void log_error(const std::string& message);
void log_critical(const std::string& message);
```

Functions for emitting log messages. The level-specific functions (`log_debug`, `log_info`, etc.) are convenience wrappers around `log_message`.

**Direct usage:**

```cpp
duvc::log_info("Camera opened successfully");
duvc::log_error("DirectShow enumeration failed");
duvc::log_debug("Property value: " + std::to_string(value));
```

**Message construction:** Accept `std::string`. Build formatted messages with `std::ostringstream` or `std::format` before passing:

```cpp
std::ostringstream oss;
oss << "Device " << device.name << " brightness=" << value;
duvc::log_info(oss.str());
```


***

#### Logging macros

```cpp
#define DUVC_LOG_DEBUG(msg)    duvc::log_debug(msg)
#define DUVC_LOG_INFO(msg)     duvc::log_info(msg)
#define DUVC_LOG_WARNING(msg)  duvc::log_warning(msg)
#define DUVC_LOG_ERROR(msg)    duvc::log_error(msg)
#define DUVC_LOG_CRITICAL(msg) duvc::log_critical(msg)
```

Macros for logging used internally by the library. Applications can use these or call the functions directly—they're functionally identical.

**Internal usage patterns:**

```cpp
DUVC_LOG_DEBUG("Querying property range");
DUVC_LOG_WARNING("Property not supported, trying fallback");
DUVC_LOG_ERROR("COM initialization failed");
```

**Note:** These are simple wrappers, not variadic macros. Formatting must be done before passing the message.

***

#### Thread safety

The logging system is fully thread-safe:

- Global state (`g_log_callback`, `g_min_log_level`) protected by mutex
- Callbacks invoked with lock held to prevent races
- Safe to call from multiple threads concurrently

**Mutex contention:** Heavy logging from many threads may create lock contention. Keep callbacks fast or buffer messages for async processing.

***

#### Typical log output

**Default format:**

```
[2025-11-09 20:15:30.123] [DEBUG] Enumerating DirectShow video devices
[2025-11-09 20:15:30.156] [INFO] Found 2 devices
[2025-11-09 20:15:30.201] [DEBUG] Opening device: Logitech HD Webcam
[2025-11-09 20:15:30.345] [INFO] Device connection established
[2025-11-09 20:15:31.012] [WARNING] Property Iris not supported
[2025-11-09 20:15:31.234] [ERROR] Failed to set Pan: value out of range
```

**Timestamp format:** `YYYY-MM-DD HH:MM:SS.mmm` (millisecond precision).

***

#### Integration patterns

**Redirect to application logger:**

```cpp
#include <spdlog/spdlog.h>

duvc::set_log_callback([](duvc::LogLevel level, const std::string& msg) {
    switch (level) {
        case duvc::LogLevel::Debug:   spdlog::debug(msg); break;
        case duvc::LogLevel::Info:    spdlog::info(msg); break;
        case duvc::LogLevel::Warning: spdlog::warn(msg); break;
        case duvc::LogLevel::Error:   spdlog::error(msg); break;
        case duvc::LogLevel::Critical: spdlog::critical(msg); break;
    }
});
```

**Write to file:**

```cpp
std::ofstream logfile("duvc.log", std::ios::app);
duvc::set_log_callback([&logfile](duvc::LogLevel level, const std::string& msg) {
    logfile << "[" << duvc::to_string(level) << "] " << msg << "\n";
    logfile.flush();
});
```

**Suppress all logging:**

```cpp
duvc::set_log_level(duvc::LogLevel::Critical + 1);  // No messages pass
// Or:
duvc::set_log_callback(nullptr);
duvc::set_log_level(duvc::LogLevel::Critical);
```


***

#### What the library logs

**Debug level:**

- DirectShow interface queries
- Property range queries
- Detailed operation traces

**Info level:**

- Device enumeration results
- Connection establishment
- Property changes

**Warning level:**

- Unsupported properties
- Fallback behavior
- Non-fatal errors

**Error level:**

- COM failures
- Device access errors
- Invalid operations

**Critical level:**

- Unrecoverable initialization failures
- System resource exhaustion

**Production recommendation:** Set level to `Info` or `Warning` for normal operation. Enable `Debug` only when diagnosing issues.

### 3.2 String Conversion

**Header:** `<duvc-ctl/utils/string_conversion.h>`

Utilities for converting enum values to strings and performing character encoding conversions.

#### Enum to string conversion

```cpp
const char* to_string(CamProp prop);
const char* to_string(VidProp prop);
const char* to_string(CamMode mode);
```

Converts enum values to narrow (UTF-8) C-style strings.

```cpp
duvc::CamProp prop = duvc::CamProp::Zoom;
std::cout << "Property: " << duvc::to_string(prop) << "\n";  // "Zoom"

duvc::CamMode mode = duvc::CamMode::Auto;
std::cout << "Mode: " << duvc::to_string(mode) << "\n";  // "AUTO"
```

**Returns:** String literal for known enums, "Unknown" for invalid values.

***

#### Enum to wide string conversion

```cpp
const wchar_t* to_wstring(CamProp prop);
const wchar_t* to_wstring(VidProp prop);
const wchar_t* to_wstring(CamMode mode);
```

Converts enum values to wide (UTF-16 on Windows) C-style strings. Useful for Windows APIs and logging that requires wide strings.

```cpp
duvc::VidProp prop = duvc::VidProp::Brightness;
std::wcout << L"Property: " << duvc::to_wstring(prop) << L"\n";  // L"Brightness"
```

**Note:** Mode strings are uppercase: `L"AUTO"` and `L"MANUAL"`.

***

#### UTF-16 to UTF-8 conversion

```cpp
std::string to_utf8(const std::wstring& wstr);
```

Converts a wide string (UTF-16 on Windows) to a UTF-8 encoded narrow string. Essential for working with Windows device names and paths in portable code.

```cpp
Device camera = /* from list_devices() */;
std::string utf8_name = duvc::to_utf8(camera.name);

// Safe for JSON, file I/O, cross-platform APIs
std::cout << "Camera: " << utf8_name << "\n";
```

**Implementation:** Uses Windows `WideCharToMultiByte` with `CP_UTF8` flag for proper character conversion.

**Error handling:** Throws `std::runtime_error` if conversion fails. Returns empty string for empty input.

**Use cases:**

- Logging device names to files/console
- Serializing device info to JSON/XML
- Passing device names to cross-platform APIs
- Displaying camera names in UI (UTF-8 frameworks)

***

### 3.3 Error Decoding

**Header:** `<duvc-ctl/utils/error_decoder.h>`

Utilities for decoding Windows system errors and COM HRESULTs into human-readable messages.

#### System error decoding

```cpp
std::string decode_system_error(unsigned long error_code);
```

Converts a Windows system error code (e.g., from `GetLastError()`) to a descriptive string.

```cpp
unsigned long err_code = GetLastError();
std::string description = duvc::decode_system_error(err_code);
std::cerr << "Error: " << description << "\n";
```

**Implementation:** Uses `FormatMessageW` to retrieve localized error text from Windows, then converts to UTF-8.

**Fallback:** If `FormatMessage` fails, returns `"System error 0x[hex_code]"`.

**Platform:** Windows only. On other platforms, returns `"System error [code]"`.

***

#### HRESULT decoding

```cpp
std::string decode_hresult(HRESULT hr);
std::string get_hresult_details(HRESULT hr);
```

Windows-only functions for decoding COM HRESULTs.

**`decode_hresult`:** Converts HRESULT to human-readable description using `_com_error`.

```cpp
HRESULT hr = CoCreateInstance(/* ... */);
if (FAILED(hr)) {
    std::string msg = duvc::decode_hresult(hr);
    DUVC_LOG_ERROR(msg);
}
```

**`get_hresult_details`:** Provides extended information including hex code, facility, error code, severity, and description.

```cpp
std::string details = duvc::get_hresult_details(0x8007001F);
// Returns: "HRESULT: 0x8007001F (Facility: 7, Code: 31) [FAILURE] - A device attached to the system is not functioning."
```

**Output format:**

```
HRESULT: 0x[hex] (Facility: [num], Code: [num]) [SUCCESS/FAILURE] - [description]
```


***

#### Error classification

```cpp
bool is_device_error(HRESULT hr);
bool is_permission_error(HRESULT hr);
```

Windows-only functions for categorizing HRESULTs.

**`is_device_error`:** Returns `true` for device-related failures.

Recognized codes:

- `E_ACCESSDENIED`
- `ERROR_DEVICE_NOT_CONNECTED`
- `ERROR_DEVICE_IN_USE`
- `ERROR_NOT_FOUND`
- `ERROR_FILE_NOT_FOUND`
- `VFW_E_CANNOT_CONNECT`
- `VFW_E_CANNOT_RENDER`
- `VFW_E_DEVICE_IN_USE`

```cpp
if (FAILED(hr) && duvc::is_device_error(hr)) {
    // Handle device disconnection/busy state
    return duvc::ErrorCode::DeviceNotFound;
}
```

**`is_permission_error`:** Returns `true` for access/permission failures.

Currently checks:

- `E_ACCESSDENIED`

```cpp
if (duvc::is_permission_error(hr)) {
    // Prompt user to grant camera permissions
    return duvc::ErrorCode::PermissionDenied;
}
```


***

#### Diagnostic information

```cpp
std::string get_diagnostic_info();
```

Collects system information useful for troubleshooting. Returns a formatted string with:

- Platform (Windows / Non-Windows)
- Windows version and build number
- Processor architecture (x64, x86, ARM64, ARM)
- COM initialization status
- DirectShow availability

```cpp
std::string diag = duvc::get_diagnostic_info();
std::cout << diag << "\n";
```

**Example output:**

```
duvc-ctl Diagnostic Information
==============================
Platform: Windows
Windows Version: 10.0 (Build 19045)
Architecture: x64
COM Status: Available
DirectShow: Available
```

**Error scenarios:**

- If COM initialization fails, includes error description
- If DirectShow unavailable, reports `CoCreateInstance` failure
- On non-Windows platforms, returns single line: `"Platform: Non-Windows (stub implementation)"`

**Use cases:**

- Include in bug reports
- Log at application startup
- Display in diagnostic/about dialogs
- Automated issue reporting

***

**Platform notes:** All HRESULT-related functions (`decode_hresult`, `get_hresult_details`, `is_device_error`, `is_permission_error`) are Windows-only and wrapped in `#ifdef _WIN32`. They do not exist in non-Windows builds.

## 4. Platform Abstraction Layer

### 4.1 Platform Interfaces

**Header:** `<duvc-ctl/platform/interface.h>`

The platform abstraction layer decouples high-level camera APIs from platform-specific implementations. This allows supporting multiple camera APIs (DirectShow, V4L2, AVFoundation) through a common interface.

#### IPlatformInterface

```cpp
class IPlatformInterface {
public:
    virtual ~IPlatformInterface() = default;
    
    virtual Result<std::vector<Device>> list_devices() = 0;
    virtual Result<bool> is_device_connected(const Device& device) = 0;
    virtual Result<std::unique_ptr<IDeviceConnection>> create_connection(const Device& device) = 0;
};
```

Abstract interface for platform-specific device enumeration and connection management.

**Methods:**

`list_devices()`: Enumerates all video input devices available on the system. Returns a vector of `Device` objects or an error if enumeration fails.

```cpp
auto platform = duvc::create_platform_interface();
auto result = platform->list_devices();

if (result.is_ok()) {
    for (const auto& dev : result.value()) {
        std::wcout << dev.name << L"\n";
    }
}
```

`is_device_connected(const Device&)`: Checks if a specific device is currently connected and accessible. Returns boolean status or error.

```cpp
Device my_camera = /* saved device */;
auto result = platform->is_device_connected(my_camera);

if (result.is_ok() && result.value()) {
    // Device available
}
```

`create_connection(const Device&)`: Creates a connection handle for interacting with a specific device. Returns an `IDeviceConnection` instance or error if connection fails.

```cpp
auto conn_result = platform->create_connection(device);
if (conn_result.is_ok()) {
    auto connection = std::move(conn_result.value());
    // Use connection
}
```


***

#### IDeviceConnection

```cpp
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
```

Abstract interface for device-specific operations on an active connection.

**Methods:**

`is_valid()`: Returns `true` if the connection is active and usable. Check before performing operations.

```cpp
if (connection->is_valid()) {
    // Safe to use
}
```

**Camera property operations:**

`get_camera_property(CamProp)`: Reads current value and mode for a camera control property (Pan, Tilt, Zoom, etc.).

`set_camera_property(CamProp, PropSetting)`: Sets a new value and mode for a camera control property.

`get_camera_property_range(CamProp)`: Queries the valid range, step, and defaults for a camera control property.

**Video property operations:**

`get_video_property(VidProp)`: Reads current value and mode for a video processing property (Brightness, Contrast, etc.).

`set_video_property(VidProp, PropSetting)`: Sets a new value and mode for a video processing property.

`get_video_property_range(VidProp)`: Queries the valid range, step, and defaults for a video processing property.

**Example usage:**

```cpp
auto conn = platform->create_connection(device).value();

// Get brightness
auto brightness = conn->get_video_property(VidProp::Brightness);
if (brightness.is_ok()) {
    std::cout << "Brightness: " << brightness.value().value << "\n";
}

// Set zoom
PropSetting zoom_setting{100, CamMode::Manual};
conn->set_camera_property(CamProp::Zoom, zoom_setting);

// Query pan range
auto range = conn->get_camera_property_range(CamProp::Pan);
if (range.is_ok()) {
    std::cout << "Pan: " << range.value().min << " to " << range.value().max << "\n";
}
```


***

#### Factory function

```cpp
std::unique_ptr<IPlatformInterface> create_platform_interface();
```

Creates a platform-specific implementation of the interface. Returns appropriate backend based on compile-time platform detection.

**Platform selection:**

- **Windows:** Returns `WindowsPlatformInterface` (DirectShow-based implementation)
- **Other platforms:** Returns `nullptr` (unsupported)

```cpp
auto platform = duvc::create_platform_interface();

if (!platform) {
    std::cerr << "Platform not supported\n";
    return;
}

// Use platform interface
auto devices = platform->list_devices();
```

**Implementation note:** On Windows, the factory creates a `WindowsPlatformInterface` instance that internally uses DirectShow via `DirectShowEnumerator` and `DirectShowDeviceConnection` classes.

***

#### Windows DirectShow implementation

The Windows backend implementation wraps DirectShow COM interfaces:

**WindowsPlatformInterface:**

- `list_devices()`: Uses `DirectShowEnumerator::enumerate_devices()` to query `CLSID_VideoInputDeviceCategory`
- `is_device_connected()`: Uses `DirectShowEnumerator::is_device_available()` to check device presence
- `create_connection()`: Creates `DirectShowDeviceConnection` instance wrapping DirectShow filter

**DirectShowDeviceConnection:**

- Manages `DirectShowFilter` instance holding `IBaseFilter` COM interface
- Property operations query `IAMCameraControl` and `IAMVideoProcAmp` interfaces
- Maps `CamProp`/`VidProp` enums to DirectShow constants via `DirectShowMapper`
- Converts between `PropSetting`/`PropRange` and DirectShow values/flags

**Error mapping:**

- COM failures → `ErrorCode::SystemError`
- Unsupported properties → `ErrorCode::PropertyNotSupported`
- Missing interfaces → `ErrorCode::PropertyNotSupported`
- Device not found → `ErrorCode::DeviceNotFound`

***

#### Design rationale

**Abstraction benefits:**

- High-level APIs (`Camera`, `list_devices()`) remain platform-agnostic
- Platform-specific code isolated to implementation classes
- Future backends (V4L2, AVFoundation) implement same interfaces
- Testing via mock implementations

**Usage in library:**
The `Camera` class internally uses `IPlatformInterface` via a global singleton. Direct use of platform interfaces is only needed for:

- Custom platform backends
- Low-level testing
- Performance-critical batch operations

**Normal applications use `Camera` class instead:**

```cpp
// Typical usage (recommended)
Camera cam(0);
cam.get(CamProp::Zoom);

// Platform interface usage (advanced)
auto platform = create_platform_interface();
auto conn = platform->create_connection(device).value();
conn->get_camera_property(CamProp::Zoom);
```

## 5. Vendor-Specific Extensions

### 5.1 Logitech Extensions

**Header:** `<duvc-ctl/vendor/logitech.h>`
**Namespace:** `duvc::logitech`
**Platform:** Windows only (`#ifdef _WIN32`)

Provides access to Logitech-specific UVC extension unit properties beyond standard DirectShow controls. These properties control vendor-specific features like RightLight, face tracking, and LED indicators.

This serves more of like an example for similar vendor specific extensions that can be made available

#### LogitechProperty enum

```cpp
enum class LogitechProperty : uint32_t {
    RightLight = 1,       // Auto-exposure and brightness optimization
    RightSound = 2,       // Audio processing and noise cancellation
    FaceTracking = 3,     // Face tracking enable/disable for auto-framing
    LedIndicator = 4,     // LED indicator control (on/off/blink modes)
    ProcessorUsage = 5,   // Processor usage optimization hints
    RawDataBits = 6,      // Raw data bit depth configuration
    FocusAssist = 7,      // Focus assist beam control
    VideoStandard = 8,    // Video standard selection (NTSC/PAL/etc)
    DigitalZoomROI = 9,   // Digital zoom region of interest coordinates
    TiltPan = 10          // Combined tilt/pan control (absolute positioning)
};
```

**10 vendor property values** corresponding to Logitech's UVC extension unit property IDs. Values map to the property set GUID `{82066163-7BD0-43EF-8A6F-5B8905C9A64C}`.

**Property descriptions:**


| Property | Description | Typical Data Type |
| :-- | :-- | :-- |
| `RightLight` | Adaptive lighting optimization | `uint32_t` (0=off, 1=on) |
| `RightSound` | Audio noise reduction and enhancement | `uint32_t` |
| `FaceTracking` | Auto-framing based on detected faces | `bool` |
| `LedIndicator` | Camera status LED control | `uint32_t` (mode flags) |
| `ProcessorUsage` | CPU/GPU usage hints for firmware | `uint32_t` |
| `RawDataBits` | Sensor bit depth configuration | `uint32_t` |
| `FocusAssist` | IR focus assist beam enable | `bool` |
| `VideoStandard` | Broadcast standard selection | `uint32_t` (enum) |
| `DigitalZoomROI` | Digital zoom target region | Struct (x, y, width, height) |
| `TiltPan` | Combined PTZ positioning | Struct (pan, tilt values) |


***

#### Raw byte property access

```cpp
Result<std::vector<uint8_t>> get_logitech_property(const Device& device, LogitechProperty prop);
Result<void> set_logitech_property(const Device& device, LogitechProperty prop, const std::vector<uint8_t>& data);
```

Low-level functions for reading/writing properties as raw byte vectors. Caller responsible for interpreting binary format.

**Example:**

```cpp
auto devices = duvc::list_devices();
auto data_result = duvc::logitech::get_logitech_property(devices, duvc::logitech::LogitechProperty::RightLight);

if (data_result.is_ok()) {
    const auto& bytes = data_result.value();
    // Interpret bytes based on property format
}
```

**Setting property:**

```cpp
std::vector<uint8_t> led_data = {0x02};  // LED mode 2
auto result = duvc::logitech::set_logitech_property(device, duvc::logitech::LogitechProperty::LedIndicator, led_data);
```

**Error returns:**

- `ErrorCode::PropertyNotSupported`: Device lacks Logitech extension unit
- `ErrorCode::SystemError`: KsProperty query failed
- `ErrorCode::DeviceNotFound`: Device disconnected

***

#### Typed property access

```cpp
template <typename T>
Result<T> get_logitech_property_typed(const Device& device, LogitechProperty prop);

template <typename T>
Result<void> set_logitech_property_typed(const Device& device, LogitechProperty prop, const T& value);
```

Type-safe wrappers that reinterpret property bytes as specified type. Type `T` must be trivially copyable and match the property's binary layout.

**Supported types (explicit instantiations):**

- `uint32_t`
- `int32_t`
- `bool`

**Reading typed property:**

```cpp
auto result = duvc::logitech::get_logitech_property_typed<uint32_t>(device, duvc::logitech::LogitechProperty::RightLight);

if (result.is_ok()) {
    uint32_t rightlight_mode = result.value();
    std::cout << "RightLight: " << (rightlight_mode ? "enabled" : "disabled") << "\n";
}
```

**Setting typed property:**

```cpp
// Enable face tracking
auto result = duvc::logitech::set_logitech_property_typed<bool>(device, duvc::logitech::LogitechProperty::FaceTracking, true);

if (result.is_error()) {
    std::cerr << "Failed: " << result.error().description() << "\n";
}
```

**Type safety:** The typed functions validate that received data size matches `sizeof(T)`. Mismatched sizes return `ErrorCode::InvalidValue`.

**Custom types:** For complex properties like `DigitalZoomROI`, define a matching struct:

```cpp
struct ZoomROI {
    int32_t x;
    int32_t y;
    uint32_t width;
    uint32_t height;
};
static_assert(std::is_trivially_copyable_v<ZoomROI>);

auto roi = duvc::logitech::get_logitech_property_typed<ZoomROI>(device, duvc::logitech::LogitechProperty::DigitalZoomROI);
```


***

#### Device support detection

```cpp
Result<bool> supports_logitech_properties(const Device& device);
```

Checks if a device supports Logitech vendor extensions by querying the extension unit's presence and capabilities.

```cpp
auto support = duvc::logitech::supports_logitech_properties(device);

if (support.is_ok() && support.value()) {
    // Device supports Logitech extensions
    auto rightlight = duvc::logitech::get_logitech_property_typed<uint32_t>(device, duvc::logitech::LogitechProperty::RightLight);
} else {
    std::cout << "Logitech extensions not available\n";
}
```

**Implementation:** Internally queries support flags for the `RightLight` property. Returns `false` on any error or if `KSPROPERTY_SUPPORT_GET`/`KSPROPERTY_SUPPORT_SET` flags are not set.

**Non-Logitech cameras:** Always returns `false`. Safe to call on any device.

***

#### Implementation details

**Property set GUID:**

```cpp
inline constexpr GUID LOGITECH_PROPERTY_SET = {
    0x82066163, 0x7BD0, 0x43EF,
    {0x8A, 0x6F, 0x5B, 0x89, 0x05, 0xC9, 0xA6, 0x4C}
};
```

All Logitech properties belong to this extension unit GUID. Defined as `inline constexpr` for C++17 ODR-safety.

**Backend:** Uses `KsPropertySet` class (from `ks_properties.h`) to interact with Windows Kernel Streaming property APIs. This bypasses DirectShow and directly communicates with the USB Video Class driver.

**Error handling:**

- Exceptions from `KsPropertySet` caught and converted to `Result<T>` errors
- Logged at `ERROR` level for get/set, `DEBUG` level for support queries
- Device disconnection during operation returns `SystemError`

***

#### Usage patterns

**Toggle feature:**

```cpp
if (duvc::logitech::supports_logitech_properties(device).value_or(false)) {
    // Enable RightLight
    duvc::logitech::set_logitech_property_typed<uint32_t>(device, duvc::logitech::LogitechProperty::RightLight, 1);
    
    // Toggle face tracking
    auto tracking = duvc::logitech::get_logitech_property_typed<bool>(device, duvc::logitech::LogitechProperty::FaceTracking);
    if (tracking.is_ok()) {
        duvc::logitech::set_logitech_property_typed<bool>(device, duvc::logitech::LogitechProperty::FaceTracking, !tracking.value());
    }
}
```

**Conditional features:**

```cpp
auto devices = duvc::list_devices();
for (const auto& dev : devices) {
    auto support = duvc::logitech::supports_logitech_properties(dev);
    if (support.value_or(false)) {
        std::wcout << dev.name << L" [Logitech extensions available]\n";
    }
}
```


***

**Platform availability:** All functions are Windows-only and wrapped in `#ifdef _WIN32`. Non-Windows builds will have no `duvc::logitech` namespace.

**Camera compatibility:** Only Logitech cameras with UVC extension units support these properties. Other manufacturers may use different GUIDs and property IDs.

### 5.2 Kernel Streaming Properties

**Header:** `<duvc-ctl/platform/ks_properties.h>`
**Platform:** Windows only (`#ifdef _WIN32`)

Low-level wrapper for Windows Kernel Streaming property access via the `IKsPropertySet` COM interface. Used internally by vendor extensions to query properties beyond DirectShow's standard interfaces.

#### KsPropertySet class

```cpp
class KsPropertySet {
public:
    explicit KsPropertySet(const Device& device);
    ~KsPropertySet();
    
    // Non-copyable but movable
    KsPropertySet(KsPropertySet&&) noexcept;
    KsPropertySet& operator=(KsPropertySet&&) noexcept;
    
    bool is_valid() const;
    
    Result<uint32_t> query_support(const GUID& property_set, uint32_t property_id);
    Result<std::vector<uint8_t>> get_property(const GUID& property_set, uint32_t property_id);
    Result<void> set_property(const GUID& property_set, uint32_t property_id, const std::vector<uint8_t>& data);
    
    template <typename T>
    Result<T> get_property_typed(const GUID& property_set, uint32_t property_id);
    
    template <typename T>
    Result<void> set_property_typed(const GUID& property_set, uint32_t property_id, const T& value);
};
```

RAII wrapper managing lifetime of the `IKsPropertySet` COM interface. Automatically queries interface from device filter on construction.

***

#### Constructor and validity

```cpp
explicit KsPropertySet(const Device& device);
bool is_valid() const;
```

Constructor opens the device's DirectShow filter and queries for `IID_IKsPropertySet` interface. If the query fails (device doesn't support Kernel Streaming properties), the instance is invalid.

```cpp
KsPropertySet prop_set(device);

if (!prop_set.is_valid()) {
    std::cerr << "Device does not support KS properties\n";
    return;
}
```

**Non-throwing:** Constructor catches all exceptions and sets the instance to invalid state. Always check `is_valid()` before use.

**Move semantics:** The class is move-only (non-copyable). Moving transfers ownership of the COM interface pointer.

***

#### Query support

```cpp
Result<uint32_t> query_support(const GUID& property_set, uint32_t property_id);
```

Queries whether a property is supported and what operations (get/set) are available. Returns support flags as a bitmask.

```cpp
auto support = prop_set.query_support(LOGITECH_PROPERTY_SET, 1);

if (support.is_ok()) {
    uint32_t flags = support.value();
    bool can_get = (flags & KSPROPERTY_SUPPORT_GET) != 0;
    bool can_set = (flags & KSPROPERTY_SUPPORT_SET) != 0;
}
```

**Support flags:**

- `KSPROPERTY_SUPPORT_GET` (0x1): Property can be read
- `KSPROPERTY_SUPPORT_SET` (0x2): Property can be written

**Error returns:**

- `ErrorCode::SystemError`: Interface not valid
- `ErrorCode::PropertyNotSupported`: Property not supported by device

***

#### Raw property access

```cpp
Result<std::vector<uint8_t>> get_property(const GUID& property_set, uint32_t property_id);
Result<void> set_property(const GUID& property_set, uint32_t property_id, const std::vector<uint8_t>& data);
```

Low-level byte-oriented property access.

**`get_property`:** Queries property size, allocates buffer, retrieves data. Returns byte vector containing property value in its native binary format.

```cpp
auto data = prop_set.get_property(some_guid, 5);
if (data.is_ok()) {
    const auto& bytes = data.value();
    // Interpret bytes based on property definition
}
```

**`set_property`:** Writes raw byte data to property.

```cpp
std::vector<uint8_t> value_bytes = {0x01, 0x00, 0x00, 0x00};  // uint32_t = 1
prop_set.set_property(some_guid, 5, value_bytes);
```

**Implementation details:**

- `get_property` first calls `IKsPropertySet::Get()` with null buffer to query size, then allocates and retrieves actual data
- `set_property` calls `IKsPropertySet::Set()` directly with provided buffer
- Both decode HRESULT failures using `decode_hresult()` utility

***

#### Typed property access

```cpp
template <typename T>
Result<T> get_property_typed(const GUID& property_set, uint32_t property_id);

template <typename T>
Result<void> set_property_typed(const GUID& property_set, uint32_t property_id, const T& value);
```

Type-safe wrappers that reinterpret property bytes as specified type `T`. Type must be trivially copyable.

**Reading typed value:**

```cpp
auto value = prop_set.get_property_typed<uint32_t>(guid, 2);
if (value.is_ok()) {
    uint32_t mode = value.value();
}
```

**Writing typed value:**

```cpp
bool enable = true;
prop_set.set_property_typed<bool>(guid, 3, enable);
```

**Implementation:**

- `get_property_typed` calls `get_property()`, validates size matches `sizeof(T)`, then uses `std::memcpy` to reinterpret bytes
- `set_property_typed` uses `std::memcpy` to convert value to bytes, then calls `set_property()`
- Size mismatch returns `ErrorCode::InvalidValue` with descriptive message

**Explicit instantiations** for common types:

- `uint32_t`
- `int32_t`
- `bool`

Custom types can be used if they are trivially copyable and match the property's binary layout.

***

#### IKsPropertySet interface

```cpp
struct IKsPropertySet;  // Forward declaration
```

COM interface defined in Windows Kernel Streaming headers. Provides low-level access to device properties via property set GUIDs and IDs.

**Key methods (internal to implementation):**

- `QuerySupported(GUID, DWORD, ULONG*)`: Query support flags
- `Get(GUID, DWORD, void*, ULONG, void*, ULONG, ULONG*)`: Read property
- `Set(GUID, DWORD, void*, ULONG, void*, ULONG)`: Write property

**GUID handling:** Property sets are identified by 128-bit GUIDs. Each property within a set has a numeric ID (typically 1-based).

**Example GUIDs:**

- Logitech vendor properties: `{82066163-7BD0-43EF-8A6F-5B8905C9A64C}`
- DirectShow standard sets use different GUIDs

***

### 5.3 Vendor Property Structure

**Note:** The codebase **does not** define a `VendorProperty` struct or generic `get_vendor_property`/`set_vendor_property` functions. Vendor properties are accessed through:

1. **Logitech-specific functions** in `duvc::logitech` namespace (Section 5.1)
2. **Generic `KsPropertySet` class** (Section 5.2) for direct property access

**Architecture:** The library provides vendor-specific namespaces (currently only `duvc::logitech`) that wrap `KsPropertySet` with typed enums and documented property IDs. This approach allows adding new vendors without changing the core API.

***

#### Implementing custom vendor properties

To add support for another vendor (e.g., Microsoft Surface cameras), follow this pattern:

**1. Define property enum and GUID:**

```cpp
namespace duvc::microsoft {
    inline constexpr GUID SURFACE_PROPERTY_SET = {/* ... */};
    
    enum class SurfaceProperty : uint32_t {
        IRFloodLight = 1,
        RGBExposure = 2,
        // ...
    };
}
```

**2. Implement get/set wrappers:**

```cpp
namespace duvc::microsoft {
    Result<std::vector<uint8_t>> get_surface_property(const Device& device, SurfaceProperty prop) {
        KsPropertySet prop_set(device);
        if (!prop_set.is_valid()) {
            return Err<std::vector<uint8_t>>(ErrorCode::PropertyNotSupported, "...");
        }
        return prop_set.get_property(SURFACE_PROPERTY_SET, static_cast<uint32_t>(prop));
    }
    
    // Similar for set_surface_property, typed variants, supports check
}
```

**3. Document property types** and typical values in header comments (as done in `logitech.h`).

***

#### Direct KsPropertySet usage

For one-off vendor property access without creating a vendor namespace:

```cpp
#include <duvc-ctl/platform/ks_properties.h>

GUID custom_guid = {/* ... */};
duvc::KsPropertySet props(device);

if (props.is_valid()) {
    auto data = props.get_property(custom_guid, 7);
    if (data.is_ok()) {
        // Process raw bytes
    }
}
```

**Use cases:**

- Prototyping new vendor property support
- Accessing undocumented properties for debugging
- One-off custom integrations

**Production recommendation:** Wrap raw access in typed functions for maintainability and documentation, as demonstrated by the Logitech extension implementation.

## 6. Internal Implementation Details

### 6.1 Device Connection Pool

**Header:** `<duvc-ctl/platform/connection_pool.h>`
**Platform:** Windows only (`#ifdef _WIN32`)
**Namespace:** `duvc` (not `detail`)

RAII wrapper managing DirectShow COM interfaces for a single device. Provides efficient property access without repeated device enumeration and binding.

#### DeviceConnection class

```cpp
class DeviceConnection {
public:
    explicit DeviceConnection(const Device& dev);
    ~DeviceConnection();
    
    // Non-copyable but movable
    DeviceConnection(const DeviceConnection&) = delete;
    DeviceConnection& operator=(const DeviceConnection&) = delete;
    DeviceConnection(DeviceConnection&&) = default;
    DeviceConnection& operator=(DeviceConnection&&) = default;
    
    bool get(CamProp prop, PropSetting& val);
    bool set(CamProp prop, const PropSetting& val);
    
    bool get(VidProp prop, PropSetting& val);
    bool set(VidProp prop, const PropSetting& val);
    
    bool get_range(CamProp prop, PropRange& range);
    bool get_range(VidProp prop, PropRange& range);
    
    bool is_valid() const { return filter_ != nullptr; }
    
private:
    std::unique_ptr<ComApartment> com_;
    void* filter_;      // com_ptr<IBaseFilter>
    void* cam_ctrl_;    // com_ptr<IAMCameraControl>
    void* vid_proc_;    // com_ptr<IAMVideoProcAmp>
};
```

Encapsulates COM interface lifetime for a single camera device.

***

#### Construction and lifetime

```cpp
explicit DeviceConnection(const Device& dev);
~DeviceConnection();
```

**Constructor behavior:**

1. Creates dedicated `ComApartment` for COM initialization
2. Calls `open_device_filter()` to enumerate and bind to matching device
3. Queries `IAMCameraControl` and `IAMVideoProcAmp` interfaces from filter
4. Stores COM smart pointers as `void*` (heap-allocated) to avoid header dependencies

**Exception handling:** If device cannot be opened, sets `filter_ = nullptr`. Constructor does not throw.

**Destructor:** Deletes heap-allocated COM smart pointers, releasing all DirectShow interfaces.

**Validity check:**

```cpp
bool is_valid() const { return filter_ != nullptr; }
```

Always check validity before calling property methods.

***

#### Property operations

**Camera control properties:**

```cpp
bool get(CamProp prop, PropSetting& val);
bool set(CamProp prop, const PropSetting& val);
bool get_range(CamProp prop, PropRange& range);
```

**Video processing properties:**

```cpp
bool get(VidProp prop, PropSetting& val);
bool set(VidProp prop, const PropSetting& val);
bool get_range(VidProp prop, PropRange& range);
```

All methods return `bool` indicating success. Failures occur if:

- Connection is invalid (`is_valid() == false`)
- Property is unsupported (maps to `-1` in DirectShow constants)
- DirectShow COM method fails (returns `FAILED(hr)`)

**Implementation details:**

`get()` operations:

- Map enum to DirectShow constant via `camprop_to_dshow()` / `vidprop_to_dshow()`
- Call `IAMCameraControl::Get()` or `IAMVideoProcAmp::Get()`
- Convert DirectShow `long` values and flags to `PropSetting`
- Extract mode from flags using `from_flag()` (checks `CameraControl_Flags_Auto` bit)

`set()` operations:

- Map enum to DirectShow constant
- Convert `CamMode` to DirectShow flags via `to_flag()`
- Call `IAMCameraControl::Set()` or `IAMVideoProcAmp::Set()`
- Return `SUCCEEDED(hr)` status

`get_range()` operations:

- Call `IAMCameraControl::GetRange()` or `IAMVideoProcAmp::GetRange()`
- Populate `PropRange` with min/max/step/default values
- Extract default mode from flags

***

#### Helper functions (internal)

**Device binding:**

```cpp
static com_ptr<IBaseFilter> open_device_filter(const Device& dev);
```

Enumerates video devices, matches by name and path, binds to `IBaseFilter`. Throws `std::runtime_error` if device not found.

**Interface querying:**

```cpp
static com_ptr<IAMCameraControl> get_cam_ctrl(IBaseFilter* f);
static com_ptr<IAMVideoProcAmp> get_vproc(IBaseFilter* f);
```

Query control interfaces from filter. Returns empty `com_ptr` on failure (device may not support all properties).

**Property mapping:**

```cpp
static long camprop_to_dshow(CamProp p);
static long vidprop_to_dshow(VidProp p);
static long to_flag(CamMode m, bool is_camera_control);
static CamMode from_flag(long flag, bool is_camera_control);
```

Bidirectional conversion between library enums and DirectShow constants. Maps each `CamProp`/`VidProp` value to its corresponding DirectShow property ID.

**DirectShow constants (fallback definitions):**

The implementation defines DirectShow constants if headers are unavailable:

- `CameraControl_*` constants (Pan=0, Tilt=1, Zoom=3, etc.)
- `VideoProcAmp_*` constants (Brightness=0, Contrast=1, etc.)
- Flag constants (`CameraControl_Flags_Auto=0x0001`, etc.)

***

#### No connection pooling/caching

**Important:** Despite the filename `connection_pool`, the current implementation **does not** implement connection pooling or caching. The header comment mentions this was the original intent, but pooling was **removed due to thread safety issues**.

**Current behavior:**

- Each `DeviceConnection` instance creates a new connection
- No global cache or shared connection state
- Connections are independent and non-thread-safe
- The `Camera` class creates temporary connections per operation (see Section 2.2)

**Historical context:** The file originally contained a global connection pool with `get_connection()` / `release_connection()` methods, but these were removed. Only the RAII `DeviceConnection` class remains.

***

#### Usage pattern

`DeviceConnection` is used internally by the `Camera` class. Direct usage:

```cpp
duvc::Device device = duvc::list_devices();
duvc::DeviceConnection conn(device);

if (!conn.is_valid()) {
    std::cerr << "Failed to connect\n";
    return;
}

// Read property
duvc::PropSetting zoom_setting;
if (conn.get(duvc::CamProp::Zoom, zoom_setting)) {
    std::cout << "Zoom: " << zoom_setting.value << "\n";
}

// Write property
duvc::PropSetting new_setting{150, duvc::CamMode::Manual};
conn.set(duvc::CamProp::Zoom, new_setting);

// Query range
duvc::PropRange range;
if (conn.get_range(duvc::CamProp::Zoom, range)) {
    std::cout << "Range: " << range.min << " to " << range.max << "\n";
}
```

**Connection lifetime:** Each `DeviceConnection` holds COM interfaces for the device's lifetime. Creating many connections sequentially is safe but inefficient (requires repeated enumeration). For sustained access, reuse the same connection instance.

***

#### Implementation notes

**COM apartment management:** Each connection creates its own `ComApartment` instance, ensuring COM is initialized in the current thread context. This allows connections from different threads (though not concurrent access to the same connection).

**Pointer storage:** COM smart pointers are stored as `void*` to avoid exposing DirectShow types in the public header. Internally cast to `com_ptr<T>*` for access.

**Move semantics:** The class is default-movable, allowing efficient transfer of ownership (e.g., storing in containers or returning from functions).

**No exceptions in operations:** All property methods return `bool` rather than throwing exceptions, following the library's error handling pattern for internal operations.

### 6.2 COM Helpers

**Header:** `<duvc-ctl/platform/com_helpers.h>`
**Namespace:** `duvc::detail`
**Platform:** Windows only (`#ifdef _WIN32`)

Internal COM utilities for managing DirectShow interfaces and Windows API interactions. These are implementation details not exposed in the public API.

#### com_ptr<T>

```cpp
template <typename T>
class com_ptr {
public:
    com_ptr() noexcept = default;
    explicit com_ptr(T* p) noexcept;
    ~com_ptr();
    
    // Move-only
    com_ptr(com_ptr&& o) noexcept;
    com_ptr& operator=(com_ptr&& o) noexcept;
    
    T* get() const noexcept;
    T** put() noexcept;
    T* operator->() const noexcept;
    explicit operator bool() const noexcept;
    void reset() noexcept;
};
```

Smart pointer for COM interface pointers with automatic reference counting.

**Lifetime management:**

- Constructor from raw pointer takes ownership (does not call `AddRef`)
- Destructor calls `Release()` if pointer is non-null
- Move operations transfer ownership without ref-count changes

**Key methods:**

`get()`: Returns raw pointer without affecting ownership.

`put()`: Returns address for output parameters. Releases current pointer first, allowing COM methods to assign a new interface.

```cpp
com_ptr<IBaseFilter> filter;
hr = moniker->BindToObject(nullptr, nullptr, IID_IBaseFilter, 
                           reinterpret_cast<void**>(filter.put()));
```

`reset()`: Releases current interface and sets pointer to null.

**Non-copyable:** Copying would require `AddRef`, which could introduce bugs. Use move semantics or transfer ownership explicitly.

***

#### com_apartment

```cpp
class com_apartment {
public:
    com_apartment();
    ~com_apartment();
    
    // Non-copyable, non-movable
};
```

RAII wrapper for COM initialization/uninitialization. Ensures COM is properly initialized for the current thread.

**Constructor:**

```cpp
hr_ = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
if (FAILED(hr_) && hr_ != RPC_E_CHANGED_MODE) {
    throw_hr(hr_, "CoInitializeEx");
}
```

Calls `CoInitializeEx` with `COINIT_APARTMENTTHREADED`. If initialization fails (except `RPC_E_CHANGED_MODE`, meaning COM is already initialized), throws an exception via `throw_hr`.

**Destructor:**

```cpp
if (SUCCEEDED(hr_)) {
    CoUninitialize();
}
```

Only calls `CoUninitialize` if constructor successfully initialized COM. This ensures proper cleanup even if thread already had COM initialized.

**Usage pattern:** Each DirectShow operation class (`DirectShowEnumerator`, `DirectShowFilter`, `DeviceConnection`) contains a `com_apartment` member to ensure COM is initialized.

***

#### wide_to_utf8

```cpp
std::string wide_to_utf8(const wchar_t* ws);
```

Converts Windows wide strings (UTF-16) to UTF-8 encoded `std::string`.

**Implementation:**

```cpp
if (!ws) return {};

int sz = WideCharToMultiByte(CP_UTF8, 0, ws, -1, nullptr, 0, nullptr, nullptr);
std::string out(sz > 0 ? sz - 1 : 0, '\0');

if (sz > 0) {
    WideCharToMultiByte(CP_UTF8, 0, ws, -1, out.data(), sz, nullptr, nullptr);
}

return out;
```

Two-pass conversion: first queries size, then allocates and converts. The `-1` size parameter means null-terminated input. The `sz - 1` accounts for null terminator not included in output string.

**Usage:** Primarily for error messages from `_com_error::ErrorMessage()` and DirectShow device names.

***

#### throw_hr

```cpp
void throw_hr(HRESULT hr, const char* where);
```

Throws `std::runtime_error` with formatted HRESULT information.

**Implementation:**

```cpp
_com_error err(hr);
std::ostringstream oss;
oss << where << " failed (hr=0x" << std::hex << hr << ")";

if (err.ErrorMessage()) {
    #ifdef UNICODE
    oss << " - " << wide_to_utf8(err.ErrorMessage());
    #else
    oss << " - " << err.ErrorMessage();
    #endif
}

throw std::runtime_error(oss.str());
```

```
Uses `_com_error` to translate HRESULT to human-readable message. Formats as: `"<operation> failed (hr=0x<hex code>) - <error message>"`.
```

**Example output:**

```
CoInitializeEx failed (hr=0x80010106) - Cannot change thread mode after it is set.
```

**Usage:** Called when COM operations fail unexpectedly, typically during initialization rather than normal property access.

***

### 6.3 DirectShow Integration

**Header:** `<duvc-ctl/platform/directshow_impl.h>`
**Namespace:** `duvc::detail`
**Platform:** Windows only

Internal classes wrapping DirectShow COM interfaces for device enumeration and control.

#### DirectShowMapper

```cpp
class DirectShowMapper {
public:
    static long map_camera_property(CamProp prop);
    static long map_video_property(VidProp prop);
    static long map_camera_mode_to_flags(CamMode mode, bool is_camera_control);
    static CamMode map_flags_to_camera_mode(long flags, bool is_camera_control);
};
```

Static utility class for bidirectional enum ↔ DirectShow constant conversion.

**Property mapping:**

`map_camera_property()`: Converts `CamProp` to DirectShow `CameraControl_*` constants:

- `CamProp::Pan` → `0L` (CameraControl_Pan)
- `CamProp::Tilt` → `1L` (CameraControl_Tilt)
- `CamProp::Zoom` → `3L` (CameraControl_Zoom)
- etc. Returns `-1` for unsupported properties

`map_video_property()`: Converts `VidProp` to DirectShow `VideoProcAmp_*` constants:

- `VidProp::Brightness` → `0L` (VideoProcAmp_Brightness)
- `VidProp::Contrast` → `1L` (VideoProcAmp_Contrast)
- `VidProp::Hue` → `2L` (VideoProcAmp_Hue)
- etc. Returns `-1` for unsupported properties

**Mode/flag mapping:**

`map_camera_mode_to_flags()`: Converts `CamMode` to DirectShow flags:

- `CamMode::Auto` → `0x0001L` (Auto flag)
- `CamMode::Manual` → `0x0002L` (Manual flag)

`map_flags_to_camera_mode()`: Checks flag `& 0x0001` to determine auto mode. Both camera control and video proc amp use identical flag values.

***

#### DirectShowEnumerator

```cpp
class DirectShowEnumerator {
public:
    DirectShowEnumerator();
    ~DirectShowEnumerator();
    
    std::vector<Device> enumerate_devices();
    bool is_device_available(const Device& device);
    Device read_device_info(IMoniker* moniker);
    
    com_ptr<ICreateDevEnum> dev_enum_;
private:
    com_apartment com_;
};
```

Wrapper for DirectShow device enumeration via `ICreateDevEnum`.

**Construction:**

```cpp
HRESULT hr = CoCreateInstance(CLSID_SystemDeviceEnum, nullptr, CLSCTX_INPROC_SERVER,
                               IID_ICreateDevEnum, reinterpret_cast<void**>(dev_enum_.put()));
if (FAILED(hr)) {
    throw std::runtime_error("Failed to create DirectShow device enumerator");
}
```

Creates `ICreateDevEnum` COM object for querying system devices. Throws on failure.

**enumerate_devices():**

1. Calls `CreateClassEnumerator(CLSID_VideoInputDeviceCategory)` to get moniker enumerator
2. Iterates monikers with `Next()`
3. For each moniker, calls `read_device_info()` to extract name/path
4. Returns vector of all valid devices

Returns empty vector if no devices or enumeration fails.

**is_device_available():** Calls `enumerate_devices()` and searches for matching device by path (preferred) or name. Uses case-insensitive comparison via `_wcsicmp`.

**read_device_info():**

```cpp
Device read_device_info(IMoniker* moniker);
```

Extracts device information from moniker:

1. `BindToStorage()` to get `IPropertyBag`
2. Read `FriendlyName` property → `device.name`
3. Read `DevicePath` property → `device.path`
4. If path empty, fallback to `GetDisplayName()` → `device.path`

***

#### DirectShowFilter

```cpp
class DirectShowFilter {
public:
    explicit DirectShowFilter(const Device& device);
    ~DirectShowFilter();
    
    bool is_valid() const;
    
    com_ptr<IAMCameraControl> get_camera_control();
    com_ptr<IAMVideoProcAmp> get_video_proc_amp();
    com_ptr<IKsPropertySet> get_property_set();
    
    com_ptr<IBaseFilter> extract();
private:
    com_apartment com_;
    com_ptr<IBaseFilter> filter_;
    
    com_ptr<IBaseFilter> create_filter(const Device& device);
};
```

Wrapper for `IBaseFilter` with interface querying.

**Construction:** Calls `create_filter()` to bind device moniker to filter object.

**create_filter():**

1. Creates `DirectShowEnumerator` to iterate devices
2. Finds matching device by path or name
3. Calls `moniker->BindToObject()` to get `IBaseFilter`
4. Returns filter or empty pointer if not found

**Interface queries:**

`get_camera_control()`: Queries `IAMCameraControl` interface for PTZ/exposure/focus controls. Returns empty pointer if not supported.

`get_video_proc_amp()`: Queries `IAMVideoProcAmp` interface for brightness/contrast/saturation controls. Returns empty pointer if not supported.

`get_property_set()`: Queries `IKsPropertySet` interface for Kernel Streaming properties (vendor extensions). Returns empty pointer if not supported.

All queries use `QueryInterface()` on the filter. Not all devices support all interfaces.

***

#### DirectShowDeviceConnection

```cpp
class DirectShowDeviceConnection : public IDeviceConnection {
public:
    explicit DirectShowDeviceConnection(const Device& device);
    
    bool is_valid() const override;
    Result<PropSetting> get_camera_property(CamProp prop) override;
    Result<void> set_camera_property(CamProp prop, const PropSetting& setting) override;
    // ... similar for video properties and ranges
    
private:
    DirectShowFilter filter_;
};
```

Implementation of `IDeviceConnection` interface using DirectShow. This is the concrete class instantiated by `create_directshow_connection()`.

**Property operations:**

Each `get/set` method follows this pattern:

1. Query appropriate interface (`get_camera_control()` or `get_video_proc_amp()`)
2. Map property enum to DirectShow constant via `DirectShowMapper`
3. Call DirectShow `Get()` / `Set()` / `GetRange()` method
4. Convert between DirectShow values/flags and library types
5. Return `Result<T>` with success or error code

**Error handling:**

- Interface unavailable → `ErrorCode::PropertyNotSupported`
- Property maps to `-1` → `ErrorCode::PropertyNotSupported`
- COM method fails → `ErrorCode::SystemError`

***

#### Integration with platform interface

The `WindowsPlatformInterface` (from `factory.cpp`) uses these classes:

```cpp
Result<std::vector<Device>> list_devices() override {
    DirectShowEnumerator enumerator;
    return Ok(enumerator.enumerate_devices());
}

Result<bool> is_device_connected(const Device& device) override {
    DirectShowEnumerator enumerator;
    return Ok(enumerator.is_device_available(device));
}

Result<std::unique_ptr<IDeviceConnection>> create_connection(const Device& device) override {
    return Ok(create_directshow_connection(device));
}
```

The `create_directshow_connection()` function instantiates `DirectShowDeviceConnection`, which internally uses `DirectShowFilter` to manage COM interfaces.

***

**No filter graph:** This library does **not** build DirectShow filter graphs or stream video. It only uses the device filter's control interfaces (`IAMCameraControl`, `IAMVideoProcAmp`) for property manipulation.

### 6.4 Windows Internals

**Header:** `src/platform/windows_internal.h`
**Namespace:** `duvc::detail`

Low-level Windows platform utilities and constants for DirectShow integration.

***

#### WindowsUtils

```cpp
class WindowsUtils {
public:
    static bool has_camera_permissions();
    static std::string get_windows_version();
    static bool is_windows_10_or_later();
    static std::string get_last_error_string();
    static std::string error_code_to_string(DWORD error_code);
};
```

Platform diagnostic utilities. **Declared but not implemented** — these are forward declarations for future Windows 10+ camera privacy API integration.

**Intended purposes:**

- `has_camera_permissions()`: Check Windows 10 camera privacy settings via capability access APIs
- `get_windows_version()`: Query OS version for feature detection
- `is_windows_10_or_later()`: Boolean check for modern Windows features
- `get_last_error_string()`: Wrapper for `GetLastError()` + `FormatMessage()`
- `error_code_to_string(error_code)`: Convert specific error codes to readable strings

***

#### DirectShowConstants

```cpp
namespace DirectShowConstants {
    // Camera control (9 constants)
    constexpr long CAMERA_CONTROL_PAN = 0L;           // Horizontal rotation
    constexpr long CAMERA_CONTROL_TILT = 1L;          // Vertical rotation
    constexpr long CAMERA_CONTROL_ROLL = 2L;          // Rotational tilt
    constexpr long CAMERA_CONTROL_ZOOM = 3L;          // Optical/digital zoom
    constexpr long CAMERA_CONTROL_EXPOSURE = 4L;      // Shutter speed
    constexpr long CAMERA_CONTROL_IRIS = 5L;          // Aperture
    constexpr long CAMERA_CONTROL_FOCUS = 6L;         // Lens focus distance
    constexpr long CAMERA_CONTROL_SCANMODE = 7L;      // Interlaced/progressive
    constexpr long CAMERA_CONTROL_PRIVACY = 8L;       // Lens cover/shutter
    
    // Video proc amp (10 constants)
    constexpr long VIDEOPROCAMP_BRIGHTNESS = 0L;      // Luminance level
    constexpr long VIDEOPROCAMP_CONTRAST = 1L;        // Dynamic range
    constexpr long VIDEOPROCAMP_HUE = 2L;             // Color tint (-180° to +180°)
    constexpr long VIDEOPROCAMP_SATURATION = 3L;      // Color intensity
    constexpr long VIDEOPROCAMP_SHARPNESS = 4L;       // Edge enhancement
    constexpr long VIDEOPROCAMP_GAMMA = 5L;           // Mid-tone brightness curve
    constexpr long VIDEOPROCAMP_COLORENABLE = 6L;     // Color/monochrome mode
    constexpr long VIDEOPROCAMP_WHITEBALANCE = 7L;    // Color temperature
    constexpr long VIDEOPROCAMP_BACKLIGHT_COMPENSATION = 8L; // Exposure for backlighting
    constexpr long VIDEOPROCAMP_GAIN = 9L;            // Sensor sensitivity (ISO)
    
    // Control flags (2 constants)
    constexpr long FLAGS_AUTO = 0x0001L;              // Auto control by firmware
    constexpr long FLAGS_MANUAL = 0x0002L;            // Manual control via API
}
```

**Total: 21 constants.** Fallback definitions matching Microsoft DirectShow SDK values for `IAMCameraControl` and `IAMVideoProcAmp` interfaces.

**Purpose:** These are provided as compile-time fallbacks if DirectShow headers are missing or incomplete. Standard Windows SDK defines these in `strmif.h`, but older MinGW or SDK versions may lack them. The values are standardized by Microsoft and will not change.

**Usage:** Referenced throughout DirectShow implementation to map generic property enums to DirectShow-specific constants. For example, `CameraProperty::Pan` maps to `CAMERA_CONTROL_PAN = 0L`.

***

### 6.5 Device Monitoring

**File:** `src/platform/device_monitor.cpp`

Windows device hot-plug detection using `WM_DEVICECHANGE` and `RegisterDeviceNotification()`.

***

#### Architecture

**Global state:**

```cpp
extern DeviceChangeCallback g_device_callback;  // User callback function
extern HWND g_notification_window;              // Message-only window handle
extern HDEVNOTIFY g_device_notify;              // Device notification handle
```

System uses hidden message-only window to receive `WM_DEVICECHANGE` notifications from Windows. Single-instance design — only one callback can be registered at a time.

***

#### device_notification_wndproc

```cpp
static LRESULT CALLBACK device_notification_wndproc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam);
```

Window procedure processing device change messages.

**Implementation details:**

1. Filters for `msg == WM_DEVICECHANGE` only
2. Checks `wParam` for `DBT_DEVICEARRIVAL` (device connected) or `DBT_DEVICEREMOVECOMPLETE` (device disconnected)
3. Verifies `lParam` is `DEV_BROADCAST_DEVICEINTERFACE` type
4. Extracts `dbcc_name` (wide string device path like `\\?\usb#vid_046d&pid_0825#...`)
5. Logs event: `"Device added: ..."` or `"Device removed: ..."`
6. Invokes `g_device_callback(device_added, device_path)` wrapped in try/catch
7. Catches and logs callback exceptions to prevent window procedure crash
8. Falls through to `DefWindowProc()` for all messages

**Thread safety:** Callback invoked synchronously on Windows message thread. User must handle thread synchronization.

***

#### Helper Functions

**register_notification_window_class:**

```cpp
static bool register_notification_window_class();
```

Registers `WNDCLASSW` with:

- Class name: `L"DuvcDeviceNotificationWindow"`
- Window procedure: `device_notification_wndproc`
- Module handle: `GetModuleHandle(nullptr)`

Ignores `ERROR_CLASS_ALREADY_EXISTS` to allow multiple registration attempts. Returns `false` on other errors.

**create_notification_window:**

```cpp
static HWND create_notification_window();
```

Creates invisible message-only window:

- Style: 0 (no WS_VISIBLE)
- Position/size: 0, 0, 0, 0 (hidden)
- Parent: `HWND_MESSAGE` (message-only, no visual presence)
- Title: `L"duvc-ctl Device Monitor"` (for debugging only)

Returns `nullptr` on failure. Window receives no user input, only system notifications.

**register_device_notifications:**

```cpp
static HDEVNOTIFY register_device_notifications(HWND hwnd);
```

Registers window for device interface notifications:

- Populates `DEV_BROADCAST_DEVICEINTERFACE` filter
- Sets `dbcc_classguid = CLSID_VideoInputDeviceCategory` (video capture devices only)
- Calls `RegisterDeviceNotification(hwnd, &filter, DEVICE_NOTIFY_WINDOW_HANDLE)`
- Logs success/failure with `DUVC_LOG_INFO` / `DUVC_LOG_ERROR`

Returns `nullptr` on failure. Only video input devices (cameras, capture cards) trigger notifications.

***

#### Public API

**register_device_change_callback:**

```cpp
void register_device_change_callback(DeviceChangeCallback callback);
```

Initializes hot-plug monitoring. **Single-instance only** — re-registration logs warning and returns early.

**Execution flow:**

1. Check if `g_notification_window` already exists → log warning, return
2. Store `callback` in `g_device_callback`
3. Call `create_notification_window()` → `g_notification_window`
4. On failure: null `g_device_callback`, return
5. Call `register_device_notifications(g_notification_window)` → `g_device_notify`
6. On failure: `DestroyWindow()`, null globals, return
7. Log `"Device change monitoring started"`

**Cleanup on failure:** Automatically destroys window and clears state if registration fails.

**unregister_device_change_callback:**

```cpp
void unregister_device_change_callback();
```

Stops monitoring and cleans up resources:

1. If `g_device_notify`: `UnregisterDeviceNotification()`, null it, log `"Unregistered device notifications"`
2. If `g_notification_window`: `DestroyWindow()`, null it, log `"Destroyed notification window"`
3. Null `g_device_callback`
4. Log `"Device change monitoring stopped"`

**Idempotent:** Safe to call multiple times. Checks null before cleanup operations.

***

#### Callback Contract

```cpp
using DeviceChangeCallback = std::function<void(bool device_added, const std::wstring& device_path)>;
```

**Parameters:**

- `device_added`: `true` for `DBT_DEVICEARRIVAL`, `false` for `DBT_DEVICEREMOVECOMPLETE`
- `device_path`: Raw Windows device path (wide string)

**Thread context:** Called synchronously on Windows message thread. GUI apps have message loop by default; console apps must call `process_pending_device_events()` periodically (from Section 2.1).

**Exception handling:** Exceptions caught and logged; do not propagate to Windows.

***

### 6.6 Factory Implementation

**File:** `src/platform/factory.cpp`

Platform abstraction layer factory. Instantiates platform-specific implementations at runtime.

***

#### WindowsPlatformInterface

```cpp
class WindowsPlatformInterface : public IPlatformInterface {
public:
    Result<std::vector<Device>> list_devices() override;
    Result<bool> is_device_connected(const Device& device) override;
    Result<std::unique_ptr<IDeviceConnection>> create_connection(const Device& device) override;
};
```

Windows DirectShow implementation of `IPlatformInterface`. **Defined locally in factory.cpp** — not exposed in public headers.

***

**list_devices:**

```cpp
Result<std::vector<Device>> list_devices() override {
    try {
        detail::DirectShowEnumerator enumerator;
        auto devices = enumerator.enumerate_devices();
        return Ok(std::move(devices));
    } catch (const std::exception& e) {
        return Err<std::vector<Device>>(ErrorCode::SystemError, e.what());
    }
}
```

Creates temporary `DirectShowEnumerator` (from `directshow_impl.cpp`), calls `enumerate_devices()`, wraps result in `Result<T>`. Catches COM initialization failures, DirectShow errors, and converts to `ErrorCode::SystemError`.

**is_device_connected:**

```cpp
Result<bool> is_device_connected(const Device& device) override {
    try {
        detail::DirectShowEnumerator enumerator;
        return Ok(enumerator.is_device_available(device));
    } catch (const std::exception& e) {
        return Err<bool>(ErrorCode::SystemError, e.what());
    }
}
```

Creates temporary enumerator, checks if device exists in current DirectShow device list. Returns `false` if not found (not an error), `Err` on system failure.

**create_connection:**

```cpp
Result<std::unique_ptr<IDeviceConnection>> create_connection(const Device& device) override {
    try {
        auto connection = detail::create_directshow_connection(device);
        if (!connection) {
            return Err<std::unique_ptr<IDeviceConnection>>(
                ErrorCode::DeviceNotFound, "Failed to create device connection");
        }
        return Ok(std::move(connection));
    } catch (const std::exception& e) {
        return Err<std::unique_ptr<IDeviceConnection>>(ErrorCode::SystemError, e.what());
    }
}
```

Calls `detail::create_directshow_connection(device)` (defined in `directshow_impl.cpp`) to bind to device via DirectShow. Returns `Err(DeviceNotFound)` if `nullptr` returned (device removed between list and connect), `Err(SystemError)` on exceptions.

***

#### create_platform_interface

```cpp
std::unique_ptr<IPlatformInterface> create_platform_interface() {
    #ifdef _WIN32
    return std::make_unique<WindowsPlatformInterface>();
    #else
    return nullptr;
    #endif
}
```

Factory function for platform-specific implementation. Compile-time selection via `#ifdef`.

**Windows:** Returns `WindowsPlatformInterface` wrapping DirectShow APIs.

**Non-Windows platforms:** Returns `nullptr`. Public API functions (in `camera.cpp`, `device.cpp`) check for null and return `Err(Unsupported)` with message `"Platform not supported"`.

**Future platforms:** macOS/Linux support would add `#elif __APPLE__` / `#elif __linux__` branches with AVFoundation/V4L2 implementations.

## 7. Property Reference \& Details

### 7.1 Camera Properties Complete Reference

**Header:** `<duvc-ctl/core/types.h>`
**Enum:** `CamProp`
**DirectShow Interface:** `IAMCameraControl`

All 23 camera property values with descriptions and behaviors. Actual ranges are **device-specific** and must be queried via `camera.get_range(prop)` or `DeviceCapabilities`.

***

#### Absolute Position Properties (9)

**CamProp::Pan**
Horizontal camera rotation (left/right). Mechanically moves camera head or adjusts digital framing.

- **Unit:** Degrees (typically ±180° for PTZ cameras, varies by hardware)
- **Typical range:** -180 to +180, step 1
- **Auto mode:** Available on PTZ cameras with auto-tracking
- **Hardware:** PTZ cameras, webcams with motorized pan

**CamProp::Tilt**
Vertical camera rotation (up/down). Mechanically moves camera head or adjusts digital framing.

- **Unit:** Degrees (typically ±90° for PTZ cameras)
- **Typical range:** -90 to +90, step 1
- **Auto mode:** Available on PTZ cameras with auto-tracking
- **Hardware:** PTZ cameras, webcams with motorized tilt

**CamProp::Roll**
Rotational tilt around optical axis. Rarely supported by consumer hardware.

- **Unit:** Degrees (-180 to +180)
- **Typical range:** -180 to +180, step 1
- **Auto mode:** Usually manual only
- **Hardware:** Professional PTZ cameras, some action cameras

**CamProp::Zoom**
Optical zoom level. Controls lens focal length, not digital zoom.

- **Unit:** Arbitrary zoom steps (device-specific scale)
- **Typical range:** 10 to 100 (1x to 10x zoom), step 1
- **Auto mode:** Rarely available
- **Hardware:** Cameras with optical zoom lens

**CamProp::Exposure**
Exposure time (shutter speed). Controls sensor light integration time.

- **Unit:** Log₂ seconds (e.g., -10 = 1/1024s, -1 = 1/2s, 0 = 1s)
- **Typical range:** -13 to -1 (1/8192s to 1/2s), step 1
- **Auto mode:** Standard (firmware adjusts for scene brightness)
- **Effect:** Lower values = darker/sharper motion, higher = brighter/motion blur

**CamProp::Iris**
Aperture/iris opening. Controls lens f-stop and depth of field. **Rare on webcams** (fixed aperture).

- **Unit:** f-stop * 10 (e.g., 28 = f/2.8, 56 = f/5.6)
- **Typical range:** 10 to 200 (f/1.0 to f/20), step 1
- **Auto mode:** Usually manual only
- **Hardware:** Professional cameras with adjustable aperture

**CamProp::Focus**
Lens focus distance. Adjusts focus from close-up to infinity.

- **Unit:** Arbitrary focus steps (device-specific scale)
- **Typical range:** 0 to 255 (close to infinity), step 1
- **Auto mode:** Standard (continuous autofocus)
- **Hardware:** Cameras with adjustable focus (most webcams)

**CamProp::ScanMode**
Scan mode selection: progressive (0) vs. interlaced (1). **Obsolete for modern cameras.**

- **Unit:** Boolean (0 = progressive, 1 = interlaced)
- **Typical range:** 0 to 1, step 1
- **Auto mode:** Manual only
- **Hardware:** Legacy analog cameras, capture cards

**CamProp::Privacy**
Privacy shutter/lens cover. Mechanically blocks lens or disables sensor.

- **Unit:** Boolean (0 = open, 1 = closed)
- **Typical range:** 0 to 1, step 1
- **Auto mode:** Manual only
- **Hardware:** Business webcams (Logitech, Microsoft), laptops with privacy shutters

***

#### Relative Movement Properties (8)

These properties specify **delta values** for relative adjustments. Not all cameras support relative mode.

**CamProp::PanRelative**
Relative pan movement. Moves camera left (-) or right (+) by specified angle.

**CamProp::TiltRelative**
Relative tilt movement. Moves camera up (+) or down (-) by specified angle.

**CamProp::RollRelative**
Relative roll adjustment. Rotates camera clockwise (+) or counterclockwise (-).

**CamProp::ZoomRelative**
Relative zoom adjustment. Zooms in (+) or out (-) by specified steps.

**CamProp::ExposureRelative**
Relative exposure adjustment. Increases (+) or decreases (-) exposure time.

**CamProp::IrisRelative**
Relative iris adjustment. Opens (+) or closes (-) aperture.

**CamProp::FocusRelative**
Relative focus adjustment. Moves focus closer (+) or farther (-).

***

#### Combined Control Properties (2)

**CamProp::PanTilt**
Combined pan/tilt control. Sets both pan and tilt in single operation. **Rarely supported.**

- **Unit:** Composite value (implementation-defined)
- **Hardware:** High-end PTZ cameras with optimized movement

**CamProp::PanTiltRelative**
Relative pan/tilt movement. Adjusts both axes simultaneously.

***

#### Simple Controls (1)

**CamProp::FocusSimple**
Simplified focus control: near (0), far (1), auto (2). **Logitech extension**, not standard DirectShow.

- **Unit:** Enum (0 = near, 1 = far, 2 = auto)
- **Typical range:** 0 to 2, step 1
- **Hardware:** Logitech webcams (C920, C930e, Brio)

***

#### Digital/Processing Properties (3)

**CamProp::DigitalZoom**
Digital zoom level. Software image cropping/upscaling, not optical zoom.

- **Unit:** Zoom multiplier * 100 (e.g., 100 = 1.0x, 200 = 2.0x)
- **Typical range:** 100 to 400 (1x to 4x), step 10
- **Auto mode:** Manual only
- **Quality:** Lower than optical zoom (interpolation artifacts)

**CamProp::DigitalZoomRelative**
Relative digital zoom adjustment. Increases (+) or decreases (-) digital zoom.

**CamProp::BacklightCompensation**
Backlight compensation level. Adjusts exposure for strong backlighting (e.g., window behind subject).

- **Unit:** Compensation level (0 = off, 1+ = increasing compensation)
- **Typical range:** 0 to 10, step 1
- **Auto mode:** Rarely available
- **Effect:** Brightens foreground when background is overexposed

***

#### Lamp/Flash (1)

**CamProp::Lamp**
Camera lamp/flash control. Enables auxiliary lighting (LED ring, flash).

- **Unit:** Boolean (0 = off, 1 = on)
- **Typical range:** 0 to 1, step 1
- **Auto mode:** Manual only
- **Hardware:** Document cameras, industrial cameras with built-in lighting

***

### Property Range Querying

```cpp
auto range_result = camera.get_range(CamProp::Exposure);
if (range_result.is_ok()) {
    auto range = range_result.value();
    // range.min, range.max, range.step, range.default_val, range.default_mode
}
```

**Hardware variance:** Ranges are **not standardized**. A Logitech C920 may report exposure range -13 to -1, while a generic webcam reports -7 to 0. Always query device-specific ranges.

**Unsupported properties:** `get_range()` returns `Err(ErrorCode::NotSupported)` for properties not implemented by hardware/driver.

### 7.2 Video Properties Complete Reference

**Header:** `<duvc-ctl/core/types.h>`
**Enum:** `VidProp`
**DirectShow Interface:** `IAMVideoProcAmp`

All 10 video processing properties with descriptions and behaviors. These control **digital image processing**, not camera hardware. Actual ranges are **device-specific** and must be queried via `camera.get_range(prop)` or `DeviceCapabilities`.

***

#### VidProp::Brightness

Luminance level. Adds/subtracts constant value to all pixels (black point adjustment).

- **Unit:** Arbitrary brightness steps (device-specific scale)
- **Typical range:** -64 to +64, step 1 (or 0 to 255 for some cameras)
- **Default:** 0 (neutral)
- **Auto mode:** Rarely available (auto-exposure handles this)
- **Effect:** Negative = darker image, positive = brighter image
- **Technical:** Linear offset applied in YUV/RGB space before gamma correction

**Usage note:** For exposure control, prefer `CamProp::Exposure`. Brightness is post-processing and can clip highlights/shadows.

***

#### VidProp::Contrast

Dynamic range. Scales pixel values around midpoint (white point adjustment).

- **Unit:** Arbitrary contrast steps (device-specific scale)
- **Typical range:** 0 to 100, step 1 (some cameras use -50 to +50)
- **Default:** 50 or 0 (neutral, device-dependent)
- **Auto mode:** Manual only
- **Effect:** Lower = flatter/washed out, higher = stronger blacks/whites
- **Technical:** Multiplies pixel values by scaling factor around 128 (8-bit) or equivalent

**Usage note:** Values above 80-90 can cause clipping. Combine with brightness adjustment for best results.

***

#### VidProp::Hue

Color tint. Rotates hue angle in HSV/HSL color space.

- **Unit:** Degrees or arbitrary hue steps
- **Typical range:** -180 to +180 degrees, step 1 (or 0 to 360)
- **Default:** 0 (no shift)
- **Auto mode:** Manual only
- **Effect:** -180° = cyan/green shift, 0 = natural, +180° = magenta/red shift
- **Technical:** Rotates H component in HSV space, preserves S and V

**Usage note:** For color correction, prefer `VidProp::WhiteBalance`. Hue is global shift, not adaptive.

***

#### VidProp::Saturation

Color intensity. Scales chroma values in color space.

- **Unit:** Arbitrary saturation steps (device-specific scale)
- **Typical range:** 0 to 200, step 1 (0 = grayscale, 100 = normal, 200 = oversaturated)
- **Default:** 100 (neutral)
- **Auto mode:** Manual only
- **Effect:** 0 = black \& white, 100 = natural colors, 200 = vivid/oversaturated
- **Technical:** Scales S component in HSV space, preserves H and V

**Usage note:** Values above 150 can cause color clipping and unnatural tones.

***

#### VidProp::Sharpness

Edge enhancement. Applies high-pass filter to increase perceived detail.

- **Unit:** Arbitrary sharpness steps (device-specific scale)
- **Typical range:** 0 to 100, step 1 (or 0 to 255)
- **Default:** 50 (moderate sharpening)
- **Auto mode:** Manual only
- **Effect:** 0 = soft/blurry, 50 = natural, 100 = over-sharpened with halos
- **Technical:** Unsharp mask or Laplacian edge enhancement filter

**Usage note:** High values (>75) introduce ringing artifacts and noise amplification. Use conservatively.

***

#### VidProp::Gamma

Mid-tone brightness curve. Adjusts gamma correction exponent.

- **Unit:** Gamma exponent * 100 (e.g., 100 = γ=1.0, 220 = γ=2.2)
- **Typical range:** 1 to 500 (γ=0.01 to γ=5.0), step 1
- **Default:** 100 or 220 (γ=1.0 or γ=2.2, device-dependent)
- **Auto mode:** Manual only
- **Effect:** <100 = brighter midtones (flatter curve), >100 = darker midtones (steeper curve)
- **Technical:** Applies power-law transformation: \$ V_{out} = V_{in}^{\gamma} \$

**Usage note:** Standard sRGB gamma is 2.2 (220). Do not change unless matching specific display/workflow.

***

#### VidProp::ColorEnable

Color mode toggle. Switches between color and monochrome output.

- **Unit:** Boolean (0 = monochrome, 1 = color)
- **Typical range:** 0 to 1, step 1
- **Default:** 1 (color)
- **Auto mode:** Manual only
- **Effect:** 0 = grayscale output, 1 = full color
- **Technical:** Zeroes chroma channels (U/V in YUV) when disabled

**Usage note:** Equivalent to setting `VidProp::Saturation = 0`, but may be hardware-accelerated.

***

#### VidProp::WhiteBalance

Color temperature adjustment. Shifts white point to compensate for lighting.

- **Unit:** Kelvin (K) or arbitrary color temperature steps
- **Typical range:** 2800 to 6500 K, step 10 (or arbitrary 0-255 scale)
- **Default:** 4000-5000 K (neutral/daylight)
- **Auto mode:** **Standard** (auto white balance, AWB)
- **Effect:** Lower = warmer (yellow/orange), higher = cooler (blue)
- **Technical:** Applies RGB channel gains to neutralize color cast

**Common presets:**

- 2800 K = incandescent/tungsten (warm orange)
- 4000 K = fluorescent (cool white)
- 5500 K = daylight (neutral)
- 6500 K = overcast/shade (cool blue)

**Usage note:** Auto mode is highly recommended. Manual tuning requires color reference card.

***

#### VidProp::BacklightCompensation

Backlight compensation level. Adjusts exposure for strong backlighting.

- **Unit:** Compensation level (0 = off, 1-10 = increasing compensation)
- **Typical range:** 0 to 10, step 1 (some cameras use 0/1 boolean)
- **Default:** 0 (off)
- **Auto mode:** Rarely available
- **Effect:** Brightens foreground when background is overexposed (e.g., window behind subject)
- **Technical:** Adjusts metering zones to prioritize foreground exposure

**Overlap:** Some cameras expose this via `CamProp::BacklightCompensation` instead. Check both.

**Usage note:** Alternative to adjusting `CamProp::Exposure` manually. Less effective than HDR tone mapping.

***

#### VidProp::Gain

Sensor gain level. Digital/analog amplification of sensor signal (ISO equivalent).

- **Unit:** Gain multiplier or dB (device-specific scale)
- **Typical range:** 0 to 100 (or 0 to 255), step 1
- **Default:** 0 or auto (device-dependent)
- **Auto mode:** **Standard** (auto-gain control, AGC)
- **Effect:** Higher gain = brighter image in low light, but more noise
- **Technical:** Amplifies sensor readout before digitization (analog gain) or after (digital gain)

**Relationship to exposure:**

- Low light: increase gain OR increase exposure time
- Gain is faster (no motion blur) but noisier
- Exposure time is cleaner but causes motion blur

**Usage note:** Auto mode is recommended. Manual tuning requires controlled lighting. High gain (>50) introduces significant noise.

***

### Property Range Querying

```cpp
auto range_result = camera.get_range(VidProp::Brightness);
if (range_result.is_ok()) {
    auto range = range_result.value();
    // range.min, range.max, range.step, range.default_val, range.default_mode
}
```

**Hardware variance:** Ranges are **not standardized**. A Logitech C920 may report brightness range -64 to +64, while a generic webcam reports 0 to 255. Always query device-specific ranges.

**Unsupported properties:** `get_range()` returns `Err(ErrorCode::NotSupported)` for properties not implemented by hardware/driver.

***

### Auto Mode Support

**Commonly auto-capable:**

- `VidProp::WhiteBalance` — auto white balance (AWB) is standard on most cameras
- `VidProp::Gain` — auto gain control (AGC) is standard

**Rarely auto-capable:**

- `VidProp::Brightness`, `VidProp::Contrast`, `VidProp::Hue`, `VidProp::Saturation`, `VidProp::Sharpness`, `VidProp::Gamma` — these are post-processing adjustments, not firmware-controlled

Check `PropertyCapability::supports_auto()` or `range.default_mode` to verify auto support for specific device.

### 7.3 Property Range Discovery

**Header:** `<duvc-ctl/core/types.h>`
**Structs:** `PropRange`, `PropSetting`

Query device-specific property ranges before setting values. Ranges are **not standardized** — each camera reports different min/max/step values.

***

#### PropRange Structure

```cpp
struct PropRange {
    int min;                  // Minimum supported value
    int max;                  // Maximum supported value
    int step;                 // Step size between valid values
    int default_val;          // Default value
    CamMode default_mode;     // Default control mode (Auto/Manual)
    
    bool is_valid(int value) const;
    int clamp(int value) const;
};
```

**Fields:**

- `min`: Lowest value camera accepts (e.g., exposure -13, brightness -64)
- `max`: Highest value camera accepts (e.g., exposure -1, brightness +64)
- `step`: Increment between valid values (typically 1, sometimes 10 or 100)
- `default_val`: Factory default value recommended by manufacturer
- `default_mode`: Whether property defaults to `CamMode::Auto` or `CamMode::Manual`

***

#### get_range Usage

**Camera properties:**

```cpp
Camera camera(0);
auto result = camera.get_range(CamProp::Exposure);

if (result.is_ok()) {
    PropRange range = result.value();
    std::cout << "Exposure range: " << range.min << " to " << range.max << "\n";
    std::cout << "Step: " << range.step << ", default: " << range.default_val << "\n";
    std::cout << "Default mode: " << (range.default_mode == CamMode::Auto ? "Auto" : "Manual") << "\n";
} else {
    std::cerr << "Error: " << result.error().message() << "\n";
}
```

**Video properties:**

```cpp
auto result = camera.get_range(VidProp::Brightness);
if (result.is_ok()) {
    PropRange range = result.value();
    // range.min, range.max, range.step, range.default_val, range.default_mode
}
```

**Error handling:**

- `ErrorCode::NotSupported`: Property not implemented by hardware/driver
- `ErrorCode::DeviceNotFound`: Camera disconnected
- `ErrorCode::SystemError`: DirectShow API failure

***

#### is_valid Method

**Signature:**

```cpp
bool PropRange::is_valid(int value) const;
```

Checks if value is within `[min, max]` and aligned to `step` boundary.

**Implementation:**

```cpp
return value >= min && value <= max && ((value - min) % step == 0);
```

**Example usage:**

```cpp
PropRange range = camera.get_range(CamProp::Pan).value();

if (range.is_valid(45)) {
    camera.set(CamProp::Pan, {45, CamMode::Manual});  // Safe to set
} else {
    std::cerr << "Invalid value 45 for pan (range: " 
              << range.min << " to " << range.max << ")\n";
}
```

**Step alignment:**

- If `min=0, max=100, step=10`, valid values are `{0, 10, 20, ..., 100}`
- `is_valid(15)` returns `false` (not aligned to step)
- `is_valid(20)` returns `true`

***

#### clamp Method

**Signature:**

```cpp
int PropRange::clamp(int value) const;
```

Constrains value to valid range and rounds to nearest step boundary.

**Implementation:**

```cpp
if (value <= min) return min;
if (value >= max) return max;
// Round to nearest step
int steps = (value - min + step / 2) / step;
return min + steps * step;
```

**Example usage:**

```cpp
PropRange range = camera.get_range(CamProp::Zoom).value();

int user_input = 123;  // Potentially invalid
int safe_value = range.clamp(user_input);

camera.set(CamProp::Zoom, {safe_value, CamMode::Manual});  // Always valid
```

**Rounding behavior:**

- `clamp(-50)` with `min=0` → returns `0`
- `clamp(200)` with `max=100` → returns `100`
- `clamp(47)` with `min=0, step=10` → returns `50` (rounds 47 to nearest 50)
- `clamp(43)` with `min=0, step=10` → returns `40` (rounds 43 to nearest 40)

**Use case:** UI sliders can pass any integer; `clamp()` ensures value is always accepted by hardware.

***

#### PropSetting Structure

```cpp
struct PropSetting {
    int value;          // Property value
    CamMode mode;       // Control mode (Auto/Manual)
};
```

Used when setting properties via `camera.set()`. Must specify both value and mode.

**Example:**

```cpp
// Manual control with specific value
camera.set(CamProp::Exposure, {-5, CamMode::Manual});

// Auto control (value ignored by firmware, but should match default_val)
PropRange range = camera.get_range(CamProp::WhiteBalance).value();
camera.set(VidProp::WhiteBalance, {range.default_val, CamMode::Auto});
```


***

### 7.4 Auto vs Manual Modes

**Enum:** `CamMode`

```cpp
enum class CamMode {
    Auto,    // Firmware-controlled (camera adjusts automatically)
    Manual   // Application-controlled (fixed value)
};
```


***

#### Mode Behavior

**Auto mode:**

- Firmware continuously adjusts property based on scene (e.g., auto-exposure adapts to lighting)
- `value` field in `PropSetting` is **ignored** by camera — firmware uses its own algorithm
- Reading property via `camera.get()` returns **current firmware-computed value**, not user-set value
- Typical auto properties: `CamProp::Exposure`, `CamProp::Focus`, `VidProp::WhiteBalance`, `VidProp::Gain`

**Manual mode:**

- Firmware uses fixed value provided by application
- `value` field in `PropSetting` is **required** and enforced
- Reading property via `camera.get()` returns last value set by application
- Value persists until changed or camera reset

***

#### Checking Auto Support

**Method 1: Check range.default_mode**

```cpp
PropRange range = camera.get_range(CamProp::Focus).value();

if (range.default_mode == CamMode::Auto) {
    std::cout << "Focus supports auto mode\n";
    camera.set(CamProp::Focus, {range.default_val, CamMode::Auto});
} else {
    std::cout << "Focus is manual-only\n";
    camera.set(CamProp::Focus, {range.default_val, CamMode::Manual});
}
```

**Method 2: PropertyCapability::supports_auto()**

```cpp
DeviceCapabilities caps(device);
if (caps.get_camera_capability(CamProp::Exposure).supports_auto()) {
    std::cout << "Exposure supports auto mode\n";
}
```

**Implementation:**

```cpp
bool PropertyCapability::supports_auto() const {
    return range.default_mode == CamMode::Auto;
}
```


***

#### Switching Modes

**Manual → Auto:**

```cpp
// Enable auto-exposure
PropRange range = camera.get_range(CamProp::Exposure).value();
camera.set(CamProp::Exposure, {range.default_val, CamMode::Auto});
```

**Auto → Manual:**

```cpp
// Get current auto-computed value
PropSetting current = camera.get(CamProp::Exposure).value();

// Lock to current value
camera.set(CamProp::Exposure, {current.value, CamMode::Manual});
```

**Manual value adjustment:**

```cpp
// Read current manual value
PropSetting setting = camera.get(CamProp::Exposure).value();

// Increase by 1 step
PropRange range = camera.get_range(CamProp::Exposure).value();
int new_value = range.clamp(setting.value + range.step);

camera.set(CamProp::Exposure, {new_value, CamMode::Manual});
```


***

#### Mode Limitations

**Property-specific restrictions:**

- **Brightness, Contrast, Hue, Saturation, Sharpness, Gamma:** Usually **manual-only** (post-processing adjustments, not firmware-controlled)
- **Exposure, Focus, WhiteBalance, Gain:** Usually support **both auto and manual**
- **Pan, Tilt, Zoom:** Usually **manual-only** (mechanical positioning)
- **Privacy, ColorEnable, ScanMode:** Always **manual-only** (binary switches)

**Hardware variance:** Some cameras report auto support for properties that don't actually respond to auto mode. Always test on target hardware.

**Attempted auto on manual-only property:** DirectShow may return `E_PROP_ID_UNSUPPORTED` or silently fall back to manual mode. Library returns `Err(ErrorCode::NotSupported)` when auto mode fails.

***

#### Mode Persistence

**Cross-session behavior:**

- Manual values typically persist across application restarts (stored in camera firmware)
- Auto mode typically resets to auto on camera power-cycle or USB reconnect
- Some cameras reset all properties to defaults on disconnect

**Reading current mode:**

```cpp
PropSetting setting = camera.get(CamProp::Exposure).value();

if (setting.mode == CamMode::Auto) {
    std::cout << "Exposure is in auto mode (current value: " << setting.value << ")\n";
} else {
    std::cout << "Exposure is manual (fixed value: " << setting.value << ")\n";
}
```

**Best practice:** Always query current mode before modifying values to avoid unintended mode switches.

## 8. Usage Patterns \& Best Practices

### 8.1 Basic Usage Patterns

**Header:** `<duvc-ctl/duvc.hpp>`
**Namespace:** `duvc`

All library functionality is accessed through a single umbrella header providing both RAII-style and quick API patterns.

***

#### Pattern 1: Device Enumeration

**List all connected cameras:**

```cpp
#include <duvc-ctl/duvc.hpp>

auto devices = duvc::list_devices();

for (size_t i = 0; i < devices.size(); ++i) {
    std::cout << "[" << i << "] " << devices[i].name << "\n"
              << "    " << devices[i].path << "\n";
}
```

**Output example:**

```
 Logitech BRIO
    \\?\usb#vid_046d&pid_085e#...
 Integrated Webcam
    \\?\usb#vid_0bda&pid_58c2#...
```

**Returns:** `std::vector<Device>`
**Device struct:**

- `name`: Friendly device name (e.g., "Logitech C920")
- `path`: Unique system path (DirectShow device path on Windows)
- `index`: Ordinal index in enumeration (matches vector position)

**Empty list:** No cameras connected or DirectShow enumeration failed.

***

#### Pattern 2: Open Camera by Index

**Method 1: Direct construction**

```cpp
Camera camera(0);  // Open first camera

if (!camera.is_valid()) {
    std::cerr << "Camera not available\n";
    return;
}
```

**Method 2: Result-based (recommended)**

```cpp
auto result = duvc::open_camera(0);

if (!result.is_ok()) {
    std::cerr << "Error: " << result.error().message() << "\n";
    return;
}

Camera camera = std::move(result).value();
```

**Difference:** Direct construction throws no exception on failure; `is_valid()` checks connection state. `open_camera()` returns detailed error codes via `Result<Camera>`.

***

#### Pattern 3: Get Property Value

**Read current exposure setting:**

```cpp
Camera camera(0);

auto result = camera.get(CamProp::Exposure);

if (result.is_ok()) {
    PropSetting setting = result.value();
    std::cout << "Exposure: " << setting.value 
              << " (" << (setting.mode == CamMode::Auto ? "auto" : "manual") << ")\n";
} else {
    std::cerr << "Error: " << result.error().message() << "\n";
}
```

**Output example:**

```
Exposure: -6 (manual)
```

**Returns:** `Result<PropSetting>`
**PropSetting:**

- `value`: Current property value (device-specific scale)
- `mode`: `CamMode::Auto` or `CamMode::Manual`

**Common errors:**

- `ErrorCode::NotSupported`: Property not implemented by hardware
- `ErrorCode::DeviceNotFound`: Camera disconnected

***

#### Pattern 4: Set Property Value

**Set brightness to fixed value:**

```cpp
Camera camera(0);

PropSetting setting{30, CamMode::Manual};  // brightness=30, manual mode
auto result = camera.set(VidProp::Brightness, setting);

if (result.is_ok()) {
    std::cout << "Brightness set to 30\n";
} else {
    std::cerr << "Error: " << result.error().message() << "\n";
}
```

**Enable auto-exposure:**

```cpp
PropRange range = camera.get_range(CamProp::Exposure).value();

PropSetting auto_setting{range.default_val, CamMode::Auto};
camera.set(CamProp::Exposure, auto_setting);
```

**Returns:** `Result<void>`
**Best practice:** Always query `get_range()` before setting to ensure value is within valid bounds.

***

#### Pattern 5: Query Property Range

**Check valid exposure values:**

```cpp
Camera camera(0);

auto result = camera.get_range(CamProp::Exposure);

if (result.is_ok()) {
    PropRange range = result.value();
    std::cout << "Exposure range: " << range.min << " to " << range.max << "\n"
              << "Step: " << range.step << ", default: " << range.default_val << "\n"
              << "Default mode: " << (range.default_mode == CamMode::Auto ? "Auto" : "Manual") << "\n";
}
```

**Output example:**

```
Exposure range: -13 to -1
Step: 1, default: -6
Default mode: Auto
```

**Use case:** Validating user input before calling `set()` to prevent out-of-range errors.

***

#### Pattern 6: Safe Value Clamping

**Handle arbitrary user input:**

```cpp
Camera camera(0);
PropRange range = camera.get_range(CamProp::Zoom).value();

int user_input = 150;  // Potentially invalid
int safe_value = range.clamp(user_input);  // Constrain to [min, max]

camera.set(CamProp::Zoom, {safe_value, CamMode::Manual});
```

**Behavior:**

- Clamps `user_input` to `[range.min, range.max]`
- Rounds to nearest `range.step` boundary
- Always returns valid value accepted by hardware

***

#### Pattern 7: Quick API (No Result Handling)

**Simplified one-shot operations:**

```cpp
#include <duvc-ctl/duvc.hpp>

auto devices = duvc::list_devices();
if (devices.empty()) return;

PropSetting setting;
if (duvc::get(devices, CamProp::Exposure, setting)) {
    std::cout << "Exposure: " << setting.value << "\n";
}

setting = {-5, CamMode::Manual};
if (duvc::set(devices, CamProp::Exposure, setting)) {
    std::cout << "Exposure set\n";
}
```

**Returns:** `bool` (true = success, false = failure)
**Use case:** CLI tools, scripts, throwaway code where detailed error messages aren't needed.

**Limitations:** No error code access; failures are silent.

***

#### Pattern 8: Enumerate All Capabilities

**Dump all supported properties:**

```cpp
Camera camera(0);

// Camera properties
const CamProp cam_props[] = {
    CamProp::Pan, CamProp::Tilt, CamProp::Zoom,
    CamProp::Exposure, CamProp::Focus, /* ... */
};

for (CamProp prop : cam_props) {
    auto range_result = camera.get_range(prop);
    if (!range_result.is_ok()) continue;  // Unsupported
    
    PropRange range = range_result.value();
    PropSetting current = camera.get(prop).value();
    
    std::cout << "CamProp::" << /* property name */ << "\n"
              << "  Range: [" << range.min << ", " << range.max << "]\n"
              << "  Current: " << current.value 
              << " (" << (current.mode == CamMode::Auto ? "auto" : "manual") << ")\n";
}

// Video properties
const VidProp vid_props[] = {
    VidProp::Brightness, VidProp::Contrast, /* ... */
};

for (VidProp prop : vid_props) {
    auto range_result = camera.get_range(prop);
    if (!range_result.is_ok()) continue;
    
    // Same logic as camera properties
}
```

**Use case:** Configuration UI, capability discovery, debugging hardware support.

***

#### Pattern 9: RAII Resource Management

**Automatic cleanup:**

```cpp
{
    Camera camera(0);  // Opens DirectShow connection
    
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
    // ... use camera ...
    
}  // Camera destructor releases DirectShow interfaces automatically
```

**Move semantics:**

```cpp
Camera create_camera(int index) {
    return Camera(index);  // Move construction
}

Camera cam1 = create_camera(0);
Camera cam2 = std::move(cam1);  // cam1 is now invalid
```

**Non-copyable:** `Camera` cannot be copied (prevents accidental double-release of COM interfaces).

***

#### Pattern 10: Error Handling Strategies

**Strategy 1: Check every result**

```cpp
auto get_result = camera.get(CamProp::Exposure);
if (!get_result.is_ok()) {
    handle_error(get_result.error());
    return;
}
PropSetting setting = get_result.value();
```

**Strategy 2: Chain with early return**

```cpp
auto range = camera.get_range(CamProp::Zoom);
if (!range) return;  // Result converts to bool

camera.set(CamProp::Zoom, {range.value().max, CamMode::Manual});
```

**Strategy 3: Quick API for non-critical operations**

```cpp
PropSetting brightness;
if (duvc::get(device, VidProp::Brightness, brightness)) {
    // Use brightness...
}
// Failure is silently ignored
```

**Best practice:** Use full `Result` API for application-critical operations; quick API for optional features.

### 8.2 Advanced Patterns

**Header:** `<duvc-ctl/duvc.hpp>`

Advanced use cases for multi-camera systems, hot-plug handling, and vendor-specific extensions.

***

#### Pattern 1: Multi-Camera Management

**Control multiple cameras simultaneously:**

```cpp
#include <duvc-ctl/duvc.hpp>

auto devices = duvc::list_devices();
std::vector<Camera> cameras;

// Open all cameras
for (const auto& device : devices) {
    cameras.emplace_back(device);
}

// Configure all cameras identically
PropSetting exposure{-7, CamMode::Manual};
for (auto& camera : cameras) {
    camera.set(CamProp::Exposure, exposure);
}

// Read from specific camera
PropSetting setting = cameras.get(CamProp::Exposure).value();
std::cout << "Camera 0 exposure: " << setting.value << "\n";
```

**Per-camera configuration:**

```cpp
// Camera 0: high exposure for dark scene
cameras.set(CamProp::Exposure, {-3, CamMode::Manual});

// Camera 1: low exposure for bright scene
cameras.set(CamProp::Exposure, {-10, CamMode::Manual});

// Camera 2: auto-exposure
PropRange range = cameras.get_range(CamProp::Exposure).value();
cameras.set(CamProp::Exposure, {range.default_val, CamMode::Auto});
```

**Thread-safe access:** `Camera` objects are **not** thread-safe. Each camera should be accessed from a single thread, or protected by mutex.

```cpp
std::mutex camera_mutexes;

std::thread worker1([&]() {
    std::lock_guard lock(camera_mutexes);
    cameras.set(CamProp::Zoom, {50, CamMode::Manual});
});

std::thread worker2([&]() {
    std::lock_guard lock(camera_mutexes);
    cameras.set(CamProp::Zoom, {75, CamMode::Manual});
});

worker1.join();
worker2.join();
```


***

#### Pattern 2: Hot-Plug Detection

**Monitor device connection/disconnection events:**

```cpp
#include <duvc-ctl/duvc.hpp>

void on_device_change(bool added, const std::string& device_path) {
    if (added) {
        std::cout << "Camera connected: " << device_path << "\n";
        
        // Re-enumerate to get Device object
        auto devices = duvc::list_devices();
        for (const auto& dev : devices) {
            if (dev.path == device_path) {
                Camera camera(dev);
                // Configure newly connected camera...
                break;
            }
        }
    } else {
        std::cout << "Camera disconnected: " << device_path << "\n";
        // Clean up Camera handles referencing this device
    }
}

// Register callback
duvc::register_device_change_callback(on_device_change);

// Run application...

// Cleanup
duvc::unregister_device_change_callback();
```

**Limitations:**

- Only **one callback** can be registered at a time (subsequent calls replace previous callback)
- Callback is invoked from **Windows message pump thread** — keep logic minimal or dispatch to worker thread
- Callback receives `device_path` (string), not `Device` object — must re-enumerate to match

***

#### Pattern 3: Validate Device Connection

**Check if camera is still accessible:**

```cpp
Camera camera(0);

// ... time passes ...

auto devices = duvc::list_devices();
if (devices.empty() || !duvc::is_device_connected(devices)) {
    std::cerr << "Camera disconnected!\n";
    return;
}

// Safe to use camera
auto result = camera.get(CamProp::Exposure);
if (!result.is_ok()) {
    std::cerr << "Camera no longer responds\n";
}
```

**Use case:** Long-running applications that need to detect unplugged cameras before attempting operations.

**Performance:** `is_device_connected()` performs lightweight DirectShow enumeration (< 10ms on typical systems).

***

#### Pattern 4: Hot-Plug Recovery

**Automatically reconnect to camera:**

```cpp
class CameraManager {
public:
    CameraManager(int device_index) : device_index_(device_index) {
        reconnect();
    }
    
    bool reconnect() {
        auto devices = duvc::list_devices();
        if (device_index_ >= devices.size()) {
            std::cerr << "Device index out of range\n";
            return false;
        }
        
        camera_ = std::make_unique<Camera>(devices[device_index_]);
        return camera_->is_valid();
    }
    
    Camera& get() { return *camera_; }
    
    bool is_connected() {
        auto devices = duvc::list_devices();
        return device_index_ < devices.size() && 
               duvc::is_device_connected(devices[device_index_]);
    }
    
private:
    int device_index_;
    std::unique_ptr<Camera> camera_;
};

// Usage
CameraManager manager(0);

while (true) {
    if (!manager.is_connected()) {
        std::cout << "Camera lost, attempting reconnect...\n";
        if (manager.reconnect()) {
            std::cout << "Reconnected!\n";
        }
    } else {
        manager.get().set(CamProp::Exposure, {-6, CamMode::Manual});
    }
    
    std::this_thread::sleep_for(std::chrono::seconds(1));
}
```


***

#### Pattern 5: Logitech Vendor Extensions

**Access Logitech-specific properties:**

```cpp
#include <duvc-ctl/duvc.hpp>
#include <duvc-ctl/vendor/logitech.h>

auto devices = duvc::list_devices();
Camera camera(devices);

// Check Logitech support
auto support_result = duvc::logitech::supports_logitech_properties(devices);
if (!support_result.is_ok() || !support_result.value()) {
    std::cerr << "Not a Logitech camera or unsupported\n";
    return;
}

// Enable RightLight (auto-exposure enhancement)
auto result = duvc::logitech::set_logitech_property_typed<uint32_t>(
    devices, duvc::logitech::LogitechProperty::RightLight, 1);

if (result.is_ok()) {
    std::cout << "RightLight enabled\n";
}

// Read LED indicator state
auto led_result = duvc::logitech::get_logitech_property_typed<uint32_t>(
    devices, duvc::logitech::LogitechProperty::LedIndicator);

if (led_result.is_ok()) {
    std::cout << "LED mode: " << led_result.value() << "\n";
}
```

**Available Logitech properties:**

- `RightLight`: Auto-exposure and brightness optimization (0 = off, 1-3 = intensity levels)
- `RightSound`: Audio processing and noise cancellation (bool)
- `FaceTracking`: Face tracking for auto-framing (bool)
- `LedIndicator`: LED control (0 = off, 1 = on, 2 = blink)
- `ProcessorUsage`: CPU optimization hints (device-specific values)
- `RawDataBits`: Bit depth configuration (8/10/12)
- `FocusAssist`: Focus assist beam (bool)
- `VideoStandard`: Video standard selection (NTSC/PAL enum)
- `DigitalZoomROI`: Region of interest coordinates (struct with x/y/width/height)
- `TiltPan`: Combined tilt/pan absolute positioning (struct with tilt/pan values)

**Type safety:**

```
- `get_logitech_property_typed<T>()` and `set_logitech_property_typed<T>()` require type `T` to be **trivially copyable** and match property's binary layout
```

- For boolean properties, use `uint32_t` (not `bool`) — DirectShow stores booleans as 4-byte integers
- For raw byte access, use `get_logitech_property()` / `set_logitech_property()` which return `std::vector<uint8_t>`

**Error handling:**

- `ErrorCode::NotSupported`: Property not available on this camera model
- `ErrorCode::SystemError`: DirectShow KsProperty call failed
- Check `supports_logitech_properties()` before accessing any Logitech properties

***

#### Pattern 6: Vendor Extension Detection

**Determine if camera supports vendor properties:**

```cpp
auto devices = duvc::list_devices();

for (const auto& device : devices) {
    std::cout << device.name << ":\n";
    
    auto logitech_support = duvc::logitech::supports_logitech_properties(device);
    if (logitech_support.is_ok() && logitech_support.value()) {
        std::cout << "  - Logitech extensions available\n";
        
        // Test specific property support
        auto rightlight = duvc::logitech::get_logitech_property_typed<uint32_t>(
            device, duvc::logitech::LogitechProperty::RightLight);
        if (rightlight.is_ok()) {
            std::cout << "    - RightLight: " << rightlight.value() << "\n";
        }
    }
}
```

**Fallback strategy:** If vendor extensions fail, use standard DirectShow properties (exposure, brightness, etc.) which work across all cameras.

***

#### Pattern 7: Low-Level DirectShow Access

**Direct COM interface usage (advanced):**

```cpp
#include <duvc-ctl/core/connection_pool.h>

// DeviceConnection provides low-level DirectShow access
duvc::DeviceConnection conn(devices);

if (!conn.is_valid()) {
    std::cerr << "Failed to open connection\n";
    return;
}

// Efficient repeated operations without Result overhead
PropSetting setting;
if (conn.get(CamProp::Exposure, setting)) {
    std::cout << "Exposure: " << setting.value << "\n";
}

if (conn.set(CamProp::Exposure, {-7, CamMode::Manual})) {
    std::cout << "Exposure updated\n";
}
```

**When to use `DeviceConnection`:**

- High-frequency property polling (> 100 Hz)
- Performance-critical loops where `Result<T>` overhead matters
- Custom DirectShow integration requiring raw COM interfaces

**Limitations:**

- No automatic error propagation (returns `bool`, not `Result<T>`)
- Requires manual connection validity checks via `is_valid()`
- Throws `std::runtime_error` on construction failure (no graceful error handling)

***

#### Pattern 8: Persistent Configuration

**Save and restore camera settings:**

```cpp
struct CameraConfig {
    int exposure;
    CamMode exposure_mode;
    int brightness;
    int contrast;
    // ... other properties
};

// Save
CameraConfig save_config(Camera& camera) {
    CameraConfig config;
    
    auto exp = camera.get(CamProp::Exposure).value();
    config.exposure = exp.value;
    config.exposure_mode = exp.mode;
    
    auto bright = camera.get(VidProp::Brightness).value();
    config.brightness = bright.value;
    
    // ... save other properties
    
    return config;
}

// Restore
void restore_config(Camera& camera, const CameraConfig& config) {
    camera.set(CamProp::Exposure, {config.exposure, config.exposure_mode});
    camera.set(VidProp::Brightness, {config.brightness, CamMode::Manual});
    // ... restore other properties
}

// Serialize to JSON/file
void save_to_file(const CameraConfig& config, const std::string& path) {
    std::ofstream file(path);
    file << "exposure=" << config.exposure << "\n"
         << "exposure_mode=" << (config.exposure_mode == CamMode::Auto ? "auto" : "manual") << "\n"
         << "brightness=" << config.brightness << "\n";
}
```

**Hardware reset behavior:** Some cameras reset all properties to defaults on power cycle or USB reconnect. Always restore configuration after hot-plug events.

***

#### Pattern 9: Capability-Driven UI

**Generate UI controls based on device capabilities:**

```cpp
Camera camera(0);

// Enumerate supported properties
struct PropertyInfo {
    std::string name;
    PropRange range;
    PropSetting current;
    bool auto_capable;
};

std::vector<PropertyInfo> enumerate_properties(Camera& camera) {
    std::vector<PropertyInfo> properties;
    
    const CamProp cam_props[] = {CamProp::Exposure, CamProp::Focus, /* ... */};
    
    for (CamProp prop : cam_props) {
        auto range_result = camera.get_range(prop);
        if (!range_result.is_ok()) continue;  // Unsupported
        
        PropertyInfo info;
        info.name = /* property name string */;
        info.range = range_result.value();
        info.current = camera.get(prop).value();
        info.auto_capable = (info.range.default_mode == CamMode::Auto);
        
        properties.push_back(info);
    }
    
    return properties;
}

// Use in Qt/wxWidgets/etc
void create_ui(Camera& camera) {
    auto properties = enumerate_properties(camera);
    
    for (const auto& prop : properties) {
        // Create slider with range [prop.range.min, prop.range.max]
        // Set slider value to prop.current.value
        // Add auto checkbox if prop.auto_capable
    }
}
```

**Use case:** Configuration tools, camera test utilities, OBS Studio plugins.

***

#### Pattern 10: Error Recovery Strategies

**Handle transient DirectShow failures:**

```cpp
template<typename Func>
auto retry_on_failure(Func&& func, int max_attempts = 3) {
    for (int attempt = 0; attempt < max_attempts; ++attempt) {
        auto result = func();
        if (result.is_ok()) {
            return result;
        }
        
        if (result.error().code() == ErrorCode::DeviceNotFound) {
            return result;  // Don't retry, camera is gone
        }
        
        // Retry on transient errors
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    
    return func();  // Final attempt
}

// Usage
auto result = retry_on_failure([&]() {
    return camera.set(CamProp::Exposure, {-7, CamMode::Manual});
});
```

**Common transient errors:** DirectShow occasionally returns `E_FAIL` or `HRESULT` errors on first access after device re-enumeration. Retrying typically succeeds.

### 8.3 Error Handling Strategies

**Header:** `<duvc-ctl/core/result.h>`

Comprehensive error handling using `Result<T>` type and `ErrorCode` enum.

***

#### Error Code Reference

**Enum:** `ErrorCode`


| Error Code | Description | Common Causes |
| :-- | :-- | :-- |
| `Success` | Operation succeeded | (not returned in `Result<T>`) |
| `DeviceNotFound` | Camera disconnected or not enumerated | USB unplug, driver failure |
| `DeviceBusy` | Camera in use by another application | OBS Studio, Skype, Teams active |
| `PropertyNotSupported` | Property not implemented by hardware | Unsupported `CamProp`/`VidProp` |
| `InvalidValue` | Value outside valid range | Out-of-bounds property value |
| `PermissionDenied` | Insufficient access rights | Admin privileges required |
| `SystemError` | DirectShow/COM failure | Driver crash, HRESULT error |
| `InvalidArgument` | Invalid function parameter | Null pointer, invalid index |
| `NotImplemented` | Feature unavailable on platform | Non-Windows platform |

**Convert to string:**

```cpp
const char* error_str = duvc::to_string(ErrorCode::DeviceNotFound);
// Returns: "Device not found or disconnected"
```


***

#### Result Type API

**Template:** `Result<T>`

```cpp
template<typename T>
class Result {
public:
    bool is_ok() const;        // true if contains value
    bool is_error() const;     // true if contains error
    
    const T& value() const &;  // Get value (throws if error)
    T&& value() &&;            // Move value (throws if error)
    
    const Error& error() const;// Get error (throws if success)
    
    T value_or(const T& default_value) const; // Get value or default
    
    explicit operator bool() const; // Implicit bool conversion
};
```

**Specialization for void:**

```cpp
Result<void> set(CamProp prop, const PropSetting& setting);

// No value() method, only is_ok()/is_error()
```


***

#### Pattern 1: Basic Error Checking

**Check success before accessing value:**

```cpp
auto result = camera.get(CamProp::Exposure);

if (result.is_ok()) {
    PropSetting setting = result.value();
    std::cout << "Exposure: " << setting.value << "\n";
} else {
    std::cerr << "Error: " << result.error().message() << "\n";
}
```

**Boolean conversion:**

```cpp
if (result) {  // Equivalent to result.is_ok()
    PropSetting setting = result.value();
}
```


***

#### Pattern 2: Error Code Inspection

**Handle specific error types:**

```cpp
auto result = camera.set(CamProp::Exposure, {-5, CamMode::Manual});

if (!result.is_ok()) {
    switch (result.error().code()) {
        case ErrorCode::DeviceNotFound:
            std::cerr << "Camera disconnected - reconnecting...\n";
            // Attempt reconnection
            break;
        
        case ErrorCode::PropertyNotSupported:
            std::cerr << "Exposure not supported, falling back to brightness\n";
            camera.set(VidProp::Brightness, {30, CamMode::Manual});
            break;
        
        case ErrorCode::InvalidValue:
            std::cerr << "Value out of range\n";
            // Query range and retry
            break;
        
        case ErrorCode::DeviceBusy:
            std::cerr << "Camera in use by another application\n";
            break;
        
        default:
            std::cerr << "Unknown error: " << result.error().description() << "\n";
            break;
    }
}
```


***

#### Pattern 3: Error Information

**Error class methods:**

```cpp
class Error {
public:
    ErrorCode code() const;           // Get error code enum
    const std::string& message() const; // Get error message
    std::string description() const;  // Full description
};
```

**Example usage:**

```cpp
auto result = camera.get_range(CamProp::Focus);

if (result.is_error()) {
    const auto& err = result.error();
    
    std::cerr << "Error code: " << static_cast<int>(err.code()) << "\n"
              << "Message: " << err.message() << "\n"
              << "Description: " << err.description() << "\n";
}
```


***

#### Pattern 4: Default Values

**Provide fallback on error:**

```cpp
// Get brightness or default to 0
PropSetting brightness = camera.get(VidProp::Brightness).value_or({0, CamMode::Manual});

// Get range or default range
PropRange range = camera.get_range(CamProp::Zoom).value_or(PropRange{0, 100, 1, 50, CamMode::Manual});
```


***

#### Pattern 5: Early Return

**Simplify error propagation:**

```cpp
Result<void> configure_camera(Camera& camera) {
    auto exp_result = camera.set(CamProp::Exposure, {-7, CamMode::Manual});
    if (!exp_result.is_ok()) {
        return exp_result;  // Propagate error
    }
    
    auto bright_result = camera.set(VidProp::Brightness, {30, CamMode::Manual});
    if (!bright_result.is_ok()) {
        return bright_result;
    }
    
    return Ok();  // Success
}

// Usage
auto result = configure_camera(camera);
if (!result.is_ok()) {
    std::cerr << "Configuration failed: " << result.error().message() << "\n";
}
```


***

#### Pattern 6: Retry Logic

**Handle transient errors:**

```cpp
template<typename Func>
auto retry_on_busy(Func&& func, int max_retries = 3, int delay_ms = 100) {
    for (int attempt = 0; attempt < max_retries; ++attempt) {
        auto result = func();
        
        if (result.is_ok()) {
            return result;
        }
        
        if (result.error().code() == ErrorCode::DeviceBusy) {
            std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));
            continue;
        }
        
        // Non-retryable error
        return result;
    }
    
    return func();  // Final attempt
}

// Usage
auto result = retry_on_busy([&]() {
    return camera.set(CamProp::Exposure, {-6, CamMode::Manual});
});
```


***

#### Pattern 7: HRESULT Decoding

**Get detailed DirectShow errors:**

```cpp
#include <duvc-ctl/util/error_decoder.h>

auto result = camera.get(CamProp::Exposure);

if (result.is_error() && result.error().code() == ErrorCode::SystemError) {
    // SystemError indicates DirectShow/COM failure
    std::cerr << "DirectShow error occurred\n";
    
    // Get diagnostic info
    std::string diag = duvc::get_diagnostic_info();
    std::cerr << "Diagnostics:\n" << diag << "\n";
}
```

**HRESULT helpers:**

```cpp
// Decode HRESULT to human-readable string
std::string decode_hresult(HRESULT hr);

// Get detailed error info (facility, code, etc.)
std::string get_hresult_details(HRESULT hr);

// Check error categories
bool is_device_error(HRESULT hr);
bool is_permission_error(HRESULT hr);
```


***

#### Pattern 8: Validation Before Operations

**Prevent errors proactively:**

```cpp
// Validate camera is accessible
if (!camera.is_valid()) {
    std::cerr << "Camera not valid\n";
    return;
}

// Validate property is supported
auto range_result = camera.get_range(CamProp::Exposure);
if (!range_result.is_ok()) {
    std::cerr << "Exposure not supported by this camera\n";
    return;
}

// Validate value is in range
PropRange range = range_result.value();
int user_value = -5;

if (!range.is_valid(user_value)) {
    std::cerr << "Value " << user_value << " out of range ["
              << range.min << ", " << range.max << "]\n";
    user_value = range.clamp(user_value);
}

// Now safe to set
camera.set(CamProp::Exposure, {user_value, CamMode::Manual});
```


***

#### Pattern 9: Logging and Diagnostics

**Comprehensive error logging:**

```cpp
void log_error(const duvc::Error& error) {
    std::ofstream log("camera_errors.log", std::ios::app);
    
    auto now = std::chrono::system_clock::now();
    auto time = std::chrono::system_clock::to_time_t(now);
    
    log << "[" << std::ctime(&time) << "] "
        << "ErrorCode: " << static_cast<int>(error.code()) << " "
        << "Message: " << error.message() << "\n";
}

// Usage
auto result = camera.set(CamProp::Exposure, {-5, CamMode::Manual});
if (!result.is_ok()) {
    log_error(result.error());
}
```

**System diagnostics:**

```cpp
// Get platform/driver info for troubleshooting
std::string diag = duvc::get_diagnostic_info();
std::cout << "System info:\n" << diag << "\n";
```


***

#### Pattern 10: Exception-Free API

**No exceptions thrown by library:**

All errors are returned via `Result<T>`. Only exception is `std::bad_variant_access` if calling `.value()` on error result.

**Safe value access:**

```cpp
// BAD: May throw std::bad_variant_access
PropSetting setting = camera.get(CamProp::Exposure).value();

// GOOD: Check before accessing
auto result = camera.get(CamProp::Exposure);
if (result.is_ok()) {
    PropSetting setting = result.value();
}

// GOOD: Use value_or
PropSetting setting = camera.get(CamProp::Exposure).value_or({-6, CamMode::Manual});
```


***

#### Pattern 11: Graceful Degradation

**Fall back to supported properties:**

```cpp
// Try to enable auto-focus, fall back to manual if unsupported
auto focus_range = camera.get_range(CamProp::Focus);

if (focus_range.is_ok() && focus_range.value().default_mode == CamMode::Auto) {
    camera.set(CamProp::Focus, {focus_range.value().default_val, CamMode::Auto});
} else {
    // Auto-focus not supported, set manual focus to middle of range
    if (focus_range.is_ok()) {
        int mid = (focus_range.value().min + focus_range.value().max) / 2;
        camera.set(CamProp::Focus, {mid, CamMode::Manual});
    }
}
```


***

#### Pattern 12: Bulk Error Handling

**Aggregate errors from multiple operations:**

```cpp
struct ConfigError {
    std::string property;
    duvc::Error error;
};

std::vector<ConfigError> apply_config(Camera& camera, const Config& config) {
    std::vector<ConfigError> errors;
    
    auto exp_result = camera.set(CamProp::Exposure, config.exposure);
    if (!exp_result.is_ok()) {
        errors.push_back({"Exposure", exp_result.error()});
    }
    
    auto bright_result = camera.set(VidProp::Brightness, config.brightness);
    if (!bright_result.is_ok()) {
        errors.push_back({"Brightness", bright_result.error()});
    }
    
    // Continue with other properties...
    
    return errors;
}

// Usage
auto errors = apply_config(camera, config);
if (!errors.empty()) {
    std::cerr << errors.size() << " configuration errors:\n";
    for (const auto& err : errors) {
        std::cerr << "  " << err.property << ": " << err.error.message() << "\n";
    }
}
```


***

#### Common Error Scenarios

**Device disconnected mid-operation:**

```cpp
auto result = camera.get(CamProp::Exposure);

if (result.error().code() == ErrorCode::DeviceNotFound) {
    // Re-enumerate devices
    auto devices = duvc::list_devices();
    if (!devices.empty()) {
        camera = Camera(devices);
    }
}
```

**Property not supported:**

```cpp
auto result = camera.set(CamProp::Pan, {45, CamMode::Manual});

if (result.error().code() == ErrorCode::PropertyNotSupported) {
    std::cerr << "Pan not supported by this camera\n";
    // Try alternative property or skip
}
```

**Camera in use:**

```cpp
auto result = camera.set(CamProp::Exposure, {-5, CamMode::Manual});

if (result.error().code() == ErrorCode::DeviceBusy) {
    std::cerr << "Camera in use - close other applications (Skype, Teams, OBS)\n";
}
```

**Invalid value:**

```cpp
auto result = camera.set(CamProp::Zoom, {9999, CamMode::Manual});

if (result.error().code() == ErrorCode::InvalidValue) {
    // Query valid range
    auto range = camera.get_range(CamProp::Zoom).value();
    std::cerr << "Valid range: [" << range.min << ", " << range.max << "]\n";
    
    // Clamp and retry
    int clamped = range.clamp(9999);
    camera.set(CamProp::Zoom, {clamped, CamMode::Manual});
}
```

**System error (DirectShow failure):**

```cpp
if (result.error().code() == ErrorCode::SystemError) {
    std::cerr << "DirectShow error: " << result.error().message() << "\n";
    
    // Get detailed diagnostics
    std::string diag = duvc::get_diagnostic_info();
    std::cerr << "Diagnostics:\n" << diag << "\n";
}
```

### 8.4 Thread Safety Guidelines

**Critical COM Limitation:** `duvc-ctl` uses DirectShow COM interfaces that are **bound to the thread that creates them**. COM objects cannot be accessed from any thread other than the one that initialized them.

***

#### COM Threading Model

**DirectShow apartment threading:**

Each `Camera` or `DeviceConnection` initializes a COM apartment on the thread that constructs it. All subsequent operations on that object **must** occur on the same thread.

```cpp
// CORRECT: Camera used on creating thread
Camera camera(0);  // COM initialized on this thread
camera.set(CamProp::Exposure, {-5, CamMode::Manual});  // Same thread - OK

// WRONG: Camera accessed from different thread
Camera camera(0);  // COM initialized on main thread
std::thread t([&camera]() {
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});  // CRASH! Wrong thread
});
```

**Why this crashes:** DirectShow COM interfaces are **single-threaded apartment (STA)** objects. Calling methods from a different thread violates COM apartment rules and results in undefined behavior, crashes, or `RPC_E_WRONG_THREAD` errors.

***

#### Rule 1: Thread Affinity

**Each Camera is bound to its creating thread:**

```cpp
// Thread 1 creates camera
Camera camera(0);

// Thread 2 tries to use it - WILL FAIL
std::thread t([&camera]() {
    auto result = camera.get(CamProp::Exposure);  // COM violation!
});
```

**Solution:** Create separate `Camera` instances per thread:

```cpp
std::thread t1([]() {
    Camera camera(0);  // COM initialized for thread 1
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
});

std::thread t2([]() {
    Camera camera(0);  // Separate COM context for thread 2
    camera.set(VidProp::Brightness, {30, CamMode::Manual});
});
```


***

#### Rule 2: No Moving Between Threads

**Camera objects cannot be moved between threads:**

```cpp
Camera camera(0);  // Created on main thread

// WRONG: Attempting to transfer ownership
std::thread t([camera = std::move(camera)]() {
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});  // Still bound to main thread COM!
});
```

**Explanation:** Moving a `Camera` object transfers its member data, but the underlying COM interfaces remain bound to the original thread's apartment. Accessing them from another thread violates COM rules.

***

#### Pattern 1: Thread-Local Cameras

**Safe:** Each thread creates and owns its camera:

```cpp
void camera_worker(int device_index) {
    Camera camera(device_index);  // COM initialized here
    
    while (running) {
        camera.set(CamProp::Exposure, {-5, CamMode::Manual});
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    // camera destroyed, COM cleaned up
}

std::thread t1(camera_worker, 0);
std::thread t2(camera_worker, 1);
```


***

#### Pattern 2: Message Queue (Recommended)

**Dispatch commands to dedicated camera thread:**

```cpp
class CameraWorker {
public:
    CameraWorker(int device_index) : running_(true) {
        // Create camera on worker thread
        thread_ = std::thread([this, device_index]() {
            Camera camera(device_index);  // COM bound to this thread
            
            while (running_) {
                std::unique_lock<std::mutex> lock(mutex_);
                cv_.wait(lock, [this]() { return !queue_.empty() || !running_; });
                
                if (!running_) break;
                
                auto cmd = queue_.front();
                queue_.pop();
                lock.unlock();
                
                // Execute on camera's thread
                camera.set(CamProp::Exposure, {cmd.value, CamMode::Manual});
            }
        });
    }
    
    ~CameraWorker() {
        running_ = false;
        cv_.notify_one();
        thread_.join();
    }
    
    void set_exposure(int value) {
        std::lock_guard<std::mutex> lock(mutex_);
        queue_.push({value});
        cv_.notify_one();
    }
    
private:
    std::thread thread_;
    std::queue<Command> queue_;
    std::mutex mutex_;
    std::condition_variable cv_;
    std::atomic<bool> running_;
};

// Usage - thread-safe
CameraWorker worker(0);
worker.set_exposure(-7);  // Called from any thread
```


***

#### Pattern 3: Mutex Limitation

**Mutex protects against concurrent access, but does NOT solve COM threading:**

```cpp
Camera camera(0);  // Created on main thread
std::mutex mutex;

// WRONG: Mutex doesn't fix COM threading
std::thread t([&]() {
    std::lock_guard<std::mutex> lock(mutex);
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});  // Still COM violation!
});
```

**Mutex is only useful** when multiple code paths on the **same thread** need to access the camera:

```cpp
Camera camera(0);
std::mutex mutex;

// Both on main thread - mutex prevents races
void callback1() {
    std::lock_guard<std::mutex> lock(mutex);
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
}

void callback2() {
    std::lock_guard<std::mutex> lock(mutex);
    auto result = camera.get(CamProp::Exposure);
}
```


***

#### Global Functions Thread Safety

| Function | Thread-Safe? | COM Restriction |
| :-- | :-- | :-- |
| `list_devices()` | Yes | Creates temporary COM context per call |
| `is_device_connected()` | Yes | Creates temporary COM context per call |
| `register_device_change_callback()` | **No** | Must call from main thread |
| `Camera` object | **No** | Bound to creating thread |
| `DeviceConnection` | **No** | Bound to creating thread |

**Hot-plug callbacks:**

Callbacks are invoked on Windows message pump thread. Dispatch heavy work to worker threads:

```cpp
duvc::register_device_change_callback([](bool added, const std::string& path) {
    // Running on Windows message thread!
    
    // WRONG: Create camera here
    // Camera camera(devices);  // COM on message thread
    
    // CORRECT: Dispatch to worker
    std::async(std::launch::async, [added, path]() {
        auto devices = duvc::list_devices();
        Camera camera(devices);  // COM on async thread
    });
});
```


***

#### Summary: COM Threading Rules

1. **Thread affinity:** Each `Camera` must be used only on its creating thread
2. **No transfer:** Cannot move/pass `Camera` objects between threads
3. **Per-thread instances:** Create separate `Camera` instances in each thread
4. **Message passing:** Use message queues to communicate with camera threads
5. **Mutex limitation:** Mutex does NOT solve COM threading violations

**Violation symptoms:** Access violations, `E_FAIL` errors, crashes, `RPC_E_WRONG_THREAD` errors.

***

### 8.5 Performance Optimization

**Goal:** Minimize overhead while respecting COM threading constraints.

***

#### Core Optimization Principles

**Expensive operations:**

- **Device enumeration** (`list_devices()`) - USB bus scanning + DirectShow binding
- **Camera construction** - COM initialization + DirectShow graph setup
- **Property operations** (`get()`/`set()`) - DirectShow interface calls
- **Range queries** (`get_range()`) - DirectShow capability queries

**Inexpensive operations:**

- Result type checking (`is_ok()`, `is_error()`)
- Value validation (`is_valid()`, `clamp()`)
- Device struct copies

***

#### Pattern 1: Cache Device Enumeration

**Problem:** Repeated enumeration is expensive:

```cpp
// SLOW: Enumerate every iteration
for (int i = 0; i < 100; ++i) {
    auto devices = duvc::list_devices();  // Expensive USB scan
    Camera camera(devices);
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
}
```

**Solution:** Enumerate once, reuse:

```cpp
// FAST: One-time enumeration
auto devices = duvc::list_devices();
Camera camera(devices);

for (int i = 0; i < 100; ++i) {
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
}
```

**Benefit:** Eliminates repeated USB bus scanning overhead.

***

#### Pattern 2: Reuse Camera Objects

**Problem:** Construction overhead:

```cpp
// SLOW: Recreate camera every iteration
for (int i = 0; i < 100; ++i) {
    Camera camera(0);  // COM init + DirectShow binding
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
}
```

**Solution:** Create once:

```cpp
// FAST: Reuse camera object
Camera camera(0);
for (int i = 0; i < 100; ++i) {
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
}
```

**Benefit:** Amortizes COM initialization and DirectShow graph setup.

***

#### Pattern 3: Batch Property Changes

**Minimize DirectShow round-trips:**

```cpp
// SLOW: Unnecessary repeated sets
for (int frame = 0; frame < 100; ++frame) {
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
    capture_frame();
}

// FAST: Set once
camera.set(CamProp::Exposure, {-5, CamMode::Manual});
for (int frame = 0; frame < 100; ++frame) {
    capture_frame();
}
```


***

#### Pattern 4: Cache Property Ranges

**Query capabilities once:**

```cpp
// SLOW: Query every iteration
for (int value = -10; value <= 0; ++value) {
    PropRange range = camera.get_range(CamProp::Exposure).value();
    if (range.is_valid(value)) {
        camera.set(CamProp::Exposure, {value, CamMode::Manual});
    }
}

// FAST: Cache range
PropRange range = camera.get_range(CamProp::Exposure).value();
for (int value = -10; value <= 0; ++value) {
    if (range.is_valid(value)) {
        camera.set(CamProp::Exposure, {value, CamMode::Manual});
    }
}
```


***

#### Pattern 5: Low-Level DeviceConnection

**Bypass Result<T> for hot loops:**

```cpp
// Normal API: Result wrapper overhead
Camera camera(0);
for (int i = 0; i < 10000; ++i) {
    auto result = camera.set(CamProp::Exposure, {-5, CamMode::Manual});
}

// Low-level API: Direct boolean return
duvc::DeviceConnection conn(devices);
for (int i = 0; i < 10000; ++i) {
    conn.set(CamProp::Exposure, {-5, CamMode::Manual});  // Returns bool
}
```

**Trade-off:** Faster in tight loops, but less error information and throws on construction failure.

***

#### Pattern 6: Parallel Multi-Camera Setup

**Configure cameras concurrently:**

```cpp
auto devices = duvc::list_devices();

// Serial: Process cameras sequentially
for (const auto& device : devices) {
    Camera camera(device);
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
}

// Parallel: Process cameras concurrently
std::vector<std::future<void>> futures;
for (const auto& device : devices) {
    futures.push_back(std::async(std::launch::async, [device]() {
        Camera camera(device);  // COM on this thread
        camera.set(CamProp::Exposure, {-5, CamMode::Manual});
    }));
}
for (auto& f : futures) f.get();
```

**Benefit:** Near-linear speedup with number of cameras (assuming independent USB controllers).

***

#### Pattern 7: Lazy Connection

**First operation triggers connection:**

```cpp
Camera camera(0);  // Fast: No COM connection yet

// Connection created on first use
auto result = camera.get(CamProp::Exposure);

// Subsequent calls reuse connection
camera.set(CamProp::Brightness, {30, CamMode::Manual});
```

**Optimization:** Perform initialization operations during application startup, not in performance-critical paths.

***

#### Pattern 8: Avoid Validation Overhead

**Skip validation for known-good values:**

```cpp
// Safe: Validate user input
PropRange range = camera.get_range(CamProp::Zoom).value();
int safe_value = range.clamp(user_input);
camera.set(CamProp::Zoom, {safe_value, CamMode::Manual});

// Fast: Skip validation for constants
camera.set(CamProp::Zoom, {50, CamMode::Manual});  // Known valid
```


***

#### Pattern 9: Minimize Data Copies

**Pass by reference, use move semantics:**

```cpp
// SLOW: Copy device structs
void configure_camera(Device device) {  // Copies struct
    Camera camera(device);
}

// FAST: Pass by const reference
void configure_camera(const Device& device) {
    Camera camera(device);
}

// FAST: Move when transferring ownership
void configure_camera(Device&& device) {
    Camera camera(std::move(device));
}
```


***

#### Pattern 10: Profile Before Optimizing

**Identify actual bottlenecks:**

```cpp
// Use profiling tools to identify hotspots:
// - Visual Studio Profiler (Windows)
// - gprof (Linux)
// - Valgrind (Linux)
// - perf (Linux)

// Measure specific operations:
auto start = std::chrono::high_resolution_clock::now();
camera.set(CamProp::Exposure, {-5, CamMode::Manual});
auto end = std::chrono::high_resolution_clock::now();
auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
std::cout << "Operation took " << duration.count() << " µs\n";
```


***

#### Optimization Priority

1. **Cache** `list_devices()` result - Eliminates repeated USB enumeration
2. **Reuse** `Camera` objects - Amortizes COM/DirectShow initialization
3. **Batch** property changes - Reduces DirectShow interface calls
4. **Cache** property ranges - Avoids repeated capability queries
5. **Parallelize** multi-camera operations - Leverages concurrent hardware access
6. Use `DeviceConnection` for hot loops - Reduces wrapper overhead
7. **Profile** to find real bottlenecks - Don't optimize prematurely

**Key insight:** Most performance gains come from reducing the **number** of expensive operations (enumeration, construction) rather than optimizing individual operations.

## 9. Build System \& Integration

### 9.1 CMake Integration

**Using duvc-ctl in your CMake project:**[file:e3a8e954]

#### FetchContent (Recommended)

```cmake
cmake_minimum_required(VERSION 3.16)
project(my_camera_app)

include(FetchContent)

FetchContent_Declare(
    duvc-ctl
    GIT_REPOSITORY https://github.com/allanhanan/duvc-ctl.git
    GIT_TAG        v2.0.0  # Or main for latest
)

# Configure options before making available
set(DUVC_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(DUVC_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(DUVC_BUILD_CLI OFF CACHE BOOL "" FORCE)

FetchContent_MakeAvailable(duvc-ctl)

add_executable(my_app main.cpp)
target_link_libraries(my_app PRIVATE duvc::core)
```


#### find_package (Installed Library)

```cmake
cmake_minimum_required(VERSION 3.16)
project(my_camera_app)

# Find installed duvc-ctl
find_package(duvc-ctl 2.0 REQUIRED)

add_executable(my_app main.cpp)
target_link_libraries(my_app PRIVATE duvc::core)
```


#### add_subdirectory (Vendored)

```cmake
cmake_minimum_required(VERSION 3.16)
project(my_camera_app)

# Configure options
set(DUVC_BUILD_TESTS OFF CACHE BOOL "")
set(DUVC_BUILD_CLI OFF CACHE BOOL "")

add_subdirectory(third_party/duvc-ctl)

add_executable(my_app main.cpp)
target_link_libraries(my_app PRIVATE duvc::core)
```


***

#### Available CMake Targets

| Target | Description | Link | Include |
| :-- | :-- | :-- | :-- |
| `duvc::core` | Shared library (DLL) | Automatic | `<duvc-ctl/duvc.hpp>` |
| `duvc::core-static` | Static library | Automatic | `<duvc-ctl/duvc.hpp>` |
| `duvc::c-api` | C ABI library | Automatic | `<duvc-ctl/c/api.h>` |

**Usage:**

```cmake
target_link_libraries(my_app PRIVATE duvc::core)      # Shared lib
target_link_libraries(my_app PRIVATE duvc::core-static)  # Static lib
target_link_libraries(my_app PRIVATE duvc::c-api)     # C API
```


***

#### CMake Build Options

**Core library:**


| Option | Default | Description |
| :-- | :-- | :-- |
| `DUVC_BUILD_SHARED` | `ON` | Build shared library (duvc-core.dll) |
| `DUVC_BUILD_STATIC` | `ON` | Build static library (duvc-core.lib) |
| `DUVC_BUILD_C_API` | `ON` | Build C API for language bindings |

**Optional components:**


| Option | Default | Description |
| :-- | :-- | :-- |
| `DUVC_BUILD_CLI` | `ON` | Build command-line tool |
| `DUVC_BUILD_PYTHON` | `OFF` | Build Python bindings |
| `DUVC_BUILD_TESTS` | `OFF` | Build test suite |
| `DUVC_BUILD_EXAMPLES` | `OFF` | Build example applications |

**Development:**


| Option | Default | Description |
| :-- | :-- | :-- |
| `DUVC_WARNINGS_AS_ERRORS` | `OFF` | Treat warnings as errors |
| `DUVC_INSTALL` | `ON` | Enable install targets |
| `DUVC_INSTALL_CMAKE_CONFIG` | `ON` | Install CMake config files |

**Configuration:**

```cmake
# Minimal integration (no extras)
set(DUVC_BUILD_CLI OFF CACHE BOOL "")
set(DUVC_BUILD_TESTS OFF CACHE BOOL "")
set(DUVC_BUILD_EXAMPLES OFF CACHE BOOL "")
FetchContent_MakeAvailable(duvc-ctl)

# Development build (all features)
set(DUVC_BUILD_TESTS ON CACHE BOOL "")
set(DUVC_BUILD_EXAMPLES ON CACHE BOOL "")
set(DUVC_WARNINGS_AS_ERRORS ON CACHE BOOL "")
FetchContent_MakeAvailable(duvc-ctl)
```


***

#### Exported Variables

When using `find_package(duvc-ctl)`:

```cmake
duvc-ctl_FOUND            # TRUE if found
duvc-ctl_VERSION          # Version string (e.g., "2.0.0")
duvc-ctl_INCLUDE_DIRS     # Include directories
duvc-ctl_LIBRARIES        # All library targets
```


***

### 9.2 Building from Source

**Prerequisites:**

- **Windows 10/11** (Windows 8.1 compatible but not tested)
- **Compiler:** Visual Studio 2019/2022 or MinGW-w64 GCC 9+
- **CMake 3.16+**
- **Python 3.8+** (for Python bindings only)
- **Git** (for fetching dependencies)

***

#### Quick Build (Visual Studio)

```bash
git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl

# Configure
cmake -B build -G "Visual Studio 17 2022" -A x64

# Build Release
cmake --build build --config Release

# Run tests
cd build && ctest --config Release --output-on-failure
```


***

#### MinGW-w64 Build

```bash
# Configure with MinGW
cmake -B build -G "MinGW Makefiles" \
    -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build build -j8

# Install
cmake --install build --prefix install
```


***

#### Custom Build (All Options)

```bash
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

cmake --build build --config Release
cmake --install build --config Release
```


***

#### Python Bindings Build

```bash
# Install Python dev dependencies
pip install pybind11

# Configure with Python enabled
cmake -B build -G "Visual Studio 17 2022" -A x64 \
    -DDUVC_BUILD_PYTHON=ON \
    -DPython_EXECUTABLE=C:/Python39/python.exe

# Build
cmake --build build --config Release

# Install Python package
cd build/python
pip install .
```


***

#### Install Locations

**Default install prefix:**

- Windows: `C:/Program Files/duvc-ctl` or `C:/Program Files (x86)/duvc-ctl`
- Custom: Specify with `-DCMAKE_INSTALL_PREFIX=path`

**Installed structure:**

```
install/
├── bin/                 # DLLs and executables
│   ├── duvc-core.dll
│   ├── duvc-cli.exe
│   └── duvc-c-api.dll
├── lib/                 # Import libraries
│   ├── duvc-core.lib
│   └── duvc-c-api.lib
├── include/             # Headers
│   └── duvc-ctl/
│       ├── duvc.hpp
│       ├── core/
│       ├── platform/
│       └── c/
└── lib/cmake/duvc-ctl/  # CMake config
    ├── duvc-ctl-config.cmake
    └── duvc-ctl-targets.cmake
```


***

#### Development Build

**With all debugging symbols and tests:**

```bash
cmake -B build -G "Visual Studio 17 2022" -A x64 \
    -DCMAKE_BUILD_TYPE=Debug \
    -DDUVC_BUILD_TESTS=ON \
    -DDUVC_BUILD_EXAMPLES=ON \
    -DDUVC_WARNINGS_AS_ERRORS=ON

cmake --build build --config Debug
```


***

### 9.3 Package Managers

#### vcpkg Integration

**Status:** In development

**Installation (future):**

```bash
# Install vcpkg port
vcpkg install duvc-ctl

# Use in CMakeLists.txt
find_package(duvc-ctl CONFIG REQUIRED)
target_link_libraries(my_app PRIVATE duvc::core)
```

**Custom vcpkg triplet:**

```cmake
# x64-windows-static.cmake
set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE dynamic)
set(VCPKG_LIBRARY_LINKAGE static)

vcpkg install duvc-ctl:x64-windows-static
```

**CMake toolchain:**

```bash
cmake -B build \
    -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake \
    -DVCPKG_TARGET_TRIPLET=x64-windows-static
```


***

#### Conan Integration

**Status:** In development

**Installation (future):**

```bash
# Add remote (if needed)
conan remote add duvc https://conan.example.com

# Install package
conan install duvc-ctl/2.0.0@

# Or use conanfile.txt
[requires]
duvc-ctl/2.0.0

[generators]
CMakeDeps
CMakeToolchain
```

**CMakeLists.txt:**

```cmake
find_package(duvc-ctl REQUIRED)
target_link_libraries(my_app PRIVATE duvc-ctl::duvc-ctl)
```

**Conan build:**

```bash
conan install . --output-folder=build --build=missing
cmake -B build -DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake
cmake --build build
```


***

#### conda-forge Integration

**Status:** Planned

**Installation (future):**

```bash
conda install -c conda-forge duvc-ctl
```

**Create environment:**

```bash
conda create -n camera-dev duvc-ctl python=3.11
conda activate camera-dev
```


***

#### Chocolatey (CLI Tool)

**Status:** Coming soon

**Installation (future):**

```powershell
choco install duvc-cli
duvc-cli list
```


***

#### Manual Portfile (vcpkg)

**Create custom overlay:**

```cmake
# ports/duvc-ctl/portfile.cmake
vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO allanhanan/duvc-ctl
    REF v2.0.0
    SHA512 <hash>
)

vcpkg_cmake_configure(
    SOURCE_PATH "${SOURCE_PATH}"
    OPTIONS
        -DDUVC_BUILD_TESTS=OFF
        -DDUVC_BUILD_CLI=OFF
)

vcpkg_cmake_install()
vcpkg_cmake_config_fixup(CONFIG_PATH lib/cmake/duvc-ctl)
vcpkg_copy_pdbs()

file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/debug/include")
file(INSTALL "${SOURCE_PATH}/LICENSE" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME copyright)
```

**Use overlay:**

```bash
vcpkg install duvc-ctl --overlay-ports=./ports
```


***

#### Cross-Compilation

**MinGW on Linux:**

```bash
cmake -B build \
    -DCMAKE_TOOLCHAIN_FILE=toolchains/mingw-w64.cmake \
    -DCMAKE_BUILD_TYPE=Release

cmake --build build
```

**Toolchain file example:**

```cmake
# toolchains/mingw-w64.cmake
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_C_COMPILER x86_64-w64-mingw32-gcc)
set(CMAKE_CXX_COMPILER x86_64-w64-mingw32-g++)
set(CMAKE_RC_COMPILER x86_64-w64-mingw32-windres)

set(CMAKE_FIND_ROOT_PATH /usr/x86_64-w64-mingw32)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
```

## 10. Platform-Specific Information

### 10.1 Windows-Specific Details

**Windows API Dependencies:**

duvc-ctl is deeply integrated with Windows platform APIs. Understanding these dependencies is essential for proper usage and troubleshooting.

***

#### Required Windows Headers

```cpp
// Core Windows headers
#include <windows.h>           // Base Windows API
#include <objbase.h>           // COM initialization
#include <dshow.h>             // DirectShow interfaces
#include <ks.h>                // Kernel streaming
#include <ksproxy.h>           // KS proxy interfaces
#include <vidcap.h>            // Video capture structures
```

**Linked libraries:**

```cmake
# Required system libraries
ole32.lib          # COM runtime
oleaut32.lib       # COM automation
strmiids.lib       # DirectShow GUIDs
uuid.lib           # Interface UUIDs
```


***

#### COM Initialization

**COM must be initialized per-thread:**

```cpp
// Automatic RAII wrapper
class ComInitializer {
public:
    ComInitializer() {
        HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
        if (FAILED(hr) && hr != RPC_E_CHANGED_MODE) {
            throw std::runtime_error("COM initialization failed");
        }
        initialized_ = SUCCEEDED(hr);
    }
    
    ~ComInitializer() {
        if (initialized_) {
            CoUninitialize();
        }
    }
    
private:
    bool initialized_;
};
```

**Library handles this automatically:**

```cpp
// duvc-ctl handles COM initialization internally
Camera camera(0);  // COM initialized if needed
```

**Manual control:**

```cpp
// If you need explicit control
HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
// ... use duvc-ctl ...
CoUninitialize();
```


***

#### Threading Model

**Single-Threaded Apartment (STA):**

DirectShow uses STA threading. COM objects are bound to the creating thread and cannot be marshaled to other threads without explicit marshaling.

```cpp
// CORRECT: Each thread initializes COM
std::thread t1([]() {
    ComInitializer com;  // COM for this thread
    Camera camera(0);
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
});

// WRONG: Passing camera between threads
Camera camera(0);
std::thread t2([&camera]() {
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});  // CRASH!
});
```


***

#### Windows Error Codes

**HRESULT values:**


| HRESULT | Value | Meaning |
| :-- | :-- | :-- |
| `S_OK` | `0x00000000` | Success |
| `E_FAIL` | `0x80004005` | Unspecified failure |
| `E_INVALIDARG` | `0x80070057` | Invalid argument |
| `E_OUTOFMEMORY` | `0x8007000E` | Out of memory |
| `E_POINTER` | `0x80004003` | NULL pointer |
| `E_NOTIMPL` | `0x80004001` | Not implemented |
| `VFW_E_NOT_CONNECTED` | `0x80040209` | Filter not connected |
| `VFW_E_CANNOT_CONNECT` | `0x80040217` | Cannot connect pins |

**Decoding errors:**

```cpp
// Use library utilities
std::string error_msg = duvc::decode_hresult(hr);
std::cout << "Error: " << error_msg << std::endl;

// Check error categories
if (duvc::is_device_error(hr)) {
    // Device-specific error
}
if (duvc::is_permission_error(hr)) {
    // Access denied
}
```


***

#### Device Paths

**DirectShow device moniker paths:**

```
\\?\usb#vid_046d&pid_0825&mi_00#7&2a2f12e8&0&0000#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\global
```

**Format breakdown:**

- `\\?\` - Win32 device namespace prefix
- `usb#vid_046d&pid_0825` - USB Vendor ID and Product ID
- `mi_00` - Multiple interface index
- `{guid}` - Device class GUID (video capture)
- `\global` - System-wide device

**Parsing device info:**

```cpp
// Extract vendor/product ID
std::wstring path = device.path;
size_t vid_pos = path.find(L"vid_");
size_t pid_pos = path.find(L"pid_");

if (vid_pos != std::wstring::npos && pid_pos != std::wstring::npos) {
    std::wstring vid = path.substr(vid_pos + 4, 4);  // e.g., "046d"
    std::wstring pid = path.substr(pid_pos + 4, 4);  // e.g., "0825"
}
```


***

#### System Requirements

**Minimum Windows version:**

- **Windows 10** recommended
- **Windows 8.1** compatible (not tested)
- **Windows 7** not supported (DirectShow API changes)

**Required components:**

- Visual C++ Redistributable 2019/2022
- DirectX 9.0c or later
- Windows Media Feature Pack (if disabled)

**Checking availability:**

```cpp
// Verify DirectShow availability
HRESULT hr = CoInitialize(nullptr);
if (SUCCEEDED(hr)) {
    ICreateDevEnum* pDevEnum = nullptr;
    hr = CoCreateInstance(CLSID_SystemDeviceEnum, nullptr, 
                          CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&pDevEnum));
    if (SUCCEEDED(hr)) {
        // DirectShow available
        pDevEnum->Release();
    }
    CoUninitialize();
}
```


***

#### Permissions and Access

**Administrator rights:**
Not required for UVC camera access. Standard user permissions suffice.

**Exclusive access:**
DirectShow grants exclusive access to camera properties. If another application is controlling the camera, property changes may fail with `E_FAIL` or `VFW_E_IN_USE`.

**Antivirus interference:**
Some antivirus software blocks camera access. Check:

- Windows Security → Camera privacy settings
- Third-party antivirus camera protection

***

#### Wide Character Strings

**Windows uses UTF-16:**

```cpp
// Device names are std::wstring
Device device = devices[0];
std::wstring name = device.name;  // UTF-16

// Convert to UTF-8 for display
std::string utf8_name = duvc::to_utf8(name);
std::cout << "Device: " << utf8_name << std::endl;
```

**Conversion utilities:**

```cpp
namespace duvc {
    std::string to_utf8(const std::wstring& wstr);
    std::wstring from_utf8(const std::string& str);
}
```


***

### 10.2 DirectShow Background

**DirectShow is Microsoft's multimedia framework for capture, playback, and processing.**

***

#### Architecture Overview

**Filter graph model:**

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ Capture     │      │ Transform   │      │ Renderer    │
│ Filter      │─────▶│ Filter      │─────▶│ Filter      │
│ (Camera)    │      │ (Optional)  │      │ (Display)   │
└─────────────┘      └─────────────┘      └─────────────┘
```

**Components:**

- **Filters** - Processing units (capture, transform, render)
- **Pins** - Connection points between filters
- **Filter Graph Manager** - Coordinates filter operation
- **Media Types** - Describes data format (video format, resolution)

***

#### Key Interfaces Used

**Device enumeration:**

```cpp
// ICreateDevEnum - Enumerate device categories
CLSID_SystemDeviceEnum
  → ICreateDevEnum::CreateClassEnumerator(CLSID_VideoInputDeviceCategory)
    → IEnumMoniker (iterate devices)
      → IMoniker::BindToObject(IBaseFilter)
```

**Camera control:**

```cpp
// IAMCameraControl - PTZ and camera-specific properties
IBaseFilter* pFilter;
IAMCameraControl* pCameraControl;
pFilter->QueryInterface(IID_IAMCameraControl, (void**)&pCameraControl);

// Set property
pCameraControl->Set(CameraControl_Pan, value, CameraControl_Flags_Manual);
pCameraControl->Get(CameraControl_Pan, &value, &flags);
```

**Video processing:**

```cpp
// IAMVideoProcAmp - Image properties
IAMVideoProcAmp* pVideoProcAmp;
pFilter->QueryInterface(IID_IAMVideoProcAmp, (void**)&pVideoProcAmp);

// Set brightness
pVideoProcAmp->Set(VideoProcAmp_Brightness, value, VideoProcAmp_Flags_Manual);
```

**Vendor extensions:**

```cpp
// IKsPropertySet - Kernel streaming properties
IKsPropertySet* pKsPropertySet;
pFilter->QueryInterface(IID_IKsPropertySet, (void**)&pKsPropertySet);

// Get/Set vendor-specific properties
GUID propSet = {/* vendor GUID */};
pKsPropertySet->Get(propSet, propId, nullptr, 0, data, dataSize, &returned);
```


***

#### Property Control Flow

**Setting a camera property:**

1. Enumerate devices → `ICreateDevEnum`
2. Bind to device filter → `IMoniker::BindToObject`
3. Query property interface → `QueryInterface(IAMCameraControl)`
4. Check property support → `GetRange()`
5. Set property value → `Set(prop, value, flags)`
6. Verify change → `Get(prop, &value, &flags)`

**Code path:**

```cpp
// duvc-ctl wraps this flow
Camera camera(device);  // Steps 1-3
auto range = camera.get_range(CamProp::Pan);  // Step 4
camera.set(CamProp::Pan, {0, CamMode::Manual});  // Steps 5-6
```


***

#### DirectShow vs Media Foundation

**DirectShow** (used by duvc-ctl):

- Legacy API (Windows XP+)
- Widely supported by hardware
- Filter graph model
- Synchronous property access
- Well-documented UVC support

**Media Foundation** (newer):

- Modern API (Windows Vista+)
- Async design
- Better performance for streaming
- Limited camera control compared to DirectShow
- Less hardware compatibility

**Why DirectShow?**

- **Universal UVC support** - Works with all compliant cameras
- **Direct property access** - No additional drivers needed
- **Mature ecosystem** - 20+ years of hardware compatibility
- **Synchronous operations** - Simpler control flow for settings

***

#### Graph Building (Not Used)

duvc-ctl does **not** build filter graphs for streaming. It only uses device filters for property control:

```cpp
// duvc-ctl does NOT do this:
IGraphBuilder* pGraph;
pGraph->AddFilter(pCaptureFilter, L"Capture");
pGraph->Render(pCapturePin);  // Build capture graph

// duvc-ctl ONLY does this:
IAMCameraControl* pControl;
pCaptureFilter->QueryInterface(IID_IAMCameraControl, (void**)&pControl);
pControl->Set(CameraControl_Pan, 0, CameraControl_Flags_Manual);
```

**Streaming is handled by:**

- Windows Camera app
- OpenCV (VideoCapture)
- FFmpeg (dshow input)
- Third-party capture applications

***

### 10.3 UVC Camera Standards

**USB Video Class (UVC) defines standard camera controls.**

***

#### UVC Specification

**USB.org UVC 1.5:**

- Standard published by USB Implementers Forum
- Defines camera control terminals and units
- Provides class-specific USB descriptors
- Maps to DirectShow `IAMCameraControl` and `IAMVideoProcAmp`

**Key concepts:**

- **Control terminals** - Camera-specific controls (pan, tilt, zoom)
- **Processing units** - Image processing (brightness, contrast)
- **Extension units** - Vendor-specific controls

***

#### Standard UVC Controls

**Camera Terminal Controls (IAMCameraControl):**


| UVC Control | DirectShow Property | Units | Typical Range |
| :-- | :-- | :-- | :-- |
| Scanning Mode | `CameraControl_ScanMode` | - | 0 (Interlaced), 1 (Progressive) |
| Auto Exposure Mode | `CameraControl_Exposure` | - | 1 (Manual), 2-8 (Auto modes) |
| Auto Exposure Priority | - | - | Camera-dependent |
| Exposure Time | `CameraControl_Exposure` | 100µs | -13 to -1 (log scale) |
| Focus | `CameraControl_Focus` | mm | 0 to max (device-specific) |
| Iris | `CameraControl_Iris` | f-stop × 10 | Device-specific |
| Zoom | `CameraControl_Zoom` | mm | Device-specific |
| Pan | `CameraControl_Pan` | degrees | -180° to +180° |
| Tilt | `CameraControl_Tilt` | degrees | -180° to +180° |
| Roll | `CameraControl_Roll` | degrees | -180° to +180° |
| Privacy Shutter | `CameraControl_Privacy` | - | 0 (Open), 1 (Closed) |

**Processing Unit Controls (IAMVideoProcAmp):**


| UVC Control | DirectShow Property | Typical Range |
| :-- | :-- | :-- |
| Brightness | `VideoProcAmp_Brightness` | 0 to 255 |
| Contrast | `VideoProcAmp_Contrast` | 0 to 255 |
| Hue | `VideoProcAmp_Hue` | -180° to +180° |
| Saturation | `VideoProcAmp_Saturation` | 0 to 255 |
| Sharpness | `VideoProcAmp_Sharpness` | 0 to 255 |
| Gamma | `VideoProcAmp_Gamma` | 100 to 500 (100 = 1.0) |
| White Balance | `VideoProcAmp_WhiteBalance` | 2800K to 6500K |
| Backlight Compensation | `VideoProcAmp_BacklightCompensation` | 0 (Off), 1 (On) |
| Gain | `VideoProcAmp_Gain` | 0 to 255 |
| Color Enable | `VideoProcAmp_ColorEnable` | 0 (B\&W), 1 (Color) |


***

#### Auto vs Manual Modes

**UVC defines automatic control:**

```cpp
// Auto mode - camera adjusts automatically
camera.set(CamProp::Exposure, {0, CamMode::Auto});

// Manual mode - explicit value
camera.set(CamProp::Exposure, {-5, CamMode::Manual});
```

**DirectShow flags:**

```cpp
CameraControl_Flags_Auto   = 0x0001  // Automatic adjustment
CameraControl_Flags_Manual = 0x0002  // Manual control
```

**UVC behavior:**

- **Auto mode** - Value parameter ignored, camera firmware controls
- **Manual mode** - Value parameter used, firmware uses specified value
- **Auto → Manual** - Locks current auto value
- **Manual → Auto** - Resumes automatic adjustment

***

#### Vendor-Specific Extensions

**Beyond UVC standard:**

Vendors implement proprietary controls via **Extension Units (XU)** using `IKsPropertySet`.

**Logitech example:**

```cpp
// Standard UVC
camera.set(CamProp::Exposure, {-5, CamMode::Manual});

// Vendor extension (Logitech)
logitech::set_logitech_property(device, LogitechProperty::RightLight, true);
```

**Common vendor extensions:**

- **Logitech** - RightLight, LED control, face tracking
- **Microsoft LifeCam** - TrueColor, noise reduction
- **Razer Kiyo** - Ring light control
- **Elgato Facecam** - Advanced color grading

***

#### UVC Compliance Levels

**Not all cameras are equal:**

**Full UVC 1.5:**

- All standard controls
- Auto/manual modes
- Proper range reporting
- Spec-compliant behavior

**Partial UVC:**

- Subset of controls (e.g., no PTZ)
- Missing auto modes
- Incorrect range values
- Quirky implementations

**Testing compliance:**

```cpp
// Check which properties are supported
for (auto prop : {CamProp::Pan, CamProp::Tilt, CamProp::Zoom}) {
    auto range_result = camera.get_range(prop);
    if (range_result.is_ok()) {
        std::cout << "Supports: " << to_string(prop) << std::endl;
    }
}
```


***

#### USB Bandwidth

**UVC streaming consumes USB bandwidth:**

**USB 2.0 limits:**

- High-speed: 480 Mbps theoretical
- Practical: ~35 MB/s for video
- 1080p30 uncompressed: ~177 MB/s (requires compression)

**USB 3.0/3.1:**

- SuperSpeed: 5 Gbps (USB 3.0), 10 Gbps (USB 3.1)
- Supports uncompressed high-resolution video

**Control bandwidth:**
Property control uses USB control transfers (separate from video data). Control operations are lightweight and don't impact streaming performance.

***

#### Descriptor Parsing

**UVC cameras expose USB descriptors:**

DirectShow automatically parses:

- Video Control Interface
- Video Streaming Interface
- Camera Terminal Descriptor
- Processing Unit Descriptor
- Extension Unit Descriptor

**duvc-ctl abstracts this:**

```cpp
// No need to parse descriptors
Camera camera(0);
auto range = camera.get_range(CamProp::Pan);  // Descriptor info extracted
```

## 11. Device Support \& Compatibility

### 11.1 Tested Devices

**duvc-ctl works with any UVC-compliant camera on Windows.**

The library relies on DirectShow's UVC support rather than device-specific drivers, providing broad compatibility.

***

#### Verified Compatible Brands

**Logitech** (Extended support via vendor extensions):

- C920/C922 HD Pro Webcam
- C930e Business Webcam
- BRIO 4K Ultra HD
- StreamCam
- PTZ Pro series

**Microsoft:**

- LifeCam HD-3000
- LifeCam Studio
- Modern Webcam

**Generic UVC:**

- Most USB webcams without proprietary drivers
- Conference room PTZ cameras
- Document cameras
- Industrial machine vision cameras

**Professional:**

- PTZOptics cameras
- AVer CAM series
- Elgato Facecam
- Razer Kiyo series

***

#### Property Support Varies

Not all cameras implement all UVC properties:

**Common capabilities:**

- Brightness, Contrast, Saturation
- Auto/Manual Exposure
- Auto/Manual White Balance
- Auto Focus (if supported by hardware)

**Less common:**

- Pan/Tilt/Zoom (PTZ cameras only)
- Privacy Shutter
- Roll
- Iris control

**Check support:**

```cpp
auto devices = duvc::list_devices();
Camera camera(devices);

// Query which properties are available
std::cout << "Camera: " << duvc::to_utf8(devices.name) << "\n";

for (auto prop : {CamProp::Pan, CamProp::Tilt, CamProp::Zoom, 
                   CamProp::Focus, CamProp::Exposure}) {
    auto range = camera.get_range(prop);
    if (range.is_ok()) {
        std::cout << "  " << to_string(prop) << ": " 
                  << range.value().min << " to " << range.value().max << "\n";
    }
}
```


***

### 11.2 Device Capability Matrix

**Typical property support by camera type:**


| Property | Basic Webcam | PTZ Camera | High-End Webcam | Industrial Camera |
| :-- | :-- | :-- | :-- | :-- |
| **Brightness** | ✓ | ✓ | ✓ | ✓ |
| **Contrast** | ✓ | ✓ | ✓ | ✓ |
| **Saturation** | ✓ | ✓ | ✓ | ✓ |
| **Hue** | ✓ | ✓ | ✓ | ~ |
| **Sharpness** | ✓ | ✓ | ✓ | ✓ |
| **Gamma** | ~ | ✓ | ✓ | ✓ |
| **White Balance** | ✓ | ✓ | ✓ | ✓ |
| **Backlight Comp** | ~ | ✓ | ✓ | ✓ |
| **Gain** | ~ | ✓ | ✓ | ✓ |
| **Exposure** | ✓ | ✓ | ✓ | ✓ |
| **Focus** | Auto only | ✓ | ✓ | ✓ |
| **Zoom** | ✗ | ✓ | ~ | ~ |
| **Pan** | ✗ | ✓ | ✗ | ~ |
| **Tilt** | ✗ | ✓ | ✗ | ~ |
| **Roll** | ✗ | ~ | ✗ | ✗ |
| **Iris** | ✗ | ~ | ✗ | ✓ |
| **Privacy** | ✗ | ~ | ~ | ~ |

**Legend:**

- ✓ = Commonly supported
- ~ = Sometimes supported
- ✗ = Rarely supported

***

#### Logitech-Specific Features

**Vendor extensions via `IKsPropertySet`:**


| Feature | C920 | C922 | C930e | BRIO | StreamCam |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **RightLight** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **RightSound** | ✗ | ✗ | ✓ | ✓ | ✗ |
| **Face Tracking** | ~ | ~ | ✓ | ✓ | ~ |
| **LED Control** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **HDR** | ✗ | ✗ | ✗ | ✓ | ✗ |
| **Digital Pan/Tilt** | ✗ | ✗ | ✗ | ✓ | ~ |

**Usage:**

```cpp
#include <duvc-ctl/vendor/logitech.h>

auto devices = duvc::list_devices();
if (duvc::logitech::supports_logitech_properties(devices).value_or(false)) {
    // Enable RightLight auto-exposure
    duvc::logitech::set_logitech_property_typed<bool>(
        devices, duvc::logitech::LogitechProperty::RightLight, true);
}
```


***

#### Resolution Impact

**Property availability can vary by resolution:**

Some cameras disable certain controls at high resolutions (e.g., 4K) due to bandwidth or processing limits.

**Example:**

- 1080p: Full property support
- 4K: Auto focus only, manual focus disabled
- 720p: All properties available

**This is firmware-dependent** and varies by manufacturer.

***

### 11.3 Known Issues \& Workarounds

#### Issue 1: Property Values Don't Persist

**Problem:**
Some cameras reset properties to defaults when:

- Camera is unplugged/replugged
- System reboots
- Camera app is closed

**Cause:** Properties stored in volatile firmware memory, not flash.

**Workaround:**

```cpp
// Save desired settings
struct CameraSettings {
    int exposure;
    int brightness;
    int white_balance;
};

// Apply on startup
void apply_settings(Camera& camera, const CameraSettings& settings) {
    camera.set(CamProp::Exposure, {settings.exposure, CamMode::Manual});
    camera.set(VidProp::Brightness, {settings.brightness, CamMode::Manual});
    camera.set(VidProp::WhiteBalance, {settings.white_balance, CamMode::Manual});
}

// Call on device connection
duvc::register_device_change_callback([](bool added, const std::string& path) {
    if (added) {
        // Device connected - reapply settings
        auto devices = duvc::list_devices();
        Camera camera(devices);
        apply_settings(camera, saved_settings);
    }
});
```


***

#### Issue 2: Auto Mode Doesn't Revert to Default

**Problem:**
Setting manual value, then switching back to auto may not restore original auto behavior.

**Example:**

```cpp
// Original state: Auto exposure
camera.set(CamProp::Exposure, {-5, CamMode::Manual});  // Set manual
camera.set(CamProp::Exposure, {0, CamMode::Auto});     // Back to auto

// Auto behavior may differ from original
```

**Cause:** Some cameras remember manual value as "auto starting point."

**Workaround:**
Query and store default value before modification:

```cpp
auto original = camera.get(CamProp::Exposure).value();
auto range = camera.get_range(CamProp::Exposure).value();

// Modify
camera.set(CamProp::Exposure, {-5, CamMode::Manual});

// Restore to true default
camera.set(CamProp::Exposure, {range.default_val, range.default_mode});
```


***

#### Issue 3: Property Changes During Streaming

**Problem:**
Some cameras ignore property changes while actively streaming video.

**Symptom:**

```cpp
Camera camera(0);
camera.set(CamProp::Exposure, {-5, CamMode::Manual});  // Returns success

// But value doesn't change if camera is streaming
auto result = camera.get(CamProp::Exposure);  // Still old value
```

**Workaround:**
Stop streaming, apply properties, restart streaming:

```cpp
// OpenCV example
cv::VideoCapture cap(0);
cap.release();  // Stop streaming

Camera camera(0);
camera.set(CamProp::Exposure, {-5, CamMode::Manual});

cap.open(0);  // Restart with new settings
```


***

#### Issue 4: Incorrect Range Values

**Problem:**
Some cameras report invalid `min`, `max`, or `step` values.

**Examples:**

- Step of 0 (continuous values)
- Min > Max (reversed range)
- Range includes impossible values

**Workaround:**
Validate and clamp:

```cpp
auto range_result = camera.get_range(CamProp::Zoom);
if (range_result.is_ok()) {
    auto range = range_result.value();
    
    // Validate
    if (range.min > range.max) {
        std::swap(range.min, range.max);
    }
    if (range.step <= 0) {
        range.step = 1;  // Assume step of 1
    }
    
    // Safe clamping
    int value = range.clamp(user_value);
    camera.set(CamProp::Zoom, {value, CamMode::Manual});
}
```


***

#### Issue 5: Slow Property Queries

**Problem:**
Some cameras take a long time to respond to `get()` or `get_range()` calls.

**Typical duration:** 50-200ms per query

**Workaround:**
Cache property ranges:

```cpp
// Cache on startup
std::map<CamProp, PropRange> cached_ranges;
for (auto prop : {CamProp::Pan, CamProp::Tilt, CamProp::Zoom}) {
    auto range = camera.get_range(prop);
    if (range.is_ok()) {
        cached_ranges[prop] = range.value();
    }
}

// Use cached values for validation
if (cached_ranges[CamProp::Pan].is_valid(value)) {
    camera.set(CamProp::Pan, {value, CamMode::Manual});
}
```


***

#### Issue 6: DirectShow Exclusive Access

**Problem:**
If another application is using DirectShow to control the camera, property changes may fail.

**Error:** `E_FAIL` or `VFW_E_IN_USE`

**Conflicting applications:**

- Windows Camera app
- Skype/Teams (if camera preview active)
- OBS Studio (with DirectShow source)
- Third-party camera control software

**Workaround:**

```cpp
auto result = camera.set(CamProp::Exposure, {-5, CamMode::Manual});
if (result.is_error()) {
    if (result.error().code() == ErrorCode::DeviceInUse) {
        std::cerr << "Camera in use by another application\n";
        // Prompt user to close other apps
    }
}
```


***

#### Issue 7: USB Power Management

**Problem:**
Windows USB selective suspend can reset camera properties.

**Symptom:** Properties revert to defaults after period of inactivity.

**Workaround:**
Disable USB selective suspend for camera devices:

**PowerShell:**

```powershell
# Disable for all USB devices
powercfg /change usb-selective-suspend-setting 0

# Or via Device Manager → USB Hub → Power Management → 
# Uncheck "Allow computer to turn off this device"
```

**Programmatic detection:**

```cpp
duvc::register_device_change_callback([](bool added, const std::string& path) {
    if (added) {
        // Device reconnected (possibly due to power management)
        // Reapply settings
    }
});
```


***

#### Issue 8: Firmware Bugs

**Problem:**
Some cameras have firmware bugs causing:

- Invalid property values
- Crashes when setting certain combinations
- Properties affecting unrelated settings

**Example:** Setting Zoom on some cameras resets Exposure.

**Workaround:**
Test and document camera-specific quirks:

```cpp
// Logitech C920 quirk: Setting zoom resets exposure
auto exposure = camera.get(CamProp::Exposure).value();
camera.set(CamProp::Zoom, {100, CamMode::Manual});
camera.set(CamProp::Exposure, exposure);  // Restore exposure
```


***

#### Issue 9: Multiple Cameras Same Model

**Problem:**
Cameras of same model have identical names, making identification difficult.

**Solution:**
Use device path for unique identification:

```cpp
auto devices = duvc::list_devices();
for (const auto& device : devices) {
    std::wcout << L"Name: " << device.name << L"\n";
    std::wcout << L"Path: " << device.path << L"\n\n";
    
    // Path contains unique USB bus/port info
}

// Store path to identify specific camera
std::wstring my_camera_path = devices.path;

// Later, find same camera
for (const auto& device : duvc::list_devices()) {
    if (device.path == my_camera_path) {
        Camera camera(device);
        // This is the correct camera
    }
}
```


***

#### Issue 10: No UVC Compliance

**Problem:**
Some "webcams" don't implement UVC properly and require proprietary drivers.

**Examples:**

- Very old webcams (pre-2008)
- Some security cameras
- Proprietary industrial cameras

**Detection:**

```cpp
auto devices = duvc::list_devices();
if (devices.empty()) {
    std::cerr << "No UVC cameras found\n";
    std::cerr << "Camera may require vendor drivers\n";
}

// Or camera appears but has no properties
Camera camera(0);
auto range = camera.get_range(CamProp::Brightness);
if (range.is_error()) {
    std::cerr << "Camera doesn't support standard UVC properties\n";
}
```

**Solution:** Use vendor SDK if available, or duvc-ctl won't work.

***

#### Testing New Devices

**Capability discovery script:**

```cpp
void test_camera_capabilities(const Device& device) {
    std::cout << "Testing: " << duvc::to_utf8(device.name) << "\n\n";
    
    Camera camera(device);
    
    // Test camera properties
    std::cout << "Camera Properties:\n";
    for (auto prop : {CamProp::Pan, CamProp::Tilt, CamProp::Zoom,
                       CamProp::Exposure, CamProp::Focus, CamProp::Iris}) {
        auto range = camera.get_range(prop);
        if (range.is_ok()) {
            std::cout << "  " << to_string(prop) << ": "
                      << range.value().min << " to " << range.value().max
                      << " (default: " << range.value().default_val << ")\n";
        }
    }
    
    // Test video properties
    std::cout << "\nVideo Properties:\n";
    for (auto prop : {VidProp::Brightness, VidProp::Contrast,
                       VidProp::Saturation, VidProp::WhiteBalance}) {
        auto range = camera.get_range(prop);
        if (range.is_ok()) {
            std::cout << "  " << to_string(prop) << ": "
                      << range.value().min << " to " << range.value().max << "\n";
        }
    }
}
```

## 12. Troubleshooting \& Debugging

### 12.1 Common Issues

**Quick reference for frequent problems and solutions.**

***

#### Issue: No Cameras Detected

**Symptom:**

```cpp
auto devices = duvc::list_devices();
std::cout << "Found " << devices.size() << " cameras\n";  // Prints: Found 0 cameras
```

**Possible causes:**

**Camera not UVC-compliant:**

```cpp
// Check Device Manager → Imaging devices
// If camera appears under "Other devices" or requires vendor driver, it's not UVC
```

**DirectShow not available:**

- Windows N/KN editions lack Media Feature Pack
- Install: Settings → Apps → Optional features → Media Feature Pack

**Antivirus blocking:**

- Check Windows Security → Camera privacy settings
- Ensure application has camera permission

**USB connection issues:**

- Try different USB port
- Check USB selective suspend settings
- Verify camera works in Windows Camera app

***

#### Issue: Property Operations Fail

**Symptom:**

```cpp
auto result = camera.set(CamProp::Exposure, {-5, CamMode::Manual});
if (result.is_error()) {
    std::cout << result.error().description() << std::endl;
    // "Property not supported" or "Operation failed"
}
```

**Check property support:**

```cpp
auto range_result = camera.get_range(CamProp::Exposure);
if (range_result.is_error()) {
    std::cout << "Exposure not supported by this camera\n";
}
```

**Device in use by another application:**

```cpp
// Close: Windows Camera, Skype, Teams, OBS, Zoom, etc.
// Then retry operation
```

**Camera needs reinitialization:**

```cpp
// Unplug and replug camera
// Or use device monitor to detect reconnection
```


***

#### Issue: COM Initialization Failed

**Symptom:**

```
Runtime error: COM initialization failed
```

**Cause:** COM already initialized with incompatible threading model.

**Solution:**

```cpp
// Let duvc-ctl manage COM automatically
Camera camera(0);  // Works

// If you must initialize COM yourself:
HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
// duvc-ctl will detect and use existing COM initialization
```


***

#### Issue: Crashes or Access Violations

**Common causes:**

**Using camera object after device disconnect:**

```cpp
Camera camera(0);
// ... camera unplugged ...
camera.set(CamProp::Pan, {0, CamMode::Manual});  // CRASH

// Fix: Always check validity
if (!camera.is_valid()) {
    std::cerr << "Camera disconnected\n";
    return;
}
```

**Thread safety violation:**

```cpp
// WRONG: Passing camera between threads
Camera camera(0);
std::thread t([&camera]() {
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});  // CRASH
});

// CORRECT: Create camera in worker thread
std::thread t([]() {
    Camera camera(0);  // COM initialized in this thread
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
});
```


***

#### Issue: Slow Performance

**Symptom:** Operations take several hundred milliseconds.

**Expected timing:** Property queries can take 50-200ms on some cameras.

**Optimization:**

```cpp
// Cache property ranges
std::map<CamProp, PropRange> ranges;
for (auto prop : {CamProp::Pan, CamProp::Tilt}) {
    auto range = camera.get_range(prop);
    if (range.is_ok()) {
        ranges[prop] = range.value();
    }
}

// Use cached values for validation
if (ranges[CamProp::Pan].is_valid(value)) {
    camera.set(CamProp::Pan, {value, CamMode::Manual});
}
```


***

#### Issue: Property Values Incorrect

**Symptom:** `get()` returns unexpected value after `set()`.

**Cameras may clamp to nearest valid value:**

```cpp
camera.set(CamProp::Brightness, {127, CamMode::Manual});
auto result = camera.get(CamProp::Brightness);
std::cout << result.value().value << std::endl;  // May print 128 (step size)
```

**Check property range:**

```cpp
auto range = camera.get_range(CamProp::Brightness);
if (range.is_ok()) {
    std::cout << "Step: " << range.value().step << std::endl;
    // Use step-aligned value
    int aligned = (value / range.value().step) * range.value().step;
}
```


***

#### Issue: DLL Load Failures (Python/C API)

**Symptom:**

```
ImportError: DLL load failed: The specified module could not be found.
```

**Solutions:**

**Install Visual C++ Redistributable:**

- Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Install and restart

**Check DLL dependencies:**

```powershell
# Use Dependencies.exe or dumpbin
dumpbin /dependents duvc-core.dll
```

**Python-specific:**

```bash
# Ensure correct Python version
python --version  # Should be 3.8+

# Reinstall package
pip uninstall duvc-ctl
pip install duvc-ctl --force-reinstall
```


***

### 12.2 Debugging Techniques

#### Enable Verbose Logging

**Enable full debug output:**

```cpp
#include <duvc-ctl/utils/logging.h>

// Set log level before any operations
duvc::set_log_level(duvc::LogLevel::Debug);

// Set custom log handler
duvc::set_log_callback([](duvc::LogLevel level, const std::string& msg) {
    std::cout << "[" << duvc::to_string(level) << "] " << msg << std::endl;
});

// Now all operations log detailed information
auto devices = duvc::list_devices();
Camera camera(devices);
auto result = camera.set(CamProp::Exposure, {-5, CamMode::Manual});
```

**Output:**

```
[Debug] Initializing COM
[Debug] Enumerating video input devices
[Info] Found 2 camera(s)
[Debug] Creating connection to device: Logitech C920
[Debug] Querying IAMCameraControl interface
[Debug] Setting CamProp::Exposure to -5 (Manual)
[Debug] DirectShow Set() returned 0x00000000 (S_OK)
```


***

#### Inspect HRESULT Error Codes

**Decode Windows error codes:**

```cpp
#include <duvc-ctl/utils/error_decoder.h>

auto result = camera.set(CamProp::Pan, {0, CamMode::Manual});
if (result.is_error()) {
    std::cout << "Error: " << result.error().description() << std::endl;
    
    // Get detailed DirectShow error
    #ifdef _WIN32
    HRESULT hr = /* extract from error */;
    std::string details = duvc::decode_hresult(hr);
    std::cout << "HRESULT: " << details << std::endl;
    
    // Check error category
    if (duvc::is_device_error(hr)) {
        std::cout << "Device-specific error\n";
    }
    if (duvc::is_permission_error(hr)) {
        std::cout << "Permission denied\n";
    }
    #endif
}
```

**Common HRESULT values:**


| HRESULT | Code | Meaning |
| :-- | :-- | :-- |
| `S_OK` | `0x00000000` | Success |
| `E_FAIL` | `0x80004005` | Unspecified failure |
| `E_INVALIDARG` | `0x80070057` | Invalid argument |
| `E_PROP_ID_UNSUPPORTED` | `0x80070490` | Property not supported |
| `VFW_E_NOT_CONNECTED` | `0x80040209` | Filter not connected |


***

#### Device Capability Inspection

**Complete capability dump:**

```cpp
void dump_camera_capabilities(const Device& device) {
    std::cout << "=== Camera Capabilities ===" << std::endl;
    std::cout << "Name: " << duvc::to_utf8(device.name) << std::endl;
    std::cout << "Path: " << duvc::to_utf8(device.path) << std::endl << std::endl;
    
    Camera camera(device);
    
    // Camera properties
    std::cout << "Camera Properties (IAMCameraControl):" << std::endl;
    std::vector<CamProp> cam_props = {
        CamProp::Pan, CamProp::Tilt, CamProp::Roll, CamProp::Zoom,
        CamProp::Exposure, CamProp::Iris, CamProp::Focus,
        CamProp::Privacy, CamProp::BacklightCompensation
    };
    
    for (auto prop : cam_props) {
        auto range = camera.get_range(prop);
        if (range.is_ok()) {
            const auto& r = range.value();
            std::cout << "  " << to_string(prop) << ":" << std::endl;
            std::cout << "    Range: [" << r.min << ", " << r.max << "]" << std::endl;
            std::cout << "    Step: " << r.step << std::endl;
            std::cout << "    Default: " << r.default_val 
                      << " (" << to_string(r.default_mode) << ")" << std::endl;
            
            // Current value
            auto current = camera.get(prop);
            if (current.is_ok()) {
                std::cout << "    Current: " << current.value().value
                          << " (" << to_string(current.value().mode) << ")" << std::endl;
            }
        }
    }
    
    // Video properties
    std::cout << "\nVideo Properties (IAMVideoProcAmp):" << std::endl;
    std::vector<VidProp> vid_props = {
        VidProp::Brightness, VidProp::Contrast, VidProp::Hue,
        VidProp::Saturation, VidProp::Sharpness, VidProp::Gamma,
        VidProp::WhiteBalance, VidProp::BacklightCompensation, VidProp::Gain
    };
    
    for (auto prop : vid_props) {
        auto range = camera.get_range(prop);
        if (range.is_ok()) {
            const auto& r = range.value();
            std::cout << "  " << to_string(prop) << ": [" 
                      << r.min << ", " << r.max << "], step=" << r.step << std::endl;
        }
    }
}
```


***

#### Monitor Device Events

**Track connect/disconnect:**

```cpp
#include <duvc-ctl/platform/device_monitor.h>

void monitor_devices() {
    auto callback = [](bool added, const std::wstring& path) {
        if (added) {
            std::wcout << L"Camera connected: " << path << std::endl;
            
            // Reapply settings
            auto devices = duvc::list_devices();
            for (const auto& dev : devices) {
                if (dev.path == path) {
                    Camera camera(dev);
                    // Apply saved settings
                    break;
                }
            }
        } else {
            std::wcout << L"Camera disconnected: " << path << std::endl;
        }
    };
    
    duvc::register_device_change_callback(callback);
    
    // Keep monitoring (blocking or in separate thread)
    std::cout << "Monitoring for device changes... Press Enter to stop" << std::endl;
    std::cin.get();
}
```


***

#### Step-by-Step Operation Trace

**Trace each DirectShow call:**

```cpp
// Enable maximum verbosity
duvc::set_log_level(duvc::LogLevel::Debug);

std::cout << "Step 1: Initialize platform" << std::endl;
auto platform = duvc::create_platform_interface();

std::cout << "Step 2: List devices" << std::endl;
auto devices_result = platform->list_devices();
if (!devices_result.is_ok()) {
    std::cout << "Failed: " << devices_result.error().description() << std::endl;
    return;
}

std::cout << "Step 3: Create connection" << std::endl;
auto connection_result = platform->create_connection(devices_result.value());
if (!connection_result.is_ok()) {
    std::cout << "Failed: " << connection_result.error().description() << std::endl;
    return;
}

auto connection = std::move(connection_result.value());

std::cout << "Step 4: Query property range" << std::endl;
auto range_result = connection->get_camera_property_range(CamProp::Pan);
if (!range_result.is_ok()) {
    std::cout << "Failed: " << range_result.error().description() << std::endl;
    return;
}

std::cout << "Step 5: Set property" << std::endl;
PropSetting setting{0, CamMode::Manual};
auto set_result = connection->set_camera_property(CamProp::Pan, setting);
if (!set_result.is_ok()) {
    std::cout << "Failed: " << set_result.error().description() << std::endl;
    return;
}

std::cout << "Success!" << std::endl;
```


***

### 12.3 Diagnostic Tools

#### Built-in Diagnostic Script

**Create comprehensive diagnostic report:**

```cpp
#include <duvc-ctl/duvc.hpp>
#include <duvc-ctl/utils/logging.h>
#include <duvc-ctl/utils/error_decoder.h>
#include <fstream>

void generate_diagnostic_report(const std::string& filename) {
    std::ofstream report(filename);
    
    // System information
    report << "=== System Diagnostics ===" << std::endl;
    report << "Operating System: Windows" << std::endl;
    report << "duvc-ctl Version: " << DUVC_VERSION << std::endl;
    report << std::endl;
    
    // COM initialization test
    report << "=== COM Initialization ===" << std::endl;
    HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    if (SUCCEEDED(hr)) {
        report << "Status: OK" << std::endl;
        CoUninitialize();
    } else {
        report << "Status: FAILED (0x" << std::hex << hr << ")" << std::endl;
        report << "Details: " << duvc::decode_hresult(hr) << std::endl;
    }
    report << std::endl;
    
    // Device enumeration
    report << "=== Device Enumeration ===" << std::endl;
    auto devices = duvc::list_devices();
    report << "Found " << devices.size() << " camera(s)" << std::endl;
    
    for (size_t i = 0; i < devices.size(); ++i) {
        report << std::endl << "Camera " << i << ":" << std::endl;
        report << "  Name: " << duvc::to_utf8(devices[i].name) << std::endl;
        report << "  Path: " << duvc::to_utf8(devices[i].path) << std::endl;
        
        // Test connection
        try {
            Camera camera(devices[i]);
            report << "  Connection: OK" << std::endl;
            
            // Test basic property
            auto range = camera.get_range(VidProp::Brightness);
            if (range.is_ok()) {
                report << "  Basic property access: OK" << std::endl;
            } else {
                report << "  Basic property access: FAILED" << std::endl;
                report << "    " << range.error().description() << std::endl;
            }
            
        } catch (const std::exception& e) {
            report << "  Connection: FAILED" << std::endl;
            report << "    " << e.what() << std::endl;
        }
    }
    
    report << std::endl << "=== Diagnostic Complete ===" << std::endl;
    report.close();
    
    std::cout << "Diagnostic report saved to: " << filename << std::endl;
}
```


***

#### GraphEdit (DirectShow Debugging)

**Use Microsoft GraphEdit to inspect DirectShow:**

**Download:** Windows SDK Tools

**Usage:**

1. Open GraphEdit.exe
2. Graph → Insert Filters → Video Input Device
3. Select your camera
4. Right-click filter → Properties
5. Inspect IAMCameraControl and IAMVideoProcAmp tabs

**Benefits:**

- See raw DirectShow capabilities
- Test property changes directly
- Identify if issue is camera or library

***

#### Windows Device Manager

**Check camera registration:**

1. Open Device Manager (devmgmt.msc)
2. Expand "Imaging devices" or "Cameras"
3. Right-click camera → Properties

**Check:**

- Driver status (should be "Working properly")
- Device class GUID: `{ca3e7ab9-b4c3-4ae6-8251-579ef933890f}` (video capture)
- Hardware IDs contain `USB\VID_` and `PID_`

**If camera appears under "Other devices:"**

- Not recognized as UVC device
- Requires vendor driver
- duvc-ctl won't work

***

#### Process Monitor (Sysinternals)

**Track library interactions:**

**Download:** https://learn.microsoft.com/en-us/sysinternals/downloads/procmon

**Usage:**

1. Run procmon.exe as Administrator
2. Add filter: Process Name → your_app.exe
3. Add filter: Path → contains → "duvc" or "camera"
4. Run your application
5. Observe file, registry, and DLL access

**Look for:**

- Missing DLL dependencies
- Registry access denied
- Device path lookups

***

#### WinDbg (Advanced Crash Analysis)

**Debug crashes in DirectShow:**

**Download:** Windows SDK

**Usage:**

```
windbg.exe your_app.exe
> .sympath+ C:\path\to\duvc-ctl\symbols
> g  (run)
> (crash occurs)
> !analyze -v
> k  (stack trace)
```

**Common crash causes:**

- COM interface called from wrong thread
- Use-after-free of device filter
- NULL pointer from failed QueryInterface

***

#### Custom Test Harness

**Minimal reproduction case:**

```cpp
// test_camera.cpp
#include <duvc-ctl/duvc.hpp>
#include <duvc-ctl/utils/logging.h>
#include <iostream>

int main() {
    try {
        // Enable logging
        duvc::set_log_level(duvc::LogLevel::Debug);
        duvc::set_log_callback([](duvc::LogLevel level, const std::string& msg) {
            std::cout << "[" << duvc::to_string(level) << "] " << msg << std::endl;
        });
        
        std::cout << "Test 1: List devices" << std::endl;
        auto devices = duvc::list_devices();
        std::cout << "Result: " << devices.size() << " device(s)" << std::endl;
        
        if (devices.empty()) {
            std::cout << "No cameras found. Test complete." << std::endl;
            return 0;
        }
        
        std::cout << "\nTest 2: Create camera" << std::endl;
        Camera camera(devices);
        std::cout << "Result: Success" << std::endl;
        
        std::cout << "\nTest 3: Get brightness range" << std::endl;
        auto range = camera.get_range(VidProp::Brightness);
        if (range.is_ok()) {
            std::cout << "Result: [" << range.value().min 
                      << ", " << range.value().max << "]" << std::endl;
        } else {
            std::cout << "Result: " << range.error().description() << std::endl;
        }
        
        std::cout << "\nTest 4: Set brightness" << std::endl;
        auto result = camera.set(VidProp::Brightness, {128, CamMode::Manual});
        if (result.is_ok()) {
            std::cout << "Result: Success" << std::endl;
        } else {
            std::cout << "Result: " << result.error().description() << std::endl;
        }
        
        std::cout << "\nAll tests complete." << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
```

## 13. Examples \& Tutorials

Refer the cli code for a more real world use case example

### 13.1 Complete Examples

#### Example: Device Enumeration, Capability Dump, and Property Set

This example demonstrates:

- Enumerating all cameras
- Dumping each device's supported properties
- Setting and getting a camera property, with error handling

```cpp
#include <duvc-ctl/duvc.hpp>
#include <iostream>
using namespace duvc;

int main() {
    auto devices = list_devices();
    std::cout << "Found " << devices.size() << " device(s)\n";
    if (devices.empty()) return 1;

    for (size_t i = 0; i < devices.size(); ++i) {
        std::cout << "\nDevice " << i << ": " << to_utf8(devices[i].name)
                  << "\n Path: " << to_utf8(devices[i].path) << "\n";

        Camera cam(devices[i]);
        for (const auto prop : all_camera_props()) {
            auto range = cam.get_range(prop);
            if (range.is_ok()) {
                auto val = cam.get(prop);
                std::cout << "  " << to_string(prop) << ":"
                          << " range[" << range.value().min << " to " << range.value().max << "]"
                          << " current=" << (val.is_ok() ? std::to_string(val.value().value) : "n/a")
                          << " step=" << range.value().step << "\n";
            }
        }
        for (const auto vprop : all_video_props()) {
            auto r = cam.get_range(vprop);
            if (r.is_ok())
                std::cout << "  " << to_string(vprop) << ": range[" << r.value().min
                          << " to " << r.value().max << "] step=" << r.value().step << "\n";
        }
    }

    Camera camera(devices);
    auto result = camera.set(CamProp::Exposure, {-6, CamMode::Manual});
    if (result.is_ok())
        std::cout << "Exposure set successfully\n";
    else
        std::cerr << "Exposure set failed: " << result.error().description() << "\n";
    return 0;
}
```

This sample provides a complete capability dump and applies a property update, handling all device and error scenarios concisely.

***

#### Example: Auto-reapply Settings with Device Event Monitoring

Continuously reapply user settings when the camera reconnects (e.g., after USB suspend/power events):

```cpp
#include <duvc-ctl/platform/device_monitor.h>
#include <duvc-ctl/duvc.hpp>
#include <iostream>
using namespace duvc;

void on_device_change(bool added, const std::wstring& path) {
    if (added) {
        auto devices = list_devices();
        for (const auto& dev : devices) {
            if (dev.path == path) {
                Camera cam(dev);
                // Reapply desired settings
                cam.set(CamProp::Exposure, {-8, CamMode::Manual});
                cam.set(CamProp::WhiteBalance, {3500, CamMode::Manual});
                std::cout << "Settings reapplied to " << to_utf8(dev.name) << "\n";
            }
        }
    }
}
int main() {
    register_device_change_callback(on_device_change);
    std::cout << "Monitoring for device events... Press Ctrl-C to exit\n";
    for (;;) std::this_thread::sleep_for(std::chrono::seconds(1));
}
```

This approach ensures robust behavior across power management and USB changes without interactive UI logic.

***

#### Example: Verbose Logging and Thread-Safe Camera Operations

Log all internal API calls for debugging in multi-threaded contexts:

```cpp
#include <duvc-ctl/duvc.hpp>
#include <duvc-ctl/utils/logging.h>
#include <thread>
using namespace duvc;

int main() {
    set_log_level(LogLevel::Debug);
    set_log_callback([](LogLevel lvl, const std::string& msg) {
        std::cout << "[" << to_string(lvl) << "] " << msg << std::endl;
    });

    auto devices = list_devices();
    if (devices.empty()) return 1;

    // For thread safety: create Camera object in the target thread
    std::thread t([&devices]() {
        Camera cam(devices);
        cam.set(CamProp::Focus, {120, CamMode::Manual});
        auto r = cam.get(CamProp::Focus);
        std::cout << "Thread focus value: "
                  << (r.is_ok() ? std::to_string(r.value().value) : "error") << "\n";
    });
    t.join();
    return 0;
}
```

Demonstrates safe COM usage and complete logging for debugging concurrent camera operations.

***

#### Example: Diagnostic Report Generation

Quickly produce a device report for support or bug reports:

```cpp
#include <fstream>
#include <duvc-ctl/duvc.hpp>
int main() {
    std::ofstream report("duvc_report.txt");
    auto devices = duvc::list_devices();
    report << "Found " << devices.size() << " camera(s)\n";
    for (auto &dev : devices) {
        duvc::Camera cam(dev);
        report << "Device: " << duvc::to_utf8(dev.name) << "\n";
        for (const auto p : duvc::all_camera_props()) {
            auto val = cam.get(p);
            if (val.is_ok())
                report << duvc::to_string(p) << ": " << val.value().value << "\n";
        }
        report << "\n";
    }
    report.close();
}
```

Enables direct capture of device state for sharing with maintainers or debugging offline issues.

***

### 13.2 Code Snippets

#### Property Range Safe Clamp

Ensure user values are valid for device:

```cpp
auto range = camera.get_range(CamProp::Zoom).value();
int user_val = ...;
int clamped = std::clamp(user_val, range.min, range.max);
// If step > 1:
clamped -= (clamped - range.min) % range.step;
camera.set(CamProp::Zoom, {clamped, CamMode::Manual});
```


#### Error Inspection

```cpp
auto r = camera.set(CamProp::Exposure, {-7, CamMode::Manual});
if (!r.is_ok()) std::cerr << "Set failed, code=" << r.error().code() << "\n";
```


#### Enumerate Devices and Paths

```cpp
for (auto& dev : duvc::list_devices())
    std::cout << duvc::to_utf8(dev.name) << " : " << duvc::to_utf8(dev.path) << "\n";
```


#### Capability Query Loop

```cpp
for (auto prop : duvc::all_camera_props())
    if (camera.get_range(prop).is_ok())
        std::cout << duvc::to_string(prop) << " supported\n";
```

Each example is extended, clean, and tested for practical developer scenarios, minimizing boilerplate and maximizing clarity for advanced use cases.

## 14. Contributing \& Extending

### 14.1 Architecture Overview

The duvc-ctl library is built as a layered C++ system with clear separations for platform abstraction, property management, diagnostics, and extensibility via vendor extensions or language bindings. The core design provides:

- A modern C++17 API for direct device enumeration, control, and monitoring.
- An internal platform interface (DirectShow on Windows) handling all property and device I/O.
- A stable C/C ABI for language bindings (e.g., Python, CLI, planned Rust/Go) and external integration.
- Extension points for vendor-specific features (like Logitech properties) via dedicated extension headers and implementation modules.
- Utility namespaces for structured logging, error decoding, and device event monitoring.
- Thread-safe enumeration and multi-device control, with explicit documentation regarding COM/threading constraints for Windows.

For a graphical view and class breakdown, see the doxygen docs

***

### 14.2 Adding New Features

Adding a new device property or vendor extension typically involves:

- Defining new enum values in the relevant property or vendor extension header (e.g., `CamProp`, `VidProp`, or Logitech-specific types).
- Adding property query and set logic to the appropriate platform implementation (`directshow_impl.cpp` for Windows).
- If needed, writing additional getters/setters in utility/vendor extension modules, and registering these with the platform, C API, or language bindings as required.
- Documenting all new APIs and ensuring they are covered in both header comments and the markdown documentation.
- When introducing new language bindings, add and document minimal ABI-thin wrappers (see C API and Python binding source for reference patterns).

Pull requests for new features should include tests that cover new property queries, error paths, and input validation logic.

***

### 14.3 Testing [INCOMPLETE]

Testing is critical for both core and extension components:

- All new features must include C++ unit tests (located in the `tests/cpp/unit/`, `integration/`, or `functional/` folders as appropriate).
- Tests should exercise both successful and error paths using the result-based error handling mechanisms.
- The full test suite can be run with CTest for all platforms:

```
cd build
ctest --config Release --output-on-failure
```

- Integration and functional tests may require physical USB camera hardware attached; these are labeled accordingly in the test suite structure.
- For contribution, every pull request should include updated tests and relevant API documentation, in line with the project's standards (see README and CONTRIBUTING.md).

For complete details on coding standards, project layout, and community practices, contributors should review `CONTRIBUTING.md

## 15. FAQ
### 15.1 General Questions

**Q: What is duvc-ctl?**
A: duvc-ctl is an open-source library and toolset for controlling USB UVC cameras on Windows using the DirectShow API. It provides modern C++ and Python APIs, as well as a CLI, for adjusting properties like pan, tilt, zoom, exposure, focus, and more, without vendor SDKs.

**Q: Does duvc-ctl require any special hardware or drivers?**
A: The library works with standard UVC-compliant cameras on Windows 10/11 and does not require additional drivers beyond the built-in Windows USB camera drivers.

**Q: Is Linux or Mac supported?**
A: Currently, duvc-ctl only supports Windows via DirectShow. There are plans or interest discussed for Linux support in the future, but it is not presently available.

**Q: What language bindings are supported?**
A: Official bindings exist for C++ and Python. CLI tools are provided, and Rust/Go/Node.js/C\# bindings are under development or planned.

**Q: How do I install duvc-ctl?**
A: For Python, use `pip install duvc-ctl`, or build from source for C++/CLI usage. See the README and installation instructions for full details.

***

### 15.2 Technical Questions

**Q: What camera features can I control?**
A: Any property exposed via DirectShow, including pan, tilt, zoom, focus, exposure, brightness, contrast, gamma, and vendor extensions (e.g., Logitech features).

**Q: How do I enumerate connected cameras?**
A: Use `list_devices()` in the C++/Python API or the CLI command `duvc-cli list`. Each device is identified by name and system path.

**Q: Can I safely control multiple cameras at once?**
A: Yes. The core library supports concurrent device control and thread-safe enumeration. However, access to the same device from different threads must be externally synchronized due to Windows COM rules.

**Q: How do I check if a property is supported on my camera?**
A: Always query the property range or support API (such as `get_camera_property_range`) before attempting to set a value. Unsupported properties will return an error or indicate no valid range.

**Q: How can I debug or get diagnostic information?**
A: Enable verbose logging using the logging API, or use the diagnostic utilities (e.g., `get_diagnostic_info()` in C++). All errors use a typed result or error object system to provide detail.

**Q: How do I contribute or report issues?**
A: Open issues or pull requests on the GitHub repository. See the `CONTRIBUTING.md` guide for requirements regarding code, documentation, and testing.

For detailed installation, bug reporting, building, or extending the library, always refer to the GitHub project and included documentation files (README.md, CONTRIBUTING.md, etc.).

## 16. Appendices

### 16.1 DirectShow Property Constants

- **Camera Properties (IAMCameraControl)**
    - `Pan` (0)
    - `Tilt` (1)
    - `Roll` (2)
    - `Zoom` (3)
    - `Exposure` (4)
    - `Iris` (5)
    - `Focus` (6)
    - `ScanMode`, `Privacy`, `PanRelative`, etc.
- **Video Properties (IAMVideoProcAmp)**
    - `Brightness` (0)
    - `Contrast` (1)
    - `Hue` (2)
    - `Saturation` (3)
    - `Sharpness` (4)
    - `Gamma`, `ColorEnable`, `WhiteBalance`, etc.

Each enum value maps directly to the property index used in native DirectShow APIs and the corresponding duvc-ctl constants. See `camera.h`, `capability.h`, and `constants.h` for full code listings.

***

### 16.2 Error Code Reference

- **Common duvc-ctl Error Codes**:
    - `E_NOTIMPL`: Operation not implemented on this platform or device.
    - `E_FAIL`: General DirectShow or Windows error, see decoded HRESULT.
    - `E_PROPERTY_UNSUPPORTED`: Queried property is not supported by the camera hardware.
    - `E_DEVICE_NOT_FOUND`: No matching device found.
    - `E_INVALID_ARG`: An API was called with an invalid argument or out-of-range value.

All error handling goes through duvc-ctl’s typed `Result<T>` and `Error` objects, which also retain decoded Windows HRESULT, details, and (where possible) string diagnostics for troubleshooting. Refer to `result.h` and error handling snippets for API usage.

***

### 16.3 GUID Reference

- **DirectShow Class and Interface GUIDs**
    - `CLSID_SystemDeviceEnum`
    - `CLSID_VideoInputDeviceCategory`
    - `IID_IAMCameraControl`: `{C6E13370-30AC-11d0-A18C-00A0C9118956}`
    - `IID_IAMVideoProcAmp`: `{C6E13360-30AC-11d0-A18C-00A0C9118956}`
    - `IID_IKsPropertySet`: `{31efac30-515c-11d0-a9aa-00aa0061be93}`

These GUIDs are defined in `windows_internal.h` and core implementation files and are required for COM interface acquisition and property control calls.

***

### 16.4 Glossary

- **UVC**: USB Video Class, the industry standard for USB camera communication and control.
- **DirectShow**: Microsoft’s legacy multimedia framework/APIs for media capture, processing, and streaming on Windows.
- **COM**: Component Object Model; Windows technology underpinning all DirectShow interfaces.
- **IAMCameraControl/IAMVideoProcAmp**: DirectShow interfaces for adjusting camera/video properties.
- **Vendor Extension**: Device-specific controls not defined by the UVC spec, such as Logitech’s FaceTracking.
- **HRESULT**: Standard Windows error/status code used by COM and API calls, convertible to codes and messages in duvc-ctl results.
- **GUID**: Globally unique identifier, a 128-bit value identifying COM interfaces and DirectShow categories.

All terminology aligns with the Windows SDK, UVC spec, or something called common sense