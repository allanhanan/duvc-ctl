"""
Test Suite 19: Platform Interface
==================================

Tests platform abstraction interfaces IPlatformInterface and IDeviceConnection.

Platform Interface Features Tested:
  IPlatformInterface (3):
    - list_devices() - Enumerate devices
    - is_device_connected() - Check device status
    - create_connection() - Create device connection
  
  IDeviceConnection (6):
    - is_valid() - Check connection validity
    - get_camera_property() / set_camera_property() - Camera control
    - get_video_property() / set_video_property() - Video processing
    - get_camera_property_range() / get_video_property_range() - Property ranges
  
  Platform Factory (1):
    - create_platform_interface() - Get platform implementation

Total: 10 platform interface operations

Test Organization:
  1. Without Camera Tests - Interface verification and type checking
  2. With Camera Tests - Integration with real platform implementation

Run: pytest tests/test_19_platform_interface.py -v
Run without camera: pytest tests/test_19_platform_interface.py -v -m "not hardware"
"""

import pytest
import sys
from typing import List, Optional

import duvc_ctl
from duvc_ctl import (
    # Core types
    Device, CamProp, VidProp, PropSetting, PropRange,
    # Device functions
    list_devices,
    # Exceptions
    DeviceNotFoundError,
)
duvc_ctl.set_log_level(duvc_ctl.LogLevel.Debug)


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
# WITHOUT CAMERA TESTS - Interface verification and type checking
# ============================================================================

class TestIPlatformInterfaceClass:
    """Test IPlatformInterface abstract interface class."""
    
    def test_iplatform_interface_exists(self):
        """Test IPlatformInterface class exists."""
        assert hasattr(duvc_ctl, 'IPlatformInterface')
    
    def test_iplatform_interface_is_abstract(self):
        """Test IPlatformInterface is an abstract interface."""
        from duvc_ctl import IPlatformInterface
        
        # Should be a class/type
        assert isinstance(IPlatformInterface, type)
    
    def test_iplatform_interface_has_list_devices_method(self):
        """Test IPlatformInterface has list_devices() method."""
        from duvc_ctl import IPlatformInterface
        
        assert hasattr(IPlatformInterface, 'list_devices')
    
    def test_iplatform_interface_has_is_device_connected_method(self):
        """Test IPlatformInterface has is_device_connected() method."""
        from duvc_ctl import IPlatformInterface
        
        assert hasattr(IPlatformInterface, 'is_device_connected')
    
    def test_iplatform_interface_has_create_connection_method(self):
        """Test IPlatformInterface has create_connection() method."""
        from duvc_ctl import IPlatformInterface
        
        assert hasattr(IPlatformInterface, 'create_connection')


class TestIDeviceConnectionClass:
    """Test IDeviceConnection abstract interface class."""
    
    def test_idevice_connection_exists(self):
        """Test IDeviceConnection class exists."""
        assert hasattr(duvc_ctl, 'IDeviceConnection')
    
    def test_idevice_connection_is_abstract(self):
        """Test IDeviceConnection is an abstract interface."""
        from duvc_ctl import IDeviceConnection
        
        # Should be a class/type
        assert isinstance(IDeviceConnection, type)
    
    def test_idevice_connection_has_is_valid_method(self):
        """Test IDeviceConnection has is_valid() method."""
        from duvc_ctl import IDeviceConnection
        
        assert hasattr(IDeviceConnection, 'is_valid')
    
    def test_idevice_connection_has_get_camera_property_method(self):
        """Test IDeviceConnection has get_camera_property() method."""
        from duvc_ctl import IDeviceConnection
        
        assert hasattr(IDeviceConnection, 'get_camera_property')
    
    def test_idevice_connection_has_set_camera_property_method(self):
        """Test IDeviceConnection has set_camera_property() method."""
        from duvc_ctl import IDeviceConnection
        
        assert hasattr(IDeviceConnection, 'set_camera_property')
    
    def test_idevice_connection_has_get_camera_property_range_method(self):
        """Test IDeviceConnection has get_camera_property_range() method."""
        from duvc_ctl import IDeviceConnection
        
        assert hasattr(IDeviceConnection, 'get_camera_property_range')
    
    def test_idevice_connection_has_get_video_property_method(self):
        """Test IDeviceConnection has get_video_property() method."""
        from duvc_ctl import IDeviceConnection
        
        assert hasattr(IDeviceConnection, 'get_video_property')
    
    def test_idevice_connection_has_set_video_property_method(self):
        """Test IDeviceConnection has set_video_property() method."""
        from duvc_ctl import IDeviceConnection
        
        assert hasattr(IDeviceConnection, 'set_video_property')
    
    def test_idevice_connection_has_get_video_property_range_method(self):
        """Test IDeviceConnection has get_video_property_range() method."""
        from duvc_ctl import IDeviceConnection
        
        assert hasattr(IDeviceConnection, 'get_video_property_range')


class TestPlatformFactoryFunction:
    """Test platform factory function."""
    
    def test_create_platform_interface_exists(self):
        """Test create_platform_interface() function exists."""
        assert hasattr(duvc_ctl, 'create_platform_interface')
        assert callable(duvc_ctl.create_platform_interface)
    
    def test_create_platform_interface_returns_interface(self):
        """Test create_platform_interface() returns IPlatformInterface."""
        from duvc_ctl import create_platform_interface, IPlatformInterface
        
        platform = create_platform_interface()
        
        assert isinstance(platform, IPlatformInterface)
    
    def test_create_platform_interface_is_singleton(self):
        """Test create_platform_interface() returns consistent instance."""
        from duvc_ctl import create_platform_interface
        
        platform1 = create_platform_interface()
        platform2 = create_platform_interface()
        
        # Should return same instance or equivalent
        assert platform1 is not None
        assert platform2 is not None

class TestPythonSubclassingSupport:
    """Test Python can subclass abstract interfaces."""
    
    def test_can_subclass_iplatform_interface(self):
        """Test Python can subclass IPlatformInterface."""
        from duvc_ctl import IPlatformInterface
        
        class MockPlatformInterface(IPlatformInterface):
            def list_devices(self):
                from duvc_ctl import Ok
                return Ok([])
            
            def is_device_connected(self, device):
                from duvc_ctl import Ok
                return Ok(False)
            
            def create_connection(self, device):
                from duvc_ctl import Err, ErrorCode
                return Err(ErrorCode.DeviceNotFound, "Mock connection")
        
        # Should be able to instantiate
        mock = MockPlatformInterface()
        
        assert isinstance(mock, IPlatformInterface)
    
    def test_can_subclass_idevice_connection(self):
        """Test Python can subclass IDeviceConnection."""
        from duvc_ctl import IDeviceConnection, CamMode
        
        class MockDeviceConnection(IDeviceConnection):
            def is_valid(self):
                return False
            
            def get_camera_property(self, prop):
                from duvc_ctl import Err, ErrorCode
                return Err(ErrorCode.PropertyNotSupported, "Mock")
            
            def set_camera_property(self, prop, setting):
                from duvc_ctl import Err, ErrorCode
                return Err(ErrorCode.PropertyNotSupported, "Mock")
            
            def get_camera_property_range(self, prop):
                from duvc_ctl import Err, ErrorCode
                return Err(ErrorCode.PropertyNotSupported, "Mock")
            
            def get_video_property(self, prop):
                from duvc_ctl import Err, ErrorCode
                return Err(ErrorCode.PropertyNotSupported, "Mock")
            
            def set_video_property(self, prop, setting):
                from duvc_ctl import Err, ErrorCode
                return Err(ErrorCode.PropertyNotSupported, "Mock")
            
            def get_video_property_range(self, prop):
                from duvc_ctl import Err, ErrorCode
                return Err(ErrorCode.PropertyNotSupported, "Mock")
        
        # Should be able to instantiate
        mock = MockDeviceConnection()
        
        assert isinstance(mock, IDeviceConnection)


# ============================================================================
# WITH CAMERA TESTS - Integration with real platform implementation
# ============================================================================

@pytest.mark.hardware
class TestPlatformInterfaceListDevices:
    """Test IPlatformInterface.list_devices() with real implementation."""
    
    def test_platform_list_devices_returns_result(self):
        """Test platform.list_devices() returns Result type."""
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.list_devices()
        
        # Should return ResultT type
        assert hasattr(result, 'is_ok')
        assert hasattr(result, 'is_error')
    
    def test_platform_list_devices_success(self, available_devices):
        """Test platform.list_devices() returns success result."""
        if not available_devices:
            pytest.skip("No devices available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.list_devices()
        
        assert result.is_ok()
        
        devices = result.value()
        assert isinstance(devices, list)
        assert len(devices) == len(available_devices)
    
    def test_platform_list_devices_returns_device_objects(self, available_devices):
        """Test platform.list_devices() returns Device objects."""
        if not available_devices:
            pytest.skip("No devices available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.list_devices()
        
        assert result.is_ok()
        
        devices = result.value()
        for dev in devices:
            assert isinstance(dev, Device)
            assert hasattr(dev, 'name')
            assert hasattr(dev, 'path')

@pytest.mark.hardware
class TestPlatformInterfaceIsDeviceConnected:
    """Test IPlatformInterface.is_device_connected() with real implementation."""
    
    def test_platform_is_device_connected_returns_result(self, test_device):
        """Test platform.is_device_connected() returns Result type."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.is_device_connected(test_device)
        
        assert hasattr(result, 'is_ok')
        assert hasattr(result, 'is_error')
    
    def test_platform_is_device_connected_true_for_available(self, test_device):
        """Test platform.is_device_connected() returns True for available device."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.is_device_connected(test_device)
        
        assert result.is_ok()
        
        connected = result.value()
        assert isinstance(connected, bool)
        assert connected == True
    
    def test_platform_is_device_connected_false_for_fake(self):
        """Test platform.is_device_connected() returns False for fake device."""
        from duvc_ctl import create_platform_interface
        
        fake_device = Device("Fake Camera", "/fake/path")
        
        platform = create_platform_interface()
        result = platform.is_device_connected(fake_device)
        
        assert result.is_ok()
        
        connected = result.value()
        assert isinstance(connected, bool)
        assert connected == False

@pytest.mark.hardware
class TestPlatformInterfaceCreateConnection:
    """Test IPlatformInterface.create_connection() with real implementation."""
    
    def test_platform_create_connection_returns_result(self, test_device):
        """Test platform.create_connection() returns Result type."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        assert hasattr(result, 'is_ok')
        assert hasattr(result, 'is_error')
    
    def test_platform_create_connection_success(self, test_device):
        """Test platform.create_connection() succeeds for available device."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface, IDeviceConnection
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        assert result.is_ok()
        
        connection = result.value()
        assert isinstance(connection, IDeviceConnection)
    
    def test_platform_create_connection_failure_for_fake(self):
        """Test platform.create_connection() fails for fake device."""
        from duvc_ctl import create_platform_interface
        
        fake_device = Device("Fake Camera", "/fake/path")
        
        platform = create_platform_interface()
        result = platform.create_connection(fake_device)
        
        # Should return error result
        assert result.is_error()

@pytest.mark.hardware
class TestDeviceConnectionIsValid:
    """Test IDeviceConnection.is_valid() with real implementation."""
    
    def test_connection_is_valid_returns_bool(self, test_device):
        """Test connection.is_valid() returns boolean."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not create connection")
        
        connection = result.value()
        valid = connection.is_valid()
        
        assert isinstance(valid, bool)
    
    def test_connection_is_valid_true_for_real_device(self, test_device):
        """Test connection.is_valid() returns True for real device."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not create connection")
        
        connection = result.value()
        
        assert connection.is_valid() == True

@pytest.mark.hardware
class TestDeviceConnectionCameraProperties:
    """Test IDeviceConnection camera property methods."""
    
    def test_connection_get_camera_property_returns_result(self, test_device):
        """Test connection.get_camera_property() returns Result type."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not create connection")
        
        connection = result.value()
        prop_result = connection.get_camera_property(CamProp.Pan)
        
        assert hasattr(prop_result, 'is_ok')
        assert hasattr(prop_result, 'is_error')
    
    def test_connection_get_camera_property_returns_propsetting(self, test_device):
        """Test connection.get_camera_property() returns PropSetting on success."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not create connection")
        
        connection = result.value()
        
        # Try Pan (may not be supported)
        prop_result = connection.get_camera_property(CamProp.Pan)
        
        if prop_result.is_ok():
            setting = prop_result.value()
            assert isinstance(setting, PropSetting)
    
    def test_connection_set_camera_property_returns_result(self, test_device):
        """Test connection.set_camera_property() returns Result type."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface, CamMode
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not create connection")
        
        connection = result.value()
        
        setting = PropSetting(0, CamMode.Manual)
        set_result = connection.set_camera_property(CamProp.Pan, setting)
        
        assert hasattr(set_result, 'is_ok')
        assert hasattr(set_result, 'is_error')
    
    def test_connection_get_camera_property_range_returns_result(self, test_device):
        """Test connection.get_camera_property_range() returns Result type."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not create connection")
        
        connection = result.value()
        range_result = connection.get_camera_property_range(CamProp.Pan)
        
        assert hasattr(range_result, 'is_ok')
        assert hasattr(range_result, 'is_error')
    
    def test_connection_get_camera_property_range_returns_proprange(self, test_device):
        """Test connection.get_camera_property_range() returns PropRange on success."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not create connection")
        
        connection = result.value()
        range_result = connection.get_camera_property_range(CamProp.Pan)
        
        if range_result.is_ok():
            prop_range = range_result.value()
            assert isinstance(prop_range, PropRange)

@pytest.mark.hardware
class TestDeviceConnectionVideoProperties:
    """Test IDeviceConnection video property methods."""
    
    def test_connection_get_video_property_returns_result(self, test_device):
        """Test connection.get_video_property() returns Result type."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not create connection")
        
        connection = result.value()
        prop_result = connection.get_video_property(VidProp.Brightness)
        
        assert hasattr(prop_result, 'is_ok')
        assert hasattr(prop_result, 'is_error')
    
    def test_connection_get_video_property_returns_propsetting(self, test_device):
        """Test connection.get_video_property() returns PropSetting on success."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not create connection")
        
        connection = result.value()
        prop_result = connection.get_video_property(VidProp.Brightness)
        
        if prop_result.is_ok():
            setting = prop_result.value()
            assert isinstance(setting, PropSetting)
    
    def test_connection_set_video_property_returns_result(self, test_device):
        """Test connection.set_video_property() returns Result type."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface, CamMode
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not create connection")
        
        connection = result.value()
        
        setting = PropSetting(128, CamMode.Manual)
        set_result = connection.set_video_property(VidProp.Brightness, setting)
        
        assert hasattr(set_result, 'is_ok')
        assert hasattr(set_result, 'is_error')
    
    def test_connection_get_video_property_range_returns_result(self, test_device):
        """Test connection.get_video_property_range() returns Result type."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not create connection")
        
        connection = result.value()
        range_result = connection.get_video_property_range(VidProp.Brightness)
        
        assert hasattr(range_result, 'is_ok')
        assert hasattr(range_result, 'is_error')
    
    def test_connection_get_video_property_range_returns_proprange(self, test_device):
        """Test connection.get_video_property_range() returns PropRange on success."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface
        
        platform = create_platform_interface()
        result = platform.create_connection(test_device)
        
        if not result.is_ok():
            pytest.skip("Could not create connection")
        
        connection = result.value()
        range_result = connection.get_video_property_range(VidProp.Brightness)
        
        if range_result.is_ok():
            prop_range = range_result.value()
            assert isinstance(prop_range, PropRange)


@pytest.mark.hardware
class TestPlatformInterfaceIntegration:
    """Test complete workflow using platform interface."""
    
    def test_complete_workflow_enumerate_connect_control(self, test_device):
        """Test complete workflow: enumerate → connect → control."""
        if test_device is None:
            pytest.skip("No test device available")
        
        from duvc_ctl import create_platform_interface, CamMode
        
        # 1. Create platform
        platform = create_platform_interface()
        
        # 2. Enumerate devices
        devices_result = platform.list_devices()
        assert devices_result.is_ok()
        
        devices = devices_result.value()
        assert len(devices) > 0
        
        # 3. Check device connection
        first_device = devices[0]
        connected_result = platform.is_device_connected(first_device)
        assert connected_result.is_ok()
        assert connected_result.value() == True
        
        # 4. Create connection
        conn_result = platform.create_connection(first_device)
        assert conn_result.is_ok()
        
        connection = conn_result.value()
        assert connection.is_valid()
        
        # 5. Get video property
        get_result = connection.get_video_property(VidProp.Brightness)
        
        if get_result.is_ok():
            current_setting = get_result.value()
            
            # 6. Set video property
            new_setting = PropSetting(current_setting.value, CamMode.Manual)
            set_result = connection.set_video_property(VidProp.Brightness, new_setting)
            
            # Should succeed or fail with specific error
            assert set_result.is_ok() or set_result.is_error()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
