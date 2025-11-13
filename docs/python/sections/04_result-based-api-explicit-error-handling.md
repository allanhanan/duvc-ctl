## 4. Result-Based API - Explicit Error Handling


The Result-Based API provides explicit, exception-free error handling by returning Result<T> objects instead of raising exceptions. This is ideal for production systems, real-time processing, and code that needs predictable performance without exception overhead. Unlike the Pythonic API where you use try-except blocks, the Result-Based API requires you to explicitly check whether operations succeeded or failed.

### 4.1 Core Functions \& Device Enumeration

The Result-Based API starts with module-level functions for discovering and opening cameras. These functions give explicit control over device lifecycle without automatic resource management. All device enumeration and connection functions are designed for maximum control in production systems.

#### `list_devices()` enumerating connected cameras

Discovers all cameras physically connected to the system. This is the entry point for all Result-Based workflows—you always start by discovering available devices, then selecting one to open.

```python
def list_devices() -> List[Device]:
    """Enumerate all connected camera devices."""
```

**Returns**: Python `list` of `Device` objects. Never raises exceptions—always succeeds. Returns empty list `[]` if no cameras found.

**Device object structure**: Each `Device` contains:

- `name`: Human-readable device name (e.g., "Logitech C920 HD").
- `path`: Platform-specific device identifier. On Linux: `/dev/videoX`. On Windows: `\\?\USB#VID_...#...`. Used for reconnection and persistent device tracking.
- `index`: Integer index in camera list (0-based). Can be used as shorthand instead of passing Device object.

**Usage patterns**:

```python
# Discover cameras
devices = duvc.list_devices()
print(f"Found {len(devices)} camera(s)")

# Iterate all devices
for i, device in enumerate(devices):
    print(f"  [{i}] {device.name}")
    print(f"      Path: {device.path}")
    print(f"      Index: {device.index}")

# Save device info for later reconnection
if devices:
    first_device = devices[0]
    saved_path = first_device.path
    
    # Later: can identify same physical device by path
    new_list = duvc.list_devices()
    for dev in new_list:
        if dev.path == saved_path:
            print("Found same device again")
            break
```

**Lifecycle context**: `list_devices()` performs hardware enumeration via DirectShow. This can take 100-500ms on systems with many USB devices. Cache results when possible to avoid repeated queries.

#### `open_camera()` connecting to a device

Opens a connection to a camera. This is the main entry point for Result-Based camera operations. Always returns a `Result<Camera>`; never throws.

```python
def open_camera(device: Device | int) -> Result[Camera]:
    """Open camera connection. Returns Result<Camera>."""
```

**Overloads**:

- `open_camera(Device)`: Pass a `Device` object from `list_devices()`.
- `open_camera(int)`: Pass device index (0, 1, 2, etc.). Convenience equivalent to `open_camera(list_devices()[index])`.

**Returns `Result[Camera]`** which is either:

- **Ok state**: Contains a `Camera` object ready for read/write operations.
- **Error state**: Contains an error describing why opening failed (device in use, disconnected, permissions, etc.).

**Opening device semantics**:

- Acquires exclusive access to the device. No other process can use it while open.
- Queries device capabilities internally.
- Validates device connectivity; fails if device disconnected.
- Does NOT perform any property read/write; only establishes connection.

**Usage with error checking**:

```python
# Method 1: Pass Device object
camera_result = duvc.open_camera(devices[0])

# Method 2: Pass index shorthand
camera_result = duvc.open_camera(0)

# Always check if successful
if camera_result.is_ok():
    camera = camera_result.value()
    print("Camera opened successfully")
    # Now safe to use camera object
    
    # Read/write properties...
    brightness_result = camera.get(duvc.VidProp.Brightness)
    # ...
    
else:
    error = camera_result.error()
    error_code = error.code()
    error_msg = error.description()
    print(f"Failed to open: {error_msg} (code: {error_code})")
```

**Common failure reasons**:

- Device already open in another application → Close it there, then retry.
- Device disconnected → Reconnect USB, re-run `list_devices()`, try again.
- Permission denied → Run with administrator/elevated privileges.
- Device driver missing → Install camera-specific drivers or Windows updates.


#### `is_device_connected()` checking device availability

Quick validation to determine if a device is still accessible without opening it. Useful for verifying device status before operations.

```python
def is_device_connected(device: Device) -> bool:
    """Check if device is currently connected and accessible."""
```

**Returns**: Plain `bool` (True/False). Never raises exceptions.

**Implementation**: Performs lightweight DirectShow enumeration check. Does not acquire exclusive access.

**Use cases**:

- Validate device before `open_camera()` to provide better error messages.
- Detect device hotplug events (disconnect/reconnect).
- Monitor device availability in long-running applications.

**Usage**:

```python
devices = duvc.list_devices()

for device in devices:
    if duvc.is_device_connected(device):
        print(f"✓ {device.name} is available")
        
        # Safe to open
        result = duvc.open_camera(device)
        if result.is_ok():
            camera = result.value()
            # Use camera...
    else:
        print(f"✗ {device.name} is disconnected")
        # Don't attempt to open
```


#### `get_device_capabilities()` querying supported properties

Asks a device which properties it supports. Returns `Result[DeviceCapabilities]` containing lists of supported video/camera properties.

```python
def get_device_capabilities(device: Device | int) -> Result[DeviceCapabilities]:
    """Query device capabilities without opening exclusive connection."""
```

**Overloads**:

- `get_device_capabilities(Device)`: Pass Device from `list_devices()`.
- `get_device_capabilities(int)`: Pass index shorthand.

**Returns `Result[DeviceCapabilities]`** containing:

- `supported_video_properties()`: List of supported video properties (brightness, contrast, etc.).
- `supported_camera_properties()`: List of supported camera properties (pan, tilt, zoom, etc.).
- `supports_video_property(VidProp)`: Boolean check for specific property.
- `supports_camera_property(CamProp)`: Boolean check for specific property.

**Key difference from `open_camera()`**: Does NOT acquire exclusive access. Multiple processes can query capabilities simultaneously. Useful for device discovery without blocking exclusive access.

**Capabilities query timing**: Capabilities are static per device model. Once known, can be cached.

**Usage pattern**:

```python
# Query capabilities before opening
caps_result = duvc.get_device_capabilities(0)

if caps_result.is_ok():
    caps = caps_result.value()
    
    # Check what this device supports
    video_props = caps.supported_video_properties()
    print(f"Video properties: {len(video_props)}")
    for prop in video_props:
        print(f"  - {duvc.to_string(prop)}")
    
    # Check specific property
    if caps.supports_video_property(duvc.VidProp.Brightness):
        print("Device supports brightness adjustment")
    
    if caps.supports_camera_property(duvc.CamProp.Pan):
        print("Device supports pan")
    
    # Now decide whether to open it
    if caps.supports_video_property(duvc.VidProp.Brightness):
        result = duvc.open_camera(0)
        # Safe to proceed with brightness operations
        
else:
    error = caps_result.error()
    print(f"Cannot query capabilities: {error.description()}")
```


#### `open_camera_or_throw()` exception-throwing wrapper

Convenience wrapper around `open_camera()` that raises an exception on failure instead of returning Result. Useful when mixing Result-based and exception-based code, or when you want fast-fail behavior.

```python
def open_camera_or_throw(device: Device | int) -> Camera:
    """Open camera or raise exception. Returns Camera (not Result)."""
```

**Behavior**: Internally calls `open_camera()`, checks `is_ok()`, and either returns the value or raises a `ErrorInfo` subclass.

**Raised exceptions**:

- `DeviceNotFoundError`: Device disconnected or not in enumeration.
- `DeviceInUseError`: Camera already open in another process.
- `PermissionError`: Lack of OS permissions.
- `HardwareError`: Generic device hardware failure.

**Usage**:

```python
try:
    camera = duvc.open_camera_or_throw(0)
    print("Camera opened")
    
except duvc.DeviceNotFoundError:
    print("Camera disconnected")
except duvc.DeviceInUseError:
    print("Camera in use by another application")
except duvc.PermissionError:
    print("Need elevated privileges")
```

**When to use**: Simpler code when exceptions fit your error handling style. Not recommended for production high-frequency code due to exception overhead.

#### `get_device_capabilities_or_throw()` exception-throwing wrapper

Convenience wrapper for `get_device_capabilities()` that raises instead of returning Result.

```python
def get_device_capabilities_or_throw(device: Device | int) -> DeviceCapabilities:
    """Get capabilities or raise exception."""
```

**Usage**:

```python
try:
    caps = duvc.get_device_capabilities_or_throw(0)
    supported = caps.supported_video_properties()
    print(f"Supports {len(supported)} video properties")
    
except duvc.PropertyAccessError:
    print("Cannot query this device")
```


#### Error codes mapping reference

When a Result is in error state, call `error().code()` to get the numeric error code. This reference maps codes to meanings and recovery strategies.


| Error Code | Name | Meaning | Recovery Strategy |
| :-- | :-- | :-- | :-- |
| 0x01 | `ERR_DEVICE_NOT_FOUND` | Device not found in enumeration | Call `list_devices()` again; reconnect USB |
| 0x02 | `ERR_DEVICE_IN_USE` | Camera open in another process | Close other apps/processes using camera |
| 0x03 | `ERR_INVALID_DEVICE` | Device object is invalid or stale | Get fresh `Device` from `list_devices()` |
| 0x04 | `ERR_PROPERTY_NOT_SUPPORTED` | Property not on this device model | Query capabilities with `get_device_capabilities()` |
| 0x05 | `ERR_INVALID_VALUE` | Value outside device range | Call `get_range()` before setting; use returned range |
| 0x06 | `ERR_PERMISSION_DENIED` | Insufficient OS permissions | Run with admin/elevated privileges |
| 0x07 | `ERR_TIMEOUT` | Device did not respond in time | Reconnect device; may indicate hardware issue |
| 0x08 | `ERR_HARDWARE_ERROR` | Generic device hardware failure | Disconnect/reconnect; test with different USB port |
| 0x09 | `ERR_COMMUNICATION_ERROR` | USB or COM communication failure | Check USB cable; restart application |
| 0x0A | `ERR_ALREADY_CONNECTED` | Camera already open | Close first with `camera.close()` or use new Camera object |

**Accessing error details**:

```python
result = duvc.open_camera(0)

if result.is_error():
    error = result.error()
    
    code = error.code()              # Integer error code
    description = error.description() # Human-readable message
    
    # Handle based on code
    if code == 0x02:  # ERR_DEVICE_IN_USE
        print("Close the other application using the camera")
    elif code == 0x06:  # ERR_PERMISSION_DENIED
        print("Run as administrator")
    else:
        print(f"Unknown error: {description}")
```


***

### 4.2 Camera Class - Result-Based Operations

Once you have a `Camera` object from `open_camera()`, you use its methods to read and write properties. All operations return `Result<T>`, requiring explicit success checks. The Camera class encapsulates a single device connection with fine-grained error handling.

#### Camera constructor

Construct a Camera from Device or index. Normally you don't call this directly; use `open_camera()` instead. Exposed for advanced scenarios.

```python
class Camera:
    def __init__(self, device: Device | int):
        """Initialize Camera from Device or device index."""
        # Internally calls open_camera(device) logic
```

**Not recommended**: Always use `open_camera()` or `open_camera_or_throw()` which return Results and handle errors properly. Direct constructor use bypasses error checking.

#### `is_valid()` \& `is_ok()` validation checks

Check if a camera is open and responsive. Quick pre-operation validation.

```python
def is_valid(self) -> bool:
    """True if camera is open, connected, and responsive."""

def is_ok(self) -> bool:
    """Alias for is_valid(). True if ready for operations."""
```

**Implementation**: Performs lightweight connectivity check (usually property read ping).

**Usage**:

```python
camera_result = duvc.open_camera(0)
if camera_result.is_ok():
    camera = camera_result.value()
    
    # Perform operations only if valid
    if camera.is_valid():
        result = camera.get(duvc.VidProp.Brightness)
    else:
        print("Camera became invalid")
```

**Reconection pattern**: If `is_valid()` returns False, device likely disconnected. Create new Camera object via `open_camera()` or reconnect manually.

#### `device()` property accessor

Get the underlying `Device` object associated with this camera connection.

```python
@property
def device(self) -> Device:
    """Return the Device this camera is connected to."""
```

**Usage**:

```python
camera = camera_result.value()
device = camera.device()
print(f"Camera: {device.name}")
print(f"Path: {device.path}")
print(f"Index: {device.index}")
```

**Persistence**: Can save `device.path` for reconnection in next session:

```python
# Session 1
devices = duvc.list_devices()
camera = duvc.open_camera(devices[0]).value()
saved_path = camera.device().path

# Session 2
devices_later = duvc.list_devices()
for dev in devices_later:
    if dev.path == saved_path:
        camera = duvc.open_camera(dev).value()
        break
```


#### `get()` reading any property

Read a video or camera property. Takes property enum, returns `Result[PropSetting]`.

```python
def get(self, property: VidProp | CamProp) -> Result[PropSetting]:
    """Read property value and mode. Returns Result<PropSetting>."""
```

**Returns `Result[PropSetting]`** where PropSetting contains:

- `value`: Current numeric value (int) or string value (str).
- `mode`: Current mode string ('manual', 'auto', 'continuous', etc.).

**Overloads**:

- `get(VidProp.Brightness)`: Read video property.
- `get(CamProp.Pan)`: Read camera property.

**Error cases**:

- Property unsupported on device → Error with `ERR_PROPERTY_NOT_SUPPORTED`.
- Device disconnected → Error with `ERR_DEVICE_NOT_FOUND`.
- Permission denied → Error with `ERR_PERMISSION_DENIED`.

**Usage with full error handling**:

```python
result = camera.get(duvc.VidProp.Brightness)

if result.is_ok():
    setting = result.value()
    print(f"Brightness: {setting.value} (mode: {setting.mode})")
    
elif result.is_error():
    error = result.error()
    if error.code() == 0x04:  # ERR_PROPERTY_NOT_SUPPORTED
        print("Device doesn't support brightness")
    else:
        print(f"Error: {error.description()}")
```

**Property value types**:

- Numeric properties (brightness, zoom): `setting.value` is integer.
- Enum properties (white balance mode, focus): `setting.value` is string.
- Boolean properties (privacy): `setting.value` is boolean.


#### `set()` writing properties

Write a property to new value and mode. Takes property enum and `PropSetting`, returns `Result[void]`.

```python
def set(self, property: VidProp | CamProp, setting: PropSetting) -> Result[void]:
    """Write property value and mode. Returns Result<void>."""
```

**PropSetting construction**: Create with `duvc.PropSetting(value, mode)`:

```python
# Numeric value, manual mode
setting1 = duvc.PropSetting(value=128, mode='manual')

# String value
setting2 = duvc.PropSetting(value='auto', mode='manual')

# Boolean value
setting3 = duvc.PropSetting(value=True, mode='manual')
```

**Overloads**:

- `set(VidProp.Brightness, PropSetting(...))`: Write video property.
- `set(CamProp.Pan, PropSetting(...))`: Write camera property.

**Returns**: `Result[void]` (no value on success; just ok/error).

**Error cases**:

- Value out of range → `ERR_INVALID_VALUE`.
- Property unsupported → `ERR_PROPERTY_NOT_SUPPORTED`.
- Device disconnected → `ERR_DEVICE_NOT_FOUND`.

**Full set workflow** (read range, validate, write):

```python
# 1. Get range
range_result = camera.get_range(duvc.VidProp.Brightness)
if range_result.is_error():
    print(f"Cannot query range: {range_result.error().description()}")
    return

prop_range = range_result.value()

# 2. Validate proposed value is in range
proposed_value = 200
if not (prop_range.min <= proposed_value <= prop_range.max):
    print(f"Value {proposed_value} out of range [{prop_range.min}, {prop_range.max}]")
    return

# 3. Create setting
setting = duvc.PropSetting(value=proposed_value, mode='manual')

# 4. Write
set_result = camera.set(duvc.VidProp.Brightness, setting)
if set_result.is_ok():
    print("Brightness set successfully")
else:
    print(f"Failed: {set_result.error().description()}")
```


#### `set_auto()` enabling automatic mode

Convenience method to enable automatic/continuous mode for a property. Returns `Result[void]`.

```python
def set_auto(self, property: VidProp | CamProp) -> Result[void]:
    """Enable auto mode for property if device supports it."""
```

**Implementation**: Internally calls `get()` to read current setting, updates mode to 'auto', calls `set()` to write back.

**Supported auto modes**:

- Video properties: white_balance, exposure, focus, iris, shutter, gain.
- Camera properties: pan, tilt, zoom (may vary by device).

**Usage**:

```python
# Enable auto white balance
result = camera.set_auto(duvc.VidProp.WhiteBalance)
if result.is_ok():
    print("Auto white balance enabled")
else:
    print(f"Cannot enable auto: {result.error().description()}")

# Enable continuous autofocus
result = camera.set_auto(duvc.VidProp.Focus)
if result.is_ok():
    print("Continuous autofocus enabled")
```


#### `get_range()` querying property limits

Query min/max/step values for a property. Returns `Result[PropRange]`.

```python
def get_range(self, property: VidProp | CamProp) -> Result[PropRange]:
    """Get property range constraints. Returns Result<PropRange>."""
```

**Returns `Result[PropRange]`** containing:

- `min`: Minimum supported value.
- `max`: Maximum supported value.
- `step`: Increment step (e.g., brightness may step by 1, zoom by 10).
- `default`: Factory default value.
- `current`: Current value.

**Critical for safe writes**: Always call `get_range()` before `set()` to avoid out-of-range errors.

**Usage**:

```python
range_result = camera.get_range(duvc.VidProp.Brightness)

if range_result.is_ok():
    r = range_result.value()
    print(f"Brightness range: {r.min} to {r.max} (step {r.step})")
    print(f"Default: {r.default}, Current: {r.current}")
    
    # Safe operations based on range
    for val in range(r.min, r.max + 1, r.step):
        setting = duvc.PropSetting(val, 'manual')
        camera.set(duvc.VidProp.Brightness, setting)
        
else:
    print(f"Cannot query range: {range_result.error().description()}")
```

**Pan/tilt/zoom ranges**: Often have larger steps. Example: pan -180 to +180 with step=1, zoom 100 to 400 with step=10.

#### `get_camera_property()` explicit camera property read

Explicit method for reading camera properties (pan, tilt, zoom, focus, roll, etc.). Functionally identical to `get(CamProp)` but makes intent clear.

```python
def get_camera_property(self, property: CamProp) -> Result[PropSetting]:
    """Read camera property (pan, tilt, zoom, etc.)."""
```

**Usage**:

```python
pan_result = camera.get_camera_property(duvc.CamProp.Pan)
if pan_result.is_ok():
    print(f"Pan: {pan_result.value().value}°")
```


#### `get_video_property()` explicit video property read

Explicit method for reading video properties (brightness, contrast, saturation, etc.). Functionally identical to `get(VidProp)` but makes intent clear.

```python
def get_video_property(self, property: VidProp) -> Result[PropSetting]:
    """Read video property (brightness, contrast, etc.)."""
```

**Usage**:

```python
brightness_result = camera.get_video_property(duvc.VidProp.Brightness)
if brightness_result.is_ok():
    print(f"Brightness: {brightness_result.value().value}")
```


#### Result pattern best practices

**Best Practice 1: Always check Result before accessing value**

```python
# ✓ Correct
result = camera.get(duvc.VidProp.Brightness)
if result.is_ok():
    value = result.value()
    # Use value safely
    
# ✗ Wrong: accessing without check crashes
value = result.value()  # Crash if error!
```

**Best Practice 2: Use `value_or()` for graceful fallback**

```python
# Get brightness with default fallback
result = camera.get(duvc.VidProp.Brightness)
setting = result.value_or(duvc.PropSetting(128, 'manual'))
print(f"Brightness: {setting.value}")  # Always works
```

**Best Practice 3: Chain property reads**

```python
# Read multiple properties, collect results
properties = [duvc.VidProp.Brightness, duvc.VidProp.Contrast, duvc.VidProp.Saturation]
results = {}

for prop in properties:
    results[prop] = camera.get(prop)

# Process results
for prop, result in results.items():
    if result.is_ok():
        print(f"{duvc.to_string(prop)}: {result.value().value}")
    else:
        print(f"{duvc.to_string(prop)}: Error - {result.error().description()}")
```

**Best Practice 4: Validate ranges before write**

```python
def safe_set_brightness(camera, target_brightness):
    # Get range first
    range_result = camera.get_range(duvc.VidProp.Brightness)
    if range_result.is_error():
        return False
    
    r = range_result.value()
    
    # Clamp to valid range
    clamped = max(r.min, min(r.max, target_brightness))
    
    # Write safely
    setting = duvc.PropSetting(clamped, 'manual')
    set_result = camera.set(duvc.VidProp.Brightness, setting)
    
    return set_result.is_ok()
```

**Best Practice 5: Differentiate video vs camera properties**

```python
# Clear code intent by using explicit methods
brightness = camera.get_video_property(duvc.VidProp.Brightness)  # Video
pan = camera.get_camera_property(duvc.CamProp.Pan)               # Camera

# Or use generic get() with appropriate enum
brightness = camera.get(duvc.VidProp.Brightness)
pan = camera.get(duvc.CamProp.Pan)
```

### 4.3 Result<T> Type System

The Result-based API uses typed Result objects to represent success or failure. Each Result type is specialized for what it contains, ensuring type safety. Understanding the different Result types helps you know what to expect from each operation.

#### Result types by operation

**PropSettingResult** - Contains property value and mode

Returned by `camera.get(prop)`, `camera.get_video_property()`, `camera.get_camera_property()`. When successful, contains a `PropSetting` object with a `value` field (int, str, or bool) and a `mode` field ('manual', 'auto', 'continuous'). When error, contains error code and message explaining why the read failed.

```python
result = camera.get(duvc.VidProp.Brightness)
if result.is_ok():
    setting = result.value()
    print(f"Value: {setting.value}, Mode: {setting.mode}")
```

**PropRangeResult** - Contains property constraints

Returned by `camera.get_range(prop)`. When successful, contains a `PropRange` object with `min`, `max`, `step`, `default`, and `current` fields. Use this to validate values before writing them. When error, may indicate the device doesn't support range queries or is disconnected.

```python
result = camera.get_range(duvc.VidProp.Brightness)
if result.is_ok():
    r = result.value()
    print(f"Range: {r.min}-{r.max}, Step: {r.step}")
```

**VoidResult** - No return value

Returned by `camera.set(prop, setting)` and `camera.set_auto(prop)`. These operations have nothing meaningful to return—only success or failure. Check `is_ok()` to determine success. Never call `value()` on VoidResult because there is no value.

```python
set_result = camera.set(duvc.VidProp.Brightness, setting)
if set_result.is_ok():
    print("Set succeeded")
else:
    print(f"Set failed: {set_result.error().description()}")
```

**CameraResult** - Opened camera object

Returned by `open_camera(device)`. When successful, contains a `Camera` object ready for operations. When error, contains details on why opening failed (device in use, disconnected, permissions). Uses move semantics internally for efficient resource transfer.

```python
camera_result = duvc.open_camera(0)
if camera_result.is_ok():
    camera = camera_result.value()
    # Use camera safely
```

**DeviceCapabilitiesResult** - Device feature list

Returned by `get_device_capabilities(device)`. When successful, contains a `DeviceCapabilities` object with lists of supported video and camera properties. When error, indicates querying failed due to device issues or permissions.

```python
caps_result = duvc.get_device_capabilities(0)
if caps_result.is_ok():
    caps = caps_result.value()
    props = caps.supported_video_properties()
```

**DeviceConnectionResult** - Connection status

Returned by future device status methods. Represents a boolean result wrapped in Result type. True means device is connected and accessible, False means disconnected. Rarely used directly; most code calls `is_device_connected(device)` which returns plain bool.

**Uint32Result** - Unsigned 32-bit integer

Returned by utility functions that query numeric device properties like property counts or firmware versions. When successful, contains uint32 value. When error, indicates the query failed.

**VectorUint8Result** - Binary data

Returned by operations that read raw device data (firmware blobs, configuration buffers). When successful, contains a list of bytes. When error, indicates the read operation failed.

**BoolResult** - Boolean result

Returned by predicate operations. When successful, contains True or False. Different semantically from DeviceConnectionResult despite having same type—context determines meaning.

#### Helper constructors for building Results

These functions create Result objects in ok or error states. Used when implementing custom error handling or writing tests that need fake Results.

**Ok_PropSetting / Err_PropSetting**:

```python
ok_result = duvc.Ok_PropSetting(duvc.PropSetting(128, 'manual'))
err_result = duvc.Err_PropSetting(duvc.Error(0x04, "Property unsupported"))
```

**Ok_PropRange / Err_PropRange**:

```python
ok_range = duvc.Ok_PropRange(duvc.PropRange(min=0, max=255, step=1, default=128, current=150))
err_range = duvc.Err_PropRange(duvc.Error(0x01, "Device not found"))
```

**Ok_void / Err_void**:

```python
ok_void = duvc.Ok_void()
err_void = duvc.Err_void(duvc.Error(0x05, "Invalid value"))
```

**Ok_bool / Err_bool**:

```python
ok_bool = duvc.Ok_bool(True)
err_bool = duvc.Err_bool(duvc.Error(0x07, "Timeout"))
```

**Ok_uint32 / Err_uint32**:

```python
ok_uint = duvc.Ok_uint32(42)
err_uint = duvc.Err_uint32(duvc.Error(0x02, "Device in use"))
```


***

### 4.4 Result Method Reference \& Error Handling

All Result types share a common interface. These methods are how you interact with Results to check success, extract values, or access errors.

#### `is_ok()` check success

Returns True if Result contains a value, False if contains error. This is the primary way to determine if an operation succeeded.

```python
result = camera.get(duvc.VidProp.Brightness)
if result.is_ok():
    # Operation succeeded; safe to call value()
    setting = result.value()
else:
    # Operation failed; safe to call error()
    error = result.error()
```

Always check `is_ok()` before calling `value()` to avoid exceptions.

#### `is_error()` check failure

Returns True if Result contains an error, False if contains a value. Opposite of `is_ok()`. Some developers prefer using this for early-exit error handling patterns.

```python
result = camera.set(duvc.VidProp.Brightness, setting)
if result.is_error():
    print(f"Failed: {result.error().description()}")
    return

# Continue on success
print("Set succeeded")
```


#### `value()` extract successful value

Returns the contained value (PropSetting, PropRange, Camera, DeviceCapabilities, etc.). Type depends on which Result specialization you're using. Only valid when `is_ok()` is true. Raises RuntimeError if called on error Result.

```python
result = camera.get(duvc.VidProp.Brightness)

# ✓ Correct: always check first
if result.is_ok():
    setting = result.value()
    print(setting.value)

# ✗ Wrong: crashes if error
setting = result.value()  # Raises RuntimeError!
```


#### `error()` extract error information

Returns an `Error` object containing error details. Only valid when `is_error()` is true. The Error object has methods:

- `code()`: Returns integer error code (0x01-0x0A).
- `description()`: Returns human-readable error message.
- `recoverable()`: Returns boolean—true if retrying might succeed.

```python
result = camera.get(duvc.VidProp.Brightness)

if result.is_error():
    error = result.error()
    print(f"Error {error.code():02x}: {error.description()}")
    
    if error.recoverable():
        print("This error may resolve after reconnect")
```


#### `value_or(default)` fallback extraction

Returns the successful value if ok, or the default value if error. Never raises exceptions. Enables graceful degradation.

```python
# Get brightness with fallback to 128
result = camera.get(duvc.VidProp.Brightness)
setting = result.value_or(duvc.PropSetting(128, 'manual'))
print(f"Brightness: {setting.value}")  # Always works
```

Useful in loops where some properties might not exist:

```python
for prop in [duvc.VidProp.Brightness, duvc.VidProp.Pan, duvc.VidProp.CustomProp]:
    result = camera.get(prop)
    setting = result.value_or(duvc.PropSetting(0, 'manual'))
    print(f"{prop}: {setting.value}")  # Never crashes
```


#### `__bool__()` result in if statements

Result evaluates to True in boolean context if ok, False if error. Shorthand for `is_ok()`.

```python
if camera.set(duvc.VidProp.Brightness, setting):
    print("Set succeeded")
else:
    print("Set failed")

# Equivalent to:
if camera.set(duvc.VidProp.Brightness, setting).is_ok():
    ...
```

Enables concise property support checks:

```python
# Check if property exists on device
if camera.get(duvc.VidProp.Brightness):
    print("Device supports brightness")
else:
    print("Device doesn't support brightness")
```


#### Error codes and exception conversion

Error results contain error codes. Common codes are `ERR_DEVICE_NOT_FOUND` (0x01), `ERR_DEVICE_IN_USE` (0x02), `ERR_PROPERTY_NOT_SUPPORTED` (0x04), `ERR_INVALID_VALUE` (0x05), `ERR_PERMISSION_DENIED` (0x06), `ERR_TIMEOUT` (0x07), `ERR_HARDWARE_ERROR` (0x08), `ERR_COMMUNICATION_ERROR` (0x09), `ERR_ALREADY_CONNECTED` (0x0A).

To convert Result errors to exceptions (for integration with exception-based code):

```python
def result_to_exception(result):
    """Convert Result error to exception."""
    if result.is_ok():
        return result.value()
    
    error = result.error()
    code = error.code()
    
    if code == 0x01:
        raise duvc.DeviceNotFoundError(error.description())
    elif code == 0x04:
        raise duvc.PropertyNotSupportedError(error.description())
    elif code == 0x06:
        raise duvc.PermissionError(error.description())
    else:
        raise duvc.ErrorInfo(error.description())
```


#### Error description access and formatting

Extract error information for logging or display.

```python
result = camera.get(duvc.VidProp.Brightness)
if result.is_error():
    error = result.error()
    code = error.code()
    msg = error.description()
    recoverable = error.recoverable()
    
    print(f"[Error {code:02x}] {msg}")
    if recoverable:
        print("[Tip] Try reconnecting the camera")
```

For structured logging of all Results:

```python
class OperationResult:
    def __init__(self, result, operation: str):
        self.operation = operation
        self.success = result.is_ok()
        if result.is_ok():
            self.value = result.value()
        else:
            error = result.error()
            self.error_code = error.code()
            self.error_msg = error.description()
            self.recoverable = error.recoverable()
    
    def __str__(self):
        if self.success:
            return f"{self.operation}: OK"
        else:
            recov = "(may retry)" if self.recoverable else "(permanent)"
            return f"{self.operation}: FAILED - {self.error_msg} {recov}"

# Usage
result = camera.set(duvc.VidProp.Brightness, setting)
report = OperationResult(result, "Set brightness")
print(report)
```

### 4.5 Device Capabilities \& Property Analysis

The DeviceCapabilities object represents what properties and features a device supports. Query capabilities before attempting to access properties so you know what's available and avoid unnecessary errors.

#### `get_device_capabilities()` entry point

Entry point for querying what a device can do. Returns `Result[DeviceCapabilities]`. Call this before opening a camera to determine which properties are worth trying to read or write.

```python
caps_result = duvc.get_device_capabilities(0)
if caps_result.is_ok():
    caps = caps_result.value()
    # Now you can query what this device supports
```

Does not require the device to be open—queries happen at the device enumeration level. This means you can check capabilities before committing to an exclusive connection.

#### DeviceCapabilities object structure

Capabilities object contains lists of what the device supports. It's a container for property support information with methods for checking and listing supported features.

**Internal fields** (don't access directly):

- Device reference: which device these capabilities describe
- Video property list: all supported video properties (brightness, contrast, saturation, etc.)
- Camera property list: all supported camera properties (pan, tilt, zoom, etc.)

Access this data only through the methods below.

#### `get_camera_capability(CamProp)` individual camera property details

Query details about a specific camera property. Returns `Result[PropertyCapability]` containing min/max/default/mode info for that one property.

```python
cap_result = caps.get_camera_capability(duvc.CamProp.Pan)
if cap_result.is_ok():
    prop_cap = cap_result.value()
    print(f"Pan range: {prop_cap.min} to {prop_cap.max}")
```

Useful when you know the device has a property but need to know its exact constraints before using it.

#### `get_video_capability(VidProp)` individual video property details

Query details about a specific video property. Returns `Result[PropertyCapability]` with same structure as camera properties.

```python
cap_result = caps.get_video_capability(duvc.VidProp.Brightness)
if cap_result.is_ok():
    prop_cap = cap_result.value()
```


#### `supports_camera_property(CamProp)` check camera property support

Returns boolean: True if device supports this camera property, False if not. Quick predicate for existence checks.

```python
if caps.supports_camera_property(duvc.CamProp.Pan):
    print("Device supports pan")
else:
    print("No pan on this device")
```

Use this to skip operations you know the device can't do.

#### `supports_video_property(VidProp)` check video property support

Returns boolean: True if device supports this video property, False if not.

```python
if caps.supports_video_property(duvc.VidProp.Brightness):
    # Safe to read/write brightness
    pass
```


#### `supported_camera_properties()` list all camera properties

Returns list of all camera properties this device supports (may be empty if device has no pan/tilt/zoom).

```python
props = caps.supported_camera_properties()
print(f"This device supports: {[duvc.to_string(p) for p in props]}")

for prop in props:
    print(f"  - {duvc.to_string(prop)}")
```

Iteration order is arbitrary; don't assume any particular order.

#### `supported_video_properties()` list all video properties

Returns list of all video properties this device supports (brightness, contrast, saturation, etc.).

```python
props = caps.supported_video_properties()
print(f"Supported {len(props)} video properties")
```


#### `device()` property accessor

Returns the Device object these capabilities describe. Useful when you're working with multiple devices and need to track which device a capabilities object refers to.

```python
device = caps.device()
print(f"These capabilities are for: {device.name}")
```


#### `is_device_accessible()` check device availability

Returns boolean: True if the device is still connected and accessible. False if disconnected or removed since capabilities were queried.

```python
if caps.is_device_accessible():
    # Safe to use these capabilities
    pass
else:
    print("Device was disconnected")
```


#### `refresh()` re-query device capabilities

Re-queries the device to get updated capability information. Use this if you suspect the device state changed (e.g., after reconnection or firmware update).

Returns `Result[void]`: ok if refresh succeeded, error if device unreachable.

```python
refresh_result = caps.refresh()
if refresh_result.is_ok():
    print("Capabilities updated")
    # Now use caps object again with fresh data
else:
    print("Device unreachable; capabilities may be stale")
```


#### Iterator protocol `__iter__()` \& `__len__()`

Enables Python iteration over supported properties. Supports both video and camera properties depending on context.

```python
caps_result = duvc.get_device_capabilities(0)
if caps_result.is_ok():
    caps = caps_result.value()
    
    # Iteration works on video properties
    for prop in caps.supported_video_properties():
        print(duvc.to_string(prop))
    
    # Get count
    video_count = len(caps.supported_video_properties())
    camera_count = len(caps.supported_camera_properties())
```

Enables `for prop in caps` style loops when context is clear.

#### String representation `__str__()` \& `__repr__()`

`__str__()` returns human-readable summary for printing.

```python
print(caps)
# Output: <DeviceCapabilities: 15 video properties, 3 camera properties>
```

`__repr__()` returns technical representation for debugging.

```python
repr(caps)
# Output: DeviceCapabilities(device=Device(...), video_count=15, camera_count=3)
```

Use in logging to inspect capabilities state.

