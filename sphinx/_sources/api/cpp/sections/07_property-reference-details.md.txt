## 7. Property Reference \& Details


### 7.1 Camera Properties Complete Reference

**Header:** `<duvc-ctl/core/types.h>`
**Enum:** `CamProp`
**DirectShow Interface:** `IAMCameraControl`

All 23 camera property values with descriptions and behaviors. Actual ranges are **device-specific** and must be queried via `camera.get_range(prop)` or `DeviceCapabilities`.

***

#### Absolute Position Properties (9)

**CamProp::Pan**
Horizontal camera rotation (left/right). Mechanically moves camera head or adjusts digital framing.

- **Unit:** Degrees (typically ±180° for PTZ cameras, varies by hardware)
- **Typical range:** -180 to +180, step 1
- **Auto mode:** Available on PTZ cameras with auto-tracking
- **Hardware:** PTZ cameras, webcams with motorized pan

**CamProp::Tilt**
Vertical camera rotation (up/down). Mechanically moves camera head or adjusts digital framing.

- **Unit:** Degrees (typically ±90° for PTZ cameras)
- **Typical range:** -90 to +90, step 1
- **Auto mode:** Available on PTZ cameras with auto-tracking
- **Hardware:** PTZ cameras, webcams with motorized tilt

**CamProp::Roll**
Rotational tilt around optical axis. Rarely supported by consumer hardware.

- **Unit:** Degrees (-180 to +180)
- **Typical range:** -180 to +180, step 1
- **Auto mode:** Usually manual only
- **Hardware:** Professional PTZ cameras, some action cameras

**CamProp::Zoom**
Optical zoom level. Controls lens focal length, not digital zoom.

- **Unit:** Arbitrary zoom steps (device-specific scale)
- **Typical range:** 10 to 100 (1x to 10x zoom), step 1
- **Auto mode:** Rarely available
- **Hardware:** Cameras with optical zoom lens

**CamProp::Exposure**
Exposure time (shutter speed). Controls sensor light integration time.

- **Unit:** Log₂ seconds (e.g., -10 = 1/1024s, -1 = 1/2s, 0 = 1s)
- **Typical range:** -13 to -1 (1/8192s to 1/2s), step 1
- **Auto mode:** Standard (firmware adjusts for scene brightness)
- **Effect:** Lower values = darker/sharper motion, higher = brighter/motion blur

**CamProp::Iris**
Aperture/iris opening. Controls lens f-stop and depth of field. **Rare on webcams** (fixed aperture).

- **Unit:** f-stop * 10 (e.g., 28 = f/2.8, 56 = f/5.6)
- **Typical range:** 10 to 200 (f/1.0 to f/20), step 1
- **Auto mode:** Usually manual only
- **Hardware:** Professional cameras with adjustable aperture

**CamProp::Focus**
Lens focus distance. Adjusts focus from close-up to infinity.

- **Unit:** Arbitrary focus steps (device-specific scale)
- **Typical range:** 0 to 255 (close to infinity), step 1
- **Auto mode:** Standard (continuous autofocus)
- **Hardware:** Cameras with adjustable focus (most webcams)

**CamProp::ScanMode**
Scan mode selection: progressive (0) vs. interlaced (1). **Obsolete for modern cameras.**

- **Unit:** Boolean (0 = progressive, 1 = interlaced)
- **Typical range:** 0 to 1, step 1
- **Auto mode:** Manual only
- **Hardware:** Legacy analog cameras, capture cards

**CamProp::Privacy**
Privacy shutter/lens cover. Mechanically blocks lens or disables sensor.

- **Unit:** Boolean (0 = open, 1 = closed)
- **Typical range:** 0 to 1, step 1
- **Auto mode:** Manual only
- **Hardware:** Business webcams (Logitech, Microsoft), laptops with privacy shutters

***

#### Relative Movement Properties (8)

These properties specify **delta values** for relative adjustments. Not all cameras support relative mode.

**CamProp::PanRelative**
Relative pan movement. Moves camera left (-) or right (+) by specified angle.

**CamProp::TiltRelative**
Relative tilt movement. Moves camera up (+) or down (-) by specified angle.

**CamProp::RollRelative**
Relative roll adjustment. Rotates camera clockwise (+) or counterclockwise (-).

**CamProp::ZoomRelative**
Relative zoom adjustment. Zooms in (+) or out (-) by specified steps.

**CamProp::ExposureRelative**
Relative exposure adjustment. Increases (+) or decreases (-) exposure time.

**CamProp::IrisRelative**
Relative iris adjustment. Opens (+) or closes (-) aperture.

**CamProp::FocusRelative**
Relative focus adjustment. Moves focus closer (+) or farther (-).

***

#### Combined Control Properties (2)

**CamProp::PanTilt**
Combined pan/tilt control. Sets both pan and tilt in single operation. **Rarely supported.**

- **Unit:** Composite value (implementation-defined)
- **Hardware:** High-end PTZ cameras with optimized movement

**CamProp::PanTiltRelative**
Relative pan/tilt movement. Adjusts both axes simultaneously.

***

#### Simple Controls (1)

**CamProp::FocusSimple**
Simplified focus control: near (0), far (1), auto (2). **Logitech extension**, not standard DirectShow.

- **Unit:** Enum (0 = near, 1 = far, 2 = auto)
- **Typical range:** 0 to 2, step 1
- **Hardware:** Logitech webcams (C920, C930e, Brio)

***

#### Digital/Processing Properties (3)

**CamProp::DigitalZoom**
Digital zoom level. Software image cropping/upscaling, not optical zoom.

- **Unit:** Zoom multiplier * 100 (e.g., 100 = 1.0x, 200 = 2.0x)
- **Typical range:** 100 to 400 (1x to 4x), step 10
- **Auto mode:** Manual only
- **Quality:** Lower than optical zoom (interpolation artifacts)

**CamProp::DigitalZoomRelative**
Relative digital zoom adjustment. Increases (+) or decreases (-) digital zoom.

**CamProp::BacklightCompensation**
Backlight compensation level. Adjusts exposure for strong backlighting (e.g., window behind subject).

- **Unit:** Compensation level (0 = off, 1+ = increasing compensation)
- **Typical range:** 0 to 10, step 1
- **Auto mode:** Rarely available
- **Effect:** Brightens foreground when background is overexposed

***

#### Lamp/Flash (1)

**CamProp::Lamp**
Camera lamp/flash control. Enables auxiliary lighting (LED ring, flash).

- **Unit:** Boolean (0 = off, 1 = on)
- **Typical range:** 0 to 1, step 1
- **Auto mode:** Manual only
- **Hardware:** Document cameras, industrial cameras with built-in lighting

***

### Property Range Querying

```cpp
auto range_result = camera.get_range(CamProp::Exposure);
if (range_result.is_ok()) {
    auto range = range_result.value();
    // range.min, range.max, range.step, range.default_val, range.default_mode
}
```

**Hardware variance:** Ranges are **not standardized**. A Logitech C920 may report exposure range -13 to -1, while a generic webcam reports -7 to 0. Always query device-specific ranges.

**Unsupported properties:** `get_range()` returns `Err(ErrorCode::NotSupported)` for properties not implemented by hardware/driver.

### 7.2 Video Properties Complete Reference

**Header:** `<duvc-ctl/core/types.h>`
**Enum:** `VidProp`
**DirectShow Interface:** `IAMVideoProcAmp`

All 10 video processing properties with descriptions and behaviors. These control **digital image processing**, not camera hardware. Actual ranges are **device-specific** and must be queried via `camera.get_range(prop)` or `DeviceCapabilities`.

***

#### VidProp::Brightness

Luminance level. Adds/subtracts constant value to all pixels (black point adjustment).

- **Unit:** Arbitrary brightness steps (device-specific scale)
- **Typical range:** -64 to +64, step 1 (or 0 to 255 for some cameras)
- **Default:** 0 (neutral)
- **Auto mode:** Rarely available (auto-exposure handles this)
- **Effect:** Negative = darker image, positive = brighter image
- **Technical:** Linear offset applied in YUV/RGB space before gamma correction

**Usage note:** For exposure control, prefer `CamProp::Exposure`. Brightness is post-processing and can clip highlights/shadows.

***

#### VidProp::Contrast

Dynamic range. Scales pixel values around midpoint (white point adjustment).

- **Unit:** Arbitrary contrast steps (device-specific scale)
- **Typical range:** 0 to 100, step 1 (some cameras use -50 to +50)
- **Default:** 50 or 0 (neutral, device-dependent)
- **Auto mode:** Manual only
- **Effect:** Lower = flatter/washed out, higher = stronger blacks/whites
- **Technical:** Multiplies pixel values by scaling factor around 128 (8-bit) or equivalent

**Usage note:** Values above 80-90 can cause clipping. Combine with brightness adjustment for best results.

***

#### VidProp::Hue

Color tint. Rotates hue angle in HSV/HSL color space.

- **Unit:** Degrees or arbitrary hue steps
- **Typical range:** -180 to +180 degrees, step 1 (or 0 to 360)
- **Default:** 0 (no shift)
- **Auto mode:** Manual only
- **Effect:** -180° = cyan/green shift, 0 = natural, +180° = magenta/red shift
- **Technical:** Rotates H component in HSV space, preserves S and V

**Usage note:** For color correction, prefer `VidProp::WhiteBalance`. Hue is global shift, not adaptive.

***

#### VidProp::Saturation

Color intensity. Scales chroma values in color space.

- **Unit:** Arbitrary saturation steps (device-specific scale)
- **Typical range:** 0 to 200, step 1 (0 = grayscale, 100 = normal, 200 = oversaturated)
- **Default:** 100 (neutral)
- **Auto mode:** Manual only
- **Effect:** 0 = black \& white, 100 = natural colors, 200 = vivid/oversaturated
- **Technical:** Scales S component in HSV space, preserves H and V

**Usage note:** Values above 150 can cause color clipping and unnatural tones.

***

#### VidProp::Sharpness

Edge enhancement. Applies high-pass filter to increase perceived detail.

- **Unit:** Arbitrary sharpness steps (device-specific scale)
- **Typical range:** 0 to 100, step 1 (or 0 to 255)
- **Default:** 50 (moderate sharpening)
- **Auto mode:** Manual only
- **Effect:** 0 = soft/blurry, 50 = natural, 100 = over-sharpened with halos
- **Technical:** Unsharp mask or Laplacian edge enhancement filter

**Usage note:** High values (>75) introduce ringing artifacts and noise amplification. Use conservatively.

***

#### VidProp::Gamma

Mid-tone brightness curve. Adjusts gamma correction exponent.

- **Unit:** Gamma exponent * 100 (e.g., 100 = γ=1.0, 220 = γ=2.2)
- **Typical range:** 1 to 500 (γ=0.01 to γ=5.0), step 1
- **Default:** 100 or 220 (γ=1.0 or γ=2.2, device-dependent)
- **Auto mode:** Manual only
- **Effect:** <100 = brighter midtones (flatter curve), >100 = darker midtones (steeper curve)
- **Technical:** Applies power-law transformation: \$ V_{out} = V_{in}^{\gamma} \$

**Usage note:** Standard sRGB gamma is 2.2 (220). Do not change unless matching specific display/workflow.

***

#### VidProp::ColorEnable

Color mode toggle. Switches between color and monochrome output.

- **Unit:** Boolean (0 = monochrome, 1 = color)
- **Typical range:** 0 to 1, step 1
- **Default:** 1 (color)
- **Auto mode:** Manual only
- **Effect:** 0 = grayscale output, 1 = full color
- **Technical:** Zeroes chroma channels (U/V in YUV) when disabled

**Usage note:** Equivalent to setting `VidProp::Saturation = 0`, but may be hardware-accelerated.

***

#### VidProp::WhiteBalance

Color temperature adjustment. Shifts white point to compensate for lighting.

- **Unit:** Kelvin (K) or arbitrary color temperature steps
- **Typical range:** 2800 to 6500 K, step 10 (or arbitrary 0-255 scale)
- **Default:** 4000-5000 K (neutral/daylight)
- **Auto mode:** **Standard** (auto white balance, AWB)
- **Effect:** Lower = warmer (yellow/orange), higher = cooler (blue)
- **Technical:** Applies RGB channel gains to neutralize color cast

**Common presets:**

- 2800 K = incandescent/tungsten (warm orange)
- 4000 K = fluorescent (cool white)
- 5500 K = daylight (neutral)
- 6500 K = overcast/shade (cool blue)

**Usage note:** Auto mode is highly recommended. Manual tuning requires color reference card.

***

#### VidProp::BacklightCompensation

Backlight compensation level. Adjusts exposure for strong backlighting.

- **Unit:** Compensation level (0 = off, 1-10 = increasing compensation)
- **Typical range:** 0 to 10, step 1 (some cameras use 0/1 boolean)
- **Default:** 0 (off)
- **Auto mode:** Rarely available
- **Effect:** Brightens foreground when background is overexposed (e.g., window behind subject)
- **Technical:** Adjusts metering zones to prioritize foreground exposure

**Overlap:** Some cameras expose this via `CamProp::BacklightCompensation` instead. Check both.

**Usage note:** Alternative to adjusting `CamProp::Exposure` manually. Less effective than HDR tone mapping.

***

#### VidProp::Gain

Sensor gain level. Digital/analog amplification of sensor signal (ISO equivalent).

- **Unit:** Gain multiplier or dB (device-specific scale)
- **Typical range:** 0 to 100 (or 0 to 255), step 1
- **Default:** 0 or auto (device-dependent)
- **Auto mode:** **Standard** (auto-gain control, AGC)
- **Effect:** Higher gain = brighter image in low light, but more noise
- **Technical:** Amplifies sensor readout before digitization (analog gain) or after (digital gain)

**Relationship to exposure:**

- Low light: increase gain OR increase exposure time
- Gain is faster (no motion blur) but noisier
- Exposure time is cleaner but causes motion blur

**Usage note:** Auto mode is recommended. Manual tuning requires controlled lighting. High gain (>50) introduces significant noise.

***

### Property Range Querying

```cpp
auto range_result = camera.get_range(VidProp::Brightness);
if (range_result.is_ok()) {
    auto range = range_result.value();
    // range.min, range.max, range.step, range.default_val, range.default_mode
}
```

**Hardware variance:** Ranges are **not standardized**. A Logitech C920 may report brightness range -64 to +64, while a generic webcam reports 0 to 255. Always query device-specific ranges.

**Unsupported properties:** `get_range()` returns `Err(ErrorCode::NotSupported)` for properties not implemented by hardware/driver.

***

### Auto Mode Support

**Commonly auto-capable:**

- `VidProp::WhiteBalance` — auto white balance (AWB) is standard on most cameras
- `VidProp::Gain` — auto gain control (AGC) is standard

**Rarely auto-capable:**

- `VidProp::Brightness`, `VidProp::Contrast`, `VidProp::Hue`, `VidProp::Saturation`, `VidProp::Sharpness`, `VidProp::Gamma` — these are post-processing adjustments, not firmware-controlled

Check `PropertyCapability::supports_auto()` or `range.default_mode` to verify auto support for specific device.

### 7.3 Property Range Discovery

**Header:** `<duvc-ctl/core/types.h>`
**Structs:** `PropRange`, `PropSetting`

Query device-specific property ranges before setting values. Ranges are **not standardized** — each camera reports different min/max/step values.

***

#### PropRange Structure

```cpp
struct PropRange {
    int min;                  // Minimum supported value
    int max;                  // Maximum supported value
    int step;                 // Step size between valid values
    int default_val;          // Default value
    CamMode default_mode;     // Default control mode (Auto/Manual)
    
    bool is_valid(int value) const;
    int clamp(int value) const;
};
```

**Fields:**

- `min`: Lowest value camera accepts (e.g., exposure -13, brightness -64)
- `max`: Highest value camera accepts (e.g., exposure -1, brightness +64)
- `step`: Increment between valid values (typically 1, sometimes 10 or 100)
- `default_val`: Factory default value recommended by manufacturer
- `default_mode`: Whether property defaults to `CamMode::Auto` or `CamMode::Manual`

***

#### get_range Usage

**Camera properties:**

```cpp
Camera camera(0);
auto result = camera.get_range(CamProp::Exposure);

if (result.is_ok()) {
    PropRange range = result.value();
    std::cout << "Exposure range: " << range.min << " to " << range.max << "\n";
    std::cout << "Step: " << range.step << ", default: " << range.default_val << "\n";
    std::cout << "Default mode: " << (range.default_mode == CamMode::Auto ? "Auto" : "Manual") << "\n";
} else {
    std::cerr << "Error: " << result.error().message() << "\n";
}
```

**Video properties:**

```cpp
auto result = camera.get_range(VidProp::Brightness);
if (result.is_ok()) {
    PropRange range = result.value();
    // range.min, range.max, range.step, range.default_val, range.default_mode
}
```

**Error handling:**

- `ErrorCode::NotSupported`: Property not implemented by hardware/driver
- `ErrorCode::DeviceNotFound`: Camera disconnected
- `ErrorCode::SystemError`: DirectShow API failure

***

#### is_valid Method

**Signature:**

```cpp
bool PropRange::is_valid(int value) const;
```

Checks if value is within `[min, max]` and aligned to `step` boundary.

**Implementation:**

```cpp
return value >= min && value <= max && ((value - min) % step == 0);
```

**Example usage:**

```cpp
PropRange range = camera.get_range(CamProp::Pan).value();

if (range.is_valid(45)) {
    camera.set(CamProp::Pan, {45, CamMode::Manual});  // Safe to set
} else {
    std::cerr << "Invalid value 45 for pan (range: " 
              << range.min << " to " << range.max << ")\n";
}
```

**Step alignment:**

- If `min=0, max=100, step=10`, valid values are `{0, 10, 20, ..., 100}`
- `is_valid(15)` returns `false` (not aligned to step)
- `is_valid(20)` returns `true`

***

#### clamp Method

**Signature:**

```cpp
int PropRange::clamp(int value) const;
```

Constrains value to valid range and rounds to nearest step boundary.

**Implementation:**

```cpp
if (value <= min) return min;
if (value >= max) return max;
// Round to nearest step
int steps = (value - min + step / 2) / step;
return min + steps * step;
```

**Example usage:**

```cpp
PropRange range = camera.get_range(CamProp::Zoom).value();

int user_input = 123;  // Potentially invalid
int safe_value = range.clamp(user_input);

camera.set(CamProp::Zoom, {safe_value, CamMode::Manual});  // Always valid
```

**Rounding behavior:**

- `clamp(-50)` with `min=0` → returns `0`
- `clamp(200)` with `max=100` → returns `100`
- `clamp(47)` with `min=0, step=10` → returns `50` (rounds 47 to nearest 50)
- `clamp(43)` with `min=0, step=10` → returns `40` (rounds 43 to nearest 40)

**Use case:** UI sliders can pass any integer; `clamp()` ensures value is always accepted by hardware.

***

#### PropSetting Structure

```cpp
struct PropSetting {
    int value;          // Property value
    CamMode mode;       // Control mode (Auto/Manual)
};
```

Used when setting properties via `camera.set()`. Must specify both value and mode.

**Example:**

```cpp
// Manual control with specific value
camera.set(CamProp::Exposure, {-5, CamMode::Manual});

// Auto control (value ignored by firmware, but should match default_val)
PropRange range = camera.get_range(CamProp::WhiteBalance).value();
camera.set(VidProp::WhiteBalance, {range.default_val, CamMode::Auto});
```


***

### 7.4 Auto vs Manual Modes

**Enum:** `CamMode`

```cpp
enum class CamMode {
    Auto,    // Firmware-controlled (camera adjusts automatically)
    Manual   // Application-controlled (fixed value)
};
```


***

#### Mode Behavior

**Auto mode:**

- Firmware continuously adjusts property based on scene (e.g., auto-exposure adapts to lighting)
- `value` field in `PropSetting` is **ignored** by camera — firmware uses its own algorithm
- Reading property via `camera.get()` returns **current firmware-computed value**, not user-set value
- Typical auto properties: `CamProp::Exposure`, `CamProp::Focus`, `VidProp::WhiteBalance`, `VidProp::Gain`

**Manual mode:**

- Firmware uses fixed value provided by application
- `value` field in `PropSetting` is **required** and enforced
- Reading property via `camera.get()` returns last value set by application
- Value persists until changed or camera reset

***

#### Checking Auto Support

**Method 1: Check range.default_mode**

```cpp
PropRange range = camera.get_range(CamProp::Focus).value();

if (range.default_mode == CamMode::Auto) {
    std::cout << "Focus supports auto mode\n";
    camera.set(CamProp::Focus, {range.default_val, CamMode::Auto});
} else {
    std::cout << "Focus is manual-only\n";
    camera.set(CamProp::Focus, {range.default_val, CamMode::Manual});
}
```

**Method 2: PropertyCapability::supports_auto()**

```cpp
DeviceCapabilities caps(device);
if (caps.get_camera_capability(CamProp::Exposure).supports_auto()) {
    std::cout << "Exposure supports auto mode\n";
}
```

**Implementation:**

```cpp
bool PropertyCapability::supports_auto() const {
    return range.default_mode == CamMode::Auto;
}
```


***

#### Switching Modes

**Manual → Auto:**

```cpp
// Enable auto-exposure
PropRange range = camera.get_range(CamProp::Exposure).value();
camera.set(CamProp::Exposure, {range.default_val, CamMode::Auto});
```

**Auto → Manual:**

```cpp
// Get current auto-computed value
PropSetting current = camera.get(CamProp::Exposure).value();

// Lock to current value
camera.set(CamProp::Exposure, {current.value, CamMode::Manual});
```

**Manual value adjustment:**

```cpp
// Read current manual value
PropSetting setting = camera.get(CamProp::Exposure).value();

// Increase by 1 step
PropRange range = camera.get_range(CamProp::Exposure).value();
int new_value = range.clamp(setting.value + range.step);

camera.set(CamProp::Exposure, {new_value, CamMode::Manual});
```


***

#### Mode Limitations

**Property-specific restrictions:**

- **Brightness, Contrast, Hue, Saturation, Sharpness, Gamma:** Usually **manual-only** (post-processing adjustments, not firmware-controlled)
- **Exposure, Focus, WhiteBalance, Gain:** Usually support **both auto and manual**
- **Pan, Tilt, Zoom:** Usually **manual-only** (mechanical positioning)
- **Privacy, ColorEnable, ScanMode:** Always **manual-only** (binary switches)

**Hardware variance:** Some cameras report auto support for properties that don't actually respond to auto mode. Always test on target hardware.

**Attempted auto on manual-only property:** DirectShow may return `E_PROP_ID_UNSUPPORTED` or silently fall back to manual mode. Library returns `Err(ErrorCode::NotSupported)` when auto mode fails.

***

#### Mode Persistence

**Cross-session behavior:**

- Manual values typically persist across application restarts (stored in camera firmware)
- Auto mode typically resets to auto on camera power-cycle or USB reconnect
- Some cameras reset all properties to defaults on disconnect

**Reading current mode:**

```cpp
PropSetting setting = camera.get(CamProp::Exposure).value();

if (setting.mode == CamMode::Auto) {
    std::cout << "Exposure is in auto mode (current value: " << setting.value << ")\n";
} else {
    std::cout << "Exposure is manual (fixed value: " << setting.value << ")\n";
}
```

**Best practice:** Always query current mode before modifying values to avoid unintended mode switches.

