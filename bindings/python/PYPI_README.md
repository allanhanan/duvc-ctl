# duvc-ctl

`duvc-ctl` is a lightweight Python library for controlling USB Video Class (UVC) camera properties on Windows using the native DirectShow API.  
It exposes camera and video properties (PTZ, focus, exposure, brightness, etc.), supports device monitoring with hotplug detection, and provides access to vendor-specific property sets — all without vendor SDKs, extra drivers, or dependencies.

## Key Features

- **Camera & Video Properties**: Get/set PTZ controls, exposure, focus, white balance, gain, and other IAMCameraControl/IAMVideoProcAmp properties.  
- **Device Monitoring**: List devices, check connectivity, and handle hotplug events with callbacks.  
- **Vendor Extensions**: Read/write custom property sets (e.g., Logitech-specific controls) for advanced hardware integration.  
- **Error Handling & Logging**: Clear and Robust result types, custom exceptions.  

Works on **Windows 10+ with Python 3.8+**. Suitable for computer vision, robotics, video streaming, and automation projects requiring precise USB camera control.


## Installation

```bash
pip install duvc-ctl
```

## Quick Start

```python
import duvc_ctl as duvc

# List all connected cameras
devices = duvc.list_devices()
print(f"Found {len(devices)} cameras")

if devices:
    device = devices[0]  # Get first camera
    print(f"Camera: {device.name}")

    # Set zoom to 2x with manual control
    zoom_setting = duvc.PropSetting(200, duvc.CamMode.Manual)
    duvc.set(device, duvc.CamProp.Zoom, zoom_setting)
    
    # Auto-adjust brightness
    brightness = duvc.PropSetting(0, duvc.CamMode.Auto)
    duvc.set(device, duvc.VidProp.Brightness, brightness)
```

## API Reference

### Core Classes

**Device**
Represents a camera device.
```python
device = duvc.Device()
print(device.name)  # Camera friendly name
print(device.path)  # Unique device path
```

**PropSetting**
Property value and control mode.
```python
setting = duvc.PropSetting(100, duvc.CamMode.Manual)  # Manual
auto_setting = duvc.PropSetting(0, duvc.CamMode.Auto)  # Automatic
```

**PropRange**
Property constraints and defaults.
```python
range_info = duvc.PropRange()
if duvc.get_range(device, duvc.CamProp.Pan, range_info):
    print(range_info.min, range_info.max, range_info.step, range_info.default_val)
```

### Camera Properties (CamProp)

- `Pan`, `Tilt`, `Roll`, `Zoom`
- `Exposure`, `Iris`, `Focus`
- `Privacy`, `ScanMode`, `Lamp`, `BacklightCompensation`
- Relative controls: `PanRelative`, `TiltRelative`, `ZoomRelative`, `ExposureRelative`, `IrisRelative`, `FocusRelative`
- Composite controls: `PanTilt`, `PanTiltRelative`, `FocusSimple`, `DigitalZoom`, `DigitalZoomRelative`

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
```python
devices = duvc.list_devices()
connected = duvc.is_device_connected(device)
duvc.clear_connection_cache()
```

### Property Control
```python
setting = duvc.PropSetting()
duvc.get(device, duvc.CamProp.Pan, setting)

new_setting = duvc.PropSetting(0, duvc.CamMode.Manual)
duvc.set(device, duvc.CamProp.Pan, new_setting)

prop_range = duvc.PropRange()
duvc.get_range(device, duvc.CamProp.Zoom, prop_range)
```

### Device Monitoring
```python
def on_device_change(event_type, device):
    print("Event:", event_type, "Device:", device.name)

duvc.register_device_change_callback(on_device_change)
duvc.unregister_device_change_callback()
```

### Vendor Properties
Access vendor-specific UVC properties by GUID.

```python
import uuid

# Example: property set GUID
prop_set_uuid = uuid.UUID("{6bdd1fc6-810f-11d0-bec7-08002be2092f}")
guid_obj = duvc.guid_from_uuid(prop_set_uuid)

# Write vendor property
ok = duvc.write_vendor_property(device, guid_obj, 1, bytes([1,2,3,4]))
print("write ok?", ok)

# Read vendor property
ok, data = duvc.read_vendor_property(device, guid_obj, 1)
print("read ok?", ok, "data:", data)
```

### Errors and Exceptions
All errors derive from `DuvcError`. Specific exceptions include:
- `DeviceNotFoundError`
- `DeviceBusyError`
- `InvalidValueError`
- `PropertyNotSupportedError`

## Examples

### PTZ Camera Control
```python
camera = duvc.list_devices()[0]

# Center camera
center = duvc.PropSetting(0, duvc.CamMode.Manual)
duvc.set(camera, duvc.CamProp.Pan, center)
duvc.set(camera, duvc.CamProp.Tilt, center)

# Set 2x zoom
zoom = duvc.PropSetting(200, duvc.CamMode.Manual)
duvc.set(camera, duvc.CamProp.Zoom, zoom)
```

### Property Validation
```python
camera = duvc.list_devices()[0]
range_info = duvc.PropRange()
if duvc.get_range(camera, duvc.CamProp.Focus, range_info):
    mid_focus = (range_info.min + range_info.max) // 2
    setting = duvc.PropSetting(mid_focus, duvc.CamMode.Manual)
    duvc.set(camera, duvc.CamProp.Focus, setting)
```

### Video Processing
```python
camera = duvc.list_devices()[0]

wb = duvc.PropSetting(0, duvc.CamMode.Auto)
duvc.set(camera, duvc.VidProp.WhiteBalance, wb)

brightness = duvc.PropSetting(75, duvc.CamMode.Manual)
duvc.set(camera, duvc.VidProp.Brightness, brightness)

saturation = duvc.PropSetting(120, duvc.CamMode.Manual)
duvc.set(camera, duvc.VidProp.Saturation, saturation)
```

### Error Handling
```python
try:
    camera = duvc.list_devices()[0]
    range_info = duvc.PropRange()
    if duvc.get_range(camera, duvc.CamProp.Pan, range_info):
        setting = duvc.PropSetting(0, duvc.CamMode.Manual)
        if not duvc.set(camera, duvc.CamProp.Pan, setting):
            print("Failed to set pan")
    else:
        print("Pan not supported")
except duvc.DuvcError as e:
    print("Camera error:", e)
```

## Features

- Control all standard UVC camera and video properties
- Automatic and manual control modes
- Range validation for safe property setting
- Vendor-specific property support via GUIDs
- Device hot-plug monitoring with callbacks
- Thread safe and connection caching
- Native C++ backend with DirectShow for performance

## Requirements

- Windows 10/11 (x64)
- Python 3.8+

## Other Interfaces

- **C++ Library** — Native API
- **CLI Tool** — `duvc-cli.exe` for scripting and automation

## Links

- **Releases**: https://github.com/allanhanan/duvc-ctl/releases
- **Full Documentation**: https://github.com/allanhanan/duvc-ctl#readme
- **Source Code**: https://github.com/allanhanan/duvc-ctl
- **Issues**: https://github.com/allanhanan/duvc-ctl/issues
