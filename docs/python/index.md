# duvc-ctl Python Documentation

A comprehensive guide to using the `duvc-ctl` Python library for controlling USB Video Class (UVC) cameras on Windows.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [API Reference](#api-reference)
    - [Core Classes](#core-classes)
    - [Enumerations](#enumerations)
    - [Functions](#functions)
    - [Result Types](#result-types)
    - [Exceptions](#exceptions)
5. [Examples](#examples)
    - [Basic Device Control](#basic-device-control)
    - [PTZ Operations](#ptz-operations)
    - [Property Management](#property-management)
    - [Device Monitoring](#device-monitoring)
    - [Vendor Properties](#vendor-properties)
    - [Error Handling](#error-handling)
6. [Building from Source](#building-from-source)
7. [Troubleshooting](#troubleshooting)

## Overview

`duvc-ctl` is a Python library that provides native control over USB Video Class (UVC) cameras on Windows through DirectShow APIs. It enables developers to:

- **Control Camera Properties**: Pan, tilt, zoom, focus, exposure, iris settings
- **Adjust Video Properties**: Brightness, contrast, saturation, hue, gamma, sharpness
- **Monitor Devices**: Enumerate devices, detect hotplug events, check connectivity
- **Access Vendor Extensions**: Read/write vendor-specific properties using GUIDs
- **Handle Errors Robustly**: Comprehensive exception handling with detailed error codes


### Key Features

- **Windows-Native**: Uses DirectShow APIs for optimal performance and compatibility
- **No Dependencies**: Self-contained with embedded C++ extension
- **Type Safe**: Full type hints support with `py.typed` marker
- **Vendor Support**: Extensible GUID-based vendor property system


### Requirements

- **OS**: Windows 10/11 (x64)
- **Python**: 3.8+
- **Hardware**: UVC-compatible cameras


## Installation

Install from PyPI:

```bash
pip install duvc-ctl
```

The package includes pre-built wheels for Windows x64 with all necessary dependencies bundled.

## Quick Start

```python
import duvc_ctl as duvc

# List all connected cameras
devices = duvc.list_devices()
print(f"Found {len(devices)} cameras")

if devices:
    device = devices[^0]
    print(f"Using: {device.name}")
    
    # Get device capabilities
    caps_result = duvc.get_device_capabilities(device)
    if caps_result.is_ok():
        caps = caps_result.value()
        print(f"Supported camera properties: {len(caps.supported_camera_properties())}")
        print(f"Supported video properties: {len(caps.supported_video_properties())}")
    
    # Set manual focus to middle of range
    focus_ok, focus_range = duvc.get_camera_property_range_direct(device, duvc.CamProp.Focus)
    if focus_ok:
        mid_focus = (focus_range.min + focus_range.max) // 2
        setting = duvc.PropSetting(mid_focus, duvc.CamMode.Manual)
        
        # Using Camera wrapper (recommended)
        with duvc.open_camera(0) as camera:
            camera.set_camera_property(duvc.CamProp.Focus, setting)
            current = camera.get_camera_property(duvc.CamProp.Focus)
            print(f"Focus set to: {current.value}")
```


## API Reference

### Core Classes

#### Device

Represents a UVC camera device with identifying information.

```python
class Device:
    name: str          # Human-readable device name
    path: str          # Unique device path identifier
    
    def is_valid(self) -> bool:
        """Check if device reference is valid"""
```

**Usage:**

```python
devices = duvc.list_devices()
device = devices[^0]
print(f"Name: {device.name}")
print(f"Path: {device.path}")
print(f"Valid: {device.is_valid()}")
```


#### PropSetting

Encapsulates a property value with its control mode.

```python
class PropSetting:
    value: int         # Property value
    mode: CamMode      # Control mode (Auto/Manual)
    
    def __init__(self, value: int = 0, mode: CamMode = CamMode.Manual)
```

**Usage:**

```python
# Manual setting
manual_zoom = duvc.PropSetting(300, duvc.CamMode.Manual)

# Auto setting
auto_exposure = duvc.PropSetting(0, duvc.CamMode.Auto)
```


#### PropRange

Defines the valid range and constraints for a property.

```python
class PropRange:
    min: int           # Minimum value
    max: int           # Maximum value  
    step: int          # Step increment
    default_val: int   # Factory default value
    
    def clamp(self, value: int) -> int:
        """Clamp value to valid range and step alignment"""
```

**Usage:**

```python
ok, range_info = duvc.get_camera_property_range_direct(device, duvc.CamProp.Pan)
if ok:
    print(f"Pan range: {range_info.min} to {range_info.max}, step: {range_info.step}")
    valid_value = range_info.clamp(150)  # Ensure value is valid
```


#### Camera

RAII wrapper for device access with automatic resource management.

```python
class Camera:
    def __init__(self, device: Device)
    def __init__(self, device_index: int)
    
    def is_valid(self) -> bool
    def device(self) -> Device
    
    # Camera properties
    def get_camera_property(self, prop: CamProp) -> PropSetting
    def set_camera_property(self, prop: CamProp, setting: PropSetting) -> bool
    def get_camera_property_range(self, prop: CamProp) -> PropRange
    
    # Video properties  
    def get_video_property(self, prop: VidProp) -> PropSetting
    def set_video_property(self, prop: VidProp, setting: PropSetting) -> bool
    def get_video_property_range(self, prop: VidProp) -> PropRange
    
    # Result-based API (doesn't throw exceptions)
    def get(self, prop: CamProp) -> PropSettingResult
    def set(self, prop: CamProp, setting: PropSetting) -> VoidResult
    def get_range(self, prop: CamProp) -> PropRangeResult
```

**Usage:**

```python
# Method 1: Direct construction
camera = duvc.Camera(device)

# Method 2: By index
camera = duvc.Camera(0)

# Method 3: Context manager (recommended)
with duvc.open_camera(0) as camera:
    zoom = camera.get_camera_property(duvc.CamProp.Zoom)
    print(f"Current zoom: {zoom.value}")
```


#### DeviceCapabilities

Provides detailed information about device supported properties and capabilities.

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


#### PropertyCapability

Detailed capability information for a specific property.

```python
class PropertyCapability:
    supported: bool        # Property is supported
    range: PropRange       # Valid value range
    current: PropSetting   # Current setting
    
    def supports_auto(self) -> bool
```


#### PyGUID (Windows-only)

Wrapper for Windows GUID structures used in vendor property access.

```python
class PyGUID:
    def __init__(self, guid_string: str = "")
    def to_string(self) -> str
```


### Enumerations

#### CamMode

Control mode for camera properties.

```python
class CamMode(Enum):
    Auto = 0      # Automatic control by camera
    Manual = 1    # Manual control with specified value
```


#### CamProp

Camera control properties (IAMCameraControl interface).

```python
class CamProp(Enum):
    Pan = 0                    # Horizontal rotation
    Tilt = 1                   # Vertical rotation
    Roll = 2                   # Rotation around optical axis
    Zoom = 3                   # Optical zoom
    Exposure = 4               # Exposure time
    Iris = 5                   # Iris/aperture setting
    Focus = 6                  # Focus distance
    # Additional properties may be available
```


#### VidProp

Video processing properties (IAMVideoProcAmp interface).

```python
class VidProp(Enum):
    Brightness = 0             # Image brightness
    Contrast = 1               # Image contrast
    Hue = 2                    # Color hue
    Saturation = 3             # Color saturation
    Sharpness = 4              # Image sharpness
    Gamma = 5                  # Gamma correction
    # Additional properties may be available
```


#### ErrorCode

Error codes returned by the underlying DirectShow operations.

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


### Functions

#### Device Management

```python
def list_devices() -> list[Device]:
    """Enumerate all connected UVC devices"""

def is_device_connected(device: Device) -> bool:
    """Check if device is currently connected"""

def find_device_by_name(name: str) -> Optional[Device]:
    """Find device by partial name match (case-insensitive)"""

def get_device_info(device: Device) -> dict[str, Any]:
    """Get comprehensive device information including all properties"""

def reset_device_to_defaults(device: Device) -> dict[str, bool]:
    """Reset all supported properties to factory defaults"""

def open_camera(index: int) -> Camera:
    """Open camera by index (throws exception on error)"""
```


#### Property Access (Direct API)

```python
def get_camera_property_direct(device: Device, prop: CamProp) -> tuple[bool, PropSetting]:
    """Get camera property - returns (success, setting)"""

def get_camera_property_range_direct(device: Device, prop: CamProp) -> tuple[bool, PropRange]:
    """Get camera property range - returns (success, range)"""

# Similar functions exist for video properties:
# get_video_property_direct, get_video_property_range_direct
```


#### Capabilities

```python
def get_device_capabilities(device: Device) -> DeviceCapabilitiesResult:
    """Get device capabilities by device reference"""

def get_device_capabilities_by_index(index: int) -> DeviceCapabilitiesResult:
    """Get device capabilities by device index"""
```


#### Device Monitoring

```python
def register_device_change_callback(callback: Callable[[bool, str], None]) -> None:
    """Register callback for device hotplug events
    
    Args:
        callback: Function called with (added: bool, device_path: str)
    """

def unregister_device_change_callback() -> None:
    """Unregister device change callback"""
```


#### Vendor Properties (Windows-only)

```python
def guid_from_uuid(u: uuid.UUID) -> PyGUID:
    """Convert Python UUID to PyGUID for vendor property access"""

def read_vendor_property(device: Device, guid: PyGUID, prop_id: int) -> tuple[bool, bytes]:
    """Read vendor-specific property
    
    Returns:
        (success, data_bytes)
    """

def write_vendor_property(device: Device, guid: PyGUID, prop_id: int, data: bytes | list[int]) -> bool:
    """Write vendor-specific property
    
    Returns:
        success
    """
```


#### Utility Functions

```python
def cam_prop_to_string(prop: CamProp) -> str:
    """Convert camera property enum to string"""

def vid_prop_to_string(prop: VidProp) -> str:
    """Convert video property enum to string"""

def cam_mode_to_string(mode: CamMode) -> str:
    """Convert camera mode enum to string"""

def error_code_to_string(code: ErrorCode) -> str:
    """Convert error code enum to string"""
```


### Result Types

Result types provide error handling without exceptions for the low-level API.

#### PropSettingResult

```python
class PropSettingResult:
    def is_ok(self) -> bool
    def is_error(self) -> bool
    def value(self) -> PropSetting      # Throws if error
    def error(self) -> CppError         # Throws if ok
```


#### PropRangeResult

```python
class PropRangeResult:
    def is_ok(self) -> bool
    def is_error(self) -> bool  
    def value(self) -> PropRange        # Throws if error
    def error(self) -> CppError         # Throws if ok
```


#### VoidResult

```python
class VoidResult:
    def is_ok(self) -> bool
    def is_error(self) -> bool
    def error(self) -> CppError         # Throws if ok
```


### Exceptions

All exceptions inherit from `DuvcError` and include error codes for programmatic handling.

```python
class DuvcError(Exception):
    error_code: Optional[DuvcErrorCode]
    context: Optional[str]

class DeviceNotFoundError(DuvcError):
    """Device not found or disconnected"""

class DeviceBusyError(DuvcError):  
    """Device is busy or in use by another application"""

class PropertyNotSupportedError(DuvcError):
    """Property not supported by device"""

class InvalidValueError(DuvcError):
    """Property value is out of range or invalid"""

class PermissionDeniedError(DuvcError):
    """Insufficient permissions to access device"""

class SystemError(DuvcError):
    """System or DirectShow error occurred"""

class InvalidArgumentError(DuvcError):
    """Invalid function argument provided"""

class NotImplementedError(DuvcError):
    """Feature not implemented on this platform"""
```


## Examples

### Basic Device Control

```python
import duvc_ctl as duvc

def list_all_devices():
    """Enumerate and display all connected cameras"""
    devices = duvc.list_devices()
    
    print(f"Found {len(devices)} UVC devices:")
    for i, device in enumerate(devices):
        status = "Connected" if duvc.is_device_connected(device) else "Disconnected"
        print(f"  [{i}] {device.name} - {status}")
        
        # Get detailed device information
        info = duvc.get_device_info(device)
        print(f"      Camera properties: {len(info['camera_properties'])}")
        print(f"      Video properties: {len(info['video_properties'])}")

if __name__ == "__main__":
    list_all_devices()
```


### PTZ Operations

```python
import duvc_ctl as duvc
import time

def ptz_demo(device_index: int = 0):
    """Demonstrate PTZ (Pan/Tilt/Zoom) operations"""
    
    try:
        with duvc.open_camera(device_index) as camera:
            print(f"Using camera: {camera.device().name}")
            
            # Get PTZ ranges
            pan_range = camera.get_camera_property_range(duvc.CamProp.Pan)
            tilt_range = camera.get_camera_property_range(duvc.CamProp.Tilt)
            zoom_range = camera.get_camera_property_range(duvc.CamProp.Zoom)
            
            print(f"Pan range: {pan_range.min} to {pan_range.max}")
            print(f"Tilt range: {tilt_range.min} to {tilt_range.max}")
            print(f"Zoom range: {zoom_range.min} to {zoom_range.max}")
            
            # Center camera
            print("Centering camera...")
            camera.set_camera_property(duvc.CamProp.Pan, duvc.PropSetting(0, duvc.CamMode.Manual))
            camera.set_camera_property(duvc.CamProp.Tilt, duvc.PropSetting(0, duvc.CamMode.Manual))
            time.sleep(1)
            
            # Pan left, then right
            print("Panning left...")
            camera.set_camera_property(duvc.CamProp.Pan, duvc.PropSetting(pan_range.min, duvc.CamMode.Manual))
            time.sleep(2)
            
            print("Panning right...")
            camera.set_camera_property(duvc.CamProp.Pan, duvc.PropSetting(pan_range.max, duvc.CamMode.Manual))
            time.sleep(2)
            
            # Return to center
            print("Returning to center...")
            camera.set_camera_property(duvc.CamProp.Pan, duvc.PropSetting(0, duvc.CamMode.Manual))
            
            # Zoom demonstration
            if zoom_range.max > zoom_range.min:
                print("Zooming in...")
                camera.set_camera_property(duvc.CamProp.Zoom, duvc.PropSetting(zoom_range.max, duvc.CamMode.Manual))
                time.sleep(2)
                
                print("Zooming out...")
                camera.set_camera_property(duvc.CamProp.Zoom, duvc.PropSetting(zoom_range.min, duvc.CamMode.Manual))
                
    except duvc.DeviceNotFoundError:
        print(f"Camera {device_index} not found")
    except duvc.DeviceBusyError:
        print(f"Camera {device_index} is busy")
    except duvc.PropertyNotSupportedError as e:
        print(f"PTZ not supported: {e}")

if __name__ == "__main__":
    ptz_demo()
```


### Property Management

```python
import duvc_ctl as duvc

def manage_video_properties():
    """Demonstrate video property management"""
    
    devices = duvc.list_devices()
    if not devices:
        print("No cameras found")
        return
        
    device = devices[^0]
    
    try:
        with duvc.open_camera(0) as camera:
            print(f"Managing properties for: {device.name}")
            
            # Get current video properties
            properties = [
                duvc.VidProp.Brightness,
                duvc.VidProp.Contrast,
                duvc.VidProp.Saturation,
                duvc.VidProp.Hue
            ]
            
            original_settings = {}
            
            for prop in properties:
                try:
                    current = camera.get_video_property(prop)
                    range_info = camera.get_video_property_range(prop)
                    
                    original_settings[prop] = current
                    prop_name = duvc.vid_prop_to_string(prop)
                    
                    print(f"{prop_name}:")
                    print(f"  Current: {current.value} ({'Auto' if current.mode == duvc.CamMode.Auto else 'Manual'})")
                    print(f"  Range: {range_info.min} to {range_info.max} (step: {range_info.step})")
                    print(f"  Default: {range_info.default_val}")
                    
                except duvc.PropertyNotSupportedError:
                    print(f"{duvc.vid_prop_to_string(prop)}: Not supported")
            
            # Adjust brightness
            print("\nAdjusting brightness...")
            brightness_range = camera.get_video_property_range(duvc.VidProp.Brightness)
            mid_brightness = (brightness_range.min + brightness_range.max) // 2
            
            camera.set_video_property(duvc.VidProp.Brightness, 
                                    duvc.PropSetting(mid_brightness, duvc.CamMode.Manual))
            
            new_brightness = camera.get_video_property(duvc.VidProp.Brightness)
            print(f"Brightness set to: {new_brightness.value}")
            
            # Enable auto white balance if available
            try:
                wb_range = camera.get_video_property_range(duvc.VidProp.WhiteBalance)
                camera.set_video_property(duvc.VidProp.WhiteBalance,
                                        duvc.PropSetting(0, duvc.CamMode.Auto))
                print("Auto white balance enabled")
            except duvc.PropertyNotSupportedError:
                print("White balance not supported")
            
            # Restore original settings
            print("\nRestoring original settings...")
            for prop, setting in original_settings.items():
                camera.set_video_property(prop, setting)
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    manage_video_properties()
```


### Device Monitoring

```python
import duvc_ctl as duvc
import time
import threading

class DeviceMonitor:
    """Monitor device hotplug events"""
    
    def __init__(self):
        self.running = False
        self.devices = {}
        
    def device_change_callback(self, added: bool, device_path: str):
        """Handle device change events"""
        action = "added" if added else "removed"
        timestamp = time.strftime("%H:%M:%S")
        
        print(f"[{timestamp}] Device {action}: {device_path}")
        
        if added:
            # Refresh device list to get new device info
            devices = duvc.list_devices()
            for device in devices:
                if device.path == device_path:
                    self.devices[device_path] = device
                    print(f"  Name: {device.name}")
                    break
        else:
            # Remove from our tracking
            if device_path in self.devices:
                device = self.devices.pop(device_path)
                print(f"  Was: {device.name}")
    
    def start_monitoring(self):
        """Start monitoring device changes"""
        print("Starting device monitoring...")
        print("Connect or disconnect UVC cameras to see events")
        print("Press Ctrl+C to stop")
        
        # Register callback
        duvc.register_device_change_callback(self.device_change_callback)
        
        # Initial device scan
        devices = duvc.list_devices()
        print(f"\nInitially found {len(devices)} devices:")
        for device in devices:
            self.devices[device.path] = device
            print(f"  {device.name}")
        
        self.running = True
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopping monitor...")
        finally:
            duvc.unregister_device_change_callback()
            print("Device monitoring stopped")

def monitor_devices():
    """Run device monitoring demo"""
    monitor = DeviceMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    monitor_devices()
```


### Vendor Properties

```python
import duvc_ctl as duvc
import uuid

def vendor_property_demo():
    """Demonstrate vendor-specific property access"""
    
    devices = duvc.list_devices()
    if not devices:
        print("No cameras found")
        return
        
    device = devices[^0]
    print(f"Testing vendor properties on: {device.name}")
    
    # Example: Logitech vendor GUID (this is just an example)
    # Real vendor GUIDs should be obtained from vendor documentation
    vendor_guid = uuid.UUID("{8E14549A-DB61-4309-AFA1-3578E927E935}")
    guid_obj = duvc.guid_from_uuid(vendor_guid)
    
    print(f"Using vendor GUID: {guid_obj.to_string()}")
    
    # Example property ID (vendor-specific)
    property_id = 1
    
    # Try to read a vendor property
    print(f"\nReading vendor property {property_id}...")
    success, data = duvc.read_vendor_property(device, guid_obj, property_id)
    
    if success:
        print(f"Read successful: {len(data)} bytes")
        print(f"Data: {data.hex() if data else 'empty'}")
        
        # Try to write the same data back
        if data:
            print(f"\nWriting data back...")
            write_success = duvc.write_vendor_property(device, guid_obj, property_id, data)
            print(f"Write successful: {write_success}")
        
        # Try writing custom data
        print(f"\nWriting custom data...")
        custom_data = bytes([0x01, 0x02, 0x03, 0x04])
        write_success = duvc.write_vendor_property(device, guid_obj, property_id, custom_data)
        print(f"Custom write successful: {write_success}")
        
        # Verify by reading back
        success2, data2 = duvc.read_vendor_property(device, guid_obj, property_id)
        if success2:
            print(f"Verification read: {data2.hex()}")
            
    else:
        print("Read failed - property may not exist or GUID may be incorrect")
        print("Note: This example uses a placeholder GUID")
        print("Real vendor properties require vendor-specific GUIDs and property IDs")

def discover_vendor_properties(device):
    """Attempt to discover vendor properties (experimental)"""
    
    # Common vendor GUIDs (examples - may not work with your device)
    test_guids = [
        "{8E14549A-DB61-4309-AFA1-3578E927E935}",  # Example GUID
        "{6bdd1fc6-810f-11d0-bec7-08002be2092f}",  # KSCATEGORY_CAPTURE
    ]
    
    print(f"Scanning for vendor properties on {device.name}...")
    
    for guid_str in test_guids:
        try:
            test_uuid = uuid.UUID(guid_str)
            guid_obj = duvc.guid_from_uuid(test_uuid)
            
            print(f"\nTesting GUID: {guid_str}")
            
            # Test property IDs 1-10
            for prop_id in range(1, 11):
                success, data = duvc.read_vendor_property(device, guid_obj, prop_id)
                if success:
                    print(f"  Property {prop_id}: {len(data)} bytes - {data.hex()[:20]}...")
                    
        except Exception as e:
            print(f"Error testing {guid_str}: {e}")

if __name__ == "__main__":
    vendor_property_demo()
```


### Error Handling

```python
import duvc_ctl as duvc

def robust_camera_control():
    """Demonstrate robust error handling"""
    
    def safe_get_property(camera, prop_type, prop):
        """Safely get a property with error handling"""
        try:
            if prop_type == "camera":
                return camera.get_camera_property(prop)
            else:
                return camera.get_video_property(prop)
        except duvc.PropertyNotSupportedError:
            print(f"  {duvc.cam_prop_to_string(prop) if prop_type == 'camera' else duvc.vid_prop_to_string(prop)}: Not supported")
            return None
        except duvc.DuvcError as e:
            print(f"  Error getting property: {e}")
            return None
    
    def safe_set_property(camera, prop_type, prop, setting):
        """Safely set a property with error handling"""
        try:
            if prop_type == "camera":
                result = camera.set_camera_property(prop, setting)
            else:
                result = camera.set_video_property(prop, setting)
            return result
        except duvc.PropertyNotSupportedError:
            print(f"  {duvc.cam_prop_to_string(prop) if prop_type == 'camera' else duvc.vid_prop_to_string(prop)}: Not supported")
            return False
        except duvc.InvalidValueError as e:
            print(f"  Invalid value for property: {e}")
            return False
        except duvc.DeviceBusyError:
            print(f"  Device busy, retrying...")
            return False
        except duvc.DuvcError as e:
            print(f"  Error setting property: {e}")
            return False
    
    # Try to find and use the first available camera
    try:
        devices = duvc.list_devices()
        if not devices:
            raise duvc.DeviceNotFoundError("No cameras found")
            
        print(f"Found {len(devices)} cameras")
        
        # Try each device until we find one that works
        for i, device in enumerate(devices):
            print(f"\nTrying camera {i}: {device.name}")
            
            try:
                # Check if device is connected
                if not duvc.is_device_connected(device):
                    print("  Device not connected, skipping...")
                    continue
                
                # Try to open camera
                camera = duvc.Camera(device)
                if not camera.is_valid():
                    print("  Failed to open camera, skipping...")
                    continue
                
                print("  Camera opened successfully")
                
                # Try to get capabilities
                caps_result = duvc.get_device_capabilities(device)
                if caps_result.is_ok():
                    caps = caps_result.value()
                    cam_props = caps.supported_camera_properties()
                    vid_props = caps.supported_video_properties()
                    
                    print(f"  Supported camera properties: {len(cam_props)}")
                    print(f"  Supported video properties: {len(vid_props)}")
                    
                    # Try camera properties
                    print("  Testing camera properties:")
                    for prop in cam_props[:3]:  # Test first 3 properties
                        current = safe_get_property(camera, "camera", prop)
                        if current:
                            prop_name = duvc.cam_prop_to_string(prop)
                            print(f"    {prop_name}: {current.value} ({'Auto' if current.mode == duvc.CamMode.Auto else 'Manual'})")
                    
                    # Try video properties  
                    print("  Testing video properties:")
                    for prop in vid_props[:3]:  # Test first 3 properties
                        current = safe_get_property(camera, "video", prop)
                        if current:
                            prop_name = duvc.vid_prop_to_string(prop)
                            print(f"    {prop_name}: {current.value} ({'Auto' if current.mode == duvc.CamMode.Auto else 'Manual'})")
                
                # Successfully used this camera, break
                print("  Camera control successful!")
                break
                
            except duvc.DeviceBusyError:
                print("  Camera is busy, trying next...")
                continue
            except duvc.PermissionDeniedError:
                print("  Permission denied, trying next...")
                continue  
            except duvc.SystemError as e:
                print(f"  System error: {e}")
                continue
            except duvc.DuvcError as e:
                print(f"  Camera error: {e}")
                continue
                
        else:
            print("No working cameras found")
            
    except duvc.DeviceNotFoundError as e:
        print(f"Device error: {e}")
    except duvc.NotImplementedError:
        print("This feature is not supported on this platform")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    robust_camera_control()
```


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
