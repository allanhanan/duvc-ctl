"""
Test Suite 01: Core Enums
==========================

Tests all enum types exposed by duvc-ctl Python bindings.

Enums Tested:
  - CamProp (23 values) - Camera control properties
  - VidProp (10 values) - Video processing properties
  - CamMode (2 values) - Auto/Manual control modes
  - ErrorCode (9 values) - Operation result codes
  - LogLevel (5 values) - Logging severity levels

Total: 49 enum values across 5 enum types

Test Organization:
  1. Without Camera Tests - Unit tests on enum types (no hardware required)
  2. With Camera Tests - Integration tests using real camera devices

Run: pytest tests/test_01_core_enums.py -v
Run without camera: pytest tests/test_01_core_enums.py -v -m "not hardware"
"""

import pytest
import sys
from typing import List, Optional
import faulthandler
faulthandler.enable()
import time

import duvc_ctl
from duvc_ctl import (
    # Core enums
    CamProp, VidProp, CamMode, ErrorCode, LogLevel,
    # Core functions needed for tests
    list_devices, open_camera, to_string,
    Device, Camera, CameraResult,
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


# ============================================================================
# WITHOUT CAMERA TESTS - Unit tests on enum types
# ============================================================================

class TestCamPropEnum:
    """Test CamProp enum - IAMCameraControl properties."""
    
    def test_all_camprop_values_exist(self):
        """Verify all 23 expected CamProp enum values are exposed."""
        # From pybind_module.cpp lines exposing CamProp enum
        expected_props = [
            'Pan', 'Tilt', 'Roll', 'Zoom', 'Exposure', 'Iris', 'Focus',
            'ScanMode', 'Privacy', 
            'PanRelative', 'TiltRelative', 'RollRelative',
            'ZoomRelative', 'ExposureRelative', 'IrisRelative', 'FocusRelative',
            'PanTilt', 'PanTiltRelative', 'FocusSimple', 
            'DigitalZoom', 'DigitalZoomRelative', 
            'BacklightCompensation', 'Lamp'
        ]
        
        assert len(expected_props) == 23, "Expected 23 CamProp values"
        
        for prop_name in expected_props:
            assert hasattr(CamProp, prop_name), f"CamProp.{prop_name} not found"
            prop = getattr(CamProp, prop_name)
            assert isinstance(prop, CamProp), f"CamProp.{prop_name} is not a CamProp instance"
    
    def test_camprop_types(self):
        """Test CamProp values are correct type."""
        assert isinstance(CamProp.Pan, CamProp)
        assert isinstance(CamProp.Tilt, CamProp)
        assert isinstance(CamProp.Zoom, CamProp)
        assert isinstance(CamProp.Focus, CamProp)
        assert isinstance(CamProp.Exposure, CamProp)
    
    def test_camprop_equality(self):
        """Test CamProp enum values are comparable."""
        pan1 = CamProp.Pan
        pan2 = CamProp.Pan
        tilt = CamProp.Tilt
        
        # Same values should be equal
        assert pan1 == pan2
        assert pan1 == CamProp.Pan
        
        # Different values should be unequal
        assert pan1 != tilt
        assert CamProp.Pan != CamProp.Tilt
    
    def test_camprop_hashable(self):
        """Test CamProp enum values can be used in sets and dicts."""
        # Can create set of props
        prop_set = {CamProp.Pan, CamProp.Tilt, CamProp.Zoom, CamProp.Pan}
        assert len(prop_set) == 3  # Pan appears twice but set has 3 unique
        assert CamProp.Pan in prop_set
        assert CamProp.Tilt in prop_set
        assert CamProp.Zoom in prop_set
        
        # Can use as dict keys
        prop_dict = {
            CamProp.Pan: "pan",
            CamProp.Tilt: "tilt",
            CamProp.Zoom: "zoom"
        }
        assert prop_dict[CamProp.Pan] == "pan"
        assert prop_dict[CamProp.Tilt] == "tilt"
        assert len(prop_dict) == 3
    
    def test_camprop_absolute_vs_relative(self):
        """Test distinction between absolute and relative properties."""
        # Absolute properties
        absolute_props = [
            CamProp.Pan, CamProp.Tilt, CamProp.Roll, CamProp.Zoom,
            CamProp.Exposure, CamProp.Iris, CamProp.Focus
        ]
        
        # Relative properties
        relative_props = [
            CamProp.PanRelative, CamProp.TiltRelative, CamProp.RollRelative,
            CamProp.ZoomRelative, CamProp.ExposureRelative, 
            CamProp.IrisRelative, CamProp.FocusRelative
        ]
        
        # Verify all absolute props exist
        for prop in absolute_props:
            assert isinstance(prop, CamProp)
        
        # Verify all relative props exist
        for prop in relative_props:
            assert isinstance(prop, CamProp)
        
        # Absolute and relative should be different
        assert CamProp.Pan != CamProp.PanRelative
        assert CamProp.Zoom != CamProp.ZoomRelative
    
    def test_camprop_combined_properties(self):
        """Test combined properties like PanTilt."""
        # Combined properties
        assert isinstance(CamProp.PanTilt, CamProp)
        assert isinstance(CamProp.PanTiltRelative, CamProp)
        
        # Should be distinct from individual props
        assert CamProp.PanTilt != CamProp.Pan
        assert CamProp.PanTilt != CamProp.Tilt
    
    def test_camprop_special_properties(self):
        """Test special properties like Privacy, Lamp, etc."""
        special_props = [
            CamProp.ScanMode,
            CamProp.Privacy,
            CamProp.FocusSimple,
            CamProp.DigitalZoom,
            CamProp.DigitalZoomRelative,
            CamProp.BacklightCompensation,
            CamProp.Lamp
        ]
        
        for prop in special_props:
            assert isinstance(prop, CamProp)


class TestVidPropEnum:
    """Test VidProp enum - IAMVideoProcAmp properties."""
    
    def test_all_vidprop_values_exist(self):
        """Verify all 10 expected VidProp enum values are exposed."""
        # From pybind_module.cpp lines exposing VidProp enum
        expected_props = [
            'Brightness', 'Contrast', 'Hue', 'Saturation', 'Sharpness',
            'Gamma', 'ColorEnable', 'WhiteBalance', 
            'BacklightCompensation', 'Gain'
        ]
        
        assert len(expected_props) == 10, "Expected 10 VidProp values"
        
        for prop_name in expected_props:
            assert hasattr(VidProp, prop_name), f"VidProp.{prop_name} not found"
            prop = getattr(VidProp, prop_name)
            assert isinstance(prop, VidProp), f"VidProp.{prop_name} is not a VidProp instance"
    
    def test_vidprop_types(self):
        """Test VidProp values are correct type."""
        assert isinstance(VidProp.Brightness, VidProp)
        assert isinstance(VidProp.Contrast, VidProp)
        assert isinstance(VidProp.Hue, VidProp)
        assert isinstance(VidProp.Saturation, VidProp)
        assert isinstance(VidProp.WhiteBalance, VidProp)
    
    def test_vidprop_equality(self):
        """Test VidProp enum values are comparable."""
        brightness1 = VidProp.Brightness
        brightness2 = VidProp.Brightness
        contrast = VidProp.Contrast
        
        # Same values should be equal
        assert brightness1 == brightness2
        assert brightness1 == VidProp.Brightness
        
        # Different values should be unequal
        assert brightness1 != contrast
        assert VidProp.Brightness != VidProp.Contrast
    
    def test_vidprop_hashable(self):
        """Test VidProp enum values can be used in sets and dicts."""
        prop_set = {VidProp.Brightness, VidProp.Contrast, VidProp.Saturation}
        assert len(prop_set) == 3
        assert VidProp.Brightness in prop_set
        
        prop_dict = {VidProp.Brightness: 50, VidProp.Contrast: 60}
        assert prop_dict[VidProp.Brightness] == 50
    
    def test_vidprop_distinct_from_camprop(self):
        """Test VidProp and CamProp are distinct types."""
        # Type check
        assert type(VidProp.Brightness).__name__ == 'VidProp'
        assert type(CamProp.Pan).__name__ == 'CamProp'
        
        # Cannot compare across types (should be False, not error)
        # Note: pybind11 enum comparison returns False for different types
        assert VidProp.Brightness != CamProp.Pan
    
    def test_vidprop_color_properties(self):
        """Test color-related properties."""
        color_props = [
            VidProp.Hue,
            VidProp.Saturation,
            VidProp.ColorEnable,
            VidProp.WhiteBalance,
            VidProp.Gamma
        ]
        
        for prop in color_props:
            assert isinstance(prop, VidProp)
    
    def test_vidprop_exposure_properties(self):
        """Test exposure/gain related properties."""
        exposure_props = [
            VidProp.Brightness,
            VidProp.BacklightCompensation,
            VidProp.Gain
        ]
        
        for prop in exposure_props:
            assert isinstance(prop, VidProp)


class TestCamModeEnum:
    """Test CamMode enum - property control mode."""
    
    def test_cammode_auto_exists(self):
        """Test CamMode.Auto enum value exists."""
        assert hasattr(CamMode, 'Auto')
        auto = CamMode.Auto
        assert isinstance(auto, CamMode)
        assert auto == CamMode.Auto
    
    def test_cammode_manual_exists(self):
        """Test CamMode.Manual enum value exists."""
        assert hasattr(CamMode, 'Manual')
        manual = CamMode.Manual
        assert isinstance(manual, CamMode)
        assert manual == CamMode.Manual
    
    def test_cammode_only_two_values(self):
        """Test CamMode has exactly 2 values."""
        # Collect all CamMode attributes
        mode_attrs = [attr for attr in dir(CamMode) if not attr.startswith('_')]
        cam_modes = [getattr(CamMode, attr) for attr in mode_attrs if isinstance(getattr(CamMode, attr), CamMode)]
        
        assert len(cam_modes) == 2, f"Expected 2 CamMode values, found {len(cam_modes)}"
    
    def test_cammode_distinct(self):
        """Test CamMode.Auto and CamMode.Manual are distinct."""
        assert CamMode.Auto != CamMode.Manual
        
        # Both should be hashable
        modes = {CamMode.Auto, CamMode.Manual}
        assert len(modes) == 2
    
    def test_cammode_equality(self):
        """Test CamMode equality."""
        auto1 = CamMode.Auto
        auto2 = CamMode.Auto
        manual = CamMode.Manual
        
        assert auto1 == auto2
        assert auto1 != manual
    
    def test_cammode_hashable(self):
        """Test CamMode values are hashable."""
        mode_dict = {CamMode.Auto: "automatic", CamMode.Manual: "manual"}
        assert mode_dict[CamMode.Auto] == "automatic"
        assert mode_dict[CamMode.Manual] == "manual"


class TestErrorCodeEnum:
    """Test ErrorCode enum - operation result codes."""
    
    def test_all_errorcode_values_exist(self):
        """Verify all 9 expected ErrorCode enum values are exposed."""
        # From pybind_module.cpp lines exposing ErrorCode enum
        expected_codes = [
            'Success', 
            'DeviceNotFound', 'DeviceBusy', 
            'PropertyNotSupported', 'InvalidValue',
            'PermissionDenied', 'SystemError',
            'InvalidArgument', 'NotImplemented'
        ]
        
        assert len(expected_codes) == 9, "Expected 9 ErrorCode values"
        
        for code_name in expected_codes:
            assert hasattr(ErrorCode, code_name), f"ErrorCode.{code_name} not found"
            code = getattr(ErrorCode, code_name)
            assert isinstance(code, ErrorCode), f"ErrorCode.{code_name} is not an ErrorCode instance"
    
    def test_errorcode_success(self):
        """Test ErrorCode.Success enum value."""
        assert hasattr(ErrorCode, 'Success')
        success = ErrorCode.Success
        assert isinstance(success, ErrorCode)
        assert success == ErrorCode.Success
    
    def test_errorcode_device_errors(self):
        """Test device-related error codes."""
        device_errors = [
            ErrorCode.DeviceNotFound,
            ErrorCode.DeviceBusy,
            ErrorCode.PermissionDenied
        ]
        
        for err in device_errors:
            assert isinstance(err, ErrorCode)
        
        # All should be distinct
        assert len(set(device_errors)) == 3
    
    def test_errorcode_property_errors(self):
        """Test property-related error codes."""
        property_errors = [
            ErrorCode.PropertyNotSupported,
            ErrorCode.InvalidValue,
            ErrorCode.InvalidArgument
        ]
        
        for err in property_errors:
            assert isinstance(err, ErrorCode)
    
    def test_errorcode_system_errors(self):
        """Test system-level error codes."""
        system_errors = [
            ErrorCode.SystemError,
            ErrorCode.NotImplemented
        ]
        
        for err in system_errors:
            assert isinstance(err, ErrorCode)
    
    def test_errorcode_equality(self):
        """Test ErrorCode enum values are comparable."""
        success1 = ErrorCode.Success
        success2 = ErrorCode.Success
        not_found = ErrorCode.DeviceNotFound
        
        assert success1 == success2
        assert success1 != not_found
        assert ErrorCode.Success != ErrorCode.DeviceNotFound
    
    def test_errorcode_hashable(self):
        """Test ErrorCode values can be used in sets and dicts."""
        error_set = {ErrorCode.Success, ErrorCode.DeviceNotFound, ErrorCode.InvalidValue}
        assert len(error_set) == 3
        
        error_dict = {
            ErrorCode.Success: "Operation succeeded",
            ErrorCode.DeviceNotFound: "Device not found"
        }
        assert error_dict[ErrorCode.Success] == "Operation succeeded"


class TestLogLevelEnum:
    """Test LogLevel enum - logging severity levels."""
    
    def test_all_loglevel_values_exist(self):
        """Verify all 5 expected LogLevel enum values are exposed."""
        # From pybind_module.cpp lines exposing LogLevel enum
        expected_levels = ['Debug', 'Info', 'Warning', 'Error', 'Critical']
        
        assert len(expected_levels) == 5, "Expected 5 LogLevel values"
        
        for level_name in expected_levels:
            assert hasattr(LogLevel, level_name), f"LogLevel.{level_name} not found"
            level = getattr(LogLevel, level_name)
            assert isinstance(level, LogLevel), f"LogLevel.{level_name} is not a LogLevel instance"
    
    def test_loglevel_types(self):
        """Test LogLevel values are correct type."""
        assert isinstance(LogLevel.Debug, LogLevel)
        assert isinstance(LogLevel.Info, LogLevel)
        assert isinstance(LogLevel.Warning, LogLevel)
        assert isinstance(LogLevel.Error, LogLevel)
        assert isinstance(LogLevel.Critical, LogLevel)
    
    def test_loglevel_distinct(self):
        """Test LogLevel enum values are all distinct."""
        levels = [
            LogLevel.Debug, LogLevel.Info, LogLevel.Warning,
            LogLevel.Error, LogLevel.Critical
        ]
        
        # All should be distinct
        assert len(set(levels)) == 5
        
        # Test some specific inequalities
        assert LogLevel.Debug != LogLevel.Info
        assert LogLevel.Info != LogLevel.Warning
        assert LogLevel.Warning != LogLevel.Error
        assert LogLevel.Error != LogLevel.Critical
    
    def test_loglevel_equality(self):
        """Test LogLevel equality."""
        debug1 = LogLevel.Debug
        debug2 = LogLevel.Debug
        info = LogLevel.Info
        
        assert debug1 == debug2
        assert debug1 != info
    
    def test_loglevel_hashable(self):
        """Test LogLevel values are hashable."""
        level_set = {LogLevel.Debug, LogLevel.Info, LogLevel.Error}
        assert len(level_set) == 3
        
        level_dict = {
            LogLevel.Debug: "debug",
            LogLevel.Info: "info",
            LogLevel.Error: "error"
        }
        assert level_dict[LogLevel.Debug] == "debug"


class TestEnumStringConversion:
    """Test to_string() conversion for all enum types."""
    
    def test_tostring_camprop_all_values(self):
        """Test to_string() for all CamProp values."""
        cam_props = [
            CamProp.Pan, CamProp.Tilt, CamProp.Roll, CamProp.Zoom,
            CamProp.Exposure, CamProp.Iris, CamProp.Focus,
            CamProp.ScanMode, CamProp.Privacy,
            CamProp.PanRelative, CamProp.TiltRelative,
            CamProp.BacklightCompensation, CamProp.Lamp
        ]
        
        for prop in cam_props:
            result = to_string(prop)
            assert isinstance(result, str)
            assert len(result) > 0, f"to_string({prop}) returned empty string"
    
    def test_tostring_vidprop_all_values(self):
        """Test to_string() for all VidProp values."""
        vid_props = [
            VidProp.Brightness, VidProp.Contrast, VidProp.Hue,
            VidProp.Saturation, VidProp.Sharpness, VidProp.Gamma,
            VidProp.ColorEnable, VidProp.WhiteBalance,
            VidProp.BacklightCompensation, VidProp.Gain
        ]
        
        for prop in vid_props:
            result = to_string(prop)
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_tostring_camprop_unique(self):
        """Test to_string() returns unique strings for different CamProp values."""
        pan_str = to_string(CamProp.Pan)
        tilt_str = to_string(CamProp.Tilt)
        zoom_str = to_string(CamProp.Zoom)
        
        # Each property should have unique string
        assert pan_str != tilt_str
        assert pan_str != zoom_str
        assert tilt_str != zoom_str
    
    def test_tostring_vidprop_unique(self):
        """Test to_string() returns unique strings for different VidProp values."""
        brightness_str = to_string(VidProp.Brightness)
        contrast_str = to_string(VidProp.Contrast)
        
        assert brightness_str != contrast_str
    
    def test_tostring_cammode(self):
        """Test to_string() for CamMode values."""
        auto_str = to_string(CamMode.Auto)
        manual_str = to_string(CamMode.Manual)
        
        assert isinstance(auto_str, str)
        assert isinstance(manual_str, str)
        assert len(auto_str) > 0
        assert len(manual_str) > 0
        assert auto_str != manual_str
    
    def test_tostring_errorcode(self):
        """Test to_string() for ErrorCode values."""
        success_str = to_string(ErrorCode.Success)
        not_found_str = to_string(ErrorCode.DeviceNotFound)
        
        assert isinstance(success_str, str)
        assert isinstance(not_found_str, str)
        assert success_str != not_found_str
    
    def test_tostring_loglevel(self):
        """Test to_string() for LogLevel values."""
        debug_str = to_string(LogLevel.Debug)
        info_str = to_string(LogLevel.Info)
        error_str = to_string(LogLevel.Error)
        
        assert isinstance(debug_str, str)
        assert isinstance(info_str, str)
        assert isinstance(error_str, str)
        
        # All should be distinct
        assert debug_str != info_str
        assert info_str != error_str


class TestEnumCollections:
    """Test enum usage in Python collections."""
    
    def test_camprop_in_list(self):
        """Test CamProp values work in lists."""
        props = [CamProp.Pan, CamProp.Tilt, CamProp.Zoom]
        
        assert CamProp.Pan in props
        assert CamProp.Focus not in props
        assert len(props) == 3
        
        # Can iterate
        for prop in props:
            assert isinstance(prop, CamProp)
    
    def test_vidprop_in_list(self):
        """Test VidProp values work in lists."""
        props = [VidProp.Brightness, VidProp.Contrast]
        
        assert VidProp.Brightness in props
        assert VidProp.Saturation not in props
    
    def test_mixed_enum_types_in_collections(self):
        """Test different enum types can coexist in collections."""
        # Can store different enum types (as objects)
        mixed_list = [CamProp.Pan, VidProp.Brightness, CamMode.Auto]
        
        assert len(mixed_list) == 3
        assert isinstance(mixed_list[0], CamProp)
        assert isinstance(mixed_list[1], VidProp)
        assert isinstance(mixed_list[2], CamMode)
    
    def test_enum_dict_mapping(self):
        """Test enums as dict keys with mixed values."""
        config = {
            CamProp.Pan: 0,
            CamProp.Tilt: 0,
            VidProp.Brightness: 50,
            VidProp.Contrast: 60,
            CamMode.Auto: True
        }
        
        assert config[CamProp.Pan] == 0
        assert config[VidProp.Brightness] == 50
        assert config[CamMode.Auto] == True


# ============================================================================
# WITH CAMERA TESTS - Integration tests using real camera
# ============================================================================

@pytest.mark.hardware
class TestEnumsWithCamera:
    """Test enum usage with real camera hardware."""
    
    def test_camprop_supported_properties(self, test_camera):
        """Test which CamProp values are actually supported by camera."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        from duvc_ctl import get_device_capabilities
        
        # Get device from camera
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip(f"Could not get capabilities: {caps_result.error().description()}")
        
        caps = caps_result.value()
        supported_cam_props = caps.supported_camera_properties()
        
        # Should return list of CamProp enums
        assert isinstance(supported_cam_props, list)
        
        for prop in supported_cam_props:
            assert isinstance(prop, CamProp)
            
            # Test we can convert supported props to strings
            prop_str = to_string(prop)
            assert isinstance(prop_str, str)
            assert len(prop_str) > 0
    
    def test_vidprop_supported_properties(self, test_camera):
        """Test which VidProp values are actually supported by camera."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        from duvc_ctl import get_device_capabilities
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip(f"Could not get capabilities: {caps_result.error().description()}")
        
        caps = caps_result.value()
        supported_vid_props = caps.supported_video_properties()
        
        # Should return list of VidProp enums
        assert isinstance(supported_vid_props, list)
        
        for prop in supported_vid_props:
            assert isinstance(prop, VidProp)
            
            # Test we can convert supported props to strings
            prop_str = to_string(prop)
            assert isinstance(prop_str, str)
    
    def test_get_property_with_enum(self, test_camera):
        """Test getting property using enum values."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        from duvc_ctl import get_device_capabilities
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_vid_props = caps.supported_video_properties()
        
        # Try to get brightness if supported
        if VidProp.Brightness in supported_vid_props:
            result = test_camera.get(VidProp.Brightness)
            
            if result.is_ok():
                setting = result.value()
                # Verify mode is an enum
                assert isinstance(setting.mode, CamMode)
                assert setting.mode in [CamMode.Auto, CamMode.Manual]
    
    def test_set_property_with_enum_and_mode(self, test_camera):
        """Test setting property with enum and mode."""
        if test_camera is None:
            pytest.skip("No camera available")
        
        from duvc_ctl import get_device_capabilities, PropSetting
        
        device = test_camera.device
        caps_result = get_device_capabilities(device)
        
        if not caps_result.is_ok():
            pytest.skip("Could not get capabilities")
        
        caps = caps_result.value()
        supported_vid_props = caps.supported_video_properties()
        
        if VidProp.Brightness in supported_vid_props:
            # Get range first
            range_result = test_camera.get_range(VidProp.Brightness)
            
            if range_result.is_ok():
                prop_range = range_result.value()
                
                # Set to middle of range with Manual mode
                mid_value = (prop_range.min + prop_range.max) // 2
                setting = PropSetting(mid_value, CamMode.Manual)
                
                set_result = test_camera.set(VidProp.Brightness, setting)
                
                # Check result used enum types correctly
                if not set_result.is_ok():
                    error = set_result.error()
                    assert isinstance(error.code(), ErrorCode)


class TestEnumEdgeCases:
    """Test edge cases and unusual enum usage."""
    
    def test_enum_identity(self):
        """Test enum value identity."""
        # Same enum value should be identical object
        pan1 = CamProp.Pan
        pan2 = CamProp.Pan
        
        # Should be same object (identity, not just equality)
        assert pan1 is pan2
    
    def test_enum_cannot_be_instantiated(self):
        """Test that enum types cannot be instantiated directly."""
        # pybind11 enums typically don't allow direct instantiation
        # This is a sanity check that our enums follow this pattern
        with pytest.raises((TypeError, AttributeError)):
            CamProp()  # Should fail
    
    def test_enum_repr_is_meaningful(self):
        """Test enum repr is meaningful."""
        pan_repr = repr(CamProp.Pan)
        assert isinstance(pan_repr, str)
        assert len(pan_repr) > 0
        # repr should contain some identifying information
        # (exact format may vary by pybind11 version)
    
    def test_enum_str_conversion(self):
        """Test enum str conversion."""
        pan_str = str(CamProp.Pan)
        assert isinstance(pan_str, str)
        assert len(pan_str) > 0


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
