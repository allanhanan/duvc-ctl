# Quick Start

Get duvc-ctl running quick across C ABI, C++, CLI, and Python. This guide covers installation, basic usage, and common patterns for each interface.

---

## Prerequisites

- **Windows** 7 SP1+ (tested on 10/11)
- **USB camera** UVC-compliant webcam or PTZ camera
- **Compiler** (C/C++): Visual Studio 2019+ or MinGW-w64 GCC 9+
- **Python** (optional): 3.8–3.12 (64-bit recommended)
- **CMake**: 3.16+ (for building from source)

---

## Installation

### Python (PyPI)

```

pip install duvc-ctl
python -c "import duvcctl; print(duvcctl.__version__)"

```

### C/C++ (Build from source)

```

git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl
cmake -B build -G "Visual Studio 17 2022" -A x64 -DDUVC_BUILD_SHARED=ON
cmake --build build --config Release
cmake --install build --config Release

```

### CLI Tool

Built automatically with `-DDUVC_BUILD_CLI=ON` (default):

```

build/bin/duvc-cli.exe list

```

---

## First Connection

### List Devices

**Python:**

```

import duvcctl as duvc
devices = duvc.list_devices()
print(f"Found {len(devices)} camera(s)")
for dev in devices:
print(f"  - {dev.name}")

```

**C++:**

```

\#include <duvc-ctl/duvc.hpp>
\#include <iostream>

int main() {
auto devices = duvc::list_devices();
std::cout << "Found " << devices.size() << " camera(s)\n";
for (const auto\& dev : devices)
std::cout << "  - " << duvc::to_utf8(dev.name) << "\n";
}

```

**C ABI:**

```

\#include <duvc-ctl/capi.h>
\#include <stdio.h>

int main() {
duvc_initialize();
duvc_device_t* devices;
size_t count;
duvc_list_devices(\&devices, \&count);
printf("Found %zu camera(s)\n", count);
duvc_free_device_list(devices, count);
duvc_shutdown();
}

```

**CLI:**

```

duvc-cli list

# Output:

# Devices: 2

# 0: Logitech HD Pro Webcam C920

# \\?\usb\#vid_046d\&pid_082d\#...

```

---

## Basic Property Control

### Read Brightness

**Python (Result-based API):**

```

import duvcctl as duvc

devices = duvc.list_devices()
camera = duvc.Camera(devices)
result = camera.get_property(duvc.VidProp.Brightness)

if result.is_ok():
setting = result.value
print(f"Brightness: {setting.value} ({setting.mode})")
else:
print(f"Error: {result.error.description}")

```

**Python (Pythonic API):**

```

from duvcctl import CameraController

with CameraController() as cam:
print(f"Brightness: {cam.brightness}")

```

**C++:**

```

\#include <duvc-ctl/duvc.hpp>
\#include <iostream>

int main() {
auto devices = duvc::list_devices();
if (devices.empty()) return 1;

    duvc::Camera cam(devices);
    auto result = cam.get(duvc::VidProp::Brightness);
    
    if (result.is_ok()) {
        auto setting = result.value;
        std::cout << "Brightness: " << setting.value << "\n";
    } else {
        std::cerr << "Error: " << result.error.description << "\n";
    }
    }

```

**C ABI:**

```

\#include <duvc-ctl/capi.h>
\#include <stdio.h>

int main() {
duvc_initialize();

    duvc_device_t* devices;
    size_t count;
    duvc_list_devices(&devices, &count);
    
    if (count > 0) {
        duvc_prop_setting_t brightness;
        if (duvc_get_video_property(devices, DUVC_VIDPROP_BRIGHTNESS, &brightness) == DUVC_SUCCESS) {
            printf("Brightness: %d (%s)\n", brightness.value,
                   brightness.mode == DUVC_CAMMODE_AUTO ? "AUTO" : "MANUAL");
        }
    }
    
    duvc_free_device_list(devices, count);
    duvc_shutdown();
    }

```

**CLI:**

```

duvc-cli get 0 vid Brightness

# Output: Brightness: 128 (MANUAL)

```

---

### Set Brightness

**Python:**

```

import duvcctl as duvc

devices = duvc.list_devices()
camera = duvc.Camera(devices)
setting = duvc.PropSetting(180, duvc.CamMode.Manual)
result = camera.set_property(duvc.VidProp.Brightness, setting)

if result.is_ok():
print("Brightness set to 180")
else:
print(f"Failed: {result.error.description}")

```

**C++:**

```

duvc::Camera cam(devices);
duvc::PropSetting setting{180, duvc::CamMode::Manual};
auto result = cam.set(duvc::VidProp::Brightness, setting);

if (result.is_ok()) {
std::cout << "Brightness set\n";
}

```

**C ABI:**

```

duvc_prop_setting_t setting = {180, DUVC_CAMMODE_MANUAL};
duvc_result_t result = duvc_set_video_property(devices, DUVC_VIDPROP_BRIGHTNESS, \&setting);

if (result == DUVC_SUCCESS) {
printf("Brightness set\n");
}

```

**CLI:**

```

duvc-cli set 0 vid Brightness 180 manual

# Output: OK

```

---

## Property Ranges & Validation

### Query Valid Range

**Python:**

```

result = camera.get_range(duvc.VidProp.Brightness)
if result.is_ok():
r = result.value
print(f"Range: {r.min}–{r.max}, step={r.step}, default={r.default_val}")

```

**C++:**

```

auto range_result = cam.get_range(duvc::VidProp::Brightness);
if (range_result.is_ok()) {
auto r = range_result.value;
std::cout << "Range: " << r.min << "–" << r.max << "\n";
}

```

**C ABI:**

```

duvc_prop_range_t range;
if (duvc_get_video_property_range(devices, DUVC_VIDPROP_BRIGHTNESS, \&range) == DUVC_SUCCESS) {
printf("Range: %d–%d (step=%d)\n", range.min, range.max, range.step);
}

```

**CLI:**

```

duvc-cli range 0 vid Brightness

# Output: Brightness: min=0, max=255, step=1, default=128, mode=AUTO

```

### Clamp Value to Range

**Python:**

```

result = camera.get_range(duvc.VidProp.Brightness)
if result.is_ok():
r = result.value
safe_value = max(r.min, min(r.max, 300))  \# Clamps 300 → 255
camera.set_property(duvc.VidProp.Brightness, duvc.PropSetting(safe_value, duvc.CamMode.Manual))

```

**C++:**

```

auto range = cam.get_range(duvc::VidProp::Brightness).value;
int clamped = range.clamp(300);  // Built-in clamp method
cam.set(duvc::VidProp::Brightness, {clamped, duvc::CamMode::Manual});

```

**C ABI:**

```

duvc_prop_range_t range;
duvc_get_video_property_range(devices, DUVC_VIDPROP_BRIGHTNESS, \&range);
int32_t clamped = duvc_clamp_value(\&range, 300);
duvc_prop_setting_t setting = {clamped, DUVC_CAMMODE_MANUAL};
duvc_set_video_property(devices, DUVC_VIDPROP_BRIGHTNESS, \&setting);

```

---

## Common Properties

| Property | Type | Range (typical) | Description |
|----------|------|-----------------|-------------|
| `Brightness` | Video | 0–255 | Image luminance |
| `Contrast` | Video | 0–255 | Difference between light/dark |
| `Saturation` | Video | 0–255 | Color intensity |
| `Pan` | Camera | -180° to +180° | Horizontal rotation (PTZ) |
| `Tilt` | Camera | -180° to +180° | Vertical rotation (PTZ) |
| `Zoom` | Camera | 100–500 | Optical zoom level |
| `Focus` | Camera | 0–255 | Manual focus distance |
| `Exposure` | Camera | -13 to -1 | Exposure time (log₂ seconds) |

**Python:** Use `duvc.VidProp.*` and `duvc.CamProp.*` enums  
**C++:** Use `duvc::VidProp::*` and `duvc::CamProp::*` enums  
**C ABI:** Use `DUVC_VIDPROP_*` and `DUVC_CAMPROP_*` constants  
**CLI:** Use names like `Brightness`, `Pan`, `Zoom` (case-insensitive)

---

## PTZ Camera Control

**Python:**

```

from duvcctl import CameraController

with CameraController() as cam:
cam.pan = 0       \# Center
cam.tilt = 0      \# Center
cam.zoom = 150    \# Zoom in

```

**C++:**

```

duvc::Camera cam(devices);
cam.set(duvc::CamProp::Pan, {0, duvc::CamMode::Manual});
cam.set(duvc::CamProp::Tilt, {0, duvc::CamMode::Manual});
cam.set(duvc::CamProp::Zoom, {150, duvc::CamMode::Manual});

```

**C ABI:**

```

duvc_prop_setting_t center = {0, DUVC_CAMMODE_MANUAL};
duvc_set_camera_property(devices, DUVC_CAMPROP_PAN, \&center);
duvc_set_camera_property(devices, DUVC_CAMPROP_TILT, \&center);

duvc_prop_setting_t zoom = {150, DUVC_CAMMODE_MANUAL};
duvc_set_camera_property(devices, DUVC_CAMPROP_ZOOM, \&zoom);

```

**CLI:**

```

duvc-cli set 0 cam Pan 0 manual
duvc-cli set 0 cam Tilt 0 manual
duvc-cli set 0 cam Zoom 150 manual

```

---

## Error Handling

### Python (Pythonic API – Exceptions)

```

from duvcctl import CameraController, PropertyNotSupportedError, InvalidValueError

try:
with CameraController() as cam:
cam.brightness = 999  \# Out of range
except InvalidValueError as e:
print(f"Invalid value: {e}")
except PropertyNotSupportedError:
print("Property not supported")

```

### Python (Result-based API – Explicit Checks)

```

result = camera.set_property(duvc.VidProp.Brightness, duvc.PropSetting(999, duvc.CamMode.Manual))
if result.is_error():
print(f"Error code: {result.error.code}")
print(f"Description: {result.error.description}")

```

### C++

```

auto result = cam.set(duvc::VidProp::Brightness, {999, duvc::CamMode::Manual});
if (result.is_error()) {
std::cerr << "Error: " << result.error.description << "\n";
switch (result.error.code) {
case duvc::ErrorCode::InvalidValue:
// Handle out-of-range
break;
case duvc::ErrorCode::PropertyNotSupported:
// Handle unsupported property
break;
default:
break;
}
}

```

### C ABI

```

duvc_result_t result = duvc_set_video_property(devices, DUVC_VIDPROP_BRIGHTNESS, \&setting);
if (result != DUVC_SUCCESS) {
fprintf(stderr, "Error: %s\n", duvc_get_error_string(result));

    // Get detailed error info
    char details;
    size_t required;
    if (duvc_get_last_error_details(details, sizeof(details), &required) == DUVC_SUCCESS) {
        fprintf(stderr, "Details: %s\n", details);
    }
    }

```

### CLI

```

duvc-cli set 0 vid Brightness 999 manual
echo \$?  \# Exit code: 4 (operation error)

```

**Exit codes:**
- `0` Success
- `1` Usage error (bad syntax)
- `2` Device error (not found)
- `3` Property error (unknown property)
- `4` Operation error (set failed)

---

## Check Device Capabilities

**Python:**

```

caps_result = duvc.get_device_capabilities(devices)
if caps_result.is_ok():
caps = caps_result.value
print("Camera properties:", [str(p) for p in caps.supported_camera_properties])
print("Video properties:", [str(p) for p in caps.supported_video_properties])

```

**C++:**

```

duvc::DeviceCapabilities caps(devices);
std::cout << "Supported camera properties:\n";
for (auto prop : caps.supported_camera_properties) {
std::cout << "  - " << duvc::to_string(prop) << "\n";
}

```

**C ABI:**

```

// Query individual property support
int supported;
duvc_supports_camera_property(devices, DUVC_CAMPROP_PAN, \&supported);
if (supported) {
printf("Pan is supported\n");
}

```

**CLI:**

```


# CLI doesn't expose full capability queries

# Use get/range commands to test individual properties:

duvc-cli range 0 cam Pan

# If supported, prints range; if not: "Property not supported"

```

---

## Multi-Device Management

**Python:**

```

devices = duvc.list_devices()
cameras = [duvc.Camera(dev) for dev in devices]

for i, cam in enumerate(cameras):
setting = duvc.PropSetting(150, duvc.CamMode.Manual)
cam.set_property(duvc.VidProp.Brightness, setting)
print(f"Camera {i} brightness set")

```

**C++:**

```

auto devices = duvc::list_devices();
std::vector[duvc::Camera](duvc::Camera) cameras;

for (const auto\& dev : devices) {
cameras.emplace_back(dev);
}

for (size_t i = 0; i < cameras.size(); ++i) {
cameras[i].set(duvc::VidProp::Brightness, {150, duvc::CamMode::Manual});
std::cout << "Camera " << i << " brightness set\n";
}

```

**C ABI:**

```

duvc_device_t* devices;
size_t count;
duvc_list_devices(\&devices, \&count);

duvc_connection_t* connections = calloc(count, sizeof(duvc_connection_t));

for (size_t i = 0; i < count; ++i) {
duvc_create_connection(devices[i], \&connections[i]);
duvc_prop_setting_t brightness = {150, DUVC_CAMMODE_MANUAL};
duvc_connection_set_video_property(connections[i], DUVC_VIDPROP_BRIGHTNESS, \&brightness);
}

// Cleanup
for (size_t i = 0; i < count; ++i) {
duvc_close_connection(connections[i]);
}
free(connections);
duvc_free_device_list(devices, count);

```

**CLI:**

```


# Script to control multiple cameras

for i in 0 1 2; do
duvc-cli set \$i vid Brightness 150 manual
done

```

---

## Device Monitoring (Hot-Plug Events)

**C++ (Advanced):**

```

\#include <duvc-ctl/platform/device_monitor.h>

void on_device_change(bool added, const std::wstring\& path) {
if (added) {
std::wcout << L"Device connected: " << path << L"\n";
} else {
std::wcout << L"Device disconnected: " << path << L"\n";
}
}

int main() {
duvc::register_device_change_callback(on_device_change);
std::cout << "Monitoring... Press Ctrl+C to exit\n";
while (true) {
std::this_thread::sleep_for(std::chrono::seconds(1));
}
}

```

**CLI:**

```

duvc-cli monitor 60

# Monitors for 60 seconds, prints DEVICE_ADDED / DEVICE_REMOVED events

```

---

## API Comparison

| Feature | Python Pythonic | Python Result | C++ | C ABI | CLI |
|---------|-----------------|---------------|-----|-------|-----|
| **Device selection** | Automatic (first) | Manual | Manual | Manual | Manual (index) |
| **Error handling** | Exceptions | `Result<T>` | `Result<T>` | Return codes | Exit codes |
| **Property access** | `cam.brightness = 80` | `camera.set_property(...)` | `cam.set(...)` | `duvc_set_video_property(...)` | `set 0 vid Brightness 80` |
| **Code verbosity** | Low | Medium | Medium | High | N/A (CLI) |
| **Type safety** | Good | Good | Excellent | None (C types) | N/A |
| **Use case** | Prototyping, scripts | Production Python | Production C++ | FFI, other languages | Automation, testing |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ImportError` on non-Windows | duvc-ctl is Windows-only (DirectShow API) |
| No devices found | Check Device Manager; close apps using camera (Zoom, Teams) |
| Property not supported | Query capabilities first: `get_device_capabilities(device)` |
| Permission denied | Run as Administrator; check Windows Privacy Settings |
| Build errors (C/C++) | Ensure CMake 3.16+, Visual Studio 2019+, 64-bit toolchain |

**Enable debug logging:**

**Python:**
```

import duvcctl as duvc
duvc.set_log_level(duvc.LogLevel.Debug)

```

**C++:**
```

duvc::set_log_level(duvc::LogLevel::Debug);

```

**C ABI:**
```

duvc_set_log_level(DUVC_LOGLEVEL_DEBUG);

```

---

## Next Steps

- **[Installation Guide](01_quick-start-installation.md)** — Building from source, CMake options
- **[C++ API Reference](index.md)** — Complete `Camera` class and Result types
- **[C ABI Documentation](index.md)** — Stable C interface for FFI
- **[Python API Reference](index.md)** — Pythonic and Result-based APIs
- **[CLI Documentation](index.md)** — Command reference and scripting examples
- **[Architecture Overview](02_architecture-design-overview.md)** — Threading, error handling, design patterns
- **[Property Reference](12_complete-property-reference.md)** — All camera/video properties with ranges
- **[Examples & Tutorials](13_examples-tutorials.md)** — Advanced workflows and multi-camera patterns

---

**Questions?** Open an issue on [GitHub](https://github.com/allanhanan/duvc-ctl/issues).
```


***