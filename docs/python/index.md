# duvc-ctl Python Documentation

Windows DirectShow UVC camera control library. Dual APIs: CameraController (Pythonic) and Result-based (explicit error handling).
A guide to using the `duvc-ctl` Python library for controlling USB Video Class (UVC) cameras on Windows.
---

## Table of Contents

1. [Overview](#overview)
2. [Installation & Building](#installation--building)
3. [Architecture](#architecture)
4. [API Comparison](#api-comparison)
5. [CameraController API](#cameracontroller-api)
   - [Initialization](#initialization)
   - [Video Properties](#video-properties)
   - [Camera Properties](#camera-properties)
   - [Relative Movement](#relative-movement)
   - [String-Based Access](#string-based-access)
   - [Property Discovery](#property-discovery)
   - [Presets](#presets)
   - [Device Info](#device-info)
6. [Result-Based API](#result-based-api)
   - [Device Enumeration](#device-enumeration)
   - [Camera Access](#camera-access)
   - [Property Operations](#property-operations)
   - [Device Capabilities](#device-capabilities)
   - [Vendor Properties](#vendor-properties)
   - [Monitoring](#monitoring)
7. [Core Types & Enums](#core-types--enums)
8. [Exception Hierarchy](#exception-hierarchy)
9. [Property Reference](#property-reference)
10. [Advanced Topics](#advanced-topics)
11. [Troubleshooting](#troubleshooting)

---

## Overview

**duvc-ctl** provides native USB Video Class (UVC) camera control on Windows via DirectShow. Two complementary APIs:

- **CameraController**: High-level, Pythonic, exception-based
- **Result-Based**: Low-level, explicit error handling, C++ semantics

Both share identical underlying C++ bindings through pybind11. Choose based on error-handling preference.

**Requirements**: Windows 10/11 (x64), Python 3.8+, DirectShow libraries (built-in on Windows)

---

## Installation & Building

### Install from PyPI

```bash
pip install duvc-ctl
```

Wheels include bundled DirectShow DLLs for Python 3.8-3.12 on Windows x64.

### Building from Source

```bash
git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl/bindings/python
pip install -e . -v
```

**Prerequisites:**
- Visual Studio 2019+ with C++ tools
- CMake 3.16+
- pybind11, scikit-build-core

**Build wheel for all Python versions (cibuildwheel):**

```bash
cibuildwheel --platform windows --archs x86_64
```

**Configuration** in `pyproject.toml`:
- `DUVC_BUILD_PYTHON=ON`: Enable Python bindings
- `DUVC_BUILD_STATIC=ON`: Static C runtime (recommended)

---

## Architecture

```
duvc-ctl/
├── C++ Core (DirectShow backend)
│   ├── Camera: Property get/set, device communication
│   ├── Result<T>: Rust-style error handling
│   ├── Enums: CamProp, VidProp, CamMode, ErrorCode
│   └── Types: Device, PropSetting, PropRange
│
├── Python Bindings (pybind11)
│   ├── _duvc_ctl: C++ module (compiled)
│   └── Exports: All types, enums, functions
│
└── Python Layer
    ├── exceptions.py: Exception hierarchy
    ├── __init__.py: CameraController, helper functions
    └── Exports: All public APIs
```

**Two-Layer Design:**
1. **C++ (`_duvc_ctl`)**: Core DirectShow communication, property control
2. **Python Wrapper**: CameraController, exceptions, convenience functions

---

## API Comparison

| Feature | CameraController | Result-Based |
|---------|------------------|--------------|
| Error Handling | Exceptions | Result<T> |
| Property Access | `cam.brightness = 200` | `camera.set(VidProp.Brightness, ...)` |
| Range Checking | Automatic | Manual |
| Auto Mode | `cam.set("exposure", "auto")` | `PropSetting(0, CamMode.Auto)` |
| Context Manager | Yes | Yes |
| Connection Management | Automatic | Manual |
| Use Case | General, simple | Low-level, explicit |

---

## CameraController API

Pythonic interface with automatic connection, range validation, exceptions.

### Initialization

```python
# Default (first camera)
cam = CameraController()

# By index (0-based)
cam = CameraController(device_index=0)

# By name (substring match, case-insensitive)
cam = CameraController(device_name="Logitech")

# Context manager (recommended)
with CameraController() as cam:
    cam.brightness = 200

# Manual cleanup
cam = CameraController()
try:
    cam.brightness = 200
finally:
    cam.close()
```

**Initialization Logic:**
1. List all devices via `list_devices()`
2. Find matching device by index or name
3. Open camera, verify connection
4. Query device capabilities for range validation

**Raises:**
- `DeviceNotFoundError`: No camera or name mismatch
- `DeviceBusyError`: Camera in use
- `SystemError`: DirectShow failure

### Video Properties

All use actual **device ranges** (not hardcoded 0-100).

```python
# Get/set (direct property access)
cam.brightness = 200
val = cam.brightness  # Returns int

# Typical ranges (device-specific)
cam.brightness = 200           # 0-255
cam.contrast = 50              # 0-100
cam.saturation = 80            # 0-100
cam.hue = -10                  # -180 to 180
cam.sharpness = 5              # 0-100
cam.gamma = 100                # 100-300 (typical)
cam.white_balance = 4500       # Kelvin (device-specific)
cam.gain = 10                  # 0-100
cam.color_enable = True        # Boolean
cam.video_backlight_compensation = 1  # 0 or 1
```

**Setter Behavior:**
1. Query device range via `_get_dynamic_range()`
2. Clamp value: `max(min_val, min(value, max_val))`
3. Set via `_set_video_property()`
4. Raise `InvalidValueError` if outside range

**Getter Behavior:**
1. Call `_get_video_property()`
2. Return int value
3. Raise `PropertyNotSupportedError` if unsupported

### Camera Properties

PTZ, exposure, focus, iris, zoom. Device-specific ranges.

```python
# Position (degrees, device range varies)
cam.pan = 30                   # e.g., -180 to 180
cam.tilt = -15                 # e.g., -90 to 90
cam.roll = 0                   # e.g., -180 to 180

# Optics
cam.zoom = 200                 # e.g., 100-400
cam.focus = 50                 # 0-100 (or device-specific)
cam.iris = 10                  # 0-100
cam.exposure = -5              # e.g., -13 to 1 (log2 seconds)

# Digital
cam.digital_zoom = 100         # e.g., 100-400
cam.backlight_compensation = 1 # 0-2

# Boolean/discrete
cam.privacy = False            # Boolean
cam.scan_mode = 0              # 0 (progressive), 1 (interlaced)
```

**Dynamic Range Discovery:**
Query device range at setter time. If device reports no range, use fallback defaults.

```python
# Example: Setting exposure with range validation
# 1. Get device range: [-13, 1] (typical)
# 2. Clamp value: exposure=-5 (in range)
# 3. Set via C++ core
# 4. If value outside range, raise InvalidValueError
```

### Relative Movement

No range validation (relative deltas). Common for PTZ cameras.

```python
# Movement (delta values, no clamping)
cam.pan_relative(10)           # Move pan +10 degrees
cam.tilt_relative(-5)          # Move tilt -5 degrees
cam.roll_relative(2)           # Roll +2 degrees
cam.zoom_relative(1)           # Zoom +1 step
cam.focus_relative(5)          # Focus +5 steps
cam.exposure_relative(-1)      # Exposure -1 step
cam.iris_relative(2)           # Iris +2 steps
cam.digital_zoom_relative(-1)  # Digital zoom -1 step

# Combined
cam.set_pan_tilt(30, -15)      # Set both simultaneously
cam.pan_tilt_relative(5, -5)   # Move both by delta
```

**Note:** Relative methods don't use ranges because deltas are directional, not absolute positions.

### String-Based Access

Property names as strings, flexible mode specification.

```python
# Get by string
value = cam.get("brightness")           # Returns int
value = cam.get("white_balance")        # Any property

# Set by string
cam.set("brightness", 200)              # Manual control
cam.set("brightness", 200, "manual")    # Explicit mode
cam.set("exposure", "auto")             # Auto mode (special string)
cam.set("focus", "auto")                # Parse "auto" -> CamMode.Auto

# Batch operations
results = cam.set_multiple({
    "brightness": 200,
    "contrast": 50,
    "saturation": 80
})
# Returns: {'brightness': True, 'contrast': True, 'saturation': True}
# (or False if failed)

values = cam.get_multiple(["brightness", "contrast", "saturation"])
# Returns: {'brightness': 200, 'contrast': 50, 'saturation': 80}
# (or None for each if failed)
```

**String Mode Parsing:**
- `"auto"` → `CamMode.Auto`
- `"manual"` → `CamMode.Manual`
- Default if omitted: `CamMode.Manual`

### Property Discovery

Introspect device capabilities at runtime.

```python
# All supported properties
supported = cam.get_supported_properties()
# Returns: {'camera': ['pan', 'tilt', 'zoom', ...], 
#           'video': ['brightness', 'contrast', ...]}

# Property aliases (convenience names)
aliases = cam.get_property_aliases()
# {'brightness': ['brightness', 'bright'],
#  'white_balance': ['white_balance', 'wb'],
#  'zoom': ['zoom', 'z'],
#  'exposure': ['exposure', 'exp'],
#  'focus': ['focus', 'f'],
#  'pan': ['pan', 'horizontal'],
#  'tilt': ['tilt', 'vertical']}

# Check if supported
is_supported = cam.is_property_supported("pan")
is_supported = cam.is_property_supported("exposure")

# List all properties
all_props = cam.list_properties()
# Returns: {'camera': [...], 'video': [...]}
```

**Usage Pattern:**
Query `get_supported_properties()` before calling setters to avoid `PropertyNotSupportedError`.

### Property Ranges

Query device range for validation.

```python
range_info = cam.get_property_range("brightness")

if range_info:
    print(range_info['min'])       # Min value
    print(range_info['max'])       # Max value
    print(range_info['step'])      # Step size
    print(range_info['default'])   # Default value
else:
    print("Not supported")
    
# Example
range_info = cam.get_property_range("exposure")
# {'min': -13, 'max': 1, 'step': 1, 'default': -5}
```

**Returns:** `None` if property unsupported or device doesn't report range.

### Auto Mode

Properties supporting auto control.

```python
# Set to auto (for properties that support it)
cam.set("white_balance", "auto")
cam.set("exposure", "auto")
cam.set("focus", "auto")
cam.set("iris", "auto")

# Get current mode
setting_info = cam.get_setting_info("exposure")
# Returns: {'value': -5, 'mode': 'manual'} or {'mode': 'auto'}

# Set with explicit mode
cam.set("white_balance", 4500, "manual")
```

**Auto-Supported Properties (typical):**
- Exposure, Focus, Iris, White Balance, Gain

**Returns:** `PropertyNotSupportedError` if property doesn't support auto mode.

### Presets

Pre-defined and custom camera configurations.

```python
# Built-in presets
presets = cam.get_preset_names()
# Returns: ['default', 'daylight', 'indoor', 'night', ...]

# Apply preset
cam.apply_preset('daylight')
# Sets: brightness, contrast, saturation, white balance for daylight

# Create custom preset
cam.create_custom_preset('myconfig', {
    'brightness': 200,
    'contrast': 50,
    'saturation': 80,
    'white_balance': 5000
})

# Apply custom
cam.apply_preset('myconfig')

# List custom presets
custom = cam.get_custom_presets()
# Returns: ['myconfig', ...]

# Delete custom
cam.delete_custom_preset('myconfig')
```

**Behavior:**
- Built-in presets: Camera-specific, may vary
- Custom presets: Stored in-memory during session
- Persists to file (if implemented): Check documentation

### Device Info

Camera and device metadata.

```python
# Connected status
if cam.is_connected:
    print("Camera connected")

# Device metadata
name = cam.device_name       # Display name, e.g., "Logitech C920"
path = cam.device_path       # Unique identifier (Windows path)

# Access core C++ camera for advanced use
core_camera = cam.core       # Direct access to Result-based API
```

### Convenience Methods

Batch operations.

```python
# Reset all to defaults
cam.reset_to_defaults()
# Internally: Sets all properties to auto or default values
# Logs: Warning for unsupported properties

# Center camera (pan/tilt)
cam.center_camera()
# Calculates: (min+max)/2 for pan and tilt
# Centers camera to middle of range
# Logs: Warning if pan/tilt unsupported

# Close (manual cleanup)
cam.close()
```

---

## Result-Based API

Low-level explicit error handling. All operations return `Result<T>`.

### Device Enumeration

List and find devices.

```python
# List all devices
devices = list_devices()
# Returns: List[Device]

# Iterate devices
for device in iter_devices():
    print(device.name, device.path)

# Iterate connected only
for device in iter_connected_devices():
    print(device.name)

# Find by name (first match)
device = find_device_by_name("Logitech")

# Find all matches
devices = find_devices_by_name("USB")

# Check connection
connected = is_device_connected(device)
# Returns: bool
```

**Device Properties:**
- `name: str` - Display name
- `path: str` - Unique identifier
- `is_valid(): bool` - Validity check

### Camera Access

Open and manage camera connections.

```python
# Open by device
camera_result = open_camera(device)
if camera_result.is_ok():
    camera = camera_result.value()
    # Use camera
else:
    error = camera_result.error()
    print(error.description())

# Open by index
camera_result = open_camera(0)

# Context manager
with open_camera(0) as camera:
    # Automatic cleanup
    if camera.is_ok():
        cam = camera.value()

# Open by name
with open_device_by_name_context("Logitech") as camera:
    if camera.is_ok():
        cam = camera.value()

# Check validity
if camera.is_valid():
    print("Camera ready")
```

**Return Values:**
- `camera_result.is_ok()`: True if opened successfully
- `camera_result.value()`: Camera object
- `camera_result.error()`: CppError object

**Raises:** Nothing (Result-based, no exceptions).

### Property Operations

Get, set, and query ranges.

```python
# Get property
result = camera.get(VidProp.Brightness)
if result.is_ok():
    setting = result.value()
    print(f"Value: {setting.value}")
    print(f"Mode: {setting.mode}")

# Set property
setting = PropSetting(200, CamMode.Manual)
result = camera.set(VidProp.Brightness, setting)
if not result.is_ok():
    error = result.error()
    print(f"Error: {error.description()}")

# Get range
range_result = camera.get_range(VidProp.Brightness)
if range_result.is_ok():
    r = range_result.value()
    print(f"{r.min} - {r.max} step {r.step}")
    
    # Clamp value
    clamped = r.clamp(value)

# Get camera properties
result = camera.get(CamProp.Pan)
result = camera.get(CamProp.Zoom)
```

**Properties Are Type-Safe:**
- `VidProp.*`: Video properties (brightness, contrast, etc.)
- `CamProp.*`: Camera properties (pan, tilt, zoom, etc.)

**Error Handling:**
Always check `.is_ok()` before `.value()`.

### Direct Property Access

Exception-throwing variants (if preferred).

```python
try:
    # Opens camera if needed
    camera = open_camera(0)  # Throws if error
    
    # Get property
    setting = camera.get_video_property(VidProp.Brightness)  # Throws if error
    value = setting.value
    
    # Set property
    success = camera.set_video_property(
        VidProp.Brightness, 
        PropSetting(200, CamMode.Manual)
    )
    
    # Get range
    range_info = camera.get_video_property_range(VidProp.Brightness)
    
except PropertyNotSupportedError:
    print("Not supported")
except InvalidValueError:
    print("Invalid range")
```

### Device Capabilities

Query what camera supports at runtime.

```python
# Get capabilities
caps_result = get_device_capabilities(device)
if caps_result.is_ok():
    caps = caps_result.value()
    
    # Supported properties
    camera_props = caps.supported_camera_properties()
    # Returns: List[CamProp]
    
    video_props = caps.supported_video_properties()
    # Returns: List[VidProp]
    
    # Check support
    supports_pan = caps.supports_camera_property(CamProp.Pan)
    supports_brightness = caps.supports_video_property(VidProp.Brightness)
    
    # Get full capability info
    cap = caps.get_camera_capability(CamProp.Pan)
    if cap:
        print(f"Range: {cap.range.min} - {cap.range.max}")
        print(f"Current: {cap.current.value}")
        print(f"Auto support: {cap.supports_auto()}")
    
    # Refresh (re-query device)
    caps.refresh()

# Device accessibility
if caps.is_device_accessible():
    print("Can access device")
```

### Utility Functions

Convenience operations on devices.

```python
# Reset to defaults
results = reset_device_to_defaults(device)
# Returns: Dict[str, bool] - {'property_name': success, ...}

# Get supported properties
supported = get_supported_properties(device)
# Returns: {'camera': [CamProp, ...], 'video': [VidProp, ...]}

# Get device info
info = get_device_info(device_index=0)
# Returns: Dict with camera_properties and video_properties metadata

# Center camera
success = center_camera_device(device)
```

### Vendor Properties

Windows-specific, GUID-based properties.

```python
import uuid

# Create GUID
vendor_guid = uuid.UUID("{12345678-1234-5678-9abc-123456789abc}")
guid = guid_from_uuid(vendor_guid)

# Read vendor property
success, data = read_vendor_property(device, guid, property_id=1)
if success:
    print(data.hex())

# Write vendor property
data = bytes([0x01, 0x02, 0x03, 0x04])
success = write_vendor_property(device, guid, property_id=1, data=data)
```

**Note:** Vendor properties are device and vendor-specific. Consult device documentation.

### Device Monitoring

React to camera connect/disconnect.

```python
def on_device_change(added: bool, device_path: str):
    if added:
        print(f"Device added: {device_path}")
    else:
        print(f"Device removed: {device_path}")

# Register callback
register_device_change_callback(on_device_change)

# Monitor...
# (Callback fires on USB device change)

# Unregister
unregister_device_change_callback()
```

**Callback Signature:**
```python
Callable[[bool, str], None]
# added: True if connected, False if disconnected
# device_path: Windows device path
```

---

## Core Types & Enums

### Device

```python
class Device:
    name: str              # Display name
    path: str              # Unique identifier
    
    def is_valid() -> bool
```

### PropSetting

Property value and control mode.

```python
class PropSetting:
    value: int             # Current value
    mode: CamMode          # Manual or Auto
    
    def __init__(self, value: int = 0, mode: CamMode = CamMode.Manual):
        pass
```

### PropRange

Property range constraints.

```python
class PropRange:
    min: int               # Minimum value
    max: int               # Maximum value
    step: int              # Step size
    default_val: int       # Default value
    
    def clamp(self, value: int) -> int:
        return max(self.min, min(value, self.max))
```

### Camera

Main camera control object.

```python
class Camera:
    def __init__(self, device: Device)
    def __init__(self, device_index: int)
    
    # Result-based API
    def get(self, prop: CamProp | VidProp) -> PropSettingResult
    def set(self, prop: CamProp | VidProp, setting: PropSetting) -> VoidResult
    def get_range(self, prop: CamProp | VidProp) -> PropRangeResult
    
    # Exception API (throws if error)
    def get_camera_property(self, prop: CamProp) -> PropSetting
    def set_camera_property(self, prop: CamProp, setting: PropSetting) -> bool
    def get_camera_property_range(self, prop: CamProp) -> PropRange
    
    def get_video_property(self, prop: VidProp) -> PropSetting
    def set_video_property(self, prop: VidProp, setting: PropSetting) -> bool
    def get_video_property_range(self, prop: VidProp) -> PropRange
    
    def is_valid(self) -> bool
    def device(self) -> Device
```

### Result Types

Explicit error handling (Rust-style).

```python
class PropSettingResult:
    def is_ok(self) -> bool
    def is_error(self) -> bool
    def value(self) -> PropSetting      # Throws if error
    def error(self) -> CppError

class PropRangeResult:
    def is_ok(self) -> bool
    def is_error(self) -> bool
    def value(self) -> PropRange
    def error(self) -> CppError

class VoidResult:
    def is_ok(self) -> bool
    def is_error(self) -> bool
    def error(self) -> CppError

class CameraResult:
    def is_ok(self) -> bool
    def is_error(self) -> bool
    def value(self) -> Camera
    def error(self) -> CppError

class DeviceCapabilitiesResult:
    def is_ok(self) -> bool
    def is_error(self) -> bool
    def value(self) -> DeviceCapabilities
    def error(self) -> CppError
```

### CppError

C++ error information.

```python
class CppError:
    def code(self) -> ErrorCode
    def description(self) -> str
```

### DeviceCapabilities

Device capability information.

```python
class DeviceCapabilities:
    def supports_camera_property(self, prop: CamProp) -> bool
    def supports_video_property(self, prop: VidProp) -> bool
    def supported_camera_properties(self) -> list[CamProp]
    def supported_video_properties(self) -> list[VidProp]
    def get_camera_capability(self, prop: CamProp) -> PropertyCapability
    def get_video_capability(self, prop: VidProp) -> PropertyCapability
    def device(self) -> Device
    def is_device_accessible(self) -> bool
    def refresh(self) -> None
```

### PropertyCapability

Full capability info for a property.

```python
class PropertyCapability:
    supported: bool        # Supported by device
    range: PropRange       # Min/max/step/default
    current: PropSetting   # Current value and mode
    
    def supports_auto(self) -> bool
```

### Enumerations

#### CamMode

Camera control mode.

```python
class CamMode(Enum):
    Auto = 0               # Camera controls automatically
    Manual = 1             # User-specified value
```

#### CamProp

Camera control properties.

```python
class CamProp(Enum):
    Pan = 0                # Horizontal rotation (degrees)
    Tilt = 1               # Vertical rotation (degrees)
    Roll = 2               # Optical axis rotation (degrees)
    Zoom = 3               # Optical zoom
    Exposure = 4           # Exposure time (log2 seconds)
    Iris = 5               # Aperture/iris
    Focus = 6              # Focus distance
    ScanMode = 7           # Progressive/interlaced
    Privacy = 8            # Privacy mode (boolean)
    PanTilt = 9            # Combined pan/tilt
    DigitalZoom = 10       # Digital zoom
    BacklightCompensation = 11
    PanRelative = 12       # Relative pan
    TiltRelative = 13      # Relative tilt
    RollRelative = 14      # Relative roll
    ZoomRelative = 15      # Relative zoom
    ExposureRelative = 16  # Relative exposure
    IrisRelative = 17      # Relative iris
    FocusRelative = 18     # Relative focus
    PanTiltRelative = 19   # Relative pan/tilt
    FocusSimple = 20       # Simple focus
    DigitalZoomRelative = 21  # Relative digital zoom
    Lamp = 22              # Camera lamp/LED
```

#### VidProp

Video processing properties.

```python
class VidProp(Enum):
    Brightness = 0         # Image brightness
    Contrast = 1           # Image contrast
    Hue = 2                # Color hue
    Saturation = 3         # Color saturation
    Sharpness = 4          # Edge sharpness
    Gamma = 5              # Gamma correction
    ColorEnable = 6        # Color vs B/W
    WhiteBalance = 7       # White balance (Kelvin)
    BacklightCompensation = 8  # Backlight comp
    Gain = 9               # Sensor gain
```

#### ErrorCode

Error codes from C++ core.

```python
class ErrorCode(Enum):
    Success = 0
    DeviceNotFound = 1
    DeviceBusy = 2
    PropertyNotSupported = 3
    InvalidValue = 4
    PermissionDenied = 5
    SystemError = 6
    InvalidArgument = 7
    NotImplemented = 8
```

#### LogLevel

Logging levels.

```python
class LogLevel(Enum):
    Debug = 0
    Info = 1
    Warning = 2
    Error = 3
    Critical = 4
```

---

## Exception Hierarchy

All exceptions inherit from `DuvcError`. CameraController raises these.

```python
DuvcError (base)
├── DeviceNotFoundError
├── DeviceBusyError
├── PropertyNotSupportedError
├── InvalidValueError
├── PermissionDeniedError
├── SystemError
├── InvalidArgumentError
├── NotImplementedError
└── ConnectionError

# Usage
try:
    cam = CameraController(device_name="NonExistent")
except DeviceNotFoundError as e:
    print(f"Device not found: {e}")
    print(f"Error code: {e.error_code}")

try:
    cam.brightness = 999
except InvalidValueError as e:
    print(f"Out of range: {e}")

try:
    cam.set("unsupported", 100)
except PropertyNotSupportedError as e:
    print(f"Not supported: {e}")
```

**Exception Attributes:**
- `message: str` - Error description
- `error_code: int` - ErrorCode value

---

## Property Reference

### Video Properties (VidProp)

Used for image processing (software or camera firmware).

| Property | Typical Range | Unit | Notes |
|----------|---------------|------|-------|
| Brightness | 0-255 | Value | Device-specific |
| Contrast | 0-100 | % | Device-specific |
| Hue | -180 to 180 | Degrees | May not be supported |
| Saturation | 0-100 | % | Device-specific |
| Sharpness | 0-100 | % | Device-specific |
| Gamma | 100-300 | Value | Device-specific |
| ColorEnable | 0-1 | Boolean | Color (1) or B/W (0) |
| WhiteBalance | 2700-6500 | Kelvin | Device-specific, auto available |
| BacklightCompensation (Video) | 0-2 | Mode | 0=Off, 1=On, 2=Enhanced |
| Gain | 0-100 | % | Sensor amplification |

### Camera Properties (CamProp)

Device-level controls (hardware PTZ, exposure, etc.).

| Property | Typical Range | Unit | Notes |
|----------|---------------|------|-------|
| Pan | -180 to 180 | Degrees | Device-specific |
| Tilt | -90 to 90 | Degrees | Device-specific |
| Roll | -180 to 180 | Degrees | Rarely supported |
| Zoom | 100-400 | % | Optical zoom |
| Exposure | -13 to 1 | log2(seconds) | Auto mode available |
| Focus | 0-100 | % | Auto mode available |
| Iris | 0-100 | % | Auto mode available |
| ScanMode | 0-1 | Mode | 0=Progressive, 1=Interlaced |
| Privacy | 0-1 | Boolean | Hardware privacy shutter |
| BacklightCompensation (Camera) | 0-2 | Mode | Camera-level comp |
| DigitalZoom | 100-400 | % | Software zoom |

### Range Availability

Not all devices report ranges. Fallback defaults:

```python
# Video properties
brightness: (0, 255)
contrast: (0, 100)
saturation: (0, 100)
hue: (-180, 180)
sharpness: (0, 100)
gamma: (100, 300)
white_balance: (2700, 6500)
gain: (0, 100)

# Camera properties
pan: (-180, 180)
tilt: (-90, 90)
zoom: (100, 400)
exposure: (-13, 1)
focus: (0, 100)
iris: (0, 100)
digital_zoom: (100, 400)
```

---

## Advanced Topics

### Connection Pooling

Internally managed (pybind11, one-to-one). No manual pooling needed.

### Property Change Callbacks

Via `register_device_change_callback()`. No per-property callbacks.

### Mode Control

Auto mode supported for: Exposure, Focus, Iris, White Balance, Gain. Others manual-only.

```python
# Auto
cam.set("exposure", "auto")

# Manual with value
cam.set("exposure", -5, "manual")

# Direct property
prop_setting = PropSetting(-5, CamMode.Manual)
camera.set(CamProp.Exposure, prop_setting)
```

### Range Validation

CameraController validates all values before sending to device.

```python
# Internal: _get_dynamic_range() queries device
# Then: clamp(value, min, max)
# Then: send to C++
# Raises: InvalidValueError if device rejects
```

### DirectShow Integration

All camera access via DirectShow APIs (Windows). No alternative backends.

- **Device Enumeration**: IMoniker, SysDevEnum
- **Property Control**: IAMVideoProcAmp, IAMCameraControl
- **Vendor Extensions**: KSPROPERTY interface

---

## Troubleshooting

### Camera Not Found

```python
# Check enumeration
devices = list_devices()
if not devices:
    print("No cameras detected")
    # Check Device Manager, USB drivers
    
# List names
for d in devices:
    print(d.name)
```

### Property Unsupported

```python
try:
    cam.set("pan", 30)
except PropertyNotSupportedError:
    print("Pan not supported (fixed camera?)")
    
# Check support first
if "pan" in cam.get_supported_properties()['camera']:
    cam.pan = 30
```

### Out of Range

```python
try:
    cam.brightness = 999
except InvalidValueError as e:
    print(f"Value outside range: {e}")
    
# Check range
r = cam.get_property_range("brightness")
print(f"Valid: {r['min']}-{r['max']}")
```

### Device Busy

```python
try:
    cam = CameraController(device_index=0)
except DeviceBusyError:
    print("Camera in use by another app")
    # Close other apps
```

### Build Failures

**Windows SDK missing:**
```bash
# Install Visual Studio C++ workload
# Verify: cmake --version (3.16+)
```

**DLL not found on import:**
```bash
# Rebuild with static runtime
pip install --force-reinstall --no-cache-dir duvc-ctl
```

**CMake errors:**
```bash
# Update pybind11
pip install --upgrade pybind11
```

---

## Examples

### Simple Brightness Control

```python
from duvc_ctl import CameraController, InvalidValueError

with CameraController() as cam:
    try:
        cam.brightness = 200
        print(f"Set brightness to {cam.brightness}")
    except InvalidValueError as e:
        print(f"Failed: {e}")
```

### Query and Set All Properties

```python
with CameraController() as cam:
    supported = cam.get_supported_properties()
    
    for prop in supported['video']:
        try:
            val = cam.get(prop)
            r = cam.get_property_range(prop)
            if r:
                print(f"{prop}: {val} ({r['min']}-{r['max']})")
        except Exception:
            pass
```

### Result-Based Error Handling

```python
from duvc_ctl import open_camera, VidProp, PropSetting, CamMode

result = open_camera(0)
if result.is_ok():
    cam = result.value()
    
    # Set with validation
    setting = PropSetting(200, CamMode.Manual)
    set_result = cam.set(VidProp.Brightness, setting)
    
    if set_result.is_ok():
        print("Success")
    else:
        print(f"Error: {set_result.error().description()}")
else:
    print(f"Cannot open: {result.error().description()}")
```

---

**For more examples, see** `example.py` **and** `simple_api.py` **in the repository.**

## Building from Source

Building from source requires `cibuildwheel` for proper DLL bundling and wheel repair on Windows.

### Prerequisites

Install required tools:

```bash
# Build tools
pip install scikit-build-core pybind11 cibuildwheel

# Windows-specific (for wheel repair)  
pip install delvewheel

# Development tools
pip install -r requirements-dev.txt
```

**System Requirements:**

- Visual Studio 2019/2022 with C++ tools
- CMake 3.16+
- Python 3.8+


### Build Process

#### Method 1: Using cibuildwheel (Recommended)

For production builds with proper DLL bundling:

```bash
# Clone repository
git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl/bindings/python

# Build wheels for all supported Python versions
cibuildwheel --platform windows --archs x86_64

# Or build for specific Python version
cibuildwheel --platform windows --archs x86_64 --build cp311-win_amd64
```

This will:

1. Build the C++ extension for each Python version
2. Locate and bundle required DLLs (e.g., `duvc-core.dll`)
3. Create distributable wheels in `wheelhouse/`

#### Method 2: Development Build

For local development and testing:

```bash
# Clone repository
git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl/bindings/python

# Install in development mode
pip install -e . -v

# Or build wheel locally
pip install build
python -m build
```


### Build Configuration

The build is configured via `pyproject.toml`:

```toml
[tool.scikit-build]
cmake.args = [
    "-DDUVC_BUILD_PYTHON=ON",
    "-DDUVC_BUILD_CLI=OFF", 
    "-DDUVC_BUILD_STATIC=ON",
    "-DDUVC_BUILD_C_API=OFF",
]

[tool.cibuildwheel]
build = "cp3{8,9,10,11,12}-win_amd64"
skip = "pp*"  # Skip PyPy

[tool.cibuildwheel.windows]
before-build = "pip install cmake pybind11[global]"
repair-wheel-command = "python repair_wheel.py {wheel} {dest_dir}"
```


### DLL Repair Process

The `repair_wheel.py` script handles DLL bundling:

1. **Locate DLL**: Finds `duvc-core.dll` in `build/{wheel_tag}/bin/Release/`
2. **Bundle Dependencies**: Uses `delvewheel` to bundle DLL into wheel
3. **Repair Wheel**: Creates self-contained wheel with all dependencies
```python
# Key part of repair_wheel.py
def find_dll_in_bin_release(build_dir: Path, dll_name: str = 'duvc-core.dll') -> str:
    search_path = build_dir / 'bin' / 'Release'  
    dll_path = search_path / dll_name
    if dll_path.exists():
        return str(dll_path)
    raise FileNotFoundError(f"Could not find {dll_name} in {search_path}")
```


### Testing Build

After building, test the installation:

```python
import duvc_ctl
print(f"duvc-ctl version: {duvc_ctl.__version__}")

# Test basic functionality
devices = duvc_ctl.list_devices()
print(f"Found {len(devices)} cameras")
```


### Troubleshooting Build Issues

**CMake Configuration Errors:**

- Ensure Visual Studio C++ tools are installed
- Check CMake version (3.16+ required)
- Verify MSVC compiler is in PATH

**DLL Not Found:**

- Check that `DUVC_BUILD_STATIC=ON` in CMake args
- Verify DLL is built in `build/{wheel_tag}/bin/Release/`
- Ensure `delvewheel` is installed for wheel repair

**Import Errors:**

- Check that wheel was built for correct Python version
- Verify all DLL dependencies are bundled
- Try rebuilding with `-v` flag for verbose output

**Platform Issues:**

- This library is Windows-only
- Ensure building on Windows x64
- Check that DirectShow libraries are available


## Troubleshooting

### Common Issues

**Import Error: "Could not import C++ extension module"**

- **Cause**: Missing or incompatible C++ extension
- **Solution**: Reinstall with `pip install --force-reinstall duvc-ctl`
- **Platform**: Ensure you're on Windows x64

**DeviceNotFoundError**

- **Cause**: No UVC cameras connected or drivers missing
- **Solution**: Check Device Manager, install camera drivers
- **USB**: Try different USB ports, check USB 3.0/2.0 compatibility

**DeviceBusyError**

- **Cause**: Camera in use by another application
- **Solution**: Close other camera apps, restart application
- **Persistent**: Restart Windows to clear driver locks

**PropertyNotSupportedError**

- **Cause**: Camera doesn't support requested property
- **Solution**: Use `get_device_capabilities()` to check support
- **Alternative**: Try different property or camera model

**PermissionDeniedError**

- **Cause**: Windows camera privacy settings
- **Solution**: Enable camera access in Windows Privacy Settings
- **App-specific**: Allow camera access for Python/your application

**SystemError with COM/DirectShow**

- **Cause**: DirectShow subsystem issues
- **Solution**: Update camera drivers, restart Windows
- **COM**: Try running as administrator


### Debugging Tips

**Enable Verbose Logging:**

```python
import duvc_ctl
import logging

# Enable debug output (if supported by build)
logging.basicConfig(level=logging.DEBUG)
```

**Check Device Capabilities:**

```python
def diagnose_device(device_index=0):
    devices = duvc.list_devices()
    if device_index < len(devices):
        device = devices[device_index]
        
        print(f"Device: {device.name}")
        print(f"Connected: {duvc.is_device_connected(device)}")
        
        caps_result = duvc.get_device_capabilities(device)
        if caps_result.is_ok():
            caps = caps_result.value()
            print(f"Camera properties: {caps.supported_camera_properties()}")
            print(f"Video properties: {caps.supported_video_properties()}")
```

**Test DirectShow Connectivity:**

```python
def test_directshow_access():
    try:
        devices = duvc.list_devices()
        print(f"DirectShow enumeration: OK ({len(devices)} devices)")
        
        if devices:
            device = devices[^0]
            with duvc.open_camera(0) as camera:
                print("DirectShow camera access: OK")
                
    except Exception as e:
        print(f"DirectShow error: {e}")
```


### Performance Optimization

**Error Handling:**

- Use Result-based API (`camera.get()`) for performance-critical code
- Cache `DeviceCapabilities` instead of repeated queries
- Handle exceptions at appropriate granularity

**Threading Considerations:**

- Library is thread-safe for different devices
- Avoid concurrent access to same device from multiple threads
- Use device change callbacks from main thread only


### Getting Help

**Documentation:**

- GitHub: https://github.com/allanhanan/duvc-ctl
- Issues: https://github.com/allanhanan/duvc-ctl/issues

**System Information for Bug Reports:**

- Windows version and build
- Python version and architecture
- Camera make/model and driver version
- Full error messages and stack traces
- Output from `duvc.get_device_info(device)`
 