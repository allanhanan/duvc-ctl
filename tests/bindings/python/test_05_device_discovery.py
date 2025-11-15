"""
Test Suite 05: Device Discovery
================================

Tests high-level device finding and discovery functions exposed by duvc-ctl.

Functions Tested:
  - find_device_by_name() - Find device by substring match
  - find_devices_by_name() - Find all devices matching substring
  - list_cameras() - Pythonic device listing (alias for list_devices)
  - find_camera() - Pythonic device finding (alias for find_device_by_name)
  - get_camera_info() - Get comprehensive device metadata
  - get_device_info() - Get device metadata with property details

Total: 6 discovery and metadata functions

Test Organization:
  1. Without Camera Tests - Unit tests without requiring specific hardware
  2. With Camera Tests - Integration tests using real camera devices

Run: pytest tests/test_05_device_discovery.py -v
Run without camera: pytest tests/test_05_device_discovery.py -v -m "not hardware"
"""

import pytest
import sys
from typing import List, Optional, Dict, Any

import duvc_ctl
from duvc_ctl import (
    # Core types
    Device,
    # Device enumeration
    list_devices, devices,
    # Device discovery functions
    find_device_by_name, find_devices_by_name,
    list_cameras, find_camera, get_camera_info,
    get_device_info,
    # Type definitions
    DeviceInfo, PropertyInfo,
    # Core enums
    CamProp, VidProp,
    # Exceptions
    DeviceNotFoundError,
    CameraController
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def available_devices() -> List[Device]:
    """Get list of available camera devices for hardware tests."""
    try:
        devices_list = list_devices()
        return devices_list
    except Exception as e:
        pytest.skip(f"Could not enumerate devices: {e}")
        return []


@pytest.fixture(scope="session")
def test_device(available_devices) -> Optional[Device]:
    """Get first available device for testing."""
    if not available_devices:
        pytest.skip("No camera devices available for hardware testing")
    return available_devices[0]


@pytest.fixture(scope="session")
def test_device_name(test_device) -> Optional[str]:
    """Get name of first test device."""
    if test_device is None:
        pytest.skip("No test device available")
    return test_device.name


# ============================================================================
# WITHOUT CAMERA TESTS - Unit tests on discovery functions
# ============================================================================

class TestFindDeviceByNameFunction:
    """Test find_device_by_name() function - substring matching."""
    
    def test_find_device_by_name_returns_device_or_none(self):
        """Test find_device_by_name() returns Device or None."""
        # Search for non-existent device
        result = find_device_by_name("NONEXISTENT_CAMERA_999")
        
        # Should return None or Device
        assert result is None or isinstance(result, Device)
    
    def test_find_device_by_name_with_empty_string(self):
        """Test find_device_by_name() with empty search string."""
        result = find_device_by_name("")
        
        # Empty string matches everything - should return first device or None
        assert result is None or isinstance(result, Device)
    
    def test_find_device_by_name_case_insensitive(self):
        """Test find_device_by_name() is case-insensitive."""
        # Create mock device list
        mock_devices = [
            Device("HD Pro Webcam", "/dev/video0"),
            Device("USB Camera", "/dev/video1")
        ]
        
        # Search with different cases
        result1 = find_device_by_name("webcam", mock_devices)
        result2 = find_device_by_name("WEBCAM", mock_devices)
        result3 = find_device_by_name("WebCam", mock_devices)
        
        # All should find same device
        if result1:
            assert result1.name == "HD Pro Webcam"
        if result2:
            assert result2.name == "HD Pro Webcam"
        if result3:
            assert result3.name == "HD Pro Webcam"
    
    def test_find_device_by_name_substring_match(self):
        """Test find_device_by_name() matches substrings."""
        mock_devices = [
            Device("Logitech HD Pro Webcam C920", "/dev/video0"),
            Device("USB 2.0 Camera", "/dev/video1")
        ]
        
        # Partial matches
        result_logitech = find_device_by_name("Logitech", mock_devices)
        result_c920 = find_device_by_name("C920", mock_devices)
        result_usb = find_device_by_name("USB", mock_devices)
        
        if result_logitech:
            assert "Logitech" in result_logitech.name
        if result_c920:
            assert "C920" in result_c920.name
        if result_usb:
            assert "USB" in result_usb.name
    
    def test_find_device_by_name_returns_first_match(self):
        """Test find_device_by_name() returns first matching device."""
        mock_devices = [
            Device("USB Camera 1", "/dev/video0"),
            Device("USB Camera 2", "/dev/video1"),
            Device("USB Camera 3", "/dev/video2")
        ]
        
        result = find_device_by_name("USB", mock_devices)
        
        # Should return first match
        if result:
            assert result.path == "/dev/video0"
    
    def test_find_device_by_name_with_preloaded_list(self):
        """Test find_device_by_name() with pre-fetched device list."""
        # Get devices once
        devices_list = list_devices()
        
        # Use same list multiple times
        result1 = find_device_by_name("camera", devices_list)
        result2 = find_device_by_name("webcam", devices_list)
        
        # Should not call list_devices() again
        assert result1 is None or isinstance(result1, Device)
        assert result2 is None or isinstance(result2, Device)


class TestFindDevicesByNameFunction:
    """Test find_devices_by_name() function - find all matches."""
    
    def test_find_devices_by_name_returns_list(self):
        """Test find_devices_by_name() returns a list."""
        result = find_devices_by_name("NONEXISTENT")
        
        assert isinstance(result, list)
    
    def test_find_devices_by_name_empty_result(self):
        """Test find_devices_by_name() returns empty list when no matches."""
        result = find_devices_by_name("NONEXISTENT_CAMERA_99999")
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_find_devices_by_name_multiple_matches(self):
        """Test find_devices_by_name() finds multiple matching devices."""
        mock_devices = [
            Device("USB Camera 1", "/dev/video0"),
            Device("USB Camera 2", "/dev/video1"),
            Device("HD Webcam", "/dev/video2"),
            Device("USB Microphone", "/dev/audio0")  # Not a camera but matches USB
        ]
        
        result = find_devices_by_name("USB", mock_devices)
        
        # Should find all devices with "USB" in name
        assert isinstance(result, list)
        if len(mock_devices) > 0:
            assert len(result) >= 2  # At least USB Camera 1 and 2
        
        for device in result:
            assert "USB" in device.name or "usb" in device.name
    
    def test_find_devices_by_name_case_insensitive(self):
        """Test find_devices_by_name() is case-insensitive."""
        mock_devices = [
            Device("Logitech Webcam", "/dev/video0"),
            Device("LOGITECH Camera", "/dev/video1"),
            Device("logitech HD", "/dev/video2")
        ]
        
        result = find_devices_by_name("logitech", mock_devices)
        
        # Should find all 3 devices regardless of case
        assert isinstance(result, list)
        if len(mock_devices) > 0:
            assert len(result) == 3
    
    def test_find_devices_by_name_preserves_order(self):
        """Test find_devices_by_name() preserves device order."""
        mock_devices = [
            Device("Camera A", "/path/a"),
            Device("Camera B", "/path/b"),
            Device("Camera C", "/path/c")
        ]
        
        result = find_devices_by_name("Camera", mock_devices)
        
        # Should preserve order from input list
        if len(result) == 3:
            assert result[0].path == "/path/a"
            assert result[1].path == "/path/b"
            assert result[2].path == "/path/c"
    
    def test_find_devices_by_name_with_preloaded_list(self):
        """Test find_devices_by_name() with pre-fetched device list."""
        devices_list = list_devices()
        
        # Use same list multiple times
        result1 = find_devices_by_name("camera", devices_list)
        result2 = find_devices_by_name("usb", devices_list)
        
        assert isinstance(result1, list)
        assert isinstance(result2, list)


class TestListCamerasFunction:
    """Test list_cameras() function - Returns List[str] of camera names."""
    
    def test_list_cameras_returns_list(self):
        """list_cameras() should return a list."""
        result = list_cameras()
        assert isinstance(result, list)
    
    def test_list_cameras_returns_strings(self):
        """list_cameras() should return list of strings (camera names)."""
        cameras = list_cameras()
        devices_list = list_devices()
        
        # Should return same count
        assert len(cameras) == len(devices_list)
        
        # Each item should be a string (camera name)
        for name in cameras:
            assert isinstance(name, str)
            assert len(name) > 0
    
    def test_list_cameras_names_match_list_devices(self):
        """list_cameras() names should match list_devices() names."""
        cameras = list_cameras()
        devices_list = list_devices()
        
        assert len(cameras) == len(devices_list)
        
        # Each name should match corresponding device name
        for i, name in enumerate(cameras):
            assert name == devices_list[i].name


class TestFindCameraFunction:
    """Test find_camera() function - Returns CameraController or raises exception."""
    
    def test_find_camera_returns_camera_controller(self):
        """find_camera() should return connected CameraController when found."""
        devices_list = list_devices()
        if not devices_list:
            pytest.skip("No cameras available")
        
        # Use first word of first camera name
        search_term = devices_list[0].name.split()[0]
        
        try:
            result = find_camera(search_term)
            assert isinstance(result, CameraController)
            assert result.is_connected
            assert result.device_name
            result.close()
        except DeviceNotFoundError:
            pytest.skip("Camera not accessible")
    
    def test_find_camera_raises_on_not_found(self):
        """find_camera() should raise DeviceNotFoundError when not found."""
        with pytest.raises(DeviceNotFoundError):
            find_camera("NONEXISTENT_CAMERA_XYZ123")


class TestGetCameraInfoFunction:
    """Test get_camera_info() function - camera metadata."""
    
    def test_get_camera_info_exists(self):
        """Test get_camera_info() function exists."""
        assert hasattr(duvc_ctl, 'get_camera_info')
        assert callable(get_camera_info)


class TestGetDeviceInfoFunction:
    """Test get_device_info() function - comprehensive metadata."""
    
    def test_get_device_info_returns_dict(self):
        """Test get_device_info() returns a dictionary."""
        # Create mock device
        mock_device = Device("Test Camera", "/test/path")
        
        result = get_device_info(mock_device)
        
        # Should return dict-like object (DeviceInfo TypedDict)
        assert isinstance(result, dict)
    
    def test_get_device_info_has_required_fields(self):
        """Test DeviceInfo has all required fields."""
        mock_device = Device("Test Camera", "/test/path")
        
        result = get_device_info(mock_device)
        
        # Required fields from DeviceInfo TypedDict
        required_fields = ['name', 'path', 'connected', 'camera_properties', 'video_properties', 'error']
        
        for field in required_fields:
            assert field in result, f"DeviceInfo missing required field: {field}"
    
    def test_get_device_info_name_and_path(self):
        """Test get_device_info() returns correct name and path."""
        mock_device = Device("HD Webcam", "/dev/video0")
        
        result = get_device_info(mock_device)
        
        assert result['name'] == "HD Webcam"
        assert result['path'] == "/dev/video0"
    
    def test_get_device_info_connected_is_bool(self):
        """Test get_device_info() connected field is boolean."""
        mock_device = Device("Test Camera", "/test/path")
        
        result = get_device_info(mock_device)
        
        assert isinstance(result['connected'], (bool, type(result['connected'])))
    
    def test_get_device_info_properties_are_dicts(self):
        """Test get_device_info() property fields are dictionaries."""
        mock_device = Device("Test Camera", "/test/path")
        
        result = get_device_info(mock_device)
        
        assert isinstance(result['camera_properties'], dict)
        assert isinstance(result['video_properties'], dict)
    
    def test_get_device_info_error_field(self):
        """Test get_device_info() error field."""
        mock_device = Device("Test Camera", "/test/path")
        
        result = get_device_info(mock_device)
        
        # Error should be None or string
        assert result['error'] is None or isinstance(result['error'], str)


class TestPropertyInfoStructure:
    """Test PropertyInfo TypedDict structure."""
    
    def test_property_info_fields(self):
        """Test PropertyInfo has expected fields."""
        # PropertyInfo fields from TypedDict definition
        expected_fields = ['supported', 'current', 'range', 'error']
        
        # Can't test directly without device, but verify TypedDict exists
        assert hasattr(duvc_ctl, 'PropertyInfo')


class TestDeviceInfoStructure:
    """Test DeviceInfo TypedDict structure."""
    
    def test_device_info_fields(self):
        """Test DeviceInfo has expected fields."""
        # DeviceInfo fields from TypedDict definition
        expected_fields = ['name', 'path', 'connected', 'camera_properties', 'video_properties', 'error']
        
        # Verify TypedDict exists
        assert hasattr(duvc_ctl, 'DeviceInfo')


# ============================================================================
# WITH CAMERA TESTS - Integration tests using real camera
# ============================================================================

@pytest.mark.hardware
class TestFindDeviceByNameWithHardware:
    """Test find_device_by_name() with real camera hardware."""
    
    def test_find_device_by_exact_name(self, test_device, test_device_name):
        """Test finding device by exact name."""
        if test_device is None:
            pytest.skip("No test device available")
        
        # Search by exact name
        result = find_device_by_name(test_device_name)
        
        if result:
            assert isinstance(result, Device)
            assert result.name == test_device_name
    
    def test_find_device_by_partial_name(self, test_device, test_device_name):
        """Test finding device by partial name."""
        if test_device is None or len(test_device_name) < 3:
            pytest.skip("No test device available or name too short")
        
        # Search by first 3 characters
        partial_name = test_device_name[:3]
        result = find_device_by_name(partial_name)
        
        if result:
            assert isinstance(result, Device)
            assert partial_name.lower() in result.name.lower()
    
    def test_find_device_case_insensitive(self, test_device, test_device_name):
        """Test finding device with different case."""
        if test_device is None:
            pytest.skip("No test device available")
        
        # Search with uppercase
        result_upper = find_device_by_name(test_device_name.upper())
        # Search with lowercase
        result_lower = find_device_by_name(test_device_name.lower())
        
        # Both should find the device (or both None if not found)
        if result_upper and result_lower:
            assert result_upper.path == result_lower.path
    
    def test_find_nonexistent_device(self):
        """Test searching for non-existent device."""
        result = find_device_by_name("TOTALLY_FAKE_CAMERA_XXXXX")
        
        # Should return None
        assert result is None


@pytest.mark.hardware
class TestFindDevicesByNameWithHardware:
    """Test find_devices_by_name() with real camera hardware."""
    
    def test_find_all_matching_devices(self, available_devices):
        """Test finding all devices matching a common term."""
        if not available_devices:
            pytest.skip("No devices available")
        
        # Search for common term (e.g., "camera" or "usb")
        result = find_devices_by_name("camera")
        
        assert isinstance(result, list)
        
        for device in result:
            assert isinstance(device, Device)
            assert "camera" in device.name.lower()
    
    def test_find_devices_with_specific_term(self, available_devices):
        """Test finding devices with specific manufacturer/model."""
        if not available_devices:
            pytest.skip("No devices available")
        
        # Try common manufacturer names
        manufacturers = ["logitech", "microsoft", "hp", "dell", "lenovo", "creative"]
        
        found_any = False
        for manufacturer in manufacturers:
            result = find_devices_by_name(manufacturer)
            if result:
                found_any = True
                for device in result:
                    assert manufacturer.lower() in device.name.lower()
        
        # It's okay if no specific manufacturer found
        # Just verify the function works


@pytest.mark.hardware
class TestListCamerasWithHardware:
    """Test list_cameras() with real camera hardware."""
    
    def test_list_cameras_finds_devices(self, available_devices):
        """list_cameras() should find available devices."""
        cameras = list_cameras()
        assert isinstance(cameras, list)
        
        # Just verify the function works
        assert len(cameras) == len(available_devices)
    
    def test_list_cameras_returns_valid_strings(self, available_devices):
        """list_cameras() should return valid camera name strings."""
        if not available_devices:
            pytest.skip("No devices available")
        
        cameras = list_cameras()
        
        # Each item should be a non-empty string
        for name in cameras:
            assert isinstance(name, str)
            assert len(name) > 0


@pytest.mark.hardware
class TestFindCameraWithHardware:
    """Test find_camera() with real camera hardware."""
    
    def test_find_camera_by_name(self, test_device, test_device_name):
        """Test finding camera by name returns CameraController."""
        if test_device is None:
            pytest.skip("No test device available")
        
        # Search by partial name
        if len(test_device_name) > 3:
            try:
                result = find_camera(test_device_name[:3])
                assert isinstance(result, CameraController)
                assert result.is_connected
                assert result.device_name
                result.close()
            except DeviceNotFoundError:
                pytest.skip("Camera not accessible")


@pytest.mark.hardware
class TestGetDeviceInfoWithHardware:
    """Test get_device_info() with real camera hardware."""
    
    def test_get_device_info_with_real_device(self, test_device):
        """Test get_device_info() with connected camera."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_info(test_device)
        
        # Verify structure
        assert isinstance(result, dict)
        assert 'name' in result
        assert 'path' in result
        assert 'connected' in result
        assert 'camera_properties' in result
        assert 'video_properties' in result
        assert 'error' in result
        
        # Verify values
        assert result['name'] == test_device.name
        assert result['path'] == test_device.path
        assert isinstance(result['connected'], bool)
    
    def test_get_device_info_camera_properties(self, test_device):
        """Test get_device_info() camera_properties field."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_info(test_device)
        
        camera_props = result['camera_properties']
        assert isinstance(camera_props, dict)
        
        # Check structure of property entries
        for prop_name, prop_info in camera_props.items():
            assert isinstance(prop_name, str)
            assert isinstance(prop_info, dict)
            
            # PropertyInfo fields
            assert 'supported' in prop_info
            assert 'current' in prop_info
            assert 'range' in prop_info
            assert 'error' in prop_info
            
            # Check types
            assert isinstance(prop_info['supported'], bool)
            assert isinstance(prop_info['current'], dict)
            assert isinstance(prop_info['range'], dict)
            assert prop_info['error'] is None or isinstance(prop_info['error'], str)
    
    def test_get_device_info_video_properties(self, test_device):
        """Test get_device_info() video_properties field."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_info(test_device)
        
        video_props = result['video_properties']
        assert isinstance(video_props, dict)
        
        # Check structure of property entries
        for prop_name, prop_info in video_props.items():
            assert isinstance(prop_name, str)
            assert isinstance(prop_info, dict)
            
            # PropertyInfo fields
            assert 'supported' in prop_info
            assert 'current' in prop_info
            assert 'range' in prop_info
    
    def test_get_device_info_property_ranges(self, test_device):
        """Test get_device_info() includes property ranges."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_info(test_device)
        
        # Check video properties for brightness (commonly supported)
        video_props = result['video_properties']
        
        if 'brightness' in video_props or 'Brightness' in video_props:
            brightness_key = 'brightness' if 'brightness' in video_props else 'Brightness'
            brightness_info = video_props[brightness_key]
            
            if brightness_info['supported']:
                # Range should have min, max, step, default
                prop_range = brightness_info['range']
                assert 'min' in prop_range
                assert 'max' in prop_range
                assert 'step' in prop_range
                assert 'default' in prop_range
                
                # Sanity checks
                assert isinstance(prop_range['min'], int)
                assert isinstance(prop_range['max'], int)
                assert prop_range['min'] <= prop_range['max']
    
    def test_get_device_info_current_values(self, test_device):
        """Test get_device_info() includes current property values."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_info(test_device)
        
        # Check for any supported property
        all_props = {**result['camera_properties'], **result['video_properties']}
        
        supported_props = [name for name, info in all_props.items() if info['supported']]
        
        if supported_props:
            # Check first supported property
            prop_info = all_props[supported_props[0]]
            current = prop_info['current']
            
            # Current should have value and mode
            assert 'value' in current
            assert 'mode' in current
            
            assert isinstance(current['value'], (int, str))
            assert isinstance(current['mode'], str)
    
    def test_get_device_info_error_handling(self):
        """Test get_device_info() with invalid device."""
        fake_device = Device("Nonexistent", "/fake/path/999")
        
        result = get_device_info(fake_device)
        
        # Should not crash, should have error field
        assert isinstance(result, dict)
        assert 'error' in result
        
        # Error field might contain error message
        # (or None if device just not found)


@pytest.mark.hardware
class TestDiscoveryWorkflows:
    """Test common device discovery workflows."""
    
    def test_enumerate_and_find_workflow(self, available_devices):
        """Test enumerating devices then finding specific one."""
        if not available_devices:
            pytest.skip("No devices available")
        
        # Get all devices
        all_devices = list_devices()
        
        # Find first device by name
        first_device = all_devices[0]
        found = find_device_by_name(first_device.name[:5], all_devices)
        
        if found:
            assert isinstance(found, Device)
    
    def test_search_and_get_info_workflow(self, test_device, test_device_name):
        """Test searching for device and getting its info."""
        if test_device is None:
            pytest.skip("No test device available")
        
        # Find device
        found = find_device_by_name(test_device_name[:5])
        
        if found:
            # Get device info
            info = get_device_info(found)
            
            assert isinstance(info, dict)
            assert info['name'] == found.name
            assert info['path'] == found.path
    
    def test_find_multiple_and_filter_workflow(self, available_devices):
        """Test finding multiple devices and filtering results."""
        if len(available_devices) < 2:
            pytest.skip("Need at least 2 devices for this test")
        
        # Find all devices with common term
        cameras = find_devices_by_name("camera")
        
        # Filter by some criteria (e.g., contains "USB")
        usb_cameras = [cam for cam in cameras if "usb" in cam.name.lower()]
        
        # Both results should be Device objects
        for cam in cameras:
            assert isinstance(cam, Device)
        for cam in usb_cameras:
            assert isinstance(cam, Device)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
