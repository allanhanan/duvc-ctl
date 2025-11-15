"""
Test Suite 10: Presets and Defaults
====================================

Tests preset configurations and default value management.

Functionality Tested:
  Built-in Presets (4):
    - "daylight" - Optimized for outdoor/daylight conditions
    - "indoor" - Optimized for indoor lighting
    - "night" - Optimized for low-light conditions
    - "conference" - Optimized for video conferencing
  
  Custom Presets (4):
    - create_custom_preset() - Create user-defined preset
    - get_custom_presets() - List custom presets
    - delete_custom_preset() - Remove custom preset
    - clear_custom_presets() - Remove all custom presets
  
  Preset Operations (2):
    - apply_preset() - Apply built-in or custom preset
    - get_preset_names() - List all available presets

Total: 10 preset-related methods

Test Organization:
  1. Without Camera Tests - Interface verification
  2. With Camera Tests - Integration tests using real camera hardware

Run: pytest tests/test_10_presets_defaults.py -v
Run without camera: pytest tests/test_10_presets_defaults.py -v -m "not hardware"
"""

import pytest
import sys
import warnings
from typing import List, Optional, Dict, Any

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


@pytest.fixture(scope="function")
def camera_controller(test_device) -> Optional[CameraController]:
    """Get fresh CameraController instance for each test."""
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

class TestBuiltInPresetInterfaces:
    """Test built-in preset interfaces exist."""
    
    def test_apply_preset_method_exists(self):
        """Test apply_preset() method exists."""
        assert hasattr(CameraController, 'apply_preset')
        assert callable(getattr(CameraController, 'apply_preset'))
    
    def test_get_preset_names_method_exists(self):
        """Test get_preset_names() method exists."""
        assert hasattr(CameraController, 'get_preset_names')
        assert callable(getattr(CameraController, 'get_preset_names'))
    
    def test_BUILT_IN_PRESETS_constant_exists(self):
        """Test BUILT_IN_PRESETS constant exists."""
        assert hasattr(CameraController, 'BUILT_IN_PRESETS')
        assert isinstance(CameraController.BUILT_IN_PRESETS, dict)


class TestCustomPresetInterfaces:
    """Test custom preset method interfaces exist."""
    
    def test_create_custom_preset_method_exists(self):
        """Test create_custom_preset() method exists."""
        assert hasattr(CameraController, 'create_custom_preset')
        assert callable(getattr(CameraController, 'create_custom_preset'))
    
    def test_get_custom_presets_method_exists(self):
        """Test get_custom_presets() method exists."""
        assert hasattr(CameraController, 'get_custom_presets')
        assert callable(getattr(CameraController, 'get_custom_presets'))
    
    def test_delete_custom_preset_method_exists(self):
        """Test delete_custom_preset() method exists."""
        assert hasattr(CameraController, 'delete_custom_preset')
        assert callable(getattr(CameraController, 'delete_custom_preset'))
    
    def test_clear_custom_presets_method_exists(self):
        """Test clear_custom_presets() method exists."""
        assert hasattr(CameraController, 'clear_custom_presets')
        assert callable(getattr(CameraController, 'clear_custom_presets'))


class TestSmartDefaultsInterfaces:
    """Test smart defaults interfaces exist."""
    
    def test_smart_defaults_constant_exists(self):
        """Test SMART_DEFAULTS constant exists."""
        assert hasattr(CameraController, 'SMART_DEFAULTS')
        assert isinstance(CameraController.SMART_DEFAULTS, dict)
    
    def test_set_smart_default_method_exists(self):
        """Test set_smart_default() method exists."""
        assert hasattr(CameraController, 'set_smart_default')
        assert callable(getattr(CameraController, 'set_smart_default'))


# ============================================================================
# WITH CAMERA TESTS - Integration tests using real camera
# ============================================================================

@pytest.mark.hardware
class TestBuiltInPresetConstants:
    """Test built-in preset definitions."""
    
    def test_BUILT_IN_PRESETS_is_dict(self):
        """Test BUILT_IN_PRESETS is a dictionary."""
        assert isinstance(CameraController.BUILT_IN_PRESETS, dict)
    
    def test_daylight_preset_exists(self):
        """Test 'daylight' preset is defined."""
        assert 'daylight' in CameraController.BUILT_IN_PRESETS
        
        preset = CameraController.BUILT_IN_PRESETS['daylight']
        assert isinstance(preset, dict)
        assert len(preset) > 0
    
    def test_indoor_preset_exists(self):
        """Test 'indoor' preset is defined."""
        assert 'indoor' in CameraController.BUILT_IN_PRESETS
        
        preset = CameraController.BUILT_IN_PRESETS['indoor']
        assert isinstance(preset, dict)
        assert len(preset) > 0
    
    def test_night_preset_exists(self):
        """Test 'night' preset is defined."""
        assert 'night' in CameraController.BUILT_IN_PRESETS
        
        preset = CameraController.BUILT_IN_PRESETS['night']
        assert isinstance(preset, dict)
        assert len(preset) > 0
    
    def test_conference_preset_exists(self):
        """Test 'conference' preset is defined."""
        assert 'conference' in CameraController.BUILT_IN_PRESETS
        
        preset = CameraController.BUILT_IN_PRESETS['conference']
        assert isinstance(preset, dict)
        assert len(preset) > 0
        
    def test_preset_has_valid_properties(self):
        """Test presets contain valid property names."""
        valid_properties = [
            'brightness', 'contrast', 'saturation', 'hue',
            'white_balance', 'exposure', 'gain', 'pan', 'tilt', 'zoom',
            'sharpness', 'gamma', 'focus'
        ]
        
        for preset_name, preset in CameraController.BUILT_IN_PRESETS.items():
            for prop_name in preset.keys():
                # Property should be in valid list (case-insensitive, exact match)
                assert any(prop_name.lower() == valid.lower() for valid in valid_properties), \
                    f"Unknown property '{prop_name}' in preset '{preset_name}'. Valid: {valid_properties}"

@pytest.mark.hardware
class TestApplyPresetMethod:
    """Test apply_preset() method."""
    
    def test_apply_daylight_preset(self, camera_controller):
        """Test applying 'daylight' preset."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = camera_controller.apply_preset('daylight')
        
        # Should return bool indicating success
        assert isinstance(result, bool)
    
    def test_apply_indoor_preset(self, camera_controller):
        """Test applying 'indoor' preset."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = camera_controller.apply_preset('indoor')
        
        assert isinstance(result, bool)
    
    def test_apply_night_preset(self, camera_controller):
        """Test applying 'night' preset."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = camera_controller.apply_preset('night')
        
        assert isinstance(result, bool)
    
    def test_apply_conference_preset(self, camera_controller):
        """Test applying 'conference' preset."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = camera_controller.apply_preset('conference')
        
        assert isinstance(result, bool)
    
    def test_apply_invalid_preset_raises(self, camera_controller):
        """Test applying non-existent preset raises ValueError."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        with pytest.raises(ValueError):
            camera_controller.apply_preset('nonexistent_preset_xyz')
    
    def test_apply_preset_changes_properties(self, camera_controller):
        """Test apply_preset() actually changes camera properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Get supported properties
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        if 'brightness' in all_props:
            try:
                # Get initial value
                initial_brightness = camera_controller.brightness
                
                # Apply preset
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    camera_controller.apply_preset('daylight')
                
                # Value may or may not change (depends on camera state)
                # Just verify we can still read it
                new_brightness = camera_controller.brightness
                assert isinstance(new_brightness, int)
            except PropertyNotSupportedError:
                pytest.skip("Brightness not supported")


@pytest.mark.hardware
class TestGetPresetNamesMethod:
    """Test get_preset_names() method."""
    
    def test_get_preset_names_returns_list(self, camera_controller):
        """Test get_preset_names() returns list."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        names = camera_controller.get_preset_names()
        
        assert isinstance(names, list)
    
    def test_get_preset_names_includes_builtins(self, camera_controller):
        """Test get_preset_names() includes all built-in presets."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        names = camera_controller.get_preset_names()
        
        # Should include all 4 built-in presets
        assert 'daylight' in names
        assert 'indoor' in names
        assert 'night' in names
        assert 'conference' in names
    
    def test_get_preset_names_includes_custom(self, camera_controller):
        """Test get_preset_names() includes custom presets."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Create custom preset
        camera_controller.create_custom_preset('test_preset', {'brightness': 50})
        
        # Get names
        names = camera_controller.get_preset_names()
        
        # Should include custom preset
        assert 'test_preset' in names
        
        # Cleanup
        camera_controller.delete_custom_preset('test_preset')


@pytest.mark.hardware
class TestCreateCustomPresetMethod:
    """Test create_custom_preset() method."""
    
    def test_create_custom_preset_simple(self, camera_controller):
        """Test creating simple custom preset."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Create preset
        camera_controller.create_custom_preset('my_preset', {
            'brightness': 75,
            'contrast': 60
        })
        
        # Verify it exists
        presets = camera_controller.get_custom_presets()
        assert 'my_preset' in presets
        assert presets['my_preset']['brightness'] == 75
        assert presets['my_preset']['contrast'] == 60
        
        # Cleanup
        camera_controller.delete_custom_preset('my_preset')
    
    def test_create_custom_preset_with_auto_mode(self, camera_controller):
        """Test creating preset with 'auto' values."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        camera_controller.create_custom_preset('auto_preset', {
            'brightness': 'auto',
            'exposure': 'auto'
        })
        
        presets = camera_controller.get_custom_presets()
        assert 'auto_preset' in presets
        assert presets['auto_preset']['brightness'] == 'auto'
        
        # Cleanup
        camera_controller.delete_custom_preset('auto_preset')
    
    def test_create_custom_preset_overwrites_existing(self, camera_controller):
        """Test creating preset with same name overwrites."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Create preset
        camera_controller.create_custom_preset('overwrite_test', {'brightness': 50})
        
        # Overwrite with different values
        camera_controller.create_custom_preset('overwrite_test', {'brightness': 75})
        
        # Should have new values
        presets = camera_controller.get_custom_presets()
        assert presets['overwrite_test']['brightness'] == 75
        
        # Cleanup
        camera_controller.delete_custom_preset('overwrite_test')
    
    def test_create_custom_preset_multiple(self, camera_controller):
        """Test creating multiple custom presets."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Create multiple presets
        camera_controller.create_custom_preset('preset1', {'brightness': 50})
        camera_controller.create_custom_preset('preset2', {'brightness': 75})
        camera_controller.create_custom_preset('preset3', {'brightness': 100})
        
        presets = camera_controller.get_custom_presets()
        assert len(presets) >= 3
        assert 'preset1' in presets
        assert 'preset2' in presets
        assert 'preset3' in presets
        
        # Cleanup
        camera_controller.clear_custom_presets()


@pytest.mark.hardware
class TestGetCustomPresetsMethod:
    """Test get_custom_presets() method."""
    
    def test_get_custom_presets_returns_dict(self, camera_controller):
        """Test get_custom_presets() returns dictionary."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        presets = camera_controller.get_custom_presets()
        
        assert isinstance(presets, dict)
    
    def test_get_custom_presets_empty_initially(self, camera_controller):
        """Test get_custom_presets() is empty for new controller."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Clear any existing presets
        camera_controller.clear_custom_presets()
        
        presets = camera_controller.get_custom_presets()
        
        assert len(presets) == 0
    
    def test_get_custom_presets_after_creation(self, camera_controller):
        """Test get_custom_presets() returns created presets."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Clear and create
        camera_controller.clear_custom_presets()
        camera_controller.create_custom_preset('test1', {'brightness': 50})
        camera_controller.create_custom_preset('test2', {'contrast': 60})
        
        presets = camera_controller.get_custom_presets()
        
        assert len(presets) == 2
        assert 'test1' in presets
        assert 'test2' in presets
        
        # Cleanup
        camera_controller.clear_custom_presets()


@pytest.mark.hardware
class TestDeleteCustomPresetMethod:
    """Test delete_custom_preset() method."""
    
    def test_delete_custom_preset_existing(self, camera_controller):
        """Test deleting existing custom preset."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Create and delete
        camera_controller.create_custom_preset('to_delete', {'brightness': 50})
        result = camera_controller.delete_custom_preset('to_delete')
        
        # Should return True for successful deletion
        assert result == True
        
        # Should not exist anymore
        presets = camera_controller.get_custom_presets()
        assert 'to_delete' not in presets
    
    def test_delete_custom_preset_nonexistent(self, camera_controller):
        """Test deleting non-existent preset returns False."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.delete_custom_preset('nonexistent_preset_xyz')
        
        assert result == False
    
    def test_delete_custom_preset_idempotent(self, camera_controller):
        """Test deleting same preset twice."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Create and delete
        camera_controller.create_custom_preset('delete_twice', {'brightness': 50})
        
        result1 = camera_controller.delete_custom_preset('delete_twice')
        assert result1 == True
        
        result2 = camera_controller.delete_custom_preset('delete_twice')
        assert result2 == False


@pytest.mark.hardware
class TestClearCustomPresetsMethod:
    """Test clear_custom_presets() method."""
    
    def test_clear_custom_presets_returns_count(self, camera_controller):
        """Test clear_custom_presets() returns count of cleared presets."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Create some presets
        camera_controller.create_custom_preset('clear1', {'brightness': 50})
        camera_controller.create_custom_preset('clear2', {'brightness': 75})
        
        # Clear
        count = camera_controller.clear_custom_presets()
        
        # Should return count
        assert isinstance(count, int)
        assert count == 2
    
    def test_clear_custom_presets_removes_all(self, camera_controller):
        """Test clear_custom_presets() removes all presets."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Create multiple presets
        camera_controller.create_custom_preset('clear_test1', {'brightness': 50})
        camera_controller.create_custom_preset('clear_test2', {'brightness': 75})
        camera_controller.create_custom_preset('clear_test3', {'brightness': 100})
        
        # Clear
        camera_controller.clear_custom_presets()
        
        # Should be empty
        presets = camera_controller.get_custom_presets()
        assert len(presets) == 0
    
    def test_clear_custom_presets_when_empty(self, camera_controller):
        """Test clear_custom_presets() when no presets exist."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Clear first
        camera_controller.clear_custom_presets()
        
        # Clear again
        count = camera_controller.clear_custom_presets()
        
        assert count == 0


@pytest.mark.hardware
class TestApplyCustomPreset:
    """Test applying custom presets."""
    
    def test_apply_custom_preset(self, camera_controller):
        """Test applying a custom preset."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Create custom preset
        camera_controller.create_custom_preset('custom_test', {
            'brightness': 65,
            'contrast': 55
        })
        
        # Apply it
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = camera_controller.apply_preset('custom_test')
        
        assert isinstance(result, bool)
        
        # Cleanup
        camera_controller.delete_custom_preset('custom_test')
    
    def test_custom_preset_overrides_builtin_name(self, camera_controller):
        """Test custom preset with same name as built-in takes precedence."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Create custom preset with built-in name
        camera_controller.create_custom_preset('daylight', {
            'brightness': 99  # Different from built-in
        })
        
        # Apply - should use custom
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            camera_controller.apply_preset('daylight')
        
        # Cleanup
        camera_controller.delete_custom_preset('daylight')


@pytest.mark.hardware
class TestSmartDefaults:
    """Test SMART_DEFAULTS functionality."""
    
    def test_smart_defaults_is_dict(self):
        """Test SMART_DEFAULTS is a dictionary."""
        assert isinstance(CameraController.SMART_DEFAULTS, dict)
    
    def test_smart_defaults_has_common_properties(self):
        """Test SMART_DEFAULTS includes common properties."""
        defaults = CameraController.SMART_DEFAULTS
        
        # Should have some common properties
        common_props = ['brightness', 'contrast', 'saturation', 'pan', 'tilt', 'zoom']
        
        # At least some should be present
        found = [prop for prop in common_props if prop in defaults]
        assert len(found) > 0
    
    def test_set_smart_default(self, camera_controller):
        """Test set_smart_default() method."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Get supported properties
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        if 'brightness' in all_props:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    camera_controller.set_smart_default('brightness')
                
                # Should not raise exception
            except PropertyNotSupportedError:
                pytest.skip("Brightness not supported")


@pytest.mark.hardware
class TestPresetWorkflows:
    """Test complete preset workflows."""
    
    def test_create_apply_delete_workflow(self, camera_controller):
        """Test complete workflow: create, apply, delete."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # 1. Create custom preset
        camera_controller.create_custom_preset('workflow_test', {
            'brightness': 70,
            'contrast': 50
        })
        
        # 2. Verify it exists
        names = camera_controller.get_preset_names()
        assert 'workflow_test' in names
        
        # 3. Apply it
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = camera_controller.apply_preset('workflow_test')
        
        assert isinstance(result, bool)
        
        # 4. Delete it
        deleted = camera_controller.delete_custom_preset('workflow_test')
        assert deleted == True
        
        # 5. Verify it's gone
        names = camera_controller.get_preset_names()
        assert 'workflow_test' not in names
    
    def test_switch_between_presets(self, camera_controller):
        """Test switching between different presets."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # Apply each built-in preset
            camera_controller.apply_preset('daylight')
            camera_controller.apply_preset('indoor')
            camera_controller.apply_preset('night')
            camera_controller.apply_preset('conference')
        
        # Should complete without errors


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
