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

