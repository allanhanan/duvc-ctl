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

