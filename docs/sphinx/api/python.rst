======================
Python API Reference
======================

Complete Python API documentation for duvc-ctl, providing control over USB Video Class (UVC) cameras on Windows through DirectShow APIs.

.. note::
   **Requirements:** Windows 10+, Python 3.8+, UVC-compatible cameras

Overview
========

The ``duvc_ctl`` package provides Python bindings for controlling USB Video Class (UVC) cameras on Windows through DirectShow APIs. The library offers both high-level convenience functions and low-level control for advanced usage.

Features:
- Device enumeration and management  
- Camera control properties (PTZ, exposure, focus, etc.)
- Video processing properties (brightness, contrast, etc.)
- Device monitoring with hotplug detection
- Vendor-specific property access via GUIDs
- Comprehensive error handling with custom exceptions

Installation
============

Install from PyPI:

.. code-block:: bash

   pip install duvc-ctl

Quick Start
===========

Basic Usage Pattern
-------------------

.. code-block:: python

   import duvc_ctl as duvc
   
   # List available cameras
   devices = duvc.list_devices()
   if not devices:
       print("No cameras found")
       return
   
   # Use first camera
   device = devices[0]
   print(f"Using: {device.name}")
   
   # Set brightness to manual mode
   setting = duvc.PropSetting(192, duvc.CamMode.Manual)
   
   # Method 1: Direct API (returns success/failure boolean)
   ok, current = duvc.get_video_property_direct(device, duvc.VidProp.Brightness)
   if ok:
       print(f"Current brightness: {current.value}")
   
   # Method 2: Camera wrapper (throws exceptions on error)
   with duvc.open_camera(0) as camera:
       camera.set_video_property(duvc.VidProp.Brightness, setting)
       verified = camera.get_video_property(duvc.VidProp.Brightness)
       print(f"Brightness set to: {verified.value}")

Error Handling Approaches
-------------------------

.. code-block:: python

   # Approach 1: Exception-based (recommended for application code)
   try:
       camera = duvc.Camera(device)
       zoom = camera.get_camera_property(duvc.CamProp.Zoom)
       print(f"Zoom: {zoom.value}")
   except duvc.PropertyNotSupportedError:
       print("Zoom not supported on this camera")
   except duvc.DeviceNotFoundError:
       print("Camera disconnected")
   
   # Approach 2: Result-based (for performance-critical code)  
   result = camera.get(duvc.CamProp.Zoom)
   if result.is_ok():
       zoom = result.value()
       print(f"Zoom: {zoom.value}")
   else:
       error = result.error()
       print(f"Failed: {error.description()}")

Core Types
==========

Device Class
------------

Represents a UVC camera device.

.. code-block:: python

   class Device:
       name: str    # Human-readable device name  
       path: str    # Unique device path identifier
       
       def is_valid() -> bool:
           """Check if device reference is valid"""

**Usage:**

.. code-block:: python

   devices = duvc.list_devices()
   device = devices[0]
   print(f"Name: {device.name}")
   print(f"Path: {device.path}")
   print(f"Valid: {device.is_valid()}")

PropSetting Class
-----------------

Encapsulates a property value with its control mode.

.. code-block:: python

   class PropSetting:
       value: int         # Property value
       mode: CamMode      # Control mode (Auto/Manual)
       
       def __init__(value: int = 0, mode: CamMode = CamMode.Manual)

**Usage:**

.. code-block:: python

   # Manual setting
   manual_zoom = duvc.PropSetting(300, duvc.CamMode.Manual)
   
   # Auto setting
   auto_exposure = duvc.PropSetting(0, duvc.CamMode.Auto)

PropRange Class
---------------

Defines the valid range and constraints for a property.

.. code-block:: python

   class PropRange:
       min: int           # Minimum value
       max: int           # Maximum value  
       step: int          # Step increment
       default_val: int   # Factory default value
       
       def clamp(value: int) -> int:
           """Clamp value to valid range and step alignment"""

**Usage:**

.. code-block:: python

   ok, range_info = duvc.get_camera_property_range_direct(device, duvc.CamProp.Pan)
   if ok:
       print(f"Pan range: {range_info.min} to {range_info.max}, step: {range_info.step}")
       valid_value = range_info.clamp(150)  # Ensure value is valid

Camera Class
------------

RAII wrapper for device access with automatic resource management.

.. code-block:: python

   class Camera:
       def __init__(device: Device)
       def __init__(device_index: int)
       
       def is_valid() -> bool
       def device() -> Device
       
       # Camera properties
       def get_camera_property(prop: CamProp) -> PropSetting
       def set_camera_property(prop: CamProp, setting: PropSetting) -> bool  
       def get_camera_property_range(prop: CamProp) -> PropRange
       
       # Video properties
       def get_video_property(prop: VidProp) -> PropSetting
       def set_video_property(prop: VidProp, setting: PropSetting) -> bool
       def get_video_property_range(prop: VidProp) -> PropRange
       
       # Result-based API (doesn't throw exceptions)
       def get(prop: CamProp) -> PropSettingResult
       def set(prop: CamProp, setting: PropSetting) -> VoidResult
       def get_range(prop: CamProp) -> PropRangeResult

**Usage:**

.. code-block:: python

   # Method 1: Direct construction
   camera = duvc.Camera(device)
   
   # Method 2: By index
   camera = duvc.Camera(0)
   
   # Method 3: Context manager (recommended)
   with duvc.open_camera(0) as camera:
       zoom = camera.get_camera_property(duvc.CamProp.Zoom)
       print(f"Current zoom: {zoom.value}")

DeviceCapabilities Class
------------------------

Provides detailed information about device supported properties and capabilities.

.. code-block:: python

   class DeviceCapabilities:
       def supports_camera_property(prop: CamProp) -> bool
       def supports_video_property(prop: VidProp) -> bool
       def supported_camera_properties() -> list[CamProp]
       def supported_video_properties() -> list[VidProp] 
       def get_camera_capability(prop: CamProp) -> PropertyCapability
       def get_video_capability(prop: VidProp) -> PropertyCapability
       def device() -> Device
       def is_device_accessible() -> bool
       def refresh() -> None

PropertyCapability Class
------------------------

Detailed capability information for a specific property.

.. code-block:: python

   class PropertyCapability:
       supported: bool        # Property is supported
       range: PropRange       # Valid value range
       current: PropSetting   # Current setting
       
       def supports_auto() -> bool

PyGUID Class (Windows-only)
---------------------------

Wrapper for Windows GUID structures used in vendor property access.

.. code-block:: python

   class PyGUID:
       def __init__(guid_string: str = "")
       def to_string() -> str

Enumerations
============

CamMode Enum
------------

Control mode for camera properties.

.. code-block:: python

   class CamMode(Enum):
       Auto = 1      # Automatic control by camera
       Manual = 2    # Manual control with specified value

CamProp Enum
------------

Camera control properties (IAMCameraControl interface).

.. code-block:: python

   class CamProp(Enum):
       Pan = 0                    # Horizontal rotation
       Tilt = 1                   # Vertical rotation
       Roll = 2                   # Rotation around optical axis
       Zoom = 3                   # Optical zoom
       Exposure = 4               # Exposure time
       Iris = 5                   # Iris/aperture setting
       Focus = 6                  # Focus distance
       ScanMode = 7               # Progressive/interlaced mode
       Privacy = 8                # Privacy shutter
       PanRelative = 9            # Relative pan movement
       TiltRelative = 10          # Relative tilt movement
       RollRelative = 11          # Relative roll movement
       ZoomRelative = 12          # Relative zoom movement
       ExposureRelative = 13      # Relative exposure adjustment
       IrisRelative = 14          # Relative iris adjustment
       FocusRelative = 15         # Relative focus adjustment
       PanTilt = 16               # Combined pan/tilt control
       PanTiltRelative = 17       # Relative pan/tilt movement
       FocusSimple = 18           # Simplified focus control
       DigitalZoom = 19           # Digital zoom level
       DigitalZoomRelative = 20   # Relative digital zoom
       BacklightCompensation = 21 # Backlight compensation
       Lamp = 22                  # Camera lamp/flash control

VidProp Enum
------------

Video processing properties (IAMVideoProcAmp interface).

.. code-block:: python

   class VidProp(Enum):
       Brightness = 0             # Image brightness
       Contrast = 1               # Image contrast
       Hue = 2                    # Color hue
       Saturation = 3             # Color saturation
       Sharpness = 4              # Image sharpness
       Gamma = 5                  # Gamma correction
       ColorEnable = 6            # Color vs. monochrome mode
       WhiteBalance = 7           # White balance adjustment
       BacklightCompensation = 8  # Backlight compensation level
       Gain = 9                   # Sensor gain level

ErrorCode Enum
--------------

Error codes returned by the underlying DirectShow operations.

.. code-block:: python

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

Result Types
============

Low-level API result types for error handling without exceptions.

PropSettingResult Class
-----------------------

.. code-block:: python

   class PropSettingResult:
       def is_ok() -> bool
       def is_error() -> bool
       def value() -> PropSetting      # Throws if error
       def error() -> CppError         # Throws if ok

PropRangeResult Class
---------------------

.. code-block:: python

   class PropRangeResult:
       def is_ok() -> bool
       def is_error() -> bool  
       def value() -> PropRange        # Throws if error
       def error() -> CppError         # Throws if ok

VoidResult Class
----------------

.. code-block:: python

   class VoidResult:
       def is_ok() -> bool
       def is_error() -> bool
       def error() -> CppError         # Throws if ok

CameraResult Class
------------------

.. code-block:: python

   class CameraResult:
       def is_ok() -> bool
       def is_error() -> bool
       def value() -> Camera           # Throws if error
       def error() -> CppError         # Throws if ok

DeviceCapabilitiesResult Class
------------------------------

.. code-block:: python

   class DeviceCapabilitiesResult:
       def is_ok() -> bool
       def is_error() -> bool
       def value() -> DeviceCapabilities  # Throws if error
       def error() -> CppError             # Throws if ok

CppError Class
--------------

.. code-block:: python

   class CppError:
       def code() -> ErrorCode
       def message() -> str
       def description() -> str

Core Functions
==============

Device Management
-----------------

list_devices()
~~~~~~~~~~~~~~

Enumerate all connected UVC devices.

.. code-block:: python

   def list_devices() -> list[Device]

**Returns:** List of all available camera devices

**Usage:**

.. code-block:: python

   devices = duvc.list_devices()
   print(f"Found {len(devices)} cameras")
   for i, device in enumerate(devices):
       print(f"[{i}] {device.name}")

is_device_connected()
~~~~~~~~~~~~~~~~~~~~~

Check if device is currently connected.

.. code-block:: python

   def is_device_connected(device: Device) -> bool

**Parameters:**
- ``device``: Device to check

**Returns:** ``True`` if device is connected and accessible

**Usage:**

.. code-block:: python

   device = devices[0]
   if duvc.is_device_connected(device):
       print("Camera is ready")

open_camera()
~~~~~~~~~~~~~

Open camera by index with context manager support.

.. code-block:: python

   def open_camera(index: int) -> Camera

**Parameters:**
- ``index``: Device index from list_devices()

**Returns:** Camera instance (throws exception on error)

**Usage:**

.. code-block:: python

   with duvc.open_camera(0) as camera:
       setting = camera.get_camera_property(duvc.CamProp.Zoom)
       print(f"Zoom: {setting.value}")


Property Access Functions
-------------------------

Direct API (Boolean Returns)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

get_camera_property_direct()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get camera property with boolean success indicator.

.. code-block:: python

   def get_camera_property_direct(device: Device, prop: CamProp) -> tuple[bool, PropSetting]

**Parameters:**
- ``device``: Target device
- ``prop``: Camera property to query

**Returns:** Tuple of (success, property_setting)

**Usage:**

.. code-block:: python

   ok, setting = duvc.get_camera_property_direct(device, duvc.CamProp.Pan)
   if ok:
       print(f"Pan: {setting.value} ({setting.mode})")

get_camera_property_range_direct()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get camera property range with boolean success indicator.

.. code-block:: python

   def get_camera_property_range_direct(device: Device, prop: CamProp) -> tuple[bool, PropRange]

**Parameters:**
- ``device``: Target device
- ``prop``: Camera property to query

**Returns:** Tuple of (success, property_range)

**Usage:**

.. code-block:: python

   ok, range_info = duvc.get_camera_property_range_direct(device, duvc.CamProp.Zoom)
   if ok:
       print(f"Zoom range: {range_info.min} to {range_info.max}")

get_video_property_direct()
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get video property with boolean success indicator.

.. code-block:: python

   def get_video_property_direct(device: Device, prop: VidProp) -> tuple[bool, PropSetting]

get_video_property_range_direct()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get video property range with boolean success indicator.

.. code-block:: python

   def get_video_property_range_direct(device: Device, prop: VidProp) -> tuple[bool, PropRange]

Device Capabilities
~~~~~~~~~~~~~~~~~~~

get_device_capabilities()
^^^^^^^^^^^^^^^^^^^^^^^^^

Get device capabilities by device reference.

.. code-block:: python

   def get_device_capabilities(device: Device) -> DeviceCapabilitiesResult

**Parameters:**
- ``device``: Target device

**Returns:** Result containing device capabilities or error

**Usage:**

.. code-block:: python

   result = duvc.get_device_capabilities(device)
   if result.is_ok():
       caps = result.value()
       print(f"Camera properties: {caps.supported_camera_properties()}")
       print(f"Video properties: {caps.supported_video_properties()}")

get_device_capabilities_by_index()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get device capabilities by device index.

.. code-block:: python

   def get_device_capabilities_by_index(index: int) -> DeviceCapabilitiesResult

Device Monitoring
-----------------

register_device_change_callback()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Register callback for device hotplug events.

.. code-block:: python

   def register_device_change_callback(callback: Callable[[bool, str], None]) -> None

**Parameters:**
- ``callback``: Function called with (added: bool, device_path: str)

**Usage:**

.. code-block:: python

   def on_device_change(added, device_path):
       action = "CONNECTED" if added else "DISCONNECTED"
       print(f"Camera {action}: {device_path}")
   
   duvc.register_device_change_callback(on_device_change)

unregister_device_change_callback()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Unregister device change callback.

.. code-block:: python

   def unregister_device_change_callback() -> None

Vendor Properties
-----------------

Windows-specific GUID-based vendor property access.

guid_from_uuid()
~~~~~~~~~~~~~~~~

Convert Python UUID to PyGUID for vendor property access.

.. code-block:: python

   def guid_from_uuid(u: uuid.UUID) -> PyGUID

**Parameters:**
- ``u``: Python uuid.UUID object

**Returns:** PyGUID object for use with vendor functions

**Usage:**

.. code-block:: python

   import uuid
   vendor_uuid = uuid.UUID("{82066163-7BD0-43EF-8A6F-5B8905C9A64C}")
   vendor_guid = duvc.guid_from_uuid(vendor_uuid)

read_vendor_property()
~~~~~~~~~~~~~~~~~~~~~~

Read vendor-specific property.

.. code-block:: python

   def read_vendor_property(device: Device, guid: PyGUID, prop_id: int) -> tuple[bool, bytes]

**Parameters:**
- ``device``: Target device
- ``guid``: Property set GUID
- ``prop_id``: Property ID within set

**Returns:** Tuple of (success, data_bytes)

**Usage:**

.. code-block:: python

   success, data = duvc.read_vendor_property(device, vendor_guid, 1)
   if success:
       print(f"Vendor data: {data.hex()}")

write_vendor_property()
~~~~~~~~~~~~~~~~~~~~~~~

Write vendor-specific property.

.. code-block:: python

   def write_vendor_property(device: Device, guid: PyGUID, prop_id: int, data: bytes | list[int]) -> bool

**Parameters:**
- ``device``: Target device
- ``guid``: Property set GUID
- ``prop_id``: Property ID within set
- ``data``: Property data as bytes or list of integers

**Returns:** ``True`` if successful

**Usage:**

.. code-block:: python

   # Write 4-byte integer value 1
   data = (1).to_bytes(4, byteorder='little')
   success = duvc.write_vendor_property(device, vendor_guid, 1, data)

Utility Functions
-----------------

String Conversion
~~~~~~~~~~~~~~~~~

cam_prop_to_string()
^^^^^^^^^^^^^^^^^^^^

Convert camera property enum to string.

.. code-block:: python

   def cam_prop_to_string(prop: CamProp) -> str

vid_prop_to_string()
^^^^^^^^^^^^^^^^^^^^

Convert video property enum to string.

.. code-block:: python

   def vid_prop_to_string(prop: VidProp) -> str

cam_mode_to_string()
^^^^^^^^^^^^^^^^^^^^

Convert camera mode enum to string.

.. code-block:: python

   def cam_mode_to_string(mode: CamMode) -> str

error_code_to_string()
^^^^^^^^^^^^^^^^^^^^^^

Convert error code enum to string.

.. code-block:: python

   def error_code_to_string(code: ErrorCode) -> str

Convenience Functions
~~~~~~~~~~~~~~~~~~~~~

find_device_by_name()
^^^^^^^^^^^^^^^^^^^^^

Find device by partial name match (case-insensitive).

.. code-block:: python

   def find_device_by_name(name: str) -> Optional[Device]

**Parameters:**
- ``name``: Partial device name to search for

**Returns:** First matching device or ``None``

**Usage:**

.. code-block:: python

   camera = duvc.find_device_by_name("Logitech")
   if camera:
       print(f"Found: {camera.name}")

get_device_info()
^^^^^^^^^^^^^^^^^

Get comprehensive device information including all properties.

.. code-block:: python

   def get_device_info(device: Device) -> dict[str, Any]

**Parameters:**
- ``device``: Target device

**Returns:** Dictionary with device information and all property values/ranges

**Usage:**

.. code-block:: python

   info = duvc.get_device_info(device)
   print(f"Connected: {info['connected']}")
   for prop_name, prop_info in info['camera_properties'].items():
       if prop_info.get('supported', True):
           current = prop_info['current']
           print(f"{prop_name}: {current['value']} ({current['mode']})")

reset_device_to_defaults()
^^^^^^^^^^^^^^^^^^^^^^^^^^

Reset all supported properties of a device to their defaults.

.. code-block:: python

   def reset_device_to_defaults(device: Device) -> dict[str, bool]

**Parameters:**
- ``device``: Target device

**Returns:** Dictionary mapping property names to success status

**Usage:**

.. code-block:: python

   results = duvc.reset_device_to_defaults(device)
   for prop_name, success in results.items():
       status = "OK" if success else "FAILED"
       print(f"{prop_name}: {status}")

Exception Handling
==================

All exceptions inherit from ``DuvcError`` and include error codes for programmatic handling.

Exception Hierarchy
-------------------

.. code-block:: python

   DuvcError
   ├── DeviceNotFoundError
   ├── DeviceBusyError
   ├── PropertyNotSupportedError
   ├── InvalidValueError
   ├── PermissionDeniedError
   ├── SystemError
   ├── InvalidArgumentError
   └── NotImplementedError

Base Exception
~~~~~~~~~~~~~~

.. code-block:: python

   class DuvcError(Exception):
       error_code: Optional[DuvcErrorCode]
       context: Optional[str]
       
       def __init__(message: str, error_code: Optional[DuvcErrorCode] = None,
                   context: Optional[str] = None)

Specific Exceptions
~~~~~~~~~~~~~~~~~~~

DeviceNotFoundError
^^^^^^^^^^^^^^^^^^^

Raised when a camera device is not found or has been disconnected.

**Typical causes:**
- Device not physically connected
- Device not recognized by system
- Driver issues

DeviceBusyError
^^^^^^^^^^^^^^^

Raised when a camera device is busy or in use by another application.

**Typical causes:**
- Another application using the camera
- Device locked by another process

PropertyNotSupportedError
^^^^^^^^^^^^^^^^^^^^^^^^^

Raised when trying to access a property not supported by the device.

**Typical causes:**
- Camera doesn't support the requested feature
- Property not available in current mode
- Driver limitations

InvalidValueError
^^^^^^^^^^^^^^^^^

Raised when trying to set a property to an invalid value.

**Typical causes:**
- Value outside supported range
- Value not aligned with step size
- Incorrect value type

PermissionDeniedError
^^^^^^^^^^^^^^^^^^^^^

Raised when there are insufficient permissions to access the device.

**Typical causes:**
- Camera privacy settings blocking access
- Application doesn't have required privileges
- System security policies preventing access

SystemError
^^^^^^^^^^^

Raised when a system or platform-specific error occurs.

**Typical causes:**
- DirectShow/COM errors
- Driver issues
- System resource problems

InvalidArgumentError
^^^^^^^^^^^^^^^^^^^^

Raised when an invalid argument is passed to a function.

**Typical causes:**
- Null pointer or invalid object
- Invalid enum value
- Programming error

NotImplementedError
^^^^^^^^^^^^^^^^^^^

Raised when a feature is not implemented on the current platform.

**Typical causes:**
- Feature is Windows-only but running on another platform
- Functionality not yet implemented
- Platform-specific limitations

Usage Examples
==============

Basic Device Control
--------------------

.. code-block:: python

   import duvc_ctl as duvc
   
   # Enumerate and select device
   devices = duvc.list_devices()
   if not devices:
       print("No cameras found")
       return
   
   device = devices[0]
   print(f"Using: {device.name}")
   
   # Check device capabilities
   caps_result = duvc.get_device_capabilities(device)
   if caps_result.is_ok():
       caps = caps_result.value()
       if caps.supports_camera_property(duvc.CamProp.Zoom):
           print("Camera supports zoom")
   
   # Set zoom to 2x
   zoom_setting = duvc.PropSetting(200, duvc.CamMode.Manual)
   with duvc.open_camera(0) as camera:
       camera.set_camera_property(duvc.CamProp.Zoom, zoom_setting)
       
       # Verify the setting
       current_zoom = camera.get_camera_property(duvc.CamProp.Zoom)
       print(f"Zoom set to: {current_zoom.value}")

Property Management
-------------------

.. code-block:: python

   def configure_camera_preset(device_index, preset_name):
       """Apply predefined camera configuration"""
       
       presets = {
           "indoor": {
               duvc.VidProp.Brightness: (128, duvc.CamMode.Manual),
               duvc.VidProp.Contrast: (120, duvc.CamMode.Manual),
               duvc.VidProp.WhiteBalance: (0, duvc.CamMode.Auto),
               duvc.CamProp.Exposure: (0, duvc.CamMode.Auto),
           },
           "outdoor": {
               duvc.VidProp.Brightness: (100, duvc.CamMode.Manual),
               duvc.VidProp.Contrast: (140, duvc.CamMode.Manual),
               duvc.VidProp.WhiteBalance: (4000, duvc.CamMode.Manual),
               duvc.CamProp.Exposure: (-6, duvc.CamMode.Manual),
           }
       }
       
       if preset_name not in presets:
           raise ValueError(f"Unknown preset: {preset_name}")
       
       preset = presets[preset_name]
       results = {}
       
       try:
           with duvc.open_camera(device_index) as camera:
               for prop, (value, mode) in preset.items():
                   setting = duvc.PropSetting(value, mode)
                   try:
                       if isinstance(prop, duvc.CamProp):
                           success = camera.set_camera_property(prop, setting)
                       else:
                           success = camera.set_video_property(prop, setting)
                       results[prop] = success
                   except duvc.PropertyNotSupportedError:
                       results[prop] = False
                       
       except duvc.DuvcError as e:
           print(f"Camera configuration failed: {e}")
           return {}
       
       return results

Device Monitoring
-----------------

.. code-block:: python

   import duvc_ctl as duvc
   import time
   from datetime import datetime
   
   def device_change_handler(added, device_path):
       timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       action = "CONNECTED" if added else "DISCONNECTED"
       print(f"[{timestamp}] Camera {action}: {device_path}")
   
   def monitor_cameras(duration=30):
       """Monitor camera changes for specified duration"""
       print(f"Monitoring camera changes for {duration} seconds...")
       print("Press Ctrl+C to stop early.")
       
       duvc.register_device_change_callback(device_change_handler)
       
       try:
           time.sleep(duration)
       except KeyboardInterrupt:
           print("\nMonitoring interrupted by user")
       finally:
           duvc.unregister_device_change_callback()
           print("Monitoring stopped")
   
   # Usage
   monitor_cameras(60)

Vendor Property Access
----------------------

.. code-block:: python

   import duvc_ctl as duvc
   import uuid
   
   def access_logitech_properties(device):
       """Example of accessing Logitech-specific properties"""
       
       # Logitech vendor property set GUID
       logitech_guid_str = "{82066163-7BD0-43EF-8A6F-5B8905C9A64C}"
       logitech_uuid = uuid.UUID(logitech_guid_str)
       logitech_guid = duvc.guid_from_uuid(logitech_uuid)
       
       # Property IDs (example values)
       RIGHTLIGHT_PROPERTY = 1
       FACE_TRACKING_PROPERTY = 3
       
       try:
           # Read RightLight setting
           success, data = duvc.read_vendor_property(device, logitech_guid, RIGHTLIGHT_PROPERTY)
           if success and len(data) >= 4:
               # Interpret as 32-bit integer (little-endian)
               rightlight_value = int.from_bytes(data[:4], byteorder='little')
               print(f"RightLight setting: {rightlight_value}")
           
           # Enable face tracking
           face_tracking_data = (1).to_bytes(4, byteorder='little')  # Enable = 1
           success = duvc.write_vendor_property(device, logitech_guid, FACE_TRACKING_PROPERTY, face_tracking_data)
           if success:
               print("Face tracking enabled")
           
       except Exception as e:
           print(f"Vendor property access failed: {e}")

Error Handling Best Practices
-----------------------------

.. code-block:: python

   import duvc_ctl as duvc
   import time
   
   def robust_camera_operation(device_index):
       """Robust camera control with comprehensive error handling"""
       
       max_retries = 3
       
       for attempt in range(max_retries):
           try:
               devices = duvc.list_devices()
               if device_index >= len(devices):
                   raise duvc.DeviceNotFoundError(f"Device index {device_index} not available")
               
               device = devices[device_index]
               
               if not duvc.is_device_connected(device):
                   raise duvc.DeviceNotFoundError("Device not connected")
               
               with duvc.open_camera(device_index) as camera:
                   # Perform camera operations
                   zoom = camera.get_camera_property(duvc.CamProp.Zoom)
                   print(f"Current zoom: {zoom.value}")
                   
                   # Set new zoom value with range validation
                   zoom_range = camera.get_camera_property_range(duvc.CamProp.Zoom)
                   target_zoom = zoom_range.clamp(300)  # Ensure valid value
                   
                   zoom_setting = duvc.PropSetting(target_zoom, duvc.CamMode.Manual)
                   camera.set_camera_property(duvc.CamProp.Zoom, zoom_setting)
                   
                   print("Camera operation completed successfully")
                   return True
                   
           except duvc.DeviceNotFoundError:
               print(f"Device not found (attempt {attempt + 1}/{max_retries})")
           except duvc.DeviceBusyError:
               print(f"Device busy (attempt {attempt + 1}/{max_retries})")
           except duvc.PropertyNotSupportedError as e:
               print(f"Property not supported: {e}")
               return False  # Don't retry for unsupported properties
           except duvc.InvalidValueError as e:
               print(f"Invalid value: {e}")
               return False  # Don't retry for invalid values
           except Exception as e:
               print(f"Unexpected error: {e} (attempt {attempt + 1}/{max_retries})")
           
           if attempt < max_retries - 1:
               print("Retrying in 1 second...")
               time.sleep(1)
       
       print("All retry attempts failed")
       return False

Building from Source
====================

Requirements
------------

- Windows 10+ (x64)
- Python 3.8+
- Visual Studio 2019+ or compatible C++ compiler
- CMake 3.16+

Development Setup
-----------------

.. code-block:: bash

   # Clone repository
   git clone https://github.com/allanhanan/duvc-ctl.git
   cd duvc-ctl/bindings/python
   
   # Create virtual environment
   python -m venv venv
   venv\Scripts\activate
   
   # Install build dependencies
   pip install -r requirements-dev.txt
   
   # Build in development mode
   pip install -e . -v

Testing Installation
--------------------

.. code-block:: python

   import duvc_ctl
   print(f"duvc-ctl version: {duvc_ctl.__version__}")
   
   # Basic functionality test
   try:
       devices = duvc_ctl.list_devices()
       print(f"Found {len(devices)} cameras")
       if devices:
           print(f"First camera: {devices[0].name}")
   except Exception as e:
       print(f"Error: {e}")

Troubleshooting
===============

Common Issues
-------------

Import Errors
~~~~~~~~~~~~~

**Problem:** ``ImportError: Could not import C++ extension module``

**Solutions:**

1. Verify Windows platform (library is Windows-only)
2. Check Python version (3.8+ required)
3. Reinstall: ``pip install --force-reinstall duvc-ctl -v``
4. Ensure Visual C++ Redistributable is installed

**Problem:** ``DLL load failed while importing _duvc_ctl``

**Solutions:**

1. Install Visual C++ Redistributable 2019+
2. Check for conflicting DLL versions
3. Try running from different directory
4. Verify wheel compatibility with Python version

Device Access Issues
~~~~~~~~~~~~~~~~~~~~

**Problem:** ``DeviceNotFoundError`` or empty device list

**Solutions:**

1. Check camera recognition in Device Manager
2. Ensure camera isn't used by other applications
3. Try running as Administrator

**Problem:** ``DeviceBusyError`` when accessing camera

**Solutions:**

1. Close other camera applications
2. Restart camera application
3. Check for background camera processes

Property Access Issues
~~~~~~~~~~~~~~~~~~~~~~

**Problem:** ``PropertyNotSupportedError`` for basic properties

**Solutions:**

1. Verify camera supports UVC standard
2. Check property name spelling and case
3. Try different property domains (camera vs video)
4. Use ``get_device_capabilities()`` to check supported properties

Permission Issues
~~~~~~~~~~~~~~~~~

**Problem:** ``PermissionDeniedError`` when accessing camera

**Solutions:**

1. Check Windows camera privacy settings
2. Run application as Administrator
3. Verify camera permissions in Windows Settings > Privacy & Security > Camera
4. Check antivirus blocking camera access

Performance Tips
----------------

1. **Use Camera wrapper** for multiple operations on same device
2. **Cache device references** rather than calling ``list_devices()`` repeatedly  
3. **Use direct API functions** for performance-critical code
4. **Batch property changes** when possible
5. **Avoid polling** device status too frequently

Platform Notes
--------------

- Library requires Windows 10+ with DirectShow support
- Tested on Windows 10/11 x64 with Python 3.8-3.12
- UVC cameras must be recognized by Windows (check Device Manager)
- Some vendor-specific features may require additional drivers
- Camera privacy settings in Windows can block access

See Also
========

- C++ API Reference
- C API Reference  
- CLI Documentation
- Build Instructions
