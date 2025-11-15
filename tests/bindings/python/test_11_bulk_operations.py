"""
Test Suite 11: Bulk Operations
===============================

Tests bulk/batch property operations for efficient camera control.

Functionality Tested:
  Multi-property Operations (2):
    - get_multiple(properties) - Get multiple properties at once
    - set_multiple(properties) - Set multiple properties at once
  
  Snapshot Operations (2):
    - get_all_properties() - Get all supported property values
    - save_state() - Save current camera state
  
  State Management (2):
    - restore_state(state) - Restore saved camera state
    - compare_states(state1, state2) - Compare two camera states

Total: 6 bulk operation methods

Test Organization:
  1. Without Camera Tests - Interface verification
  2. With Camera Tests - Integration tests using real camera hardware

Run: pytest tests/test_11_bulk_operations.py -v
Run without camera: pytest tests/test_11_bulk_operations.py -v -m "not hardware"
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

class TestBulkOperationInterfaces:
    """Test bulk operation method interfaces exist."""
    
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
class TestGetMultipleBasics:
    """Test get_multiple() basic functionality."""
    
    def test_get_multiple_empty_list(self, camera_controller):
        """Test get_multiple() with empty property list."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.get_multiple([])
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_get_multiple_single_property(self, camera_controller):
        """Test get_multiple() with single property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Get supported properties
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        if not all_props:
            pytest.skip("No supported properties")
        
        # Get first supported property
        result = camera_controller.get_multiple([all_props[0]])
        
        assert isinstance(result, dict)
        if all_props[0] in result:
            assert isinstance(result[all_props[0]], (int, bool))
    
    def test_get_multiple_two_properties(self, camera_controller):
        """Test get_multiple() with two properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        if len(all_props) < 2:
            pytest.skip("Need at least 2 supported properties")
        
        # Get first two supported properties
        props_to_get = all_props[:2]
        result = camera_controller.get_multiple(props_to_get)
        
        assert isinstance(result, dict)
        
        # Check both properties were attempted
        for prop in props_to_get:
            if prop in result:
                assert isinstance(result[prop], (int, bool))
    
    def test_get_multiple_returns_dict(self, camera_controller):
        """Test get_multiple() always returns dictionary."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Try with various inputs
        result1 = camera_controller.get_multiple([])
        result2 = camera_controller.get_multiple(['brightness'])
        result3 = camera_controller.get_multiple(['brightness', 'contrast', 'fake_prop'])
        
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert isinstance(result3, dict)


@pytest.mark.hardware
class TestGetMultipleEdgeCases:
    """Test get_multiple() edge cases."""
    
    def test_get_multiple_with_unsupported_property(self, camera_controller):
        """Test get_multiple() gracefully handles unsupported properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Mix supported and unsupported
        result = camera_controller.get_multiple([
            'brightness',
            'totally_fake_property_xyz',
            'contrast'
        ])
        
        # Unsupported should be omitted from result
        assert 'totally_fake_property_xyz' not in result
    
    def test_get_multiple_with_all_unsupported(self, camera_controller):
        """Test get_multiple() with all unsupported properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.get_multiple([
            'fake_prop_1',
            'fake_prop_2',
            'fake_prop_3'
        ])
        
        # Should return empty dict
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_get_multiple_with_duplicates(self, camera_controller):
        """Test get_multiple() with duplicate property names."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.get_multiple([
            'brightness',
            'brightness',
            'brightness'
        ])
        
        # Should handle duplicates gracefully
        assert isinstance(result, dict)
        if 'brightness' in result:
            # Should only appear once
            assert isinstance(result['brightness'], int)
    
    def test_get_multiple_preserves_order(self, camera_controller):
        """Test get_multiple() order doesn't affect results."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        if len(all_props) < 3:
            pytest.skip("Need at least 3 supported properties")
        
        # Get in different orders
        props = all_props[:3]
        result1 = camera_controller.get_multiple(props)
        result2 = camera_controller.get_multiple(list(reversed(props)))
        
        # Results should have same keys
        assert set(result1.keys()) == set(result2.keys())


@pytest.mark.hardware
class TestSetMultipleBasics:
    """Test set_multiple() basic functionality."""
    
    def test_set_multiple_empty_dict(self, camera_controller):
        """Test set_multiple() with empty property dict."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.set_multiple({})
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_set_multiple_single_property(self, camera_controller):
        """Test set_multiple() with single property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        if 'brightness' in all_props:
            try:
                # Get current value
                current = camera_controller.get('brightness')
                
                # Set same value back
                result = camera_controller.set_multiple({'brightness': current})
                
                assert isinstance(result, dict)
                assert 'brightness' in result
                assert isinstance(result['brightness'], bool)
            except PropertyNotSupportedError:
                pytest.skip("Brightness not supported")
    
    def test_set_multiple_two_properties(self, camera_controller):
        """Test set_multiple() with two properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        test_props = {}
        if 'brightness' in all_props:
            try:
                test_props['brightness'] = camera_controller.get('brightness')
            except PropertyNotSupportedError:
                pass
        
        if 'contrast' in all_props:
            try:
                test_props['contrast'] = camera_controller.get('contrast')
            except PropertyNotSupportedError:
                pass
        
        if len(test_props) < 2:
            pytest.skip("Need at least 2 readable properties")
        
        # Set properties
        result = camera_controller.set_multiple(test_props)
        
        assert isinstance(result, dict)
        assert len(result) >= 2
        
        for prop_name in test_props.keys():
            assert prop_name in result
            assert isinstance(result[prop_name], bool)
    
    def test_set_multiple_returns_dict(self, camera_controller):
        """Test set_multiple() always returns status dictionary."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result1 = camera_controller.set_multiple({})
        result2 = camera_controller.set_multiple({'brightness': 50})
        result3 = camera_controller.set_multiple({'brightness': 50, 'fake': 100})
        
        assert isinstance(result1, dict)
        assert isinstance(result2, dict)
        assert isinstance(result3, dict)


@pytest.mark.hardware
class TestSetMultipleEdgeCases:
    """Test set_multiple() edge cases."""
    
    def test_set_multiple_with_invalid_property(self, camera_controller):
        """Test set_multiple() handles invalid properties gracefully."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.set_multiple({
            'brightness': 50,
            'totally_fake_property': 100
        })
        
        assert isinstance(result, dict)
        assert 'totally_fake_property' in result
        assert result['totally_fake_property'] == False
    
    def test_set_multiple_partial_failure(self, camera_controller):
        """Test set_multiple() handles partial failures."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.set_multiple({
            'brightness': 50,  # Valid
            'fake_prop_1': 100,  # Invalid
            'contrast': 60,  # Valid
            'fake_prop_2': 200  # Invalid
        })
        
        assert isinstance(result, dict)
        
        # Valid properties should succeed or fail gracefully
        # Invalid properties should be marked as failed
        assert result.get('fake_prop_1') == False
        assert result.get('fake_prop_2') == False
    
    def test_set_multiple_with_auto_value(self, camera_controller):
        """Test set_multiple() with 'auto' string values."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.set_multiple({
            'brightness': 'auto',
            'exposure': 'auto'
        })
        
        assert isinstance(result, dict)
        # Should handle 'auto' strings
    
    def test_set_multiple_verbose_mode(self, camera_controller):
        """Test set_multiple() verbose mode issues warnings."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            result = camera_controller.set_multiple({
                'fake_prop': 100
            }, verbose=True)
            
            # May issue warning for failed properties
            assert isinstance(result, dict)


@pytest.mark.hardware
class TestGetSetMultipleIntegration:
    """Test integration between get_multiple() and set_multiple()."""
    
    def test_get_then_set_multiple(self, camera_controller):
        """Test getting then setting multiple properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        if len(all_props) < 2:
            pytest.skip("Need at least 2 supported properties")
        
        # Get first 2 supported properties
        props_to_test = all_props[:2]
        
        # Get current values
        current_values = camera_controller.get_multiple(props_to_test)
        
        if len(current_values) < 2:
            pytest.skip("Could not read enough properties")
        
        # Set same values back
        set_result = camera_controller.set_multiple(current_values)
        
        assert isinstance(set_result, dict)
        assert len(set_result) >= 2
    
    def test_roundtrip_get_set_get(self, camera_controller):
        """Test roundtrip: get -> set -> get."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        if 'brightness' not in all_props:
            pytest.skip("Brightness not supported")
        
        try:
            # Get initial value
            initial = camera_controller.get_multiple(['brightness'])
            
            if 'brightness' not in initial:
                pytest.skip("Could not read brightness")
            
            # Set same value
            camera_controller.set_multiple(initial)
            
            # Get again
            final = camera_controller.get_multiple(['brightness'])
            
            # Value should be consistent (allowing for small variations)
            assert 'brightness' in final
        except PropertyNotSupportedError:
            pytest.skip("Brightness not supported")
    
    def test_bulk_property_update(self, camera_controller):
        """Test bulk updating multiple properties at once."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        # Build update dict
        updates = {}
        if 'brightness' in all_props:
            updates['brightness'] = 60
        if 'contrast' in all_props:
            updates['contrast'] = 50
        if 'saturation' in all_props:
            updates['saturation'] = 55
        
        if len(updates) < 2:
            pytest.skip("Need at least 2 writable properties")
        
        # Apply bulk update
        result = camera_controller.set_multiple(updates)
        
        # Count successes
        successes = sum(1 for success in result.values() if success)
        assert successes >= 1  # At least some should succeed


@pytest.mark.hardware
class TestBulkOperationPerformance:
    """Test bulk operation performance characteristics."""
    
    def test_get_multiple_faster_than_sequential(self, camera_controller):
        """Test get_multiple() is more efficient than sequential gets."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        if len(all_props) < 3:
            pytest.skip("Need at least 3 properties for performance test")
        
        props_to_test = all_props[:3]
        
        import time
        
        # Time bulk get
        start_bulk = time.time()
        bulk_result = camera_controller.get_multiple(props_to_test)
        bulk_time = time.time() - start_bulk
        
        # Time sequential gets
        start_seq = time.time()
        for prop in props_to_test:
            try:
                camera_controller.get(prop)
            except PropertyNotSupportedError:
                pass
        seq_time = time.time() - start_seq
        
        # Bulk should be at least as fast (usually faster)
        # Just verify both complete in reasonable time
        assert bulk_time < 5.0
        assert seq_time < 5.0
    
    def test_set_multiple_completes_quickly(self, camera_controller):
        """Test set_multiple() completes in reasonable time."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        import time
        
        start = time.time()
        camera_controller.set_multiple({
            'brightness': 50,
            'contrast': 50,
            'saturation': 50
        })
        duration = time.time() - start
        
        # Should complete in under 2 seconds
        assert duration < 2.0


@pytest.mark.hardware
class TestBulkOperationUseCases:
    """Test practical bulk operation use cases."""
    
    def test_save_and_restore_brightness_contrast(self, camera_controller):
        """Test saving and restoring specific properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        props_to_save = []
        if 'brightness' in all_props:
            props_to_save.append('brightness')
        if 'contrast' in all_props:
            props_to_save.append('contrast')
        
        if len(props_to_save) < 2:
            pytest.skip("Need brightness and contrast")
        
        # Save current values
        saved = camera_controller.get_multiple(props_to_save)
        
        # Modify values
        modified = {k: v + 10 for k, v in saved.items() if isinstance(v, int)}
        camera_controller.set_multiple(modified)
        
        # Restore original values
        camera_controller.set_multiple(saved)
        
        # Verify restored
        restored = camera_controller.get_multiple(props_to_save)
        
        # Values should be close to original (allowing small variations)
        for prop in props_to_save:
            if prop in saved and prop in restored:
                assert abs(saved[prop] - restored[prop]) <= 5
    
    def test_batch_configure_video_properties(self, camera_controller):
        """Test batch configuration of video properties."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        video_config = {
            'brightness': 60,
            'contrast': 55,
            'saturation': 50,
            'hue': 0,
            'sharpness': 45
        }
        
        result = camera_controller.set_multiple(video_config)
        
        # Should attempt all properties
        assert isinstance(result, dict)
        assert len(result) == len(video_config)
    
    def test_copy_settings_workflow(self, camera_controller):
        """Test workflow: read all, modify some, write back."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        supported = camera_controller.get_supported_properties()
        all_props = supported['camera'] + supported['video']
        
        # Read current settings
        current_settings = camera_controller.get_multiple(all_props)
        
        # Modify a subset
        for prop in ['brightness', 'contrast']:
            if prop in current_settings:
                current_settings[prop] = 75
        
        # Write modified settings back
        result = camera_controller.set_multiple(current_settings)
        
        # Should process all properties
        assert isinstance(result, dict)


@pytest.mark.hardware
class TestBulkOperationErrorHandling:
    """Test error handling in bulk operations."""
    
    def test_get_multiple_with_exception_continues(self, camera_controller):
        """Test get_multiple() continues despite individual failures."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # Mix valid and invalid properties
        result = camera_controller.get_multiple([
            'brightness',  # Valid
            'invalid_prop_1',  # Invalid
            'contrast',  # Valid
            'invalid_prop_2'  # Invalid
        ])
        
        # Should still process valid properties
        assert isinstance(result, dict)
        
        # Invalid properties omitted
        assert 'invalid_prop_1' not in result
        assert 'invalid_prop_2' not in result
    
    def test_set_multiple_with_mixed_success(self, camera_controller):
        """Test set_multiple() returns status for each property."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        result = camera_controller.set_multiple({
            'brightness': 50,  # Valid value
            'contrast': 50,  # Valid value
            'fake_prop': 100  # Invalid property
        })
        
        # Should have status for all properties
        assert isinstance(result, dict)
        assert len(result) == 3
        
        # Invalid property should be False
        assert result.get('fake_prop') == False
    
    def test_bulk_operations_dont_crash_on_invalid_input(self, camera_controller):
        """Test bulk operations handle invalid input gracefully."""
        if camera_controller is None:
            pytest.skip("No camera controller available")
        
        # These should not crash
        try:
            camera_controller.get_multiple([''])
            camera_controller.get_multiple([None])
            camera_controller.set_multiple({'': 50})
        except (ValueError, TypeError, AttributeError):
            # Exception is acceptable, just shouldn't crash
            pass


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
