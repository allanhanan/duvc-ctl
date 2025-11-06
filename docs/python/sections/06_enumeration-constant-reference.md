## 6. Enumeration & Constant Reference


### 6.1 Property Enumerations

#### CamProp - Camera control properties (22 total values)

| Property | Enum Constant | Type | Range | Description |
| :-- | :-- | :-- | :-- | :-- |
| Pan | `duvc.CamProp.Pan` | int | -180 to 180 | Horizontal left/right rotation in degrees |
| Tilt | `duvc.CamProp.Tilt` | int | -90 to 90 | Vertical up/down rotation in degrees |
| Roll | `duvc.CamProp.Roll` | int | -180 to 180 | Rotation around optical axis in degrees |
| Zoom | `duvc.CamProp.Zoom` | int | 100-400+ | Zoom multiplier in steps (100=1x, 200=2x) |
| Exposure | `duvc.CamProp.Exposure` | int | Device-dependent | Exposure time in log2 units or milliseconds |
| Iris | `duvc.CamProp.Iris` | int | 0-255 | Iris aperture f-stop (0=most open, 255=closed) |
| Focus | `duvc.CamProp.Focus` | int | 0-255+ | Focus distance (0=infinity, 255=closest) |
| ScanMode | `duvc.CamProp.ScanMode` | int | 0-2 | Interlaced (0), Progressive (1), or both (2) |
| Privacy | `duvc.CamProp.Privacy` | bool | True/False | Hardware privacy shutter on/off |
| PanRelative | `duvc.CamProp.PanRelative` | int | Device-dependent | Pan movement amount per step (relative) |
| TiltRelative | `duvc.CamProp.TiltRelative` | int | Device-dependent | Tilt movement amount per step (relative) |
| RollRelative | `duvc.CamProp.RollRelative` | int | Device-dependent | Roll movement amount per step (relative) |
| ZoomRelative | `duvc.CamProp.ZoomRelative` | int | Device-dependent | Zoom change amount per step (relative) |
| ExposureRelative | `duvc.CamProp.ExposureRelative` | int | Device-dependent | Exposure adjustment per step (relative) |
| IrisRelative | `duvc.CamProp.IrisRelative` | int | Device-dependent | Iris adjustment per step (relative) |
| FocusRelative | `duvc.CamProp.FocusRelative` | int | Device-dependent | Focus adjustment per step (relative) |
| PanTilt | `duvc.CamProp.PanTilt` | int | Device-dependent | Combined pan/tilt movement (paired value) |
| PanTiltRelative | `duvc.CamProp.PanTiltRelative` | int | Device-dependent | Combined pan/tilt relative movement |
| FocusSimple | `duvc.CamProp.FocusSimple` | int | 0-3 | Simple focus: 0=auto, 1=manual, 2=near, 3=far |
| DigitalZoom | `duvc.CamProp.DigitalZoom` | int | 100-400+ | Digital zoom multiplier (separate from optical) |
| DigitalZoomRelative | `duvc.CamProp.DigitalZoomRelative` | int | Device-dependent | Digital zoom adjustment per step (relative) |
| BacklightCompensation | `duvc.CamProp.BacklightCompensation` | int | 0-255 | Backlight compensation strength |

**Property grouping**:

- **Absolute positioning**: Pan, Tilt, Roll, Zoom, Exposure, Iris, Focus, DigitalZoom, ScanMode, Privacy, FocusSimple, BacklightCompensation.
- **Relative movement**: PanRelative, TiltRelative, RollRelative, ZoomRelative, ExposureRelative, IrisRelative, FocusRelative, DigitalZoomRelative.
- **Combined operations**: PanTilt, PanTiltRelative.

***

#### VidProp - Video/image properties (10 total values)

| Property | Enum Constant | Type | Range | Description |
| :-- | :-- | :-- | :-- | :-- |
| Brightness | `duvc.VidProp.Brightness` | int | 0-255 | Image brightness (0=darkest, 255=brightest) |
| Contrast | `duvc.VidProp.Contrast` | int | 0-255 | Contrast between light and dark areas |
| Hue | `duvc.VidProp.Hue` | int | -180 to 180 | Color hue shift in degrees |
| Saturation | `duvc.VidProp.Saturation` | int | 0-255 | Color saturation (0=grayscale, 255=vivid) |
| Sharpness | `duvc.VidProp.Sharpness` | int | 0-255 | Edge sharpening amount |
| Gamma | `duvc.VidProp.Gamma` | int | Device-dependent | Gamma correction curve |
| ColorEnable | `duvc.VidProp.ColorEnable` | bool | True/False | Enable/disable color processing |
| WhiteBalance | `duvc.VidProp.WhiteBalance` | int | Device-dependent | White balance temperature or preset |
| BacklightCompensation | `duvc.VidProp.BacklightCompensation` | int | 0-255 | Backlight compensation compensation strength |
| Gain | `duvc.VidProp.Gain` | int | 0-255 | Signal amplification (0=minimum) |


***

#### Property capability matrix reference

**Auto mode support by property**:


| Property | Auto Support | Manual Support | Notes |
| :-- | :-- | :-- | :-- |
| Brightness | Yes | Yes | Most cameras support auto brightness |
| Contrast | Sometimes | Yes | Device-dependent auto support |
| Saturation | Sometimes | Yes | Device-dependent auto support |
| Hue | No | Yes | Typically manual only |
| Gamma | No | Yes | Typically manual only |
| Sharpness | Sometimes | Yes | Device-dependent auto support |
| Gain | Yes | Yes | Auto-gain common on cameras |
| WhiteBalance | Yes | Yes | Auto white balance is very common |
| ColorEnable | No | Yes | On/off control only |
| BacklightCompensation | Sometimes | Yes | Device-dependent auto support |
| Focus | Yes | Yes | Autofocus vs manual focus |
| Exposure | Yes | Yes | Auto-exposure very common |
| Pan/Tilt/Zoom | No | Yes | Manual positioning only |
| Privacy | No | Yes | Binary on/off only |
| ScanMode | No | Yes | Fixed selection only |

**Usage pattern for auto support**:

```python
# Always check before using auto
cap_result = caps.get_video_capability(duvc.VidProp.WhiteBalance)
if cap_result.is_ok():
    cap = cap_result.value()
    if cap.supports_auto():
        camera.set_auto(duvc.VidProp.WhiteBalance)
    else:
        # Manual only
        r = cap.range
        setting = duvc.PropSetting((r.min + r.max) // 2, 'manual')
        camera.set(duvc.VidProp.WhiteBalance, setting)
```

### 6.2 Control \& Error Enumerations

#### CamMode - Property control mode (2 total values)

| Mode | Enum Constant | Description |
| :-- | :-- | :-- |
| Auto | `duvc.CamMode.Auto` | Automatic control by camera (device adjusts property) |
| Manual | `duvc.CamMode.Manual` | Manual control by application (user specifies value) |

**Usage**:

```python
# Set brightness with manual mode
setting = duvc.PropSetting(value=128, mode=duvc.CamMode.Manual)
camera.set(duvc.VidProp.Brightness, setting)

# Enable auto mode (value ignored by device)
setting = duvc.PropSetting(value=0, mode=duvc.CamMode.Auto)
camera.set(duvc.VidProp.Brightness, setting)

# Check capability before auto
cap_result = caps.get_video_capability(duvc.VidProp.WhiteBalance)
if cap_result.is_ok() and cap_result.value().supports_auto():
    setting = duvc.PropSetting(value=0, mode=duvc.CamMode.Auto)
    camera.set(duvc.VidProp.WhiteBalance, setting)
```


***

#### ErrorCode - Error codes (9 total values)

| Code | Enum Constant | Description |
| :-- | :-- | :-- |
| Success | `duvc.ErrorCode.Success` | Operation succeeded (0x00) |
| DeviceNotFound | `duvc.ErrorCode.DeviceNotFound` | Device not found or disconnected (0x01) |
| DeviceBusy | `duvc.ErrorCode.DeviceBusy` | Device busy or in use elsewhere (0x02) |
| PropertyNotSupported | `duvc.ErrorCode.PropertyNotSupported` | Property not supported by device (0x03) |
| InvalidValue | `duvc.ErrorCode.InvalidValue` | Property value out of range (0x04) |
| PermissionDenied | `duvc.ErrorCode.PermissionDenied` | Insufficient permissions (0x05) |
| SystemError | `duvc.ErrorCode.SystemError` | System/platform-specific error (0x06) |
| InvalidArgument | `duvc.ErrorCode.InvalidArgument` | Invalid function argument (0x07) |
| NotImplemented | `duvc.ErrorCode.NotImplemented` | Feature not implemented (0x08) |

**Error code cross-reference**:

```python
result = camera.get(duvc.VidProp.Brightness)
if result.is_error():
    error = result.error()
    code = error.code()
    
    if code == duvc.ErrorCode.DeviceNotFound:
        print("Device disconnected")
    elif code == duvc.ErrorCode.PropertyNotSupported:
        print("Property not supported")
    elif code == duvc.ErrorCode.InvalidValue:
        print("Value out of range")
    elif code == duvc.ErrorCode.PermissionDenied:
        print("Need elevated privileges")
    else:
        print(f"Error: {error.description()}")
```


***

#### LogLevel - Logging severity (5 total values)

| Level | Enum Constant | Description |
| :-- | :-- | :-- |
| Debug | `duvc.LogLevel.Debug` | Detailed debugging information (lowest) |
| Info | `duvc.LogLevel.Info` | General informational messages |
| Warning | `duvc.LogLevel.Warning` | Warning conditions |
| Error | `duvc.LogLevel.Error` | Error conditions |
| Critical | `duvc.LogLevel.Critical` | Critical error conditions (highest) |

**Usage with logging callback**:

```python
def log_handler(level, message):
    level_name = duvc.to_string(level)
    print(f"[{level_name}] {message}")

duvc.set_log_callback(log_handler)
duvc.set_log_level(duvc.LogLevel.Debug)

# Manual logging
duvc.log_debug("Debug message")
duvc.log_info("Info message")
duvc.log_warning("Warning message")
duvc.log_error("Error message")
duvc.log_critical("Critical message")
```


***

### 6.3 String Conversion Functions

#### to_string() - Convert enums to human-readable strings

Converts any duvc-ctl enum to its string representation. Used for logging, display, and debugging.

**Function signatures**:

```python
# Convert CamProp to string
name = duvc.to_string(duvc.CamProp.Pan)  # Returns "Pan"
name = duvc.to_string(duvc.CamProp.Focus)  # Returns "Focus"

# Convert VidProp to string
name = duvc.to_string(duvc.VidProp.Brightness)  # Returns "Brightness"
name = duvc.to_string(duvc.VidProp.Contrast)  # Returns "Contrast"

# Convert CamMode to string
mode_str = duvc.to_string(duvc.CamMode.Auto)  # Returns "Auto"
mode_str = duvc.to_string(duvc.CamMode.Manual)  # Returns "Manual"

# Convert ErrorCode to string
code_str = duvc.to_string(duvc.ErrorCode.DeviceNotFound)  # Returns "DeviceNotFound"
code_str = duvc.to_string(duvc.ErrorCode.PermissionDenied)  # Returns "PermissionDenied"

# Convert LogLevel to string
level_str = duvc.to_string(duvc.LogLevel.Warning)  # Returns "Warning"
level_str = duvc.to_string(duvc.LogLevel.Critical)  # Returns "Critical"
```

**Common patterns**:

```python
# Display supported properties
caps_result = duvc.get_device_capabilities(0)
if caps_result.is_ok():
    caps = caps_result.value()
    
    print("Camera properties:")
    for prop in caps.supported_camera_properties():
        print(f"  - {duvc.to_string(prop)}")
    
    print("Video properties:")
    for prop in caps.supported_video_properties():
        print(f"  - {duvc.to_string(prop)}")

# Log property operations
result = camera.set(duvc.VidProp.Brightness, setting)
if result.is_ok():
    print(f"Set {duvc.to_string(duvc.VidProp.Brightness)} successfully")
else:
    print(f"Failed to set {duvc.to_string(duvc.VidProp.Brightness)}: {result.error().description()}")

# List all properties with modes
for prop in caps.supported_video_properties():
    cap = caps.get_video_capability(prop).value()
    auto_support = "auto" if cap.supports_auto() else "manual only"
    print(f"{duvc.to_string(prop)}: {auto_support}")
```

