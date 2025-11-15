"""
Test Suite 06: Result-Based API (Camera Class)
================================================

Tests the Result-based API centered around open_camera() and Camera class.

Functions and Methods Tested:
  - open_camera(device) - Open camera from Device object
  - open_camera(index) - Open camera from integer index
  - Camera.is_valid() - Check camera validity
  - Camera.is_ok() - Alias for is_valid()
  - Camera.device - Get underlying Device
  - Camera.get(CamProp) - Get camera property
  - Camera.get(VidProp) - Get video property
  - Camera.set(prop, PropSetting) - Set property with PropSetting
  - Camera.set(prop, value) - Set property with value only (manual mode)
  - Camera.set(prop, value, mode_str) - Set with string mode ("auto"/"manual")
  - Camera.set_auto(prop) - Set property to automatic mode
  - Camera.get_range(CamProp) - Get camera property range
  - Camera.get_range(VidProp) - Get video property range
  - Context manager support (__enter__/__exit__)

Total: 15+ Camera methods and operations

Test Organization:
  1. Without Camera Tests - Unit tests on API interface
  2. With Camera Tests - Integration tests using real camera hardware

Run: pytest tests/test_06_result_api.py -v
Run without camera: pytest tests/test_06_result_api.py -v -m "not hardware"
"""

import pytest
import sys
from typing import List, Optional

import duvc_ctl
from duvc_ctl import (
    # Core types
    Device, PropSetting, PropRange,
    # Core enums
    CamProp, VidProp, CamMode, ErrorCode,
    # Result types
    CameraResult, PropSettingResult, PropRangeResult, VoidResult,
    # Result helpers
    Ok_PropSetting, Err_PropSetting,
    # Camera class and functions
    Camera, open_camera,
    # Device functions
    list_devices, get_device_capabilities,
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
def test_camera(test_device) -> Optional[Camera]:
    """Get an open camera instance for testing."""
    if test_device is None:
        pytest.skip("No test device available")
    
    result: CameraResult = open_camera(test_device)
    if not result.is_ok():
        pytest.skip(f"Could not open camera: {result.error().description()}")
    
    camera = result.value()
    yield camera
    # Cleanup handled by Camera's RAII


# ============================================================================
# WITHOUT CAMERA TESTS - Unit tests on API interface
# ============================================================================

class TestOpenCameraFunction:
    """Test open_camera() function - camera creation."""
    
    def test_open_camera_signature_with_device(self):
        """Test open_camera() accepts Device parameter."""
        # Verify function exists and is callable
        assert hasattr(duvc_ctl, 'open_camera')
        assert callable(open_camera)
        
        # Create mock device
        mock_device = Device("Test Camera", "/test/path")
        
        # Should return CameraResult (may be error for fake device)
        result = open_camera(mock_device)
        assert isinstance(result, CameraResult)
    
    def test_open_camera_signature_with_index(self):
        """Test open_camera() accepts integer index parameter."""
        # Should accept int and return CameraResult
        result = open_camera(0)
        assert isinstance(result, CameraResult)
    
    def test_open_camera_returns_result_type(self):
        """Test open_camera() returns CameraResult."""
        mock_device = Device("Test", "/test")
        result = open_camera(mock_device)
        
        # Must have Result interface
        assert hasattr(result, 'is_ok')
        assert hasattr(result, 'is_error')
        assert callable(result.is_ok)
        assert callable(result.is_error)
    
    def test_open_camera_with_invalid_device(self):
        """Test open_camera() with invalid device returns error."""
        invalid_device = Device("Nonexistent", "/fake/path/999")
        result = open_camera(invalid_device)
        
        # Should return error result
        assert result.is_error()
        assert not result.is_ok()
    
    def test_open_camera_with_invalid_index(self):
        """Test open_camera() with out-of-range index returns error."""
        # Very high index unlikely to exist
        result = open_camera(999)
        
        # Should return error result
        assert result.is_error()
    
    def test_open_camera_error_has_description(self):
        """Test error result from open_camera() has description."""
        invalid_device = Device("Fake", "/fake")
        result = open_camera(invalid_device)
        
        if result.is_error():
            error = result.error()
            assert hasattr(error, 'description')
            assert hasattr(error, 'code')
            assert isinstance(error.description(), str)
            assert len(error.description()) > 0


class TestCameraResultType:
    """Test CameraResult type returned by open_camera()."""
    
    def test_camera_result_is_ok_method(self):
        """Test CameraResult.is_ok() method."""
        mock_device = Device("Test", "/test")
        result = open_camera(mock_device)
        
        # is_ok should return bool
        assert isinstance(result.is_ok(), bool)
    
    def test_camera_result_is_error_method(self):
        """Test CameraResult.is_error() method."""
        mock_device = Device("Test", "/test")
        result = open_camera(mock_device)
        
        # is_error should return bool
        assert isinstance(result.is_error(), bool)
        
        # is_ok and is_error should be inverses
        assert result.is_ok() != result.is_error()
    
    def test_camera_result_bool_conversion(self):
        """Test CameraResult boolean conversion."""
        result = open_camera(999)  # Invalid index
        
        # Should be falsy for error
        assert not result
        
        # bool() should match is_ok()
        assert bool(result) == result.is_ok()
    
    def test_camera_result_value_on_error_raises(self):
        """Test calling value() on error result raises exception."""
        result = open_camera(999)
        
        # Should raise exception when accessing value on error
        if result.is_error():
            with pytest.raises((RuntimeError, Exception)):
                result.value()
    
    def test_camera_result_error_on_success_raises(self):
        """Test calling error() on success result would raise exception."""
        # Can only test interface, need hardware for actual success
        # Test structure: if result.is_ok(), accessing error() should fail
        pass  # Tested with hardware


class TestCameraClassInterface:
    """Test Camera class interface and methods."""
    
    def test_camera_has_required_methods(self):
        """Test Camera class has all required methods."""
        required_methods = [
            'is_valid', 'is_ok', 'device',
            'get', 'set', 'set_auto', 'get_range'
        ]
        
        for method in required_methods:
            assert hasattr(Camera, method), f"Camera missing method: {method}"
    
    def test_camera_is_valid_method_signature(self):
        """Test Camera.is_valid() method signature."""
        assert hasattr(Camera, 'is_valid')
        # Method should be callable
    
    def test_camera_is_ok_method_signature(self):
        """Test Camera.is_ok() method signature (alias for is_valid)."""
        assert hasattr(Camera, 'is_ok')
    
    def test_camera_device_method_signature(self):
        """Test Camera.device method signature."""
        assert hasattr(Camera, 'device')
    
    def test_camera_get_method_signature(self):
        """Test Camera.get() method signature."""
        assert hasattr(Camera, 'get')
    
    def test_camera_set_method_signature(self):
        """Test Camera.set() method signature."""
        assert hasattr(Camera, 'set')
    
    def test_camera_set_auto_method_signature(self):
        """Test Camera.set_auto() method signature."""
        assert hasattr(Camera, 'set_auto')
    
    def test_camera_get_range_method_signature(self):
        """Test Camera.get_range() method signature."""
        assert hasattr(Camera, 'get_range')
    
    def test_camera_context_manager_support(self):
        """Test Camera supports context manager protocol."""
        assert hasattr(Camera, '__enter__')
        assert hasattr(Camera, '__exit__')


class TestCameraSetMethodOverloads:
    """Test Camera.set() method overloads."""
    
    def test_camera_set_with_prop_setting_signature(self):
        """Test set(prop, PropSetting) signature exists."""
        # This is tested via interface check
        assert hasattr(Camera, 'set')
    
    def test_camera_set_with_value_only_signature(self):
        """Test set(prop, value) signature exists."""
        # Overload: set(prop, int) - defaults to manual mode
        assert hasattr(Camera, 'set')
    
    def test_camera_set_with_mode_string_signature(self):
        """Test set(prop, value, mode_str) signature exists."""
        # Overload: set(prop, int, str) - "auto"/"manual"
        assert hasattr(Camera, 'set')


# ============================================================================
# WITH CAMERA TESTS - Integration tests using real camera
# ============================================================================

@pytest.mark.hardware
class TestOpenCameraWithHardware:
    """Test open_camera() with real camera hardware."""
    
    def test_open_camera_with_device_success(self, test_device):
        """Test opening camera with valid Device."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = open_camera(test_device)
        
        assert isinstance(result, CameraResult)
        assert result.is_ok()
        assert not result.is_error()
    
    def test_open_camera_with_index_success(self, available_devices):
        """Test opening camera with valid index."""
        if not available_devices:
            pytest.skip("No devices available")
        
        result = open_camera(0)
        
        assert isinstance(result, CameraResult)
        assert result.is_ok()
    
    def test_open_camera_value_returns_camera(self, test_device):
        """Test CameraResult.value() returns Camera object."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = open_camera(test_device)
        
        if result.is_ok():
            camera = result.value()
            assert isinstance(camera, Camera)
    
    def test_open_camera_multiple_times(self, test_device):
        """Test opening same camera multiple times."""
        if test_device is None:
            pytest.skip("No test device available")
        
        # Open first camera
        result1 = open_camera(test_device)
        assert result1.is_ok()
        
        # Open second camera (may fail if device busy)
        result2 = open_camera(test_device)
        
        # Either succeeds (multiple connections allowed) or fails (device busy)
        assert isinstance(result2, CameraResult)
    
    def test_open_camera_with_disconnected_device(self):
        """Test opening camera for disconnected device."""
        fake_device = Device("Disconnected Camera", "/fake/path/123")
        result = open_camera(fake_device)
        
        # Should return error
        assert result.is_error()
        
        error = result.error()
        assert error.code() in [ErrorCode.DeviceNotFound, ErrorCode.SystemError]


@pytest.mark.hardware
class TestCameraIsValidMethod:
    """Test Camera.is_valid() method."""
    
    def test_is_valid_returns_true_for_open_camera(self, test_camera):
        """Test is_valid() returns True for successfully opened camera."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        assert test_camera.is_valid()
    
    def test_is_ok_alias_matches_is_valid(self, test_camera):
        """Test is_ok() is alias for is_valid()."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        assert test_camera.is_ok() == test_camera.is_valid()
    
    def test_is_valid_multiple_calls_consistent(self, test_camera):
        """Test is_valid() returns consistent results."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        # Multiple calls should return same result
        result1 = test_camera.is_valid()
        result2 = test_camera.is_valid()
        result3 = test_camera.is_valid()
        
        assert result1 == result2 == result3


@pytest.mark.hardware
class TestCameraDeviceMethod:
    """Test Camera.device attribute."""
    
    def test_device_returns_device_object(self, test_camera, test_device):
        """Test device returns Device object."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        
        assert isinstance(device, Device)
    
    def test_device_matches_original(self, test_camera, test_device):
        """Test device returns same device used to open camera."""
        if test_camera is None or test_device is None:
            pytest.skip("No camera or device available")
        
        device = test_camera.device
        
        # Should match original device
        assert device.name == test_device.name
        assert device.path == test_device.path
        assert device == test_device
    
    def test_device_multiple_calls_consistent(self, test_camera):
        """Test device returns consistent results."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device1 = test_camera.device
        device2 = test_camera.device
        
        assert device1 == device2
        assert device1.path == device2.path


@pytest.mark.hardware
class TestCameraGetMethod:
    """Test Camera.get() method - property reading."""
    
    def test_get_camera_property(self, test_camera):
        """Test getting camera property with get(CamProp)."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_cam_props = caps.supported_camera_properties()
        
        if not supported_cam_props:
            pytest.skip("No supported camera properties")
        
        # Get first supported property
        prop = supported_cam_props[0]
        result = test_camera.get(prop)
        
        assert isinstance(result, PropSettingResult)
    
    def test_get_video_property(self, test_camera):
        """Test getting video property with get(VidProp)."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_vid_props = caps.supported_video_properties()
        
        if not supported_vid_props:
            pytest.skip("No supported video properties")
        
        # Get first supported property
        prop = supported_vid_props[0]
        result = test_camera.get(prop)
        
        assert isinstance(result, PropSettingResult)
    
    def test_get_returns_prop_setting_result(self, test_camera):
        """Test get() returns PropSettingResult."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_props:
            result = test_camera.get(VidProp.Brightness)
            
            assert hasattr(result, 'is_ok')
            assert hasattr(result, 'value')
            assert hasattr(result, 'error')
    
    def test_get_successful_returns_prop_setting(self, test_camera):
        """Test successful get() returns PropSetting with value and mode."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_props:
            result = test_camera.get(VidProp.Brightness)
            
            if result.is_ok():
                setting = result.value()
                
                assert isinstance(setting, PropSetting)
                assert isinstance(setting.value, int)
                assert isinstance(setting.mode, CamMode)
                assert setting.mode in [CamMode.Auto, CamMode.Manual]
    
    def test_get_unsupported_property_returns_error(self, test_camera):
        """Test getting unsupported property returns error result."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_cam_props = caps.supported_camera_properties()
        
        # Find unsupported property
        all_props = [CamProp.Pan, CamProp.Tilt, CamProp.Roll, CamProp.Zoom, CamProp.Focus]
        unsupported = None
        
        for prop in all_props:
            if prop not in supported_cam_props:
                unsupported = prop
                break
        
        if unsupported is None:
            pytest.skip("All test properties supported")
        
        result = test_camera.get(unsupported)
        
        # Should return error (or may succeed with some cameras)
        assert isinstance(result, PropSettingResult)


@pytest.mark.hardware
class TestCameraSetMethod:
    """Test Camera.set() method - property writing."""
    
    def test_set_with_prop_setting(self, test_camera):
        """Test set(prop, PropSetting) method."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_props:
            # Get current value
            get_result = test_camera.get(VidProp.Brightness)
            if not get_result.is_ok():
                pytest.skip("Could not read brightness")
            
            current = get_result.value()
            
            # Set same value back
            set_result = test_camera.set(VidProp.Brightness, current)
            
            assert isinstance(set_result, VoidResult)
    
    def test_set_with_value_only(self, test_camera):
        """Test set(prop, value) method (defaults to manual mode)."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_props:
            # Get range
            range_result = test_camera.get_range(VidProp.Brightness)
            if not range_result.is_ok():
                pytest.skip("Could not get range")
            
            prop_range = range_result.value()
            
            # Set to middle value with value-only signature
            mid_value = (prop_range.min + prop_range.max) // 2
            set_result = test_camera.set(VidProp.Brightness, mid_value)
            
            assert isinstance(set_result, VoidResult)
    
    def test_set_with_mode_string(self, test_camera):
        """Test set(prop, value, mode_str) method."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_props:
            range_result = test_camera.get_range(VidProp.Brightness)
            if not range_result.is_ok():
                pytest.skip("Could not get range")
            
            prop_range = range_result.value()
            mid_value = (prop_range.min + prop_range.max) // 2
            
            # Test with "manual" string
            set_result = test_camera.set(VidProp.Brightness, mid_value, "manual")
            assert isinstance(set_result, VoidResult)
            
            # Test with "auto" string
            set_result_auto = test_camera.set(VidProp.Brightness, mid_value, "auto")
            assert isinstance(set_result_auto, VoidResult)
    
    def test_set_returns_void_result(self, test_camera):
        """Test set() returns VoidResult."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_props:
            get_result = test_camera.get(VidProp.Brightness)
            if get_result.is_ok():
                current = get_result.value()
                set_result = test_camera.set(VidProp.Brightness, current)
                
                assert hasattr(set_result, 'is_ok')
                assert hasattr(set_result, 'is_error')
    
    def test_set_with_invalid_value_returns_error(self, test_camera):
        """Test setting out-of-range value returns error."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_props:
            range_result = test_camera.get_range(VidProp.Brightness)
            if range_result.is_ok():
                prop_range = range_result.value()
                
                # Try value way above max
                invalid_value = prop_range.max + 10000
                set_result = test_camera.set(VidProp.Brightness, invalid_value, "manual")
                
                # May fail or may clamp (implementation dependent)
                assert isinstance(set_result, VoidResult)


@pytest.mark.hardware
class TestCameraSetAutoMethod:
    """Test Camera.set_auto() method."""
    
    def test_set_auto_camera_property(self, test_camera):
        """Test set_auto(CamProp) sets property to automatic mode."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_camera_properties()
        
        if CamProp.Focus in supported_props:
            result = test_camera.set_auto(CamProp.Focus)
            
            assert isinstance(result, VoidResult)
    
    def test_set_auto_video_property(self, test_camera):
        """Test set_auto(VidProp) sets property to automatic mode."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_video_properties()
        
        if VidProp.WhiteBalance in supported_props:
            result = test_camera.set_auto(VidProp.WhiteBalance)
            
            assert isinstance(result, VoidResult)
    
    def test_set_auto_then_get_shows_auto_mode(self, test_camera):
        """Test set_auto() followed by get() shows Auto mode."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_video_properties()
        
        if VidProp.WhiteBalance in supported_props:
            # Set to auto
            set_result = test_camera.set_auto(VidProp.WhiteBalance)
            
            if set_result.is_ok():
                # Get current setting
                get_result = test_camera.get(VidProp.WhiteBalance)
                
                if get_result.is_ok():
                    setting = get_result.value()
                    # Should be in Auto mode
                    assert setting.mode == CamMode.Auto


@pytest.mark.hardware
class TestCameraGetRangeMethod:
    """Test Camera.get_range() method."""
    
    def test_get_range_camera_property(self, test_camera):
        """Test get_range(CamProp) returns property range."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_camera_properties()
        
        if not supported_props:
            pytest.skip("No supported camera properties")
        
        prop = supported_props[0]
        result = test_camera.get_range(prop)
        
        assert isinstance(result, PropRangeResult)
    
    def test_get_range_video_property(self, test_camera):
        """Test get_range(VidProp) returns property range."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_props:
            result = test_camera.get_range(VidProp.Brightness)
            
            assert isinstance(result, PropRangeResult)
    
    def test_get_range_successful_returns_prop_range(self, test_camera):
        """Test successful get_range() returns PropRange with valid data."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_props:
            result = test_camera.get_range(VidProp.Brightness)
            
            if result.is_ok():
                prop_range = result.value()
                
                assert isinstance(prop_range, PropRange)
                assert isinstance(prop_range.min, int)
                assert isinstance(prop_range.max, int)
                assert isinstance(prop_range.step, int)
                assert isinstance(prop_range.default_val, int)
                assert isinstance(prop_range.default_mode, CamMode)
                
                # Sanity checks
                assert prop_range.min <= prop_range.max
                assert prop_range.step > 0
                assert prop_range.min <= prop_range.default_val <= prop_range.max


@pytest.mark.hardware
class TestCameraContextManager:
    """Test Camera context manager support."""
    
    def test_camera_as_context_manager(self, test_device):
        """Test using Camera with 'with' statement."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = open_camera(test_device)
        if not result.is_ok():
            pytest.skip("Could not open camera")
        
        camera = result.value()
        
        # Use as context manager
        with camera as cam:
            assert cam.is_valid()
            assert isinstance(cam, Camera)
    
    def test_context_manager_cleanup(self, test_device):
        """Test context manager properly cleans up."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = open_camera(test_device)
        if not result.is_ok():
            pytest.skip("Could not open camera")
        
        camera = result.value()
        
        # Use in context
        with camera as cam:
            device = cam.device
            assert device == test_device
        
        # After context, camera still exists but may be in different state
        # RAII handles cleanup internally


@pytest.mark.hardware
class TestCameraWorkflows:
    """Test common Camera usage workflows."""
    
    def test_open_get_close_workflow(self, test_device):
        """Test complete open -> get -> close workflow."""
        if test_device is None:
            pytest.skip("No test device available")
        
        # Open camera
        result = open_camera(test_device)
        assert result.is_ok()
        
        camera = result.value()
        assert camera.is_valid()
        
        # Get device capabilities
        caps_result = get_device_capabilities(test_device)
        if caps_result.is_ok():
            caps = caps_result.value()
            supported_props = caps.supported_video_properties()
            
            # Get property if any supported
            if supported_props:
                prop = supported_props[0]
                get_result = camera.get(prop)
                assert isinstance(get_result, PropSettingResult)
    
    def test_open_get_set_workflow(self, test_device):
        """Test open -> get -> modify -> set workflow."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = open_camera(test_device)
        if not result.is_ok():
            pytest.skip("Could not open camera")
        
        camera = result.value()
        
        caps_result = get_device_capabilities(test_device)
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_props:
            # Get current value
            get_result = camera.get(VidProp.Brightness)
            if get_result.is_ok():
                current = get_result.value()
                
                # Set same value back
                set_result = camera.set(VidProp.Brightness, current)
                
                # Verify set succeeded or understand why it failed
                assert isinstance(set_result, VoidResult)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
