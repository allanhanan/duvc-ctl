## 13. Common Patterns \& Recipes


### 13.1 Basic \& Multi-Camera Control

Pragmatic usage patterns for single and multiple cameras, showing both Pythonic and explicit error-handling approaches.

***

#### Simple Pythonic API usage

**Automatic device management with context manager:**

```python
import duvc_ctl as duvc

# Automatically opens & closes device
with duvc.CameraController(0) as cam:
    cam.brightness = 100
    cam.zoom = 2
    current_zoom = cam.zoom
    print(f"Zoom: {current_zoom}")
```

No explicit error handling—exceptions propagate. Ideal for scripts where device is guaranteed connected.

**Manual context (if device may disconnect):**

```python
cam = duvc.CameraController(0)
try:
    cam.set("brightness", 100)
    cam.set("zoom", 2)
finally:
    cam.close()
```


***

#### Result-based error handling

**Explicit control via Result types:**

```python
import duvc_ctl as duvc

device = duvc.list_devices()[0]
result = duvc.open_camera(device)

if not result.is_ok():
    error = result.error()
    print(f"Failed to open: {error.description()}")
    exit(1)

cam = result.value()

# Read property, handle individually
brightness_result = cam.get_camera_property(duvc.CamProp.Brightness)
if brightness_result.is_ok():
    brightness = brightness_result.value().value
    print(f"Brightness: {brightness}")
else:
    print(f"Failed to read brightness")

cam.close()
```

No exceptions thrown—check `.is_ok()` after each operation.

***

#### Multi-camera management

**Sequential access (process cameras one-by-one):**

```python
import duvc_ctl as duvc

devices = duvc.list_devices()
print(f"Found {len(devices)} cameras")

for i, device in enumerate(devices):
    try:
        with duvc.CameraController(i) as cam:
            print(f"Camera {i}: {device.name}")
            cam.brightness = 80 + (i * 10)  # Vary per camera
            print(f"  Brightness set to {cam.brightness}")
    except duvc.DeviceNotFoundError:
        print(f"Camera {i} disconnected")
    except Exception as e:
        print(f"Camera {i} error: {e}")
```

Each camera opened/closed in sequence.

**Parallel management (all cameras at once):**

```python
import duvc_ctl as duvc
import threading

devices = duvc.list_devices()
cameras = []

# Open all devices
for i in range(len(devices)):
    try:
        cameras.append(duvc.CameraController(i))
    except duvc.DeviceNotFoundError:
        print(f"Failed to open camera {i}")

# Apply settings in parallel
threads = []
def configure_camera(cam, index):
    cam.brightness = 100
    cam.zoom = 2
    print(f"Camera {index} configured")

for idx, cam in enumerate(cameras):
    thread = threading.Thread(target=configure_camera, args=(cam, idx))
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()

# Close all
for cam in cameras:
    cam.close()
```

**Thread safety**: Each camera operates independently. Device operations may block (e.g., autofocus); use threads to avoid stalls.

***

#### Switching between cameras

**Change active camera by index:**

```python
import duvc_ctl as duvc

cam = duvc.CameraController(0)
print(f"Current device: {cam.device.name}")

# Switch to different camera
cam.close()
cam = duvc.CameraController(1)
print(f"Switched to: {cam.device.name}")
```

Each `CameraController()` instance binds to one device.

**Query current device before operations:**

```python
try:
    cam.brightness = 150
except duvc.DeviceNotFoundError:
    print("Camera was disconnected; switching...")
    cam.close()
    cam = duvc.CameraController(0)  # Rebind to first available
    cam.brightness = 150
```


***

#### Concurrent operations

**Avoid interleaved hardware access** (may corrupt state):

```python
import duvc_ctl as duvc
import threading

cam = duvc.CameraController(0)
lock = threading.Lock()

def set_exposure(value):
    with lock:
        cam.exposure_mode = "manual"
        cam.exposure = value

def read_exposure():
    with lock:
        mode = cam.exposure_mode
        value = cam.exposure
        return mode, value

# Safe concurrent access
threads = [
    threading.Thread(target=set_exposure, args=(5,)),
    threading.Thread(target=read_exposure),
]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

Use locks to serialize property access on same device.

**Multiple cameras = no locking needed** (each device independent):

```python
# Safe without locks - different devices
cam0 = duvc.CameraController(0)
cam1 = duvc.CameraController(1)

threading.Thread(target=lambda: setattr(cam0, 'brightness', 100)).start()
threading.Thread(target=lambda: setattr(cam1, 'brightness', 200)).start()
# No contention - different hardware
```


***

#### Basic usage patterns

**Quick snapshot setup:**

```python
import duvc_ctl as duvc

def setup_camera():
    cam = duvc.CameraController(0)
    cam.exposure_mode = "manual"
    cam.exposure = -2  # Faster shutter
    cam.brightness = 90
    cam.focus_mode = "manual"
    cam.focus = 200  # Far field
    return cam

cam = setup_camera()
# Now ready for video capture
```

**Configuration reload:**

```python
config = {
    "brightness": 100,
    "saturation": 64,
    "exposure_mode": "auto",
}

cam = duvc.CameraController(0)
for prop, value in config.items():
    try:
        setattr(cam, prop, value)
    except Exception as e:
        print(f"Warning: {prop} not supported or out of range")
```

**List all available properties:**

```python
import duvc_ctl as duvc

cam = duvc.CameraController(0)
caps = cam.get_capabilities()

print("Camera Properties:")
for prop in caps.supported_camera_properties:
    try:
        value = getattr(cam, prop.lower())
        print(f"  {prop}: {value}")
    except:
        print(f"  {prop}: <unavailable>")

print("Video Properties:")
for prop in caps.supported_video_properties:
    try:
        value = getattr(cam, prop.lower())
        print(f"  {prop}: {value}")
    except:
        print(f"  {prop}: <unavailable>")
```

### 13.2 Bulk \& Property Operations

Efficient multi-property access patterns with intelligent failure handling.

***

#### set_multiple() with partial failure

**Apply multiple properties sequentially with continue-on-error:**

Attempt to set all properties even if some fail. Collect errors for logging or UI feedback. Use the pattern: gather unsupported properties, log warnings, continue with remaining operations.

Properties set independently—failure of one doesn't prevent others. For example: setting brightness fails (unsupported), but zoom, pan, and focus succeed. Application receives partial success indicator and list of failed properties.

**Strategy**: Sort properties by criticality. Set essential properties first. Mark non-critical failures as warnings rather than fatal errors. This prevents one unsupported property from blocking all configuration.

***

#### get_multiple() with failure

**Read multiple properties with graceful fallback:**

Query property ranges and current values in bulk. Missing ranges fall back to defaults. Device may not support all properties—`get_property_range()` returns `None` if unsupported.

Implementation iterates through requested properties, catches `PropertyNotSupportedError` per property, logs mismatches, continues to next. Return dict with successes and failures mapped separately. Caller can inspect which properties succeeded.

***

#### Partial failure handling

**Pattern**: Distinguish recoverable from fatal failures.

Recoverable (continue):

- Property unsupported on device
- Out-of-range value (clamp and retry)
- Temporary device timeout (reconnect)

Fatal (abort):

- Device disconnected (needs reconnection)
- Permission denied (needs elevated privileges)
- Hardware fault

**Implementation**: Wrap each property operation in try-catch. Categorize exception type. For recoverable, log and skip. For fatal, escalate or signal caller to handle reconnection.

***

#### PTZ coordination

**Synchronized Pan/Tilt movement:**

Apply pan and tilt together to prevent intermediate invalid states. Use combined `PanTilt` property if device supports it (single atomic operation). Otherwise, sequence pan first, then tilt (or vice versa based on movement distance).

**Timing**: Hardware may require delay between pan and tilt adjustments. Add configurable delay (typically 50–100ms) between operations if combined property unavailable.

**Centering before PTZ**: Reset pan/tilt to center (0° each) before large movements. Prevents jerky motion or hardware limits. Use `center_camera()` helper which calculates midpoint of each axis range.

***

#### Relative vs absolute

**Absolute operations** (`pan = 45`): Set precise value. Requires no prior state knowledge. Use for keyframe or preset setup.

**Relative operations** (`pan_relative(15)`): Adjust from current position. Avoids explicit state query. Ideal for smooth real-time tracking or incremental UI controls (e.g., joystick input).

**Mixing**: Don't alternate absolute and relative on same property without verification. Read current state after relative move if next operation is absolute.

**Efficiency**: Relative is faster—no redundant read before write. Absolute is safer when target state must be exact regardless of history.

***

#### Centering

**PTZ centering strategy:**

Query pan/tilt ranges, compute center as `(min + max) / 2` for each axis. Apply both simultaneously if device supports `PanTilt` property, otherwise sequence. Verify success by reading back values (may not move if hardware mechanical limits differ from reported range).

**Fallback**: If centering fails, leave cameras at current position. Log warning but don't throw—centering is typically a convenience feature, not critical.

***

#### Batch efficiency

**Minimize I/O round-trips:**

Group property reads into single device query when possible. UVC `get_device_info()` returns all capabilities/properties in one enumeration.

**Pipelining**: Queue multiple writes before reading confirmations. Reduces latency vs. write-confirm-write-confirm loop.

**Threading**: Multi-camera batch operations benefit from thread-per-camera. Each camera's operation doesn't block others. Use locks only for shared state (e.g., device list).

**Caching**: Store property ranges locally after first query. Avoids redundant hardware I/O during repeated property validation.

***

### 13.3 Advanced Patterns

Resilience, state management, and runtime adaptation.

***

#### Device hotplug handling via callbacks

**Register callback for device attach/detach events:**

Library provides `register_device_change_callback()` which fires when cameras connect or disconnect. Callback receives device info and event type (attach/detach).

**Callback responsibilities**:

- Update UI to reflect device list changes
- Gracefully close handles to disconnected devices
- Trigger reconnection logic if application was using that device
- Do NOT perform blocking operations in callback; defer heavy work to event queue

**Pattern**: Callback sets flag, main thread polls flag and handles reconnection asynchronously. Prevents deadlock if callback tries to reacquire locks or enumerate devices.

***

#### Reconnection logic

**Detect disconnection and retry:**

Catch `DeviceNotFoundError` during property access. Attempt to reopen device via `CameraController(device_index)` or `CameraController(device_name_pattern)`. If reopen succeeds, resume operations. If fails repeatedly, mark device offline.

**Backoff strategy**: First retry immediately. If still fails, wait 100ms, retry. Exponential backoff up to 5 seconds. After N failures (typically 3–5), escalate to user (notify, don't auto-retry forever).

**Device lookup by path**: Prefer matching by device path (stored before disconnect) rather than index. Indices shift when cameras are plugged/unplugged; paths remain stable within OS session.

***

#### Device path tracking

**Stable device identification:**

Each `Device` object has `name` (human-readable) and `path` (system identifier). Path persists across reconnection (unless device is physically moved to different USB port).

**Usage**: Store `device.path` when camera connects. On disconnect/reconnect, search new device list by path to rebind to same physical camera. This prevents accidentally switching to a different camera if user plugs/unplugs multiple devices.

**Implementation**: Maintain map `{path: CameraController_instance}` for multi-camera applications.

***

#### Preset persistence \& loading

**Save/restore camera configurations:**

Store property values (brightness, zoom, focus, etc.) as dict. On reconnection, reapply same dict to camera.

**Format**: JSON or YAML for human readability and version compatibility.

```
{
  "device_path": "/path/to/device",
  "properties": {
    "brightness": 100,
    "exposure_mode": "manual",
    "exposure": -2,
    "focus_mode": "manual",
    "focus": 200
  },
  "timestamp": "2025-11-06T14:30:00Z"
}
```

**Versioning**: Include schema version in preset. On load mismatch (e.g., property removed from device), skip unsupported properties with warning, apply remainder.

**Partial application**: If device doesn't support all saved properties, apply only supported subset. Don't fail entire preset load.

***

#### Property introspection

**Query device capability at runtime:**

Call `get_supported_properties()` or `get_device_info()` to discover which properties camera supports. Iterate through returned lists and conditionally enable UI controls or log availability.

**Range introspection**: Call `get_property_range(property_name)` for each property to determine slider/spinner bounds dynamically. Don't hardcode ranges—devices vary widely.

**Example**: Brightness range on USB 2 camera is ; on USB 3, . Detect at runtime and adjust UI accordingly.

***

#### Range validation \& capability

**Validate before setting:**

Query range, clamp value to [min, max], check step alignment if applicable. Some properties require values to be multiples of step (e.g., step=10 means only values 0, 10, 20… allowed).

**Clamping**: `clamp(value, range.min, range.max)` ensures in bounds. If out-of-range error still occurs, log warning (device range may be dynamic or misreported).

**Capability gates**: Wrap advanced features behind capability check. Only offer PTZ UI if device reports Pan/Tilt support. Only show autofocus if Focus property supported in Auto mode.

***

#### Real-time monitoring

**Poll or stream property changes:**

Periodically read property values to detect hardware changes (e.g., autofocus converged, brightness adjusted by user via physical controls on camera).

**Polling interval**: Typically 200–500ms balances responsiveness vs. I/O overhead. Avoid sub-100ms polling—causes thread contention and power drain.

**Change detection**: Compare current value to previous. Log or trigger callback only on actual change. Prevents redundant updates.

**Threading**: Monitor in separate thread to avoid blocking main UI thread. Use thread-safe queue to post changes to UI thread for display.

**Graceful degradation**: If property read fails during monitoring, skip that property in current iteration; retry next cycle. Don't crash monitor thread.

