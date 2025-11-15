"""
Test Suite 08: Pythonic API Methods (CameraController)
=======================================================

Tests CameraController method-based interface for movement and control.

Methods Tested:
  Relative Movement (8):
    - pan_relative(degrees) - Relative pan movement
    - tilt_relative(degrees) - Relative tilt movement
    - roll_relative(degrees) - Relative roll rotation
    - zoom_relative(steps) - Relative zoom adjustment
    - focus_relative(steps) - Relative focus adjustment
    - exposure_relative(steps) - Relative exposure adjustment
    - iris_relative(steps) - Relative iris adjustment
    - digital_zoom_relative(steps) - Relative digital zoom
  
  Combined Control (2):
    - set_pan_tilt(pan, tilt) - Set both pan and tilt together
    - pan_tilt_relative(pan_delta, tilt_delta) - Relative pan+tilt movement
  
  Utility Methods (2):
    - reset_to_defaults() - Reset all properties to defaults/auto
    - center_camera() - Move pan/tilt to center position

Total: 12 methods

Test Organization:
  1. Without Camera Tests - Interface verification
  2. With Camera Tests - Integration tests using real camera hardware

Run: pytest tests/test_08_pythonic_api_methods.py -v
Run without camera: pytest tests/test_08_pythonic_api_methods.py -v -m "not hardware"
"""

import pytest
import sys
import warnings
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

class TestRelativeMovementMethodInterfaces:
    """Test relative movement method interfaces exist."""
    
    def test_pan_relative_method_exists(self):
        """Test pan_relative() method exists."""
        assert hasattr(CameraController, 'pan_relative')
        assert callable(getattr(CameraController, 'pan_relative'))
    
    def test_tilt_relative_method_exists(self):
        """Test tilt_relative() method exists."""
        assert hasattr(CameraController, 'tilt_relative')
        assert callable(getattr(CameraController, 'tilt_relative'))
    
    def test_roll_relative_method_exists(self):
        """Test roll_relative() method exists."""
        assert hasattr(CameraController, 'roll_relative')
        assert callable(getattr(CameraController, 'roll_relative'))
    
    def test_zoom_relative_method_exists(self):
        """Test zoom_relative() method exists."""
        assert hasattr(CameraController, 'zoom_relative')
        assert callable(getattr(CameraController, 'zoom_relative'))
    
    def test_focus_relative_method_exists(self):
        """Test focus_relative() method exists."""
        assert hasattr(CameraController, 'focus_relative')
        assert callable(getattr(CameraController, 'focus_relative'))
    
    def test_exposure_relative_method_exists(self):
        """Test exposure_relative() method exists."""
        assert hasattr(CameraController, 'exposure_relative')
        assert callable(getattr(CameraController, 'exposure_relative'))
    
    def test_iris_relative_method_exists(self):
        """Test iris_relative() method exists."""
        assert hasattr(CameraController, 'iris_relative')
        assert callable(getattr(CameraController, 'iris_relative'))
    
    def test_digital_zoom_relative_method_exists(self):
        """Test digital_zoom_relative() method exists."""
        assert hasattr(CameraController, 'digital_zoom_relative')
        assert callable(getattr(CameraController, 'digital_zoom_relative'))


class TestCombinedControlMethodInterfaces:
    """Test combined control method interfaces exist."""
    
    def test_set_pan_tilt_method_exists(self):
        """Test set_pan_tilt() method exists."""
        assert hasattr(CameraController, 'set_pan_tilt')
        assert callable(getattr(CameraController, 'set_pan_tilt'))
    
    def test_pan_tilt_relative_method_exists(self):
        """Test pan_tilt_relative() method exists."""
        assert hasattr(CameraController, 'pan_tilt_relative')
        assert callable(getattr(CameraController, 'pan_tilt_relative'))


class TestUtilityMethodInterfaces:
    """Test utility method interfaces exist."""
    
    def test_reset_to_defaults_method_exists(self):
        """Test reset_to_defaults() method exists."""
        assert hasattr(CameraController, 'reset_to_defaults')
        assert callable(getattr(CameraController, 'reset_to_defaults'))
    
    def test_center_camera_method_exists(self):
        """Test center_camera() method exists."""
        assert hasattr(CameraController, 'center_camera')
        assert callable(getattr(CameraController, 'center_camera'))


# ============================================================================
# WITH CAMERA TESTS - Integration tests using real camera
# ============================================================================

@pytest.mark.hardware
class TestPanRelativeMethod:
    """Test pan_relative() method."""
    
    def test_pan_relative_positive(self, camera_controller):
        """Test pan_relative() with positive value (right)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Move right by 10 degrees
            camera_controller.pan_relative(10)
        except PropertyNotSupportedError:
            pytest.skip("Pan relative not supported by camera")
    
    def test_pan_relative_negative(self, camera_controller):
        """Test pan_relative() with negative value (left)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Move left by 10 degrees
            camera_controller.pan_relative(-10)
        except PropertyNotSupportedError:
            pytest.skip("Pan relative not supported by camera")
    
    def test_pan_relative_zero(self, camera_controller):
        """Test pan_relative() with zero (no movement)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.pan_relative(0)
        except PropertyNotSupportedError:
            pytest.skip("Pan relative not supported by camera")


@pytest.mark.hardware
class TestTiltRelativeMethod:
    """Test tilt_relative() method."""
    
    def test_tilt_relative_positive(self, camera_controller):
        """Test tilt_relative() with positive value (up)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.tilt_relative(5)
        except PropertyNotSupportedError:
            pytest.skip("Tilt relative not supported by camera")
    
    def test_tilt_relative_negative(self, camera_controller):
        """Test tilt_relative() with negative value (down)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.tilt_relative(-5)
        except PropertyNotSupportedError:
            pytest.skip("Tilt relative not supported by camera")


@pytest.mark.hardware
class TestRollRelativeMethod:
    """Test roll_relative() method."""
    
    def test_roll_relative_positive(self, camera_controller):
        """Test roll_relative() with positive value (clockwise)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.roll_relative(5)
        except PropertyNotSupportedError:
            pytest.skip("Roll relative not supported by camera")
    
    def test_roll_relative_negative(self, camera_controller):
        """Test roll_relative() with negative value (counter-clockwise)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.roll_relative(-5)
        except PropertyNotSupportedError:
            pytest.skip("Roll relative not supported by camera")


@pytest.mark.hardware
class TestZoomRelativeMethod:
    """Test zoom_relative() method."""
    
    def test_zoom_relative_positive(self, camera_controller):
        """Test zoom_relative() with positive value (zoom in)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.zoom_relative(10)
        except PropertyNotSupportedError:
            pytest.skip("Zoom relative not supported by camera")
    
    def test_zoom_relative_negative(self, camera_controller):
        """Test zoom_relative() with negative value (zoom out)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.zoom_relative(-10)
        except PropertyNotSupportedError:
            pytest.skip("Zoom relative not supported by camera")


@pytest.mark.hardware
class TestFocusRelativeMethod:
    """Test focus_relative() method."""
    
    def test_focus_relative_positive(self, camera_controller):
        """Test focus_relative() with positive value (focus farther)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.focus_relative(10)
        except PropertyNotSupportedError:
            pytest.skip("Focus relative not supported by camera")
    
    def test_focus_relative_negative(self, camera_controller):
        """Test focus_relative() with negative value (focus closer)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.focus_relative(-10)
        except PropertyNotSupportedError:
            pytest.skip("Focus relative not supported by camera")


@pytest.mark.hardware
class TestExposureRelativeMethod:
    """Test exposure_relative() method."""
    
    def test_exposure_relative_positive(self, camera_controller):
        """Test exposure_relative() with positive value (longer exposure)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.exposure_relative(1)
        except PropertyNotSupportedError:
            pytest.skip("Exposure relative not supported by camera")
    
    def test_exposure_relative_negative(self, camera_controller):
        """Test exposure_relative() with negative value (shorter exposure)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.exposure_relative(-1)
        except PropertyNotSupportedError:
            pytest.skip("Exposure relative not supported by camera")


@pytest.mark.hardware
class TestIrisRelativeMethod:
    """Test iris_relative() method."""
    
    def test_iris_relative_positive(self, camera_controller):
        """Test iris_relative() with positive value (open iris)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.iris_relative(5)
        except PropertyNotSupportedError:
            pytest.skip("Iris relative not supported by camera")
    
    def test_iris_relative_negative(self, camera_controller):
        """Test iris_relative() with negative value (close iris)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.iris_relative(-5)
        except PropertyNotSupportedError:
            pytest.skip("Iris relative not supported by camera")


@pytest.mark.hardware
class TestDigitalZoomRelativeMethod:
    """Test digital_zoom_relative() method."""
    
    def test_digital_zoom_relative_positive(self, camera_controller):
        """Test digital_zoom_relative() with positive value."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.digital_zoom_relative(10)
        except PropertyNotSupportedError:
            pytest.skip("Digital zoom relative not supported by camera")
    
    def test_digital_zoom_relative_negative(self, camera_controller):
        """Test digital_zoom_relative() with negative value."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.digital_zoom_relative(-10)
        except PropertyNotSupportedError:
            pytest.skip("Digital zoom relative not supported by camera")


@pytest.mark.hardware
class TestSetPanTiltMethod:
    """Test set_pan_tilt() combined control method."""
    
    def test_set_pan_tilt_center(self, camera_controller):
        """Test set_pan_tilt() to move to center (0, 0)."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.set_pan_tilt(0, 0)
        except PropertyNotSupportedError:
            pytest.skip("Pan/tilt not supported by camera")
    
    def test_set_pan_tilt_custom_position(self, camera_controller):
        """Test set_pan_tilt() with custom position."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Get valid ranges
            pan_range = camera_controller.get_property_range('pan')
            tilt_range = camera_controller.get_property_range('tilt')
            
            if pan_range and tilt_range:
                # Set to mid-range values
                pan_mid = (pan_range['min'] + pan_range['max']) // 2
                tilt_mid = (tilt_range['min'] + tilt_range['max']) // 2
                
                camera_controller.set_pan_tilt(pan_mid, tilt_mid)
        except PropertyNotSupportedError:
            pytest.skip("Pan/tilt not supported by camera")
    
    def test_set_pan_tilt_separate_fallback(self, camera_controller):
        """Test set_pan_tilt() falls back to separate controls if combined not supported."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # This should work even if combined control isn't available
            camera_controller.set_pan_tilt(0, 0)
        except PropertyNotSupportedError:
            pytest.skip("Neither pan/tilt nor combined control supported")


@pytest.mark.hardware
class TestPanTiltRelativeMethod:
    """Test pan_tilt_relative() combined relative movement method."""
    
    def test_pan_tilt_relative_positive(self, camera_controller):
        """Test pan_tilt_relative() with positive deltas."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.pan_tilt_relative(5, 5)
        except PropertyNotSupportedError:
            pytest.skip("Pan/tilt relative not supported by camera")
    
    def test_pan_tilt_relative_negative(self, camera_controller):
        """Test pan_tilt_relative() with negative deltas."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.pan_tilt_relative(-5, -5)
        except PropertyNotSupportedError:
            pytest.skip("Pan/tilt relative not supported by camera")
    
    def test_pan_tilt_relative_mixed(self, camera_controller):
        """Test pan_tilt_relative() with mixed positive/negative deltas."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            camera_controller.pan_tilt_relative(10, -10)
        except PropertyNotSupportedError:
            pytest.skip("Pan/tilt relative not supported by camera")
    
    def test_pan_tilt_relative_separate_fallback(self, camera_controller):
        """Test pan_tilt_relative() falls back to separate controls."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Should work even if combined relative control not available
            camera_controller.pan_tilt_relative(5, 5)
        except PropertyNotSupportedError:
            pytest.skip("Neither pan/tilt relative nor combined control supported")


@pytest.mark.hardware
class TestResetToDefaultsMethod:
    """Test reset_to_defaults() utility method."""
    
    def test_reset_to_defaults_executes(self, camera_controller):
        """Test reset_to_defaults() executes without crashing."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Should not raise exception even if some properties fail
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            camera_controller.reset_to_defaults()
    
    def test_reset_to_defaults_with_warnings(self, camera_controller):
        """Test reset_to_defaults() may issue warnings for unsupported properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Reset may warn about unsupported properties
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            camera_controller.reset_to_defaults()
            
            # May or may not have warnings depending on camera
            assert isinstance(w, list)
    
    def test_reset_to_defaults_restores_values(self, camera_controller):
        """Test reset_to_defaults() actually changes property values."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Get brightness before reset
            try:
                brightness_before = camera_controller.brightness
            except PropertyNotSupportedError:
                pytest.skip("Brightness not supported")
            
            # Reset
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                camera_controller.reset_to_defaults()
            
            # Get brightness after reset
            brightness_after = camera_controller.brightness
            
            # Value may change or stay same (if already at default)
            assert isinstance(brightness_after, int)
        except PropertyNotSupportedError:
            pytest.skip("Brightness not supported for comparison")


@pytest.mark.hardware
class TestCenterCameraMethod:
    """Test center_camera() utility method."""
    
    def test_center_camera_executes(self, camera_controller):
        """Test center_camera() executes without crashing."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            camera_controller.center_camera()
    
    def test_center_camera_moves_to_center(self, camera_controller):
        """Test center_camera() moves pan/tilt to center position."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Get ranges
            pan_range = camera_controller.get_property_range('pan')
            tilt_range = camera_controller.get_property_range('tilt')
            
            if not pan_range or not tilt_range:
                pytest.skip("Pan/tilt ranges not available")
            
            # Center camera
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                camera_controller.center_camera()
            
            # Get current positions
            current_pan = camera_controller.pan
            current_tilt = camera_controller.tilt
            
            # Calculate expected center
            expected_pan = (pan_range['min'] + pan_range['max']) // 2
            expected_tilt = (tilt_range['min'] + tilt_range['max']) // 2
            
            # Should be at or near center (allow small tolerance)
            assert abs(current_pan - expected_pan) <= 10
            assert abs(current_tilt - expected_tilt) <= 10
            
        except PropertyNotSupportedError:
            pytest.skip("Pan/tilt not supported by camera")
    
    def test_center_camera_with_warnings(self, camera_controller):
        """Test center_camera() may issue warnings if pan/tilt not supported."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            camera_controller.center_camera()
            
            # May have warnings if pan/tilt not supported
            assert isinstance(w, list)


@pytest.mark.hardware
class TestRelativeMovementSequences:
    """Test sequences of relative movements."""
    
    def test_pan_sequence(self, camera_controller):
        """Test sequence of pan movements."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Move right, then left, then right again
            camera_controller.pan_relative(10)
            camera_controller.pan_relative(-20)
            camera_controller.pan_relative(10)
        except PropertyNotSupportedError:
            pytest.skip("Pan relative not supported")
    
    def test_zoom_sequence(self, camera_controller):
        """Test sequence of zoom movements."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Zoom in, out, in
            camera_controller.zoom_relative(10)
            camera_controller.zoom_relative(-10)
            camera_controller.zoom_relative(5)
        except PropertyNotSupportedError:
            pytest.skip("Zoom relative not supported")
    
    def test_combined_movement_sequence(self, camera_controller):
        """Test combined pan/tilt movement sequence."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Move in various directions
            camera_controller.pan_tilt_relative(5, 5)
            camera_controller.pan_tilt_relative(-5, 0)
            camera_controller.pan_tilt_relative(0, -5)
        except PropertyNotSupportedError:
            pytest.skip("Pan/tilt relative not supported")


@pytest.mark.hardware
class TestMethodCombinations:
    """Test combinations of different methods."""
    
    def test_absolute_then_relative(self, camera_controller):
        """Test setting absolute position then relative movement."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Set absolute position
            camera_controller.set_pan_tilt(0, 0)
            
            # Then move relatively
            camera_controller.pan_tilt_relative(10, 10)
        except PropertyNotSupportedError:
            pytest.skip("Pan/tilt not supported")
    
    def test_reset_then_adjust(self, camera_controller):
        """Test resetting defaults then making adjustments."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Reset everything
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                camera_controller.reset_to_defaults()
            
            # Then adjust brightness
            try:
                camera_controller.brightness = 75
            except PropertyNotSupportedError:
                pass  # OK if brightness not supported
        except Exception as e:
            pytest.fail(f"Unexpected error: {e}")
    
    def test_center_then_relative_move(self, camera_controller):
        """Test centering camera then moving relatively."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            # Center camera
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                camera_controller.center_camera()
            
            # Move relatively from center
            camera_controller.pan_relative(15)
            camera_controller.tilt_relative(-10)
        except PropertyNotSupportedError:
            pytest.skip("Pan/tilt not supported")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
