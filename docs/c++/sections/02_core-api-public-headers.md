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

#### find_device_by_path() - lookup by Windows device path

Find device by Windows device path (case-insensitive matching).

```cpp
Device find_device_by_path(const std::wstring& path);
```

Searches the list of connected devices for one matching the given Windows device path. Path comparison is case-insensitive using `wcsicmp`. This function re-enumerates devices using DirectShow to ensure the latest list is queried.

**Parameters:**
- `path` (const std::wstring&) – Windows device path (e.g., `L"\\?\USB#VID_046D&PID_082D#..."`). Can be in any case.

**Returns:**
- Device object if found with the matching path

**Throws:**
- `std::runtime_error` – If DirectShow enumeration fails
- `std::runtime_error` – If no matching device found (path not in any connected camera)

**Implementation notes:**
- Uses case-insensitive string comparison (`wcsicmp`) for flexible path matching
- Re-enumerates devices via `list_devices()` to reflect current hardware state
- If path not found after enumeration, throws exception with descriptive error message
- Useful for recovering a device reference when saved path is available

**Usage patterns:**

```cpp
// Save device path on first run
auto devices = duvc::list_devices();
std::wstring saved_path = devices[0].path;

// Later session - reconnect using saved path
try {
    duvc::Device device = duvc::find_device_by_path(saved_path);
    duvc::Camera cam(device);
    // Use camera...
} catch (const std::runtime_error& e) {
    std::cerr << "Device not found at saved path: " << e.what() << std::endl;
}
```

**Multi-camera scenario:**

```cpp
// Multiple cameras with same name - use path for disambiguation
std::vector<duvc::Device> devices = duvc::list_devices();
std::map<std::wstring, std::wstring> device_map;  // path -> name

for (const auto& dev : devices) {
    device_map[dev.path] = dev.name;
}

// Reconnect all stored devices
for (const auto& [path, name] : device_map) {
    try {
        auto device = duvc::find_device_by_path(path);
        auto cam = duvc::Camera(device);
        std::wcout << L"Connected: " << cam.get_device().name << std::endl;
    } catch (...) {
        std::wcout << L"Device " << name << L" not found" << std::endl;
    }
}
```

**Error handling:**

```cpp
// Graceful fallback to enumeration if saved path unavailable
std::wstring saved_path = get_saved_camera_path();

duvc::Device device;
try {
    device = duvc::find_device_by_path(saved_path);
} catch (const std::runtime_error&) {
    // Camera not at saved path, use first available
    auto devices = duvc::list_devices();
    if (devices.empty()) {
        throw std::runtime_error("No cameras available");
    }
    device = devices[0];
}

duvc::Camera cam(device);
```

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

#### open_camera() with device path – factory function

```cpp
ResultCamera open_camera(const std::wstring& path);
```

Opens a camera by Windows device path. Convenience function combining `find_device_by_path()` and camera construction with explicit error handling.

**Parameters:**
- `path` (const std::wstring&) – Device path (case-insensitive)

**Returns:**
- `ResultCamera` – On success, contains valid Camera object; on error, contains error details

**Error codes:**
- `ErrorCode::DeviceNotFound` – Device not found at given path
- `ErrorCode::DeviceBusy` – Device already in use by another application
- `ErrorCode::SystemError` – DirectShow or platform error

**Usage:**

```cpp
// Result-based error handling
auto cam_result = duvc::open_camera(L"\\?\USB#VID_046D&PID_082D...");

if (cam_result.is_ok()) {
    auto cam = std::move(cam_result.value());
    auto result = cam.get(duvc::VidProp::Brightness);
    if (result.is_ok()) {
        std::cout << "Brightness: " << result.value().value << std::endl;
    }
} else {
    std::cerr << "Failed to open camera: " << cam_result.error().description() << std::endl;
}
```

**Persistent reconnection pattern:**

```cpp
// Save on first run
std::wstring camera_path = devices[0].path;
config.set("camera_path", camera_path);

// Reconnect on next run
std::wstring saved_path = config.get("camera_path");
auto cam_result = duvc::open_camera(saved_path);

if (cam_result.is_ok()) {
    auto cam = std::move(cam_result.value());
    // Use camera
} else {
    // Fallback to first available camera
    auto fallback_result = duvc::open_camera(0);  // By index
}
```

**Implementation:**
- Internally calls `find_device_by_path()` to locate device
- Constructs Camera and performs basic validity checks
- Returns Result type for explicit error handling instead of exceptions

**Advantages over exception-based approach:**
- No exceptions thrown – returns error codes in Result
- Explicit error checking required – prevents silent failures
- Error context included – full error description available
- Chainable for error propagation

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

