## 12. Complete Property Reference \& Details


### 12.1 Video Properties Reference

All 10 DirectShow video (image) properties with technical ranges, device-specific behaviors, and range query details. Typically adjust capture appearance without hardware reconfiguration.

**Reference table:**


| Property | Range | Typical Default | Dynamic Query | Device Notes |
| :-- | :-- | :-- | :-- | :-- |
| **Brightness** | 0–255 | 127 | Yes | Most cameras support. Value $0$ = black, $255$ = full white. |
| **Contrast** | 0–127 | 64 | Yes | Scaling factor for luminance. Some cameras fix at 64. |
| **Saturation** | 0–127 | 64 | Yes | Color intensity. Set $0$ for grayscale, $127$ for maximum color. |
| **Gamma** | 40–500 | 220 | Yes | Nonlinear tone curve. Measured in 1/100 increments. Lower = darker midtones. |
| **Hue** | −180 to +180 | 0 | Yes | Color rotation in degrees. Useless on grayscale cameras. |
| **Sharpness** | 0–100 | 50 | Yes | Edge enhancement strength. Low = soft, High = crisp but noisy. |
| **Backlight Compensation** | 0–127 | 0 | Yes | Brightens foreground when backlit. Rarely exceeds 64. |
| **Gain (Master)** | 0–255 | 128 | Yes | Analog amplification. Higher = more noise, but captures low-light detail. |
| **Whitebalance (Color Temp)** | 2700–6500 K | 4000 | Varies | Some cameras only report temperature in auto mode. |
| **Color Effects** | 0–6 | 0 | Manual | `0`=Normal, `1`=Sepia, `2`=Monochrome, `3`=Negative, `4`=Posterize, `5`=Solarize, `6`=Vivid. Not all modes available on all devices. |


***

#### Dynamic range query details

**Query via get_property_range()**:

```python
import duvc_ctl as duvc

device = duvc.devices()[^0]
cam = duvc.Camera(device)

# Get brightness range
result = cam.get_property_range(duvc.VidProp.Brightness)
if result.is_ok():
    range_info = result.value()
    print(f"Min: {range_info.min}, Max: {range_info.max}, Step: {range_info.step}")
    print(f"Default: {range_info.default_val}")
```

Returns `{min: int, max: int, step: int, default: int, default_mode: str}`.

**Device-specific variations:**

Some devices report hardcoded ranges instead of querying hardware:

- USB 1.1 cameras often max brightness at 128 (8-bit value)
- Built-in webcams may not support Hue adjustment

**Query fallback mechanism:**

If device doesn't report range, library uses UVC defaults:

```cpp
static constexpr PropRange DefaultBrightness{0, 255, 1, 127, CamMode::Auto};
static constexpr PropRange DefaultContrast{0, 127, 1, 64, CamMode::Auto};
// ... etc
```


***

#### Device-specific behaviors

**Logitech cameras** may not support all video properties through standard UVC. Use `supports_logitech_properties()` to check, then access via `get_logitech_property()`.

**Built-in laptop cameras** often:

- Lock saturation and gamma to fixed values
- Report incorrect ranges (e.g., claim range but return error on out-of-range set)
- Skip color effects entirely

**Professional USB cameras** (FLIR, industrial):

- Gamma may require absolute calibration (values \$\$ represent specific curves)
- Whitebalance in Kelvin only available in manual mode; auto mode returns current effective temperature

***

#### Querying video properties in bulk

```python
import duvc_ctl as duvc

device = duvc.devices()[^0]
cam = duvc.Camera(device)

supported = cam.get_supported_properties()
video_props = supported.get('video', [])

for prop_name in video_props:
    prop_enum = duvc.VidProp[prop_name]  # String → enum
    result = cam.get_property(prop_enum)
    if result.is_ok():
        value = result.value()
        print(f"{prop_name}: {value.value} (mode: {value.mode})")
```

### 12.2 Camera Properties Reference

All 22 UVC camera control properties. These affect lens and sensor behavior: focus, pan/tilt, exposure, zoom. Typically require longer I/O than video properties and may lock during automatic operation.

**Reference table:**


| Property | Range | Typical Default | Mode Support | Hardware Dependent |
| :-- | :-- | :-- | :-- | :-- |
| **Pan** | ±180° | 0 | Both | PTZ cameras only; non-PTZ ignored |
| **Tilt** | ±90° | 0 | Both | PTZ cameras only |
| **Roll** | ±180° | 0 | Both | Very rare; built-in cameras unsupported |
| **Zoom** | 1–10× or 1–50 | 1 | Both | USB 3.0+ cameras common; USB 2 rare |
| **Exposure (Auto)** | 0–128 | 0 | Auto only | Shutter time in $\log_2$ increments. Negative = faster. |
| **Exposure (Manual)** | −10 to +10 | 0 | Manual only | Set mode to Manual first before changing. |
| **Iris/Aperture** | 0–128 | N/A | Both | Motorized iris only; fixed aperture cameras unsupported |
| **Focus (Auto)** | N/A | Enabled | Auto only | Affects focus distance automatically. |
| **Focus (Manual)** | 0–255 | 128 | Manual only | Distance: 0=Near, 255=Infinity. Set Focus to Manual first. |
| **Focus Relative** | ±10 | 0 | Manual only | Incremental focus adjustment for video. |
| **Privacy** | On/Off (0/1) | Off | Manual | Disables lens physically (mechanical shutter). Not all cameras support. |
| **Backlight Comp** | 0–127 | 0 | Both | Brightens subject against bright background. |
| **Brightness Comp** | −50 to +50 | 0 | Both | Brightness delta applied over video brightness. |
| **Power Line Freq** | 50/60 Hz | 60 | Manual | Flicker elimination. Match your AC mains (US=60, EU=50). |
| **Scene Mode** | 0–8 | 0 | Manual | Scene presets: Auto(0), Portrait(1), Landscape(2), etc. Device-specific. |
| **Scanning Mode** | 0–1 | 0 | Manual | Interlaced(0) or Progressive(1). Modern cameras use Progressive. |
| **Contrast Enhancement** | 0–127 | 0 | Manual | Adaptive contrast. Higher = more aggressive. |
| **Saturation Boost** | 0–127 | 0 | Manual | Post-processing color intensification. |
| **Sharpening** | 0–100 | 50 | Manual | Edge enhancement; tradeoff with noise. |
| **Zoom Relative** | ±10 | 0 | Manual | Incremental zoom (video mode, not absolute setting). |
| **Digital Multiplier** | 1–4× | 1 | Manual | Post-sensor digital magnification. Reduces effective resolution. |
| **White Balance Comp** | −127 to +127 | 0 | Manual | Temporary offset to white balance temperature. |

These ranges are just fallbacks and are not definitive, ranges vary device to device

***

#### Relative vs absolute guide

**Absolute properties** set exact values (Pan, Tilt, Zoom, Focus):

```python
cam.pan = 45  # Set pan to exactly 45 degrees
cam.zoom = 2  # Set zoom to exactly 2x (if supported)
```

**Relative properties** apply incremental changes (Pan Relative, Tilt Relative, Zoom Relative, Focus Relative):

```python
cam.pan_relative(15)  # Move 15 degrees from current position
cam.zoom_relative(-1)  # Zoom out incrementally
cam.focus_relative(5)  # Move focus closer
```

Relative operations are useful for **real-time adjustments during video capture** without querying current state.

***

#### Device-specific configuration notes

**Auto-focus behavior:**

On cameras with motorized autofocus, set `Focus` to Auto mode:

```python
cam.focus_mode = "auto"  # Or CamMode.Auto
```

Then leave Focus value unchanged. Do not set Focus value manually while in Auto mode; instead use relative adjustments or switch to Manual mode.

**Pan/Tilt on PTZ cameras:**

Professional PTZ (Pan-Tilt-Zoom) cameras support full 3-axis movement. Consumer USB cameras typically do not support Pan/Tilt (values are accepted but ignored by hardware).

Check capability before use:

```python
caps = cam.get_capabilities()
if "Pan" in caps.supported_camera_properties:
    cam.pan = 30
else:
    print("Camera does not support Pan")
```

**Zoom on USB 3.0+ cameras:**

USB 3 cameras common support hardware zoom (1–10×). USB 2 cameras typically support digital zoom only (Digital Multiplier, 1–4×). Query range to distinguish:

```python
zoom_range = cam.get_property_range(CamProp.Zoom)
if zoom_range.max > 4:
    print(f"Hardware zoom: {zoom_range.max}x")
else:
    print(f"Digital zoom: {zoom_range.max}x")
```

**Iris/Aperture (motorized):**

Only professional cameras with motorized iris. Most USB cameras have fixed aperture. Setting fails silently on unsupported hardware; query range first:

```python
iris_range = cam.get_property_range(CamProp.Iris)
if iris_range.max > 0:
    cam.iris = iris_range.max  # Open iris wide
```

**Exposure modes and temperature:**

Auto exposure adjusts shutter time automatically in low light. Manual exposure fixes shutter for consistent brightness. Switching modes:

```python
# Auto exposure
cam.exposure_mode = "auto"

# Manual exposure (set specific shutter)
cam.exposure_mode = "manual"
cam.exposure = -5  # Faster shutter (brighter in dark, less motion blur)
```

Negative exposure values = **faster shutter** (darker in daylight, clearer motion).

***

#### Device-specific workarounds

**Issue: Focus locks after setting manual value**

Some cameras lock focus after manual setting and ignore relative adjustments. **Workaround**: Switch to Auto mode, wait 2 seconds, then set manual value if needed:

```python
cam.focus_mode = "auto"
time.sleep(2)
cam.focus_mode = "manual"
cam.focus = 100
```

**Issue: Pan/Tilt not moving despite no error**

Non-PTZ cameras silently ignore Pan/Tilt commands. **Workaround**: Check device name or query property range (returns `[^0][^0]` if unsupported):

```python
range_result = cam.get_property_range(CamProp.Pan)
if range_result.value().max == 0:
    print("Camera does not support Pan (not a PTZ model)")
```

**Issue: Zoom changes resolution unexpectedly**

Some cameras apply digital zoom, reducing output resolution. **Workaround**: Use `Digital Multiplier` for magnification without resolution loss (if supported), or apply software zoom post-capture.

**Issue: Autofocus too slow or hunts constantly**

Hardware autofocus may oscillate or take seconds to settle. **Workaround**: Use manual focus for fixed subjects:

```python
cam.focus_mode = "manual"
cam.focus = 200  # Far field (landscape)
```

Or apply focus lock (if camera supports):

```python
# Set autofocus, wait for convergence, switch to manual
cam.focus_mode = "auto"
time.sleep(3)
current_focus = cam.focus
cam.focus_mode = "manual"
cam.focus = current_focus  # Lock at current position
```

**Issue: Exposure flickers in low light**

Auto exposure may hunt when ambient light is marginal. **Workaround**: Lock to manual mode with fixed value:

```python
cam.exposure_mode = "manual"
cam.exposure = -3  # Slow shutter (gather more light)
```

Or disable power line frequency cancellation if causing 50/60 Hz flicker:

```python
cam.power_line_frequency = 0  # Disabled (not always supported)
```

### 12.3 Auto vs Manual Modes

Camera properties support automatic and manual operation modes via `CamMode` enum. **Auto mode** delegates control to hardware algorithms; **manual mode** locks to specified values. Some properties only support one mode.

***

#### CamMode enum

```python
import duvc_ctl as duvc

duvc.CamMode.Auto      # Hardware automatic control
duvc.CamMode.Manual    # User-locked value
```


***

#### Property-specific mode support

| Property | Auto | Manual | Notes |
| :-- | :-- | :-- | :-- |
| Exposure | ✓ | ✓ | Auto adjusts shutter; Manual locks. |
| Focus | ✓ | ✓ | Auto seeks; Manual is fixed distance. |
| Iris/Aperture | ✓ | ✓ | Auto for varying light; Manual for fixed depth. |
| Whitebalance | ✓ | ✓ | Auto calibrates; Manual sets Kelvin. |
| Brightness (Video) | ✓ | ✓ | Both modes typically available. |
| Pan/Tilt | ✓ | ✓ | Auto returns to center; Manual stays put. |
| Zoom | ✓ | ✓ | Auto optical tracking; Manual user control. |
| Privacy | Manual only | — | Hardware toggle; no auto mode. |
| Gain | ✓ | ✓ | Auto normalizes; Manual fixes amplification. |


***

#### Mode persistence

**Mode setting persists until changed explicitly.** Setting a property value does not reset mode:

```python
import duvc_ctl as duvc

cam = duvc.CameraController(0)

# Focus in auto mode
cam.focus_mode = "auto"

# Set value (mode remains auto; value ignored)
cam.focus = 100

# Switch to manual—previous value retained
cam.focus_mode = "manual"
print(cam.focus)  # Returns 100 (retained)
```


***

#### Mode string parsing

User-friendly string input supports multiple aliases:


| Input String | Equivalent Enum | Variations |
| :-- | :-- | :-- |
| `"manual"` | `CamMode.Manual` | `"m"` |
| `"auto"` | `CamMode.Auto` | `"a"`, `"automatic"` |

**Parsing implementation** (case-insensitive):

```python
cam.focus_mode = "auto"        # Valid
cam.exposure_mode = "Manual"   # Case-insensitive
cam.iris_mode = "a"            # Short form
cam.pan_mode = "automatic"     # Alternative spelling
```

Invalid strings raise `ValueError`:

```python
cam.zoom_mode = "invalid"  # ValueError: Invalid mode 'invalid' for zoom...
```


***

#### Mode string implementation details

Parser implemented in `CameraController.parse_mode_string()`:

```python
def parse_mode_string(self, mode: str, property_name: str) -> CamMode:
    """Convert mode string to CamMode enum."""
    mode_lower = mode.lower().strip()
    mode_mapping = {
        "manual": CamMode.Manual,
        "auto": CamMode.Auto,
        "automatic": CamMode.Auto,
        "m": CamMode.Manual,
        "a": CamMode.Auto,
    }
    if mode_lower not in mode_mapping:
        available = list(mode_mapping.keys())
        raise ValueError(
            f"Invalid mode '{mode}' for {property_name}. "
            f"Available modes: {', '.join(available)}"
        )
    return mode_mapping[mode_lower]
```


***

### 12.4 Range Discovery \& Clamping

Property constraints vary by device. Query valid ranges before setting values. Library provides automatic validation and fallback defaults.

***

#### get_property_range() returns dict

Returns dictionary with constraint metadata:

```python
import duvc_ctl as duvc

cam = duvc.CameraController(0)

brightness_range = cam.get_property_range("brightness")
print(brightness_range)
# {'min': 0, 'max': 255, 'step': 1, 'default': 127}
```

**Returns None if property unsupported:**

```python
unsupported = cam.get_property_range("pan")  # PTZ-only camera
if unsupported is None:
    print("Pan not supported on this device")
```


***

#### PropRange.clamp()

Clamp value to valid range with optional stepping:

```python
import duvc_ctl as duvc

cam = duvc.CameraController(0)
range_info = cam.get_property_range("zoom")

clamped = range_info["max"]  # Clamp to max
if clamped > range_info["max"]:
    clamped = range_info["max"]
if clamped < range_info["min"]:
    clamped = range_info["min"]

cam.zoom = clamped
```

**Automatic clamping** in setter:

```python
cam.zoom = 999  # Out of range
# Library clamps to max and applies successfully
```


***

#### PropRange.__contains__

Check if value in valid range:

```python
range_info = cam.get_property_range("brightness")

if 128 in range_info:  # min <= 128 <= max
    cam.brightness = 128
else:
    print("Value out of range")
```


***

#### Automatic range validation

Setters validate against device constraints before applying:

```python
import duvc_ctl as duvc

cam = duvc.CameraController(0)

# Out-of-range raises InvalidValueError
try:
    cam.brightness = 999  # Device max is 255
except duvc.InvalidValueError as e:
    print(f"Error: {e}")  # brightness must be <= 255, got 999
```

**Automatic validation applies bounds-checking:**

```python
zoom_range = cam.get_property_range("zoom")
if zoom_range:
    value = max(zoom_range["min"], min(value, zoom_range["max"]))
    # Value is now safe to apply
```


***

#### Default value recovery

Retrieve hardware default from range:

```python
expo_range = cam.get_property_range("exposure")

if expo_range:
    default = expo_range.get("default", 0)
    print(f"Hardware default: {default}")
    
    # Reset to hardware default
    cam.exposure = default
else:
    print("Exposure range unavailable")
```


***

#### Device-specific variations

**Different devices report different ranges:**

```python
# USB 2 camera
brightness_range_usb2 = {"min": 0, "max": 128, "step": 1, "default": 64}

# USB 3 camera
brightness_range_usb3 = {"min": 0, "max": 255, "step": 1, "default": 128}

# Check actual device range
actual = cam.get_property_range("brightness")
print(f"This camera: min={actual['min']}, max={actual['max']}")
```

Some devices report hardcoded ranges instead of querying hardware. Always use returned range, not UVC spec values.

***

#### Fallback mechanism documentation

When device doesn't report range, library uses safe defaults:

```python
def get_dynamic_range(self, property_name, fallback_min, fallback_max):
    """Get device range with fallback."""
    try:
        prop_range = self.get_property_range(property_name)
        if prop_range:
            return prop_range["min"], prop_range["max"]
    except Exception:
        pass
    # Fallback to safe defaults
    return fallback_min, fallback_max

# Usage
min_val, max_val = self.get_dynamic_range("brightness", 0, 100)
# Returns actual device range if available, else (0, 100)
```

**Fallback used by property setters** to prevent out-of-range errors on devices without range reporting. Application can override by explicitly querying and clamping.

