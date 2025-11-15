"""
Test Suite 02: Core Types
==========================

Tests all core type classes exposed by duvc-ctl Python bindings.

Types Tested:
  - Device - Camera device identification
  - PropSetting - Property value and control mode
  - PropRange - Property constraints and validation  
  - PropertyCapability - Property support information
  - Error - Error context with code and description
  - DeviceCapabilities - Complete device capability snapshot

Total: 6 core types + their methods

Test Organization:
  1. Without Camera Tests - Unit tests on type objects (no hardware required)
  2. With Camera Tests - Integration tests using real camera devices

Run: pytest tests/test_02_core_types.py -v
Run without camera: pytest tests/test_02_core_types.py -v -m "not hardware"
"""

import pytest
import sys
import copy
from typing import List, Optional

import duvc_ctl
from duvc_ctl import (
    # Core types
    Device, PropSetting, PropRange, PropertyCapability, ErrorInfo, DeviceCapabilities,
    # Core enums
    CamProp, VidProp, CamMode, ErrorCode,
    # Core functions
    list_devices, open_camera, get_device_capabilities, to_string,
    # Result types
    CameraResult, DeviceCapabilitiesResult,
    Camera,
)


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


@pytest.fixture
def mock_prop_range() -> PropRange:
    """Create a valid PropRange for testing."""
    prop_range = PropRange()
    prop_range.min = 0
    prop_range.max = 100
    prop_range.step = 1  # CRITICAL: Non-zero to avoid division by zero
    prop_range.default_val = 50
    prop_range.default_mode = CamMode.Manual
    return prop_range


# ============================================================================
# WITHOUT CAMERA TESTS - Unit tests on type objects
# ============================================================================

class TestDeviceType:
    """Test Device type - camera device identification."""
    
    def test_device_default_construction(self):
        """Test creating empty Device."""
        device = Device()
        assert isinstance(device, Device)
        # Empty device should not be valid
        assert not device.is_valid()
    
    def test_device_construction_with_parameters(self):
        """Test creating Device with name and path."""
        device = Device("Test Camera", "/dev/video0")
        
        assert isinstance(device, Device)
        assert device.is_valid()
        assert device.name == "Test Camera"
        assert device.path == "/dev/video0"
    
    def test_device_name_property(self):
        """Test Device.name property."""
        device = Device("HD Pro Webcam", "/dev/video1")
        
        assert hasattr(device, 'name')
        assert isinstance(device.name, str)
        assert device.name == "HD Pro Webcam"
        
        # Name should be read-only
        with pytest.raises(AttributeError):
            device.name = "New Name"
    
    def test_device_path_property(self):
        """Test Device.path property."""
        device = Device("Camera", "\\\\?\\USB#VID_046D&PID_0825")
        
        assert hasattr(device, 'path')
        assert isinstance(device.path, str)
        assert "USB" in device.path
        
        # Path should be read-only
        with pytest.raises(AttributeError):
            device.path = "New Path"
    
    def test_device_is_valid(self):
        """Test Device.is_valid() method."""
        # Valid device
        valid_device = Device("Camera", "/path")
        assert valid_device.is_valid()
        
        # Empty device
        empty_device = Device()
        assert not empty_device.is_valid()
        
        # Device with only name
        name_only = Device("Camera", "")
        # Should be invalid without path
        assert not name_only.is_valid()
    
    def test_device_get_id(self):
        """Test Device.get_id() method."""
        device = Device("Test Camera", "/dev/video0")
        
        device_id = device.get_id()
        assert isinstance(device_id, str)
        assert len(device_id) > 0
        
        # ID should be based on path (stable identifier)
        device2 = Device("Different Name", "/dev/video0")
        assert device.get_id() == device2.get_id()
    
    def test_device_equality(self):
        """Test Device equality comparison."""
        dev1 = Device("Camera 1", "/path/1")
        dev2 = Device("Camera 1", "/path/1")
        dev3 = Device("Camera 2", "/path/2")
        dev4 = Device("Different Name", "/path/1")  # Same path
        
        # Same device (by path)
        assert dev1 == dev2
        
        # Different devices
        assert dev1 != dev3
        
        # Equality based on path, not name
        assert dev1 == dev4
    
    def test_device_inequality(self):
        """Test Device inequality operator."""
        dev1 = Device("Camera 1", "/path/1")
        dev2 = Device("Camera 2", "/path/2")
        
        assert dev1 != dev2
        assert not (dev1 != dev1)
    
    def test_device_hashing(self):
        """Test Device can be used in sets and dicts."""
        dev1 = Device("Camera 1", "/path/1")
        dev2 = Device("Camera 1", "/path/1")
        dev3 = Device("Camera 2", "/path/2")
        
        # Test in set
        device_set = {dev1, dev2, dev3}
        assert len(device_set) == 2  # dev1 and dev2 are same
        assert dev1 in device_set
        assert dev3 in device_set
        
        # Test as dict key
        device_dict = {dev1: "first", dev3: "second"}
        assert device_dict[dev1] == "first"
        assert device_dict[dev2] == "first"  # Same as dev1
        assert device_dict[dev3] == "second"
    
    def test_device_copy(self):
        """Test Device copy operations."""
        original = Device("Original", "/original/path")
        
        # Shallow copy
        shallow = copy.copy(original)
        assert shallow == original
        assert shallow.name == original.name
        assert shallow.path == original.path
        
        # Deep copy
        deep = copy.deepcopy(original)
        assert deep == original
        assert deep.name == original.name
    
    def test_device_str_representation(self):
        """Test Device.__str__() method."""
        device = Device("HD Pro Webcam", "/dev/video0")
        
        str_repr = str(device)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0
        # String should contain name
        assert "HD Pro Webcam" in str_repr
    
    def test_device_repr_representation(self):
        """Test Device.__repr__() method."""
        device = Device("HD Pro Webcam", "/dev/video0")
        
        repr_str = repr(device)
        assert isinstance(repr_str, str)
        assert "Device" in repr_str
        assert "HD Pro Webcam" in repr_str
        assert "/dev/video0" in repr_str


class TestPropSettingType:
    """Test PropSetting type - property value and control mode."""
    
    def test_propsetting_default_construction(self):
        """Test creating PropSetting with defaults."""
        setting = PropSetting()
        
        assert isinstance(setting, PropSetting)
        assert hasattr(setting, 'value')
        assert hasattr(setting, 'mode')
        # Don't assume specific default values
    
    def test_propsetting_construction_with_value(self):
        """Test creating PropSetting with value only."""
        setting = PropSetting(75)
        
        assert isinstance(setting, PropSetting)
        assert setting.value == 75
        # Mode should default to Manual
        assert setting.mode == CamMode.Manual
    
    def test_propsetting_construction_with_value_and_mode(self):
        """Test creating PropSetting with value and mode."""
        setting = PropSetting(100, CamMode.Auto)
        
        assert setting.value == 100
        assert setting.mode == CamMode.Auto
        
        setting_manual = PropSetting(50, CamMode.Manual)
        assert setting_manual.value == 50
        assert setting_manual.mode == CamMode.Manual
    
    def test_propsetting_value_property_get(self):
        """Test getting PropSetting.value."""
        setting = PropSetting(42, CamMode.Manual)
        
        assert setting.value == 42
        assert isinstance(setting.value, int)
    
    def test_propsetting_value_property_set(self):
        """Test setting PropSetting.value."""
        setting = PropSetting()
        
        setting.value = 123
        assert setting.value == 123
        
        setting.value = -50
        assert setting.value == -50
        
        setting.value = 0
        assert setting.value == 0
    
    def test_propsetting_mode_property_get(self):
        """Test getting PropSetting.mode."""
        auto_setting = PropSetting(0, CamMode.Auto)
        assert auto_setting.mode == CamMode.Auto
        assert isinstance(auto_setting.mode, CamMode)
        
        manual_setting = PropSetting(50, CamMode.Manual)
        assert manual_setting.mode == CamMode.Manual
    
    def test_propsetting_mode_property_set(self):
        """Test setting PropSetting.mode."""
        setting = PropSetting(50, CamMode.Manual)
        
        # Change to Auto
        setting.mode = CamMode.Auto
        assert setting.mode == CamMode.Auto
        
        # Change back to Manual
        setting.mode = CamMode.Manual
        assert setting.mode == CamMode.Manual
    
    def test_propsetting_independent_properties(self):
        """Test value and mode are independent."""
        setting = PropSetting(100, CamMode.Manual)
        
        # Change value, mode stays same
        original_mode = setting.mode
        setting.value = 200
        assert setting.mode == original_mode
        
        # Change mode, value stays same
        original_value = setting.value
        setting.mode = CamMode.Auto
        assert setting.value == original_value
    
    def test_propsetting_copy(self):
        """Test PropSetting copy operations."""
        original = PropSetting(75, CamMode.Auto)
        
        # Shallow copy
        shallow = copy.copy(original)
        assert shallow.value == original.value
        assert shallow.mode == original.mode
        
        # Deep copy
        deep = copy.deepcopy(original)
        assert deep.value == original.value
        assert deep.mode == original.mode
        
        # Modifications don't affect original
        shallow.value = 999
        assert original.value == 75
    
    def test_propsetting_str_representation(self):
        """Test PropSetting.__str__() method."""
        auto_setting = PropSetting(50, CamMode.Auto)
        manual_setting = PropSetting(75, CamMode.Manual)
        
        auto_str = str(auto_setting)
        assert isinstance(auto_str, str)
        assert "50" in auto_str
        assert "Auto" in auto_str
        
        manual_str = str(manual_setting)
        assert "75" in manual_str
        assert "Manual" in manual_str
    
    def test_propsetting_repr_representation(self):
        """Test PropSetting.__repr__() method."""
        setting = PropSetting(100, CamMode.Manual)
        
        repr_str = repr(setting)
        assert isinstance(repr_str, str)
        assert "PropSetting" in repr_str
        assert "100" in repr_str
        assert "Manual" in repr_str


class TestPropRangeType:
    """Test PropRange type - property constraints and validation."""
    
    def test_proprange_default_construction(self):
        """Test creating empty PropRange."""
        prop_range = PropRange()
        
        assert isinstance(prop_range, PropRange)
        assert hasattr(prop_range, 'min')
        assert hasattr(prop_range, 'max')
        assert hasattr(prop_range, 'step')
        assert hasattr(prop_range, 'default_val')
        assert hasattr(prop_range, 'default_mode')
    
    def test_proprange_min_max_properties(self):
        """Test PropRange min and max properties."""
        prop_range = PropRange()
        
        # Set min/max
        prop_range.min = 0
        prop_range.max = 100
        
        assert prop_range.min == 0
        assert prop_range.max == 100
        
        # Test negative values
        prop_range.min = -50
        prop_range.max = 50
        assert prop_range.min == -50
        assert prop_range.max == 50
    
    def test_proprange_step_property(self):
        """Test PropRange step property."""
        prop_range = PropRange()
        
        prop_range.step = 5
        assert prop_range.step == 5
        
        prop_range.step = 1
        assert prop_range.step == 1
        
        # CRITICAL: step must be non-zero to avoid division by zero
        prop_range.step = 10
        assert prop_range.step == 10
    
    def test_proprange_default_val_property(self):
        """Test PropRange default_val property."""
        prop_range = PropRange()
        
        prop_range.default_val = 50
        assert prop_range.default_val == 50
        
        prop_range.default_val = 0
        assert prop_range.default_val == 0
    
    def test_proprange_default_mode_property(self):
        """Test PropRange default_mode property."""
        prop_range = PropRange()
        
        prop_range.default_mode = CamMode.Auto
        assert prop_range.default_mode == CamMode.Auto
        
        prop_range.default_mode = CamMode.Manual
        assert prop_range.default_mode == CamMode.Manual
    
    def test_proprange_is_valid_method(self):
        """Test PropRange.is_valid() method."""
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 100
        prop_range.step = 5
        
        # Valid values
        assert prop_range.is_valid(0)    # min
        assert prop_range.is_valid(50)   # middle
        assert prop_range.is_valid(100)  # max
        assert prop_range.is_valid(25)   # on step boundary
        
        # Invalid values (out of range)
        assert not prop_range.is_valid(-1)   # below min
        assert not prop_range.is_valid(101)  # above max
        assert not prop_range.is_valid(-100) # far below
        assert not prop_range.is_valid(200)  # far above
    
    def test_proprange_is_valid_with_step_alignment(self):
        """Test is_valid() respects step alignment."""
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 100
        prop_range.step = 10
        
        # On step boundaries
        assert prop_range.is_valid(0)
        assert prop_range.is_valid(10)
        assert prop_range.is_valid(50)
        assert prop_range.is_valid(100)
        
        # Between steps (may or may not be valid depending on implementation)
        # Some implementations allow any value in range, others enforce step
        # Just verify method doesn't crash
        result = prop_range.is_valid(5)
        assert isinstance(result, bool)
    
    def test_proprange_clamp_method(self):
        """Test PropRange.clamp() method."""
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 100
        prop_range.step = 1  # CRITICAL: Must be non-zero
        
        # Values in range (unchanged)
        assert prop_range.clamp(50) == 50
        assert prop_range.clamp(0) == 0
        assert prop_range.clamp(100) == 100
        
        # Values below min (clamped to min)
        assert prop_range.clamp(-10) == 0
        assert prop_range.clamp(-1) == 0
        assert prop_range.clamp(-1000) == 0
        
        # Values above max (clamped to max)
        assert prop_range.clamp(150) == 100
        assert prop_range.clamp(101) == 100
        assert prop_range.clamp(9999) == 100
    
    def test_proprange_clamp_with_negative_range(self):
        """Test clamp() with negative range."""
        prop_range = PropRange()
        prop_range.min = -100
        prop_range.max = -10
        prop_range.step = 1
        
        assert prop_range.clamp(-50) == -50
        assert prop_range.clamp(0) == -10     # Above max
        assert prop_range.clamp(-200) == -100 # Below min
    
    def test_proprange_contains_method(self):
        """Test PropRange.__contains__() method (in operator)."""
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 100
        prop_range.step = 1  # CRITICAL: Must be non-zero
        
        # Test 'in' operator
        assert 50 in prop_range
        assert 0 in prop_range
        assert 100 in prop_range
        
        assert -1 not in prop_range
        assert 101 not in prop_range
        assert 1000 not in prop_range
    
    def test_proprange_copy(self):
        """Test PropRange copy operations."""
        original = PropRange()
        original.min = 0
        original.max = 100
        original.step = 5
        original.default_val = 50
        original.default_mode = CamMode.Auto
        
        # Shallow copy
        shallow = copy.copy(original)
        assert shallow.min == original.min
        assert shallow.max == original.max
        assert shallow.step == original.step
        assert shallow.default_val == original.default_val
        assert shallow.default_mode == original.default_mode
        
        # Deep copy
        deep = copy.deepcopy(original)
        assert deep.min == original.min
        assert deep.max == original.max
        
        # Modifications don't affect original
        shallow.min = -100
        assert original.min == 0
    
    def test_proprange_str_representation(self):
        """Test PropRange.__str__() method."""
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 100
        prop_range.step = 5
        
        str_repr = str(prop_range)
        assert isinstance(str_repr, str)
        assert "0" in str_repr  # min
        assert "100" in str_repr  # max
        assert "5" in str_repr  # step
    
    def test_proprange_repr_representation(self):
        """Test PropRange.__repr__() method."""
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 100
        prop_range.step = 1
        prop_range.default_val = 50
        
        repr_str = repr(prop_range)
        assert isinstance(repr_str, str)
        assert "PropRange" in repr_str


class TestPropertyCapabilityType:
    """Test PropertyCapability type - property support information."""
    
    def test_propertycapability_construction(self):
        """Test PropertyCapability can be created."""
        cap = PropertyCapability()
        
        assert isinstance(cap, PropertyCapability)
        assert hasattr(cap, 'supported')
        assert hasattr(cap, 'range')
        assert hasattr(cap, 'current')
    
    def test_propertycapability_supported_property(self):
        """Test PropertyCapability.supported property."""
        cap = PropertyCapability()
        
        # Should be able to set supported flag
        cap.supported = True
        assert cap.supported == True
        
        cap.supported = False
        assert cap.supported == False
    
    def test_propertycapability_range_property(self):
        """Test PropertyCapability.range property."""
        cap = PropertyCapability()
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 100
        prop_range.step = 1
        
        cap.range = prop_range
        assert isinstance(cap.range, PropRange)
        assert cap.range.min == 0
        assert cap.range.max == 100
    
    def test_propertycapability_current_property(self):
        """Test PropertyCapability.current property."""
        cap = PropertyCapability()
        setting = PropSetting(50, CamMode.Manual)
        
        cap.current = setting
        assert isinstance(cap.current, PropSetting)
        assert cap.current.value == 50
        assert cap.current.mode == CamMode.Manual
    
    def test_propertycapability_supports_auto_method(self):
        """Test PropertyCapability.supports_auto() method."""
        cap = PropertyCapability()
        
        # Test method exists and returns bool
        result = cap.supports_auto()
        assert isinstance(result, bool)


class TestErrorInfoType:
    """
    Test ErrorInfo type - Low-level error information from C++ bindings.
    """

    def test_errorinfo_construction_with_errorcode(self):
        """Test creating ErrorInfo with ErrorCode and message."""
        error = ErrorInfo(ErrorCode.DeviceNotFound, "Device not available")
        assert isinstance(error, ErrorInfo)
        assert error.code() == ErrorCode.DeviceNotFound
        assert isinstance(error.message(), str)
        assert "Device not available" in error.message()

    def test_errorinfo_code_method(self):
        """Test ErrorInfo.code() method."""
        error = ErrorInfo(ErrorCode.PropertyNotSupported, "Property not supported")
        code = error.code()
        assert isinstance(code, ErrorCode)
        assert code == ErrorCode.PropertyNotSupported

    def test_errorinfo_message_method(self):
        """Test ErrorInfo.message() method."""
        error = ErrorInfo(ErrorCode.InvalidValue, "Value out of range")
        message = error.message()
        assert isinstance(message, str)
        assert len(message) > 0
        assert "Value out of range" in message

    def test_errorinfo_description_method(self):
        """Test ErrorInfo.description() method."""
        error = ErrorInfo(ErrorCode.SystemError, "System call failed")
        description = error.description()
        assert isinstance(description, str)
        assert len(description) > 0

    def test_errorinfo_different_codes(self):
        """Test ErrorInfo with various ErrorCode values."""
        error_codes = [
            (ErrorCode.Success, "Operation succeeded"),
            (ErrorCode.DeviceNotFound, "Device not found"),
            (ErrorCode.DeviceBusy, "Device is busy"),
            (ErrorCode.PropertyNotSupported, "Property not supported"),
            (ErrorCode.InvalidValue, "Invalid value"),
            (ErrorCode.PermissionDenied, "Permission denied"),
            (ErrorCode.InvalidArgument, "Invalid argument"),
        ]
        for code, msg in error_codes:
            error = ErrorInfo(code, msg)
            assert error.code() == code
            assert isinstance(error.message(), str)

    def test_errorinfo_str_representation(self):
        """Test ErrorInfo.__str__() method."""
        error = ErrorInfo(ErrorCode.DeviceNotFound, "Camera disconnected")
        str_repr = str(error)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0
        assert "disconnected" in str_repr.lower() or "camera" in str_repr.lower()

    def test_errorinfo_repr_representation(self):
        """Test ErrorInfo.__repr__() method."""
        error = ErrorInfo(ErrorCode.InvalidValue, "Value too high")
        repr_str = repr(error)
        assert isinstance(repr_str, str)
        assert "ErrorInfo" in repr_str


class TestDeviceCapabilitiesType:
    """Test DeviceCapabilities type - device capability snapshot."""
    
    def test_devicecapabilities_construction_requires_device(self):
        """Test DeviceCapabilities construction requires Device."""
        # DeviceCapabilities requires a valid device
        # We test the interface, actual functionality tested with hardware
        device = Device("Test", "/test/path")
        
        # Construction may fail if device not accessible
        # This is expected behavior - we just test the interface exists
        assert hasattr(DeviceCapabilities, '__init__')
    
    def test_devicecapabilities_has_required_methods(self):
        """Test DeviceCapabilities has all required methods."""
        # Verify method existence (interface check)
        required_methods = [
            'get_camera_capability',
            'get_video_capability',
            'supports_camera_property',
            'supports_video_property',
            'supported_camera_properties',
            'supported_video_properties',
            'device',
            'is_device_accessible',
            'refresh',
        ]
        
        for method_name in required_methods:
            assert hasattr(DeviceCapabilities, method_name), \
                f"DeviceCapabilities missing method: {method_name}"


# ============================================================================
# WITH CAMERA TESTS - Integration tests using real camera
# ============================================================================

@pytest.mark.hardware
class TestDeviceWithCamera:
    """Test Device type with real camera hardware."""
    
    def test_device_from_list_devices(self, available_devices):
        """Test Device objects from list_devices()."""
        if not available_devices:
            pytest.skip("No devices available")
        
        for device in available_devices:
            # All devices should be valid
            assert isinstance(device, Device)
            assert device.is_valid()
            
            # All devices should have name and path
            assert isinstance(device.name, str)
            assert len(device.name) > 0
            assert isinstance(device.path, str)
            assert len(device.path) > 0
            
            # Device ID should be consistent
            id1 = device.get_id()
            id2 = device.get_id()
            assert id1 == id2
    
    def test_device_with_camera_operations(self, test_device, test_camera):
        """Test Device used with Camera operations."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        # Get device from camera
        camera_device = test_camera.device
        
        assert isinstance(camera_device, Device)
        assert camera_device.is_valid()
        
        # Should match original device
        assert camera_device == test_device

@pytest.mark.hardware
class TestPropSettingWithCamera:
    """Test PropSetting with real camera hardware."""
    
    def test_propsetting_from_camera_get(self, test_camera):
        """Test PropSetting returned by camera.get()."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        from duvc_ctl import get_device_capabilities
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_vid_props = caps.supported_video_properties()
        
        # Try to get a video property
        if VidProp.Brightness in supported_vid_props:
            result = test_camera.get(VidProp.Brightness)
            
            if result.is_ok():
                setting = result.value()
                
                assert isinstance(setting, PropSetting)
                assert isinstance(setting.value, int)
                assert isinstance(setting.mode, CamMode)
                assert setting.mode in [CamMode.Auto, CamMode.Manual]
    
    def test_propsetting_used_for_camera_set(self, test_camera):
        """Test using PropSetting to set camera property."""
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
            # Get current value
            get_result = test_camera.get(VidProp.Brightness)
            if not get_result.is_ok():
                pytest.skip("Could not read brightness")
            
            current = get_result.value()
            
            # Create new setting
            new_setting = PropSetting(current.value, CamMode.Manual)
            
            # Set it back
            set_result = test_camera.set(VidProp.Brightness, new_setting)
            
            # Should succeed or fail gracefully
            assert hasattr(set_result, 'is_ok')
            assert isinstance(set_result.is_ok(), bool)


@pytest.mark.hardware
class TestPropRangeWithCamera:
    """Test PropRange with real camera hardware."""
    
    def test_proprange_from_camera_get_range(self, test_camera):
        """Test PropRange returned by camera.get_range()."""
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
            range_result = test_camera.get_range(VidProp.Brightness)
            
            if range_result.is_ok():
                prop_range = range_result.value()
                
                assert isinstance(prop_range, PropRange)
                assert isinstance(prop_range.min, int)
                assert isinstance(prop_range.max, int)
                assert isinstance(prop_range.step, int)
                assert isinstance(prop_range.default_val, int)
                assert isinstance(prop_range.default_mode, CamMode)
                
                # Range should be valid
                assert prop_range.min <= prop_range.max
                assert prop_range.step > 0  # Must be positive
                assert prop_range.min <= prop_range.default_val <= prop_range.max
    
    def test_proprange_validation_with_real_values(self, test_camera):
        """Test PropRange validation methods with real camera values."""
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
            range_result = test_camera.get_range(VidProp.Brightness)
            
            if range_result.is_ok():
                prop_range = range_result.value()
                
                # Test is_valid with range boundaries
                assert prop_range.is_valid(prop_range.min)
                assert prop_range.is_valid(prop_range.max)
                assert prop_range.is_valid(prop_range.default_val)
                
                # Test clamping
                below_min = prop_range.min - 100
                above_max = prop_range.max + 100
                
                assert prop_range.clamp(below_min) == prop_range.min
                assert prop_range.clamp(above_max) == prop_range.max


@pytest.mark.hardware
class TestDeviceCapabilitiesWithCamera:
    """Test DeviceCapabilities with real camera hardware."""
    
    def test_devicecapabilities_from_device(self, test_device):
        """Test creating DeviceCapabilities from Device."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_capabilities(test_device)
        
        if not result.is_ok():
            pytest.skip(f"Could not get capabilities: {result.error().description()}")
        
        caps = result.value()
        
        assert isinstance(caps, DeviceCapabilities)
    
    def test_devicecapabilities_supported_properties(self, test_device):
        """Test getting supported properties lists."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_capabilities(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = result.value()
        
        # Get supported camera properties
        cam_props = caps.supported_camera_properties()
        assert isinstance(cam_props, list)
        for prop in cam_props:
            assert isinstance(prop, CamProp)
        
        # Get supported video properties
        vid_props = caps.supported_video_properties()
        assert isinstance(vid_props, list)
        for prop in vid_props:
            assert isinstance(prop, VidProp)
    
    def test_devicecapabilities_supports_property_methods(self, test_device):
        """Test supports_camera_property and supports_video_property."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_capabilities(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = result.value()
        
        # Test supports methods return bool
        cam_supported = caps.supports_camera_property(CamProp.Pan)
        assert isinstance(cam_supported, bool)
        
        vid_supported = caps.supports_video_property(VidProp.Brightness)
        assert isinstance(vid_supported, bool)
        
        # Consistency check
        cam_props = caps.supported_camera_properties()
        if CamProp.Pan in cam_props:
            assert caps.supports_camera_property(CamProp.Pan)
    
    def test_devicecapabilities_get_capability_methods(self, test_device):
        """Test get_camera_capability and get_video_capability."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_capabilities(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = result.value()
        
        # Get camera property capability
        cam_props = caps.supported_camera_properties()
        if cam_props:
            cap = caps.get_camera_capability(cam_props[0])
            assert isinstance(cap, PropertyCapability)
        
        # Get video property capability
        vid_props = caps.supported_video_properties()
        if vid_props:
            cap = caps.get_video_capability(vid_props[0])
            assert isinstance(cap, PropertyCapability)
    
    def test_devicecapabilities_device_method(self, test_device):
        """Test DeviceCapabilities.device() method."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_capabilities(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = result.value()
        
        device = caps.device
        assert isinstance(device, Device)
        assert device == test_device
    
    def test_devicecapabilities_is_device_accessible(self, test_device):
        """Test DeviceCapabilities.is_device_accessible() method."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_capabilities(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = result.value()
        
        is_accessible = caps.is_device_accessible()
        assert isinstance(is_accessible, bool)
        # If we got capabilities, device should be accessible
        assert is_accessible


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
