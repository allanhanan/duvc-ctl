# duvc-ctl

Python library for controlling USB cameras on Windows using DirectShow API without external drivers/SDKs. Read and write camera properties like zoom, focus, pan, tilt, and exposure.

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

    # Set zoom to 2x with manual control
    zoom_setting = duvc.PropSetting(200, duvc.CamMode.Manual)
    duvc.set(device, duvc.CamProp.Zoom, zoom_setting)
    
    # Auto-adjust brightness
    brightness = duvc.PropSetting(0, duvc.CamMode.Auto)
    duvc.set(device, duvc.VidProp.Brightness, brightness)
```

## Complete API Reference

### Core Classes

**Device** - Represents a camera device
```

device = duvc.Device()
print(device.name)  \# Camera friendly name
print(device.path)  \# Unique device path

```

**PropSetting** - Property value and control mode
```


# Manual control with specific value

setting = duvc.PropSetting(100, duvc.CamMode.Manual)

# Automatic control

auto_setting = duvc.PropSetting(0, duvc.CamMode.Auto)

```

**PropRange** - Property constraints and defaults
```

range_info = duvc.PropRange()
if duvc.get_range(device, duvc.CamProp.Pan, range_info):
print(f"Pan range: {range_info.min} to {range_info.max}")
print(f"Step: {range_info.step}")
print(f"Default: {range_info.default_val}")

```

### Camera Properties (CamProp)

Access all DirectShow IAMCameraControl properties:

**Basic PTZ Controls:**
- `duvc.CamProp.Pan` - Horizontal camera movement
- `duvc.CamProp.Tilt` - Vertical camera movement  
- `duvc.CamProp.Roll` - Camera rotation
- `duvc.CamProp.Zoom` - Optical zoom level

**Image Controls:**
- `duvc.CamProp.Exposure` - Exposure time
- `duvc.CamProp.Iris` - Iris/aperture opening
- `duvc.CamProp.Focus` - Focus distance

**Advanced Features:**
- `duvc.CamProp.Privacy` - Privacy shutter control
- `duvc.CamProp.ScanMode` - Progressive/interlaced
- `duvc.CamProp.Lamp` - Camera light/flash
- `duvc.CamProp.BacklightCompensation` - Backlight adjustment

**Relative Controls (Delta Adjustments):**
- `duvc.CamProp.PanRelative` - Relative pan movement
- `duvc.CamProp.TiltRelative` - Relative tilt movement
- `duvc.CamProp.ZoomRelative` - Relative zoom change
- `duvc.CamProp.ExposureRelative` - Relative exposure adjustment
- `duvc.CamProp.IrisRelative` - Relative iris adjustment
- `duvc.CamProp.FocusRelative` - Relative focus adjustment

**Composite/Special Controls:**
- `duvc.CamProp.PanTilt` - Combined pan/tilt control
- `duvc.CamProp.PanTiltRelative` - Combined relative movement
- `duvc.CamProp.FocusSimple` - Simplified focus control
- `duvc.CamProp.DigitalZoom` - Digital zoom level
- `duvc.CamProp.DigitalZoomRelative` - Relative digital zoom

### Video Properties (VidProp)

Access all DirectShow IAMVideoProcAmp properties:

**Basic Image Adjustment:**
- `duvc.VidProp.Brightness` - Image brightness level
- `duvc.VidProp.Contrast` - Image contrast level
- `duvc.VidProp.Saturation` - Color saturation
- `duvc.VidProp.Hue` - Color hue shift

**Advanced Processing:**
- `duvc.VidProp.Sharpness` - Image sharpness
- `duvc.VidProp.Gamma` - Gamma correction
- `duvc.VidProp.ColorEnable` - Color/monochrome mode
- `duvc.VidProp.WhiteBalance` - White balance adjustment
- `duvc.VidProp.Gain` - Signal amplification
- `duvc.VidProp.BacklightCompensation` - Backlight correction

### Control Modes

**CamMode** - Property control modes:
- `duvc.CamMode.Auto` - Camera automatically adjusts property
- `duvc.CamMode.Manual` - Manual control with specific values

## Core Functions

### Device Management
```


# Get all available cameras

devices = duvc.list_devices()

# Check if device is connected

connected = duvc.is_device_connected(device)

# Clear connection cache for fresh connections

duvc.clear_connection_cache()

```

### Property Control
```


# Get property value

setting = duvc.PropSetting()
success = duvc.get(device, duvc.CamProp.Pan, setting)

# Set property value

new_setting = duvc.PropSetting(0, duvc.CamMode.Manual)
success = duvc.set(device, duvc.CamProp.Pan, new_setting)

# Get property range/constraints

prop_range = duvc.PropRange()
success = duvc.get_range(device, duvc.CamProp.Zoom, prop_range)

```

### Device Monitoring
```


# Register callback for device changes

def on_device_change(added, device_path):
status = "ADDED" if added else "REMOVED"
print(f"Device {status}: {device_path}")

duvc.register_device_change_callback(on_device_change)

# Unregister callback

duvc.unregister_device_change_callback()

```

### Utility Functions
```


# Convert mode enum to human-readable string

mode_str = duvc.cam_mode_to_string(duvc.CamMode.Auto)    \# Returns "Auto"
mode_str = duvc.cam_mode_to_string(duvc.CamMode.Manual)  \# Returns "Manual"

```

## Practical Examples

### PTZ Camera Control
```

import duvc_ctl as duvc

devices = duvc.list_devices()
if devices:
camera = devices  \# Get first camera

    # Center camera
    center = duvc.PropSetting(0, duvc.CamMode.Manual)
    duvc.set(camera, duvc.CamProp.Pan, center)
    duvc.set(camera, duvc.CamProp.Tilt, center)
    
    # Set 2x zoom
    zoom = duvc.PropSetting(200, duvc.CamMode.Manual)
    duvc.set(camera, duvc.CamProp.Zoom, zoom)
```

### Property Validation
```


# Always check ranges before setting values

devices = duvc.list_devices()
if devices:
device = devices
range_info = duvc.PropRange()
if duvc.get_range(device, duvc.CamProp.Focus, range_info):
\# Set focus to middle of range
mid_focus = (range_info.min + range_info.max) // 2
focus_setting = duvc.PropSetting(mid_focus, duvc.CamMode.Manual)
duvc.set(device, duvc.CamProp.Focus, focus_setting)

```

### Video Processing
```


# Enhance video quality

devices = duvc.list_devices()
if devices:
device = devices  \# Get first camera

    # Auto white balance
    wb = duvc.PropSetting(0, duvc.CamMode.Auto)
    duvc.set(device, duvc.VidProp.WhiteBalance, wb)
    
    # Manual brightness adjustment
    brightness = duvc.PropSetting(75, duvc.CamMode.Manual)
    duvc.set(device, duvc.VidProp.Brightness, brightness)
    
    # Increase saturation
    saturation = duvc.PropSetting(120, duvc.CamMode.Manual)
    duvc.set(device, duvc.VidProp.Saturation, saturation)
```

### Error Handling
```
try:
    devices = duvc.list_devices()
    if devices:
        device = devices[0]  # Get first camera

        # Check if property is supported
        range_info = duvc.PropRange()
        if duvc.get_range(device, duvc.CamProp.Pan, range_info):
            # Property is supported
            setting = duvc.PropSetting(0, duvc.CamMode.Manual)
            success = duvc.set(device, duvc.CamProp.Pan, setting)
            if not success:
                print("Failed to set pan - camera may be busy")
        else:
            print("Pan control not supported on this camera")
except Exception as e:
    print(f"Camera control error: {e}")


```

## Features

- **Complete UVC Control**: Access to all 24 camera properties and 10 video properties
- **Dual Control Modes**: Both automatic and manual property control
- **Range Validation**: Get min/max/step values for safe property setting  
- **Device Monitoring**: Real-time hot-plug detection with callbacks
- **Connection Pooling**: Optimized performance with automatic connection caching
- **Thread Safe**: Safe for multi-threaded applications
- **Native Performance**: Built on C++ with DirectShow for optimal speed

## Requirements

- Windows 10/11 (x64)
- Python 3.8+
- No additional dependencies required

## Other Interfaces

**duvc-ctl** is also available as:

- **C++ Library**: Native API for integration into C++ applications
- **CLI Tool**: Standalone executable for scripting and automation (`duvc-cli.exe`)

Both share the same core functionality as this Python package.

## Common Use Cases

- Automate camera settings for livestreaming/broadcasting
- Control PTZ cameras in robotics, kiosks, and classrooms  
- Build computer vision pipelines with adaptive camera settings
- Create testing rigs for camera quality assurance
- Replace vendor-specific camera software with scriptable control
- Integrate camera control into larger automation systems

## Links

- **CLI Tool & C++ API**: https://github.com/allanhanan/duvc-ctl/releases
- **Full Documentation**: https://github.com/allanhanan/duvc-ctl#readme
- **Source Code**: https://github.com/allanhanan/duvc-ctl
- **Issue Tracker**: https://github.com/allanhanan/duvc-ctl/issues
