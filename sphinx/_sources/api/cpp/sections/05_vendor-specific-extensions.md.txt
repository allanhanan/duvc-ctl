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

