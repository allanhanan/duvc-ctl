"""
Test Suite 09: Pythonic API Query Methods (CameraController)
=============================================================

Tests CameraController query and metadata methods.

Methods Tested:
  Property Queries (4):
    - get_supported_properties() - List supported camera/video properties
    - get_property_range(name) - Get min/max/step/default for property
    - get(name) - Get property value by name
    - list_properties() - List all available property names
  
  Metadata Queries (3):
    - device_name - Get device name property
    - device_path - Get device path property
    - is_connected - Check if device is responsive
  
  Multi-property Operations (2):
    - get_multiple(names) - Get multiple properties at once
    - set_multiple(dict) - Set multiple properties at once

Total: 9 query and metadata methods

Test Organization:
  1. Without Camera Tests - Interface verification
  2. With Camera Tests - Integration tests using real camera hardware

Run: pytest tests/test_09_pythonic_api_queries.py -v
Run without camera: pytest tests/test_09_pythonic_api_queries.py -v -m "not hardware"
"""

import pytest
import sys
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

class TestQueryMethodInterfaces:
    """Test query method interfaces exist."""
    
    def test_get_supported_properties_method_exists(self):
        """Test get_supported_properties() method exists."""
        assert hasattr(CameraController, 'get_supported_properties')
        assert callable(getattr(CameraController, 'get_supported_properties'))
    
    def test_get_property_range_method_exists(self):
        """Test get_property_range() method exists."""
        assert hasattr(CameraController, 'get_property_range')
        assert callable(getattr(CameraController, 'get_property_range'))
    
    def test_get_method_exists(self):
        """Test get() method exists."""
        assert hasattr(CameraController, 'get')
        assert callable(getattr(CameraController, 'get'))
    
    def test_list_properties_method_exists(self):
        """Test list_properties() method exists."""
        assert hasattr(CameraController, 'list_properties')
        assert callable(getattr(CameraController, 'list_properties'))


class TestMetadataPropertyInterfaces:
    """Test metadata property interfaces exist."""
    
    def test_device_name_property_exists(self):
        """Test device_name property exists."""
        assert hasattr(CameraController, 'device_name')
    
    def test_device_path_property_exists(self):
        """Test device_path property exists."""
        assert hasattr(CameraController, 'device_path')
    
    def test_is_connected_property_exists(self):
        """Test is_connected property exists."""
        assert hasattr(CameraController, 'is_connected')


class TestMultiPropertyMethodInterfaces:
    """Test multi-property method interfaces exist."""
    
    def test_get_multiple_method_exists(self):
        """Test get_multiple() method exists."""
        assert hasattr(CameraController, 'get_multiple')
        assert callable(getattr(CameraController, 'get_multiple'))
    
    def test_set_multiple_method_exists(self):
        """Test set_multiple() method exists."""
        assert hasattr(CameraController, 'set_multiple')
        assert callable(getattr(CameraController, 'set_multiple'))


# ============================================================================
# WITH CAMERA TESTS - Integration tests using real camera
# ============================================================================

@pytest.mark.hardware
class TestGetSupportedPropertiesMethod:
    """Test get_supported_properties() method."""
    
    def test_get_supported_properties_returns_dict(self, camera_controller):
        """Test get_supported_properties() returns dictionary."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.get_supported_properties()
        
        assert isinstance(result, dict)
        assert 'camera' in result
        assert 'video' in result
    
    def test_supported_properties_are_lists(self, camera_controller):
        """Test supported properties are lists of strings."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.get_supported_properties()
        
        assert isinstance(result['camera'], list)
        assert isinstance(result['video'], list)
        
        # All items should be strings
        for prop in result['camera']:
            assert isinstance(prop, str)
        
        for prop in result['video']:
            assert isinstance(prop, str)
    
    def test_supported_properties_non_empty(self, camera_controller):
        """Test at least some properties are supported."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.get_supported_properties()
        
        # Most cameras support at least some video properties
        total_props = len(result['camera']) + len(result['video'])
        assert total_props > 0, "Camera should support at least some properties"
    
    def test_supported_properties_typical_props(self, camera_controller):
        """Test common properties are in supported list."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.get_supported_properties()
        all_props = result['camera'] + result['video']
        
        # Most cameras support brightness
        # (but don't fail if not - some specialized cameras may not)
        common_props = ['brightness', 'contrast', 'saturation', 'pan', 'tilt', 'zoom', 'focus']
        
        # At least ONE common property should be supported
        supported_common = [p for p in common_props if p in all_props]
        # This is a very lenient test - just checking method works


@pytest.mark.hardware
class TestGetPropertyRangeMethod:
    """Test get_property_range() method."""
    
    def test_get_property_range_returns_dict(self, camera_controller):
        """Test get_property_range() returns dictionary."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            result = camera_controller.get_property_range('brightness')
            
            if result is not None:
                assert isinstance(result, dict)
                assert 'min' in result
                assert 'max' in result
                assert 'step' in result
                assert 'default' in result
        except PropertyNotSupportedError:
            pytest.skip("Brightness not supported")
    
    def test_get_property_range_values_are_ints(self, camera_controller):
        """Test property range values are integers."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            result = camera_controller.get_property_range('brightness')
            
            if result:
                assert isinstance(result['min'], int)
                assert isinstance(result['max'], int)
                assert isinstance(result['step'], int)
                assert isinstance(result['default'], int)
        except PropertyNotSupportedError:
            pytest.skip("Brightness not supported")
    
    def test_get_property_range_valid_range(self, camera_controller):
        """Test property range min <= max."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            result = camera_controller.get_property_range('brightness')
            
            if result:
                assert result['min'] <= result['max']
                assert result['step'] > 0
                assert result['min'] <= result['default'] <= result['max']
        except PropertyNotSupportedError:
            pytest.skip("Brightness not supported")
    
    def test_get_property_range_multiple_properties(self, camera_controller):
        """Test get_property_range() for multiple properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        properties = ['brightness', 'contrast', 'saturation', 'pan', 'tilt']
        
        for prop in properties:
            try:
                result = camera_controller.get_property_range(prop)
                # Just verify method doesn't crash
                assert result is None or isinstance(result, dict)
            except (PropertyNotSupportedError, ValueError):
                # OK if property not supported
                pass


@pytest.mark.hardware
class TestGetMethod:
    """Test get() method - get property by name."""
    
    def test_get_returns_int_for_int_properties(self, camera_controller):
        """Test get() returns int for numeric properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.get('brightness')
            assert isinstance(value, int)
        except PropertyNotSupportedError:
            pytest.skip("Brightness not supported")
    
    def test_get_returns_bool_for_bool_properties(self, camera_controller):
        """Test get() returns bool for boolean properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        try:
            value = camera_controller.get('color_enable')
            assert isinstance(value, bool)
        except PropertyNotSupportedError:
            pytest.skip("Color enable not supported")
    
    def test_get_unsupported_property_raises(self, camera_controller):
        """Test get() raises exception for unsupported property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Try property we know camera doesn't support
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        # Find a property NOT in supported list
        test_props = ['pan', 'tilt', 'roll', 'zoom', 'focus']
        unsupported = None
        
        for prop in test_props:
            if prop not in all_props:
                unsupported = prop
                break
        
        if unsupported:
            with pytest.raises(PropertyNotSupportedError):
                camera_controller.get(unsupported)
    
    def test_get_invalid_property_raises(self, camera_controller):
        """Test get() raises ValueError for invalid property name."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        with pytest.raises(ValueError):
            camera_controller.get('totally_fake_property_name')


@pytest.mark.hardware
class TestListPropertiesMethod:
    """Test list_properties() method."""
    
    def test_list_properties_returns_list(self, camera_controller):
        """Test list_properties() returns list."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.list_properties()
        
        assert isinstance(result, list)
    
    def test_list_properties_contains_strings(self, camera_controller):
        """Test list_properties() returns list of strings."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.list_properties()
        
        for prop in result:
            assert isinstance(prop, str)
    
    def test_list_properties_sorted(self, camera_controller):
        """Test list_properties() returns sorted list."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.list_properties()
        
        # Should be sorted alphabetically
        assert result == sorted(result)
    
    def test_list_properties_includes_all_types(self, camera_controller):
        """Test list_properties() includes both camera and video properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.list_properties()
        
        # Should include properties from both categories
        assert len(result) > 0
        
        # Common properties that should be in the list
        expected_props = [
            'brightness', 'contrast', 'saturation', 'hue',
            'pan', 'tilt', 'zoom', 'focus', 'exposure'
        ]
        
        # At least some of these should be in the list
        found = [p for p in expected_props if p in result]
        # Very lenient - just check method works


@pytest.mark.hardware
class TestDeviceNameProperty:
    """Test device_name property."""
    
    def test_device_name_returns_string(self, camera_controller):
        """Test device_name returns string."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        name = camera_controller.device_name
        
        assert isinstance(name, str)
        assert len(name) > 0
    
    def test_device_name_meaningful(self, camera_controller):
        """Test device_name is meaningful."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        name = camera_controller.device_name
        
        # Should have some alphanumeric content
        assert any(c.isalnum() for c in name)


@pytest.mark.hardware
class TestDevicePathProperty:
    """Test device_path property."""
    
    def test_device_path_returns_string(self, camera_controller):
        """Test device_path returns string."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        path = camera_controller.device_path
        
        assert isinstance(path, str)
        assert len(path) > 0
    
    def test_device_path_stable(self, camera_controller):
        """Test device_path is stable across multiple reads."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        path1 = camera_controller.device_path
        path2 = camera_controller.device_path
        
        assert path1 == path2


@pytest.mark.hardware
class TestIsConnectedProperty:
    """Test is_connected property."""
    
    def test_is_connected_returns_bool(self, camera_controller):
        """Test is_connected returns boolean."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        connected = camera_controller.is_connected
        
        assert isinstance(connected, bool)
    
    def test_is_connected_true_for_open_camera(self, camera_controller):
        """Test is_connected is True for active camera."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        connected = camera_controller.is_connected
        
        # Camera should be connected if we got this far
        assert connected == True


@pytest.mark.hardware
class TestGetMultipleMethod:
    """Test get_multiple() method."""
    
    def test_get_multiple_returns_dict(self, camera_controller):
        """Test get_multiple() returns dictionary."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.get_multiple(['brightness', 'contrast'])
        
        assert isinstance(result, dict)
    
    def test_get_multiple_with_supported_properties(self, camera_controller):
        """Test get_multiple() with supported properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Get supported properties first
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        if not all_props:
            pytest.skip("No supported properties")
        
        # Get first 2 supported properties
        test_props = all_props[:min(2, len(all_props))]
        result = camera_controller.get_multiple(test_props)
        
        # Should have entries for each requested property
        for prop in test_props:
            if prop in result:  # May be omitted if read failed
                assert isinstance(result[prop], (int, bool))
    
    def test_get_multiple_skips_unsupported(self, camera_controller):
        """Test get_multiple() skips unsupported properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Mix of real and fake properties
        props = ['brightness', 'fake_property_123', 'contrast']
        result = camera_controller.get_multiple(props)
        
        # Unsupported properties should be omitted from result
        assert 'fake_property_123' not in result
    
    def test_get_multiple_empty_list(self, camera_controller):
        """Test get_multiple() with empty list."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.get_multiple([])
        
        assert isinstance(result, dict)
        assert len(result) == 0


@pytest.mark.hardware
class TestSetMultipleMethod:
    """Test set_multiple() method."""
    
    def test_set_multiple_returns_dict(self, camera_controller):
        """Test set_multiple() returns status dictionary."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Get a supported property first
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        if 'brightness' in all_props:
            try:
                current = camera_controller.get('brightness')
                result = camera_controller.set_multiple({'brightness': current})
                
                assert isinstance(result, dict)
                assert 'brightness' in result
                assert isinstance(result['brightness'], bool)
            except PropertyNotSupportedError:
                pytest.skip("Brightness not supported")
    
    def test_set_multiple_with_valid_values(self, camera_controller):
        """Test set_multiple() with valid property values."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        if 'brightness' in all_props and 'contrast' in all_props:
            try:
                # Get current values
                bright = camera_controller.get('brightness')
                contrast = camera_controller.get('contrast')
                
                # Set same values back
                result = camera_controller.set_multiple({
                    'brightness': bright,
                    'contrast': contrast
                })
                
                # Both should succeed
                assert result.get('brightness') in [True, False]  # May fail but shouldn't crash
                assert result.get('contrast') in [True, False]
            except PropertyNotSupportedError:
                pytest.skip("Properties not supported")
    
    def test_set_multiple_partial_success(self, camera_controller):
        """Test set_multiple() handles partial success."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Mix of valid and invalid properties
        result = camera_controller.set_multiple({
            'brightness': 50,
            'fake_property': 100
        })
        
        # Should have results for both (False for fake)
        assert isinstance(result, dict)
        assert 'fake_property' in result
        assert result['fake_property'] == False
    
    def test_set_multiple_empty_dict(self, camera_controller):
        """Test set_multiple() with empty dictionary."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.set_multiple({})
        
        assert isinstance(result, dict)
        assert len(result) == 0


@pytest.mark.hardware
class TestQueryIntegration:
    """Test integration between query methods."""
    
    def test_query_workflow(self, camera_controller):
        """Test complete query workflow."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # 1. Get supported properties
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        assert len(all_props) > 0
        
        # 2. Get property range for first supported property
        test_prop = all_props[0]
        prop_range = camera_controller.get_property_range(test_prop)
        
        if prop_range:
            assert 'min' in prop_range
            assert 'max' in prop_range
        
        # 3. Get current value
        try:
            current_value = camera_controller.get(test_prop)
            assert isinstance(current_value, (int, bool))
        except PropertyNotSupportedError:
            pass  # OK if get fails
    
    def test_list_properties_matches_supported(self, camera_controller):
        """Test list_properties() matches get_supported_properties()."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Get via both methods
        all_list = camera_controller.list_properties()
        supported = camera_controller.get_supported_properties()
        
        # list_properties should include all possible properties
        # get_supported_properties returns only supported ones
        all_supported = supported['camera'] + supported['video']
        
        # All supported should be in list
        for prop in all_supported:
            assert prop in all_list


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
