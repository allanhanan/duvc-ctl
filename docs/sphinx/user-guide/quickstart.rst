==========
Quickstart
==========

This guide will get you started with duvc-ctl for Python development on Windows. The library provides native DirectShow UVC camera control through a simple Python API.

.. note::
   **Requirements:** Windows 10+, Python 3.8+, UVC-compatible cameras

Installation
============

Install from PyPI:

.. code-block:: bash

   pip install duvc-ctl

The package includes pre-built wheels for Windows x64 with all dependencies bundled.

Basic Usage
===========

Import and Device Discovery
---------------------------

.. code-block:: python

   import duvc_ctl as duvc
   
   # List all connected cameras
   devices = duvc.list_devices()
   print(f"Found {len(devices)} cameras")
   
   if devices:
       device = devices[0]
       print(f"Using: {device.name}")
       print(f"Path: {device.path}")
       print(f"Connected: {duvc.is_device_connected(device)}")

Camera Property Control
-----------------------

The library provides two approaches for property control: direct functions and Camera wrapper class.

Direct API Approach
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get camera property with success indicator
   success, setting = duvc.get_camera_property_direct(device, duvc.CamProp.Zoom)
   if success:
       print(f"Current zoom: {setting.value} ({setting.mode})")
   
   # Get property range
   success, range_info = duvc.get_camera_property_range_direct(device, duvc.CamProp.Zoom)
   if success:
       print(f"Zoom range: {range_info.min} to {range_info.max}")
       
       # Set zoom to middle of range
       mid_zoom = (range_info.min + range_info.max) // 2
       new_setting = duvc.PropSetting(mid_zoom, duvc.CamMode.Manual)
       # Direct setting requires device-specific functions

Camera Wrapper Approach (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Using Camera wrapper with automatic resource management
   with duvc.open_camera(0) as camera:  # Open first camera
       # Get current zoom
       zoom = camera.get_camera_property(duvc.CamProp.Zoom)
       print(f"Current zoom: {zoom.value}")
       
       # Get zoom range for validation
       zoom_range = camera.get_camera_property_range(duvc.CamProp.Zoom)
       print(f"Range: {zoom_range.min}-{zoom_range.max}, step: {zoom_range.step}")
       
       # Set zoom to 2x (value depends on camera)
       zoom_setting = duvc.PropSetting(200, duvc.CamMode.Manual)
       camera.set_camera_property(duvc.CamProp.Zoom, zoom_setting)
       
       # Verify the change
       new_zoom = camera.get_camera_property(duvc.CamProp.Zoom)
       print(f"Zoom set to: {new_zoom.value}")

Video Processing Properties
---------------------------

Control image processing properties like brightness, contrast, and white balance:

.. code-block:: python

   with duvc.open_camera(0) as camera:
       # Auto white balance
       wb_setting = duvc.PropSetting(0, duvc.CamMode.Auto)
       camera.set_video_property(duvc.VidProp.WhiteBalance, wb_setting)
       
       # Manual brightness
       brightness = duvc.PropSetting(128, duvc.CamMode.Manual)
       camera.set_video_property(duvc.VidProp.Brightness, brightness)
       
       # Check current settings
       current_wb = camera.get_video_property(duvc.VidProp.WhiteBalance)
       current_brightness = camera.get_video_property(duvc.VidProp.Brightness)
       
       print(f"White balance: {current_wb.value} ({current_wb.mode})")
       print(f"Brightness: {current_brightness.value} ({current_brightness.mode})")

PTZ Camera Control
==================

For cameras with Pan/Tilt/Zoom capabilities:

.. code-block:: python

   def control_ptz_camera(device_index=0):
       with duvc.open_camera(device_index) as camera:
           # Center the camera
           center_setting = duvc.PropSetting(0, duvc.CamMode.Manual)
           
           try:
               camera.set_camera_property(duvc.CamProp.Pan, center_setting)
               camera.set_camera_property(duvc.CamProp.Tilt, center_setting)
               print("Camera centered")
           except duvc.PropertyNotSupportedError:
               print("PTZ not supported on this camera")
           
           # Set zoom level
           try:
               zoom_range = camera.get_camera_property_range(duvc.CamProp.Zoom)
               # Set to 50% of zoom range
               zoom_value = zoom_range.min + (zoom_range.max - zoom_range.min) // 2
               zoom_setting = duvc.PropSetting(zoom_value, duvc.CamMode.Manual)
               camera.set_camera_property(duvc.CamProp.Zoom, zoom_setting)
               print(f"Zoom set to: {zoom_value}")
           except duvc.PropertyNotSupportedError:
               print("Zoom not supported on this camera")

   control_ptz_camera()

Device Capabilities
===================

Check what properties your camera supports:

.. code-block:: python

   def show_camera_capabilities(device):
       caps_result = duvc.get_device_capabilities(device)
       if caps_result.is_ok():
           caps = caps_result.value()
           
           print("Supported Camera Properties:")
           for prop in caps.supported_camera_properties():
               prop_name = duvc.cam_prop_to_string(prop)
               print(f"  - {prop_name}")
           
           print("\nSupported Video Properties:")  
           for prop in caps.supported_video_properties():
               prop_name = duvc.vid_prop_to_string(prop)
               print(f"  - {prop_name}")
           
           # Get detailed capability info
           if caps.supports_camera_property(duvc.CamProp.Pan):
               pan_cap = caps.get_camera_capability(duvc.CamProp.Pan)
               print(f"\nPan capability:")
               print(f"  Range: {pan_cap.range.min} to {pan_cap.range.max}")
               print(f"  Current: {pan_cap.current.value}")
               print(f"  Supports auto: {pan_cap.supports_auto()}")

   devices = duvc.list_devices()
   if devices:
       show_camera_capabilities(devices[0])

Error Handling
==============

Exception-Based Handling
-------------------------

The Camera wrapper throws exceptions for errors:

.. code-block:: python

   try:
       with duvc.open_camera(0) as camera:
           # This will raise PropertyNotSupportedError if not supported
           pan = camera.get_camera_property(duvc.CamProp.Pan)
           print(f"Pan: {pan.value}")
           
   except duvc.DeviceNotFoundError:
       print("No camera found or camera disconnected")
   except duvc.PropertyNotSupportedError:
       print("Pan property not supported by this camera")
   except duvc.InvalidValueError:
       print("Invalid value provided for property")
   except duvc.DuvcError as e:
       print(f"Camera error: {e}")

Result-Based Handling
---------------------

For performance-critical code, use the Result-based API:

.. code-block:: python

   with duvc.open_camera(0) as camera:
       # Result-based API doesn't throw exceptions
       result = camera.get(duvc.CamProp.Pan)
       if result.is_ok():
           setting = result.value()
           print(f"Pan: {setting.value}")
       else:
           error = result.error()
           print(f"Failed to get pan: {error.description()}")

Device Monitoring
=================

Monitor camera connect/disconnect events:

.. code-block:: python

   def device_change_handler(added, device_path):
       action = "CONNECTED" if added else "DISCONNECTED"
       print(f"Camera {action}: {device_path}")

   # Register for device change notifications
   duvc.register_device_change_callback(device_change_handler)
   
   # Your application runs here
   import time
   try:
       print("Monitoring for device changes (30 seconds)...")
       time.sleep(30)
   finally:
       # Always unregister when done
       duvc.unregister_device_change_callback()

Vendor-Specific Properties
==========================

Access manufacturer-specific features using GUIDs:

.. code-block:: python

   import uuid
   
   def access_vendor_properties(device):
       # Example: Logitech property set GUID
       vendor_uuid = uuid.UUID("{82066163-7BD0-43EF-8A6F-5B8905C9A64C}")
       vendor_guid = duvc.guid_from_uuid(vendor_uuid)
       
       # Read vendor property (property ID 1)
       success, data = duvc.read_vendor_property(device, vendor_guid, 1)
       if success:
           print(f"Vendor property data: {data.hex()}")
       
       # Write vendor property  
       new_data = (1).to_bytes(4, byteorder='little')  # Enable feature
       success = duvc.write_vendor_property(device, vendor_guid, 1, new_data)
       if success:
           print("Vendor property updated")

   devices = duvc.list_devices() 
   if devices:
       access_vendor_properties(devices[0])

Convenience Functions
=====================

The library provides several convenience functions:

.. code-block:: python

   # Find camera by name (partial, case-insensitive)
   camera = duvc.find_device_by_name("Logitech")
   if camera:
       print(f"Found: {camera.name}")
   
   # Get comprehensive device information
   info = duvc.get_device_info(camera)
   print(f"Connected: {info['connected']}")
   print("Camera properties:", list(info['camera_properties'].keys()))
   print("Video properties:", list(info['video_properties'].keys()))
   
   # Reset all properties to defaults
   results = duvc.reset_device_to_defaults(camera)
   for prop_name, success in results.items():
       status = "OK" if success else "FAILED"
       print(f"{prop_name}: {status}")
   

Property Validation
===================

Always validate property values using ranges:

.. code-block:: python

   def safe_property_setting(camera, prop, target_value):
       try:
           # Get valid range first
           prop_range = camera.get_camera_property_range(prop)
           
           # Clamp value to valid range and step alignment
           safe_value = prop_range.clamp(target_value)
           if safe_value != target_value:
               print(f"Value adjusted from {target_value} to {safe_value}")
           
           # Set the property
           setting = duvc.PropSetting(safe_value, duvc.CamMode.Manual)
           camera.set_camera_property(prop, setting)
           
           return True
           
       except duvc.PropertyNotSupportedError:
           print(f"Property {duvc.cam_prop_to_string(prop)} not supported")
           return False

   # Example usage
   with duvc.open_camera(0) as camera:
       safe_property_setting(camera, duvc.CamProp.Zoom, 500)  # May be clamped

Complete Example
================

Here's a complete example demonstrating multiple features:

.. code-block:: python

   import duvc_ctl as duvc
   
   def camera_control_demo():
       # List available cameras
       devices = duvc.list_devices()
       if not devices:
           print("No cameras found")
           return
           
       print(f"Found {len(devices)} camera(s)")
       device = devices[0]
       print(f"Using: {device.name}")
       
       # Check device capabilities
       caps_result = duvc.get_device_capabilities(device) 
       if not caps_result.is_ok():
           print("Failed to get device capabilities")
           return
           
       caps = caps_result.value()
       print(f"Supports {len(caps.supported_camera_properties())} camera properties")
       print(f"Supports {len(caps.supported_video_properties())} video properties")
       
       # Control the camera
       try:
           with duvc.open_camera(0) as camera:
               # Set up video processing
               if caps.supports_video_property(duvc.VidProp.Brightness):
                   brightness = duvc.PropSetting(150, duvc.CamMode.Manual)
                   camera.set_video_property(duvc.VidProp.Brightness, brightness)
                   print("Brightness set to 150")
               
               if caps.supports_video_property(duvc.VidProp.WhiteBalance):
                   wb = duvc.PropSetting(0, duvc.CamMode.Auto) 
                   camera.set_video_property(duvc.VidProp.WhiteBalance, wb)
                   print("White balance set to auto")
               
               # PTZ control if supported
               if caps.supports_camera_property(duvc.CamProp.Pan):
                   center = duvc.PropSetting(0, duvc.CamMode.Manual)
                   camera.set_camera_property(duvc.CamProp.Pan, center)
                   camera.set_camera_property(duvc.CamProp.Tilt, center)
                   print("Camera centered")
               
               # Show final settings
               print("\nFinal settings:")
               for prop in caps.supported_video_properties():
                   try:
                       setting = camera.get_video_property(prop)
                       prop_name = duvc.vid_prop_to_string(prop)
                       mode_name = duvc.cam_mode_to_string(setting.mode)
                       print(f"  {prop_name}: {setting.value} ({mode_name})")
                   except duvc.PropertyNotSupportedError:
                       pass
                       
       except duvc.DuvcError as e:
           print(f"Camera control error: {e}")
   
   if __name__ == "__main__":
       camera_control_demo()

Next Steps
==========

- Review the :doc:`../api-reference/python` for complete API documentation
- Check out :doc:`../examples/python-examples` for more usage patterns  
- See :doc:`../troubleshooting` for common issues and solutions
- Explore vendor-specific features for your camera model
