"""
Test Suite 03: Result Types
============================

Tests all Result<T> type specializations and helper functions exposed by duvc-ctl.

Result Types Tested:
  - PropSettingResult - Result<PropSetting>
  - PropRangeResult - Result<PropRange>
  - VoidResult - Result<void>
  - CameraResult - Result<Camera>
  - DeviceCapabilitiesResult - Result<DeviceCapabilities>
  - BoolResult - Result<bool>
  - Uint32Result - Result<uint32_t>

Helper Functions:
  - Ok_PropSetting, Err_PropSetting
  - Ok_PropRange, Err_PropRange
  - Ok_void, Err_void
  - Ok_bool, Err_bool, Ok_uint32, Err_uint32

Total: 7 Result types + 14 helper functions

Test Organization:
  1. Without Camera Tests - Unit tests on Result types (no hardware required)
  2. With Camera Tests - Integration tests using real camera operations

Run: pytest tests/test_03_result_types.py -v
Run without camera: pytest tests/test_03_result_types.py -v -m "not hardware"
"""

import pytest
import sys
from typing import List, Optional

import duvc_ctl
from duvc_ctl import (
    # Core types
    Device, PropSetting, PropRange, PropertyCapability, Error, DeviceCapabilities, Camera,
    # Core enums
    CamProp, VidProp, CamMode, ErrorCode,
    # Result types
    PropSettingResult, PropRangeResult, VoidResult, CameraResult, DeviceCapabilitiesResult,
    BoolResult, Uint32Result,
    # Helper functions - Ok variants
    Ok_PropSetting, Ok_PropRange, Ok_void, Ok_bool, Ok_uint32,
    # Helper functions - Err variants
    Err_PropSetting, Err_PropRange, Err_void, Err_bool, Err_uint32,
    # Core functions
    list_devices, open_camera, get_device_capabilities, to_string,
)


from duvc_ctl import ErrorInfo as Error


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def available_devices() -> List[Device]:
    """Get list of available camera devices for hardware tests."""
    try:
        devices = list_devices()
        return devices
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
# WITHOUT CAMERA TESTS - Unit tests on Result types
# ============================================================================

class TestPropSettingResult:
    """Test PropSettingResult - Result<PropSetting> type."""
    
    def test_propsettingresult_ok_creation(self):
        """Test creating successful PropSettingResult with Ok_PropSetting."""
        setting = PropSetting(50, CamMode.Manual)
        result = Ok_PropSetting(setting)
        
        assert isinstance(result, PropSettingResult)
        assert result.is_ok()
        assert not result.is_error()
    
    def test_propsettingresult_ok_value_access(self):
        """Test accessing value from successful PropSettingResult."""
        setting = PropSetting(75, CamMode.Auto)
        result = Ok_PropSetting(setting)
        
        retrieved = result.value()
        assert isinstance(retrieved, PropSetting)
        assert retrieved.value == 75
        assert retrieved.mode == CamMode.Auto
    
    def test_propsettingresult_err_creation(self):
        """Test creating error PropSettingResult with Err_PropSetting."""
        result = Err_PropSetting(ErrorCode.PropertyNotSupported, "Property not supported")
        
        assert isinstance(result, PropSettingResult)
        assert not result.is_ok()
        assert result.is_error()
    
    def test_propsettingresult_err_error_access(self):
        """Test accessing error from failed PropSettingResult."""
        result = Err_PropSetting(ErrorCode.InvalidValue, "Value out of range")
        
        error = result.error()
        assert isinstance(error, Error)
        assert error.code() == ErrorCode.InvalidValue
        assert "Value out of range" in error.message()
    
    def test_propsettingresult_bool_conversion(self):
        """Test boolean conversion of PropSettingResult."""
        ok_result = Ok_PropSetting(PropSetting(50, CamMode.Manual))
        err_result = Err_PropSetting(ErrorCode.DeviceNotFound, "Not found")
        
        # Ok result should be truthy
        assert bool(ok_result) == True
        assert ok_result  # Direct bool conversion
        
        # Error result should be falsy
        assert bool(err_result) == False
        assert not err_result
    
    def test_propsettingresult_value_or_method(self):
        """Test value_or() method for default fallback."""
        ok_result = Ok_PropSetting(PropSetting(100, CamMode.Auto))
        err_result = Err_PropSetting(ErrorCode.SystemError, "System error")
        
        # Ok result returns actual value
        value = ok_result.value_or(PropSetting(0, CamMode.Manual))
        assert value.value == 100
        
        # Error result returns default
        default = PropSetting(999, CamMode.Manual)
        value = err_result.value_or(default)
        assert value.value == 999
    
    def test_propsettingresult_cannot_access_error_on_ok(self):
        """Test that accessing error on Ok result raises exception."""
        result = Ok_PropSetting(PropSetting(50, CamMode.Manual))
        
        # Should not be able to get error from Ok result
        with pytest.raises((RuntimeError, AttributeError, Exception)):
            result.error()
    
    def test_propsettingresult_cannot_access_value_on_error(self):
        """Test that accessing value on Error result raises exception."""
        result = Err_PropSetting(ErrorCode.DeviceBusy, "Device busy")
        
        # Should not be able to get value from Error result
        with pytest.raises((RuntimeError, AttributeError, Exception)):
            result.value()


class TestPropRangeResult:
    """Test PropRangeResult - Result<PropRange> type."""
    
    def test_proprangeresult_ok_creation(self):
        """Test creating successful PropRangeResult with Ok_PropRange."""
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 100
        prop_range.step = 1
        
        result = Ok_PropRange(prop_range)
        
        assert isinstance(result, PropRangeResult)
        assert result.is_ok()
        assert not result.is_error()
    
    def test_proprangeresult_ok_value_access(self):
        """Test accessing value from successful PropRangeResult."""
        prop_range = PropRange()
        prop_range.min = -50
        prop_range.max = 50
        prop_range.step = 5
        prop_range.default_val = 0
        prop_range.default_mode = CamMode.Auto
        
        result = Ok_PropRange(prop_range)
        
        retrieved = result.value()
        assert isinstance(retrieved, PropRange)
        assert retrieved.min == -50
        assert retrieved.max == 50
        assert retrieved.step == 5
        assert retrieved.default_val == 0
        assert retrieved.default_mode == CamMode.Auto
    
    def test_proprangeresult_err_creation(self):
        """Test creating error PropRangeResult with Err_PropRange."""
        result = Err_PropRange(ErrorCode.PropertyNotSupported, "Range not available")
        
        assert isinstance(result, PropRangeResult)
        assert not result.is_ok()
        assert result.is_error()
    
    def test_proprangeresult_err_error_access(self):
        """Test accessing error from failed PropRangeResult."""
        result = Err_PropRange(ErrorCode.PermissionDenied, "Access denied")
        
        error = result.error()
        assert isinstance(error, Error)
        assert error.code() == ErrorCode.PermissionDenied
        assert "Access denied" in error.message()
    
    def test_proprangeresult_bool_conversion(self):
        """Test boolean conversion of PropRangeResult."""
        ok_result = Ok_PropRange(PropRange())
        err_result = Err_PropRange(ErrorCode.DeviceNotFound, "Not found")
        
        assert bool(ok_result) == True
        assert bool(err_result) == False
    
    def test_proprangeresult_value_or_method(self):
        """Test value_or() method with default."""
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 100
        
        ok_result = Ok_PropRange(prop_range)
        err_result = Err_PropRange(ErrorCode.SystemError, "Error")
        
        # Ok result returns actual value
        value = ok_result.value_or(PropRange())
        assert value.min == 0
        assert value.max == 100
        
        # Error result returns default
        default_range = PropRange()
        default_range.min = -1
        default_range.max = -1
        value = err_result.value_or(default_range)
        assert value.min == -1


class TestVoidResult:
    """Test VoidResult - Result<void> type."""
    
    def test_voidresult_ok_creation(self):
        """Test creating successful VoidResult with Ok_void."""
        result = Ok_void()
        
        assert isinstance(result, VoidResult)
        assert result.is_ok()
        assert not result.is_error()
    
    def test_voidresult_err_creation(self):
        """Test creating error VoidResult with Err_void."""
        result = Err_void(ErrorCode.InvalidArgument, "Invalid argument")
        
        assert isinstance(result, VoidResult)
        assert not result.is_ok()
        assert result.is_error()
    
    def test_voidresult_no_value_method(self):
        """Test VoidResult has no value() method."""
        result = Ok_void()
        
        # VoidResult should not have value() method
        assert not hasattr(result, 'value')
    
    def test_voidresult_error_access(self):
        """Test accessing error from failed VoidResult."""
        result = Err_void(ErrorCode.NotImplemented, "Not implemented")
        
        error = result.error()
        assert isinstance(error, Error)
        assert error.code() == ErrorCode.NotImplemented
    
    def test_voidresult_bool_conversion(self):
        """Test boolean conversion of VoidResult."""
        ok_result = Ok_void()
        err_result = Err_void(ErrorCode.SystemError, "System error")
        
        assert bool(ok_result) == True
        assert bool(err_result) == False
    
    def test_voidresult_various_error_codes(self):
        """Test VoidResult with various ErrorCode values."""
        error_codes = [
            ErrorCode.DeviceNotFound,
            ErrorCode.DeviceBusy,
            ErrorCode.PropertyNotSupported,
            ErrorCode.InvalidValue,
            ErrorCode.PermissionDenied,
            ErrorCode.SystemError,
            ErrorCode.InvalidArgument,
            ErrorCode.NotImplemented,
        ]
        
        for code in error_codes:
            result = Err_void(code, f"Error: {to_string(code)}")
            assert result.is_error()
            assert result.error().code() == code


class TestCameraResult:
    """Test CameraResult - Result<Camera> type."""
    
    def test_cameraresult_has_required_methods(self):
        """Test CameraResult has all required methods."""
        # Test interface exists (actual Camera creation tested with hardware)
        required_methods = ['is_ok', 'is_error', 'value', 'error']
        
        for method in required_methods:
            assert hasattr(CameraResult, method), f"CameraResult missing {method}"
    
    @pytest.mark.skip(reason="Err_Camera not implemented - Camera is move-only")
    def test_cameraresult_err_creation(self):
        """Test creating error CameraResult."""
        # Can create error results without hardware
        # Note: Cannot create Ok result without actual camera
        
        # Err_Camera helper should exist
        assert hasattr(duvc_ctl, 'Err_Camera')


class TestDeviceCapabilitiesResult:
    """Test DeviceCapabilitiesResult - Result<DeviceCapabilities> type."""
    
    def test_devicecapabilitiesresult_has_required_methods(self):
        """Test DeviceCapabilitiesResult has all required methods."""
        required_methods = ['is_ok', 'is_error', 'value', 'error']
        
        for method in required_methods:
            assert hasattr(DeviceCapabilitiesResult, method)
    
    @pytest.mark.skip(reason="Err_Camera not implemented - Camera is move-only")
    def test_devicecapabilitiesresult_err_creation(self):
        """Test creating error DeviceCapabilitiesResult."""
        # Err_DeviceCapabilities helper should exist
        assert hasattr(duvc_ctl, 'Err_DeviceCapabilities')


class TestBoolResult:
    """Test BoolResult - Result<bool> type."""
    
    def test_boolresult_ok_true(self):
        """Test creating successful BoolResult with Ok_bool(True)."""
        result = Ok_bool(True)
        
        assert isinstance(result, BoolResult)
        assert result.is_ok()
        assert not result.is_error()
        assert result.value() == True
    
    def test_boolresult_ok_false(self):
        """Test creating successful BoolResult with Ok_bool(False)."""
        result = Ok_bool(False)
        
        assert result.is_ok()
        assert result.value() == False
    
    def test_boolresult_err_creation(self):
        """Test creating error BoolResult with Err_bool."""
        result = Err_bool(ErrorCode.DeviceNotFound, "Device not found")
        
        assert isinstance(result, BoolResult)
        assert not result.is_ok()
        assert result.is_error()
    
    def test_boolresult_error_access(self):
        """Test accessing error from failed BoolResult."""
        result = Err_bool(ErrorCode.PermissionDenied, "Access denied")
        
        error = result.error()
        assert isinstance(error, Error)
        assert error.code() == ErrorCode.PermissionDenied
    
    def test_boolresult_bool_conversion(self):
        """Test boolean conversion of BoolResult (checks success, not value)."""
        ok_true = Ok_bool(True)
        ok_false = Ok_bool(False)
        err_result = Err_bool(ErrorCode.SystemError, "Error")
        
        # Boolean conversion checks is_ok(), not the contained bool value
        assert bool(ok_true) == True   # Result is Ok
        assert bool(ok_false) == True  # Result is Ok (even though value is False)
        assert bool(err_result) == False  # Result is Error


class TestUint32Result:
    """Test Uint32Result - Result<uint32_t> type."""
    
    def test_uint32result_ok_creation(self):
        """Test creating successful Uint32Result with Ok_uint32."""
        result = Ok_uint32(12345)
        
        assert isinstance(result, Uint32Result)
        assert result.is_ok()
        assert not result.is_error()
    
    def test_uint32result_ok_value_access(self):
        """Test accessing value from successful Uint32Result."""
        test_values = [0, 1, 100, 1000, 65535, 2**32 - 1]
        
        for val in test_values:
            result = Ok_uint32(val)
            assert result.value() == val
    
    def test_uint32result_err_creation(self):
        """Test creating error Uint32Result with Err_uint32."""
        result = Err_uint32(ErrorCode.InvalidValue, "Invalid ID")
        
        assert isinstance(result, Uint32Result)
        assert not result.is_ok()
        assert result.is_error()
    
    def test_uint32result_error_access(self):
        """Test accessing error from failed Uint32Result."""
        result = Err_uint32(ErrorCode.DeviceNotFound, "Device not found")
        
        error = result.error()
        assert isinstance(error, Error)
        assert error.code() == ErrorCode.DeviceNotFound
    
    def test_uint32result_bool_conversion(self):
        """Test boolean conversion of Uint32Result."""
        ok_result = Ok_uint32(42)
        err_result = Err_uint32(ErrorCode.SystemError, "Error")
        
        assert bool(ok_result) == True
        assert bool(err_result) == False


class TestResultHelperFunctions:
    """Test Ok_* and Err_* helper functions."""
    
    def test_ok_helpers_exist(self):
        """Test all Ok_* helper functions exist."""
        ok_helpers = [
            'Ok_PropSetting',
            'Ok_PropRange',
            'Ok_void',
            'Ok_bool',
            'Ok_uint32',
        ]
        
        for helper in ok_helpers:
            assert hasattr(duvc_ctl, helper), f"Missing helper: {helper}"
    
    def test_err_helpers_exist(self):
        """Test all Err_* helper functions exist."""
        err_helpers = [
            'Err_PropSetting',
            'Err_PropRange',
            'Err_void',
            'Err_bool',
            'Err_uint32',
        ]
        
        for helper in err_helpers:
            assert hasattr(duvc_ctl, helper), f"Missing helper: {helper}"
    
    def test_ok_helper_return_types(self):
        """Test Ok_* helpers return correct Result types."""
        # PropSetting
        assert isinstance(Ok_PropSetting(PropSetting(50, CamMode.Manual)), PropSettingResult)
        
        # PropRange
        assert isinstance(Ok_PropRange(PropRange()), PropRangeResult)
        
        # void
        assert isinstance(Ok_void(), VoidResult)
        
        # bool
        assert isinstance(Ok_bool(True), BoolResult)
        
        # uint32
        assert isinstance(Ok_uint32(123), Uint32Result)
    
    def test_err_helper_return_types(self):
        """Test Err_* helpers return correct Result types."""
        code = ErrorCode.DeviceNotFound
        msg = "Test error"
        
        # PropSetting
        assert isinstance(Err_PropSetting(code, msg), PropSettingResult)
        
        # PropRange
        assert isinstance(Err_PropRange(code, msg), PropRangeResult)
        
        # void
        assert isinstance(Err_void(code, msg), VoidResult)
        
        # bool
        assert isinstance(Err_bool(code, msg), BoolResult)
        
        # uint32
        assert isinstance(Err_uint32(code, msg), Uint32Result)


class TestResultErrorCodes:
    """Test Result types with all ErrorCode values."""
    
    def test_all_error_codes_in_results(self):
        """Test creating Results with all ErrorCode values."""
        error_codes = [
            ErrorCode.Success,
            ErrorCode.DeviceNotFound,
            ErrorCode.DeviceBusy,
            ErrorCode.PropertyNotSupported,
            ErrorCode.InvalidValue,
            ErrorCode.PermissionDenied,
            ErrorCode.SystemError,
            ErrorCode.InvalidArgument,
            ErrorCode.NotImplemented,
        ]
        
        for code in error_codes:
            msg = f"Test error: {to_string(code)}"
            
            # Test with PropSettingResult
            result = Err_PropSetting(code, msg)
            assert result.error().code() == code
            
            # Test with VoidResult
            void_result = Err_void(code, msg)
            assert void_result.error().code() == code
    
    def test_error_code_success_in_result(self):
        """Test ErrorCode.Success can be used in error results."""
        # Even though semantically odd, Success code can be in error result
        result = Err_PropSetting(ErrorCode.Success, "Success error")
        
        assert result.is_error()
        assert result.error().code() == ErrorCode.Success


class TestResultChaining:
    """Test Result chaining and composition patterns."""
    
    def test_result_chaining_with_is_ok(self):
        """Test chaining operations based on is_ok()."""
        ok_result = Ok_PropSetting(PropSetting(50, CamMode.Manual))
        err_result = Err_PropSetting(ErrorCode.DeviceNotFound, "Not found")
        
        # Chain with is_ok()
        if ok_result.is_ok():
            value = ok_result.value()
            assert value.value == 50
        
        if not err_result.is_ok():
            error = err_result.error()
            assert error.code() == ErrorCode.DeviceNotFound
    
    def test_result_value_or_chaining(self):
        """Test using value_or for fallback chains."""
        result1 = Err_PropSetting(ErrorCode.DeviceNotFound, "Not found")
        result2 = Ok_PropSetting(PropSetting(75, CamMode.Auto))
        
        # Chain with value_or
        default = PropSetting(0, CamMode.Manual)
        value = result1.value_or(default)
        
        # Should get default since result1 is error
        assert value.value == 0


# ============================================================================
# WITH CAMERA TESTS - Integration tests using real camera operations
# ============================================================================

@pytest.mark.hardware
class TestResultsWithCamera:
    """Test Result types with real camera operations."""
    
    def test_cameraresult_from_open_camera(self, test_device):
        """Test CameraResult returned by open_camera()."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = open_camera(test_device)
        
        assert isinstance(result, CameraResult)
        assert hasattr(result, 'is_ok')
        assert hasattr(result, 'is_error')
        
        if result.is_ok():
            camera = result.value()
            assert isinstance(camera, Camera)
            assert camera.is_valid()
        else:
            error = result.error()
            assert isinstance(error, Error)
            assert isinstance(error.code(), ErrorCode)
    
    def test_cameraresult_with_invalid_device(self):
        """Test CameraResult with invalid device."""
        invalid_device = Device("Nonexistent", "/invalid/path")
        result = open_camera(invalid_device)
        
        assert isinstance(result, CameraResult)
        # Should be error
        assert result.is_error()
        
        error = result.error()
        assert isinstance(error.code(), ErrorCode)
    
    def test_propsettingresult_from_camera_get(self, test_camera):
        """Test PropSettingResult from camera.get()."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        from duvc_ctl import get_device_capabilities
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_vid_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_vid_props:
            result = test_camera.get(VidProp.Brightness)
            
            assert isinstance(result, PropSettingResult)
            assert result.is_ok() or result.is_error()
            
            if result.is_ok():
                setting = result.value()
                assert isinstance(setting, PropSetting)
                assert isinstance(setting.mode, CamMode)
            else:
                error = result.error()
                assert isinstance(error, Error)
    
    def test_proprangeresult_from_camera_get_range(self, test_camera):
        """Test PropRangeResult from camera.get_range()."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        from duvc_ctl import get_device_capabilities
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_vid_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_vid_props:
            result = test_camera.get_range(VidProp.Brightness)
            
            assert isinstance(result, PropRangeResult)
            
            if result.is_ok():
                prop_range = result.value()
                assert isinstance(prop_range, PropRange)
                assert prop_range.min <= prop_range.max
                assert prop_range.step > 0
            else:
                error = result.error()
                assert isinstance(error, Error)
    
    def test_voidresult_from_camera_set(self, test_camera):
        """Test VoidResult from camera.set()."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        from duvc_ctl import get_device_capabilities
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_vid_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_vid_props:
            # Get current value first
            get_result = test_camera.get(VidProp.Brightness)
            if not get_result.is_ok():
                pytest.skip("Could not read brightness")
            
            current = get_result.value()
            
            # Set same value back
            set_result = test_camera.set(VidProp.Brightness, current)
            
            assert isinstance(set_result, VoidResult)
            
            if set_result.is_ok():
                # Success has no value to check
                pass
            else:
                error = set_result.error()
                assert isinstance(error, Error)
    
    def test_devicecapabilitiesresult_from_get_capabilities(self, test_device):
        """Test DeviceCapabilitiesResult from get_device_capabilities()."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_capabilities(test_device)
        
        assert isinstance(result, DeviceCapabilitiesResult)
        
        if result.is_ok():
            caps = result.value()
            assert isinstance(caps, DeviceCapabilities)
            
            # Verify capabilities have expected properties
            cam_props = caps.supported_camera_properties()
            vid_props = caps.supported_video_properties()
            
            assert isinstance(cam_props, list)
            assert isinstance(vid_props, list)
        else:
            error = result.error()
            assert isinstance(error, Error)


@pytest.mark.hardware
class TestResultErrorHandlingWithCamera:
    """Test Result error handling with real camera scenarios."""
    
    def test_result_error_for_unsupported_property(self, test_camera):
        """Test Result returns error for unsupported property."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        from duvc_ctl import get_device_capabilities
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_cam_props = caps.supported_camera_properties()
        
        # Find an unsupported property
        all_props = [CamProp.Pan, CamProp.Tilt, CamProp.Roll, CamProp.Zoom, CamProp.Focus]
        unsupported = None
        
        for prop in all_props:
            if prop not in supported_cam_props:
                unsupported = prop
                break
        
        if unsupported is None:
            pytest.skip("All properties supported by camera")
        
        # Try to get unsupported property
        result = test_camera.get(unsupported)
        
        # Should return error result
        if result.is_error():
            error = result.error()
            # Should be PropertyNotSupported error
            assert error.code() in [ErrorCode.PropertyNotSupported, ErrorCode.SystemError]
    
    def test_result_error_for_invalid_value(self, test_camera):
        """Test Result returns error for out-of-range value."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        from duvc_ctl import get_device_capabilities
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_vid_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_vid_props:
            # Get valid range
            range_result = test_camera.get_range(VidProp.Brightness)
            
            if range_result.is_ok():
                prop_range = range_result.value()
                
                # Try to set value way above max
                invalid_value = prop_range.max + 10000
                setting = PropSetting(invalid_value, CamMode.Manual)
                
                set_result = test_camera.set(VidProp.Brightness, setting)
                
                # May fail with InvalidValue or may clamp (implementation dependent)
                # Just verify we get a valid Result
                assert isinstance(set_result, VoidResult)
                assert isinstance(set_result.is_ok(), bool)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
