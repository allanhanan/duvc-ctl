## 11. Device Support \& Compatibility


### 11.1 Tested Devices

**duvc-ctl works with any UVC-compliant camera on Windows.**

The library relies on DirectShow's UVC support rather than device-specific drivers, providing broad compatibility.

***

#### Verified Compatible Brands

**Logitech** (Extended support via vendor extensions):

- C920/C922 HD Pro Webcam
- C930e Business Webcam
- BRIO 4K Ultra HD
- StreamCam
- PTZ Pro series

**Microsoft:**

- LifeCam HD-3000
- LifeCam Studio
- Modern Webcam

**Generic UVC:**

- Most USB webcams without proprietary drivers
- Conference room PTZ cameras
- Document cameras
- Industrial machine vision cameras

**Professional:**

- PTZOptics cameras
- AVer CAM series
- Elgato Facecam
- Razer Kiyo series

***

#### Property Support Varies

Not all cameras implement all UVC properties:

**Common capabilities:**

- Brightness, Contrast, Saturation
- Auto/Manual Exposure
- Auto/Manual White Balance
- Auto Focus (if supported by hardware)

**Less common:**

- Pan/Tilt/Zoom (PTZ cameras only)
- Privacy Shutter
- Roll
- Iris control

**Check support:**

```cpp
auto devices = duvc::list_devices();
Camera camera(devices);

// Query which properties are available
std::cout << "Camera: " << duvc::to_utf8(devices.name) << "\n";

for (auto prop : {CamProp::Pan, CamProp::Tilt, CamProp::Zoom, 
                   CamProp::Focus, CamProp::Exposure}) {
    auto range = camera.get_range(prop);
    if (range.is_ok()) {
        std::cout << "  " << to_string(prop) << ": " 
                  << range.value().min << " to " << range.value().max << "\n";
    }
}
```


***

### 11.2 Device Capability Matrix

**Typical property support by camera type:**


| Property | Basic Webcam | PTZ Camera | High-End Webcam | Industrial Camera |
| :-- | :-- | :-- | :-- | :-- |
| **Brightness** | ✓ | ✓ | ✓ | ✓ |
| **Contrast** | ✓ | ✓ | ✓ | ✓ |
| **Saturation** | ✓ | ✓ | ✓ | ✓ |
| **Hue** | ✓ | ✓ | ✓ | ~ |
| **Sharpness** | ✓ | ✓ | ✓ | ✓ |
| **Gamma** | ~ | ✓ | ✓ | ✓ |
| **White Balance** | ✓ | ✓ | ✓ | ✓ |
| **Backlight Comp** | ~ | ✓ | ✓ | ✓ |
| **Gain** | ~ | ✓ | ✓ | ✓ |
| **Exposure** | ✓ | ✓ | ✓ | ✓ |
| **Focus** | Auto only | ✓ | ✓ | ✓ |
| **Zoom** | ✗ | ✓ | ~ | ~ |
| **Pan** | ✗ | ✓ | ✗ | ~ |
| **Tilt** | ✗ | ✓ | ✗ | ~ |
| **Roll** | ✗ | ~ | ✗ | ✗ |
| **Iris** | ✗ | ~ | ✗ | ✓ |
| **Privacy** | ✗ | ~ | ~ | ~ |

**Legend:**

- ✓ = Commonly supported
- ~ = Sometimes supported
- ✗ = Rarely supported

***

#### Logitech-Specific Features

**Vendor extensions via `IKsPropertySet`:**


| Feature | C920 | C922 | C930e | BRIO | StreamCam |
| :-- | :-- | :-- | :-- | :-- | :-- |
| **RightLight** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **RightSound** | ✗ | ✗ | ✓ | ✓ | ✗ |
| **Face Tracking** | ~ | ~ | ✓ | ✓ | ~ |
| **LED Control** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **HDR** | ✗ | ✗ | ✗ | ✓ | ✗ |
| **Digital Pan/Tilt** | ✗ | ✗ | ✗ | ✓ | ~ |

**Usage:**

```cpp
#include <duvc-ctl/vendor/logitech.h>

auto devices = duvc::list_devices();
if (duvc::logitech::supports_logitech_properties(devices).value_or(false)) {
    // Enable RightLight auto-exposure
    duvc::logitech::set_logitech_property_typed<bool>(
        devices, duvc::logitech::LogitechProperty::RightLight, true);
}
```


***

#### Resolution Impact

**Property availability can vary by resolution:**

Some cameras disable certain controls at high resolutions (e.g., 4K) due to bandwidth or processing limits.

**Example:**

- 1080p: Full property support
- 4K: Auto focus only, manual focus disabled
- 720p: All properties available

**This is firmware-dependent** and varies by manufacturer.

***

### 11.3 Known Issues \& Workarounds

#### Issue 1: Property Values Don't Persist

**Problem:**
Some cameras reset properties to defaults when:

- Camera is unplugged/replugged
- System reboots
- Camera app is closed

**Cause:** Properties stored in volatile firmware memory, not flash.

**Workaround:**

```cpp
// Save desired settings
struct CameraSettings {
    int exposure;
    int brightness;
    int white_balance;
};

// Apply on startup
void apply_settings(Camera& camera, const CameraSettings& settings) {
    camera.set(CamProp::Exposure, {settings.exposure, CamMode::Manual});
    camera.set(VidProp::Brightness, {settings.brightness, CamMode::Manual});
    camera.set(VidProp::WhiteBalance, {settings.white_balance, CamMode::Manual});
}

// Call on device connection
duvc::register_device_change_callback([](bool added, const std::string& path) {
    if (added) {
        // Device connected - reapply settings
        auto devices = duvc::list_devices();
        Camera camera(devices);
        apply_settings(camera, saved_settings);
    }
});
```


***

#### Issue 2: Auto Mode Doesn't Revert to Default

**Problem:**
Setting manual value, then switching back to auto may not restore original auto behavior.

**Example:**

```cpp
// Original state: Auto exposure
camera.set(CamProp::Exposure, {-5, CamMode::Manual});  // Set manual
camera.set(CamProp::Exposure, {0, CamMode::Auto});     // Back to auto

// Auto behavior may differ from original
```

**Cause:** Some cameras remember manual value as "auto starting point."

**Workaround:**
Query and store default value before modification:

```cpp
auto original = camera.get(CamProp::Exposure).value();
auto range = camera.get_range(CamProp::Exposure).value();

// Modify
camera.set(CamProp::Exposure, {-5, CamMode::Manual});

// Restore to true default
camera.set(CamProp::Exposure, {range.default_val, range.default_mode});
```


***

#### Issue 3: Property Changes During Streaming

**Problem:**
Some cameras ignore property changes while actively streaming video.

**Symptom:**

```cpp
Camera camera(0);
camera.set(CamProp::Exposure, {-5, CamMode::Manual});  // Returns success

// But value doesn't change if camera is streaming
auto result = camera.get(CamProp::Exposure);  // Still old value
```

**Workaround:**
Stop streaming, apply properties, restart streaming:

```cpp
// OpenCV example
cv::VideoCapture cap(0);
cap.release();  // Stop streaming

Camera camera(0);
camera.set(CamProp::Exposure, {-5, CamMode::Manual});

cap.open(0);  // Restart with new settings
```


***

#### Issue 4: Incorrect Range Values

**Problem:**
Some cameras report invalid `min`, `max`, or `step` values.

**Examples:**

- Step of 0 (continuous values)
- Min > Max (reversed range)
- Range includes impossible values

**Workaround:**
Validate and clamp:

```cpp
auto range_result = camera.get_range(CamProp::Zoom);
if (range_result.is_ok()) {
    auto range = range_result.value();
    
    // Validate
    if (range.min > range.max) {
        std::swap(range.min, range.max);
    }
    if (range.step <= 0) {
        range.step = 1;  // Assume step of 1
    }
    
    // Safe clamping
    int value = range.clamp(user_value);
    camera.set(CamProp::Zoom, {value, CamMode::Manual});
}
```


***

#### Issue 5: Slow Property Queries

**Problem:**
Some cameras take a long time to respond to `get()` or `get_range()` calls.

**Typical duration:** 50-200ms per query

**Workaround:**
Cache property ranges:

```cpp
// Cache on startup
std::map<CamProp, PropRange> cached_ranges;
for (auto prop : {CamProp::Pan, CamProp::Tilt, CamProp::Zoom}) {
    auto range = camera.get_range(prop);
    if (range.is_ok()) {
        cached_ranges[prop] = range.value();
    }
}

// Use cached values for validation
if (cached_ranges[CamProp::Pan].is_valid(value)) {
    camera.set(CamProp::Pan, {value, CamMode::Manual});
}
```


***

#### Issue 6: DirectShow Exclusive Access

**Problem:**
If another application is using DirectShow to control the camera, property changes may fail.

**Error:** `E_FAIL` or `VFW_E_IN_USE`

**Conflicting applications:**

- Windows Camera app
- Skype/Teams (if camera preview active)
- OBS Studio (with DirectShow source)
- Third-party camera control software

**Workaround:**

```cpp
auto result = camera.set(CamProp::Exposure, {-5, CamMode::Manual});
if (result.is_error()) {
    if (result.error().code() == ErrorCode::DeviceInUse) {
        std::cerr << "Camera in use by another application\n";
        // Prompt user to close other apps
    }
}
```


***

#### Issue 7: USB Power Management

**Problem:**
Windows USB selective suspend can reset camera properties.

**Symptom:** Properties revert to defaults after period of inactivity.

**Workaround:**
Disable USB selective suspend for camera devices:

**PowerShell:**

```powershell
# Disable for all USB devices
powercfg /change usb-selective-suspend-setting 0

# Or via Device Manager → USB Hub → Power Management → 
# Uncheck "Allow computer to turn off this device"
```

**Programmatic detection:**

```cpp
duvc::register_device_change_callback([](bool added, const std::string& path) {
    if (added) {
        // Device reconnected (possibly due to power management)
        // Reapply settings
    }
});
```


***

#### Issue 8: Firmware Bugs

**Problem:**
Some cameras have firmware bugs causing:

- Invalid property values
- Crashes when setting certain combinations
- Properties affecting unrelated settings

**Example:** Setting Zoom on some cameras resets Exposure.

**Workaround:**
Test and document camera-specific quirks:

```cpp
// Logitech C920 quirk: Setting zoom resets exposure
auto exposure = camera.get(CamProp::Exposure).value();
camera.set(CamProp::Zoom, {100, CamMode::Manual});
camera.set(CamProp::Exposure, exposure);  // Restore exposure
```


***

#### Issue 9: Multiple Cameras Same Model

**Problem:**
Cameras of same model have identical names, making identification difficult.

**Solution:**
Use device path for unique identification:

```cpp
auto devices = duvc::list_devices();
for (const auto& device : devices) {
    std::wcout << L"Name: " << device.name << L"\n";
    std::wcout << L"Path: " << device.path << L"\n\n";
    
    // Path contains unique USB bus/port info
}

// Store path to identify specific camera
std::wstring my_camera_path = devices.path;

// Later, find same camera
for (const auto& device : duvc::list_devices()) {
    if (device.path == my_camera_path) {
        Camera camera(device);
        // This is the correct camera
    }
}
```


***

#### Issue 10: No UVC Compliance

**Problem:**
Some "webcams" don't implement UVC properly and require proprietary drivers.

**Examples:**

- Very old webcams (pre-2008)
- Some security cameras
- Proprietary industrial cameras

**Detection:**

```cpp
auto devices = duvc::list_devices();
if (devices.empty()) {
    std::cerr << "No UVC cameras found\n";
    std::cerr << "Camera may require vendor drivers\n";
}

// Or camera appears but has no properties
Camera camera(0);
auto range = camera.get_range(CamProp::Brightness);
if (range.is_error()) {
    std::cerr << "Camera doesn't support standard UVC properties\n";
}
```

**Solution:** Use vendor SDK if available, or duvc-ctl won't work.

***

#### Testing New Devices

**Capability discovery script:**

```cpp
void test_camera_capabilities(const Device& device) {
    std::cout << "Testing: " << duvc::to_utf8(device.name) << "\n\n";
    
    Camera camera(device);
    
    // Test camera properties
    std::cout << "Camera Properties:\n";
    for (auto prop : {CamProp::Pan, CamProp::Tilt, CamProp::Zoom,
                       CamProp::Exposure, CamProp::Focus, CamProp::Iris}) {
        auto range = camera.get_range(prop);
        if (range.is_ok()) {
            std::cout << "  " << to_string(prop) << ": "
                      << range.value().min << " to " << range.value().max
                      << " (default: " << range.value().default_val << ")\n";
        }
    }
    
    // Test video properties
    std::cout << "\nVideo Properties:\n";
    for (auto prop : {VidProp::Brightness, VidProp::Contrast,
                       VidProp::Saturation, VidProp::WhiteBalance}) {
        auto range = camera.get_range(prop);
        if (range.is_ok()) {
            std::cout << "  " << to_string(prop) << ": "
                      << range.value().min << " to " << range.value().max << "\n";
        }
    }
}
```

