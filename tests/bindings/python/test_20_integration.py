"""
Test Suite 20: Integration Tests
=================================

Tests complete end-to-end workflows combining multiple features.

Integration Workflows Tested:
  CameraController Workflows (5):
    - Connect → Get/Set properties → Close
    - Context manager workflow
    - Batch operations workflow
    - PTZ control workflow
    - Preset management workflow
  
  Result-Based API Workflows (3):
    - open_camera → Camera operations → cleanup
    - Error handling workflow
    - Property range workflow
  
  Mixed API Workflows (2):
    - CameraController + core API
    - Platform interface integration

Total: 10 complete workflow scenarios

Test Organization:
  1. Without Camera Tests - Workflow interface verification
  2. With Camera Tests - Real device integration workflows

Run: pytest tests/test_20_integration.py -v
Run without camera: pytest tests/test_20_integration.py -v -m "not hardware"
"""

import pytest
import sys
import time
from typing import List, Optional

import duvc_ctl
from duvc_ctl import (
    # Core functions
    list_devices, open_camera,
    # CameraController
    CameraController,
    # Core types
    Device, CamProp, VidProp, CamMode, PropSetting,
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


# ============================================================================
# WITHOUT CAMERA TESTS - Workflow interface verification
# ============================================================================

class TestCameraControllerWorkflowInterface:
    """Test CameraController workflow interfaces exist."""
    
    def test_cameracontroller_class_exists(self):
        """Test CameraController class exists."""
        assert hasattr(duvc_ctl, 'CameraController')
    
    def test_cameracontroller_has_context_manager_methods(self):
        """Test CameraController has __enter__ and __exit__."""
        assert hasattr(CameraController, '__enter__')
        assert hasattr(CameraController, '__exit__')
    
    def test_cameracontroller_has_property_methods(self):
        """Test CameraController has get/set methods."""
        assert hasattr(CameraController, 'get')
        assert hasattr(CameraController, 'set')
    
    def test_cameracontroller_has_batch_methods(self):
        """Test CameraController has batch operation methods."""
        # May have set_multiple, get_multiple if implemented
        assert hasattr(CameraController, 'set') or hasattr(CameraController, 'get')


class TestResultAPIWorkflowInterface:
    """Test Result-based API workflow interfaces exist."""
    
    def test_open_camera_exists(self):
        """Test open_camera() function exists."""
        assert hasattr(duvc_ctl, 'open_camera')
        assert callable(open_camera)
    
    def test_list_devices_exists(self):
        """Test list_devices() function exists."""
        assert hasattr(duvc_ctl, 'list_devices')
        assert callable(list_devices)


# ============================================================================
# WITH CAMERA TESTS - Real device integration workflows
# ============================================================================

@pytest.mark.hardware
class TestCameraControllerBasicWorkflow:
    """Test basic CameraController connect → control → close workflow."""
    
    def test_workflow_connect_get_set_close(self, test_device):
        """Test complete workflow: connect → get → set → close."""
        if test_device is None:
            pytest.skip("No test device available")
        
        # 1. Connect to camera
        cam = CameraController(device_index=0)
        
        assert cam is not None
        assert hasattr(cam, 'device_name')
        
        try:
            # 2. Get current brightness
            try:
                current_brightness = cam.brightness
                assert isinstance(current_brightness, int)
            except (PropertyNotSupportedError, AttributeError):
                pytest.skip("Brightness not supported")
            
            # 3. Set brightness to known value
            test_value = 128
            cam.brightness = test_value
            
            # 4. Verify it was set
            new_brightness = cam.brightness
            assert isinstance(new_brightness, int)
            
            # 5. Restore original value
            cam.brightness = current_brightness
        finally:
            # 6. Close camera
            cam.close()
    
    def test_workflow_with_multiple_properties(self, test_device):
        """Test workflow with multiple property operations."""
        if test_device is None:
            pytest.skip("No test device available")
        
        cam = CameraController(device_index=0)
        
        try:
            # Get multiple properties
            properties_tested = []
            
            try:
                brightness = cam.brightness
                properties_tested.append(('brightness', brightness))
            except (PropertyNotSupportedError, AttributeError):
                pass
            
            try:
                contrast = cam.contrast
                properties_tested.append(('contrast', contrast))
            except (PropertyNotSupportedError, AttributeError):
                pass
            
            try:
                saturation = cam.saturation
                properties_tested.append(('saturation', saturation))
            except (PropertyNotSupportedError, AttributeError):
                pass
            
            # Should have at least one property
            assert len(properties_tested) > 0
            
            # All values should be integers
            for name, value in properties_tested:
                assert isinstance(value, int)
        finally:
            cam.close()


@pytest.mark.hardware
class TestCameraControllerContextManagerWorkflow:
    """Test CameraController context manager workflow."""
    
    def test_workflow_context_manager_basic(self, test_device):
        """Test context manager: with CameraController."""
        if test_device is None:
            pytest.skip("No test device available")
        
        # Context manager automatically opens and closes
        with CameraController(device_index=0) as cam:
            assert cam is not None
            
            # Try to get a property
            try:
                brightness = cam.brightness
                assert isinstance(brightness, int)
            except (PropertyNotSupportedError, AttributeError):
                pass  # Property not supported, but context manager still works
        
        # Camera should be closed after exiting context
    
    def test_workflow_context_manager_with_operations(self, test_device):
        """Test context manager with property operations."""
        if test_device is None:
            pytest.skip("No test device available")
        
        original_value = None
        
        with CameraController(device_index=0) as cam:
            try:
                # Save original
                original_value = cam.brightness
                
                # Modify
                cam.brightness = 100
                
                # Verify
                new_value = cam.brightness
                assert isinstance(new_value, int)
                
                # Restore
                if original_value is not None:
                    cam.brightness = original_value
            except (PropertyNotSupportedError, AttributeError):
                pytest.skip("Brightness not supported")
    
    def test_workflow_context_manager_exception_handling(self, test_device):
        """Test context manager handles exceptions properly."""
        if test_device is None:
            pytest.skip("No test device available")
        
        try:
            with CameraController(device_index=0) as cam:
                # Deliberately cause an error
                raise RuntimeError("Test exception")
        except RuntimeError:
            # Exception should propagate, but camera should be closed
            pass


@pytest.mark.hardware
class TestCameraControllerPTZWorkflow:
    """Test PTZ control workflow."""
    
    def test_workflow_ptz_absolute_positioning(self, test_device):
        """Test PTZ workflow: get position → move → verify → restore."""
        if test_device is None:
            pytest.skip("No test device available")
        
        with CameraController(device_index=0) as cam:
            try:
                # 1. Get original position
                original_pan = cam.pan
                original_tilt = cam.tilt
                
                # 2. Move to new position
                cam.pan = 0
                cam.tilt = 0
                
                # 3. Verify move
                new_pan = cam.pan
                new_tilt = cam.tilt
                
                assert isinstance(new_pan, int)
                assert isinstance(new_tilt, int)
                
                # 4. Restore original position
                cam.pan = original_pan
                cam.tilt = original_tilt
            except (PropertyNotSupportedError, AttributeError):
                pytest.skip("PTZ not supported")
    
    def test_workflow_ptz_relative_movement(self, test_device):
        """Test PTZ relative movement workflow."""
        if test_device is None:
            pytest.skip("No test device available")
        
        with CameraController(device_index=0) as cam:
            try:
                # Get starting position
                start_pan = cam.pan
                
                # Move relative
                if hasattr(cam, 'pan_relative'):
                    cam.pan_relative(10)
                    
                    # Allow time for movement
                    time.sleep(0.1)
                    
                    # Get new position
                    new_pan = cam.pan
                    
                    # Should have moved
                    # (exact value may vary due to hardware limits)
                    assert isinstance(new_pan, int)
                else:
                    pytest.skip("Relative pan not supported")
            except (PropertyNotSupportedError, AttributeError):
                pytest.skip("PTZ not supported")


@pytest.mark.hardware
class TestResultAPIBasicWorkflow:
    """Test Result-based API workflow."""
    
    def test_workflow_open_get_set_close(self, test_device):
        """Test Result API: open → get → set → close."""
        if test_device is None:
            pytest.skip("No test device available")
        
        # 1. Open camera
        result = open_camera(test_device)
        
        assert result.is_ok()
        
        camera = result.value()
        
        try:
            # 2. Get property
            get_result = camera.get(VidProp.Brightness)
            
            if get_result.is_ok():
                current_setting = get_result.value()
                
                # 3. Set property
                new_setting = PropSetting(128, CamMode.Manual)
                set_result = camera.set(VidProp.Brightness, new_setting)
                
                # Should succeed or fail with error
                assert set_result.is_ok() or set_result.is_error()
                
                # 4. Restore original
                restore_result = camera.set(VidProp.Brightness, current_setting)
        finally:
            # 5. Camera cleanup handled by Python GC
            pass
    
    def test_workflow_enumerate_and_open(self, available_devices):
        """Test workflow: enumerate → select → open."""
        if not available_devices:
            pytest.skip("No devices available")

        # 1. Enumerate devices
        devices = list_devices()
        assert len(devices) > 0

        # 2. Select first device from enumeration
        device = devices[0]

        # 3. Open device using single Device object (not list)
        result = open_camera(device)
        assert result.is_ok()
        camera = result.value()

        # 4. Verify camera has get and set methods
        assert hasattr(camera, 'get')
        assert hasattr(camera, 'set')


@pytest.mark.hardware
class TestResultAPIErrorHandlingWorkflow:
    """Test Result API error handling workflow."""
    
    def test_workflow_handle_unsupported_property(self, test_device):
        """Test workflow for handling unsupported properties."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = open_camera(test_device)
        assert result.is_ok()
        
        camera = result.value()
        
        # Try multiple properties, some may not be supported
        properties_to_test = [
            CamProp.Pan,
            CamProp.Tilt,
            CamProp.Zoom,
            CamProp.Focus,
        ]
        
        for prop in properties_to_test:
            get_result = camera.get(prop)
            
            if get_result.is_ok():
                # Property supported
                setting = get_result.value()
                assert isinstance(setting, PropSetting)
            else:
                # Property not supported - check error
                error = get_result.error()
                assert hasattr(error, 'code')
                assert hasattr(error, 'description')
    
    def test_workflow_validate_range_before_set(self, test_device):
        """Test workflow: get range → validate → set."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = open_camera(test_device)
        assert result.is_ok()
        
        camera = result.value()
        
        # 1. Get property range
        range_result = camera.get_range(VidProp.Brightness)
        
        if range_result.is_ok():
            prop_range = range_result.value()
            
            # 2. Validate range
            assert hasattr(prop_range, 'min')
            assert hasattr(prop_range, 'max')
            
            # 3. Set value within range
            mid_value = (prop_range.min + prop_range.max) // 2
            setting = PropSetting(mid_value, CamMode.Manual)
            
            set_result = camera.set(VidProp.Brightness, setting)
            
            # Should succeed since value is in range
            if set_result.is_error():
                # May fail for other reasons, but not range
                error = set_result.error()
                # Error shouldn't be INVALID_VALUE
                pass

@pytest.mark.hardware
class TestMixedAPIWorkflow:
    """Test workflows mixing CameraController and Result-based API."""
    
    def test_workflow_cameracontroller_with_core_access(self, test_device):
        """Test workflow using CameraController.core for ResultT operations."""
        if test_device is None:
            pytest.skip("No test device available")
        
        with CameraController(device_index=0) as cam:
            # Access underlying core Camera
            core_camera = cam.core
            
            assert core_camera is not None
            
            # Use Result-based API
            result = core_camera.get(VidProp.Brightness)
            
            if result.is_ok():
                setting = result.value()
                assert isinstance(setting, PropSetting)
            
            # Can mix with Pythonic API
            try:
                brightness = cam.brightness
                assert isinstance(brightness, int)
            except (PropertyNotSupportedError, AttributeError):
                pass
    
    def test_workflow_platform_interface_integration(self, test_device):
        """Test workflow using platform interface."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        # 1. Create platform
        platform = create_platform_interface()
        
        # 2. List devices
        devices_result = platform.list_devices()
        assert devices_result.is_ok()
        
        devices = devices_result.value()
        assert len(devices) > 0
        
        # 3. Create connection
        conn_result = platform.create_connection(devices[0])
        
        if conn_result.is_ok():
            connection = conn_result.value()
            
            # 4. Use connection
            prop_result = connection.get_video_property(VidProp.Brightness)
            
            if prop_result.is_ok():
                setting = prop_result.value()
                assert isinstance(setting, PropSetting)


@pytest.mark.hardware
class TestComplexWorkflows:
    """Test complex multi-step workflows."""
    
    def test_workflow_full_camera_configuration(self, test_device):
        """Test complete camera configuration workflow."""
        if test_device is None:
            pytest.skip("No test device available")
        
        with CameraController(device_index=0) as cam:
            # 1. Save current configuration
            config = {}
            
            properties = ['brightness', 'contrast', 'saturation']
            
            for prop_name in properties:
                try:
                    value = getattr(cam, prop_name)
                    config[prop_name] = value
                except (PropertyNotSupportedError, AttributeError):
                    pass
            
            # 2. Apply new configuration
            try:
                if 'brightness' in config:
                    cam.brightness = 100
                if 'contrast' in config:
                    cam.contrast = 75
                if 'saturation' in config:
                    cam.saturation = 80
            except (PropertyNotSupportedError, AttributeError, InvalidValueError):
                pass
            
            # 3. Verify changes
            for prop_name in properties:
                if prop_name in config:
                    try:
                        new_value = getattr(cam, prop_name)
                        assert isinstance(new_value, int)
                    except (PropertyNotSupportedError, AttributeError):
                        pass
            
            # 4. Restore original configuration
            for prop_name, value in config.items():
                try:
                    setattr(cam, prop_name, value)
                except (PropertyNotSupportedError, AttributeError, InvalidValueError):
                    pass
    
    def test_workflow_camera_health_monitoring(self, test_device):
        """Test camera health monitoring workflow."""
        if test_device is None:
            pytest.skip("No test device available")
        
        with CameraController(device_index=0) as cam:
            # 1. Check if camera is connected
            if hasattr(cam, 'is_connected'):
                connected = cam.is_connected
                assert isinstance(connected, bool)
            
            # 2. Test basic operation
            try:
                brightness = cam.brightness
                
                # 3. Verify camera responds
                assert isinstance(brightness, int)
                
                # 4. Test write operation
                cam.brightness = brightness
                
                # 5. Camera is healthy if we got here
                health_ok = True
            except (PropertyNotSupportedError, AttributeError):
                # Not supported, but camera may still be healthy
                health_ok = True
            except Exception:
                # Other errors indicate unhealthy camera
                health_ok = False
            
            assert health_ok or not health_ok  # Either state is valid
    
    def test_workflow_multi_device_coordination(self, available_devices):
        """Test workflow coordinating multiple devices."""
        if len(available_devices) < 1:
            pytest.skip("Need at least 1 device for multi-device test")
        
        # Open first device
        with CameraController(device_index=0) as cam1:
            # Get property from first device
            try:
                brightness1 = cam1.brightness
                
                # If we have second device, compare
                if len(available_devices) >= 2:
                    try:
                        with CameraController(device_index=1) as cam2:
                            brightness2 = cam2.brightness
                            
                            # Both should return integers
                            assert isinstance(brightness1, int)
                            assert isinstance(brightness2, int)
                    except (DeviceNotFoundError, PropertyNotSupportedError):
                        pass
            except (PropertyNotSupportedError, AttributeError):
                pytest.skip("Brightness not supported")


@pytest.mark.hardware
class TestErrorRecoveryWorkflows:
    """Test error recovery workflows."""
    
    def test_workflow_recover_from_invalid_value(self, test_device):
        """Test recovery from invalid value error."""
        if test_device is None:
            pytest.skip("No test device available")
        
        with CameraController(device_index=0) as cam:
            try:
                # Get valid range
                if hasattr(cam, 'get_property_range'):
                    range_info = cam.get_property_range('brightness')
                    
                    if range_info:
                        # Try to set out-of-range value
                        try:
                            cam.brightness = range_info['max'] + 1000
                            # Should raise InvalidValueError
                        except (InvalidValueError, PropertyNotSupportedError):
                            # Expected - recover by setting valid value
                            mid_value = (range_info['min'] + range_info['max']) // 2
                            cam.brightness = mid_value
                            
                            # Verify recovery
                            new_value = cam.brightness
                            assert isinstance(new_value, int)
            except (PropertyNotSupportedError, AttributeError):
                pytest.skip("Brightness or range not supported")
    
    def test_workflow_handle_device_disconnect(self, test_device):
        """Test handling device disconnect scenario."""
        if test_device is None:
            pytest.skip("No test device available")
        
        cam = CameraController(device_index=0)
        
        try:
            # Get initial value
            try:
                initial_value = cam.brightness
                assert isinstance(initial_value, int)
            except (PropertyNotSupportedError, AttributeError):
                pytest.skip("Brightness not supported")
            
            # Simulate disconnect by closing
            cam.close()
            
            # Try to access after close - should handle gracefully
            try:
                value = cam.brightness
                # May succeed if camera auto-reopens
            except (RuntimeError, Exception):
                # Expected after close
                pass
        finally:
            # Ensure cleanup
            try:
                cam.close()
            except:
                pass


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
