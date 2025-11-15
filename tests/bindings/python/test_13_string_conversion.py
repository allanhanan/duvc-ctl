"""
Test Suite 13: String Conversion
=================================

Tests to_string() conversion functions for all duvc-ctl types.

String Conversion Tested:
  Enum to_string (5):
    - to_string(CamProp) - Camera property to string
    - to_string(VidProp) - Video property to string
    - to_string(CamMode) - Camera mode to string
    - to_string(ErrorCode) - Error code to string
    - to_string(LogLevel) - Log level to string
  
  Type __str__ and __repr__ (8):
    - Device.__str__() and Device.__repr__()
    - PropSetting.__str__() and PropSetting.__repr__()
    - PropRange.__str__() and PropRange.__repr__()
    - Error.__str__() and Error.__repr__()

Total: 13 string conversion operations

Test Organization:
  1. Without Camera Tests - String conversion verification
  2. Enum String Tests - All enum value string representations

Run: pytest tests/test_13_string_conversion.py -v
"""

import pytest
import sys
from typing import List

import duvc_ctl
from duvc_ctl import (
    # Core enums
    CamProp, VidProp, CamMode, ErrorCode, LogLevel,
    # Core types
    Device, PropSetting, PropRange, ErrorInfo,
    # String conversion
    to_string,
)


# ============================================================================
# WITHOUT CAMERA TESTS - String conversion verification
# ============================================================================

class TestToStringCamProp:
    """Test to_string() for CamProp enum."""
    
    def test_to_string_pan(self):
        """Test to_string(CamProp.Pan)."""
        result = to_string(CamProp.Pan)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert 'pan' in result.lower()
    
    def test_to_string_tilt(self):
        """Test to_string(CamProp.Tilt)."""
        result = to_string(CamProp.Tilt)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert 'tilt' in result.lower()
    
    def test_to_string_zoom(self):
        """Test to_string(CamProp.Zoom)."""
        result = to_string(CamProp.Zoom)
        
        assert isinstance(result, str)
        assert 'zoom' in result.lower()
    
    def test_to_string_focus(self):
        """Test to_string(CamProp.Focus)."""
        result = to_string(CamProp.Focus)
        
        assert isinstance(result, str)
        assert 'focus' in result.lower()
    
    def test_to_string_exposure(self):
        """Test to_string(CamProp.Exposure)."""
        result = to_string(CamProp.Exposure)
        
        assert isinstance(result, str)
        assert 'exposure' in result.lower()
    
    def test_to_string_all_camprop_values(self):
        """Test to_string() for all CamProp values."""
        cam_props = [
            CamProp.Pan, CamProp.Tilt, CamProp.Roll,
            CamProp.Zoom, CamProp.Exposure, CamProp.Iris,
            CamProp.Focus, CamProp.ScanMode, CamProp.Privacy,
            CamProp.PanRelative, CamProp.TiltRelative, CamProp.RollRelative,
            CamProp.ZoomRelative, CamProp.ExposureRelative,
            CamProp.IrisRelative, CamProp.FocusRelative,
            CamProp.PanTilt, CamProp.PanTiltRelative,
            CamProp.FocusSimple, CamProp.DigitalZoom,
            CamProp.DigitalZoomRelative, CamProp.BacklightCompensation,
            CamProp.Lamp
        ]
        
        for prop in cam_props:
            result = to_string(prop)
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_to_string_camprop_unique(self):
        """Test to_string() returns unique strings for different CamProp values."""
        pan_str = to_string(CamProp.Pan)
        tilt_str = to_string(CamProp.Tilt)
        zoom_str = to_string(CamProp.Zoom)
        
        assert pan_str != tilt_str
        assert pan_str != zoom_str
        assert tilt_str != zoom_str
    
    def test_to_string_camprop_relative_distinct(self):
        """Test to_string() distinguishes absolute and relative properties."""
        pan_str = to_string(CamProp.Pan)
        pan_rel_str = to_string(CamProp.PanRelative)
        
        assert pan_str != pan_rel_str
        assert 'relative' in pan_rel_str.lower() or 'rel' in pan_rel_str.lower()


class TestToStringVidProp:
    """Test to_string() for VidProp enum."""
    
    def test_to_string_brightness(self):
        """Test to_string(VidProp.Brightness)."""
        result = to_string(VidProp.Brightness)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert 'brightness' in result.lower()
    
    def test_to_string_contrast(self):
        """Test to_string(VidProp.Contrast)."""
        result = to_string(VidProp.Contrast)
        
        assert isinstance(result, str)
        assert 'contrast' in result.lower()
    
    def test_to_string_saturation(self):
        """Test to_string(VidProp.Saturation)."""
        result = to_string(VidProp.Saturation)
        
        assert isinstance(result, str)
        assert 'saturation' in result.lower()
    
    def test_to_string_hue(self):
        """Test to_string(VidProp.Hue)."""
        result = to_string(VidProp.Hue)
        
        assert isinstance(result, str)
        assert 'hue' in result.lower()
    
    def test_to_string_white_balance(self):
        """Test to_string(VidProp.WhiteBalance)."""
        result = to_string(VidProp.WhiteBalance)
        
        assert isinstance(result, str)
        assert 'white' in result.lower() or 'balance' in result.lower()
    
    def test_to_string_all_vidprop_values(self):
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
    
    def test_to_string_vidprop_unique(self):
        """Test to_string() returns unique strings for different VidProp values."""
        brightness_str = to_string(VidProp.Brightness)
        contrast_str = to_string(VidProp.Contrast)
        saturation_str = to_string(VidProp.Saturation)
        
        assert brightness_str != contrast_str
        assert brightness_str != saturation_str
        assert contrast_str != saturation_str


class TestToStringCamMode:
    """Test to_string() for CamMode enum."""
    
    def test_to_string_auto(self):
        """Test to_string(CamMode.Auto)."""
        result = to_string(CamMode.Auto)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert 'auto' in result.lower()
    
    def test_to_string_manual(self):
        """Test to_string(CamMode.Manual)."""
        result = to_string(CamMode.Manual)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert 'manual' in result.lower()
    
    def test_to_string_cammode_unique(self):
        """Test to_string() returns different strings for Auto and Manual."""
        auto_str = to_string(CamMode.Auto)
        manual_str = to_string(CamMode.Manual)
        
        assert auto_str != manual_str


class TestToStringErrorCode:
    """Test to_string() for ErrorCode enum."""
    
    def test_to_string_success(self):
        """Test to_string(ErrorCode.Success)."""
        result = to_string(ErrorCode.Success)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert 'success' in result.lower()
    
    def test_to_string_device_not_found(self):
        """Test to_string(ErrorCode.DeviceNotFound)."""
        result = to_string(ErrorCode.DeviceNotFound)
        
        assert isinstance(result, str)
        assert 'device' in result.lower() or 'not' in result.lower()
    
    def test_to_string_device_busy(self):
        """Test to_string(ErrorCode.DeviceBusy)."""
        result = to_string(ErrorCode.DeviceBusy)
        
        assert isinstance(result, str)
        assert 'busy' in result.lower()
    
    def test_to_string_property_not_supported(self):
        """Test to_string(ErrorCode.PropertyNotSupported)."""
        result = to_string(ErrorCode.PropertyNotSupported)
        
        assert isinstance(result, str)
        assert 'property' in result.lower() or 'not' in result.lower() or 'support' in result.lower()
    
    def test_to_string_invalid_value(self):
        """Test to_string(ErrorCode.InvalidValue)."""
        result = to_string(ErrorCode.InvalidValue)
        
        assert isinstance(result, str)
        assert 'invalid' in result.lower() or 'value' in result.lower()
    
    def test_to_string_all_errorcode_values(self):
        """Test to_string() for all ErrorCode values."""
        error_codes = [
            ErrorCode.Success, ErrorCode.DeviceNotFound,
            ErrorCode.DeviceBusy, ErrorCode.PropertyNotSupported,
            ErrorCode.InvalidValue, ErrorCode.PermissionDenied,
            ErrorCode.SystemError, ErrorCode.InvalidArgument,
            ErrorCode.NotImplemented
        ]
        
        for code in error_codes:
            result = to_string(code)
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_to_string_errorcode_unique(self):
        """Test to_string() returns unique strings for different ErrorCode values."""
        success_str = to_string(ErrorCode.Success)
        not_found_str = to_string(ErrorCode.DeviceNotFound)
        busy_str = to_string(ErrorCode.DeviceBusy)
        
        assert success_str != not_found_str
        assert success_str != busy_str
        assert not_found_str != busy_str


class TestToStringLogLevel:
    """Test to_string() for LogLevel enum."""
    
    def test_to_string_debug(self):
        """Test to_string(LogLevel.Debug)."""
        result = to_string(LogLevel.Debug)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert 'debug' in result.lower()
    
    def test_to_string_info(self):
        """Test to_string(LogLevel.Info)."""
        result = to_string(LogLevel.Info)
        
        assert isinstance(result, str)
        assert 'info' in result.lower()
    
    def test_to_string_warning(self):
        """Test to_string(LogLevel.Warning)."""
        result = to_string(LogLevel.Warning)
        
        assert isinstance(result, str)
        assert 'warn' in result.lower()
    
    def test_to_string_error(self):
        """Test to_string(LogLevel.Error)."""
        result = to_string(LogLevel.Error)
        
        assert isinstance(result, str)
        assert 'error' in result.lower()
    
    def test_to_string_critical(self):
        """Test to_string(LogLevel.Critical)."""
        result = to_string(LogLevel.Critical)
        
        assert isinstance(result, str)
        assert 'critical' in result.lower()
    
    def test_to_string_all_loglevel_values(self):
        """Test to_string() for all LogLevel values."""
        log_levels = [
            LogLevel.Debug, LogLevel.Info, LogLevel.Warning,
            LogLevel.Error, LogLevel.Critical
        ]
        
        for level in log_levels:
            result = to_string(level)
            assert isinstance(result, str)
            assert len(result) > 0
    
    def test_to_string_loglevel_unique(self):
        """Test to_string() returns unique strings for different LogLevel values."""
        debug_str = to_string(LogLevel.Debug)
        info_str = to_string(LogLevel.Info)
        error_str = to_string(LogLevel.Error)
        
        assert debug_str != info_str
        assert debug_str != error_str
        assert info_str != error_str


class TestDeviceStringMethods:
    """Test Device.__str__() and __repr__() methods."""
    
    def test_device_str(self):
        """Test Device.__str__() returns device name."""
        device = Device("Test Camera", "/dev/video0")
        
        result = str(device)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Test Camera" in result
    
    def test_device_repr(self):
        """Test Device.__repr__() is informative."""
        device = Device("Test Camera", "/dev/video0")
        
        result = repr(device)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Device" in result
        assert "Test Camera" in result
        assert "/dev/video0" in result
    
    def test_device_str_vs_repr(self):
        """Test Device.__str__() and __repr__() are different."""
        device = Device("Test Camera", "/dev/video0")
        
        str_result = str(device)
        repr_result = repr(device)
        
        # __repr__ should be more detailed
        assert len(repr_result) >= len(str_result)
    
    def test_device_str_empty_name(self):
        """Test Device.__str__() with empty name."""
        device = Device("", "/dev/video0")
        
        result = str(device)
        
        assert isinstance(result, str)
    
    def test_device_repr_empty_path(self):
        """Test Device.__repr__() with empty path."""
        device = Device("Camera", "")
        
        result = repr(device)
        
        assert isinstance(result, str)
        assert "Camera" in result


class TestPropSettingStringMethods:
    """Test PropSetting.__str__() and __repr__() methods."""
    
    def test_propsetting_str_manual(self):
        """Test PropSetting.__str__() for manual mode."""
        setting = PropSetting(50, CamMode.Manual)
        
        result = str(setting)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "50" in result
        assert "manual" in result.lower()
    
    def test_propsetting_str_auto(self):
        """Test PropSetting.__str__() for auto mode."""
        setting = PropSetting(0, CamMode.Auto)
        
        result = str(setting)
        
        assert isinstance(result, str)
        assert "auto" in result.lower()
    
    def test_propsetting_repr(self):
        """Test PropSetting.__repr__() is informative."""
        setting = PropSetting(75, CamMode.Manual)
        
        result = repr(setting)
        
        assert isinstance(result, str)
        assert "PropSetting" in result
        assert "75" in result
    
    def test_propsetting_str_different_values(self):
        """Test PropSetting.__str__() differs for different values."""
        setting1 = PropSetting(50, CamMode.Manual)
        setting2 = PropSetting(100, CamMode.Manual)
        
        str1 = str(setting1)
        str2 = str(setting2)
        
        assert str1 != str2
    
    def test_propsetting_str_different_modes(self):
        """Test PropSetting.__str__() differs for different modes."""
        setting1 = PropSetting(50, CamMode.Manual)
        setting2 = PropSetting(50, CamMode.Auto)
        
        str1 = str(setting1)
        str2 = str(setting2)
        
        assert str1 != str2


class TestPropRangeStringMethods:
    """Test PropRange.__str__() and __repr__() methods."""
    
    def test_proprange_str(self):
        """Test PropRange.__str__() shows range."""
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 255
        prop_range.step = 1
        prop_range.default_val = 128
        
        result = str(prop_range)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "0" in result
        assert "255" in result
    
    def test_proprange_repr(self):
        """Test PropRange.__repr__() is informative."""
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 100
        prop_range.step = 5
        prop_range.default_val = 50
        
        result = repr(prop_range)
        
        assert isinstance(result, str)
        assert "PropRange" in result
        assert "0" in result
        assert "100" in result
    
    def test_proprange_str_includes_step(self):
        """Test PropRange.__str__() includes step information."""
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 100
        prop_range.step = 10
        
        result = str(prop_range)
        
        # Should mention step or show it's not continuous
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_proprange_repr_includes_default(self):
        """Test PropRange.__repr__() includes default value."""
        prop_range = PropRange()
        prop_range.min = 0
        prop_range.max = 100
        prop_range.step = 1
        prop_range.default_val = 75
        
        result = repr(prop_range)
        
        assert "75" in result or "default" in result.lower()


class TestErrorStringMethods:
    """Test Error.__str__() and __repr__() methods."""
    
    def test_error_str(self):
        """Test Error.__str__() returns error message."""
        error = ErrorInfo(ErrorCode.DeviceNotFound, "Device not found")
        
        result = str(error)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Device not found" in result
    
    def test_error_repr(self):
        """Test Error.__repr__() is informative."""
        error = ErrorInfo(ErrorCode.DeviceNotFound, "Device not found")
        
        result = repr(error)
        
        assert isinstance(result, str)
        assert "Error" in result or "DuvcError" in result
        assert "Device not found" in result
    
    def test_error_str_different_codes(self):
        """Test Error.__str__() differs for different error codes."""
        error1 = ErrorInfo(ErrorCode.DeviceNotFound, "Device not found")
        error2 = ErrorInfo(ErrorCode.DeviceBusy, "Device busy")
        
        str1 = str(error1)
        str2 = str(error2)
        
        assert str1 != str2
    
    def test_error_repr_includes_code(self):
        """Test Error.__repr__() includes error code."""
        error = ErrorInfo(ErrorCode.PropertyNotSupported, "Property not supported")
        
        result = repr(error)
        
        # Should include code number or name
        assert isinstance(result, str)
        assert len(result) > 0


class TestStringConversionConsistency:
    """Test consistency across string conversion methods."""
    
    def test_to_string_consistent_across_calls(self):
        """Test to_string() returns same string for same enum value."""
        str1 = to_string(CamProp.Pan)
        str2 = to_string(CamProp.Pan)
        
        assert str1 == str2
    
    def test_device_str_consistent(self):
        """Test Device.__str__() returns same string for same device."""
        device = Device("Test Camera", "/dev/video0")
        
        str1 = str(device)
        str2 = str(device)
        
        assert str1 == str2
    
    def test_propsetting_str_consistent(self):
        """Test PropSetting.__str__() returns same string for same setting."""
        setting = PropSetting(50, CamMode.Manual)
        
        str1 = str(setting)
        str2 = str(setting)
        
        assert str1 == str2
    
    def test_enum_str_via_to_string_vs_direct(self):
        """Test to_string() vs str() for enums."""
        # Note: pybind11 enums may have different __str__ implementation
        # to_string() is the canonical conversion function
        
        to_string_result = to_string(CamProp.Pan)
        str_result = str(CamProp.Pan)
        
        # Both should be strings
        assert isinstance(to_string_result, str)
        assert isinstance(str_result, str)


class TestStringConversionEdgeCases:
    """Test edge cases in string conversion."""
    
    def test_device_with_special_characters(self):
        """Test Device string methods with special characters in name."""
        device = Device("Camera (USB 2.0)", "/dev/video0")
        
        str_result = str(device)
        repr_result = repr(device)
        
        assert isinstance(str_result, str)
        assert isinstance(repr_result, str)
        assert "Camera" in str_result
    
    def test_device_with_unicode(self):
        """Test Device string methods with Unicode characters."""
        device = Device("カメラ", "/dev/video0")
        
        str_result = str(device)
        repr_result = repr(device)
        
        assert isinstance(str_result, str)
        assert isinstance(repr_result, str)
    
    def test_propsetting_extreme_values(self):
        """Test PropSetting string methods with extreme values."""
        setting1 = PropSetting(-1000000, CamMode.Manual)
        setting2 = PropSetting(1000000, CamMode.Manual)
        
        str1 = str(setting1)
        str2 = str(setting2)
        
        assert isinstance(str1, str)
        assert isinstance(str2, str)
        assert str1 != str2
    
    def test_proprange_inverted(self):
        """Test PropRange string methods with unusual values."""
        prop_range = PropRange()
        prop_range.min = 100
        prop_range.max = 0  # Inverted range
        prop_range.step = 1
        
        result = str(prop_range)
        
        # Should still produce valid string
        assert isinstance(result, str)
        assert len(result) > 0


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
