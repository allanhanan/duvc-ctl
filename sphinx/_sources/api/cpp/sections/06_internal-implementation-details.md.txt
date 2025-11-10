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

