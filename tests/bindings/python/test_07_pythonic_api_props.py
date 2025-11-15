"""
Test Suite 07: Pythonic API Properties (CameraController)
==========================================================

Tests CameraController property-based interface for all camera properties.

Properties Tested:
  Video Properties (10):
    - brightness - Camera brightness (0-255)
    - contrast - Image contrast (0-100)
    - hue - Color hue (-180 to 180)
    - saturation - Color saturation (0-100)
    - sharpness - Image sharpness (0-100)
    - gamma - Gamma correction (100-300)
    - color_enable - Color vs monochrome (bool)
    - white_balance - White balance temperature (Kelvin)
    - video_backlight_compensation - Video backlight compensation
    - gain - Sensor gain/amplification (0-100)
  
  Camera Properties (11):
    - pan - Camera pan position (degrees)
    - tilt - Camera tilt position (degrees)
    - roll - Camera roll rotation (degrees)
    - zoom - Optical zoom level
    - exposure - Exposure time/shutter speed
    - iris - Aperture/iris diameter
    - focus - Focus distance position
    - scan_mode - Progressive/interlaced
    - privacy - Privacy mode on/off (bool)
    - digital_zoom - Digital zoom level
    - backlight_compensation - Camera backlight compensation

Total: 21 properties (10 video + 11 camera)

Test Organization:
  1. Without Camera Tests - Interface verification
  2. With Camera Tests - Integration tests using real camera hardware

Run: pytest tests/test_07_pythonic_api_props.py -v
Run without camera: pytest tests/test_07_pythonic_api_props.py -v -m "not hardware"
"""

import pytest
import sys
from typing import List, Optional

import duvc_ctl
from duvc_ctl import (
    # Pythonic API
    CameraController,
    # Device functions
    list_devices,
    # Core types
    Device,
    # Exceptions
    DeviceNotFoundError, PropertyNotSupportedError, InvalidValueError,
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
def camera_controller(test_device) -> Optional[CameraController]:
    """Get CameraController instance for testing."""
    if test_device is None:
        pytest.skip("No test device available")
    
    try:
        controller = CameraController(device_index=0)
        yield controller
        controller.close()
    except Exception as e:
        pytest.skip(f"Could not create CameraController: {e}")


# ============================================================================
# WITHOUT CAMERA TESTS - Interface verification
# ============================================================================

class TestCameraControllerVideoPropertyInterfaces:
    """Test CameraController video property interfaces exist."""
    
    def test_brightness_property_exists(self):
        """Test brightness property getter/setter exist."""
        assert hasattr(CameraController, 'brightness')
    
    def test_contrast_property_exists(self):
        """Test contrast property getter/setter exist."""
        assert hasattr(CameraController, 'contrast')
    
    def test_hue_property_exists(self):
        """Test hue property getter/setter exist."""
        assert hasattr(CameraController, 'hue')
    
    def test_saturation_property_exists(self):
        """Test saturation property getter/setter exist."""
        assert hasattr(CameraController, 'saturation')
    
    def test_sharpness_property_exists(self):
        """Test sharpness property getter/setter exist."""
        assert hasattr(CameraController, 'sharpness')
    
    def test_gamma_property_exists(self):
        """Test gamma property getter/setter exist."""
        assert hasattr(CameraController, 'gamma')
    
    def test_color_enable_property_exists(self):
        """Test color_enable property getter/setter exist."""
        assert hasattr(CameraController, 'color_enable')
    
    def test_white_balance_property_exists(self):
        """Test white_balance property getter/setter exist."""
        assert hasattr(CameraController, 'white_balance')
    
    def test_video_backlight_compensation_property_exists(self):
        """Test video_backlight_compensation property getter/setter exist."""
        assert hasattr(CameraController, 'video_backlight_compensation')
    
    def test_gain_property_exists(self):
        """Test gain property getter/setter exist."""
        assert hasattr(CameraController, 'gain')


class TestCameraControllerCameraPropertyInterfaces:
    """Test CameraController camera property interfaces exist."""
    
    def test_pan_property_exists(self):
        """Test pan property getter/setter exist."""
        assert hasattr(CameraController, 'pan')
    
    def test_tilt_property_exists(self):
        """Test tilt property getter/setter exist."""
        assert hasattr(CameraController, 'tilt')
    
    def test_roll_property_exists(self):
        """Test roll property getter/setter exist."""
        assert hasattr(CameraController, 'roll')
    
    def test_zoom_property_exists(self):
        """Test zoom property getter/setter exist."""
        assert hasattr(CameraController, 'zoom')
    
    def test_exposure_property_exists(self):
        """Test exposure property getter/setter exist."""
        assert hasattr(CameraController, 'exposure')
    
    def test_iris_property_exists(self):
        """Test iris property getter/setter exist."""
        assert hasattr(CameraController, 'iris')
    
    def test_focus_property_exists(self):
        """Test focus property getter/setter exist."""
        assert hasattr(CameraController, 'focus')
    
    def test_scan_mode_property_exists(self):
        """Test scan_mode property getter/setter exist."""
        assert hasattr(CameraController, 'scan_mode')
    
    def test_privacy_property_exists(self):
        """Test privacy property getter/setter exist."""
        assert hasattr(CameraController, 'privacy')
    
    def test_digital_zoom_property_exists(self):
        """Test digital_zoom property getter/setter exist."""
        assert hasattr(CameraController, 'digital_zoom')
    
    def test_backlight_compensation_property_exists(self):
        """Test backlight_compensation property getter/setter exist."""
        assert hasattr(CameraController, 'backlight_compensation')


# ============================================================================
# WITH CAMERA TESTS - Integration tests using real camera
# ============================================================================

@pytest.mark.hardware
class TestBrightnessProperty:
    """Test brightness video property."""
    
    def test_brightness_read(self, camera_controller):
        """Test reading brightness property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.brightness
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Brightness not supported by camera")
    
    def test_brightness_write(self, camera_controller):
        """Test writing brightness property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Get current value
            original = camera_controller.brightness
            
            # Set to same value
            camera_controller.brightness = original
            
            # Verify it was set
            new_value = camera_controller.brightness
            assert isinstance(new_value, int)
        except PropertyNotSupportedError:
            pytest.skip("Brightness not supported by camera")
    
    def test_brightness_range_validation(self, camera_controller):
        """Test brightness respects valid range."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            prop_range = camera_controller.get_property_range('brightness')
            if prop_range:
                min_val = prop_range['min']
                max_val = prop_range['max']
                
                # Set to min
                camera_controller.brightness = min_val
                # Set to max
                camera_controller.brightness = max_val
        except PropertyNotSupportedError:
            pytest.skip("Brightness not supported by camera")


@pytest.mark.hardware
class TestContrastProperty:
    """Test contrast video property."""
    
    def test_contrast_read(self, camera_controller):
        """Test reading contrast property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.contrast
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Contrast not supported by camera")
    
    def test_contrast_write(self, camera_controller):
        """Test writing contrast property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.contrast
            camera_controller.contrast = original
        except PropertyNotSupportedError:
            pytest.skip("Contrast not supported by camera")


@pytest.mark.hardware
class TestHueProperty:
    """Test hue video property."""
    
    def test_hue_read(self, camera_controller):
        """Test reading hue property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.hue
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Hue not supported by camera")
    
    def test_hue_write(self, camera_controller):
        """Test writing hue property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.hue
            camera_controller.hue = original
        except PropertyNotSupportedError:
            pytest.skip("Hue not supported by camera")


@pytest.mark.hardware
class TestSaturationProperty:
    """Test saturation video property."""
    
    def test_saturation_read(self, camera_controller):
        """Test reading saturation property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.saturation
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Saturation not supported by camera")
    
    def test_saturation_write(self, camera_controller):
        """Test writing saturation property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.saturation
            camera_controller.saturation = original
        except PropertyNotSupportedError:
            pytest.skip("Saturation not supported by camera")


@pytest.mark.hardware
class TestSharpnessProperty:
    """Test sharpness video property."""
    
    def test_sharpness_read(self, camera_controller):
        """Test reading sharpness property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.sharpness
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Sharpness not supported by camera")
    
    def test_sharpness_write(self, camera_controller):
        """Test writing sharpness property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.sharpness
            camera_controller.sharpness = original
        except PropertyNotSupportedError:
            pytest.skip("Sharpness not supported by camera")


@pytest.mark.hardware
class TestGammaProperty:
    """Test gamma video property."""
    
    def test_gamma_read(self, camera_controller):
        """Test reading gamma property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.gamma
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Gamma not supported by camera")
    
    def test_gamma_write(self, camera_controller):
        """Test writing gamma property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.gamma
            camera_controller.gamma = original
        except PropertyNotSupportedError:
            pytest.skip("Gamma not supported by camera")


@pytest.mark.hardware
class TestColorEnableProperty:
    """Test color_enable video property."""
    
    def test_color_enable_read(self, camera_controller):
        """Test reading color_enable property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.color_enable
            assert isinstance(value, bool)
        except PropertyNotSupportedError:
            pytest.skip("Color enable not supported by camera")
    
    def test_color_enable_write(self, camera_controller):
        """Test writing color_enable property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.color_enable
            camera_controller.color_enable = original
        except PropertyNotSupportedError:
            pytest.skip("Color enable not supported by camera")


@pytest.mark.hardware
class TestWhiteBalanceProperty:
    """Test white_balance video property."""
    
    def test_white_balance_read(self, camera_controller):
        """Test reading white_balance property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.white_balance
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("White balance not supported by camera")
    
    def test_white_balance_write(self, camera_controller):
        """Test writing white_balance property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.white_balance
            camera_controller.white_balance = original
        except PropertyNotSupportedError:
            pytest.skip("White balance not supported by camera")


@pytest.mark.hardware
class TestVideoBacklightCompensationProperty:
    """Test video_backlight_compensation property."""
    
    def test_video_backlight_compensation_read(self, camera_controller):
        """Test reading video_backlight_compensation property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.video_backlight_compensation
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Video backlight compensation not supported")
    
    def test_video_backlight_compensation_write(self, camera_controller):
        """Test writing video_backlight_compensation property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.video_backlight_compensation
            camera_controller.video_backlight_compensation = original
        except PropertyNotSupportedError:
            pytest.skip("Video backlight compensation not supported")


@pytest.mark.hardware
class TestGainProperty:
    """Test gain video property."""
    
    def test_gain_read(self, camera_controller):
        """Test reading gain property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.gain
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Gain not supported by camera")
    
    def test_gain_write(self, camera_controller):
        """Test writing gain property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.gain
            camera_controller.gain = original
        except PropertyNotSupportedError:
            pytest.skip("Gain not supported by camera")


@pytest.mark.hardware
class TestPanProperty:
    """Test pan camera property."""
    
    def test_pan_read(self, camera_controller):
        """Test reading pan property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.pan
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Pan not supported by camera")
    
    def test_pan_write(self, camera_controller):
        """Test writing pan property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.pan
            camera_controller.pan = original
        except PropertyNotSupportedError:
            pytest.skip("Pan not supported by camera")
    
    def test_pan_range_validation(self, camera_controller):
        """Test pan respects valid range."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            prop_range = camera_controller.get_property_range('pan')
            if prop_range:
                min_val = prop_range['min']
                max_val = prop_range['max']
                
                # Typically -180 to 180 degrees
                assert min_val <= 0 <= max_val
        except PropertyNotSupportedError:
            pytest.skip("Pan not supported by camera")


@pytest.mark.hardware
class TestTiltProperty:
    """Test tilt camera property."""
    
    def test_tilt_read(self, camera_controller):
        """Test reading tilt property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.tilt
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Tilt not supported by camera")
    
    def test_tilt_write(self, camera_controller):
        """Test writing tilt property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.tilt
            camera_controller.tilt = original
        except PropertyNotSupportedError:
            pytest.skip("Tilt not supported by camera")


@pytest.mark.hardware
class TestRollProperty:
    """Test roll camera property."""
    
    def test_roll_read(self, camera_controller):
        """Test reading roll property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.roll
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Roll not supported by camera")
    
    def test_roll_write(self, camera_controller):
        """Test writing roll property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.roll
            camera_controller.roll = original
        except PropertyNotSupportedError:
            pytest.skip("Roll not supported by camera")


@pytest.mark.hardware
class TestZoomProperty:
    """Test zoom camera property."""
    
    def test_zoom_read(self, camera_controller):
        """Test reading zoom property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.zoom
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Zoom not supported by camera")
    
    def test_zoom_write(self, camera_controller):
        """Test writing zoom property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.zoom
            camera_controller.zoom = original
        except PropertyNotSupportedError:
            pytest.skip("Zoom not supported by camera")


@pytest.mark.hardware
class TestExposureProperty:
    """Test exposure camera property."""
    
    def test_exposure_read(self, camera_controller):
        """Test reading exposure property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.exposure
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Exposure not supported by camera")
    
    def test_exposure_write(self, camera_controller):
        """Test writing exposure property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.exposure
            camera_controller.exposure = original
        except PropertyNotSupportedError:
            pytest.skip("Exposure not supported by camera")


@pytest.mark.hardware
class TestIrisProperty:
    """Test iris camera property."""
    
    def test_iris_read(self, camera_controller):
        """Test reading iris property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.iris
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Iris not supported by camera")
    
    def test_iris_write(self, camera_controller):
        """Test writing iris property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.iris
            camera_controller.iris = original
        except PropertyNotSupportedError:
            pytest.skip("Iris not supported by camera")


@pytest.mark.hardware
class TestFocusProperty:
    """Test focus camera property."""
    
    def test_focus_read(self, camera_controller):
        """Test reading focus property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.focus
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Focus not supported by camera")
    
    def test_focus_write(self, camera_controller):
        """Test writing focus property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.focus
            camera_controller.focus = original
        except PropertyNotSupportedError:
            pytest.skip("Focus not supported by camera")


@pytest.mark.hardware
class TestScanModeProperty:
    """Test scan_mode camera property."""
    
    def test_scan_mode_read(self, camera_controller):
        """Test reading scan_mode property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.scan_mode
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Scan mode not supported by camera")
    
    def test_scan_mode_write(self, camera_controller):
        """Test writing scan_mode property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.scan_mode
            camera_controller.scan_mode = original
        except PropertyNotSupportedError:
            pytest.skip("Scan mode not supported by camera")


@pytest.mark.hardware
class TestPrivacyProperty:
    """Test privacy camera property."""
    
    def test_privacy_read(self, camera_controller):
        """Test reading privacy property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.privacy
            assert isinstance(value, bool)
        except PropertyNotSupportedError:
            pytest.skip("Privacy not supported by camera")
    
    def test_privacy_write(self, camera_controller):
        """Test writing privacy property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.privacy
            camera_controller.privacy = original
        except PropertyNotSupportedError:
            pytest.skip("Privacy not supported by camera")


@pytest.mark.hardware
class TestDigitalZoomProperty:
    """Test digital_zoom camera property."""
    
    def test_digital_zoom_read(self, camera_controller):
        """Test reading digital_zoom property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.digital_zoom
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Digital zoom not supported by camera")
    
    def test_digital_zoom_write(self, camera_controller):
        """Test writing digital_zoom property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.digital_zoom
            camera_controller.digital_zoom = original
        except PropertyNotSupportedError:
            pytest.skip("Digital zoom not supported by camera")


@pytest.mark.hardware
class TestBacklightCompensationProperty:
    """Test backlight_compensation camera property."""
    
    def test_backlight_compensation_read(self, camera_controller):
        """Test reading backlight_compensation property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.backlight_compensation
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Backlight compensation not supported")
    
    def test_backlight_compensation_write(self, camera_controller):
        """Test writing backlight_compensation property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            original = camera_controller.backlight_compensation
            camera_controller.backlight_compensation = original
        except PropertyNotSupportedError:
            pytest.skip("Backlight compensation not supported")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
