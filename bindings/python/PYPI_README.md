# duvc-ctl

`duvc-ctl` is a lightweight Python library for controlling USB Video Class (UVC) camera properties on Windows using the native DirectShow API.  
It exposes camera and video properties (PTZ, focus, exposure, brightness, etc.), supports device monitoring with hotplug detection, and provides access to vendor-specific property sets — all without vendor SDKs, extra drivers, or dependencies.

## Key Features

- **Camera & Video Properties**: Get/set PTZ controls, exposure, focus, white balance, gain, and other IAMCameraControl/IAMVideoProcAmp properties.  
- **Device Monitoring**: List devices, check connectivity, and handle hotplug events with callbacks.  
- **Vendor Extensions**: Read/write custom property sets (e.g., Logitech-specific controls) for advanced hardware integration.  
- **Result-Based Error Handling**: Safe, explicit error handling with Result types and custom exceptions.  
- **Multiple API Styles**: Result-based, direct functions, and exception-based APIs for different use cases.

Works on **Windows 10+ with Python 3.8+**. Suitable for computer vision, robotics, video streaming, and automation projects requiring precise USB camera control.

## Installation

```

pip install duvc-ctl

```

## Quick Start

```

import duvc_ctl as duvc

# List all connected cameras

devices = duvc.list_devices()
print(f"Found {len(devices)} cameras")

if devices:
device = devices  \# Get first camera
print(f"Camera: {device.name}")

    # Method 1: High-level Camera API (recommended)
    camera_result = duvc.open_camera(device)
    if camera_result.is_ok():
        camera = camera_result.value()
        
        # Set zoom to 2x with manual control
        zoom_setting = duvc.PropSetting(200, duvc.CamMode.Manual)
        result = camera.set(duvc.CamProp.Zoom, zoom_setting)
        if result.is_ok():
            print("Zoom set successfully")
        
        # Auto-adjust brightness
        brightness = duvc.PropSetting(0, duvc.CamMode.Auto)
        camera.set(duvc.VidProp.Brightness, brightness)
    
    # Method 2: Exception-based API (convenience)
    try:
        camera = duvc.open_camera_or_throw(device)
        zoom_setting = duvc.PropSetting(200, duvc.CamMode.Manual)
        camera.set(duvc.CamProp.Zoom, zoom_setting)
    except duvc.DuvcError as e:
        print(f"Error: {e}")
```

## API Reference

### Core Classes

**Device**
Represents a camera device.
```

device = duvc.Device()
print(device.name)  \# Camera friendly name
print(device.path)  \# Unique device path
print(device.is_valid())  \# Check validity

```

**Camera**
High-level camera control interface.
```

camera_result = duvc.open_camera(device)
if camera_result.is_ok():
camera = camera_result.value()
print(camera.is_valid())

    # Get property
    pan_result = camera.get(duvc.CamProp.Pan)
    if pan_result.is_ok():
        setting = pan_result.value()
        print(f"Pan: {setting.value}")
    
    # Set property
    new_setting = duvc.PropSetting(0, duvc.CamMode.Manual)
    result = camera.set(duvc.CamProp.Pan, new_setting)
```

**PropSetting**
Property value and control mode.
```

setting = duvc.PropSetting(100, duvc.CamMode.Manual)  \# Manual
auto_setting = duvc.PropSetting(0, duvc.CamMode.Auto)  \# Automatic
print(setting.value, setting.mode)

```

**PropRange**
Property constraints and defaults.
```

camera_result = duvc.open_camera(device)
if camera_result.is_ok():
camera = camera_result.value()
range_result = camera.get_range(duvc.CamProp.Pan)
if range_result.is_ok():
prop_range = range_result.value()
print(prop_range.min, prop_range.max, prop_range.step, prop_range.default_val)

```

**Result Types**
Safe error handling with Result<T> objects.
```


# All main functions return Result types

camera_result = duvc.open_camera(device)       \# Result<Camera>
setting_result = camera.get(duvc.CamProp.Pan)  \# Result<PropSetting>
range_result = camera.get_range(duvc.CamProp.Pan)  \# Result<PropRange>

# Check results

if camera_result.is_ok():
camera = camera_result.value()
else:
error = camera_result.error()
print(f"Error: {error.description()}")

```

### Camera Properties (CamProp)

- `Pan`, `Tilt`, `Roll`, `Zoom`
- `Exposure`, `Iris`, `Focus`
- `Privacy`, `ScanMode`, `Lamp`, `BacklightCompensation`

### Video Properties (VidProp)

- `Brightness`, `Contrast`, `Saturation`, `Hue`
- `Sharpness`, `Gamma`, `ColorEnable`, `WhiteBalance`, `Gain`
- `BacklightCompensation`

### Control Modes

**CamMode**
- `Auto` — Camera automatically adjusts property
- `Manual` — Manual control with specific values

## Core Functions

### Device Management
```

devices = duvc.list_devices()  \# List all devices
connected = duvc.is_device_connected(device)  \# Check connection

# Device capabilities

caps_result = duvc.get_device_capabilities(device)
if caps_result.is_ok():
capabilities = caps_result.value()
print(f"Accessible: {capabilities.is_device_accessible()}")

```

### Camera Control (High-level API)
```
# Open camera

camera_result = duvc.open_camera(device)
if camera_result.is_ok():
camera = camera_result.value()

    # Get property
    result = camera.get(duvc.CamProp.Pan)
    if result.is_ok():
        setting = result.value()
        print(f"Current pan: {setting.value}")
    
    # Set property
    new_setting = duvc.PropSetting(0, duvc.CamMode.Manual)
    result = camera.set(duvc.CamProp.Pan, new_setting)
    if result.is_ok():
        print("Pan set successfully")
    
    # Get range
    range_result = camera.get_range(duvc.CamProp.Zoom)
    if range_result.is_ok():
        prop_range = range_result.value()
        print(f"Zoom range: {prop_range.min}-{prop_range.max}")
```

### Exception-based API (Convenience)
```

try:
camera = duvc.open_camera_or_throw(device)
capabilities = duvc.get_device_capabilities_or_throw(device)

    # Work with camera directly
    result = camera.get(duvc.CamProp.Pan)
    if result.is_ok():
        setting = result.value()
        print(f"Pan: {setting.value}")
    except duvc.DuvcError as e:
print(f"Camera error: {e}")

```

### Vendor Properties
Access vendor-specific UVC properties by GUID.

```

from uuid import UUID

# Example: property set GUID

prop_set_uuid = UUID("{6bdd1fc6-810f-11d0-bec7-08002be2092f}")

# Set vendor property

data = bytes()
success = duvc.set_vendor_property(device, prop_set_uuid, 1, data)
print("Set successful:", success)

# Get vendor property

success, data = duvc.get_vendor_property(device, prop_set_uuid, 1)
if success:
print("Data:", data)

```

### String Utilities
```


# Convert enums to strings

print(duvc.to_string(duvc.CamProp.Pan))        \# "Pan"
print(duvc.to_string(duvc.VidProp.Brightness)) \# "Brightness"
print(duvc.to_string(duvc.CamMode.Auto))       \# "Auto"

```

## Examples

### PTZ Camera Control
```

devices = duvc.list_devices()
if devices:
camera_result = duvc.open_camera(devices)
if camera_result.is_ok():
camera = camera_result.value()

        # Center camera
        center = duvc.PropSetting(0, duvc.CamMode.Manual)
        camera.set(duvc.CamProp.Pan, center)
        camera.set(duvc.CamProp.Tilt, center)
        
        # Set 2x zoom
        zoom = duvc.PropSetting(200, duvc.CamMode.Manual)
        camera.set(duvc.CamProp.Zoom, zoom)
```

### Property Validation
```

camera_result = duvc.open_camera(devices)
if camera_result.is_ok():
camera = camera_result.value()
range_result = camera.get_range(duvc.CamProp.Focus)
if range_result.is_ok():
prop_range = range_result.value()
mid_focus = (prop_range.min + prop_range.max) // 2
setting = duvc.PropSetting(mid_focus, duvc.CamMode.Manual)
camera.set(duvc.CamProp.Focus, setting)

```

### Video Processing
```

camera_result = duvc.open_camera(devices)
if camera_result.is_ok():
camera = camera_result.value()

    # Auto white balance
    wb = duvc.PropSetting(0, duvc.CamMode.Auto)
    camera.set(duvc.VidProp.WhiteBalance, wb)
    
    # Manual brightness
    brightness = duvc.PropSetting(75, duvc.CamMode.Manual)
    camera.set(duvc.VidProp.Brightness, brightness)
```

### Device Capabilities
```

caps_result = duvc.get_device_capabilities(device)
if caps_result.is_ok():
capabilities = caps_result.value()

    # Check what's supported
    if capabilities.supports_camera_property(duvc.CamProp.Pan):
        cap = capabilities.get_camera_capability(duvc.CamProp.Pan)
        current = cap.current
        prop_range = cap.range
        print(f"Pan: {current.value} (range: {prop_range.min}-{prop_range.max})")
```

### Error Handling
```


# Result-based error handling

camera_result = duvc.open_camera(device)
if camera_result.is_ok():
camera = camera_result.value()

    pan_result = camera.get(duvc.CamProp.Pan)
    if pan_result.is_ok():
        setting = pan_result.value()
        print(f"Pan: {setting.value}")
    else:
        error = pan_result.error()
        print(f"Failed to get pan: {error.description()}")
    else:
error = camera_result.error()
print(f"Failed to open camera: {error.description()}")

# Exception-based error handling

try:
camera = duvc.open_camera_or_throw(device)
result = camera.get(duvc.CamProp.Pan)
if result.is_ok():
setting = result.value()
print(f"Pan: {setting.value}")
except duvc.DeviceNotFoundError:
print("Camera not found")
except duvc.PropertyNotSupportedError:
print("Pan not supported")
except duvc.DuvcError as e:
print(f"Camera error: {e}")

```

## Error Types

All errors derive from `DuvcError`. Specific exceptions include:
- `DeviceNotFoundError` - Camera disconnected or not found
- `DeviceBusyError` - Camera in use by another application  
- `InvalidValueError` - Property value out of range
- `PropertyNotSupportedError` - Property not supported by camera
- `PermissionDeniedError` - Insufficient permissions
- `SystemError` - Windows/DirectShow system error

## Features

- **Result-based Error Handling**: Explicit success/failure with detailed error information
- **High-level Camera API**: Object-oriented interface with automatic resource management
- **Exception-based API**: Traditional exception handling for convenience
- **Device Capabilities**: Query supported properties and ranges before use
- **String Utilities**: Convert enums to human-readable strings
- **Vendor Property Support**: Access manufacturer-specific controls via GUIDs
- **Thread-safe**: Safe for use in multi-threaded applications
- **Native Performance**: C++ backend with DirectShow for optimal performance

## Requirements

- Windows 7/8/8.1/10/11 (x64)
- Python 3.8+
- No additional drivers or SDKs required

## Other Interfaces

- **C++ Library** — Native API for C++ applications
- **CLI Tool** — `duvc-cli.exe` for scripting and automation

## Links

- **Releases**: [https://github.com/allanhanan/duvc-ctl/releases](https://github.com/allanhanan/duvc-ctl/releases)
- **Full Documentation**: [https://github.com/allanhanan/duvc-ctl#readme](https://github.com/allanhanan/duvc-ctl#readme)
- **Source Code**: [https://github.com/allanhanan/duvc-ctl](https://github.com/allanhanan/duvc-ctl)
- **Issues**: [https://github.com/allanhanan/duvc-ctl/issues](https://github.com/allanhanan/duvc-ctl/issues)
```