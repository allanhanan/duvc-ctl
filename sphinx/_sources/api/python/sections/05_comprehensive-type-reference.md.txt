## 5. Comprehensive Type Reference

Understanding the core types used throughout the API helps you work effectively with the library. These types represent devices, properties, settings, and errors that flow through your code.

### 5.1 Core Types \& Their Methods

#### Device type - camera identification

Represents a physical camera connected to the system. Returned by `list_devices()` and used throughout the API to identify which device to open or query. Immutable and hashable.

**Fields**:

- `name` (str): Human-readable device name from DirectShow. Example: `"Logitech C920 HD Webcam"`. Useful for UI display; not guaranteed unique if multiple identical cameras are connected.
- `path` (str): Unique device identifier. Windows: `\\?\USB#VID_046D&PID_082F#...` or similar. Used for persistent device identification across sessions and reboots. More reliable than name for identification.

**Methods**:

`is_valid() -> bool`: Returns True if device is still enumerable and accessible. False if device was disconnected or removed. Use before attempting operations.

```python
device = devices[0]
if device.is_valid():
    result = duvc.open_camera(device)
```

`get_id() -> str`: Returns unique identifier string. Typically equivalent to path. Use this for persistent device tracking.

```python
device_id = device.get_id()
# Save this across sessions to reconnect to same physical device
```

`__eq__(other: Device) -> bool`: Equality comparison. Two Device objects are equal if they represent the same physical device (same path/ID).

```python
device1 = devices[0]
device2 = devices[0]
assert device1 == device2  # Same device
```

`__ne__(other: Device) -> bool`: Inequality. Opposite of `__eq__`.

```python
if device1 != device2:
    print("Different devices")
```

`__hash__() -> int`: Returns hash of device. Enables using Device as dictionary key or in sets.

```python
device_dict = {device: camera_config}
device_set = {devices[0], devices[1]}
```

`__copy__() -> Device`: Shallow copy. Creates new Device object referencing same underlying device.

```python
device_copy = copy.copy(device)
```

`__deepcopy__() -> Device`: Deep copy. Same as shallow copy for Device (immutable).

```python
device_deep = copy.deepcopy(device)
```

`__str__() -> str`: User-friendly string representation. Used by `print()`.

```python
print(device)  # Output: "Logitech C920 HD Webcam"
```

`__repr__() -> str`: Technical representation for debugging. Shows type, name, path, index.

```python
repr(device)
# Output: Device(name='Logitech C920 HD Webcam', path='\\?\USB#...', index=0)
```


***

#### PropSetting type - property value and mode pair

Encapsulates a property's current value and its control mode. When reading properties, you get a PropSetting. When writing, you create and pass a PropSetting.

**Fields**:

- `value`: The actual property value. Type varies: int (brightness 0-255), str (white balance mode), or bool (privacy switch). Depends on property type.
- `mode` (str): How the property is being controlled. Valid values: `'manual'` (user-controlled), `'auto'` (device auto-adjusts), `'continuous'` (ongoing auto-adjustment). Device may not support all modes for all properties.

**Constructor**:

```python
PropSetting(value, mode)
```

Creates new property setting. Both parameters required.

```python
setting1 = duvc.PropSetting(value=128, mode='manual')
setting2 = duvc.PropSetting(value='warm', mode='manual')
setting3 = duvc.PropSetting(value=None, mode='auto')  # For auto-capable properties
```

**Methods**:

`__copy__() -> PropSetting`: Shallow copy. Creates new PropSetting with same value and mode.

```python
copy1 = copy.copy(setting)
```

`__deepcopy__() -> PropSetting`: Deep copy. Same as shallow copy (immutable fields).

```python
copy2 = copy.deepcopy(setting)
```

`__str__() -> str`: User-friendly representation. Shows value and mode.

```python
print(setting)  # Output: PropSetting(value=128, mode='manual')
```

`__repr__() -> str`: Technical representation. Same as __str__ for this type.

```python
repr(setting)
# Output: PropSetting(value=128, mode='manual')
```


***

#### PropRange type - property constraints and bounds

Describes the allowed range for a property. Obtained from `camera.get_range(property)`. Always query range before writing numeric properties.

**Fields**:

- `min` (int): Minimum allowed value for this property on this device.
- `max` (int): Maximum allowed value for this property on this device.
- `step` (int): Increment step. Brightness might step by 1; zoom by 10. Always use step when iterating ranges.
- `default_val` (int): Factory default value (what it ships set to).
- `default_mode` (str): Factory default mode ('manual', 'auto', etc.).

**Methods**:

`is_valid(value: int) -> bool`: Checks if value is within [min, max]. Returns True if valid, False otherwise.

```python
range_result = camera.get_range(duvc.VidProp.Brightness)
if range_result.is_ok():
    r = range_result.value()
    
    if r.is_valid(150):
        print("150 is in valid range")
    else:
        print("150 is out of range")
```

`clamp(value: int) -> int`: Clamps value to [min, max]. Returns value unchanged if in range, or returns min/max if out of bounds. Useful for enforcing range constraints.

```python
user_input = 300
safe_value = r.clamp(user_input)  # Returns max (e.g., 255)

setting = duvc.PropSetting(safe_value, 'manual')
camera.set(duvc.VidProp.Brightness, setting)
```

`__contains__(value: int) -> bool`: Enables `in` operator. Equivalent to `is_valid()`.

```python
if 128 in prop_range:
    print("128 is in range")
else:
    print("128 is out of range")
```

`__copy__() -> PropRange`: Shallow copy. Creates new PropRange with same bounds.

```python
copy1 = copy.copy(range_obj)
```

`__deepcopy__() -> PropRange`: Deep copy. Same as shallow copy (immutable fields).

```python
copy2 = copy.deepcopy(range_obj)
```

`__str__() -> str`: User-friendly representation showing range.

```python
print(prop_range)  # Output: PropRange(min=0, max=255, step=1, default=128)
```

`__repr__() -> str`: Technical representation.

```python
repr(prop_range)
# Output: PropRange(min=0, max=255, step=1, default=128, default_mode='manual')
```


***

#### PropertyCapability type - capability of a single property

Represents what a single property can do on a specific device. Query via `caps.get_video_capability(prop)` or `caps.get_camera_capability(prop)`.

**Fields**:

- `supported` (bool): True if device supports this property, False otherwise. Check first before querying range or current value.
- `range` (PropRange): Valid range for this property (if supported). May be None if property is boolean or doesn't have numeric range.
- `current` (PropSetting): Current value and mode (if accessible). May be None if device is disconnected or range is still querying.

**Methods**:

`supports_auto() -> bool`: Returns True if property can be set to auto or continuous mode, False if only manual mode supported.

```python
cap_result = caps.get_video_capability(duvc.VidProp.Brightness)
if cap_result.is_ok():
    cap = cap_result.value()
    
    if cap.supported:
        if cap.supports_auto():
            # Can set to auto mode
            duvc.PropSetting(None, 'auto')
        else:
            # Manual only
            duvc.PropSetting(128, 'manual')
```

### 5.2 Error \& Status Types

#### DuvcError exception hierarchy

Base exception class for all library errors. Raised by exception-throwing API methods. Subclasses represent specific error categories for precise exception handling.

**Methods**:

`code() -> int`: Returns integer error code (0x01-0x0A). Used to programmatically handle different error types.

```python
try:
    camera = duvc.open_camera_or_throw(0)
except duvc.DuvcError as e:
    code = e.code()
    if code == 0x01:  # ERR_DEVICE_NOT_FOUND
        print("Device disconnected")
    elif code == 0x06:  # ERR_PERMISSION_DENIED
        print("Need elevated privileges")
```

`message() -> str`: Returns internal error message (technical string). Lower-level than description; includes implementation details.

```python
error.message()  # "IMoniker::BindToObject failed with HRESULT 0x80004004"
```

`description() -> str`: Returns user-friendly error explanation. Suitable for displaying to end users or logging.

```python
error.description()  # "Camera is not connected or was disconnected"
```

`get_recovery_suggestions() -> str`: Returns actionable recovery steps for this specific error.

```python
try:
    camera = duvc.open_camera_or_throw(0)
except duvc.DeviceNotFoundError as e:
    print(e.get_recovery_suggestions())
    # Output: "1. Reconnect the camera\n2. Check Device Manager\n3. Restart the application"
```

**Common subclasses**:

- `DeviceNotFoundError`: Device not enumerated. Recovery: reconnect, restart app.
- `DeviceInUseError`: Camera open elsewhere. Recovery: close other apps.
- `PropertyNotSupportedError`: Property not on device. Recovery: query capabilities first.
- `InvalidValueError`: Value out of range. Recovery: use get_range() first.
- `PermissionError`: Insufficient privileges. Recovery: run elevated.
- `HardwareError`: Device hardware failure. Recovery: disconnect/reconnect.

***

#### DeviceCapabilities with iterator support

Container for device capabilities. Implements iterator protocol to iterate over supported properties.

**Iterator methods**:

`__iter__()`: Enables iteration over video properties (default iteration). Used in `for prop in caps` loops.

```python
caps_result = duvc.get_device_capabilities(0)
if caps_result.is_ok():
    caps = caps_result.value()
    
    for prop in caps.supported_video_properties():
        print(duvc.to_string(prop))
```

`__len__()`: Returns count of properties. Use `len(caps.supported_video_properties())` or `len(caps.supported_camera_properties())` for explicit length.

```python
caps_result = duvc.get_device_capabilities(0)
if caps_result.is_ok():
    caps = caps_result.value()
    
    video_count = len(caps.supported_video_properties())
    camera_count = len(caps.supported_camera_properties())
    print(f"Device has {video_count} video and {camera_count} camera properties")
```

**Why iteration matters**: Enables Pythonic loops without manually calling methods, making code cleaner and more readable.

***

#### Camera Result-based with move semantics

`Result[Camera]` from `open_camera()`. Contains Camera object when successful. Internally uses move semantics for efficient resource transfer (pybind11 handles this automatically in Python).

**Meaning of move semantics**: When you call `result.value()`, the underlying C++ Camera object is efficiently transferred to your Python variable without copying expensive resources (file handles, memory).

```python
camera_result = duvc.open_camera(0)
if camera_result.is_ok():
    # Efficient transfer; original Camera in Result is invalidated
    camera = camera_result.value()
    
    # Now 'camera' owns the DirectShow resources
    result = camera.get(duvc.VidProp.Brightness)
```

**Why it matters**: Resources aren't duplicated. No performance penalty for passing Results around; only one Camera object holds the actual DirectShow connections.

***

#### Result<T> complete interface

All Result types share this common interface. The type `T` varies by Result specialization.

**Methods**:

`is_ok() -> bool`: True if Result contains successful value, False if contains error.

```python
result = camera.get(duvc.VidProp.Brightness)
if result.is_ok():
    setting = result.value()
else:
    error = result.error()
```

`is_error() -> bool`: True if Result contains error, False if contains value. Opposite of `is_ok()`.

```python
result = camera.set(duvc.VidProp.Brightness, setting)
if result.is_error():
    print(f"Failed: {result.error().description()}")
    return
```

`value() -> T`: Extract contained value. Only valid if `is_ok()` is true. Raises RuntimeError if called on error Result.

```python
# ✓ Correct
if result.is_ok():
    setting = result.value()

# ✗ Wrong: crashes if error
setting = result.value()
```

`error() -> Error`: Extract error details. Only valid if `is_error()` is true. Returns Error object with `code()`, `description()`, `recoverable()` methods.

```python
if result.is_error():
    error = result.error()
    print(f"Code: {error.code()}, Message: {error.description()}")
```

`__bool__() -> bool`: Enables `if result:` checks. True if ok, False if error.

```python
if camera.get(duvc.VidProp.Brightness):
    print("Read succeeded")
else:
    print("Read failed")
```

**Value extraction patterns**:

Safe extraction with explicit check:

```python
result = camera.get(prop)
if result.is_ok():
    value = result.value()
    # Use value
else:
    handle_error(result.error())
```

Extraction with fallback using `value_or()`:

```python
result = camera.get(prop)
value = result.value_or(duvc.PropSetting(128, 'manual'))
# Always succeeds; uses default if error
```

Early exit on error:

```python
result = camera.get(prop)
if result.is_error():
    return result.error().description()

value = result.value()
# Continue
```

### 5.3 TypedDicts \& Type Definitions

TypedDicts are optional data structure schemas. Use them for structured reporting, logging, or saving device/property state to JSON or databases. Not required by the API; provided for convenience.

#### PropertyInfo TypedDict

Schema for serializing or reporting complete property state. Captures everything about a property: support status, current value, valid range, and any errors.

**Fields**:

`supported` (bool): Whether device supports this property. Query via `caps.supports_video_property(prop)` or `caps.supports_camera_property(prop)`.

```python
info = {
    'supported': caps.supports_video_property(duvc.VidProp.Brightness)
}
```

`current` (dict or None): Current property setting if readable. Contains `value` (int/str/bool) and `mode` (str: 'manual'/'auto'/'continuous'). None if property not supported or unreadable.

```python
result = camera.get(duvc.VidProp.Brightness)
if result.is_ok():
    setting = result.value()
    info['current'] = {
        'value': setting.value,
        'mode': setting.mode
    }
else:
    info['current'] = None
```

`range` (dict or None): Valid numeric range if property has bounds. Contains `min`, `max`, `step`, `default`. None for boolean/enum properties or if range unavailable.

```python
range_result = camera.get_range(duvc.VidProp.Brightness)
if range_result.is_ok():
    r = range_result.value()
    info['range'] = {
        'min': r.min,
        'max': r.max,
        'step': r.step,
        'default': r.default_val
    }
else:
    info['range'] = None
```

`error` (str or None): Error message if querying failed. None if successful.

```python
result = camera.get(prop)
info['error'] = result.error().description() if result.is_error() else None
```

**Full PropertyInfo construction**:

```python
def build_property_info(camera, prop_enum, is_video=True):
    info = {}
    
    caps_result = duvc.get_device_capabilities(0)
    if caps_result.is_error():
        info['error'] = "Cannot query capabilities"
        return info
    
    caps = caps_result.value()
    
    if is_video:
        info['supported'] = caps.supports_video_property(prop_enum)
        current_result = camera.get_video_property(prop_enum)
        range_result = camera.get_range(prop_enum)
    else:
        info['supported'] = caps.supports_camera_property(prop_enum)
        current_result = camera.get_camera_property(prop_enum)
        range_result = camera.get_range(prop_enum)
    
    if not info['supported']:
        info['current'] = None
        info['range'] = None
        info['error'] = None
        return info
    
    if current_result.is_ok():
        setting = current_result.value()
        info['current'] = {'value': setting.value, 'mode': setting.mode}
        info['error'] = None
    else:
        info['current'] = None
        info['error'] = current_result.error().description()
    
    if range_result.is_ok():
        r = range_result.value()
        info['range'] = {'min': r.min, 'max': r.max, 'step': r.step, 'default': r.default_val}
    else:
        info['range'] = None
    
    return info
```


***

#### DeviceInfo TypedDict

Schema for serializing complete device state. Useful for displaying device information, saving device configs, or API responses.

**Fields**:

`name` (str): Device human-readable name from DirectShow.

```python
device = devices[0]
info = {'name': device.name}
```

`path` (str): Unique device identifier (platform-specific path). Use for persistent identification across sessions.

```python
info['path'] = device.path
```

`connected` (bool): Current connection status. True if device enumerable, False if disconnected/removed.

```python
info['connected'] = duvc.is_device_connected(device)
```

`camera_properties` (list of str): List of supported camera property names (pan, tilt, zoom, etc.). Empty if device has no camera controls.

```python
caps_result = duvc.get_device_capabilities(device)
if caps_result.is_ok():
    caps = caps_result.value()
    props = caps.supported_camera_properties()
    info['camera_properties'] = [duvc.to_string(p) for p in props]
else:
    info['camera_properties'] = []
```

`video_properties` (list of str): List of supported video property names (brightness, contrast, saturation, etc.).

```python
if caps_result.is_ok():
    caps = caps_result.value()
    props = caps.supported_video_properties()
    info['video_properties'] = [duvc.to_string(p) for p in props]
else:
    info['video_properties'] = []
```

`error` (str or None): Error message if query failed. None if successful.

```python
info['error'] = caps_result.error().description() if caps_result.is_error() else None
```

**Full DeviceInfo construction**:

```python
def build_device_info(device):
    info = {}
    
    info['name'] = device.name
    info['path'] = device.path
    info['connected'] = duvc.is_device_connected(device)
    
    caps_result = duvc.get_device_capabilities(device)
    
    if caps_result.is_ok():
        caps = caps_result.value()
        camera_props = caps.supported_camera_properties()
        video_props = caps.supported_video_properties()
        
        info['camera_properties'] = [duvc.to_string(p) for p in camera_props]
        info['video_properties'] = [duvc.to_string(p) for p in video_props]
        info['error'] = None
    else:
        info['camera_properties'] = []
        info['video_properties'] = []
        info['error'] = caps_result.error().description()
    
    return info

# Use for logging or JSON serialization
devices = duvc.list_devices()
all_devices_info = [build_device_info(d) for d in devices]
print(json.dumps(all_devices_info, indent=2))
```


***

### 5.4 Windows-Only Types

These types are Windows-specific implementations. They wrap DirectShow and KsProperty APIs. Only available on Windows; not relevant on other platforms.

#### VendorProperty type - OEM/manufacturer extensions

Represents vendor-specific (proprietary) camera properties not in standard UVC spec. Different manufacturers (Logitech, Intel, etc.) expose custom controls via vendor properties.

**What they are**: Beyond standard UVC properties like brightness, some cameras have manufacturer-specific features: LED control, focus speed, advanced stabilization, color temperature presets, etc. These are exposed as VendorProperty.

**How they're accessed**: Internally, VendorProperty wraps a property ID and access path. You query vendor properties through the same API as standard properties, but you must know the property ID in advance (no enum constant; usually documented by manufacturer).

**Platform context**: On Windows, DirectShow supports both standard UVC properties (via IAMCameraControl/IAMVideoProcAmp) and vendor extensions (via IKsPropertySet). VendorProperty abstracts this DirectShow layer.

**Example scenario**:

```python
# Standard property access (universally available)
brightness_result = camera.get(duvc.VidProp.Brightness)

# Vendor property access (device-specific)
# You'd need the vendor property ID from camera documentation
# Example: Logitech may use a specific KSPROPERTY ID for LED control
# This is handled internally; not exposed directly in Python API
```

**Why included in docs**: Knowing VendorProperty exists helps explain why some cameras support properties beyond the standard set. Most applications use standard properties; vendor properties are for advanced/specialized use cases.

***

#### DeviceConnection type - lifecycle management

Represents the active DirectShow connection to a physical device. Manages COM object lifecycle and exclusive device access. Internal implementation detail; normally managed automatically by Camera class.

**What it encapsulates**: DirectShow COM objects (IMoniker, IBaseFilter, IAMCameraControl, IAMVideoProcAmp, IKsPropertySet). These must be created when opening a camera and properly released when closing.

**Lifecycle**:

1. Device enumeration: DirectShow enumerates devices via IMoniker.
2. Connection: DeviceConnection created when opening camera; acquires exclusive device access.
3. Operations: Property reads/writes go through DirectShow interfaces.
4. Disconnection: DeviceConnection destroyed; DirectShow resources released.

**Why move semantics matter**: When Camera closes, DeviceConnection destructor runs, releasing all COM object references. Ensures no resource leaks or device locks.

**Advanced use** (rare):

```python
# Normally Camera handles this automatically
camera_result = duvc.open_camera(0)
if camera_result.is_ok():
    camera = camera_result.value()
    # Camera internally owns a DeviceConnection
    # When camera goes out of scope, DeviceConnection releases resources
```

If you need to manually manage connection lifecycle (e.g., disconnecting without destroying Camera), you'd work with DeviceConnection directly, but this is not exposed in the Python API. It's internal only.

***

#### KsPropertySet type - DirectShow property interface

Low-level wrapper for DirectShow's IKsPropertySet COM interface. Handles reading/writing hardware properties at the Windows multimedia level. Purely internal; not directly accessible from Python.

**What it does**: Translates between high-level property enums (VidProp, CamProp) and low-level DirectShow KSPROPERTY structures. Queries Windows for property support and ranges.

**Properties it manages**:

- **Camera control properties** (KSPROPERTY_CAMERACONTROL_*): Pan, tilt, zoom, focus, iris, shutter, gain, roll.
- **Video proc-amp properties** (KSPROPERTY_VIDCAP_VIDEOPROCAMP_*): Brightness, contrast, saturation, hue, etc.
- **Vendor extensions** (IKsPropertySet): Device-specific properties.

**Example property ID** (internal):

```cpp
// Internal C++ code (not exposed to Python)
KSPROPERTY_CAMERACONTROL_PAN -> maps to duvc.CamProp.Pan
KSPROPERTY_VIDEOPROCAMP_BRIGHTNESS -> maps to duvc.VidProp.Brightness
```

**Why it matters for developers**: Understanding KsPropertySet helps explain why property access might fail on certain Windows versions or drivers. If a property reads as unsupported, it's likely because KsPropertySet can't access that KSPROPERTY_* on this device/driver combo.

***

#### Platform-specific implementation

duvc-ctl abstracts away platform differences. Currently Windows-only; architecture allows future porting.

**Windows implementation layers**:


| Layer | Technology | Purpose |
| :-- | :-- | :-- |
| Python API | duvc_ctl module | User-facing API (list_devices, open_camera, etc.) |
| C++ bindings | pybind11 | Python ↔ C++ bridge |
| C++ core | Windows DirectShow | Device enumeration, property access |
| DirectShow | COM/IMoniker | Device discovery (ICreateDevEnum, IMoniker) |
| DirectShow | COM/IBaseFilter | Device connection |
| DirectShow | COM/IAMCameraControl | Camera properties (pan, tilt, zoom) |
| DirectShow | COM/IAMVideoProcAmp | Video properties (brightness, contrast) |
| DirectShow | COM/IKsPropertySet | Extended/vendor properties |
| OS | Windows Multimedia | DirectShow runtime |

**Why this layering**: Each layer abstracts complexity. Python developers don't see DirectShow COM objects; C++ abstracts it. This design allows porting to Linux (V4L2) or macOS (AVFoundation) without changing Python API.

**For developers**: If troubleshooting device issues, understand that failure points occur at different layers:

- Device not enumerated → ICreateDevEnum/IMoniker issue
- Device open fails → IBaseFilter issue
- Property read fails → IAMCameraControl/IAMVideoProcAmp/IKsPropertySet issue
- Permission denied → OS/driver issue

The library surfaces these as error codes and messages; understanding layers helps diagnose root cause.

