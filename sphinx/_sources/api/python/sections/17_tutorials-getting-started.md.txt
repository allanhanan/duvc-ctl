## 17. Tutorials & Getting Started


### 17.1 Beginner Tutorial
#### Beginner's Guide to duvc-ctl: Control Your USB Camera from Python

duvc-ctl is a Windows library that lets you control USB cameras (like webcams or PTZ cameras) directly from Python code. Instead of fiddling with Windows settings or clunky GUI tools, you can write simple scripts to adjust brightness, zoom, focus, and more.

#### Installation (2 minutes)

duvc-ctl works on Windows 10/11 with Python 3.8+. That's it—no extra drivers needed since your camera already works in Windows.

Open your terminal and run:

```
pip install duvc-ctl
```

Verify it worked:

```
python -c "import duvc_ctl; print(duvc_ctl.__version__)"
```

If you see a version number like "2.0.0", you're good. If you get an import error, make sure you're on Windows and Python 3.8+.

#### Your First Program

Here's the simplest working example:

```python
import duvc_ctl as duvc

# Get list of cameras connected
devices = duvc.list_devices()
print(f"Found {len(devices)} camera(s)")

# Show each camera's name
for device in devices:
    print(f"  - {device.name}")
```

Run this. It should print your camera name. If nothing appears, plug in a USB camera and try again.

#### Reading Camera Settings

Once you have a camera, you can read its current brightness:

```python
import duvc_ctl as duvc

devices = duvc.list_devices()
if not devices:
    print("No cameras found")
    exit()

camera = duvc.Camera(devices[^0])  # Open first camera

# Read brightness
result = camera.get_property(duvc.VidProp.Brightness)

if result.is_ok:
    # Success—we got the brightness value
    brightness = result.value.value
    mode = result.value.mode  # "Manual" or "Auto"
    print(f"Brightness: {brightness} (Mode: {mode})")
else:
    # Camera doesn't support brightness or it failed
    print(f"Error: {result.error.description}")
```

The `result.is_ok` check is crucial—it tells you if the operation succeeded. If it didn't, `result.error` has the reason.

#### Changing Camera Settings

To change brightness to 150:

```python
import duvc_ctl as duvc

devices = duvc.list_devices()
camera = duvc.Camera(devices[^0])

# Create a new setting
setting = duvc.PropSetting(150, duvc.CamMode.Manual)

# Apply it
result = camera.set_property(duvc.VidProp.Brightness, setting)

if result.is_ok:
    print("Brightness set to 150")
else:
    print(f"Failed: {result.error.description}")
```

`PropSetting` takes two things: the value (0–255 typically) and the mode (Manual for user control, Auto for the camera to decide).

#### Common Properties You Can Control

**Camera properties** (Pan, Tilt, Zoom, Focus, Exposure):

```python
camera.set_property(duvc.CamProp.Zoom, duvc.PropSetting(50, duvc.CamMode.Manual))
```

**Video/Image properties** (Brightness, Contrast, Saturation, Hue):

```python
camera.set_property(duvc.VidProp.Contrast, duvc.PropSetting(100, duvc.CamMode.Manual))
```

Not all cameras support all properties—if you set something unsupported, you'll get an error message.

#### Error Handling

Three things commonly fail:

1. **Camera disconnected**: `DeviceNotFoundError` — plug camera back in.
2. **Camera busy**: `DeviceBusyError` — close other apps using the camera (like Zoom, Teams, etc.).
3. **Property not supported**: `PropertyNotSupportedError` — your camera model doesn't have that feature. Check what it supports by querying ranges first.

To find what your camera supports:

```python
caps = duvc.get_device_capabilities(device)
if caps.is_ok:
    capabilities = caps.value
    print("Camera properties:", capabilities.supported_camera_properties)
    print("Video properties:", capabilities.supported_video_properties)
```

This shows exactly which controls your camera has.

#### Two Ways to Write Code

**Simple (exceptions)** — easier for quick scripts:

```python
from duvc_ctl import CameraController
cam = CameraController()
cam.set_brightness(200)  # Raises exception if it fails
```

**Explicit (Result types)** — more control for production apps:

```python
import duvc_ctl as duvc
result = camera.set_property(duvc.VidProp.Brightness, setting)
if result.is_ok:
    # succeeded
else:
    # handle error with result.error.code
```

For beginners, start with the simple version. Once comfortable, switch to Result types for better error messages. Both work identically underneath.

#### Next Steps

- Read a property and print its range to find valid values
- Loop through all cameras and adjust each one
- Combine camera control with your own image capture code using OpenCV
- Check the full documentation for vendor-specific properties like Logitech RightLight

You now have everything needed to start controlling cameras from Python!

### 17.2 Intermediate Patterns

#### Intermediate Patterns: Getting Smart with Camera Control

Once you're comfortable opening cameras and reading properties, the next level involves reusable patterns for real-world applications. These techniques handle multiple cameras, deal with reconnection, save camera states, and manage code complexity.

#### Context Managers: The Clean Way to Handle Cameras

Every time you open a camera, you need to close it properly—otherwise Windows keeps the device locked and your next script fails. Python's context manager (`with` statement) handles this automatically:

```python
import duvc_ctl as duvc

devices = duvc.list_devices()
if devices:
    # Camera opens here
    with duvc.Camera(devices[0]) as camera:
        result = camera.get_property(duvc.VidProp.Brightness)
        if result.is_ok:
            print(f"Brightness: {result.value.value}")
    # Camera closes here automatically
```

The `with` block ensures the camera closes even if an error happens. You don't need to write cleanup code. This becomes critical when you have multiple cameras or run scripts frequently—forgotten close calls lock up your camera.

#### Device Enumeration: Listing All Connected Cameras

Real cameras get plugged in and unplugged. Your script needs to handle this:

```python
import duvc_ctl as duvc

def list_and_describe_cameras():
    devices = duvc.list_devices()
    if not devices:
        print("No cameras connected")
        return
    
    for i, device in enumerate(devices):
        print(f"\n[{i}] {device.name}")
        print(f"    Path: {device.path}")
        
        # Try to open and check capabilities
        try:
            caps = duvc.get_device_capabilities(device)
            if caps.is_ok:
                cap = caps.value
                print(f"    Camera props: {len(cap.supported_camera_properties)}")
                print(f"    Video props: {len(cap.supported_video_properties)}")
        except Exception as e:
            print(f"    (unavailable: {e})")

list_and_describe_cameras()
```

This gives users a menu to pick which camera to use. When cameras aren't available (plugged in elsewhere, different USB port), they simply don't appear in the list.

#### Bulk Operations: Set Multiple Properties at Once

Instead of setting brightness, contrast, saturation one-by-one (slow), batch them:

```python
import duvc_ctl as duvc

def apply_preset_daylight(camera):
    """Set camera for outdoor daylight conditions."""
    settings = {
        duvc.VidProp.Brightness: duvc.PropSetting(180, duvc.CamMode.Manual),
        duvc.VidProp.Contrast: duvc.PropSetting(120, duvc.CamMode.Manual),
        duvc.VidProp.Saturation: duvc.PropSetting(150, duvc.CamMode.Manual),
        duvc.CamProp.Exposure: duvc.PropSetting(80, duvc.CamMode.Manual),
    }
    
    failed = []
    for prop, setting in settings.items():
        result = camera.set_property(prop, setting)
        if not result.is_ok:
            failed.append((prop, result.error.description))
    
    if failed:
        print("Failed to set:")
        for prop, err in failed:
            print(f"  {prop}: {err}")
    else:
        print("Daylight preset applied successfully")

devices = duvc.list_devices()
if devices:
    with duvc.Camera(devices[0]) as cam:
        apply_preset_daylight(cam)
```

This pattern is reusable—create a preset function for "video conference mode," "streaming," etc., and call it anytime.

#### Presets: Save and Restore Camera States

Your users tweak settings to get perfect image quality. Let them save this as a preset so they can restore it later:

```python
import duvc_ctl as duvc
import json

def save_preset(camera, filename):
    """Capture all current camera settings to a JSON file."""
    state = {}
    
    # Define which properties to save
    props_to_save = [
        (duvc.VidProp.Brightness, "brightness"),
        (duvc.VidProp.Contrast, "contrast"),
        (duvc.VidProp.Saturation, "saturation"),
        (duvc.VidProp.Gamma, "gamma"),
    ]
    
    for prop, name in props_to_save:
        result = camera.get_property(prop)
        if result.is_ok:
            setting = result.value
            state[name] = {
                "value": setting.value,
                "mode": setting.mode
            }
    
    with open(filename, "w") as f:
        json.dump(state, f, indent=2)
    print(f"Preset saved to {filename}")

def load_preset(camera, filename):
    """Restore camera settings from a JSON preset."""
    with open(filename, "r") as f:
        state = json.load(f)
    
    # Map names back to properties
    prop_map = {
        "brightness": duvc.VidProp.Brightness,
        "contrast": duvc.VidProp.Contrast,
        "saturation": duvc.VidProp.Saturation,
        "gamma": duvc.VidProp.Gamma,
    }
    
    for name, data in state.items():
        if name not in prop_map:
            continue
        prop = prop_map[name]
        setting = duvc.PropSetting(data["value"], data["mode"])
        result = camera.set_property(prop, setting)
        if not result.is_ok:
            print(f"Warning: Failed to set {name}: {result.error.description}")

# Usage:
devices = duvc.list_devices()
if devices:
    with duvc.Camera(devices[0]) as cam:
        # User tweaks settings, then...
        save_preset(cam, "my_preset.json")
        
        # Later session, restore:
        load_preset(cam, "my_preset.json")
```

Now users can share presets: "here's my Twitch streaming config" as a single JSON file.

#### Connection Recovery: Handle Cameras That Disconnect

Real USB cameras can glitch or get unplugged. Your app should survive this:

```python
import duvc_ctl as duvc
import time

def reconnect_with_retry(device, max_retries=5, delay=2):
    """Try to reconnect to a camera, retrying if it fails."""
    for attempt in range(max_retries):
        try:
            camera = duvc.Camera(device)
            # Quick health check
            result = camera.get_property(duvc.VidProp.Brightness)
            if result.is_ok:
                print(f"Reconnected on attempt {attempt + 1}")
                return camera
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
    
    raise RuntimeError(f"Failed to reconnect after {max_retries} attempts")

# Usage in your monitoring loop:
devices = duvc.list_devices()
if devices:
    device = devices[0]
    camera = duvc.Camera(device)
    
    try:
        while True:
            result = camera.get_property(duvc.VidProp.Brightness)
            if result.is_ok:
                print(f"Brightness: {result.value.value}")
            else:
                # Camera might have disconnected
                if "not found" in result.error.description:
                    print("Camera disconnected, attempting reconnect...")
                    camera = reconnect_with_retry(device)
                    continue
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped")
```

This prevents your script from crashing mid-stream if the camera temporarily loses USB power.

#### Real-World Example: Building a Camera Streamer

Here's how to combine these patterns into a production-like application:

```python
import duvc_ctl as duvc
import threading
import time
import json

class CameraStreamer:
    def __init__(self, device, preset_file=None):
        self.device = device
        self.camera = None
        self.running = False
        self.lock = threading.Lock()
        
        if preset_file:
            self.preset_file = preset_file
        else:
            self.preset_file = None
    
    def start(self):
        """Open camera and load preset if available."""
        try:
            self.camera = duvc.Camera(self.device)
            if self.preset_file:
                self._load_preset()
            self.running = True
            print(f"Streamer started: {self.device.name}")
        except Exception as e:
            print(f"Failed to start: {e}")
            raise
    
    def _load_preset(self):
        """Load settings from preset file."""
        try:
            with open(self.preset_file, "r") as f:
                state = json.load(f)
            
            prop_map = {
                "brightness": duvc.VidProp.Brightness,
                "contrast": duvc.VidProp.Contrast,
            }
            
            for name, data in state.items():
                if name not in prop_map:
                    continue
                prop = prop_map[name]
                setting = duvc.PropSetting(data["value"], data["mode"])
                self.camera.set_property(prop, setting)
            
            print(f"Preset loaded from {self.preset_file}")
        except Exception as e:
            print(f"Warning: Could not load preset: {e}")
    
    def adjust_brightness(self, value):
        """Thread-safe brightness adjustment."""
        with self.lock:
            if self.camera:
                setting = duvc.PropSetting(value, duvc.CamMode.Manual)
                result = self.camera.set_property(duvc.VidProp.Brightness, setting)
                return result.is_ok
        return False
    
    def get_status(self):
        """Get current camera state."""
        with self.lock:
            if not self.camera:
                return {"status": "offline"}
            
            result = self.camera.get_property(duvc.VidProp.Brightness)
            if result.is_ok:
                return {
                    "status": "online",
                    "brightness": result.value.value,
                    "camera": self.device.name
                }
            else:
                return {"status": "error", "message": result.error.description}
    
    def stop(self):
        """Close camera."""
        with self.lock:
            if self.camera:
                self.camera = None
                self.running = False
                print("Streamer stopped")

# Usage:
if __name__ == "__main__":
    devices = duvc.list_devices()
    if devices:
        streamer = CameraStreamer(devices[0], preset_file="streaming_preset.json")
        streamer.start()
        
        # Adjust via UI or API
        streamer.adjust_brightness(150)
        
        # Poll status
        print(streamer.get_status())
        
        streamer.stop()
```

This object-oriented approach handles threading safely, survives disconnections gracefully, and scales to manage multiple cameras.

### 17.3 Advanced Workflows

#### Advanced Workflows: Expert-Level Camera Orchestration

Once you're shipping code to production, you hit new challenges: specialized hardware needs custom handling, performance matters, and reliability becomes non-negotiable. This section covers patterns that power camera systems at scale.

#### Vendor Property Access: Controlling Camera-Specific Features

Standard camera properties (brightness, contrast) work everywhere. But specialized cameras like Logitech PTZ, HD Pro, or custom industrial cameras expose vendor-specific extensions that aren't in the standard set. Access these directly:

```python
import duvc_ctl as duvc

def enable_logitech_rightlight(camera):
    """Enable Logitech RightLight auto-exposure for low-light scenarios."""
    # Logitech RightLight uses a vendor GUID and property IDs
    # These values are from Logitech's DirectShow documentation
    LOGITECH_GUID = "{04efb3d8-7dcc-4cbc-acf1-69a5f1301da0}"
    RIGHTLIGHT_PROP = 1  # Property ID for RightLight control
    
    try:
        # Set RightLight mode (value > 0 enables it)
        vendor_prop = duvc.VendorProperty(
            prop_set_guid=LOGITECH_GUID,
            prop_id=RIGHTLIGHT_PROP,
            data=b'\x01'  # Enable RightLight
        )
        result = camera.set_vendor_property(vendor_prop)
        if result.is_ok:
            print("RightLight enabled")
        else:
            print(f"RightLight failed: {result.error.description}")
    except Exception as e:
        print(f"Vendor property not supported: {e}")
```

Access vendor properties only on cameras that support them—unsupported GUID/property combinations raise errors. Test with your exact camera model first.

#### Performance Optimization: Batch Operations and Caching

Calling `get_property()` for every property query hits the OS each time (slow). Cache results and batch operations:

```python
import duvc_ctl as duvc
import time

class CameraSnapshot:
    """Fast read of multiple camera properties at once."""
    def __init__(self, camera):
        self.camera = camera
        self.cache = {}
        self.cache_time = {}
        self.TTL = 5  # Cache for 5 seconds
    
    def get_property_cached(self, prop, use_cache=True):
        """Get property with optional caching."""
        now = time.time()
        
        if use_cache and prop in self.cache:
            if now - self.cache_time[prop] < self.TTL:
                return self.cache[prop]
        
        result = self.camera.get_property(prop)
        if result.is_ok:
            self.cache[prop] = result.value
            self.cache_time[prop] = now
        return result
    
    def clear_cache(self):
        """Force refresh on next read."""
        self.cache.clear()
        self.cache_time.clear()

# Usage:
devices = duvc.list_devices()
if devices:
    camera = duvc.Camera(devices[0])
    snapshot = CameraSnapshot(camera)
    
    # First read—hits hardware
    b1 = snapshot.get_property_cached(duvc.VidProp.Brightness)
    print(f"Brightness: {b1.value.value}")
    
    # Second read—from cache (fast)
    b2 = snapshot.get_property_cached(duvc.VidProp.Brightness)
    print(f"Brightness: {b2.value.value}")
    
    # Force refresh
    snapshot.clear_cache()
    b3 = snapshot.get_property_cached(duvc.VidProp.Brightness)
```

For loops reading many properties, caching cuts overhead by 5-10x. Refresh only when you need current state.

#### Event-Driven Architecture: React to Camera Changes

Instead of polling `get_property()` in a loop, set up callbacks that fire when settings change or errors occur:

```python
import duvc_ctl as duvc
import threading
from queue import Queue

class CameraMonitor:
    """Monitor camera state changes with callbacks."""
    def __init__(self, camera):
        self.camera = camera
        self.callbacks = {}
        self.running = False
        self.event_queue = Queue()
    
    def register_callback(self, event_type, callback):
        """Register callback for event type."""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    def start_monitoring(self):
        """Start background monitoring thread."""
        self.running = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
    
    def _monitor_loop(self):
        """Background thread that polls and fires events."""
        last_brightness = None
        
        while self.running:
            result = self.camera.get_property(duvc.VidProp.Brightness)
            
            if result.is_ok:
                current = result.value.value
                if current != last_brightness:
                    # Brightness changed—fire callbacks
                    last_brightness = current
                    self._fire_event("brightness_changed", current)
            else:
                # Error occurred
                self._fire_event("error", result.error.description)
            
            threading.Event().wait(0.5)  # Poll every 500ms
    
    def _fire_event(self, event_type, data):
        """Fire all callbacks for an event."""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Callback error: {e}")
    
    def stop_monitoring(self):
        """Stop background thread."""
        self.running = False

# Usage:
devices = duvc.list_devices()
if devices:
    camera = duvc.Camera(devices[0])
    monitor = CameraMonitor(camera)
    
    def on_brightness_changed(value):
        print(f"Brightness changed to {value}")
    
    def on_error(message):
        print(f"Camera error: {message}")
    
    monitor.register_callback("brightness_changed", on_brightness_changed)
    monitor.register_callback("error", on_error)
    
    monitor.start_monitoring()
    # ... your main code runs, callbacks fire in background ...
    monitor.stop_monitoring()
```

This reactive pattern scales well to complex apps where UI needs to update when camera state changes.

#### Production Deployment: Docker Containerization

Deploy camera apps reliably with Docker. Key gotcha: DirectShow only works on Windows, so containers must use Windows base images:

```dockerfile
# Dockerfile (Windows-based)
FROM mcr.microsoft.com/windows/servercore:ltsc2022

# Install Python
RUN powershell -Command \
    $ProgressPreference = 'SilentlyContinue'; \
    Invoke-WebRequest -Uri https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe \
    -OutFile python-installer.exe; \
    .\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1; \
    Remove-Item python-installer.exe

# Copy app and install dependencies
COPY app.py requirements.txt ./
RUN pip install -r requirements.txt

# For USB device access from container, pass device through Docker
# docker run --device "\\.\COM1" my_camera_app

ENTRYPOINT ["python", "app.py"]
```

Then run with device passthrough:

```bash
docker build -t camera-app .
docker run --device "\\.\GLOBAL??\" camera-app
```

**Key production requirements:**

- Retry logic for camera reconnections (shown in Intermediate Patterns)
- Logging to centralized system (ELK, Splunk, etc.)
- Health checks that verify camera is responding
- Graceful shutdown that closes cameras before exit

```python
# Production health check
def health_check(camera):
    """Verify camera is alive and responsive."""
    result = camera.get_property(duvc.VidProp.Brightness)
    return result.is_ok
```

Run this periodically. If it fails consistently, restart the service or alert ops.

### Custom Device Backends: Abstraction for Testing

For unit tests or multi-platform support, abstract the camera layer behind an interface:

```python
from abc import ABC, abstractmethod
import duvc_ctl as duvc

class CameraBackend(ABC):
    """Abstract camera interface."""
    @abstractmethod
    def get_property(self, prop):
        pass
    
    @abstractmethod
    def set_property(self, prop, setting):
        pass

class RealCameraBackend(CameraBackend):
    """Real hardware camera via duvc-ctl."""
    def __init__(self, device):
        self.camera = duvc.Camera(device)
    
    def get_property(self, prop):
        return self.camera.get_property(prop)
    
    def set_property(self, prop, setting):
        return self.camera.set_property(prop, setting)

class MockCameraBackend(CameraBackend):
    """Fake camera for testing without hardware."""
    def __init__(self):
        self.properties = {
            duvc.VidProp.Brightness: 128,
            duvc.VidProp.Contrast: 100,
        }
    
    def get_property(self, prop):
        # Return mock result
        class MockResult:
            is_ok = True
            value = duvc.PropSetting(self.properties.get(prop, 0), duvc.CamMode.Manual)
        return MockResult()
    
    def set_property(self, prop, setting):
        self.properties[prop] = setting.value
        class MockResult:
            is_ok = True
        return MockResult()

# Usage in production
def get_camera_backend(device=None):
    if device:  # Real camera
        return RealCameraBackend(device)
    else:  # Testing
        return MockCameraBackend()

# Your application code uses the abstraction
def adjust_brightness(backend, value):
    setting = duvc.PropSetting(value, duvc.CamMode.Manual)
    result = backend.set_property(duvc.VidProp.Brightness, setting)
    return result.is_ok

# Test without hardware
backend = get_camera_backend()  # Returns MockCameraBackend
adjust_brightness(backend, 150)
```

This pattern lets you test camera logic without actual cameras connected. Swap implementations as needed.

damn ts big af