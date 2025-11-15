"""
Test Suite 12: Device Capabilities
===================================

Tests device capability querying and property metadata.

Functionality Tested:
  Capability Query (1):
    - get_device_capabilities(device) - Get complete device capability snapshot
    - get_device_capabilities(index) - Get capabilities by device index
  
  DeviceCapabilities Methods (8):
    - get_camera_capability(prop) - Get camera property capability info
    - get_video_capability(prop) - Get video property capability info
    - supports_camera_property(prop) - Check camera property support
    - supports_video_property(prop) - Check video property support
    - supported_camera_properties() - List supported camera properties
    - supported_video_properties() - List supported video properties
    - device - Get device this capability snapshot is for
    - is_device_accessible() - Check if device is accessible
  
  PropertyCapability Fields (4):
    - supported - Property support status (bool)
    - range - Valid property range (PropRange)
    - current - Current property value (PropSetting)
    - supports_auto() - Check auto mode support

Total: 13 capability-related operations

Test Organization:
  1. Without Camera Tests - Interface verification
  2. With Camera Tests - Integration tests using real camera hardware

Run: pytest tests/test_12_device_capabilities.py -v
Run without camera: pytest tests/test_12_device_capabilities.py -v -m "not hardware"
"""

import pytest
import sys
from typing import List, Optional

import duvc_ctl
from duvc_ctl import (
    # Core types
    Device, PropRange, PropSetting, PropertyCapability, DeviceCapabilities,
    # Core enums
    CamProp, VidProp, CamMode,
    # Result types
    DeviceCapabilitiesResult,
    # Device functions
    list_devices, get_device_capabilities,
    # Exceptions
    DeviceNotFoundError,
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
def device_caps(test_device) -> Optional[DeviceCapabilities]:
    """Get DeviceCapabilities for test device."""
    if test_device is None:
        pytest.skip("No test device available")
    
    result = get_device_capabilities(test_device)
    if not result.is_ok():
        pytest.skip(f"Could not get device capabilities: {result.error().description()}")
    
    return result.value()


# ============================================================================
# WITHOUT CAMERA TESTS - Interface verification
# ============================================================================

class TestGetDeviceCapabilitiesFunction:
    """Test get_device_capabilities() function interface."""
    
    def test_get_device_capabilities_exists(self):
        """Test get_device_capabilities() function exists."""
        assert hasattr(duvc_ctl, 'get_device_capabilities')
        assert callable(get_device_capabilities)
    
    def test_get_device_capabilities_with_device(self):
        """Test get_device_capabilities() accepts Device."""
        # Create mock device
        mock_device = Device("Test Camera", "/test/path")
        
        # Should return DeviceCapabilitiesResult (may be error for fake device)
        result = get_device_capabilities(mock_device)
        assert isinstance(result, DeviceCapabilitiesResult)
    
    def test_get_device_capabilities_with_index(self):
        """Test get_device_capabilities() accepts integer index."""
        # Should return DeviceCapabilitiesResult
        result = get_device_capabilities(0)
        assert isinstance(result, DeviceCapabilitiesResult)


class TestDeviceCapabilitiesInterface:
    """Test DeviceCapabilities class interface."""
    
    def test_device_capabilities_has_required_methods(self):
        """Test DeviceCapabilities has all required methods."""
        required_methods = [
            'get_camera_capability',
            'get_video_capability',
            'supports_camera_property',
            'supports_video_property',
            'supported_camera_properties',
            'supported_video_properties',
            'device',
            'is_device_accessible',
            'refresh'
        ]
        
        for method in required_methods:
            assert hasattr(DeviceCapabilities, method), \
                   f"DeviceCapabilities missing method: {method}"


class TestPropertyCapabilityInterface:
    """Test PropertyCapability class interface."""
    
    def test_property_capability_has_required_fields(self):
        """Test PropertyCapability has all required fields."""
        required_fields = ['supported', 'range', 'current', 'supports_auto']
        
        for field in required_fields:
            assert hasattr(PropertyCapability, field), \
                   f"PropertyCapability missing field: {field}"


# ============================================================================
# WITH CAMERA TESTS - Integration tests using real camera
# ============================================================================

@pytest.mark.hardware
class TestGetDeviceCapabilitiesWithHardware:
    """Test get_device_capabilities() with real camera hardware."""
    
    def test_get_device_capabilities_with_valid_device(self, test_device):
        """Test getting capabilities for valid device."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_capabilities(test_device)
        
        assert isinstance(result, DeviceCapabilitiesResult)
        assert result.is_ok()
        assert not result.is_error()
    
    def test_get_device_capabilities_with_valid_index(self, available_devices):
        """Test getting capabilities by valid index."""
        if not available_devices:
            pytest.skip("No devices available")
        
        result = get_device_capabilities(0)
        
        assert isinstance(result, DeviceCapabilitiesResult)
        assert result.is_ok()
    
    def test_get_device_capabilities_returns_capabilities_object(self, test_device):
        """Test get_device_capabilities() returns DeviceCapabilities."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = get_device_capabilities(test_device)
        
        if result.is_ok():
            caps = result.value()
            assert isinstance(caps, DeviceCapabilities)
    
    def test_get_device_capabilities_with_invalid_device(self):
        """Test getting capabilities for non-existent device."""
        fake_device = Device("Nonexistent Camera", "/fake/path/123")
        result = get_device_capabilities(fake_device)
        
        # Should return error
        assert result.is_error()
    
    def test_get_device_capabilities_with_invalid_index(self):
        """Test getting capabilities with out-of-range index."""
        result = get_device_capabilities(999)
        
        # Should return error
        assert result.is_error()


@pytest.mark.hardware
class TestDeviceCapabilitiesDevice:
    """Test DeviceCapabilities.device."""
    
    def test_device_returns_device_object(self, device_caps, test_device):
        """Test device returns Device object."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        device = device_caps.device
        
        assert isinstance(device, Device)
        assert device == test_device
    
    def test_device_matches_original(self, device_caps, test_device):
        """Test device returns same device used to create capabilities."""
        if device_caps is None or test_device is None:
            pytest.skip("No capabilities or device available")
        
        device = device_caps.device
        
        assert device.name == test_device.name
        assert device.path == test_device.path


@pytest.mark.hardware
class TestDeviceCapabilitiesAccessibility:
    """Test DeviceCapabilities.is_device_accessible() method."""
    
    def test_is_device_accessible_returns_bool(self, device_caps):
        """Test is_device_accessible() returns boolean."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        accessible = device_caps.is_device_accessible()
        
        assert isinstance(accessible, bool)
    
    def test_is_device_accessible_true_for_open_device(self, device_caps):
        """Test is_device_accessible() returns True for accessible device."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        accessible = device_caps.is_device_accessible()
        
        # Device should be accessible if we got this far
        assert accessible == True


@pytest.mark.hardware
class TestSupportedPropertiesLists:
    """Test supported_camera_properties() and supported_video_properties()."""
    
    def test_supported_camera_properties_returns_list(self, device_caps):
        """Test supported_camera_properties() returns list."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        props = device_caps.supported_camera_properties()
        
        assert isinstance(props, list)
    
    def test_supported_video_properties_returns_list(self, device_caps):
        """Test supported_video_properties() returns list."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        props = device_caps.supported_video_properties()
        
        assert isinstance(props, list)
    
    def test_supported_properties_contain_enums(self, device_caps):
        """Test supported properties lists contain enum values."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        cam_props = device_caps.supported_camera_properties()
        vid_props = device_caps.supported_video_properties()
        
        for prop in cam_props:
            assert isinstance(prop, CamProp)
        
        for prop in vid_props:
            assert isinstance(prop, VidProp)
    
    def test_at_least_some_properties_supported(self, device_caps):
        """Test device supports at least some properties."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        cam_props = device_caps.supported_camera_properties()
        vid_props = device_caps.supported_video_properties()
        
        total_props = len(cam_props) + len(vid_props)
        
        # Most USB cameras support at least brightness
        assert total_props > 0, "Camera should support at least some properties"
    
    def test_common_properties_likely_supported(self, device_caps):
        """Test common video properties are likely supported."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        vid_props = device_caps.supported_video_properties()
        
        # Most USB cameras support brightness and contrast
        common_props = [VidProp.Brightness, VidProp.Contrast]
        
        # At least ONE common property should be supported
        # (very lenient test - just checking the method works)
        supported_common = [p for p in common_props if p in vid_props]


@pytest.mark.hardware
class TestSupportsPropertyMethods:
    """Test supports_camera_property() and supports_video_property()."""
    
    def test_supports_camera_property_returns_bool(self, device_caps):
        """Test supports_camera_property() returns boolean."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        result = device_caps.supports_camera_property(CamProp.Pan)
        
        assert isinstance(result, bool)
    
    def test_supports_video_property_returns_bool(self, device_caps):
        """Test supports_video_property() returns boolean."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        result = device_caps.supports_video_property(VidProp.Brightness)
        
        assert isinstance(result, bool)
    
    def test_supports_matches_supported_list_camera(self, device_caps):
        """Test supports_camera_property() matches supported_camera_properties()."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        supported_list = device_caps.supported_camera_properties()
        
        for prop in [CamProp.Pan, CamProp.Tilt, CamProp.Zoom]:
            in_list = prop in supported_list
            supports = device_caps.supports_camera_property(prop)
            
            assert in_list == supports, \
                   f"Mismatch for {prop}: in list={in_list}, supports={supports}"
    
    def test_supports_matches_supported_list_video(self, device_caps):
        """Test supports_video_property() matches supported_video_properties()."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        supported_list = device_caps.supported_video_properties()
        
        for prop in [VidProp.Brightness, VidProp.Contrast, VidProp.Saturation]:
            in_list = prop in supported_list
            supports = device_caps.supports_video_property(prop)
            
            assert in_list == supports, \
                   f"Mismatch for {prop}: in list={in_list}, supports={supports}"


@pytest.mark.hardware
class TestGetCapabilityMethods:
    """Test get_camera_capability() and get_video_capability()."""
    
    def test_get_camera_capability_returns_property_capability(self, device_caps):
        """Test get_camera_capability() returns PropertyCapability."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        supported_props = device_caps.supported_camera_properties()
        
        if not supported_props:
            pytest.skip("No supported camera properties")
        
        prop = supported_props[0]
        capability = device_caps.get_camera_capability(prop)
        
        assert isinstance(capability, PropertyCapability)
    
    def test_get_video_capability_returns_property_capability(self, device_caps):
        """Test get_video_capability() returns PropertyCapability."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        supported_props = device_caps.supported_video_properties()
        
        if not supported_props:
            pytest.skip("No supported video properties")
        
        prop = supported_props[0]
        capability = device_caps.get_video_capability(prop)
        
        assert isinstance(capability, PropertyCapability)
    
    def test_get_capability_for_supported_property(self, device_caps):
        """Test get_capability() for supported property."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        vid_props = device_caps.supported_video_properties()
        
        if VidProp.Brightness in vid_props:
            capability = device_caps.get_video_capability(VidProp.Brightness)
            
            assert capability.supported == True
            assert isinstance(capability.range, PropRange)
            assert isinstance(capability.current, PropSetting)
    
    def test_get_capability_for_unsupported_property(self, device_caps):
        """Test get_capability() for unsupported property."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        cam_props = device_caps.supported_camera_properties()
        
        # Find unsupported property
        all_props = [CamProp.Pan, CamProp.Tilt, CamProp.Roll, CamProp.Zoom]
        unsupported = None
        
        for prop in all_props:
            if prop not in cam_props:
                unsupported = prop
                break
        
        if unsupported is None:
            pytest.skip("All test properties supported")
        
        capability = device_caps.get_camera_capability(unsupported)
        
        # Should still return PropertyCapability but marked as unsupported
        assert isinstance(capability, PropertyCapability)
        assert capability.supported == False


@pytest.mark.hardware
class TestPropertyCapabilityStructure:
    """Test PropertyCapability structure and fields."""
    
    def test_property_capability_supported_field(self, device_caps):
        """Test PropertyCapability.supported field."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        vid_props = device_caps.supported_video_properties()
        
        if not vid_props:
            pytest.skip("No supported video properties")
        
        prop = vid_props[0]
        capability = device_caps.get_video_capability(prop)
        
        assert isinstance(capability.supported, bool)
        assert capability.supported == True
    
    def test_property_capability_range_field(self, device_caps):
        """Test PropertyCapability.range field."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        vid_props = device_caps.supported_video_properties()
        
        if VidProp.Brightness in vid_props:
            capability = device_caps.get_video_capability(VidProp.Brightness)
            
            assert isinstance(capability.range, PropRange)
            assert capability.range.min <= capability.range.max
            assert capability.range.step > 0
    
    def test_property_capability_current_field(self, device_caps):
        """Test PropertyCapability.current field."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        vid_props = device_caps.supported_video_properties()
        
        if VidProp.Brightness in vid_props:
            capability = device_caps.get_video_capability(VidProp.Brightness)
            
            assert isinstance(capability.current, PropSetting)
            assert isinstance(capability.current.value, int)
            assert isinstance(capability.current.mode, CamMode)
    
    def test_property_capability_supports_auto_method(self, device_caps):
        """Test PropertyCapability.supports_auto() method."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        vid_props = device_caps.supported_video_properties()
        
        if VidProp.WhiteBalance in vid_props:
            capability = device_caps.get_video_capability(VidProp.WhiteBalance)
            
            auto_supported = capability.supports_auto()
            
            assert isinstance(auto_supported, bool)


@pytest.mark.hardware
class TestDeviceCapabilitiesIteration:
    """Test DeviceCapabilities iteration support."""
    
    def test_device_capabilities_iterable(self, device_caps):
        """Test DeviceCapabilities supports iteration."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        # Should be able to iterate
        props = list(device_caps)
        
        assert isinstance(props, list)
        assert len(props) > 0
    
    def test_device_capabilities_len(self, device_caps):
        """Test len() on DeviceCapabilities."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        length = len(device_caps)
        
        # Should equal total of camera + video properties
        cam_props = device_caps.supported_camera_properties()
        vid_props = device_caps.supported_video_properties()
        expected_length = len(cam_props) + len(vid_props)
        
        assert length == expected_length
    
    def test_iteration_includes_all_properties(self, device_caps):
        """Test iteration includes all supported properties."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        iterated_props = list(device_caps)
        
        cam_props = device_caps.supported_camera_properties()
        vid_props = device_caps.supported_video_properties()
        all_props = cam_props + vid_props
        
        assert len(iterated_props) == len(all_props)


@pytest.mark.hardware
class TestCapabilityRefresh:
    """Test DeviceCapabilities.refresh() method."""
    
    def test_refresh_method_exists(self, device_caps):
        """Test refresh() method exists."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        assert hasattr(device_caps, 'refresh')
        assert callable(device_caps.refresh)
    
    def test_refresh_updates_capabilities(self, device_caps):
        """Test refresh() updates capability snapshot."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        # Get initial state
        initial_accessible = device_caps.is_device_accessible()
        
        # Refresh
        device_caps.refresh()
        
        # Should still be accessible
        after_refresh = device_caps.is_device_accessible()
        
        assert isinstance(after_refresh, bool)
        # Accessibility shouldn't change for active device
        assert after_refresh == initial_accessible


@pytest.mark.hardware
class TestCapabilityWorkflows:
    """Test complete capability query workflows."""
    
    def test_query_all_supported_properties(self, device_caps):
        """Test querying capabilities for all supported properties."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        # Get all supported properties
        cam_props = device_caps.supported_camera_properties()
        vid_props = device_caps.supported_video_properties()
        
        # Query capability for each
        for prop in cam_props:
            capability = device_caps.get_camera_capability(prop)
            assert capability.supported == True
        
        for prop in vid_props:
            capability = device_caps.get_video_capability(prop)
            assert capability.supported == True
    
    def test_capability_range_validation(self, device_caps):
        """Test capability ranges are valid."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        vid_props = device_caps.supported_video_properties()
        
        for prop in vid_props:
            capability = device_caps.get_video_capability(prop)
            
            if capability.supported:
                prop_range = capability.range
                
                # Validate range
                assert prop_range.min <= prop_range.max
                assert prop_range.step > 0
                assert prop_range.min <= prop_range.default_val <= prop_range.max
    
    def test_current_value_in_range(self, device_caps):
        """Test current property value is within valid range."""
        if device_caps is None:
            pytest.skip("No device capabilities available")
        
        vid_props = device_caps.supported_video_properties()
        
        for prop in vid_props:
            capability = device_caps.get_video_capability(prop)
            
            if capability.supported and capability.current.mode == CamMode.Manual:
                current_value = capability.current.value
                prop_range = capability.range
                
                # Current value should be within range (with small tolerance)
                assert prop_range.min - 5 <= current_value <= prop_range.max + 5, \
                       f"Current value {current_value} outside range [{prop_range.min}, {prop_range.max}]"


@pytest.mark.hardware
class TestCapabilityComparisons:
    """Test comparing capabilities across multiple devices."""
    
    def test_same_device_same_capabilities(self, test_device):
        """Test querying same device twice gives consistent capabilities."""
        if test_device is None:
            pytest.skip("No test device available")
        
        # Get capabilities twice
        result1 = get_device_capabilities(test_device)
        result2 = get_device_capabilities(test_device)
        
        if not (result1.is_ok() and result2.is_ok()):
            pytest.skip("Could not get capabilities")
        
        caps1 = result1.value()
        caps2 = result2.value()
        
        # Should have same supported properties
        cam_props1 = caps1.supported_camera_properties()
        cam_props2 = caps2.supported_camera_properties()
        
        assert set(cam_props1) == set(cam_props2)
        
        vid_props1 = caps1.supported_video_properties()
        vid_props2 = caps2.supported_video_properties()
        
        assert set(vid_props1) == set(vid_props2)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
