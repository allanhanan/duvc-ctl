import duvc_ctl as duvc

# List all connected cameras
devices = duvc.list_devices()
print(f"Found {len(devices)} cameras")

if devices:
    device = devices[0]  # Get first camera
    print(f"Camera: {device.name}")
    
    # Set zoom to 2x with manual control
    zoom_setting = duvc.PropSetting(200, duvc.CamMode.Manual)
    success = duvc.set(device, duvc.CamProp.Zoom, zoom_setting)
    print(f"Set zoom successful: {success}")
    
    # Auto-adjust brightness
    brightness = duvc.PropSetting(0, duvc.CamMode.Auto)
    success = duvc.set(device, duvc.VidProp.Brightness, brightness)
    print(f"Set brightness successful: {success}")
    
    # Get property range example
    range_info = duvc.PropRange()
    if duvc.get_range(device, duvc.CamProp.Zoom, range_info):
        print(f"Zoom range: {range_info.min} to {range_info.max}, step: {range_info.step}")
    
    # Test vendor property (example with a dummy GUID - replace with real one)
    try:
        from uuid import UUID
        dummy_guid = UUID('{00000000-0000-0000-0000-000000000000}')
        data = [1, 2, 3]  # Example data
        success = duvc.set_vendor_property(device, dummy_guid, 1, data)
        print(f"Set vendor property successful: {success}")
    except Exception as e:
        print(f"Vendor property test failed: {e}")
else:
    print("No cameras found - connect a USB camera and try again.")
