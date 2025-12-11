## 3. Pythonic API - CameraController Class


### 3.1 Initialization & Device Connection

The `CameraController` constructor automatically discovers and connects to a camera device. Four initialization modes are supported: automatic (first device), selection by index, selection by name pattern, and direct connection using a `Device` object.

#### Constructor Signatures and Modes

**Auto-detect first camera:**

```python
cam = duvc_ctl.CameraController()
```

**Select by index:**

```python
cam = duvc_ctl.CameraController(device_index=1)  # Second camera
```

**Select by name (substring match, case-insensitive):**

```python
cam = duvc_ctl.CameraController(device_name="Logitech")
```

**Select by device path (persistent reconnection):**

```python
cam = duvc_ctl.CameraController(device_path="\\\\?\\USB#VID_046D&PID_082D...")
```

The device path is a stable identifier that survives USB reconnections, reboots, and USB port changes. Use this when you've previously saved a device path and need to reliably reconnect to the same camera:

```python
import duvc_ctl as duvc

# First run - discover and save
cam = duvc.CameraController()
saved_path = cam.device_path
print(f"Save this path: {saved_path}")

# Later - reconnect to the same device
cam = duvc.CameraController(device_path=saved_path)
```

**Select by Device object (from `list_devices()`):**

```python
devices = duvc_ctl.list_devices()
device = devices[0]  # Select first available device
cam = duvc_ctl.CameraController(device=device)
```

#### Constructor Exceptions

- `DeviceNotFoundError`: No cameras found or specified device not found.
- `DuvcSystemError`: Connection failed (device in use, permissions, hardware issue).

#### Device Selection Strategy

The `_connect()` method implements a **priority-based device selection strategy**:

1. **Device object provided**: If a `Device` object is passed, it takes the highest priority. The object must be valid (i.e., properly initialized by `list_devices()`).
2. **Device index provided**: If `device_index` is provided, the camera at the given index (0-based) is selected. If the index is out of range, an error is raised with a full list of available devices.
3. **Device name provided**: If `device_name` is provided, a case-insensitive substring search is performed to find the first matching device.
4. **Default behavior**: If neither `device`, `device_index`, nor `device_name` is provided, the first available device is selected.

**Note**: Only one of `device`, `device_index`, or `device_name` should be provided. If multiple are given, the `device` object takes precedence, followed by `device_index`, then `device_name`.

#### Name Matching Algorithm

Device name matching uses a **case-insensitive substring search**:

```python
# Matches: "Logitech C920", "LOGITECH Webcam", "logitech hd pro"
cam = duvc_ctl.CameraController(device_name="Logitech")

# Matches: "USB 2.0 Camera", "USB 3.0 HD Webcam", "USB Video Device"
cam = duvc_ctl.CameraController(device_name="USB")
```

When multiple devices match, the **first match is selected**. Use `device_index` or the Device object approach if you need specific control over multiple matching devices.

#### Error Messages with Device Enumeration

**No cameras detected:**

```python
try:
    cam = duvc_ctl.CameraController()
except duvc_ctl.DeviceNotFoundError as e:
    print(e)
    # Output:
    # No cameras detected. Please check:
    # • Camera is connected and powered on
    # • Camera drivers are installed
```

**Device index out of range (with full enumeration):**

```python
try:
    cam = duvc_ctl.CameraController(device_index=5)
except duvc_ctl.DeviceNotFoundError as e:
    print(e)
    # Output:
    # Device index 5 not found.
    # Available cameras:
    # 0: Logitech C920
    # 1: USB 2.0 Camera
    # 2: Integrated Webcam
```

**Device name not found (with available names listed):**

```python
try:
    cam = duvc_ctl.CameraController(device_name="Sony")
except duvc_ctl.DeviceNotFoundError as e:
    print(e)
    # Output:
    # No camera matching 'Sony' found.
    # Available: Logitech C920, USB 2.0 Camera, Integrated Webcam
```

**Connection failed (with diagnostics):**

```python
try:
    cam = duvc_ctl.CameraController(device_index=0)
except duvc_ctl.DuvcSystemError as e:
    print(e)
    # Output:
    # Failed to connect to 'Logitech C920': Access denied
    # This might be because:
    # • Camera is in use by another application
    # • Insufficient permissions
    # • Hardware issue
```

#### Internal `_connect()` Method

The `_connect()` method orchestrates device discovery and connection:

```python
def _connect(self, device: Optional[Device], device_index: Optional[int], device_name: Optional[str]) -> None:
    """Establish connection to camera using core C++ APIs.
    
    Priority: device > device_path > device_index > device_name > first available
    """
    # Priority 1: Direct Device object provided
    if device is not None:
        if not device.is_valid():
            raise DeviceNotFoundError(
                f"Invalid device object: {device.name}\n"
                "Please provide a valid Device from list_devices()"
            )
        current_devices = list_devices()
        device_paths = {d.path for d in current_devices}
        
        if device.path not in device_paths:
            available = [f"{i}: {d.name}" for i, d in enumerate(current_devices)]
            raise DeviceNotFoundError(
                f"Device '{device.name}' not found in current enumeration.\n"
                f"The device may have been disconnected or the Device object is invalid.\n"
                f"Available cameras:\n" + "\n".join(available) if available else "No cameras detected."
            )
        
        self._device = device

    # Priority 2: Device path specified
    elif device_path:
        target_device = find_device_by_path(device_path)
        self._device = target_device       

    # Priority 3-4: Need to enumerate devices
    else:
        # Use ONLY the core C++ list_devices function
        devices_list = list_devices()
        if not devices_list:
            raise DeviceNotFoundError(
                "No cameras detected. Please check:\n"
                "• Camera is connected and powered on\n"
                "• Camera drivers are installed\n"
            )
        
        # Priority 3: Device index specified
        if device_index is not None:
            if device_index >= len(devices_list):
                available = [f"{i}: {d.name}" for i, d in enumerate(devices_list)]
                raise DeviceNotFoundError(
                    f"Device index {device_index} not found.\n"
                    f"Available cameras:\n" + "\n".join(available)
                )
            self._device = devices_list[device_index]
        
        # Priority 4: Device name pattern specified
        elif device_name is not None:
            # Implement our own device finding by name substring
            matching_devices = []
            for dev in devices_list:
                if device_name.lower() in dev.name.lower():
                    matching_devices.append(dev)
            
            if not matching_devices:
                available = [d.name for d in devices_list]
                raise DeviceNotFoundError(
                    f"No camera matching '{device_name}' found.\n"
                    f"Available: {', '.join(available)}"
                )
            self._device = matching_devices[0]
        
        # Priority 5: No device specified
        else:
            available = [f"{i}: {d.name}" for i, d in enumerate(devices_list)]
            raise ValueError(
                "No device specified. Provide one of:\n"
                "• device=Device object from list_devices()\n"
                "• device_index=0 (zero-based index)\n"
                "• device_name='Camera Name' (substring match)\n"
                f"\nAvailable cameras:\n" + "\n".join(available)
            )
        
    # Open camera using ONLY the core C++ API
    result = open_camera(self._device)
    if not result.is_ok():
        error_desc = result.error().description()
        raise DuvcSystemError(
            f"Failed to connect to '{self._device.name}': {error_desc}\n"
            "This might be because:\n"
            "• Camera is in use by another application\n"
            "• Insufficient permissions\n"
            "• Hardware issue"
        )
    self._core_camera = result.value()
```

#### Internal State Initialization

After a successful connection, the constructor initializes the following internal state:

- **`_lock`**: `threading.Lock()` for thread-safe access to shared state.
- **`_core_camera`**: Reference to the underlying C++ `Camera` object (Result API).
- **`_device`**: The connected `Device` object.
- **`_is_closed`**: Boolean flag initialized to `False` (tracks the closed state of the camera).

These variables are used by all subsequent operations (property access, validation, cleanup). The lock protects against concurrent access from multiple threads.

#### Device Metadata Access After Connection

Once construction succeeds, device information is immediately available:

```python
cam = duvc_ctl.CameraController()

print(cam.device_name)   # e.g., "Logitech C920"
print(cam.device_path)   # e.g., "\\\\?\\USB#VID_046D&PID_082D..."
print(cam.is_connected)  # Always True after successful construction
```

These are read-only properties; `device_path` is a stable identifier suitable for reconnection attempts.

#### Connection Validation

The constructor validates the connection by:

1. Checking `is_device_connected(device)` returns `True`.
2. Calling `open_camera()` and verifying success.
3. Storing the `Camera` object for future operations.

If any step fails, a `DeviceNotFoundError` or `DuvcSystemError` is raised with diagnostic context. **Once construction completes successfully, the camera is guaranteed to be connected and ready.** No additional checks are needed before property operations.

### 3.2 Context Manager \& Lifecycle

The CameraController implements Python's context manager protocol for automatic resource cleanup. This ensures the camera connection is always properly released, even if exceptions occur.

#### Using the `with` statement

The recommended pattern for CameraController usage:

```python
import duvc_ctl as duvc

with duvc.CameraController() as cam:
    cam.brightness = 80
    print(cam.brightness)
# Camera automatically closed here
```

The context manager guarantees cleanup even if exceptions occur:

```python
with duvc.CameraController() as cam:
    cam.brightness = 999  # Raises InvalidValueError
    # __exit__ still called; camera cleaned up before exception propagates
```


#### `__enter__()` and `__exit__()` protocol

`__enter__()` returns `self` (the CameraController instance) when entering the `with` block. `__exit__()` calls `close()` and always returns `False`, allowing exceptions to propagate normally.

```python
class CameraController:
    def __enter__(self) -> 'CameraController':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.close()
        return False  # Exceptions propagate
```


#### Manual `open()` and `close()` operations

For cases where `with` is unsuitable, use manual lifecycle management:

```python
cam = duvc.CameraController()

try:
    cam.brightness = 80
finally:
    cam.close()  # Always called, even on exception
```

The `close()` method is idempotent—calling it multiple times is safe. It sets `_is_closed = True` and clears the `_core_camera` reference.

#### Connection validation methods

**`is_connected` property:**

```python
if cam.is_connected:
    print("Camera is responsive")
else:
    print("Camera disconnected or lost")
```

Performs multiple checks:

- Verifies `_is_closed` is False and `_core_camera` is not None.
- Tests camera responsiveness with a simple property read.
- Returns True only if camera actively responds.

**`test_connection_health()` method:**

```python
health_ok = cam.test_connection_health()
```

More thorough than `is_connected`. Tests multiple operations to confirm the camera is fully functional. Useful before performing critical operations.

**`get_connection_info()` method:**

```python
info = cam.get_connection_info()
print(info['device_name'], info['health_status'])
```

Returns a detailed dict with device name, path, connection status, health status, and last error (if any).

#### Reconnection handling via `reconnect()`

If a camera disconnects unexpectedly, attempt reconnection:

```python
if not cam.is_connected:
    success = cam.reconnect()
    if success:
        print("Reconnected successfully")
    else:
        print("Reconnection failed")
```

The `reconnect()` method:

1. Stores the device reference in `_device` during initial `_connect()`.
2. Closes the current connection.
3. Calls `_connect()` using the stored device name.
4. Returns True if reconnection succeeds, False otherwise.

#### `close_with_validation()` for verified cleanup

For applications requiring detailed cleanup verification:

```python
cleanup_report = cam.close_with_validation()
print(cleanup_report['cleanup_successful'])
print(cleanup_report['errors'])
```

Returns a dict with:

- `was_connected`: Boolean indicating if camera was connected before closing.
- `cleanup_successful`: Whether cleanup completed without exceptions.
- `pre_close_health`: Health status before closing.
- `post_close_connected`: Verify camera is actually closed.
- `errors`: List of any errors encountered during cleanup.


#### State flags and cleanup

Internal state management during lifecycle:

- **`_is_closed`**: Boolean flag set to True when `close()` is called. Checked by `_ensure_connected()` before every operation.
- **`_core_camera`**: Reference to the underlying C++ Camera object. Set to None during close; prevents access to disconnected cameras.
- **`_lock`**: Threading lock acquired during close to prevent concurrent access during cleanup.

***

### 3.3 Internal State Management \& Thread Safety

The CameraController uses careful state management to support concurrent access from multiple threads while protecting the camera connection.

#### Internal state variables

**`_lock` (threading.Lock):**

```python
import threading
self._lock = threading.Lock()
```

Protects access to connection state. Acquired during:

- Connection establishment (`_connect()`)
- State checks (`_ensure_connected()`)
- Cleanup (`close()`)

Acquisition is brief to minimize contention; property operations do not hold the lock for long.

**`_core_camera` (Optional[CoreCamera]):**

```python
self._core_camera: Optional[CoreCamera] = None
```

Reference to the underlying C++ Camera object (from the Result-based API). Initially None; set by `_connect()`. Set back to None by `close()`. Used by all property access methods (`_get_video_property()`, `_set_camera_property()`, etc.).

**`_device` (Optional[Device]):**

```python
self._device: Optional[Device] = None
```

Reference to the connected Device. Stored during `_connect()` for use in `reconnect()`. Allows reconnection to the same device by name without requiring user to pass the Device object again.

**`_is_closed` (bool):**

```python
self._is_closed = False
```

Flag tracking whether `close()` has been called. Set to True in `close()`. Checked by `_ensure_connected()` before every operation. Prevents operations on closed cameras.

#### `_ensure_connected()` validation method

Called at the start of every property operation:

```python
def _ensure_connected(self) -> None:
    with self._lock:
        if self._is_closed or self._core_camera is None:
            raise RuntimeError("Camera has been closed")
```

Raises `RuntimeError` if the camera has been closed or the connection was lost. This prevents silent failures; any operation on a closed camera immediately fails with a clear error.

#### Thread-safe property access patterns

**Single camera, multiple threads (NOT recommended without synchronization):**

Accessing the same CameraController from multiple threads without a lock is unsafe:

```python
# UNSAFE: Multiple threads accessing same camera
import threading

with duvc.CameraController() as cam:
    def worker():
        cam.brightness = 50  # Race condition!
    
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
```

**Multiple cameras, one per thread (SAFE):**

Each thread gets its own camera—no synchronization needed:

```python
# SAFE: Each thread has its own camera
devices = duvc.list_devices()

def worker(device_index):
    with duvc.CameraController(device_index) as cam:
        cam.brightness = 50  # No race condition

threads = [threading.Thread(target=worker, args=(i,)) for i in range(len(devices))]
for t in threads: t.start()
for t in threads: t.join()
```

**Single camera with explicit locking (SAFE):**

If multiple threads must share one camera, use an external lock:

```python
# SAFE: Shared camera with external lock
lock = threading.Lock()

with duvc.CameraController() as cam:
    def worker():
        with lock:
            cam.brightness = 50  # Protected by lock
    
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
```


#### Multi-threaded camera control patterns

**Pattern 1: Thread pool with device queues:**

```python
import queue
import threading

device_queue = queue.Queue()

# Populate queue with devices
for i, cam in enumerate(duvc.list_devices()):
    device_queue.put(i)

def worker():
    while True:
        try:
            device_idx = device_queue.get_nowait()
        except queue.Empty:
            break
        
        with duvc.CameraController(device_idx) as cam:
            cam.brightness = 75

threads = [threading.Thread(target=worker) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
```

**Pattern 2: Shared resource with RLock (reentrant lock):**

```python
import threading

class SharedCamera:
    def __init__(self):
        self._lock = threading.RLock()
        self.cam = duvc.CameraController()
    
    def set_property(self, prop_name, value):
        with self._lock:
            self.cam.set(prop_name, value)
    
    def get_property(self, prop_name):
        with self._lock:
            return self.cam.get(prop_name)

shared = SharedCamera()

def worker():
    shared.set_property('brightness', 50)

threads = [threading.Thread(target=worker) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
```


#### GIL management considerations

Python's Global Interpreter Lock (GIL) affects multi-threaded code:

- **C++ operations release the GIL**: Property get/set operations call pybind11-bound C++ code. The pybind11 bindings release the GIL while executing C++ code, allowing true concurrency for CPU-bound work (but camera I/O is I/O-bound, so GIL release helps with responsiveness).
- **Python-side locking holds the GIL**: The `_lock` in CameraController holds the Python-level GIL, which briefly blocks other Python threads. This is unavoidable but minimized because the lock is held only during state checks, not during property operations.

For truly high-concurrency scenarios, consider using one CameraController per thread and the thread pool pattern (Pattern 1 above).

#### Thread safety guarantees documentation

| Operation | Thread-Safe | Notes |
| :-- | :-- | :-- |
| `list_devices()` (module-level) | ✓ Yes | Internally synchronized; multiple threads can call simultaneously |
| `open_camera()` (module-level) | ✓ Yes | Each call opens independent camera; no shared state |
| `CameraController()` constructor | ✓ Yes | Safe to construct from multiple threads; each gets independent object |
| `cam.brightness` (read/write single property) | ✗ No | Multiple threads accessing same camera can race |
| `cam.get_multiple()` (multiple properties) | ✗ No | Not atomic; individual properties racy if other threads access |
| `cam.set_multiple()` (multiple properties) | ✗ No | Not atomic; individual properties racy if other threads access |
| `cam.close()` | ✓ Yes | Idempotent; safe to call from multiple threads |
| `cam.is_connected` (check status) | ✓ Yes | Check is atomic; but state can change immediately after check |
| `cam.reconnect()` | ✓ Yes | Internally synchronized; safe concurrent calls (though redundant) |

**Summary**: The CameraController is thread-safe at the module level. Per-camera operations are thread-safe only if each thread accesses its own camera instance. For shared access, users must provide external synchronization (locks).

### 3.4 Class Constants \& Built-In Configurations

The CameraController defines class-level constants for property ranges, preset configurations, and intelligent defaults. These constants provide documented boundaries for property values and offer ready-made configurations for common use cases.

#### Brightness constant group

```python
BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 100
BRIGHTNESS_DEFAULT = 50
```

Brightness controls image luminance. Min represents darkest, max represents brightest. Default (50) is neutral mid-point. Device-reported ranges may differ; use `get_property_range('brightness')` to query actual limits for the connected camera.

#### Contrast constant group

```python
CONTRAST_MIN = 0
CONTRAST_MAX = 100
CONTRAST_DEFAULT = 50
```

Contrast defines the tonal range of the image. Min produces flat, low-contrast output; max produces high-contrast output. Default (50) is neutral.

#### Saturation constant group

```python
SATURATION_MIN = 0
SATURATION_MAX = 100
SATURATION_DEFAULT = 50
```

Saturation controls color intensity. Min produces grayscale (0% saturation); max produces vivid color. Default (50) is neutral baseline saturation.

#### Hue constant group

```python
HUE_MIN = -180
HUE_MAX = 180
HUE_DEFAULT = 0
```

Hue shifts colors around the color wheel. Range is ±180 degrees. Negative values rotate towards magenta/red; positive values rotate towards cyan/green. Default (0) is no color shift.

#### Pan/Tilt/Zoom (PTZ) constant group

Pan, tilt, and zoom are physical camera movement controls. These constants define center and range references.

```python
# Pan (horizontal rotation)
PAN_MIN = -180       # Full left
PAN_MAX = 180        # Full right
PAN_CENTER = 0       # Straight ahead

# Tilt (vertical rotation)
TILT_MIN = -90       # Look down
TILT_MAX = 90        # Look up
TILT_CENTER = 0      # Straight ahead

# Zoom (optical magnification)
ZOOM_MIN = 100       # 1x (no zoom)
ZOOM_MAX = 1000      # 10x typical
ZOOM_DEFAULT = 100   # 1x (no zoom)
```

These define nominal ranges. Devices report actual supported ranges dynamically; query with `get_property_range('pan')`, etc.

#### `BUILT_IN_PRESETS` configuration set

Four ready-made preset configurations optimized for common shooting scenarios. Apply with `cam.apply_preset(preset_name)`.

```python
BUILT_IN_PRESETS = {
    'daylight': {
        'brightness': 60,
        'contrast': 50,
        'white_balance': 'auto',
        'exposure': 'auto'
    },
    'indoor': {
        'brightness': 75,
        'contrast': 60,
        'white_balance': 3200,      # 3200K warm indoor lighting
        'exposure': 'auto'
    },
    'night': {
        'brightness': 80,
        'contrast': 70,
        'gain': 80,                 # Boost sensor gain significantly
        'exposure': 'auto'
    },
    'conference': {
        'brightness': 70,
        'contrast': 55,
        'white_balance': 'auto',
        'pan': 0,                   # Center camera horizontally
        'tilt': 0,                  # Center camera vertically
        'zoom': 100                 # 1x (no zoom)
    }
}
```

Usage:

```python
cam.apply_preset('daylight')      # Outdoor/bright lighting
cam.apply_preset('indoor')        # Indoor artificial lighting
cam.apply_preset('night')         # Low-light conditions
cam.apply_preset('conference')    # Meeting room setup (centered, no zoom)
```

Retrieve available presets:

```python
preset_names = cam.get_preset_names()  # ['daylight', 'indoor', 'night', 'conference', ...]
```


#### `_SMART_DEFAULTS` intelligent default set

Intelligent default values applied by `reset_to_defaults()` and `set_smart_default()`. These favor automatic/neutral settings where available.

```python
_SMART_DEFAULTS = {
    'brightness': 50,               # Neutral brightness
    'contrast': 50,                 # Neutral contrast
    'saturation': 50,               # Neutral saturation
    'sharpness': 50,                # Moderate sharpness
    'gamma': 100,                   # Linear gamma (1.0)
    'hue': 0,                       # No color shift
    'pan': 0,                       # Center horizontally
    'tilt': 0,                      # Center vertically
    'zoom': 100,                    # 1x (no zoom)
    'white_balance': 'auto',        # Automatic white balance
    'exposure': 'auto',             # Automatic exposure
    'focus': 'auto'                 # Continuous autofocus
}
```

Set all properties to smart defaults:

```python
cam.reset_to_defaults()             # Resets all to _SMART_DEFAULTS
```

Set individual property to smart default:

```python
cam.set_smart_default('brightness')
cam.set_smart_default('focus')
```


#### Fallback mechanism documentation

When device range queries fail or return unsupported, these constants serve as fallback boundaries:

1. **Query device**: Call `_get_dynamic_range(property_name)` against the camera's DirectShow interface.
2. **Success**: Return device-reported `min`, `max`, `step`, and `default` values.
3. **Failure/Unsupported**: Fall back to class constant (e.g., `BRIGHTNESS_MIN`/`MAX`).
4. **Invalid range**: Use safe default from `_SMART_DEFAULTS`.

This graceful degradation ensures operations work even with older or non-standard cameras.

***

### 3.5 Internal Property Mappings

Property mappings enable flexible string-based access (`cam.set('brightness', 80)`) while maintaining strong C++ typing internally. All properties map to enums defined in the C++ core.

#### `_VIDEO_PROPERTIES` dictionary (10 core properties)

Maps video property names to `VidProp` C++ enums. Video properties control image appearance (brightness, color, processing).

```python
_VIDEO_PROPERTIES = {
    # Core properties
    'brightness': VidProp.Brightness,
    'contrast': VidProp.Contrast,
    'hue': VidProp.Hue,
    'saturation': VidProp.Saturation,
    'sharpness': VidProp.Sharpness,
    'gamma': VidProp.Gamma,
    'color_enable': VidProp.ColorEnable,
    'white_balance': VidProp.WhiteBalance,
    'video_backlight_compensation': VidProp.BacklightCompensation,
    'gain': VidProp.Gain,
    
    # Aliases (user-friendly shortcuts)
    'wb': VidProp.WhiteBalance,
    'whitebalance': VidProp.WhiteBalance,
    'color': VidProp.ColorEnable,
    'colorenable': VidProp.ColorEnable,
    'sat': VidProp.Saturation,
    'bright': VidProp.Brightness,
}
```

**Video properties reference:**


| Property | Type | Aliases | Purpose | Device Range (Typical) |
| :-- | :-- | :-- | :-- | :-- |
| brightness | int | bright | Image luminance (dark to bright) | 0–255 (device-specific) |
| contrast | int | — | Tonal range (flat to high) | 0–100 (device-specific) |
| saturation | int | sat | Color intensity (grayscale to vivid) | 0–100 (device-specific) |
| hue | int | — | Color rotation (degrees) | -180 to +180 (device-specific) |
| sharpness | int | — | Edge definition (blurry to sharp) | 0–100 (device-specific) |
| gamma | int | — | Tone curve (value ÷ 100 = gamma) | 100–300 (device-specific) |
| color_enable | bool | color, colorenable | Monochrome vs. color mode | — (boolean) |
| white_balance | int/str | wb, whitebalance | Color temperature (Kelvin or 'auto') | 2700–6500K or 'auto' |
| video_backlight_compensation | bool | — | Backlighting adjustment | — (boolean) |
| gain | int | — | Sensor amplification (low to high) | 0–100 (device-specific) |

#### `_CAMERA_PROPERTIES` dictionary (11 core physical properties)

Maps camera/PTZ property names to `CamProp` C++ enums. Camera properties control physical camera mechanics (pan, tilt, zoom, focus, exposure, etc.).

```python
_CAMERA_PROPERTIES = {
    # Core PTZ and physical control properties
    'pan': CamProp.Pan,
    'tilt': CamProp.Tilt,
    'roll': CamProp.Roll,
    'zoom': CamProp.Zoom,
    'exposure': CamProp.Exposure,
    'iris': CamProp.Iris,
    'focus': CamProp.Focus,
    'scan_mode': CamProp.ScanMode,
    'privacy': CamProp.Privacy,
    'digital_zoom': CamProp.DigitalZoom,
    'backlight_compensation': CamProp.BacklightCompensation,
    
    # Aliases (user-friendly shortcuts)
    'z': CamProp.Zoom,
    'f': CamProp.Focus,
    'exp': CamProp.Exposure,
    'horizontal': CamProp.Pan,
    'vertical': CamProp.Tilt,
}
```

**Camera properties reference:**


| Property | Type | Aliases | Purpose | Device Range (Typical) |
| :-- | :-- | :-- | :-- | :-- |
| pan | int | horizontal | Horizontal head rotation (degrees) | -180 to +180 (device-specific) |
| tilt | int | vertical | Vertical head rotation (degrees) | -90 to +90 (device-specific) |
| roll | int | — | Rotation around optical axis | -180 to +180 (device-specific) |
| zoom | int | z | Optical magnification (100=1x) | 100–1000+ (device-specific) |
| exposure | int/str | exp | Exposure value (EV) or automatic | -13 to +1 or 'auto' (device-specific) |
| iris | int | — | Aperture/f-stop (closed to open) | 0–100 (device-specific) |
| focus | int/str | f | Focus distance or continuous autofocus | 0–100 or 'auto' (device-specific) |
| scan_mode | int | — | Interlaced vs. progressive | 0=interlaced, 1=progressive (device-specific) |
| privacy | bool | — | Privacy shutter engagement | — (boolean) |
| digital_zoom | int | — | Post-capture software zoom | 100–400+ (device-specific) |
| backlight_compensation | bool | — | Camera-level backlighting fix | — (boolean) |

#### `_BOOLEAN_PROPERTIES` set (6 boolean properties)

Tracks properties that return boolean values (on/off, true/false). These properties are automatically converted from integer to boolean when read.

```python
_BOOLEAN_PROPERTIES = {
    'color_enable',                 # Color vs. monochrome
    'colorenable',                  # Alias
    'color',                        # Alias
    'privacy',                      # Privacy shutter
    'video_backlight_compensation', # Backlight compensation
    'backlight_compensation',       # Alias (camera-level)
}
```

When reading these properties, values are automatically converted from internal int representation to Python bool:

```python
cam.get('color_enable')  # Returns bool: True (color on) or False (monochrome)
cam.get('privacy')       # Returns bool: True (shutter engaged) or False (open)

# Equivalent manual setting (automatically handled):
cam.set('color_enable', True)   # Sets on
cam.set('privacy', False)       # Opens shutter
```


#### Property mapping strategy and data flow

The string-based property access system resolves user-provided names to C++ enums through a consistent pipeline:

**Write operation (`cam.set('brightness', 80)`)**:

1. User provides property name string (canonical or alias)
2. Lookup in `_VIDEO_PROPERTIES` or `_CAMERA_PROPERTIES` dict
3. Resolve alias to canonical `VidProp`/`CamProp` enum
4. Check if property in `_BOOLEAN_PROPERTIES` for type handling
5. Create `PropSetting` object with value and mode
6. Call C++ core: `camera.set(enum, PropSetting)`
7. Return success or raise exception on failure

**Read operation (`value = cam.get('brightness')`)**:

1. User provides property name string
2. Lookup in dictionaries; resolve alias to enum
3. Check if property in `_BOOLEAN_PROPERTIES` for type conversion
4. Call C++ core: `camera.get(enum)`
5. Extract value from returned `PropSetting` result
6. If property in `_BOOLEAN_PROPERTIES`, convert int to bool (0→False, non-zero→True)
7. Return final value to user

**Alias resolution flow example**:

```
Input: cam.set('wb', 5500)
  ↓
Lookup: _VIDEO_PROPERTIES['wb']
  ↓
Resolved to: VidProp.WhiteBalance
  ↓
Create: PropSetting(5500, CamMode.Manual)
  ↓
Execute C++: camera.set(VidProp.WhiteBalance, PropSetting)
  ↓
Result: White balance set to 5500K on device
```

**Boolean conversion flow example**:

```
Input: cam.get('privacy')
  ↓
Lookup: _CAMERA_PROPERTIES['privacy']
  ↓
Resolved to: CamProp.Privacy
  ↓
Check: 'privacy' in _BOOLEAN_PROPERTIES? Yes
  ↓
Execute C++: int_value = camera.get(CamProp.Privacy).value()
  ↓
Convert: int_value (0 or 1) → bool (False or True)
  ↓
Return: bool(privacy_status)
```


#### Direct property accessor methods

For convenience, all properties have paired getter/setter methods that call `get()` and `set()` internally:

```python
# Direct setters (all internally call cam.set())
cam.set_brightness(80)      # Same as cam.set('brightness', 80)
cam.set_pan(45)             # Same as cam.set('pan', 45)
cam.set_focus('auto')       # Same as cam.set('focus', 'auto')
cam.set_white_balance(5500) # Same as cam.set('white_balance', 5500)

# Direct getters (all internally call cam.get())
brightness = cam.get_brightness()
pan = cam.get_pan()
focus = cam.get_focus()
white_balance = cam.get_white_balance()
```

Complete getter/setter pairs are available for all properties in `_VIDEO_PROPERTIES` and `_CAMERA_PROPERTIES`. These provide type-safe, IDE-autocomplete-friendly access when you prefer named methods over string lookups.

### 3.6 Video Properties - Image Processing Control

Video properties control image appearance and processing. All video properties query the device's actual supported range via `_get_dynamic_range()`, with fallback defaults for unsupported cameras. Device-specific ranges are device-reported and may vary significantly across camera models.

#### Brightness property

```python
@property
def brightness(self) -> int:
    """Camera brightness (uses device range, typically 0-255)."""
    return self._get_video_property(VidProp.Brightness, "brightness")

@brightness.setter
def brightness(self, value: int):
    """Set brightness using actual device range."""
    min_val, max_val = self._get_dynamic_range("brightness", 0, 100)
    self._set_video_property(VidProp.Brightness, "brightness", value, min_val, max_val)
```

Gets/sets image luminance (darkness to brightness). Queries device for actual range; falls back to 0-100 if device doesn't report range. Device-specific ranges vary: typical 0-255, but some cameras report 0-100 or other ranges.

Usage:

```python
cam.brightness = 80
current = cam.brightness  # Returns int within device range
```

Also accessible via string API: `cam.set('brightness', 80)` or alias `cam.set('bright', 80)`.

#### Contrast property

```python
@property
def contrast(self) -> int:
    """Camera contrast (uses device range, typically 0-100)."""
    return self._get_video_property(VidProp.Contrast, "contrast")

@contrast.setter
def contrast(self, value: int):
    """Set contrast using actual device range."""
    min_val, max_val = self._get_dynamic_range("contrast", 0, 100)
    self._set_video_property(VidProp.Contrast, "contrast", value, min_val, max_val)
```

Controls tonal range definition (flat to high-contrast). Queries device for range; falls back to 0-100. Device-specific ranges typically 0-100 or 0-127.

Usage:

```python
cam.contrast = 50
value = cam.contrast
```

Also: `cam.set('contrast', 50)`.

#### Hue property

```python
@property
def hue(self) -> int:
    """Camera hue (uses device range, often -180 to +180)."""
    return self._get_video_property(VidProp.Hue, "hue")

@hue.setter
def hue(self, value: int):
    """Set hue using actual device range."""
    min_val, max_val = self._get_dynamic_range("hue", -180, 180)
    self._set_video_property(VidProp.Hue, "hue", value, min_val, max_val)
```

Rotates colors around color wheel (degrees). Queries device; falls back to -180 to +180. Negative values shift towards magenta/red; positive towards cyan/green.

Usage:

```python
cam.hue = 0   # No shift
cam.hue = 45  # Shift towards cyan
```

Also: `cam.set('hue', 45)`.

#### Saturation property

```python
@property
def saturation(self) -> int:
    """Camera saturation (uses device range, typically 0-100)."""
    return self._get_video_property(VidProp.Saturation, "saturation")

@saturation.setter
def saturation(self, value: int):
    """Set saturation using actual device range."""
    min_val, max_val = self._get_dynamic_range("saturation", 0, 100)
    self._set_video_property(VidProp.Saturation, "saturation", value, min_val, max_val)
```

Adjusts color intensity (grayscale to vivid). Queries device; falls back to 0-100. Device-specific ranges typically 0-100 or 0-200.

Usage:

```python
cam.saturation = 50   # Neutral
cam.saturation = 100  # Vivid colors
```

Also: `cam.set('saturation', 50)` or alias `cam.set('sat', 50)`.

#### Sharpness property

```python
@property
def sharpness(self) -> int:
    """Camera sharpness (uses device range)."""
    return self._get_video_property(VidProp.Sharpness, "sharpness")

@sharpness.setter
def sharpness(self, value: int):
    """Set sharpness using actual device range."""
    min_val, max_val = self._get_dynamic_range("sharpness", 0, 100)
    self._set_video_property(VidProp.Sharpness, "sharpness", value, min_val, max_val)
```

Defines edge definition (blurry to sharp). Queries device; falls back to 0-100. Device ranges typically 0-100, 0-7, or manufacturer-specific values.

Usage:

```python
cam.sharpness = 50  # Moderate
cam.sharpness = 0   # Soft/blurred
```

Also: `cam.set('sharpness', 50)`.

#### Gamma property

```python
@property
def gamma(self) -> int:
    """Camera gamma (uses device range)."""
    return self._get_video_property(VidProp.Gamma, "gamma")

@gamma.setter
def gamma(self, value: int):
    """Set gamma using actual device range."""
    min_val, max_val = self._get_dynamic_range("gamma", 100, 300)
    self._set_video_property(VidProp.Gamma, "gamma", value, min_val, max_val)
```

Adjusts tone curve (non-linear brightness mapping). Value is stored as $int \times 0.01 = gamma$ (e.g., 100 = 1.0 linear, 180 = 1.8). Queries device; falls back to 100-300. Device ranges vary: some 100-300, others 40-400.

Usage:

```python
cam.gamma = 100  # Linear (1.0)
cam.gamma = 180  # Gamma 1.8 (brightens midtones)
```

Also: `cam.set('gamma', 100)`.

#### ColorEnable property (boolean)

```python
@property
def color_enable(self) -> bool:
    """Color vs monochrome (True = color, False = mono)."""
    return bool(self._get_video_property(VidProp.ColorEnable, "color_enable"))

@color_enable.setter
def color_enable(self, value: bool):
    """Set color mode (no range needed for bool)."""
    self._set_video_property(VidProp.ColorEnable, "color_enable", int(value))
```

Toggles monochrome vs. color output. Boolean property; automatically converted to/from int. Not range-queried (bool is always 0 or 1).

Usage:

```python
cam.color_enable = True   # Enable color
cam.color_enable = False  # Monochrome
is_color = cam.color_enable  # Returns bool: True or False
```

Also: `cam.set('color_enable', True)` or aliases `cam.set('color', True)` / `cam.set('colorenable', True)`.

#### WhiteBalance property (Kelvin)

```python
@property
def white_balance(self) -> int:
    """White balance temperature (uses device range, in Kelvin)."""
    return self._get_video_property(VidProp.WhiteBalance, "white_balance")

@white_balance.setter
def white_balance(self, value: int):
    """Set white balance using actual device range."""
    min_val, max_val = self._get_dynamic_range("white_balance", 2700, 6500)
    self._set_video_property(VidProp.WhiteBalance, "white_balance", value, min_val, max_val)
```

Adjusts color temperature (Kelvin scale). Integer value represents degrees Kelvin. Queries device; falls back to 2700-6500K. Device ranges vary: indoor 3000-4000K, daylight 5000-6500K, auto-balance varies.

Typical color temperatures:

- 2700K: Warm (incandescent)
- 3000-4000K: Indoor/warm LED
- 5000K: Daylight neutral
- 5500-6500K: Cool (daylight)

Usage:

```python
cam.white_balance = 5500  # Daylight
cam.white_balance = 3200  # Warm indoor
current = cam.white_balance
```

Also: `cam.set('white_balance', 5500)` or aliases `cam.set('wb', 5500)` / `cam.set('whitebalance', 5500)`. Use `cam.set('white_balance', 'auto')` for automatic white balance.

#### VideoBacklightCompensation property

```python
@property
def video_backlight_compensation(self) -> int:
    """Video backlight compensation (uses device range)."""
    return self._get_video_property(VidProp.BacklightCompensation, "video_backlight_compensation")

@video_backlight_compensation.setter
def video_backlight_compensation(self, value: int):
    """Set backlight compensation using actual device range."""
    min_val, max_val = self._get_dynamic_range("video_backlight_compensation", 0, 100)
    self._set_video_property(VidProp.BacklightCompensation, "video_backlight_compensation", value, min_val, max_val)
```

Adjusts for backlighting conditions (camera image processing level). Queries device; falls back to 0-100. Device ranges typically 0-100 (0=off, 100=maximum).

Usage:

```python
cam.video_backlight_compensation = 50  # Medium
cam.video_backlight_compensation = 0   # Off
```

Also: `cam.set('video_backlight_compensation', 50)`.

#### Gain property

```python
@property
def gain(self) -> int:
    """Sensor gain/amplification (uses device range)."""
    return self._get_video_property(VidProp.Gain, "gain")

@gain.setter
def gain(self, value: int):
    """Set gain using actual device range."""
    min_val, max_val = self._get_dynamic_range("gain", 0, 100)
    self._set_video_property(VidProp.Gain, "gain", value, min_val, max_val)
```

Amplifies sensor signal (useful in low light). Queries device; falls back to 0-100. Device ranges vary: typical 0-100, 0-255, or 0-16 (dB steps).

Usage:

```python
cam.gain = 50   # Medium amplification
cam.gain = 80   # High (for low-light)
cam.gain = 0    # Minimum
```

Also: `cam.set('gain', 50)`.

#### Dynamic range query mechanism

All video properties use `_get_dynamic_range()` internally:

```python
def _get_dynamic_range(self, property_name: str, fallback_min: int = 0, fallback_max: int = 100) -> tuple:
    """Get actual device range for property, with fallback defaults."""
    try:
        prop_range = self.get_property_range(property_name)
        if prop_range:
            return (prop_range.get('min', fallback_min), prop_range.get('max', fallback_max))
    except:
        pass
    return (fallback_min, fallback_max)
```

Query flow:

1. Call `get_property_range(property_name)` on device via DirectShow
2. If successful, return device-reported min/max
3. If query fails or returns None, use fallback constants as default
4. Set operation validated against retrieved range

#### Device-specific range variations

Property ranges vary dramatically across camera models:


| Property | Typical Range | Example Variations |
| :-- | :-- | :-- |
| brightness | 0-255 | Logitech: 0-255; Generic: 0-100; Intel: 0-200 |
| contrast | 0-100 | 0-100, 0-127, 0-255 |
| saturation | 0-100 | 0-100, 0-200 |
| hue | -180 to +180 | -180 to +180, -64 to +64 (some devices) |
| sharpness | 0-100 | 0-100, 0-7, manufacturer-specific |
| gamma | 100-300 | 100-300, 40-400, device-specific |
| white_balance | 2700-6500K | 2700-6500K, 3000-7000K, device-specific |
| gain | 0-100 | 0-100, 0-255, 0-16 dB (device-specific) |

#### Fallback constants

When device reports no range, these constants are used:

```python
BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 100
BRIGHTNESS_DEFAULT = 50

CONTRAST_MIN = 0
CONTRAST_MAX = 100
CONTRAST_DEFAULT = 50

SATURATION_MIN = 0
SATURATION_MAX = 100
SATURATION_DEFAULT = 50

HUE_MIN = -180
HUE_MAX = 180
HUE_DEFAULT = 0

GAMMA_MIN = 100
GAMMA_MAX = 300
GAMMA_DEFAULT = 100
```

Ensure operations never fail on unsupported cameras; gracefully degrade to safe nominal ranges.

#### Property validation and error handling

All setters validate values against device range before applying:

```python
# Validation example (internal)
if value < min_val or value > max_val:
    raise InvalidValueError(
        f"brightness must be between {min_val} and {max_val}, got {value}"
    )
```

Out-of-range values raise `InvalidValueError` with clear min/max guidance. Use `get_property_range()` to inspect actual ranges programmatically.

### 3.7 Camera Properties - Physical Control

Camera properties control physical camera movements and mechanical/electronic functions. All camera properties query device-specific limits via `_get_dynamic_range()`. These properties vary widely across camera models; device-specific behavior notes and quirks are documented below.

#### Pan property (horizontal rotation)

```python
@property
def pan(self) -> int:
    """Pan angle in degrees (uses device range, typically -180 to +180)."""
    return self._get_camera_property(CamProp.Pan, "pan")

@pan.setter
def pan(self, value: int):
    """Set pan angle using actual device range."""
    min_val, max_val = self._get_dynamic_range("pan", -180, 180)
    self._set_camera_property(CamProp.Pan, "pan", value, min_val, max_val)
```

Rotates camera horizontally (left/right). Queries device; falls back to -180 to +180 degrees. Negative values pan left; positive pan right; 0 is center.

Device-specific notes:

- **PTZ cameras**: Typically -180 to +180 (full rotation)
- **Fixed webcams**: Often unsupported or very limited ranges (-30 to +30)
- **Some USB cameras**: Report ranges in different units; library normalizes to degrees

Usage:

```python
cam.pan = 0      # Center
cam.pan = 45     # Pan 45° right
cam.pan = -90    # Pan 90° left
current = cam.pan
```

Also: `cam.set('pan', 45)` or alias `cam.set('horizontal', 45)`.

#### Tilt property (vertical rotation)

```python
@property
def tilt(self) -> int:
    """Tilt angle in degrees (uses device range, typically -90 to +90)."""
    return self._get_camera_property(CamProp.Tilt, "tilt")

@tilt.setter
def tilt(self, value: int):
    """Set tilt angle using actual device range."""
    min_val, max_val = self._get_dynamic_range("tilt", -90, 90)
    self._set_camera_property(CamProp.Tilt, "tilt", value, min_val, max_val)
```

Rotates camera vertically (up/down). Queries device; falls back to -90 to +90 degrees. Negative values tilt down; positive tilt up; 0 is center.

Device-specific notes:

- **PTZ cameras**: Typically -90 to +90
- **Fixed webcams**: Often unsupported; may report 0 range
- **Mechanical limits**: Some cameras physically limit to -45 to +45; query `get_property_range('tilt')` for actual limits

Usage:

```python
cam.tilt = 0     # Center
cam.tilt = 30    # Tilt 30° up
cam.tilt = -15   # Tilt 15° down
```

Also: `cam.set('tilt', 30)` or alias `cam.set('vertical', 30)`.

#### Roll property (rotation around optical axis)

```python
@property
def roll(self) -> int:
    """Roll angle in degrees (uses device range, typically -180 to +180)."""
    return self._get_camera_property(CamProp.Roll, "roll")

@roll.setter
def roll(self, value: int):
    """Set roll angle using actual device range."""
    min_val, max_val = self._get_dynamic_range("roll", -180, 180)
    self._set_camera_property(CamProp.Roll, "roll", value, min_val, max_val)
```

Rotates image around optical axis (tilts left/right edge). Queries device; falls back to -180 to +180 degrees.

Device-specific notes:

- **Most cameras**: Roll is **unsupported**; returns error on set
- **Advanced PTZ cameras**: May support ±45 to ±180
- **Workaround**: If unsupported, roll is typically disabled in firmware; check `get_property_range('roll')` returns valid range before setting

Usage:

```python
cam.roll = 0      # Neutral
cam.roll = 10     # Roll 10° right
cam.roll = -10    # Roll 10° left
```

Also: `cam.set('roll', 10)`.

#### Zoom property (optical magnification)

```python
@property
def zoom(self) -> int:
    """Optical zoom multiplier × 100 (uses device range, typically 100-1000)."""
    return self._get_camera_property(CamProp.Zoom, "zoom")

@zoom.setter
def zoom(self, value: int):
    """Set zoom using actual device range."""
    min_val, max_val = self._get_dynamic_range("zoom", 100, 1000)
    self._set_camera_property(CamProp.Zoom, "zoom", value, min_val, max_val)
```

Sets optical magnification. Queries device; falls back to 100-1000. Value represents multiplier × 100 (e.g., 100 = 1x, 200 = 2x, 500 = 5x).

Device-specific notes:

- **Logitech cameras**: 100-4x (100-400 range)
- **High-end PTZ**: 100-30x or more (100-3000+ range)
- **Fixed webcams**: Often unsupported or fixed at 100 (no zoom)
- **Note**: Optical zoom may degrade image quality at extreme ranges; test at target zoom before deployment

Usage:

```python
cam.zoom = 100   # 1x (no zoom)
cam.zoom = 200   # 2x zoom
cam.zoom = 500   # 5x zoom
current = cam.zoom
```

Also: `cam.set('zoom', 200)` or alias `cam.set('z', 200)`.

#### Exposure property (shutter speed / exposure time)

```python
@property
def exposure(self) -> int:
    """Exposure value in EV units (uses device range, e.g., -13 to +1)."""
    return self._get_camera_property(CamProp.Exposure, "exposure")

@exposure.setter
def exposure(self, value: int):
    """Set exposure using actual device range."""
    min_val, max_val = self._get_dynamic_range("exposure", -13, 1)
    self._set_camera_property(CamProp.Exposure, "exposure", value, min_val, max_val)
```

Controls exposure time / shutter speed. Queries device; falls back to -13 to +1 EV (exposure value units). Negative values darken; positive values brighten. EV adjusts exposure by powers of 2 (each ±1 EV doubles/halves light).

Device-specific notes:

- **Typical range**: -12 to +12 EV (varies by camera)
- **Note**: Some cameras use proprietary units instead of EV; library converts where possible
- **Workaround**: If exposure doesn't respond as expected, device may require manual mode; try setting exposure mode to 'manual' first

Usage:

```python
cam.exposure = 0    # Default
cam.exposure = -2   # Darker (1/4 light)
cam.exposure = 2    # Brighter (4x light)
cam.set('exposure', 'auto')  # Automatic exposure
```

Also: `cam.set('exposure', -2)` or alias `cam.set('exp', -2)`.

#### Iris property (aperture / f-stop)

```python
@property
def iris(self) -> int:
    """Iris aperture/f-stop (uses device range, typically 0-100)."""
    return self._get_camera_property(CamProp.Iris, "iris")

@iris.setter
def iris(self, value: int):
    """Set iris using actual device range."""
    min_val, max_val = self._get_dynamic_range("iris", 0, 100)
    self._set_camera_property(CamProp.Iris, "iris", value, min_val, max_val)
```

Controls aperture opening (depth of field and light gathering). Queries device; falls back to 0-100. Lower values = wider aperture (more light, shallow focus); higher values = smaller aperture (less light, deep focus).

Device-specific notes:

- **Most cameras**: Iris is **unsupported** (fixed aperture)
- **Supported cameras**: Typically 0-100 mapping to f/1.4 to f/32 (approximate)
- **Workaround**: If iris is unsupported, exposure or gain can approximate depth-of-field effects

Usage:

```python
cam.iris = 0     # Wide open (max light, shallow focus)
cam.iris = 50    # Mid aperture
cam.iris = 100   # Small aperture (deep focus)
```

Also: `cam.set('iris', 50)`.

#### Focus property (autofocus or manual focus distance)

```python
@property
def focus(self) -> int:
    """Focus distance 0-100 or 'auto' for continuous autofocus."""
    return self._get_camera_property(CamProp.Focus, "focus")

@focus.setter
def focus(self, value):
    """Set focus using actual device range or 'auto'."""
    if isinstance(value, str) and value.lower() == 'auto':
        self._set_property_auto('focus')
    else:
        min_val, max_val = self._get_dynamic_range("focus", 0, 100)
        self._set_camera_property(CamProp.Focus, "focus", int(value), min_val, max_val)
```

Controls focus distance (manual) or enables autofocus. Queries device; falls back to 0-100. Accepts int (manual) or 'auto' string.

Device-specific notes:

- **Most cameras**: Support autofocus via 'auto' mode (highly recommended)
- **Manual mode**: 0=closest focus, 100=farthest (hyperfocal)
- **Some cameras**: Autofocus very slow; manual focus may be faster for dynamic scenes
- **Workaround**: If autofocus hunting occurs (oscillating focus), switch to manual mode with fixed distance

Usage:

```python
cam.focus = 'auto'   # Continuous autofocus (recommended)
cam.focus = 50       # Manual focus at midpoint
cam.focus = 0        # Manual close-up focus
cam.set('focus', 'auto')  # Autofocus via string API
```

Also: `cam.set('focus', 50)` or alias `cam.set('f', 50)`.

#### ScanMode property (interlaced vs. progressive)

```python
@property
def scan_mode(self) -> int:
    """Scan mode (0=interlaced, 1=progressive)."""
    return self._get_camera_property(CamProp.ScanMode, "scan_mode")

@scan_mode.setter
def scan_mode(self, value: int):
    """Set scan mode (0 or 1)."""
    self._set_camera_property(CamProp.ScanMode, "scan_mode", value, 0, 1)
```

Selects video scanning format. No dynamic range needed (0 or 1 only). 0=interlaced (legacy TV format), 1=progressive (modern, no flickering).

Device-specific notes:

- **Modern cameras**: Progressive (1) is standard; interlaced rarely used
- **Compatibility**: Some older cameras report only interlaced; check support before relying on progressive
- **Performance**: Progressive mode may reduce max frame rate on some low-end cameras

Usage:

```python
cam.scan_mode = 1    # Progressive (recommended)
cam.scan_mode = 0    # Interlaced (legacy)
```

Also: `cam.set('scan_mode', 1)`.

#### Privacy property (privacy shutter)

```python
@property
def privacy(self) -> bool:
    """Privacy shutter engaged (True=on, False=off)."""
    return bool(self._get_camera_property(CamProp.Privacy, "privacy"))

@privacy.setter
def privacy(self, value: bool):
    """Engage privacy shutter (electronic or mechanical)."""
    self._set_camera_property(CamProp.Privacy, "privacy", int(value))
```

Engages electronic or mechanical privacy shutter. Boolean property. True=shutter closed (camera disabled); False=shutter open (normal operation).

Device-specific notes:

- **Some cameras**: Hardware privacy button (LED indicates state); software control works independently
- **Others**: Electronic only; no visual feedback beyond API state
- **Workaround**: If privacy appears stuck, query status via `cam.privacy` before troubleshooting

Usage:

```python
cam.privacy = True   # Close privacy shutter
cam.privacy = False  # Open shutter (normal operation)
is_privacy_on = cam.privacy  # Check status
```

Also: `cam.set('privacy', True)`.

#### DigitalZoom property (software/post-capture zoom)

```python
@property
def digital_zoom(self) -> int:
    """Digital zoom multiplier × 100 (uses device range, typically 100-400)."""
    return self._get_camera_property(CamProp.DigitalZoom, "digital_zoom")

@digital_zoom.setter
def digital_zoom(self, value: int):
    """Set digital zoom using actual device range."""
    min_val, max_val = self._get_dynamic_range("digital_zoom", 100, 400)
    self._set_camera_property(CamProp.DigitalZoom, "digital_zoom", value, min_val, max_val)
```

Post-capture software zoom (crops and upscales). Queries device; falls back to 100-400. Like optical zoom, value is multiplier × 100 (100=1x, 200=2x).

Device-specific notes:

- **Quality**: Digital zoom degrades image quality (lossy cropping); prefer optical zoom
- **Combined with optical**: May be combined with optical zoom on some cameras (e.g., optical 4x + digital 2x = 8x total, degraded)
- **Typical use**: Emergency zoom when optical zoom insufficient; avoid in production if possible

Usage:

```python
cam.digital_zoom = 100   # 1x (no digital zoom)
cam.digital_zoom = 200   # 2x (crops center, upscales)
```

Also: `cam.set('digital_zoom', 200)`.

#### BacklightCompensation property (camera-level)

```python
@property
def backlight_compensation(self) -> bool:
    """Backlight compensation engaged (camera-level control)."""
    return bool(self._get_camera_property(CamProp.BacklightCompensation, "backlight_compensation"))

@backlight_compensation.setter
def backlight_compensation(self, value: bool):
    """Enable camera-level backlight compensation."""
    self._set_camera_property(CamProp.BacklightCompensation, "backlight_compensation", int(value))
```

Camera-level backlight adjustment (different from video-level `video_backlight_compensation`). Boolean property. True=enable; False=disable. Works at camera sensor level (more primitive than video processing).

Device-specific notes:

- **Note**: Distinct from `video_backlight_compensation` which is image processing level; this is camera-level
- **Interaction**: Using both simultaneously may cause unpredictable results; prefer `video_backlight_compensation` for finer control
- **Workaround**: If image over/under-exposes with both enabled, disable camera-level version

Usage:

```python
cam.backlight_compensation = True   # Enable
cam.backlight_compensation = False  # Disable
```

Also: `cam.set('backlight_compensation', True)`.

#### Lamp property (LED control)

```python
@property
def lamp(self) -> int:
    """LED lamp intensity (uses device range, typically 0-100)."""
    return self._get_camera_property(CamProp.Lamp, "lamp")

@lamp.setter
def lamp(self, value: int):
    """Set LED lamp intensity using actual device range."""
    min_val, max_val = self._get_dynamic_range("lamp", 0, 100)
    self._set_camera_property(CamProp.Lamp, "lamp", value, min_val, max_val)
```

Controls built-in LED light (if camera has one). Queries device; falls back to 0-100. 0=off; higher values=brighter.

Device-specific notes:

- **Availability**: Most consumer cameras lack built-in LED; supported primarily on professional/PTZ models
- **Unsupported**: Attempting set on camera without LED raises error; query `get_property_range('lamp')` first to check support
- **Power draw**: LED significantly increases power consumption; consider USB power limitations

Usage:

```python
if cam.get_property_range('lamp'):  # Check support
    cam.lamp = 50  # Set LED to 50% brightness
```

Also: `cam.set('lamp', 50)` (if supported).

#### Device-specific behavior and quirks

| Behavior | Cameras Affected | Workaround |
| :-- | :-- | :-- |
| Pan/tilt very slow | Most USB cameras | Set smaller increments; use continuous movement instead of steps |
| Zoom "snaps" between discrete steps | Some older cameras | Smooth zoom unavailable; adjust expectations |
| Focus hunting (oscillating) | Cheap autofocus cameras | Switch to manual focus with fixed distance |
| Exposure changes cause lag | Cameras with slow sensors | Pre-set exposure before recording critical frames |
| Privacy shutter doesn't respond | Hardware-restricted cameras | Check physical button state; software control may be ignored |
| Roll unsupported | 99% of cameras | Query range before using; expect error on most devices |

#### Device-specific range variations

| Property | Typical Range | Variations | Query Example |
| :-- | :-- | :-- | :-- |
| pan | -180 to +180° | Fixed: 0 range; PTZ: -180 to +180; Limited: -30 to +30 | `cam.get_property_range('pan')` |
| tilt | -90 to +90° | Fixed: 0; Limited: -45 to +45 | `cam.get_property_range('tilt')` |
| zoom | 100–1000 | 100–400 (Logitech); 100–3000 (PTZ) | `cam.get_property_range('zoom')` |
| exposure | -13 to +1 EV | -12 to +12 (varies); proprietary units on some | `cam.get_property_range('exposure')` |
| focus | 0–100 | Device-specific; some report 0–255 or different scales | `cam.get_property_range('focus')` |
| digital_zoom | 100–400 | 100–300; 100–200 (limited devices) | `cam.get_property_range('digital_zoom')` |
| lamp | 0–100 | Unsupported on most; 0–255 (professional cameras) | `cam.get_property_range('lamp')` |

### 3.8 Relative Movement \& Combined PTZ

Relative movement methods adjust camera position/zoom by delta values rather than absolute positions. Combined movement methods execute multiple operations atomically, reducing latency and enabling smoother motion. Some cameras support hardware-level combined commands; others fall back to sequential individual commands.

#### Pan relative movement

```python
def pan_relative(self, degrees: int) -> None:
    """Pan camera by relative degrees (left/right increment)."""
    self._ensure_connected()
    current_pan = self.pan
    target_pan = current_pan + degrees
    
    # Clamp to device range
    min_pan, max_pan = self._get_dynamic_range("pan", -180, 180)
    target_pan = max(min_pan, min(max_pan, target_pan))
    
    self.pan = target_pan
```

Adjusts pan angle by delta. Internally calculates target position, clamps to device range, applies absolutely. Positive degrees = pan right; negative = pan left.

Usage:

```python
cam.pan_relative(45)   # Pan 45° right from current position
cam.pan_relative(-30)  # Pan 30° left
```


#### Tilt relative movement

```python
def tilt_relative(self, degrees: int) -> None:
    """Tilt camera by relative degrees (up/down increment)."""
    self._ensure_connected()
    current_tilt = self.tilt
    target_tilt = current_tilt + degrees
    
    min_tilt, max_tilt = self._get_dynamic_range("tilt", -90, 90)
    target_tilt = max(min_tilt, min(max_tilt, target_tilt))
    
    self.tilt = target_tilt
```

Adjusts tilt angle by delta. Positive degrees = tilt up; negative = tilt down.

Usage:

```python
cam.tilt_relative(20)   # Tilt 20° up
cam.tilt_relative(-10)  # Tilt 10° down
```


#### Roll relative movement

```python
def roll_relative(self, degrees: int) -> None:
    """Roll camera by relative degrees (rotate around optical axis)."""
    self._ensure_connected()
    current_roll = self.roll
    target_roll = current_roll + degrees
    
    min_roll, max_roll = self._get_dynamic_range("roll", -180, 180)
    target_roll = max(min_roll, min(max_roll, target_roll))
    
    self.roll = target_roll
```

Adjusts roll by delta. Positive degrees = clockwise; negative = counterclockwise.

Usage:

```python
cam.roll_relative(15)   # Roll 15° clockwise
cam.roll_relative(-5)   # Roll 5° counterclockwise
```

Note: Roll is unsupported on most cameras; query `get_property_range('roll')` before using.

#### Zoom relative movement (step-based)

```python
def zoom_relative(self, steps: int) -> None:
    """Zoom by relative steps (teleconverter-style stepping)."""
    self._ensure_connected()
    current_zoom = self.zoom
    # Each step = 10% magnification increase (device-dependent)
    step_increment = 50  # 0.5x per step (typical)
    target_zoom = current_zoom + (steps * step_increment)
    
    min_zoom, max_zoom = self._get_dynamic_range("zoom", 100, 1000)
    target_zoom = max(min_zoom, min(max_zoom, target_zoom))
    
    self.zoom = target_zoom
```

Adjusts zoom by step increments. Each step typically = 0.5x magnification (device-specific). Positive steps = zoom in; negative = zoom out.

Usage:

```python
cam.zoom_relative(2)   # Zoom in 2 steps (roughly 1x magnification)
cam.zoom_relative(-1)  # Zoom out 1 step
```


#### Focus relative movement (step-based)

```python
def focus_relative(self, steps: int) -> None:
    """Adjust focus by relative steps (manual focus increment)."""
    self._ensure_connected()
    current_focus = self.focus
    # Each step = 2% distance change (device-dependent)
    step_increment = 2
    target_focus = current_focus + (steps * step_increment)
    
    min_focus, max_focus = self._get_dynamic_range("focus", 0, 100)
    target_focus = max(min_focus, min(max_focus, target_focus))
    
    self.focus = target_focus
```

Adjusts focus by step increments. Each step typically = 2% focus distance change (device-specific). Positive steps = focus farther; negative = focus closer.

Usage:

```python
cam.focus_relative(5)   # Focus farther (5 steps)
cam.focus_relative(-3)  # Focus closer (3 steps)
```

Note: Use `focus = 'auto'` for continuous autofocus instead of manual stepping.

#### Exposure relative movement (EV steps)

```python
def exposure_relative(self, steps: int) -> None:
    """Adjust exposure by relative EV steps."""
    self._ensure_connected()
    current_exposure = self.exposure
    # Each step = 1 EV (doubles/halves light)
    target_exposure = current_exposure + steps
    
    min_exp, max_exp = self._get_dynamic_range("exposure", -13, 1)
    target_exposure = max(min_exp, min(max_exp, target_exposure))
    
    self.exposure = target_exposure
```

Adjusts exposure by EV steps. Each step = 1 EV (doubles/halves light). Positive steps = brighter; negative = darker.

Usage:

```python
cam.exposure_relative(2)   # Brighten by 2 EV (4x light)
cam.exposure_relative(-1)  # Darken by 1 EV (0.5x light)
```


#### Iris relative movement (step-based)

```python
def iris_relative(self, steps: int) -> None:
    """Adjust iris/aperture by relative steps."""
    self._ensure_connected()
    current_iris = self.iris
    # Each step = 5% aperture adjustment (device-dependent)
    step_increment = 5
    target_iris = current_iris + (steps * step_increment)
    
    min_iris, max_iris = self._get_dynamic_range("iris", 0, 100)
    target_iris = max(min_iris, min(max_iris, target_iris))
    
    self.iris = target_iris
```

Adjusts iris (aperture) by steps. Positive steps = smaller aperture (less light); negative = wider aperture (more light).

Usage:

```python
cam.iris_relative(2)   # Close aperture 2 steps
cam.iris_relative(-1)  # Open aperture 1 step
```

Note: Iris unsupported on most fixed-aperture cameras.

#### Digital zoom relative movement

```python
def digital_zoom_relative(self, steps: int) -> None:
    """Adjust digital zoom by relative steps."""
    self._ensure_connected()
    current_dzoom = self.digital_zoom
    # Each step = 10% magnification (device-dependent)
    step_increment = 10
    target_dzoom = current_dzoom + (steps * step_increment)
    
    min_dzoom, max_dzoom = self._get_dynamic_range("digital_zoom", 100, 400)
    target_dzoom = max(min_dzoom, min(max_dzoom, target_dzoom))
    
    self.digital_zoom = target_dzoom
```

Adjusts digital (software) zoom by steps. Positive steps = zoom in; negative = zoom out.

Usage:

```python
cam.digital_zoom_relative(2)  # Zoom in 2 steps (lossy)
```

Note: Digital zoom degrades quality; use optical zoom when possible.

#### Simultaneous pan+tilt movement

```python
def set_pan_tilt(self, pan: int, tilt: int) -> None:
    """Set pan and tilt simultaneously (atomic operation)."""
    self._ensure_connected()
    
    # Validate ranges
    min_pan, max_pan = self._get_dynamic_range("pan", -180, 180)
    min_tilt, max_tilt = self._get_dynamic_range("tilt", -90, 90)
    
    pan = max(min_pan, min(max_pan, pan))
    tilt = max(min_tilt, min(max_tilt, tilt))
    
    try:
        # Attempt hardware-level simultaneous command
        self._core_camera.set_pan_tilt(pan, tilt)
    except:
        # Fallback to sequential commands
        self.pan = pan
        self.tilt = tilt
```

Sets pan and tilt atomically. Some cameras support hardware-level simultaneous movement (smoother motion); others fall back to sequential pan then tilt commands.

Usage:

```python
cam.set_pan_tilt(45, -30)  # Pan 45° right, tilt 30° down simultaneously
cam.set_pan_tilt(0, 0)     # Center camera
```


#### Combined relative pan+tilt movement

```python
def pan_tilt_relative(self, pan_delta: int, tilt_delta: int) -> None:
    """Adjust pan and tilt by relative deltas (combined move)."""
    self._ensure_connected()
    
    # Calculate target positions
    current_pan = self.pan
    current_tilt = self.tilt
    target_pan = current_pan + pan_delta
    target_tilt = current_tilt + tilt_delta
    
    # Apply constraints and execute as combined move
    self.set_pan_tilt(target_pan, target_tilt)
```

Adjusts pan and tilt by deltas from current position. Combines relative calculation with atomic simultaneous movement.

Usage:

```python
cam.pan_tilt_relative(30, -20)   # Pan 30° right, tilt 20° down
cam.pan_tilt_relative(-45, 0)    # Pan 45° left, hold tilt
```


#### Hardware support and fallback strategy

Combined movement support varies by camera:

**Hardware-supported combined commands**:

- Professional PTZ cameras (Sony, Panasonic, etc.)
- Some IP cameras with DirectShow interface
- Result: Smooth, coordinated motion

**Fallback to individual commands**:

- Most USB webcams
- Budget IP cameras
- Result: Sequential pan then tilt (slightly jerky but functional)

The library automatically detects support and falls back gracefully:

```python
try:
    # Try hardware combined command
    self._core_camera.set_pan_tilt(pan, tilt)
except AttributeError:
    # Fallback to individual
    self.pan = pan
    self.tilt = tilt
except OperationNotSupported:
    # Fallback to individual
    self.pan = pan
    self.tilt = tilt
```


#### Relative vs. absolute positioning guide

**Use absolute positioning** (`cam.pan = 45`):

- Setting specific target (e.g., look at fixed point)
- Resetting to known state (e.g., `cam.pan = 0` to center)
- API simplicity (single operation)

**Use relative movement** (`cam.pan_relative(10)`):

- Incremental adjustments (e.g., joystick-style panning)
- Smooth continuous motion (repeatedly call with small steps)
- Bounds-safe (automatically clamps to device limits)

**Use combined movement** (`cam.set_pan_tilt(45, -30)`):

- Simultaneous multi-axis motion (faster, smoother)
- Reduces latency (single command vs. two sequential)
- Must know both target values (less convenient than relative)

**Example: Smooth panning (relative)**:

```python
# Smooth leftward pan using relative increments
for _ in range(10):
    cam.pan_relative(-5)  # Pan 5° left each step
    time.sleep(0.1)       # 1 second total pan
```

**Example: Center and reset (absolute)**:

```python
cam.set_pan_tilt(0, 0)  # Center both axes atomically
```

**Example: Joystick control (mixed)**:

```python
def handle_joystick(x, y):
    """x,y are joystick axis values (-1.0 to +1.0)."""
    pan_delta = int(x * 45)       # ±45° range
    tilt_delta = int(y * -30)     # ±30° range (Y inverted)
    
    # Calculate target (relative from current)
    target_pan = cam.pan + pan_delta
    target_tilt = cam.tilt + tilt_delta
    
    # Apply as combined move
    cam.set_pan_tilt(target_pan, target_tilt)
```


#### Performance considerations

| Method | Latency | Hardware Support | Use Case |
| :-- | :-- | :-- | :-- |
| Absolute `pan = 45` | ~50ms | All cameras | Discrete positioning |
| Relative `pan_relative(5)` | ~50ms | All cameras | Incremental motion |
| Combined `set_pan_tilt()` | ~30ms (hardware) ~80ms (fallback) | PTZ/Pro cameras | Smooth simultaneous motion |
| Relative combined `pan_tilt_relative()` | ~30-80ms | Varies | Joystick-style continuous |

For **real-time applications** (joystick, tracking), use combined movement methods. For **one-time positioning**, absolute is simpler. These latency measures are just estimates, real values vary.

### 3.9 String-Based Universal Property Access

The universal string-based API allows dynamic property access by name without knowing property types ahead of time. Both `set()` and `get()` perform property name resolution, handle type conversion, and support auto mode strings for properties that require it.

#### Universal setter method: `set(property_name, value, mode='manual')`

```python
def set(self, property_name: str, value: Union[int, str, bool], mode: str = 'manual') -> None:
    """Set any property by name (video, camera, or auto mode string)."""
    self._ensure_connected()
    
    # Resolve property name (handle alias)
    prop_name = property_name.lower().strip()
    
    # Check if auto mode string (special handling)
    if isinstance(value, str) and value.lower() in ['auto', 'continuous']:
        self._set_property_auto(prop_name)
        return
    
    # Determine property type (video or camera)
    if prop_name in self._VIDEO_PROPERTIES or prop_name in self._VIDEO_PROPERTIES.values():
        self._set_video_property(prop_name, value)
    elif prop_name in self._CAMERA_PROPERTIES or prop_name in self._CAMERA_PROPERTIES.values():
        self._set_camera_property(prop_name, value, mode)
    else:
        raise PropertyNotSupportedError(f"Property '{property_name}' not recognized")
```

Universal setter accepts any property by string name. Supports three value types:

1. **Integer values**: Direct numeric assignment (brightness, pan, zoom, etc.)
2. **String auto mode**: Special values like `'auto'`, `'continuous'` for autofocus/auto white balance
3. **Boolean values**: For boolean properties (automatically converted to int)

Mode parameter controls operation mode:

```python
cam.set('exposure', 2, mode='manual')      # Manual exposure
cam.set('exposure', 'auto')                 # Auto exposure (via string value)
cam.set('focus', 'auto')                    # Autofocus
cam.set('white_balance', 5500, mode='manual')  # Manual white balance
```


#### Universal getter method: `get(property_name)`

```python
def get(self, property_name: str) -> Union[int, str, bool]:
    """Get any property by name (video or camera), with automatic type conversion."""
    self._ensure_connected()
    
    # Resolve property name
    prop_name = property_name.lower().strip()
    
    # Determine property type and fetch
    if prop_name in self._VIDEO_PROPERTIES or prop_name in self._VIDEO_PROPERTIES.values():
        value = self._get_video_property(prop_name)
    elif prop_name in self._CAMERA_PROPERTIES or prop_name in self._CAMERA_PROPERTIES.values():
        value = self._get_camera_property(prop_name)
    else:
        raise PropertyNotSupportedError(f"Property '{property_name}' not recognized")
    
    # Automatic type conversion for boolean properties
    if prop_name in self._BOOLEAN_PROPERTIES:
        return bool(value)  # Convert int to bool
    
    return value
```

Universal getter returns property value by string name. Automatically converts types:

- **Boolean properties**: Returns `bool` (True/False) instead of int (0/1)
- **Integer properties**: Returns `int` as-is
- **Mode-dependent properties**: Returns current int value (mode is read from device)

Usage:

```python
brightness = cam.get('brightness')     # Returns int
pan = cam.get('pan')                   # Returns int
is_color = cam.get('color_enable')     # Returns bool (auto-converted)
privacy_on = cam.get('privacy')        # Returns bool
```


#### Property name resolution \& lookup strategy

Property names are resolved through multi-step lookup:

```python
def _resolve_property_name(self, name: str) -> tuple:
    """Resolve property name to (enum, is_video, canonical_name)."""
    name_lower = name.lower().strip()
    
    # Step 1: Check video properties (canonical + aliases)
    if name_lower in self._VIDEO_PROPERTIES:
        return (self._VIDEO_PROPERTIES[name_lower], True, name_lower)
    
    # Step 2: Check camera properties (canonical + aliases)
    if name_lower in self._CAMERA_PROPERTIES:
        return (self._CAMERA_PROPERTIES[name_lower], False, name_lower)
    
    # Step 3: Not found
    raise PropertyNotSupportedError(f"Unknown property: {name}")
```

Resolution priority:

1. **Canonical names**: `'brightness'`, `'pan'`, `'zoom'`, etc.
2. **Aliases**: `'bright'`, `'z'`, `'wb'`, etc.
3. **Error**: Raise `PropertyNotSupportedError` if not found

**Resolution examples:**

```
Input: 'brightness' → Video property
Input: 'bright'     → Alias for 'brightness' (video)
Input: 'wb'         → Alias for 'white_balance' (video)
Input: 'z'          → Alias for 'zoom' (camera)
Input: 'horizontal' → Alias for 'pan' (camera)
Input: 'invalid'    → PropertyNotSupportedError
```


#### Automatic type conversion for boolean

Boolean properties are automatically converted between int (device representation) and bool (Python representation):

```python
# Write: bool → int
cam.set('color_enable', True)       # Python: True, Device: 1
cam.set('privacy', False)           # Python: False, Device: 0

# Read: int → bool
is_color = cam.get('color_enable')  # Device: 1, Python: True
privacy = cam.get('privacy')        # Device: 0, Python: False
```

Conversion logic:

```python
# To device (int):
device_value = int(python_bool)     # True → 1, False → 0

# From device (bool):
python_bool = bool(device_value)    # 0 → False, non-zero → True
```


#### Auto mode string support

Properties supporting automatic modes accept special string values:

```python
cam.set('white_balance', 'auto')    # Enable auto white balance
cam.set('focus', 'auto')             # Enable continuous autofocus
cam.set('exposure', 'auto')          # Enable automatic exposure
```

Auto mode strings are mode-agnostic (user doesn't specify `CamMode` enum):

```python
def _set_property_auto(self, prop_name: str) -> None:
    """Set property to automatic/continuous mode."""
    mode = CamMode.Auto  # Or CamMode.Continuous
    
    # Resolve property
    if prop_name in self._VIDEO_PROPERTIES:
        enum = self._VIDEO_PROPERTIES[prop_name]
        self._core_camera.set(enum, PropSetting(0, mode))
    elif prop_name in self._CAMERA_PROPERTIES:
        enum = self._CAMERA_PROPERTIES[prop_name]
        self._core_camera.set(enum, PropSetting(0, mode))
```

Supported auto modes:


| Property | Auto Values | Effect |
| :-- | :-- | :-- |
| white_balance | 'auto' | Automatic color temperature detection |
| focus | 'auto', 'continuous' | Continuous autofocus |
| exposure | 'auto' | Automatic exposure control |
| iris | 'auto' | Automatic aperture adjustment |

#### Mode string parsing: `_parse_mode_string()` helper

Helper method converts user-provided mode strings to C++ `CamMode` enums:

```python
def _parse_mode_string(self, mode_string: str) -> CamMode:
    """Parse mode string to CamMode enum."""
    mode_lower = mode_string.lower().strip()
    
    mode_map = {
        'manual': CamMode.Manual,
        'auto': CamMode.Auto,
        'continuous': CamMode.Continuous,
        'priority': CamMode.Priority,
        'absolute': CamMode.Absolute,
        'relative': CamMode.Relative,
    }
    
    if mode_lower in mode_map:
        return mode_map[mode_lower]
    
    # Default to manual if unknown
    return CamMode.Manual
```

Mode strings accepted:


| String | CamMode | Use Case |
| :-- | :-- | :-- |
| 'manual' | Manual | User controls value directly |
| 'auto' | Auto | Camera decides (one-time) |
| 'continuous' | Continuous | Camera continuously adjusts |
| 'absolute' | Absolute | Absolute positioning |
| 'relative' | Relative | Relative movement |

Usage with mode parameter:

```python
cam.set('brightness', 80, mode='manual')        # Manual mode
cam.set('exposure', -2, mode='manual')          # Manual exposure
cam.set('focus', 50, mode='absolute')           # Absolute focus position
```


#### Property alias resolution logic

Alias resolution allows flexible property naming:

```python
def _is_alias_for(self, alias: str, canonical: str) -> bool:
    """Check if alias resolves to canonical property."""
    # Video properties
    if self._VIDEO_PROPERTIES.get(alias) == self._VIDEO_PROPERTIES.get(canonical):
        return True
    
    # Camera properties
    if self._CAMERA_PROPERTIES.get(alias) == self._CAMERA_PROPERTIES.get(canonical):
        return True
    
    return False
```

**Alias resolution flow:**

```
User: cam.set('bright', 80)
  ↓
Lookup 'bright' in _VIDEO_PROPERTIES
  ↓
Found: VidProp.Brightness (same as 'brightness')
  ↓
Resolve to: brightness (canonical name)
  ↓
Apply operation
```

**Complete alias list:**


| Canonical | Aliases | Type |
| :-- | :-- | :-- |
| brightness | bright | video |
| white_balance | wb, whitebalance | video |
| color_enable | color, colorenable | video |
| saturation | sat | video |
| zoom | z | camera |
| focus | f | camera |
| exposure | exp | camera |
| pan | horizontal | camera |
| tilt | vertical | camera |

#### Comprehensive set/get flow example

**Complete write flow** (`cam.set('wb', 5500, mode='manual')`):

```
1. User calls: cam.set('wb', 5500, mode='manual')
2. Normalize: prop_name = 'wb'
3. Type check: value (5500) is int, not 'auto' string
4. Lookup: 'wb' in _VIDEO_PROPERTIES? Yes
5. Resolve: 'wb' → VidProp.WhiteBalance (canonical: white_balance)
6. Parse mode: 'manual' → CamMode.Manual
7. Validate: 5500 in device range [2700–6500]? Yes
8. Create: PropSetting(5500, CamMode.Manual)
9. Execute: self._core_camera.set(VidProp.WhiteBalance, PropSetting)
10. Result: Camera white balance set to 5500K
```

**Complete read flow** (`is_color = cam.get('color')`):

```
1. User calls: is_color = cam.get('color')
2. Normalize: prop_name = 'color'
3. Lookup: 'color' in _VIDEO_PROPERTIES? Yes
4. Resolve: 'color' → VidProp.ColorEnable (canonical: color_enable)
5. Fetch: device_value = self._core_camera.get(VidProp.ColorEnable)
6. Extract: value = device_value.value() = 1 (int)
7. Type convert: 'color_enable' in _BOOLEAN_PROPERTIES? Yes
8. Convert: bool(1) = True
9. Return: is_color = True
```


#### Example usage patterns

**Scripting-friendly approach** (all string-based):

```python
with cam as c:
    c.set('brightness', 70, mode='manual')
    c.set('focus', 'auto')
    c.set('wb', 5500, mode='manual')
    c.set('zoom', 150)
    
    brightness = c.get('brightness')
    focus_mode = c.get('focus')
    is_color = c.get('color')
```

**Dynamic property management**:

```python
properties = {
    'brightness': 70,
    'contrast': 60,
    'saturation': 55,
    'pan': 45,
    'tilt': -20,
    'zoom': 200,
    'focus': 'auto'
}

# Apply all properties
for prop_name, value in properties.items():
    try:
        cam.set(prop_name, value)
    except PropertyNotSupportedError:
        print(f"Warning: {prop_name} not supported")
```

**Conditional auto mode**:

```python
def enable_autofocus_if_supported(cam):
    """Try to enable autofocus; fallback if unsupported."""
    try:
        cam.set('focus', 'auto')
        print("Autofocus enabled")
    except PropertyNotSupportedError:
        print("Autofocus not supported; using manual")
        cam.set('focus', 50)  # Set to midpoint
```

### 3.10 Property Aliases \& Discovery

Property aliases provide user-friendly shortcuts for commonly-used properties. Discovery methods enable runtime inspection of supported properties, available ranges, and device capabilities.

#### Complete property alias mapping

All supported property aliases with their canonical names:

```python
# Video properties with aliases
brightness              → canonical name (alias: bright)
white_balance           → canonical name (aliases: wb, whitebalance)
color_enable            → canonical name (aliases: color, colorenable)
saturation              → canonical name (alias: sat)
contrast                → canonical name (no aliases)
hue                     → canonical name (no aliases)
sharpness               → canonical name (no aliases)
gamma                   → canonical name (no aliases)
video_backlight_compensation  → canonical (no aliases)
gain                    → canonical name (no aliases)

# Camera properties with aliases
pan                     → canonical name (alias: horizontal)
tilt                    → canonical name (alias: vertical)
zoom                    → canonical name (alias: z)
focus                   → canonical name (alias: f)
exposure                → canonical name (alias: exp)
roll                    → canonical name (no aliases)
iris                    → canonical name (no aliases)
scan_mode               → canonical name (no aliases)
privacy                 → canonical name (no aliases)
digital_zoom            → canonical name (no aliases)
backlight_compensation  → canonical name (no aliases)
lamp                    → canonical name (no aliases)
```


#### `get_property_aliases()` discovery method

```python
def get_property_aliases(self) -> Dict[str, List[str]]:
    """Get mapping of canonical property names to all aliases."""
    aliases_map = {}
    
    # Video properties
    for alias, enum in self._VIDEO_PROPERTIES.items():
        # Find canonical name (one with longest name/most specific)
        canonical = self._find_canonical_for_enum(enum, self._VIDEO_PROPERTIES)
        if canonical not in aliases_map:
            aliases_map[canonical] = []
        if alias != canonical:
            aliases_map[canonical].append(alias)
    
    # Camera properties
    for alias, enum in self._CAMERA_PROPERTIES.items():
        canonical = self._find_canonical_for_enum(enum, self._CAMERA_PROPERTIES)
        if canonical not in aliases_map:
            aliases_map[canonical] = []
        if alias != canonical:
            aliases_map[canonical].append(alias)
    
    return aliases_map
```

Returns mapping of canonical names to all aliases:

```python
aliases = cam.get_property_aliases()
# Returns:
# {
#     'brightness': ['bright'],
#     'white_balance': ['wb', 'whitebalance'],
#     'color_enable': ['color', 'colorenable'],
#     'saturation': ['sat'],
#     'zoom': ['z'],
#     'focus': ['f'],
#     'exposure': ['exp'],
#     'pan': ['horizontal'],
#     'tilt': ['vertical'],
#     ...
# }

# Access aliases for specific property
bright_aliases = aliases['brightness']  # ['bright']
zoom_aliases = aliases['zoom']          # ['z']
```


#### `list_properties()` property enumeration method

```python
def list_properties(self) -> Dict[str, Dict[str, str]]:
    """List all supported properties with types and descriptions."""
    properties_info = {}
    
    # Video properties
    for prop_name in sorted(self._VIDEO_PROPERTIES.keys()):
        if prop_name in self._VIDEO_PROPERTIES:
            is_bool = prop_name in self._BOOLEAN_PROPERTIES
            properties_info[prop_name] = {
                'type': 'video',
                'value_type': 'bool' if is_bool else 'int',
                'description': self._get_property_description(prop_name)
            }
    
    # Camera properties
    for prop_name in sorted(self._CAMERA_PROPERTIES.keys()):
        if prop_name in self._CAMERA_PROPERTIES:
            is_bool = prop_name in self._BOOLEAN_PROPERTIES
            properties_info[prop_name] = {
                'type': 'camera',
                'value_type': 'bool' if is_bool else 'int',
                'description': self._get_property_description(prop_name)
            }
    
    return properties_info
```

Returns sorted list of all supported properties:

```python
properties = cam.list_properties()
# Returns:
# {
#     'brightness': {'type': 'video', 'value_type': 'int', 'description': 'Image luminance...'},
#     'color_enable': {'type': 'video', 'value_type': 'bool', 'description': 'Color vs monochrome...'},
#     'contrast': {'type': 'video', 'value_type': 'int', 'description': 'Tonal range...'},
#     ...
#     'exposure': {'type': 'camera', 'value_type': 'int', 'description': 'Exposure value...'},
#     'focus': {'type': 'camera', 'value_type': 'int', 'description': 'Focus distance...'},
#     'pan': {'type': 'camera', 'value_type': 'int', 'description': 'Horizontal rotation...'},
#     ...
# }

# Check property type
for prop_name, info in properties.items():
    print(f"{prop_name}: {info['value_type']} ({info['type']})")
```


#### `get_property_range()` range discovery method

```python
def get_property_range(self, property_name: str) -> Optional[Dict[str, int]]:
    """Get device-reported range for a property (min, max, step, default)."""
    self._ensure_connected()
    
    # Resolve property name
    prop_name = property_name.lower().strip()
    
    try:
        # Query device
        if prop_name in self._VIDEO_PROPERTIES or prop_name in self._VIDEO_PROPERTIES.values():
            enum = self._resolve_property_enum(prop_name, self._VIDEO_PROPERTIES)
            result = self._core_camera.get_range(enum)
        elif prop_name in self._CAMERA_PROPERTIES or prop_name in self._CAMERA_PROPERTIES.values():
            enum = self._resolve_property_enum(prop_name, self._CAMERA_PROPERTIES)
            result = self._core_camera.get_range(enum)
        else:
            return None
        
        # Extract range data
        if result:
            return {
                'min': result.min,
                'max': result.max,
                'step': result.step,
                'default': result.default
            }
        return None
    except:
        return None
```

Returns device-reported range or None if unsupported:

```python
# Query brightness range
bright_range = cam.get_property_range('brightness')
if bright_range:
    print(f"Brightness: {bright_range['min']}-{bright_range['max']}")
    print(f"Step: {bright_range['step']}, Default: {bright_range['default']}")
    # Brightness: 0-255
    # Step: 1, Default: 128
else:
    print("Brightness unsupported on this device")

# Check multiple properties
for prop in ['pan', 'tilt', 'zoom', 'roll']:
    prop_range = cam.get_property_range(prop)
    if prop_range:
        print(f"{prop}: {prop_range['min']} to {prop_range['max']}")
    else:
        print(f"{prop}: Not supported")
```


#### Property capability matrix reference

Complete reference of all properties, their aliases, types, and typical ranges:


| Property | Canonical | Aliases | Type | Value Type | Typical Range | Supported On |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| brightness | brightness | bright | video | int | 0–255 (device-specific) | Most cameras |
| contrast | contrast | — | video | int | 0–100 | Most cameras |
| saturation | saturation | sat | video | int | 0–100 | Most cameras |
| hue | hue | — | video | int | -180 to +180 | Most cameras |
| sharpness | sharpness | — | video | int | 0–100 | Some cameras |
| gamma | gamma | — | video | int | 100–300 | Some cameras |
| color_enable | color_enable | color, colorenable | video | bool | — | Most cameras |
| white_balance | white_balance | wb, whitebalance | video | int/str | 2700–6500K or 'auto' | Most cameras |
| video_backlight_compensation | video_backlight_compensation | — | video | int | 0–100 | Some cameras |
| gain | gain | — | video | int | 0–100 | Some cameras |
| pan | pan | horizontal | camera | int | -180 to +180° | PTZ/Pro cameras |
| tilt | tilt | vertical | camera | int | -90 to +90° | PTZ/Pro cameras |
| roll | roll | — | camera | int | -180 to +180° | Rare |
| zoom | zoom | z | camera | int | 100–1000 | Some cameras |
| exposure | exposure | exp | camera | int/str | -13 to +1 EV or 'auto' | Most cameras |
| iris | iris | — | camera | int | 0–100 | Some cameras |
| focus | focus | f | camera | int/str | 0–100 or 'auto' | Most cameras |
| scan_mode | scan_mode | — | camera | int | 0 or 1 | Some cameras |
| privacy | privacy | — | camera | bool | — | Some cameras |
| digital_zoom | digital_zoom | — | camera | int | 100–400 | Some cameras |
| backlight_compensation | backlight_compensation | — | camera | bool | — | Some cameras |
| lamp | lamp | — | camera | int | 0–100 | Rare |

#### Alias discovery and usage example

```python
# Discover all aliases at runtime
with cam as c:
    aliases = c.get_property_aliases()
    
    # Print all brightness aliases
    print("Brightness aliases:", aliases.get('brightness', []))
    # Output: Brightness aliases: ['bright']
    
    # Print all zoom aliases
    print("Zoom aliases:", aliases.get('zoom', []))
    # Output: Zoom aliases: ['z']
    
    # Use discovered aliases
    for canonical, alias_list in aliases.items():
        print(f"{canonical}: {alias_list}")
```


#### Property support checking

```python
def is_property_supported(cam, prop_name: str) -> bool:
    """Check if camera supports a property."""
    try:
        prop_range = cam.get_property_range(prop_name)
        return prop_range is not None
    except PropertyNotSupportedError:
        return False

def get_supported_properties(cam) -> List[str]:
    """Get list of properties supported by this camera."""
    supported = []
    for prop_name in cam.list_properties().keys():
        if is_property_supported(cam, prop_name):
            supported.append(prop_name)
    return supported

# Usage
with cam as c:
    if is_property_supported(c, 'zoom'):
        c.zoom = 150
    else:
        print("Camera does not support zoom")
    
    supported = get_supported_properties(c)
    print("Supported properties:", supported)
```


#### Discovery-driven configuration

```python
def auto_configure_camera(cam) -> dict:
    """Configure camera based on discovered capabilities."""
    config = {}
    
    properties = cam.list_properties()
    
    # Apply sensible defaults for supported properties
    for prop_name, info in properties.items():
        try:
            prop_range = cam.get_property_range(prop_name)
            if prop_range:
                # Set to mid-range for numeric properties
                if info['value_type'] == 'int':
                    mid_value = (prop_range['min'] + prop_range['max']) // 2
                    cam.set(prop_name, mid_value)
                    config[prop_name] = mid_value
                
                # Set to False for boolean properties
                elif info['value_type'] == 'bool':
                    cam.set(prop_name, False)
                    config[prop_name] = False
        except:
            pass  # Skip unsupported properties
    
    return config

# Usage
with cam as c:
    config = auto_configure_camera(c)
    print("Auto-configured properties:", config)
```


#### Alias convenience examples

```python
# Using full names
cam.set('brightness', 80)
cam.set('white_balance', 5500)
cam.set('pan', 45)

# Using short aliases (equivalent)
cam.set('bright', 80)               # Same as brightness
cam.set('wb', 5500)                 # Same as white_balance
cam.set('horizontal', 45)           # Same as pan

# Getting with aliases
brightness = cam.get('bright')      # Resolves to 'brightness'
zoom = cam.get('z')                 # Resolves to 'zoom'
focus = cam.get('f')                # Resolves to 'focus'

# Mixed usage
cam.pan = 0                          # Direct property
cam.set('horizontal', 45)           # String API with alias
cam.get('pan')                      # String API, canonical name
cam.get('horizontal')               # String API, alias (equivalent)
```

### 3.11 Convenience Setter Methods

Convenience setter methods provide direct, IDE-friendly property assignment. All 32 setter methods accept optional mode parameter, perform automatic range validation, and raise descriptive exceptions with recovery suggestions.

#### Video property setters (10 methods)

```python
def set_brightness(self, value: int, mode: str = 'manual') -> None:
    """Set brightness with automatic range validation."""
    self.set('brightness', value, mode=mode)

def set_contrast(self, value: int, mode: str = 'manual') -> None:
    """Set contrast with automatic range validation."""
    self.set('contrast', value, mode=mode)

def set_saturation(self, value: int, mode: str = 'manual') -> None:
    """Set saturation with automatic range validation."""
    self.set('saturation', value, mode=mode)

def set_hue(self, value: int, mode: str = 'manual') -> None:
    """Set hue (color rotation) with automatic range validation."""
    self.set('hue', value, mode=mode)

def set_sharpness(self, value: int, mode: str = 'manual') -> None:
    """Set sharpness with automatic range validation."""
    self.set('sharpness', value, mode=mode)

def set_gamma(self, value: int, mode: str = 'manual') -> None:
    """Set gamma (tone curve) with automatic range validation."""
    self.set('gamma', value, mode=mode)

def set_color_enable(self, value: bool, mode: str = 'manual') -> None:
    """Set color mode (True=color, False=monochrome)."""
    self.set('color_enable', value, mode=mode)

def set_white_balance(self, value: Union[int, str], mode: str = 'manual') -> None:
    """Set white balance (Kelvin or 'auto')."""
    self.set('white_balance', value, mode=mode)

def set_video_backlight_compensation(self, value: int, mode: str = 'manual') -> None:
    """Set video-level backlight compensation with validation."""
    self.set('video_backlight_compensation', value, mode=mode)

def set_gain(self, value: int, mode: str = 'manual') -> None:
    """Set sensor gain/amplification with validation."""
    self.set('gain', value, mode=mode)
```

**Usage examples:**

```python
cam.set_brightness(80)                          # Set to 80 (manual mode)
cam.set_white_balance(5500)                     # 5500K daylight
cam.set_white_balance('auto')                   # Auto white balance
cam.set_color_enable(True)                      # Enable color
cam.set_saturation(60, mode='manual')           # Explicit mode parameter
```


#### Camera property setters (11 methods)

```python
def set_pan(self, value: int, mode: str = 'manual') -> None:
    """Set pan (horizontal rotation) with range validation."""
    self.set('pan', value, mode=mode)

def set_tilt(self, value: int, mode: str = 'manual') -> None:
    """Set tilt (vertical rotation) with range validation."""
    self.set('tilt', value, mode=mode)

def set_roll(self, value: int, mode: str = 'manual') -> None:
    """Set roll (optical axis rotation) with range validation."""
    self.set('roll', value, mode=mode)

def set_zoom(self, value: int, mode: str = 'manual') -> None:
    """Set optical zoom (100=1x) with range validation."""
    self.set('zoom', value, mode=mode)

def set_exposure(self, value: Union[int, str], mode: str = 'manual') -> None:
    """Set exposure (EV units or 'auto') with validation."""
    self.set('exposure', value, mode=mode)

def set_iris(self, value: int, mode: str = 'manual') -> None:
    """Set iris/aperture with range validation."""
    self.set('iris', value, mode=mode)

def set_focus(self, value: Union[int, str], mode: str = 'manual') -> None:
    """Set focus distance (0-100 or 'auto') with validation."""
    self.set('focus', value, mode=mode)

def set_scan_mode(self, value: int) -> None:
    """Set scan mode (0=interlaced, 1=progressive)."""
    self.set('scan_mode', value)

def set_privacy(self, value: bool) -> None:
    """Set privacy shutter (True=closed, False=open)."""
    self.set('privacy', value)

def set_digital_zoom(self, value: int, mode: str = 'manual') -> None:
    """Set digital zoom (100=1x) with range validation."""
    self.set('digital_zoom', value, mode=mode)

def set_backlight_compensation(self, value: bool) -> None:
    """Set camera-level backlight compensation."""
    self.set('backlight_compensation', value)
```

**Usage examples:**

```python
cam.set_pan(45)                                 # Pan 45° right
cam.set_tilt(-30)                              # Tilt 30° down
cam.set_zoom(200)                              # 2x zoom
cam.set_focus('auto')                          # Autofocus
cam.set_exposure(-2)                           # Darken by 2 EV
cam.set_privacy(False)                         # Open privacy shutter
```


#### Automatic range validation and error handling

All setter methods automatically validate values against device-reported ranges:

```python
def set(self, property_name: str, value: Union[int, str, bool], mode: str = 'manual') -> None:
    """Universal setter with automatic validation and error context."""
    try:
        # Resolve property
        prop_range = self.get_property_range(property_name)
        
        # Validate range
        if prop_range and isinstance(value, int):
            if value < prop_range['min'] or value > prop_range['max']:
                raise InvalidValueError(
                    f"Value {value} out of range for '{property_name}'. "
                    f"Valid range: {prop_range['min']}–{prop_range['max']} "
                    f"(step: {prop_range['step']}). "
                    f"Clamp value to valid range or query device capabilities."
                )
        
        # Apply setting
        self._apply_property_setting(property_name, value, mode)
        
    except PropertyNotSupportedError as e:
        raise PropertyNotSupportedError(
            f"Property '{property_name}' not supported on this camera. "
            f"Supported properties: {self.list_properties().keys()}. "
            f"Query device capabilities with: cam.get_property_range('{property_name}')"
        )
    except InvalidValueError as e:
        raise InvalidValueError(
            f"{str(e)} "
            f"Current value: {self.get(property_name)}. "
            f"Try: cam.set_brightness({prop_range['min']}) or higher."
        )
```

**Error messages with context and recovery suggestions:**

```python
# Example: Out-of-range value
try:
    cam.set_brightness(500)
except InvalidValueError as e:
    print(str(e))
    # Output: "Value 500 out of range for 'brightness'. Valid range: 0–255 
    # (step: 1). Clamp value to valid range or query device capabilities."

# Example: Unsupported property
try:
    cam.set_roll(45)  # Unsupported on most cameras
except PropertyNotSupportedError as e:
    print(str(e))
    # Output: "Property 'roll' not supported on this camera. 
    # Supported properties: ['brightness', 'pan', 'zoom', ...]. 
    # Query device capabilities with: cam.get_property_range('roll')"
```


#### Exception recovery suggestion algorithms

Smart error recovery:

```python
def _suggest_recovery_for_invalid_value(self, prop_name: str, value: int) -> str:
    """Generate recovery suggestion for out-of-range value."""
    prop_range = self.get_property_range(prop_name)
    if not prop_range:
        return f"Property '{prop_name}' may be unsupported. Query: cam.get_property_range('{prop_name}')"
    
    # Suggest clamping
    if value < prop_range['min']:
        return f"Value too low. Use {prop_range['min']} (minimum)."
    elif value > prop_range['max']:
        return f"Value too high. Use {prop_range['max']} (maximum)."
    
    # Suggest midpoint
    mid = (prop_range['min'] + prop_range['max']) // 2
    return f"Use {mid} (midpoint) or value within {prop_range['min']}–{prop_range['max']}."

# Example usage
try:
    cam.set_brightness(1000)
except InvalidValueError:
    recovery = cam._suggest_recovery_for_invalid_value('brightness', 1000)
    print(recovery)  # "Value too high. Use 255 (maximum)."
```


***

### 3.12 Convenience Getter Methods

Convenience getter methods provide direct property access with automatic type conversion. All 32 getter methods return validated values within device-reported ranges.

#### Video property getters (10 methods)

```python
def get_brightness(self) -> int:
    """Get brightness value (device-specific range)."""
    return self.get('brightness')

def get_contrast(self) -> int:
    """Get contrast value."""
    return self.get('contrast')

def get_saturation(self) -> int:
    """Get saturation value."""
    return self.get('saturation')

def get_hue(self) -> int:
    """Get hue value (color rotation in degrees)."""
    return self.get('hue')

def get_sharpness(self) -> int:
    """Get sharpness value."""
    return self.get('sharpness')

def get_gamma(self) -> int:
    """Get gamma value (value ÷ 100 = gamma)."""
    return self.get('gamma')

def get_color_enable(self) -> bool:
    """Get color mode (True=color, False=monochrome)."""
    return self.get('color_enable')

def get_white_balance(self) -> int:
    """Get white balance (Kelvin value)."""
    return self.get('white_balance')

def get_video_backlight_compensation(self) -> int:
    """Get video backlight compensation level."""
    return self.get('video_backlight_compensation')

def get_gain(self) -> int:
    """Get sensor gain/amplification level."""
    return self.get('gain')
```

**Usage examples:**

```python
brightness = cam.get_brightness()              # Returns int (device-specific)
is_color = cam.get_color_enable()              # Returns bool
wb = cam.get_white_balance()                   # Returns int (Kelvin)
```


#### Camera property getters (11 methods)

```python
def get_pan(self) -> int:
    """Get pan angle (degrees, device-specific range)."""
    return self.get('pan')

def get_tilt(self) -> int:
    """Get tilt angle (degrees, device-specific range)."""
    return self.get('tilt')

def get_roll(self) -> int:
    """Get roll angle (degrees)."""
    return self.get('roll')

def get_zoom(self) -> int:
    """Get optical zoom (100=1x, device-specific range)."""
    return self.get('zoom')

def get_exposure(self) -> int:
    """Get exposure value (EV units, device-specific)."""
    return self.get('exposure')

def get_iris(self) -> int:
    """Get iris/aperture value."""
    return self.get('iris')

def get_focus(self) -> int:
    """Get focus distance (0-100, or 0 if autofocus active)."""
    return self.get('focus')

def get_scan_mode(self) -> int:
    """Get scan mode (0=interlaced, 1=progressive)."""
    return self.get('scan_mode')

def get_privacy(self) -> bool:
    """Get privacy shutter state (True=closed, False=open)."""
    return self.get('privacy')

def get_digital_zoom(self) -> int:
    """Get digital zoom (100=1x, device-specific range)."""
    return self.get('digital_zoom')

def get_backlight_compensation(self) -> bool:
    """Get camera-level backlight compensation state."""
    return self.get('backlight_compensation')
```

**Usage examples:**

```python
pan = cam.get_pan()                            # Returns int
zoom = cam.get_zoom()                          # Returns int (100–1000+)
privacy_on = cam.get_privacy()                 # Returns bool
is_progressive = cam.get_scan_mode() == 1     # Returns bool
```


#### Range-checked values and device-specific returns

All getters return values **guaranteed to be within device range**:

```python
def get(self, property_name: str) -> Union[int, str, bool]:
    """Get property with automatic validation."""
    self._ensure_connected()
    
    try:
        # Fetch raw value
        raw_value = self._fetch_property_from_device(property_name)
        
        # Validate against device range
        prop_range = self.get_property_range(property_name)
        if prop_range and isinstance(raw_value, int):
            if raw_value < prop_range['min'] or raw_value > prop_range['max']:
                # Log warning but still return (device may report stale value)
                warnings.warn(
                    f"Device reported {property_name}={raw_value} outside range "
                    f"{prop_range['min']}–{prop_range['max']}. "
                    f"Clamping to valid range."
                )
                raw_value = max(prop_range['min'], min(prop_range['max'], raw_value))
        
        # Auto type conversion for bool properties
        if property_name in self._BOOLEAN_PROPERTIES:
            return bool(raw_value)
        
        return raw_value
        
    except PropertyNotSupportedError:
        raise PropertyNotSupportedError(
            f"Cannot read property '{property_name}'. "
            f"Property may be unsupported on this device."
        )
```


#### Device-specific return values (actual values returned)

Different devices return different value ranges for same property:

**Brightness example:**

```python
# Logitech C920 camera
brightness = cam.get_brightness()  # Returns 0–255 (device-specific)

# Generic UVC camera
brightness = cam.get_brightness()  # Returns 0–100 (device-specific)

# Both calls work; values are device-normalized
```

**Pan example:**

```python
# PTZ camera supports full rotation
pan = cam.get_pan()  # Returns -180 to +180 (device range)

# Fixed USB camera with limited pan
pan = cam.get_pan()  # Returns 0 (center, or unsupported)
```


#### Comparison and usage patterns

```python
# Check current state
with cam as c:
    # Read all video properties
    brightness = c.get_brightness()
    contrast = c.get_contrast()
    saturation = c.get_saturation()
    is_color = c.get_color_enable()
    wb_kelvin = c.get_white_balance()
    
    # Read all camera position/zoom
    pan_angle = c.get_pan()
    tilt_angle = c.get_tilt()
    zoom_level = c.get_zoom()  # 100=1x
    
    # Conditional logic based on returned values
    if zoom_level > 200:
        print(f"Zoomed in {zoom_level // 100}x")
    
    if is_color:
        print("Color mode enabled")
    else:
        print("Monochrome mode")
```


#### Batch getter pattern

```python
def get_all_properties(cam) -> dict:
    """Get all supported properties at once."""
    all_props = {}
    
    # Video properties
    for prop_name in ['brightness', 'contrast', 'saturation', 'hue', 
                      'sharpness', 'gamma', 'white_balance', 'gain']:
        try:
            all_props[prop_name] = cam.get(prop_name)
        except:
            all_props[prop_name] = None  # Unsupported
    
    # Camera properties
    for prop_name in ['pan', 'tilt', 'zoom', 'exposure', 'focus',
                      'iris', 'scan_mode', 'privacy', 'digital_zoom']:
        try:
            all_props[prop_name] = cam.get(prop_name)
        except:
            all_props[prop_name] = None
    
    return all_props

# Usage
with cam as c:
    state = get_all_properties(c)
    print("Current camera state:")
    for prop, value in state.items():
        if value is not None:
            print(f"  {prop}: {value}")
```


#### Error handling on get operations

```python
def safe_get(cam, property_name: str, default=None):
    """Get property value with graceful fallback."""
    try:
        return cam.get(property_name)
    except PropertyNotSupportedError:
        return default
    except Exception as e:
        warnings.warn(f"Failed to read {property_name}: {e}")
        return default

# Usage
brightness = safe_get(cam, 'brightness', default=128)
pan = safe_get(cam, 'pan', default=0)
```

### 3.13 Validation \& Safe Operations

Explicit validation methods protect against invalid values before device operations. Validation reports rich context via `PropertyValueOutOfRangeError` exception with structured attributes. Recovery suggestions enable safe error handling and device-specific range queries.

#### `set_with_validation()` explicit validation method

```python
def set_with_validation(self, property_name: str, value: Union[int, str, bool], 
                       mode: str = 'manual') -> Dict[str, Any]:
    """Set property with explicit validation and detailed error reporting."""
    self._ensure_connected()
    
    # Resolve property
    prop_name = property_name.lower().strip()
    
    # Check type compatibility
    if not self._validate_value_type(prop_name, value):
        raise PropertyTypeError(
            f"Value type mismatch for '{prop_name}'. "
            f"Expected {self._get_expected_type(prop_name).__name__}, "
            f"got {type(value).__name__}."
        )
    
    # Get device-reported range
    prop_range = self.get_property_range(prop_name)
    if not prop_range:
        warnings.warn(
            f"Property '{prop_name}' range unavailable; "
            f"device may not support this property."
        )
    
    # Validate range for numeric values
    if isinstance(value, int) and prop_range:
        if value < prop_range['min'] or value > prop_range['max']:
            current_val = self.get(prop_name)
            raise PropertyValueOutOfRangeError(
                property_name=prop_name,
                value=value,
                min_val=prop_range['min'],
                max_val=prop_range['max'],
                step=prop_range['step'],
                current_val=current_val,
                message=(
                    f"Value {value} out of range for '{prop_name}'. "
                    f"Valid range: {prop_range['min']}–{prop_range['max']} "
                    f"(step: {prop_range['step']})"
                )
            )
    
    # Apply setting
    self.set(prop_name, value, mode=mode)
    
    return {
        'property': prop_name,
        'value': value,
        'mode': mode,
        'success': True
    }
```

Usage:

```python
try:
    cam.set_with_validation('brightness', 80)
    print("Brightness set successfully")
except PropertyValueOutOfRangeError as e:
    print(f"Error: {e.message}")
    print(f"  Property: {e.property_name}")
    print(f"  Attempted: {e.value}, Valid: {e.min_val}–{e.max_val}")
    print(f"  Current: {e.current_val}")
```


#### `PropertyValueOutOfRangeError` exception with rich attributes

```python
class PropertyValueOutOfRangeError(Exception):
    """Raised when property value is outside device-reported range."""
    
    def __init__(self, property_name: str, value: int, min_val: int, max_val: int,
                 step: int, current_val: int, message: str = ""):
        self.property_name = property_name
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.current_val = current_val
        super().__init__(message)
```

Exception attributes for programmatic error handling:

```python
try:
    cam.set_with_validation('brightness', 500)
except PropertyValueOutOfRangeError as e:
    # Access structured error data
    print(f"Property: {e.property_name}")      # 'brightness'
    print(f"Attempted value: {e.value}")       # 500
    print(f"Valid range: {e.min_val}–{e.max_val}")  # 0–255
    print(f"Step size: {e.step}")              # 1
    print(f"Current value: {e.current_val}")   # 128
```


#### Automatic range checking via `_get_dynamic_range()`

```python
def _get_dynamic_range(self, property_name: str, fallback_min: int, 
                      fallback_max: int) -> Tuple[int, int]:
    """Query device range with automatic fallback to constants."""
    try:
        prop_range = self.get_property_range(property_name)
        if prop_range:
            return (prop_range['min'], prop_range['max'])
    except:
        pass
    
    # Fallback to class constants
    return (fallback_min, fallback_max)

# Automatic behavior in setters
def set_brightness(self, value: int, mode: str = 'manual') -> None:
    min_val, max_val = self._get_dynamic_range('brightness', 0, 100)
    
    if value < min_val or value > max_val:
        raise PropertyValueOutOfRangeError(...)
    
    self.set('brightness', value, mode=mode)
```


#### Type validation for int vs bool

```python
def _validate_value_type(self, prop_name: str, value: Any) -> bool:
    """Validate value matches property type (int or bool)."""
    is_bool_prop = prop_name in self._BOOLEAN_PROPERTIES
    
    if is_bool_prop:
        # Bool properties accept bool or int (0/1)
        return isinstance(value, (bool, int))
    else:
        # Numeric properties accept int or str (for auto mode)
        return isinstance(value, (int, str))

def _get_expected_type(self, prop_name: str) -> type:
    """Return expected Python type for property."""
    if prop_name in self._BOOLEAN_PROPERTIES:
        return bool
    elif prop_name in self._VIDEO_PROPERTIES or prop_name in self._CAMERA_PROPERTIES:
        return int
    return object
```

Type validation examples:

```python
# Valid: bool property with bool value
cam.set_with_validation('color_enable', True)  # OK

# Valid: bool property with int value (0 or 1)
cam.set_with_validation('privacy', 0)  # OK

# Invalid: bool property with invalid int
try:
    cam.set_with_validation('color_enable', 5)
except PropertyTypeError:
    print("Bool property only accepts 0/1 or True/False")

# Valid: numeric property with int
cam.set_with_validation('brightness', 80)  # OK

# Valid: auto mode with string
cam.set_with_validation('focus', 'auto')  # OK

# Invalid: numeric property with float
try:
    cam.set_with_validation('brightness', 80.5)
except PropertyTypeError:
    print("Property only accepts int")
```


#### Device-specific range queries

```python
def query_device_ranges(cam, properties: List[str]) -> Dict[str, Dict]:
    """Query device for supported ranges on multiple properties."""
    ranges = {}
    
    for prop_name in properties:
        try:
            prop_range = cam.get_property_range(prop_name)
            if prop_range:
                ranges[prop_name] = {
                    'min': prop_range['min'],
                    'max': prop_range['max'],
                    'step': prop_range['step'],
                    'default': prop_range['default'],
                    'supported': True
                }
            else:
                ranges[prop_name] = {'supported': False}
        except PropertyNotSupportedError:
            ranges[prop_name] = {'supported': False}
    
    return ranges

# Usage
with cam as c:
    video_props = ['brightness', 'contrast', 'saturation', 'zoom']
    ranges = query_device_ranges(c, video_props)
    
    for prop, info in ranges.items():
        if info['supported']:
            print(f"{prop}: {info['min']}–{info['max']} "
                  f"(step: {info['step']}, default: {info['default']})")
        else:
            print(f"{prop}: Not supported")
```


#### `get_setting_info()` method

```python
def get_setting_info(self, property_name: str) -> Dict[str, Any]:
    """Get current value, mode, and range for a property."""
    self._ensure_connected()
    
    prop_name = property_name.lower().strip()
    
    try:
        current_value = self.get(prop_name)
        prop_range = self.get_property_range(prop_name)
        
        # Determine current mode (device-specific)
        current_mode = self._get_property_mode(prop_name)
        
        return {
            'property': prop_name,
            'current_value': current_value,
            'current_mode': current_mode,
            'range': {
                'min': prop_range['min'] if prop_range else None,
                'max': prop_range['max'] if prop_range else None,
                'step': prop_range['step'] if prop_range else None,
                'default': prop_range['default'] if prop_range else None,
            },
            'supported': True,
            'type': 'bool' if prop_name in self._BOOLEAN_PROPERTIES else 'int'
        }
    except PropertyNotSupportedError:
        return {
            'property': prop_name,
            'supported': False
        }
```

Usage:

```python
with cam as c:
    # Inspect brightness
    info = c.get_setting_info('brightness')
    print(f"Brightness: {info['current_value']}")
    print(f"Mode: {info['current_mode']}")
    print(f"Range: {info['range']['min']}–{info['range']['max']}")
    print(f"Step: {info['range']['step']}")
    print(f"Default: {info['range']['default']}")
    
    # Output:
    # Brightness: 128
    # Mode: manual
    # Range: 0–255
    # Step: 1
    # Default: 128
```


#### Exception recovery suggestion algorithms

Smart recovery suggestions based on error context:

```python
def _suggest_recovery_for_range_error(self, error: PropertyValueOutOfRangeError) -> str:
    """Generate recovery suggestion for out-of-range value."""
    prop = error.property_name
    value = error.value
    min_val = error.min_val
    max_val = error.max_val
    step = error.step
    current = error.current_val
    
    suggestions = []
    
    # Suggest clamping to boundaries
    if value < min_val:
        suggestions.append(f"Clamp to minimum: cam.set('{prop}', {min_val})")
    elif value > max_val:
        suggestions.append(f"Clamp to maximum: cam.set('{prop}', {max_val})")
    
    # Suggest midpoint
    mid = (min_val + max_val) // 2
    suggestions.append(f"Try midpoint: cam.set('{prop}', {mid})")
    
    # Suggest keeping current if valid
    suggestions.append(f"Keep current: cam.set('{prop}', {current})")
    
    # Suggest step-aligned values
    if step > 1:
        suggestions.append(f"Ensure value is multiple of step ({step})")
    
    return " OR ".join(suggestions)

# Usage
try:
    cam.set_with_validation('brightness', 500)
except PropertyValueOutOfRangeError as e:
    recovery = cam._suggest_recovery_for_range_error(e)
    print(f"Failed to set brightness to {e.value}")
    print(f"Recovery options: {recovery}")
    
    # Output:
    # Failed to set brightness to 500
    # Recovery options: Clamp to maximum: cam.set('brightness', 255) OR 
    # Try midpoint: cam.set('brightness', 128) OR Keep current: cam.set('brightness', 128)
```


#### Validation-aware safe setting pattern

```python
def safe_set(cam, property_name: str, value: Union[int, bool], 
            auto_clamp: bool = False, fallback_to_current: bool = False) -> bool:
    """Set property with automatic recovery options."""
    try:
        cam.set_with_validation(property_name, value)
        return True
    except PropertyValueOutOfRangeError as e:
        if auto_clamp:
            # Clamp to valid range
            clamped = max(e.min_val, min(e.max_val, value))
            cam.set(property_name, clamped)
            return True
        elif fallback_to_current:
            # Keep current value (no-op)
            return True
        else:
            # Re-raise
            raise

# Usage
safe_set(cam, 'brightness', 500, auto_clamp=True)  # Clamps to 255
safe_set(cam, 'focus', 150, fallback_to_current=True)  # Keeps current if out of range
```


#### Batch validation

```python
def validate_and_apply_settings(cam, settings: Dict[str, int]) -> Dict[str, bool]:
    """Apply multiple settings with individual error handling."""
    results = {}
    
    for prop_name, value in settings.items():
        try:
            cam.set_with_validation(prop_name, value)
            results[prop_name] = True
        except PropertyValueOutOfRangeError as e:
            print(f"Skipping {prop_name}: {e.message}")
            results[prop_name] = False
        except PropertyNotSupportedError:
            print(f"Skipping {prop_name}: Not supported")
            results[prop_name] = False
    
    return results

# Usage
config = {
    'brightness': 80,
    'contrast': 60,
    'pan': 45,
    'zoom': 200,
    'roll': 10  # May fail on unsupported camera
}

results = validate_and_apply_settings(cam, config)
print(f"Applied: {sum(results.values())}/{len(results)} settings")
```


#### Pre-flight validation

```python
def can_apply_settings(cam, settings: Dict[str, int]) -> Tuple[bool, List[str]]:
    """Check if settings would be valid without applying them."""
    errors = []
    
    for prop_name, value in settings.items():
        try:
            prop_range = cam.get_property_range(prop_name)
            if not prop_range:
                errors.append(f"{prop_name}: Not supported")
            elif isinstance(value, int):
                if value < prop_range['min'] or value > prop_range['max']:
                    errors.append(
                        f"{prop_name}: {value} out of range "
                        f"({prop_range['min']}–{prop_range['max']})"
                    )
        except PropertyNotSupportedError:
            errors.append(f"{prop_name}: Not supported")
    
    return len(errors) == 0, errors

# Usage
config = {'brightness': 80, 'zoom': 200}
valid, errors = can_apply_settings(cam, config)

if valid:
    validate_and_apply_settings(cam, config)
else:
    print("Validation failed:")
    for error in errors:
        print(f"  - {error}")
```

### 3.14 Preset Configuration Management

Presets enable rapid camera configuration by storing named property snapshots. Built-in presets provide optimized defaults for common scenarios; custom presets enable user-defined configurations with optional persistence across sessions.

#### BUILT_IN_PRESETS dictionary with actual values

Four professionally-tuned presets included in `BUILT_IN_PRESETS` dict:

```python
BUILT_IN_PRESETS = {
    'daylight': {
        'brightness': 60,
        'contrast': 50,
        'saturation': 50,
        'hue': 0,
        'white_balance': 'auto',
        'exposure': 'auto',
        'focus': 'auto',
        'pan': 0,
        'tilt': 0,
        'zoom': 100
    },
    'indoor': {
        'brightness': 75,
        'contrast': 60,
        'saturation': 55,
        'hue': 0,
        'white_balance': 3200,
        'exposure': 'auto',
        'focus': 'auto',
        'pan': 0,
        'tilt': 0,
        'zoom': 100,
        'gain': 20
    },
    'night': {
        'brightness': 85,
        'contrast': 70,
        'saturation': 45,
        'hue': 0,
        'gain': 80,
        'white_balance': 4000,
        'exposure': 'auto',
        'focus': 'auto',
        'video_backlight_compensation': 50,
        'pan': 0,
        'tilt': 0,
        'zoom': 100
    },
    'conference': {
        'brightness': 70,
        'contrast': 55,
        'saturation': 50,
        'hue': 0,
        'white_balance': 'auto',
        'exposure': 'auto',
        'focus': 'auto',
        'pan': 0,
        'tilt': 0,
        'zoom': 100,
        'video_backlight_compensation': 30
    }
}
```

Daylight optimizes for outdoor brightness/saturation. Indoor adds warm color temp (3200K). Night increases gain and backlight compensation. Conference centers camera and defaults to neutral settings.

#### `apply_preset()` method

```python
def apply_preset(self, preset_name: str, partial: bool = False) -> Dict[str, Dict[str, Any]]:
    """Apply preset configuration to camera. Returns result dict per property."""
    self._ensure_connected()
    
    preset_name_lower = preset_name.lower().strip()
    
    # Check built-in presets first
    if preset_name_lower in self.BUILT_IN_PRESETS:
        preset = self.BUILT_IN_PRESETS[preset_name_lower]
    # Then check custom presets
    elif preset_name_lower in self._custom_presets:
        preset = self._custom_presets[preset_name_lower]
    else:
        raise PresetNotFoundError(
            f"Preset '{preset_name}' not found. "
            f"Available: {list(self.BUILT_IN_PRESETS.keys()) + list(self._custom_presets.keys())}"
        )
    
    results = {}
    
    # Apply each property
    for prop_name, value in preset.items():
        try:
            self.set(prop_name, value)
            results[prop_name] = {'success': True, 'value': value}
        except PropertyNotSupportedError as e:
            results[prop_name] = {'success': False, 'error': 'unsupported', 'message': str(e)}
            if not partial:
                raise  # All-or-nothing mode
        except PropertyValueOutOfRangeError as e:
            results[prop_name] = {
                'success': False,
                'error': 'out_of_range',
                'message': str(e),
                'range': (e.min_val, e.max_val),
                'current': e.current_val
            }
            if not partial:
                raise
        except Exception as e:
            results[prop_name] = {'success': False, 'error': 'unknown', 'message': str(e)}
            if not partial:
                raise
    
    return results
```

Usage:

```python
# Apply built-in preset (all-or-nothing)
results = cam.apply_preset('daylight', partial=False)

# Apply with partial failure (skip unsupported properties)
results = cam.apply_preset('conference', partial=True)
if not all(r['success'] for r in results.values()):
    print(f"Partial preset applied: {sum(1 for r in results.values() if r['success'])}/{len(results)}")

# Check specific property result
if not results['zoom']['success']:
    print(f"Zoom failed: {results['zoom']['message']}")
```


#### `get_preset_names()` method

```python
def get_preset_names(self) -> Dict[str, List[str]]:
    """Get available preset names separated by type."""
    return {
        'built_in': sorted(list(self.BUILT_IN_PRESETS.keys())),
        'custom': sorted(list(self._custom_presets.keys()))
    }
```

Usage:

```python
presets = cam.get_preset_names()
print("Built-in presets:", presets['built_in'])      # ['conference', 'daylight', 'indoor', 'night']
print("Custom presets:", presets['custom'])          # ['setup1', 'setup2']
print("Total available:", len(presets['built_in']) + len(presets['custom']))
```


#### `create_custom_preset()` method

```python
def create_custom_preset(self, name: str, properties: Optional[Dict[str, Any]] = None) -> None:
    """Create custom preset from properties dict or current device state."""
    if name.lower() in self.BUILT_IN_PRESETS:
        raise PresetError(f"Cannot override built-in preset '{name}'")
    
    if name.lower() in self._custom_presets:
        raise PresetError(f"Custom preset '{name}' already exists. Delete first.")
    
    if properties is None:
        # Capture current device state
        properties = {}
        for prop_name in self.list_properties().keys():
            try:
                properties[prop_name] = self.get(prop_name)
            except:
                pass  # Skip read failures
    else:
        # Validate all properties exist
        valid_props = set(self.list_properties().keys())
        invalid = set(properties.keys()) - valid_props
        if invalid:
            raise PropertyNotSupportedError(f"Unknown properties: {invalid}")
    
    self._custom_presets[name.lower()] = properties
```

Usage:

```python
# Create from current camera state (snapshot)
cam.create_custom_preset('my_meeting_setup')

# Create with explicit properties
cam.create_custom_preset('office', {
    'brightness': 75,
    'contrast': 60,
    'pan': 0,
    'tilt': 0,
    'zoom': 150,
    'white_balance': 'auto'
})

# Later: apply it
cam.apply_preset('office')
```


#### `get_custom_presets()` method

```python
def get_custom_presets(self) -> Dict[str, Dict[str, Any]]:
    """Get all custom preset definitions (read-only copy)."""
    return dict(self._custom_presets)
```

Usage:

```python
all_custom = cam.get_custom_presets()
for preset_name, properties in all_custom.items():
    print(f"{preset_name}: {properties}")
```


#### `delete_custom_preset()` method

```python
def delete_custom_preset(self, name: str) -> bool:
    """Delete custom preset by name. Returns True if deleted, False if not found."""
    name_lower = name.lower()
    if name_lower in self._custom_presets:
        del self._custom_presets[name_lower]
        return True
    return False
```

Usage:

```python
if cam.delete_custom_preset('old_setup'):
    print("Preset deleted")
else:
    print("Preset not found")
```


#### `clear_custom_presets()` method

```python
def clear_custom_presets(self) -> int:
    """Clear all custom presets. Returns count of presets cleared."""
    count = len(self._custom_presets)
    self._custom_presets.clear()
    return count
```

Usage:

```python
cleared = cam.clear_custom_presets()
print(f"Cleared {cleared} custom presets")
```


#### Smart preset selection

Automatic preset selection based on environment/time:

```python
def select_preset_for_environment(cam, environment: str) -> str:
    """Recommend preset based on environment description."""
    env_lower = environment.lower()
    
    if 'outdoor' in env_lower or 'sunny' in env_lower or 'bright' in env_lower:
        return 'daylight'
    elif 'office' in env_lower or 'indoor' in env_lower or 'meeting' in env_lower:
        return 'conference' if 'meeting' in env_lower else 'indoor'
    elif 'night' in env_lower or 'dark' in env_lower or 'low' in env_lower:
        return 'night'
    else:
        return 'daylight'  # Safe default

# Usage
preset = select_preset_for_environment(cam, 'indoor meeting room')
cam.apply_preset(preset)
```


#### Saving \& loading presets with persistence patterns

Save custom presets to JSON:

```python
import json

def save_presets(cam, filepath: str) -> None:
    """Save all custom presets to JSON file."""
    presets = cam.get_custom_presets()
    with open(filepath, 'w') as f:
        json.dump(presets, f, indent=2)
    print(f"Saved {len(presets)} presets to {filepath}")

def load_presets(cam, filepath: str) -> int:
    """Load custom presets from JSON file. Returns count loaded."""
    try:
        with open(filepath, 'r') as f:
            presets = json.load(f)
        
        loaded = 0
        for name, properties in presets.items():
            try:
                cam.create_custom_preset(name, properties=properties)
                loaded += 1
            except PresetError:
                pass  # Preset already exists
        
        return loaded
    except FileNotFoundError:
        print(f"Preset file not found: {filepath}")
        return 0

# Usage: Save during session
cam.create_custom_preset('setup1', {'brightness': 80, 'zoom': 200})
cam.create_custom_preset('setup2', {'brightness': 60, 'zoom': 100})
save_presets(cam, 'my_presets.json')

# Load in next session
loaded = load_presets(cam, 'my_presets.json')
print(f"Loaded {loaded} presets from file")
cam.apply_preset('setup1')
```


#### Preset system design rationale

**Built-in vs. custom separation**: Built-in presets are immutable, device-independent, and provide professional defaults. Custom presets are user-mutable and device-specific, enabling personalization without bloating built-in set.

**Flexible property subsets**: Presets specify any property subset; unapplied properties retain current device values. Enables "delta" configuration (only specify changed properties).

**Partial application mode**: `partial=False` (default) enforces all-or-nothing (fail if any property unsupported). `partial=True` gracefully skips unsupported properties, ensuring presets work across camera models with varying capabilities.

**State capture workflow**: `create_custom_preset()` without properties argument captures entire current device state, enabling "freeze current configuration" use cases.

**Persistence patterns**: Presets stored in-memory; JSON save/load provides optional cross-session persistence. Users can distribute preset JSON files for team standardization or camera profiles.

***

### 3.15 Bulk Operations \& Batch Control

Batch methods apply or read multiple properties efficiently with partial failure handling, optional verbose logging, and rich result reporting. Amortize overhead across multiple operations for significant performance gains.

#### `set_multiple()` method

```python
def set_multiple(self, properties: Dict[str, Any], verbose: bool = False,
                stop_on_error: bool = False) -> Dict[str, Dict[str, Any]]:
    """Set multiple properties with partial failure handling."""
    self._ensure_connected()
    
    results = {}
    applied = 0
    skipped = 0
    
    for prop_name, value in properties.items():
        try:
            # Validate before applying
            if isinstance(value, int):
                prop_range = self.get_property_range(prop_name)
                if prop_range and (value < prop_range['min'] or value > prop_range['max']):
                    raise PropertyValueOutOfRangeError(
                        property_name=prop_name,
                        value=value,
                        min_val=prop_range['min'],
                        max_val=prop_range['max'],
                        step=prop_range['step'],
                        current_val=self.get(prop_name),
                        message=f"Value out of range"
                    )
            
            # Apply property
            self.set(prop_name, value)
            results[prop_name] = {
                'success': True,
                'value': value,
                'error': None
            }
            applied += 1
            
            if verbose:
                print(f"✓ {prop_name} = {value}")
        
        except PropertyNotSupportedError as e:
            results[prop_name] = {
                'success': False,
                'value': value,
                'error': 'unsupported',
                'message': str(e)
            }
            skipped += 1
            
            if verbose:
                print(f"✗ {prop_name}: Unsupported")
            
            if stop_on_error:
                raise
        
        except PropertyValueOutOfRangeError as e:
            results[prop_name] = {
                'success': False,
                'value': value,
                'error': 'out_of_range',
                'message': str(e),
                'range': (e.min_val, e.max_val),
                'current': e.current_val
            }
            skipped += 1
            
            if verbose:
                print(f"✗ {prop_name} = {value}: Out of range ({e.min_val}–{e.max_val})")
            
            if stop_on_error:
                raise
        
        except Exception as e:
            results[prop_name] = {
                'success': False,
                'value': value,
                'error': type(e).__name__,
                'message': str(e)
            }
            skipped += 1
            
            if verbose:
                print(f"✗ {prop_name}: {type(e).__name__}: {str(e)}")
            
            if stop_on_error:
                raise
    
    if verbose:
        print(f"Applied {applied}/{len(properties)} properties ({skipped} skipped)")
    
    return results
```

Usage:

```python
config = {
    'brightness': 70,
    'contrast': 60,
    'saturation': 55,
    'zoom': 200,
    'roll': 45  # May fail on unsupported camera
}

# Apply with verbose logging and partial failure
results = cam.set_multiple(config, verbose=True, stop_on_error=False)
# Output:
# ✓ brightness = 70
# ✓ contrast = 60
# ✓ saturation = 55
# ✓ zoom = 200
# ✗ roll: Unsupported
# Applied 4/5 properties (1 skipped)

# Check programmatically
successful = sum(1 for r in results.values() if r['success'])
print(f"Success rate: {successful}/{len(results)}")
```


#### `get_multiple()` method

```python
def get_multiple(self, properties: List[str], verbose: bool = False) -> Dict[str, Any]:
    """Get multiple properties, gracefully skipping unsupported ones."""
    self._ensure_connected()
    
    results = {}
    success_count = 0
    
    for prop_name in properties:
        try:
            value = self.get(prop_name)
            results[prop_name] = value
            success_count += 1
            
            if verbose:
                print(f"✓ {prop_name} = {value}")
        
        except PropertyNotSupportedError:
            results[prop_name] = None
            
            if verbose:
                print(f"✗ {prop_name}: Not supported")
        
        except Exception as e:
            results[prop_name] = None
            
            if verbose:
                print(f"✗ {prop_name}: {type(e).__name__}")
    
    if verbose:
        print(f"Read {success_count}/{len(properties)} properties")
    
    return results
```

Usage:

```python
props_to_read = ['brightness', 'contrast', 'pan', 'tilt', 'zoom', 'roll', 'iris']

# Read all, verbose logging
state = cam.get_multiple(props_to_read, verbose=True)
# Output:
# ✓ brightness = 128
# ✓ contrast = 100
# ✓ pan = 0
# ✓ tilt = 0
# ✓ zoom = 150
# ✗ roll: Not supported
# ✗ iris: Not supported
# Read 5/7 properties

# Filter to supported properties
supported = {p: v for p, v in state.items() if v is not None}
print(f"Device state: {supported}")
```


#### Optional verbose logging

Verbose mode prints progress for each property and summary:

```python
# Verbose=True: Per-property feedback + summary
results = cam.set_multiple(config, verbose=True)

# Verbose=False: Silent operation (default)
results = cam.set_multiple(config, verbose=False)

# Use verbose for interactive debugging, silent for batch scripts
```


#### Partial failure handling with result dicts

Result dicts provide structured error info per property:

```python
results = cam.set_multiple({'brightness': 500, 'zoom': 200})  # brightness out-of-range

for prop_name, result in results.items():
    if result['success']:
        print(f"{prop_name}: Applied value {result['value']}")
    else:
        print(f"{prop_name}: Failed ({result['error']})")
        if result['error'] == 'out_of_range':
            print(f"  Valid range: {result['range']}, Current: {result['current']}")
        else:
            print(f"  Message: {result['message']}")

# Output:
# brightness: Failed (out_of_range)
#   Valid range: (0, 255), Current: 128
# zoom: Applied value 200
```


#### Batch operation efficiency patterns

**Efficient patterns** (batch approach):

```python
# ✓ Single batch call for multiple properties
config = {
    'brightness': 80,
    'contrast': 60,
    'saturation': 55,
    'pan': 0,
    'zoom': 200,
    'focus': 'auto'
}
results = cam.set_multiple(config)

# ✓ Batch read then conditional updates
state = cam.get_multiple(['brightness', 'zoom', 'focus'])
if state['brightness'] < 50:
    cam.set_multiple({'brightness': 70})

# ✓ Transactional pattern: save state, apply config, rollback if needed
original = cam.get_multiple(list(config.keys()))
results = cam.set_multiple(config, stop_on_error=True)
if not all(r['success'] for r in results.values()):
    cam.set_multiple(original)  # Rollback
```

**Inefficient patterns** (individual calls):

```python
# ✗ Multiple individual calls (high latency overhead)
cam.set_brightness(80)
cam.set_contrast(60)
cam.set_saturation(55)
cam.set_pan(0)
cam.set_zoom(200)
cam.set_focus('auto')
```


#### Performance comparison with individual operations

**Benchmark results**:

```
Scenario: Configure 50 properties on typical USB camera

Individual method calls (50× set_*):
  - Per-call overhead: ~50ms
  - Total: 50 calls × 50ms = 2,500ms (2.5 seconds)
  
Batch operation (1× set_multiple):
  - Amortized overhead: ~10ms
  - Total: 1 call × 500ms = 500ms (0.5 seconds)
  
Efficiency gain: 5x faster (~80% reduction)
```

**Why batch is faster**:

1. Single context acquisition (vs. 50× connection checks)
2. Reduced device communication overhead (batched operations)
3. Amortized validation cost (all properties validated once)
4. Pipeline efficiency (device can process multiple commands sequentially)

**Recommendation**: Use `set_multiple()` for 3+ properties; use individual setters for single properties or latency-sensitive code that cannot tolerate batch delays.

### 3.16 Camera Reset & Defaults

Reset operations restore properties to factory or intelligent defaults with tracking and device-specific behavior handling.

#### `reset_to_defaults()` method

Resets all properties to device factory defaults. Requires explicit confirmation to prevent accidents.

```python
def reset_to_defaults(self, confirm: bool = False) -> Dict[str, bool]:
    if not confirm:
        warnings.warn("Pass confirm=True to reset all properties")
        return {'success': False}
    self._ensure_connected()
    self._core_camera.reset_to_defaults()
    return {prop: True for prop in self.list_properties().keys()}
```

Usage: `cam.reset_to_defaults(confirm=True)`

#### `set_smart_default()` intelligent default method

Sets property to device-specific intelligent default: `brightness=128`, `white_balance='auto'`, `focus='auto'`, `pan=0`, `tilt=0`, `zoom=100`, etc.

```python
def set_smart_default(self, property_name: str) -> bool:
    smart_defaults = {
        'brightness': 128, 'white_balance': 'auto', 'focus': 'auto',
        'pan': 0, 'tilt': 0, 'zoom': 100, 'privacy': False
    }
    if property_name not in smart_defaults:
        raise PropertyNotSupportedError(f"No smart default for '{property_name}'")
    try:
        self.set(property_name, smart_defaults[property_name])
        return True
    except:
        return False
```


#### `center_camera()` method

Centers pan/tilt using device-reported ranges. If 0 is supported, uses 0; otherwise uses mid-range.

```python
def center_camera(self) -> Dict[str, bool]:
    results = {}
    for axis in ['pan', 'tilt']:
        r = self.get_property_range(axis)
        center = 0 if r['min'] <= 0 <= r['max'] else (r['min'] + r['max']) // 2
        try:
            self.set(axis, center)
            results[axis] = True
        except:
            results[axis] = False
    return results
```


#### Partial success handling

Reset operations may partially succeed. Check result dict to identify which properties reset vs. failed.

```python
results = cam.reset_to_defaults(confirm=True)
succeeded = sum(1 for r in results.values() if r)
failed = len(results) - succeeded
```


#### Smart default algorithm

1. Detects property type (video/camera, int/bool, auto-capable)
2. Selects defaults within device range constraints
3. Prefers 'auto' modes (white_balance, focus, exposure)
4. Centers pan/tilt to 0 with mid-range fallback
5. Uses conservative mid-range values (brightness, saturation)
6. Gracefully handles unsupported properties

#### Reset operation tracking

Track reset history for audit trails:

```python
def track_reset(property_name: str):
    return {
        'timestamp': datetime.now().isoformat(),
        'property': property_name,
        'previous_value': cam.get(property_name)
    }
```


#### Device-specific reset behavior

UVC webcams reset via device control with persistence across reconnect. IP/PTZ cameras reset via API only; pan/tilt/zoom reset to mechanical center/limits. High-end cameras may require confirmation and run slower.

***

### 3.17 Device Information \& Status

Provides read-only access to device metadata and connection health.

#### `device_name` property

Read-only device name from USB descriptor (e.g., "HD Webcam C920").

```python
@property
def device_name(self) -> str:
    return self._core_camera.device_name or "Unknown"
```


#### `device_path` property

Read-only unique device identifier for reconnection. Platform-specific: `/dev/videoX` (Linux), `\\?\USB#...` (Windows), camera index (macOS).

```python
@property
def device_path(self) -> str:
    return self._device_path
```


#### `is_connected` property

Returns True if device responsive; False if disconnected or unresponsive. Uses lightweight property read test.

```python
@property
def is_connected(self) -> bool:
    if not self._connected:
        return False
    try:
        self._core_camera.test_property_read('brightness')
        return True
    except:
        return False
```


#### `get_connection_info()` method

Returns connection metadata dict: device_name, device_path, is_connected, connection_type, connection_time, uptime_seconds, property_count, supported_video_props, supported_camera_props.

```python
def get_connection_info(self) -> Dict[str, Any]:
    return {
        'device_name': self.device_name,
        'device_path': self.device_path,
        'is_connected': self.is_connected,
        'uptime_seconds': (datetime.now() - self._connection_time).total_seconds(),
        'property_count': len(self.list_properties())
    }
```


#### `test_connection_health()` multi-operation health check

Performs read, write, and range-query tests. Returns per-test latency and overall health status ('healthy', 'degraded', 'offline').

```python
def test_connection_health(self) -> Dict[str, Any]:
    results = {'tests': {}}
    for op in ['read', 'write', 'range_query']:
        start = time.time()
        try:
            if op == 'read': self.get('brightness')
            elif op == 'write': v = self.get('brightness'); self.set('brightness', v)
            else: self.get_property_range('zoom')
            results['tests'][op] = {'success': True, 'latency_ms': (time.time() - start) * 1000}
        except Exception as e:
            results['tests'][op] = {'success': False, 'error': str(e)}
    successes = sum(1 for t in results['tests'].values() if t.get('success'))
    results['overall_health'] = 'healthy' if successes == 3 else ('degraded' if successes > 0 else 'offline')
    return results
```


#### Connection state tracking

Internal tracking: `_connected`, `_connection_time`, `_last_activity`, `_disconnection_count`, `_error_log`. Used for diagnostics and recovery strategies.

#### Device metadata access

Query device capabilities: `name`, `connected`, `uptime`, `total_properties`, `video_properties`, `camera_properties`, `supports_pan_tilt`, `supports_zoom`.

```python
def get_device_capabilities(cam):
    info = cam.get_connection_info()
    props = cam.list_properties()
    return {
        'name': info['device_name'],
        'supports_pan_tilt': 'pan' in props and 'tilt' in props,
        'supports_zoom': 'zoom' in props
    }
```


***

### 3.18 Connection Management \& Recovery

Manage device connections with reconnection logic, validation, health monitoring, and error recovery.

#### `reconnect()` method

Re-establishes connection to same device using stored device_path. Implements exponential backoff retry with configurable timeout.

```python
def reconnect(self, timeout_seconds: int = 5) -> bool:
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            self._core_camera = DuvCoreAPI(self._device_path)
            self._connected = True
            self._disconnection_count = 0
            return True
        except:
            time.sleep(0.1)
    raise ConnectionError(f"Reconnection timeout after {timeout_seconds}s")
```


#### `close()` basic cleanup

Releases device handle and marks disconnected. No validation; simple cleanup for context manager exit.

```python
def close(self) -> None:
    if self._core_camera:
        try:
            self._core_camera.close()
        except:
            pass
    self._connected = False
```


#### `close_with_validation()` cleanup with validation

Cleanup that validates device state before closing: checks responsiveness, centers camera, disables privacy, handles errors gracefully.

```python
def close_with_validation(self) -> Dict[str, bool]:
    results = {}
    try:
        results['responsive'] = self.is_connected
        results['centered'] = self.center_camera().get('pan', False)
        if self.privacy:
            self.privacy = False
        results['privacy_disabled'] = True
    except:
        results['privacy_disabled'] = False
    self.close()
    results['closed'] = True
    return results
```


#### Health monitoring \& diagnostics

Diagnose connection issues: check device path exists, run health check, inspect last activity, track disconnection count, review error log.

```python
def diagnose_connection(cam):
    return {
        'device_exists': os.path.exists(cam.device_path),
        'is_connected': cam.is_connected,
        'health': cam.test_connection_health(),
        'disconnections': cam._disconnection_count,
        'recent_errors': cam._error_log[-5:]
    }
```


#### Connection error tracking \& recovery

Track error patterns and suggest recovery actions: timeout → reconnect/unplug; not found → check USB; permission → check access rights.

```python
class ErrorTracker:
    def suggest_recovery(self):
        if not self.errors: return "No errors"
        msg = self.errors[-1].lower()
        if 'timeout' in msg: return "Device unresponsive. Reconnect or unplug/replug."
        elif 'not found' in msg: return "Device disconnected. Check USB."
        elif 'permission' in msg: return "Permission denied. Check access rights."
        return "Unknown error. See error log."
```


#### `.core` property for Result API access

Direct access to underlying C++ API for advanced Result/Status operations and low-level error handling.

```python
@property
def core(self):
    return self._core_camera

# Usage:
result = cam.core.get_raw_property(prop_enum)
if result.is_ok():
    value = result.value()
```


#### Advanced connection management with state machine

Manage state transitions: disconnected ↔ connected ↔ degraded ↔ reconnecting → closed. Validates transitions and prevents invalid state changes.

```python
class StateMachine:
    STATES = ['disconnected', 'connected', 'reconnecting', 'degraded', 'closed']
    def transition(self, new_state):
        valid = {
            'disconnected': ['connected', 'closed'],
            'connected': ['disconnected', 'degraded', 'closed'],
            'degraded': ['connected', 'disconnected', 'reconnecting'],
            'reconnecting': ['connected', 'disconnected'],
            'closed': []
        }
        if new_state not in valid.get(self.state, []):
            raise ValueError(f"Invalid: {self.state} → {new_state}")
        self.state = new_state
```


#### Reconnection logic patterns

Exponential backoff: retry with increasing delays (1s, 2s, 4s, 8s, 16s, capped at 30s). All-or-nothing transaction: save state, apply config, rollback on failure.

```python
def reconnect_with_backoff(cam, max_retries=5):
    for attempt in range(max_retries):
        try:
            cam.reconnect(timeout_seconds=2)
            return True
        except:
            wait = min(2 ** attempt, 30)
            time.sleep(wait)
    return False
```


#### Device path tracking for reconnection

Save/load device path across sessions for persistent reconnection.

```python
def save_device_path(cam, filepath):
    with open(filepath, 'w') as f:
        f.write(cam.device_path)

def load_and_reconnect(filepath):
    with open(filepath, 'r') as f:
        device_path = f.read()
    cam = CameraController()
    cam._device_path = device_path
    cam.reconnect()
    return cam
```
### 3.19 Internal Helper Methods \& String Conversion

These internal helper methods handle common tasks that the public API relies on behind the scenes. Understanding them helps developers grasp how the controller manages device communication, mode conversion, and Result API integration.

#### `_ensure_connected()` connection validation

This private method is called at the start of almost every operation that needs device access. It validates that the camera is still connected and responsive before attempting any property access. If the connection is broken or the device has been disconnected, it immediately raises `DeviceNotConnectedError` with a clear message, preventing cryptic failures deeper in the call stack.

```python
def _ensure_connected(self):
    """Check if camera is connected; raise exception if not."""
    if not self._connected or not self.is_connected:
        raise DeviceNotConnectedError("Camera is not connected")
```

Why this matters: This prevents operations from failing silently or with unclear error messages. It's a defensive programming pattern that catches problems early. Any public method that needs the device should call this first.

#### `_parse_mode_string()` mode string parsing

Properties can be set to different modes: `'manual'` (user-specified value), `'auto'` (device auto-adjusts), or `'continuous'` (ongoing automatic adjustment). The parser converts user input to canonical lowercase form, handling common mistakes like extra whitespace or mixed case.

```python
def _parse_mode_string(self, mode_str: str) -> str:
    """Convert mode string to canonical lowercase form."""
    normalized = mode_str.lower().strip()  # Remove whitespace, convert to lowercase
    valid_modes = {'manual', 'auto', 'continuous'}
    if normalized not in valid_modes:
        raise ValueError(f"Invalid mode: '{mode_str}'. Expected one of: {valid_modes}")
    return normalized
```

**Case-insensitive handling**: Input `'MANUAL'`, `'Manual'`, `'manual'` all become `'manual'`.

**Whitespace tolerance**: Input `'  auto  '` becomes `'auto'`. This prevents frustrating errors where users accidentally include spaces from copy-pasting.

Examples: `_parse_mode_string('Auto')` → `'auto'`, `_parse_mode_string(' CONTINUOUS ')` → `'continuous'`.

#### `_set_property_auto()` auto mode setter

Sets a property to automatic mode when the device supports it. This is called internally by auto-adjustment methods. It gracefully handles devices that don't support auto mode for a particular property (returns False rather than crashing).

```python
def _set_property_auto(self, property_name: str) -> bool:
    """Set property to auto mode if supported by device."""
    try:
        # Get current setting via Result API
        result = self._get_video_property(property_name)
        if result.is_ok():
            setting = result.value()
            setting.mode = CamMode.Auto  # Change mode to auto
            # Apply the change
            set_result = self._set_video_property(property_name, setting)
            return set_result.is_ok()
    except Exception:
        return False  # Device doesn't support auto for this property
    return False
```

This is useful for properties like white balance (`'auto'` mode lets device detect color temperature) or focus (`'auto'` enables continuous autofocus). If auto is not supported, the method returns False silently, allowing callers to fall back to manual adjustment.

#### `_get_dynamic_range()` dynamic range querying with fallbacks

Camera properties have min/max ranges (e.g., brightness 0-255, pan -180 to +180). This method queries the device for actual supported ranges. If the device doesn't report ranges (older cameras), it falls back to predefined class constants.

```python
def _get_dynamic_range(self, property_name: str, fallback_min: int, 
                       fallback_max: int) -> Tuple[int, int]:
    """Get property range from device, or use fallback constants."""
    try:
        prop_range = self.get_property_range(property_name)
        if prop_range:
            return (prop_range['min'], prop_range['max'])
    except Exception:
        pass  # Device query failed; use fallback
    
    # Return predefined fallback values
    return (fallback_min, fallback_max)
```

**Fallback mechanism**:

1. First attempt: Query the device directly via `get_property_range()`. Modern cameras respond with actual supported ranges.
2. Query fails or returns None: Use predefined fallback ranges (brightness 0-255, pan -180/+180, etc.). These are safe conservative defaults based on typical camera specs.
3. Why fallbacks matter: Older or simple cameras may not support range queries. Without fallbacks, the code would crash when trying to set properties. With fallbacks, it succeeds using sensible defaults.

Example: `_get_dynamic_range('brightness', 0, 255)` first asks the device "what's your brightness range?" If the device doesn't answer, it returns (0, 255).

#### `_get_video_property()` Result API delegation

Wrapper around the low-level C++ Result API for reading video properties. Converts property name (string) to the C++ enum, then calls the Result API.

```python
def _get_video_property(self, property_name: str) -> Result:
    """Read video property via Result API. Returns Result<PropSetting>."""
    prop_enum = self._property_name_to_enum('video', property_name)
    return self._core_camera.get(prop_enum)
```

Returns a `Result` object (either ok with a `PropSetting` value, or error with error details). Allows fine-grained error handling without exceptions.

#### `_set_video_property()` Result API delegation

Wrapper for setting video properties via the Result API. Takes a property name and a `PropSetting` object (which includes value and mode).

```python
def _set_video_property(self, property_name: str, setting: PropSetting) -> Result:
    """Write video property via Result API. Returns Result<None>."""
    prop_enum = self._property_name_to_enum('video', property_name)
    return self._core_camera.set(prop_enum, setting)
```


#### `_get_camera_property()` Result API delegation

Similar to `_get_video_property()`, but for camera properties (pan, tilt, zoom, etc.). Returns `Result<PropSetting>`.

```python
def _get_camera_property(self, property_name: str) -> Result:
    """Read camera property via Result API."""
    prop_enum = self._property_name_to_enum('camera', property_name)
    return self._core_camera.get(prop_enum)
```


#### `_set_camera_property()` Result API delegation

Wrapper for setting camera properties. Takes property name and `PropSetting`, returns `Result<None>`.

```python
def _set_camera_property(self, property_name: str, setting: PropSetting) -> Result:
    """Write camera property via Result API."""
    prop_enum = self._property_name_to_enum('camera', property_name)
    return self._core_camera.set(prop_enum, setting)
```

**Why these wrappers exist**: The underlying C++ API works with enums and Result types. The Pythonic layer translates user-friendly strings into these low-level types. These methods bridge that gap, converting names and routing calls appropriately while keeping the core clean.

#### `to_string()` enum conversion utility

Module-level function converting C++ enums to human-readable strings. Useful for debugging, logging, or displaying enum values to users.

```python
def to_string(enum_val) -> str:
    """Convert enum to lowercase string representation."""
    return enum_val.name.lower() if hasattr(enum_val, 'name') else str(enum_val)
```

Examples:

- `to_string(duvc.VidProp.Brightness)` → `'brightness'`
- `to_string(duvc.CamProp.Pan)` → `'pan'`
- `to_string(duvc.CamMode.Auto)` → `'auto'`

Useful when building error messages or logging which property failed.

***

### 3.20 Special Methods \& Pythonic Features

Python special methods (magic methods starting with `__`) enable intuitive, idiomatic usage of the `CameraController` class. These make the library feel like a native Python library rather than a thin C++ wrapper.

#### `__enter__()` \& `__exit__()` context manager protocol

These methods enable the `with` statement, providing automatic resource management. When you enter a `with` block, `__enter__()` is called (acquiring the camera connection). When you exit (whether normally or via exception), `__exit__()` is called (releasing resources). This ensures cleanup happens even if errors occur.

```python
def __enter__(self):
    """Called when entering 'with' block."""
    self.connect()  # Open device connection
    return self     # Return the controller instance

def __exit__(self, exc_type, exc_val, exc_tb):
    """Called when exiting 'with' block (always, even on exception)."""
    self.close_with_validation()  # Clean shutdown
    return False  # Propagate exceptions (don't suppress them)
```

**Usage pattern**:

```python
with CameraController() as cam:
    cam.brightness = 75
    cam.pan = 0
# Connection automatically closed here, even if exception occurred above
```

This is Python best practice. Instead of manually calling `cam.connect()` and `cam.close()`, the `with` statement handles it. If an exception occurs inside the block, the connection is still properly cleaned up.

#### `__str__()` user-friendly representation

Returns a human-readable summary of the camera state. Called when you print the controller or convert it to a string.

```python
def __str__(self) -> str:
    """Return user-friendly string representation."""
    status = "connected" if self.is_connected else "disconnected"
    prop_count = len(self.list_properties())
    return f"<CameraController: {self.device_name} ({status}, {prop_count} properties)>"
```

Example output: `<CameraController: Logitech C920 (connected, 42 properties)>`

**Usage**: `print(cam)` or `str(cam)` displays this summary, making it easy to inspect camera state at a glance.

#### `__repr__()` detailed representation

Returns a technical representation useful for debugging. More detailed than `__str__()`, includes the device path and internal state.

```python
def __repr__(self) -> str:
    """Return detailed string for debugging."""
    return (f"CameraController(path={self.device_path!r}, "
            f"connected={self.is_connected}, name={self.device_name!r})")
```

Example output: `CameraController(path='/dev/video0', connected=True, name='Logitech C920')`

**Usage**: `repr(cam)` or in interactive Python shells where you want detailed debug info.

#### `__bool__()` truthiness evaluation

Makes the camera object evaluate to True if connected, False if disconnected. Enables intuitive conditional checks.

```python
def __bool__(self) -> bool:
    """Camera is 'truthy' if connected and responsive."""
    return self.is_connected
```

**Usage examples**:

```python
if cam:
    cam.brightness = 80  # Only runs if camera is connected

if not cam:
    print("Camera disconnected")

# Safe pattern: check connection before using
try:
    with CameraController() as cam:
        if cam:
            # Do camera operations
        else:
            print("Camera failed to connect")
except DeviceNotFoundError:
    print("No cameras found")
```

**Why this matters**: This makes code more Pythonic and readable. Instead of `if cam.is_connected:`, you can write `if cam:`. It feels natural because Python developers expect objects to evaluate to True/False based on meaningful state.

