# duvc-ctl

`duvc-ctl` is a lightweight Python library for controlling USB Video Class (UVC) camera properties on Windows using the native DirectShow API.  
It exposes camera and video properties (PTZ, focus, exposure, brightness, etc.), supports device monitoring with hotplug detection, and provides access to vendor-specific property sets — all without vendor SDKs, extra drivers, or dependencies.


## Key Features

- **Simple Pythonic API**: Property-based access (`cam.brightness = 80`) with automatic device management and beginner-friendly error handling
- **Advanced Result-Based API**: Explicit error handling with Result types for detailed control in production code
- **Camera & Video Properties**: Get/set PTZ controls, exposure, focus, white balance, gain, and other IAMCameraControl/IAMVideoProcAmp properties
- **Device Monitoring**: List devices, check connectivity, and handle hotplug events
- **Vendor Extensions**: Access custom property sets via GUID
- **Multiple Error Handling**: Simple exceptions, Result types, or safe tuple returns
- **Thread-Safe**: Safe for use in multi-threaded applications

Works on **Windows 7+ with Python 3.8+**. Suitable for computer vision, robotics, video streaming, and automation projects requiring precise USB camera control.


## Installation

```
pip install duvc-ctl
```


## Two APIs, One Library

`duvc-ctl` provides two complementary APIs for different use cases:

### 1. Pythonic API (Recommended for Most Users)

**Use when:** You want simple, readable code with automatic device selection and beginner-friendly errors.

Simple property-based control with context manager support:

```python
import duvc_ctl as duvc

# Connect to first available camera
with duvc.CameraController() as cam:
    cam.brightness = 80        # Simple assignment
    cam.pan += 10              # Relative adjustment
    print(f"Zoom: {cam.zoom}")  # Simple property read
    
    # Reset to defaults
    cam.reset_to_defaults()
```

Or find a specific camera:

```python
cam = duvc.find_camera("Logitech")
cam.brightness = 80
cam.close()
```

### 2. Result-Based API (Advanced)

**Use when:** You need explicit error handling, detailed diagnostics, or building production systems.

Result types provide detailed error information without exceptions:

```python
import duvc_ctl as duvc

devices = duvc.list_devices()
if not devices:
    print("No cameras found")
else:
    device = devices[0]
    camera_result = duvc.open_camera(device)
    
    if camera_result.is_ok():
        camera = camera_result.value()
        
        # Set property with explicit error checking
        setting = duvc.PropSetting(100, duvc.CamMode.Manual)
        result = camera.set(duvc.CamProp.Pan, setting)
        
        if result.is_ok():
            print("Pan set successfully")
        else:
            error = result.error()
            print(f"Error: {error.description()}")
    else:
        print(f"Failed to open camera: {camera_result.error().description()}")
```

## API Comparison

| Feature | Pythonic | Result-Based |
|---------|----------|--------------|
| **Device selection** | Automatic | Manual |
| **Error handling** | Exceptions | Result types |
| **Code verbosity** | Minimal | Explicit |
| **Learning curve** | Easy | Moderate |
| **Production ready** | Yes | Yes |
| **Diagnostics** | Basic | Detailed |

## Quick Start — Pythonic API

```python
import duvc_ctl as duvc

# List cameras
cameras = duvc.list_cameras()
print(f"Found {len(cameras)} camera(s): {cameras}")

# Connect and control
with duvc.CameraController() as cam:
    print(f"Connected to: {cam.device_name}")
    
    # Check supported properties
    supported = cam.get_supported_properties()
    print(f"Camera properties: {supported['camera']}")
    print(f"Video properties: {supported['video']}")
    
    # Video properties
    if 'brightness' in supported['video']:
        cam.brightness = 75
        cam.contrast = 60
        print(f"Brightness: {cam.brightness}")
    
    # PTZ properties
    if 'pan' in supported['camera']:
        cam.pan = 0      # Center
        cam.zoom = 100   # 1x zoom
```

## Quick Start — Result-Based API

```python
import duvc_ctl as duvc

devices = duvc.list_devices()
if devices:
    device = devices[0]
    
    # Open camera with explicit error handling
    result = duvc.open_camera(device)
    if result.is_ok():
        camera = result.value()
        
        # Get property with range
        range_result = camera.get_range(duvc.CamProp.Pan)
        if range_result.is_ok():
            pan_range = range_result.value()
            print(f"Pan range: {pan_range.min} to {pan_range.max}")
            
            # Set to center
            center = duvc.PropSetting(0, duvc.CamMode.Manual)
            result = camera.set(duvc.CamProp.Pan, center)
```


## API Reference

### Pythonic API — Classes

**CameraController**

High-level camera control with property-based access.

```python
# Connect to first available camera
cam = duvc.CameraController()

# Connect to specific camera
cam = duvc.CameraController(device_index=1)
cam = duvc.CameraController(device_name="Logitech")

# Use as context manager (recommended)
with duvc.CameraController() as cam:
    cam.brightness = 80
    # Auto-closes camera

# Property access
cam.brightness = 75       # Set
value = cam.brightness    # Get
range_info = cam.get_property_range('brightness')

# Device info
print(cam.device_name)
print(cam.is_connected)

# Cleanup
cam.close()
```

### Pythonic API — Device Discovery

```python
# List camera names
cameras = duvc.list_cameras()

# Find camera by name pattern
cam = duvc.find_camera("Logitech")

# Get camera info
info = duvc.get_camera_info(0)
```

### Result-Based API — Classes

**Device**

Represents a connected USB camera.

```python
device.name   # Friendly name
device.path   # System path
device.is_valid()
```

**Camera**

Opened camera connection with explicit error handling.

```python
result = duvc.open_camera(device)
if result.is_ok():
    camera = result.value()
    
    # All operations return Result types
    get_result = camera.get(duvc.CamProp.Pan)
    set_result = camera.set(duvc.CamProp.Pan, setting)
    range_result = camera.get_range(duvc.CamProp.Pan)
```

**PropSetting**

Property value and control mode.

```python
setting = duvc.PropSetting(100, duvc.CamMode.Manual)
auto_setting = duvc.PropSetting(0, duvc.CamMode.Auto)
print(setting.value, setting.mode)
```

**PropRange**

Property constraints and defaults.

```python
range_result = camera.get_range(duvc.CamProp.Pan)
if range_result.is_ok():
    prop_range = range_result.value()
    print(prop_range.min, prop_range.max, prop_range.step)
```

**Result Types**

```python
# All Result types have the same pattern
result = camera.get(duvc.CamProp.Pan)

if result.is_ok():
    value = result.value()      # Get the value
else:
    error = result.error()      # Get the error
    print(error.description())
```

### Property Enums

**CamProp** (Camera Properties)
```python
Pan, Tilt, Roll, Zoom, Exposure, Iris, Focus, Privacy, 
ScanMode, Lamp, BacklightCompensation, DigitalZoom
```

**VidProp** (Video Properties)
```python
Brightness, Contrast, Hue, Saturation, Sharpness, Gamma,
ColorEnable, WhiteBalance, BacklightCompensation, Gain
```

### Control Modes

**CamMode**
- `Auto` — Automatic adjustment
- `Manual` — Manual control with specific values


## Error Types

### Pythonic API

Standard Python exceptions:

```python
try:
    cam = duvc.CameraController()
except duvc.DeviceNotFoundError:
    print("No cameras found")
except duvc.PropertyNotSupportedError:
    print("Property not supported")
```

### Result-Based API

Result type checking with no exceptions:

```python
result = duvc.open_camera(device)
if result.is_ok():
    camera = result.value()
else:
    error = result.error()
    code = error.code()           # Get error code
    description = error.description()  # Get description
```

### Exception Types (Both APIs)

- `DuvcError` — Base exception for all errors
- `DeviceNotFoundError` — Camera disconnected or not found
- `DeviceBusyError` — Camera in use by another application
- `PropertyNotSupportedError` — Property not supported by camera
- `InvalidValueError` — Property value out of range
- `PermissionDeniedError` — Insufficient permissions
- `SystemError` — Windows/DirectShow system error


## Examples

### Property Enumeration

```python
with duvc.CameraController() as cam:
    # Get supported properties
    props = cam.get_supported_properties()
    
    print("Camera properties:")
    for prop in props['camera']:
        print(f"  - {prop}")
    
    print("Video properties:")
    for prop in props['video']:
        print(f"  - {prop}")
```

### PTZ Control

```python
with duvc.CameraController() as cam:
    # Absolute positioning
    cam.pan = 0      # Center
    cam.tilt = 0
    
    # Relative movement
    cam.pan_relative(15)   # Move 15 degrees right
    cam.zoom_relative(2)   # Zoom in 2 steps
    
    # Get current values
    print(f"Pan: {cam.pan}°, Tilt: {cam.tilt}°, Zoom: {cam.zoom}")
```

### Preset Configuration

```python
with duvc.CameraController() as cam:
    # Apply built-in preset
    cam.apply_preset('daylight')
    
    # Create custom preset
    config = {
        'brightness': 75,
        'contrast': 60,
        'saturation': 80
    }
    cam.create_custom_preset('my_preset', config)
    
    # Apply custom preset
    cam.apply_preset('my_preset')
```

### Batch Operations

```python
with duvc.CameraController() as cam:
    # Set multiple properties at once
    settings = {
        'brightness': 80,
        'contrast': 65,
        'saturation': 75
    }
    results = cam.set_multiple(settings)
    
    # Get multiple properties at once
    values = cam.get_multiple(['brightness', 'contrast', 'saturation'])
```

### Vendor Properties

```python
import uuid
import duvc_ctl as duvc

device = duvc.list_devices()[0]

# Read vendor property
vendor_guid = uuid.UUID('12345678-1234-5678-9abc-123456789abc')
success, data = duvc.read_vendor_property(device, vendor_guid, 1)
if success:
    print(f"Property data: {data.hex()}")

# Write vendor property
success = duvc.write_vendor_property(device, vendor_guid, 1, b'\\x01\\x02\\x03')
```

### Error Handling Patterns

```python
# Pythonic API - with exceptions
try:
    with duvc.CameraController() as cam:
        cam.brightness = 999  # Out of range
except duvc.InvalidValueError as e:
    print(f"Invalid value: {e}")

# Result-Based API - explicit checking
result = duvc.open_camera(device)
if result.is_ok():
    camera = result.value()
    set_result = camera.set(duvc.CamProp.Pan, setting)
    if not set_result.is_ok():
        print(f"Failed: {set_result.error().description()}")
```


## Requirements

- Windows 10+ (x64)
- Python 3.8+
- No additional drivers or SDKs required


## Performance

- **Native C++ backend** with DirectShow for optimal performance
- **Thread-safe** for concurrent access
- **Minimal overhead** — thin Python wrapper over C++ core


## Other Interfaces

- **C++ Library** — Native API for C++ applications
- **CLI Tool** — `duvc-cli.exe` for scripting and automation


## Links

- **Releases**: https://github.com/allanhanan/duvc-ctl/releases
- **Documentation**: https://allanhanan.github.io/duvc-ctl/sphinx/api/python/index.html
- **Source Code**: https://github.com/allanhanan/duvc-ctl
- **Issues**: https://github.com/allanhanan/duvc-ctl/issues
