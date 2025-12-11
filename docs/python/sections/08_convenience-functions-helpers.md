## 8. Convenience Functions & Helpers


### 8.1 Device Discovery \& Management

Core functions for discovering, enumerating, and identifying camera devices on the system.

***

#### list_devices() - enumerate all cameras

Returns list of all camera devices recognized by DirectShow. Primary discovery function.

```python
def list_devices() -> list[Device]:
    """Get list of available camera devices."""
```

**Returns**: List of `Device` objects with `name`, `path`, and `is_valid()` method.

**Usage**:

```python
devices = duvc.list_devices()
print(f"Found {len(devices)} camera(s)")
for dev in devices:
    print(f"  {dev.name} - {dev.path}")
```


***

#### devices() - alias for list_devices()

Recommended shorter alias for `list_devices()`. Preferred for cleaner code.

```python
def devices() -> list[Device]:
    """Get list of available camera devices (alias)."""
```

**Usage**:

```python
# Preferred
for dev in duvc.devices():
    print(dev.name)

# Equivalent to
for dev in duvc.list_devices():
    print(dev.name)
```


***

#### find_device_by_name() - search by name substring

Find first device matching case-insensitive substring search. Raises exception if not found.

```python
def find_device_by_name(
    name: str,
    devices_list: list[Device] | None = None
) -> Device:
    """
    Find first device with name containing search string.
    
    Args:
        name: Search string (case-insensitive)
        devices_list: Optional pre-fetched device list (avoids re-enumeration)
    
    Returns:
        Device if found
        
    Raises:
        DeviceNotFoundError: If no matching device found
    """
```

**Usage**:

```python
# Find by substring
try:
    logitech = duvc.find_device_by_name("Logitech")
    print(f"Found: {logitech.name}")
except duvc.DeviceNotFoundError as e:
    print(f"Not found: {e}")

# Reuse enumeration
device_list = duvc.devices()
cam1 = duvc.find_device_by_name("USB", device_list)
cam2 = duvc.find_device_by_name("HD", device_list)  # No re-enumeration
```


***

#### find_devices_by_name() - search all matches

Find all devices matching case-insensitive substring. Returns empty list if none found (never raises).

```python
def find_devices_by_name(
    name: str,
    devices_list: list[Device] | None = None
) -> list[Device]:
    """
    Find all devices with name containing search string.
    
    Args:
        name: Search string (case-insensitive)
        devices_list: Optional pre-fetched device list
    
    Returns:
        List of matching devices (empty if none found)
    """
```

**Usage**:

```python
# Find all USB cameras
usb_cameras = duvc.find_devices_by_name("USB")
print(f"Found {len(usb_cameras)} USB camera(s)")
for cam in usb_cameras:
    print(f"  {cam.name}")

# Find all Logitech devices
logitechs = duvc.find_devices_by_name("logitech")
if not logitechs:
    print("No Logitech cameras found")
```


***

#### find_device_by_path() - lookup by Windows device path

Find device by Windows device path. Case-insensitive matching. Useful for reliably reconnecting to a specific camera across application restarts.

```python
def find_device_by_path(path: str) -> Device:
    """
    Find device by Windows device path.
    
    Args:
        path: Windows device path (case-insensitive, e.g., "\\?\\USB#VID_046D&PID_082D...")
        
    Returns:
        Device if found
        
    Raises:
        Exception: If path not found or invalid (generalized exception for broad error handling)
    """
```

**Usage**:

```python
import duvc_ctl as duvc

# Save device path on first run
devices = duvc.list_devices()
if devices:
    saved_path = devices[0].path
    print(f"Device path: {saved_path}")

# Later session - reconnect using saved path
try:
    device = duvc.find_device_by_path(saved_path)
    print(f"Reconnected to: {device.name}")
except Exception as e:
    print(f"Device not found at path: {e}")

# Case-insensitive - these are equivalent
device1 = duvc.find_device_by_path(saved_path)
device2 = duvc.find_device_by_path(saved_path.upper())
device3 = duvc.find_device_by_path(saved_path.lower())
```

**Multi-camera scenario** - maintain stable device references:

```python
import duvc_ctl as duvc
import json

# Discovery and save
camera_map = {}
for dev in duvc.list_devices():
    camera_map[dev.name] = dev.path

# Save to file for next run
with open("camera_paths.json", "w") as f:
    json.dump(camera_map, f)

# Later - reconnect all
loaded_paths = json.load(open("camera_paths.json"))
for name, path in loaded_paths.items():
    try:
        device = duvc.find_device_by_path(path)
        camera = duvc.CameraController(device=device)
        print(f"✅ Connected: {camera.device_name}")
    except Exception:
        print(f"❌ {name} not found at {path}")
```

**Path format**: Windows device paths follow the pattern `\\?\\USB#VID_XXXX&PID_XXXX#SERIAL...`. These are stable identifiers that persist across sessions.


#### iter_devices() - lazy device iteration

Generator yielding devices one at a time. Memory-efficient for large device counts.

```python
def iter_devices() -> Generator[Device, None, None]:
    """Yield available video devices one at a time."""
```

**Usage**:

```python
# Iterate without loading all into memory
for device in duvc.iter_devices():
    print(device.name)
    if device.name == "Target":
        break  # Stop early if found

# First device only
first_device = next(duvc.iter_devices(), None)
if first_device:
    print(f"First camera: {first_device.name}")
```


***

#### iter_connected_devices() - filter connected only

Generator yielding only devices that are currently connected and accessible. Filters disconnected/stale devices.

```python
def iter_connected_devices() -> Generator[Device, None, None]:
    """Yield only connected devices."""
```

**Usage**:

```python
# Only connected cameras
for device in duvc.iter_connected_devices():
    print(f"Connected: {device.name}")
    try:
        camera = duvc.Camera(device)
        # Use camera
    except duvc.DeviceNotFoundError:
        print(f"Device {device.name} became unavailable")
```


***

#### list_cameras() - Pythonic device listing

Alias for device enumeration in CameraController context. Returns same as `list_devices()`.

```python
def list_cameras() -> list[Device]:
    """Get list of available cameras (Pythonic API alias)."""
```

**Usage**:

```python
# CameraController context
cameras = duvc.list_cameras()
for cam_device in cameras:
    camera = duvc.CameraController(cam_device)
    print(f"{camera.name}: brightness={camera.brightness}")
```


***

#### find_camera() - find and open camera

Find device by substring and return opened `CameraController`. Combines find + open.

```python
def find_camera(name: str) -> CameraController:
    """
    Find and open camera by name substring.
    
    Args:
        name: Search string (case-insensitive)
        
    Returns:
        Opened CameraController instance
        
    Raises:
        DeviceNotFoundError: If no matching device found
        DeviceBusyError: If device in use
    """
```

**Usage**:

```python
# One-step find and open
try:
    camera = duvc.find_camera("Logitech")
    print(f"Opened: {camera.name}")
    camera.set_brightness(150)
except duvc.DeviceNotFoundError:
    print("Camera not found")
except duvc.DeviceBusyError:
    print("Camera in use")
```


***

#### get_device_info() - comprehensive device analysis

Query all device properties, capabilities, and current values. Non-throwing: returns error details for failed properties.

```python
def get_device_info(device: Device) -> DeviceInfo:
    """
    Collect property metadata for a device.
    
    Queries device capabilities and reads all property values, ranges,
    and current settings. Failed property reads are captured with error
    details rather than raising exceptions.
    
    Args:
        device: Target device
        
    Returns:
        DeviceInfo dict with:
            - name: str
            - path: str
            - connected: bool
            - camera_properties: dict[str, PropertyInfo]
            - video_properties: dict[str, PropertyInfo]
            - error: str | None
    """
```

**Usage**:

```python
device = duvc.devices()[^0]
info = duvc.get_device_info(device)

print(f"Device: {info['name']}")
print(f"Connected: {info['connected']}")

# Inspect properties
for prop_name, prop_info in info['camera_properties'].items():
    if prop_info['supported']:
        current = prop_info['current']
        range_info = prop_info['range']
        print(f"{prop_name}: {current['value']} ({range_info['min']}-{range_info['max']})")
    else:
        print(f"{prop_name}: Not supported - {prop_info['error']}")

# Video properties
for prop_name, prop_info in info['video_properties'].items():
    if prop_info['supported']:
        print(f"{prop_name}: {prop_info['current']['value']}")
```


***

#### get_camera_info() - alias for get_device_info()

Pythonic alias for `get_device_info()`. Identical functionality.

```python
def get_camera_info(device: Device) -> DeviceInfo:
    """Alias for get_device_info() (Pythonic API)."""
```


***

#### Device support matrix reference

Different cameras support different property sets. Query before use to avoid exceptions.

**Common property support patterns**:


| Camera Type | Pan/Tilt | Zoom | Focus | Exposure | WhiteBalance | Brightness |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| Webcam (basic) | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| HD Webcam | ❌ | ✅ | ✅ (digital) | ✅ | ✅ | ✅ |
| PTZ Camera | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Conference Cam | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Security Cam | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |

**Usage pattern**:

```python
# Query capabilities before use
device = duvc.devices()[^0]
info = duvc.get_device_info(device)

# Check if property supported
if info['camera_properties']['Pan']['supported']:
    camera = duvc.CameraController(device)
    camera.set_pan(45)
else:
    print("Pan not supported on this device")

# Batch capability check
supported_props = [
    name for name, prop_info in info['video_properties'].items()
    if prop_info['supported']
]
print(f"Supported video properties: {supported_props}")
```

### 8.2 Device Context Managers

Context managers for automatic device cleanup and safe resource management. Two levels: `DeviceContextManager` for direct core `Camera` access, and context-aware properties on `CameraController`.

***

#### DeviceContextManager class

Wraps core `Camera` for automatic cleanup via `with` statement. Direct access to low-level Result types.

**Methods**:

- `__enter__()` – Opens device, returns core `Camera` object.
- `__exit__(exctype, excval, exctb)` – Closes device, releases resources.
- `is_closed` (property) – Check if context has been closed.

**Usage**:

```python
from duvc_ctl import open_device_context

device = duvc.devices()[^0]

# Automatic cleanup with context manager
with duvc.open_device_context(device) as camera:
    result = camera.get(duvc.VidProp.Brightness)
    if result.is_ok():
        print(f"Brightness: {result.value().value}")
    # Camera auto-closed on exit, even if exception occurs

# Camera is now closed; further operations fail
```

**Exception handling**:

```python
device = duvc.devices()[^0]

try:
    with duvc.open_device_context(device) as camera:
        # Operations here
        result = camera.get(duvc.VidProp.Contrast)
        if not result.is_ok():
            raise Exception(result.error().description())
except RuntimeError as e:
    if "already open" in str(e):
        print("Device already in use")
    else:
        raise
# Camera is properly closed even if exception raised
```


***

#### open_device_context() - device context factory

Creates `DeviceContextManager` for a specific device. Low-level control with explicit cleanup.

```python
def open_device_context(device: Device) -> DeviceContextManager:
    """
    Create context manager for direct core Camera access.
    
    Args:
        device: Device to connect to
        
    Returns:
        Context manager yielding core Camera object
        
    Raises:
        RuntimeError: If device cannot be opened
    """
```

**Usage**:

```python
device = duvc.devices()[^0]

# Single operation with automatic cleanup
with duvc.open_device_context(device) as camera:
    brightness = camera.get(duvc.VidProp.Brightness)
    camera.set(duvc.VidProp.Brightness, duvc.PropSetting(150))

# Multiple operations with same camera
with duvc.open_device_context(device) as camera:
    for prop in [duvc.VidProp.Brightness, duvc.VidProp.Contrast]:
        result = camera.get(prop)
        if result.is_ok():
            print(f"{prop}: {result.value().value}")
```


***

#### open_device_by_name_context() - named device context

Finds device by name substring, then opens as context manager. Combines discovery + opening in one call.

```python
def open_device_by_name_context(device_name: str) -> DeviceContextManager:
    """
    Create context manager for device access by name.
    
    Args:
        device_name: Device name or partial match (case-insensitive)
        
    Returns:
        Context manager yielding core Camera object
        
    Raises:
        DeviceNotFoundError: If no matching device found
        RuntimeError: If device cannot be opened
    """
```

**Usage**:

```python
# Find by substring and open automatically
try:
    with duvc.open_device_by_name_context("Logitech") as camera:
        brightness = camera.get(duvc.VidProp.Brightness)
        print(f"Brightness: {brightness.value().value}")
except duvc.DeviceNotFoundError:
    print("Logitech camera not found")
```


***

#### Case-insensitive substring matching

Both context managers and discovery functions use **case-insensitive** substring matching for device names. Allows flexible search without exact names.

**Matching behavior**:

```python
# Device actual name: "Logitech USB HD Webcam"

# All these match:
duvc.open_device_by_name_context("logitech")  # ✓ Substring
duvc.open_device_by_name_context("LOGITECH")  # ✓ Case insensitive
duvc.open_device_by_name_context("usb hd")    # ✓ Substring
duvc.open_device_by_name_context("webcam")    # ✓ Suffix match
duvc.open_device_by_name_context("HD Web")    # ✓ Non-consecutive substring

# These don't match:
duvc.open_device_by_name_context("Sony")      # ✗ Different device
duvc.open_device_by_name_context("cam2")      # ✗ Not substring
```

**Matching is done with**:

```python
if search_string.lower() in device_name.lower():
    # Match found
```

**Multi-device scenarios**:

```python
# Device list:
# [^0] "Logitech USB HD Webcam"
# [^1] "Logitech C920"
# [^2] "Built-in Camera"

# Search returns FIRST match
with duvc.open_device_by_name_context("Logitech") as camera:
    # Opens device [^0] "Logitech USB HD Webcam"
    pass

# Be specific to target single device
with duvc.open_device_by_name_context("C920") as camera:
    # Opens device [^1] "Logitech C920"
    pass

# Find all matches first, then open
cameras = duvc.find_devices_by_name("Logitech")
for device in cameras:
    with duvc.open_device_context(device) as camera:
        print(device.name)
```

**CameraController also uses substring matching**:

```python
# Pythonic API with automatic matching
camera = duvc.CameraController(device_name="Logitech")
# Finds first device containing "logitech" (case-insensitive)

# Also works with device index
camera = duvc.CameraController(device_index=0)
# Opens first device by index
```

### 8.3 Property \& Connection Helpers

Utility functions for safe property operations, connection verification, and batch management.

***

#### reset_device_to_defaults() - restore factory settings

Reset all device properties to their default values. Queries property ranges for defaults, then sets each. Individual failures don't stop remaining properties.

```python
def reset_device_to_defaults(device: Device) -> dict[str, bool]:
    """
    Reset all supported properties to device defaults.
    
    Args:
        device: Target device
        
    Returns:
        Dict mapping property names (e.g., "Brightness", "Contrast") to success status
    """
```

**Usage**:

```python
device = duvc.devices()[^0]

# Restore all to defaults
results = duvc.reset_device_to_defaults(device)

# Check which reset successfully
for prop_name, success in results.items():
    status = "✓" if success else "✗"
    print(f"{status} {prop_name}")

# Track failed properties
failed = {name for name, success in results.items() if not success}
if failed:
    print(f"Failed to reset: {failed}")
```


***

#### get_supported_properties() - capability query

Query all supported camera and video properties for a device. Non-throwing: captures errors.

```python
def get_supported_properties(device: Device) -> dict[str, list[str]]:
    """
    Get lists of supported properties.
    
    Args:
        device: Target device
        
    Returns:
        Dict with keys:
            - "camera": List of supported camera property names
            - "video": List of supported video property names
    """
```

**Usage**:

```python
device = duvc.devices()[^0]
supported = duvc.get_supported_properties(device)

print("Camera properties:")
for prop in supported["camera"]:
    print(f"  - {prop}")

print("Video properties:")
for prop in supported["video"]:
    print(f"  - {prop}")

# Filter before operations
if "Pan" in supported["camera"]:
    camera = duvc.CameraController(device)
    camera.set_pan(45)
else:
    print("Pan not supported")
```


***

#### set_property_safe() - error-free property setting

Set property with validation and error capture. Returns status + error message without raising. Type-safe enum checking.

```python
def set_property_safe(
    device: Device,
    domain: str,
    property_enum: CamProp | VidProp,
    value: int,
    mode: str = "manual"
) -> tuple[bool, str]:
    """
    Set property with validation and error reporting.
    
    Args:
        device: Target device
        domain: "cam" or "vid" (case-insensitive)
        property_enum: CamProp or VidProp enum
        value: Property value
        mode: "auto" or "manual" (default)
        
    Returns:
        (success: bool, error_message: str)
        error_message is empty if successful
    """
```

**Usage**:

```python
device = duvc.devices()[^0]

# Safe property set (no exceptions)
success, error = duvc.set_property_safe(
    device,
    "vid",
    duvc.VidProp.Brightness,
    150,
    mode="manual"
)

if success:
    print("Brightness set successfully")
else:
    print(f"Failed: {error}")
    # Handle gracefully

# Batch safe sets
props_to_set = [
    ("vid", duvc.VidProp.Brightness, 100),
    ("vid", duvc.VidProp.Contrast, 80),
    ("cam", duvc.CamProp.Pan, 45),
]

for domain, prop_enum, value in props_to_set:
    success, error = duvc.set_property_safe(device, domain, prop_enum, value)
    if not success:
        print(f"Skipping {prop_enum}: {error}")
```


***

#### get_property_safe() - error-free property reading

Get property with validation and error capture. Returns status + value + error message. No exceptions.

```python
def get_property_safe(
    device: Device,
    domain: str,
    property_enum: CamProp | VidProp
) -> tuple[bool, PropSetting | None, str]:
    """
    Get property with validation and error reporting.
    
    Args:
        device: Target device
        domain: "cam" or "vid" (case-insensitive)
        property_enum: CamProp or VidProp enum
        
    Returns:
        (success: bool, setting: PropSetting | None, error_message: str)
        error_message is empty if successful
    """
```

**Usage**:

```python
device = duvc.devices()[^0]

# Safe property read (no exceptions)
success, setting, error = duvc.get_property_safe(
    device,
    "vid",
    duvc.VidProp.Brightness
)

if success:
    print(f"Brightness: {setting.value} (mode: {setting.mode})")
else:
    print(f"Failed to read: {error}")

# Batch safe reads
props_to_read = [
    ("vid", duvc.VidProp.Brightness),
    ("vid", duvc.VidProp.Contrast),
    ("cam", duvc.CamProp.Pan),
]

current_state = {}
for domain, prop_enum in props_to_read:
    success, setting, error = duvc.get_property_safe(device, domain, prop_enum)
    if success:
        current_state[str(prop_enum)] = setting.value
    else:
        print(f"Skipping read: {error}")
```


***

#### is_device_connected() - connection status check

Check if device is currently accessible and connected. Non-throwing: returns bool.

```python
def is_device_connected(device: Device) -> bool:
    """
    Check if device is currently connected and accessible.
    
    Args:
        device: Target device
        
    Returns:
        True if device accessible, False if disconnected or inaccessible
    """
```

**Usage**:

```python
device = duvc.devices()[^0]

if duvc.is_device_connected(device):
    print(f"{device.name} is connected")
    camera = duvc.CameraController(device)
else:
    print(f"{device.name} is disconnected")
    # Try to find alternative or reconnect

# Connection monitoring
for device in duvc.devices():
    status = "✓" if duvc.is_device_connected(device) else "✗"
    print(f"{status} {device.name}")

# Retry pattern
def get_with_retry(device, prop, retries=3):
    for attempt in range(retries):
        if not duvc.is_device_connected(device):
            print(f"Attempt {attempt+1}: Device disconnected")
            time.sleep(1)
            continue
        
        try:
            camera = duvc.CameraController(device)
            return camera.get(prop)
        except duvc.DuvcError as e:
            if attempt < retries - 1:
                time.sleep(1)
    return None
```


***

### 8.4 Logging Setup \& Utilities

Configure logging level, enable debug output, and set callback handlers for library events.

***

#### setup_logging() - configure log level and callback

Set log level and optional callback for all library log messages. Callback receives (level, message).

```python
def setup_logging(
    level: LogLevel = LogLevel.Info,
    callback: Callable[[LogLevel, str], None] | None = None
) -> None:
    """
    Configure library logging.
    
    Args:
        level: Minimum log level to capture (default: Info)
        callback: Optional function(level, message) called for each log event
    """
```

**LogLevel values**: Debug, Info, Warning, Error, Critical

**Usage**:

```python
import duvc_ctl as duvc

# Set level without callback
duvc.setup_logging(duvc.LogLevel.Debug)

# With custom callback
def my_log_handler(level, message):
    level_name = duvc.to_string(level)
    timestamp = datetime.datetime.now().isoformat()
    print(f"[{timestamp}] {level_name}: {message}")

duvc.setup_logging(duvc.LogLevel.Debug, my_log_handler)

# Log to file
log_file = open("duvc.log", "a")

def file_log_handler(level, message):
    level_name = duvc.to_string(level)
    log_file.write(f"{level_name}: {message}\n")
    log_file.flush()

duvc.setup_logging(duvc.LogLevel.Info, file_log_handler)

# Operations now logged
camera = duvc.CameraController(0)
camera.set_brightness(150)  # Triggers log messages
```


***

#### enable_debug_logging() - quick debug output

Enable debug-level logging with console output. Convenience function for quick diagnostics.

```python
def enable_debug_logging() -> None:
    """
    Enable debug-level logging to console.
    Equivalent to setup_logging(LogLevel.Debug, print_handler)
    """
```

**Usage**:

```python
import duvc_ctl as duvc

# Single call for debugging
duvc.enable_debug_logging()

# Now see all debug output
devices = duvc.list_devices()  # Logs device enumeration
camera = duvc.CameraController(0)  # Logs open operation
camera.set_brightness(150)  # Logs property operations

# Output example:
# [DEBUG] Enumerating DirectShow devices
# [DEBUG] Found 2 camera(s)
# [DEBUG] Opening device "Logitech USB HD Webcam"
# [DEBUG] Device opened successfully
# [DEBUG] Setting property: Brightness = 150
```

**Typical debug output categories**:


| Category | When | Example |
| :-- | :-- | :-- |
| Device Enumeration | `list_devices()` | "Found N camera(s)", "Device: name" |
| Device Open/Close | Camera creation | "Opening device", "Device opened/closed" |
| Property Operations | `get/set_brightness()` | "Getting Brightness", "Set Brightness = 150" |
| Capabilities Query | `get_capabilities()` | "Querying capabilities", "Supported properties: ..." |
| Mode Changes | Property mode changes | "Setting auto mode", "Switching to manual" |
| Errors | Failures | "Failed to open: Permission denied", "Device disconnected" |

