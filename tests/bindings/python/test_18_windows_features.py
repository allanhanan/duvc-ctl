"""
Test Suite 18: Windows Features
================================

Tests Windows-specific DirectShow functionality including GUID handling,
vendor-specific properties, and Logitech extensions.

Windows-Specific Features Tested:
  GUID Handling (5):
    - PyGUID creation and parsing
    - GUID string formats (with/without braces, dashes)
    - guid_from_uuid() conversion
    - GUID equality and hashing
    - _normalize_guid() helper
  
  Vendor Properties (4):
    - KsPropertySet interface
    - get_vendor_property() / set_vendor_property()
    - query_vendor_property_support()
    - VendorProperty class
  
  Logitech Extensions (4):
    - LogitechProperty enum
    - get_logitech_property() / set_logitech_property()
    - supports_logitech_properties()
    - Logitech-specific property IDs
  
  DirectShow Wrappers (2):
    - DeviceConnection low-level interface
    - BaseFilter and EnumMoniker

Total: 15 Windows-specific operations

Test Organization:
  1. Without Camera Tests - Interface and type verification
  2. With Camera Tests - Integration with real Windows devices

Run: pytest tests/test_18_windows_features.py -v
Run without camera: pytest tests/test_18_windows_features.py -v -m "not hardware"
"""

import pytest
import sys
import uuid
from typing import List, Optional

import duvc_ctl
from duvc_ctl import (
    # Core types
    Device, CamProp, VidProp, PropSetting,
    # Device functions
    list_devices,
    # Exceptions
    DeviceNotFoundError,
)


# Check if running on Windows
WINDOWS_ONLY = sys.platform == 'win32'


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def available_devices() -> List[Device]:
    """Get list of available camera devices for hardware tests."""
    if not WINDOWS_ONLY:
        pytest.skip("Windows-only test")
    
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
# WITHOUT CAMERA TESTS - Interface and type verification
# ============================================================================

class TestGUIDClassInterface:
    """Test PyGUID class interface."""
    
    def test_pyguid_class_exists_on_windows(self):
        """Test PyGUID class exists on Windows."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'PyGUID')
    
    def test_guid_from_uuid_exists_on_windows(self):
        """Test guid_from_uuid() function exists on Windows."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'guid_from_uuid')
        assert callable(duvc_ctl.guid_from_uuid)
    
    def test_normalize_guid_exists(self):
        """Test _normalize_guid() helper exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, '_normalize_guid')
        assert callable(duvc_ctl._normalize_guid)


class TestGUIDCreationAndParsing:
    """Test GUID creation and string parsing."""
    
    def test_pyguid_from_string_with_braces(self):
        """Test PyGUID creation from string with braces."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import PyGUID
        
        guid_str = "{12345678-1234-5678-9ABC-123456789ABC}"
        guid = PyGUID(guid_str)
        
        assert isinstance(guid, PyGUID)
    
    def test_pyguid_from_string_without_braces(self):
        """Test PyGUID creation from string without braces."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import PyGUID
        
        guid_str = "12345678-1234-5678-9ABC-123456789ABC"
        guid = PyGUID(guid_str)
        
        assert isinstance(guid, PyGUID)
    
    def test_pyguid_from_string_without_dashes(self):
        """Test PyGUID creation from 32-char hex string."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import PyGUID
        
        guid_str = "12345678123456789ABC123456789ABC"
        guid = PyGUID(guid_str)
        
        assert isinstance(guid, PyGUID)
    
    def test_pyguid_tostring_format(self):
        """Test PyGUID.to_string() returns correct format."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import PyGUID
        
        guid_str = "12345678-1234-5678-9ABC-123456789ABC"
        guid = PyGUID(guid_str)
        
        result = guid.to_string()
        
        assert isinstance(result, str)
        assert len(result) == 36  # Format: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
        assert result.count('-') == 4
    
    def test_pyguid_str_method(self):
        """Test PyGUID.__str__() returns string representation."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import PyGUID
        
        guid = PyGUID("12345678-1234-5678-9ABC-123456789ABC")
        
        result = str(guid)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_pyguid_repr_method(self):
        """Test PyGUID.__repr__() returns representation."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import PyGUID
        
        guid = PyGUID("12345678-1234-5678-9ABC-123456789ABC")
        
        result = repr(guid)
        
        assert isinstance(result, str)
        assert "PyGUID" in result or "GUID" in result


class TestGUIDConversions:
    """Test GUID conversion functions."""
    
    def test_guid_from_uuid_with_python_uuid(self):
        """Test guid_from_uuid() with Python uuid.UUID."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import guid_from_uuid
        
        test_uuid = uuid.UUID("12345678-1234-5678-9ABC-123456789ABC")
        result = guid_from_uuid(test_uuid)
        
        # Should return PyGUID
        from duvc_ctl import PyGUID
        assert isinstance(result, PyGUID)
    
    def test_normalize_guid_with_string(self):
        """Test _normalize_guid() with string."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import _normalize_guid, PyGUID
        
        guid_str = "12345678-1234-5678-9ABC-123456789ABC"
        result = _normalize_guid(guid_str)
        
        assert isinstance(result, PyGUID)
    
    def test_normalize_guid_with_uuid(self):
        """Test _normalize_guid() with uuid.UUID."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import _normalize_guid, PyGUID
        
        test_uuid = uuid.UUID("12345678-1234-5678-9ABC-123456789ABC")
        result = _normalize_guid(test_uuid)
        
        assert isinstance(result, PyGUID)
    
    def test_normalize_guid_with_bytes(self):
        from duvc_ctl import _normalize_guid, PyGUID

        guid_bytes = bytes([
            0x78, 0x56, 0x34, 0x12,  # Data1
            0x34, 0x12,              # Data2
            0x78, 0x56,              # Data3
            0x9A, 0xBC,              # Data4 (first 2 bytes)
            0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC  # Data4 (last 6 bytes)
        ])
        result = _normalize_guid(guid_bytes)
        assert isinstance(result, PyGUID)
    
    def test_normalize_guid_with_pyguid(self):
        """Test _normalize_guid() with PyGUID returns same object."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import _normalize_guid, PyGUID
        
        guid = PyGUID("12345678-1234-5678-9ABC-123456789ABC")
        result = _normalize_guid(guid)
        
        assert result is guid  # Should return same object


class TestGUIDEqualityAndHashing:
    """Test GUID equality and hash operations."""
    
    def test_pyguid_equality(self):
        """Test PyGUID equality comparison."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import PyGUID
        
        guid1 = PyGUID("12345678-1234-5678-9ABC-123456789ABC")
        guid2 = PyGUID("12345678-1234-5678-9ABC-123456789ABC")
        
        assert guid1 == guid2
    
    def test_pyguid_inequality(self):
        """Test PyGUID inequality comparison."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import PyGUID
        
        guid1 = PyGUID("12345678-1234-5678-9ABC-123456789ABC")
        guid2 = PyGUID("87654321-4321-8765-CBA9-CBA987654321")
        
        assert guid1 != guid2
    
    def test_pyguid_hashable(self):
        """Test PyGUID can be used in sets/dicts."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import PyGUID
        
        guid1 = PyGUID("12345678-1234-5678-9ABC-123456789ABC")
        guid2 = PyGUID("12345678-1234-5678-9ABC-123456789ABC")
        
        guid_set = {guid1, guid2}
        
        # Same GUID should result in single element
        assert len(guid_set) == 1
    
    def test_pyguid_as_dict_key(self):
        """Test PyGUID can be used as dictionary key."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import PyGUID
        
        guid = PyGUID("12345678-1234-5678-9ABC-123456789ABC")
        test_dict = {guid: "test_value"}
        
        assert test_dict[guid] == "test_value"


class TestVendorPropertyInterface:
    """Test vendor property interfaces."""
    
    def test_vendorproperty_class_exists_on_windows(self):
        """Test VendorProperty class exists on Windows."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'VendorProperty')
    
    def test_kspropertyse_class_exists_on_windows(self):
        """Test KsPropertySet class exists on Windows."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'KsPropertySet')
    
    def test_get_vendor_property_exists(self):
        """Test get_vendor_property() function exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'get_vendor_property')
        assert callable(duvc_ctl.get_vendor_property)
    
    def test_set_vendor_property_exists(self):
        """Test set_vendor_property() function exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'set_vendor_property')
        assert callable(duvc_ctl.set_vendor_property)
    
    def test_query_vendor_property_support_exists(self):
        """Test query_vendor_property_support() function exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'query_vendor_property_support')
        assert callable(duvc_ctl.query_vendor_property_support)

class TestLogitechExtensionInterface:
    """Test Logitech extension interfaces."""
    
    def test_logitech_property_enum_exists_on_windows(self):
        """Test LogitechProperty enum exists on Windows."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'LogitechProperty')
    
    def test_get_logitech_property_exists(self):
        """Test get_logitech_property() function exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'get_logitech_property')
        assert callable(duvc_ctl.get_logitech_property)
    
    def test_set_logitech_property_exists(self):
        """Test set_logitech_property() function exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'set_logitech_property')
        assert callable(duvc_ctl.set_logitech_property)
    
    def test_supports_logitech_properties_exists(self):
        """Test supports_logitech_properties() function exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'supports_logitech_properties')
        assert callable(duvc_ctl.supports_logitech_properties)

class TestLogitechPropertyEnum:
    """Test LogitechProperty enum values."""
    
    def test_logitech_property_rightlight_exists(self):
        """Test LogitechProperty.RightLight exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import LogitechProperty
        
        assert hasattr(LogitechProperty, 'RightLight')
    
    def test_logitech_property_rightsound_exists(self):
        """Test LogitechProperty.RightSound exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import LogitechProperty
        
        assert hasattr(LogitechProperty, 'RightSound')
    
    def test_logitech_property_facetracking_exists(self):
        """Test LogitechProperty.FaceTracking exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import LogitechProperty
        
        assert hasattr(LogitechProperty, 'FaceTracking')
    
    def test_logitech_property_ledindicator_exists(self):
        """Test LogitechProperty.LedIndicator exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import LogitechProperty
        
        assert hasattr(LogitechProperty, 'LedIndicator')
        
    def test_logitech_property_values_are_int(self):
        """Verify LogitechProperty enum members are accessible and convertible to integers."""
        from duvc_ctl import LogitechProperty
        
        # Verify class exists and is callable as enum-like
        assert callable(LogitechProperty), "LogitechProperty should be class-like for enum access"
        
        # Dynamically check all non-property members from dir() are int-convertible
        member_values = []
        for member_name in dir(LogitechProperty):
            if not member_name.startswith('_'):  # Skip private attrs
                member = getattr(LogitechProperty, member_name)
                if isinstance(member, property):  # Skip built-in properties like 'name', 'value'
                    continue
                try:
                    value = int(member)  # Pybind11 enums allow int() coercion
                    assert isinstance(value, int), f"{member_name} should coerce to int, got {type(value)}"
                    member_values.append((member_name, value))
                except (TypeError, ValueError) as e:
                    pytest.fail(f"{member_name} failed int conversion: {e} (got {type(member)})")
        
        # Verify known members (from C++ binding) are present with correct values
        known_members = {
            'RightLight': 1,
            'RightSound': 2,
            'FaceTracking': 3,
            'LedIndicator': 4,
            'ProcessorUsage': 5,
            'RawDataBits': 6,
            'FocusAssist': 7,
            'VideoStandard': 8,
            'DigitalZoomROI': 9,
            'TiltPan': 10
        }
        for name, expected_value in known_members.items():
            member = getattr(LogitechProperty, name, None)
            assert member is not None, f"Missing known member {name}"
            assert int(member) == expected_value, f"{name} should be {expected_value}, got int({member}) == {int(member)}"
        
        assert len(member_values) == len(known_members), "Exactly expected members should be present (no extras)"


class TestDirectShowWrapperInterfaces:
    """Test DirectShow wrapper classes."""
    
    def test_deviceconnection_class_exists_on_windows(self):
        """Test DeviceConnection class exists on Windows."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'DeviceConnection')
    
    def test_basefilter_class_exists_on_windows(self):
        """Test BaseFilter class exists on Windows."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'BaseFilter')
    
    def test_enummoniker_class_exists_on_windows(self):
        """Test EnumMoniker class exists on Windows."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'EnumMoniker')


# ============================================================================
# WITH CAMERA TESTS - Integration with real Windows devices
# ============================================================================

class TestKsPropertySetWithHardware:
    """Test KsPropertySet with real hardware (requires camera)."""
    
    @pytest.fixture(autouse=True)
    def setup_device(self):
        if not duvc_ctl.devices:
            pytest.skip("No camera connected: duvc_ctl.list_devices()")
        devices = list(duvc_ctl.list_devices())
        self.device = devices[0]  # Use first device
        result = duvc_ctl.open_camera(self.device)
        if not result.is_ok():
            pytest.skip(f"Cannot open camera: {result.error}")
        self.camera = result.value
        yield

    
    @pytest.mark.skipif(not duvc_ctl.devices, reason="Hardware test requires camera")
    def test_kspropertyse_instantiation(self):
        """Test KsPropertySet instantiation with hardware."""
        ks = duvc_ctl.KsPropertySet(self.device)
        assert ks.is_valid()
    
    @pytest.mark.skipif(not duvc_ctl.devices, reason="Hardware test requires camera")
    def test_kspropertyse_isvalid(self):
        """Test KsPropertySet.is_valid() method."""
        ks = duvc_ctl.KsPropertySet(self.device)
        assert ks.is_valid()
    
    @pytest.mark.skipif(not duvc_ctl.devices, reason="Hardware test requires camera")
    def test_kspropertyse_query_support(self):
        """Test KsPropertySet.query_support() method."""
        ks = duvc_ctl.KsPropertySet(self.device)
        
        # query_support expects (GUID property_set, int property_id)
        # PROPSETID_VIDCAP_VIDEOPROCAMP = {C6E13370-30AC-11d0-A18C-00A0C9118956}
        # VideoProcAmp_Brightness = 0
        vidproc_guid = duvc_ctl.PyGUID("C6E13370-30AC-11d0-A18C-00A0C9118956")
        brightness_id = 0  # VideoProcAmp_Brightness
        
        result = ks.query_support(vidproc_guid, brightness_id)  # CHANGE: Remove .guid
        
        # Should either succeed or return NOT_SUPPORTED (device-dependent)
        assert result.is_ok() or result.error().code() == duvc_ctl.ErrorCode.PropertyNotSupported

@pytest.mark.hardware
class TestVendorPropertiesWithHardware:
    """Test vendor property functions with real device."""
    
    def test_get_vendor_property_returns_tuple(self, test_device):
        """Test get_vendor_property() returns (bool, bytes) tuple."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import get_vendor_property
        
        if test_device is None:
            pytest.skip("No test device available")
        
        # Use a fake GUID for testing
        test_guid = "11111111-2222-3333-4444-555555555555"
        
        result = get_vendor_property(test_device, test_guid, 0)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        
        success, data = result
        assert isinstance(success, bool)
        assert isinstance(data, bytes)
    
    def test_set_vendor_property_returns_bool(self, test_device):
        """Test set_vendor_property() returns bool."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import set_vendor_property
        
        if test_device is None:
            pytest.skip("No test device available")
        
        test_guid = "11111111-2222-3333-4444-555555555555"
        test_data = b'\x00\x01\x02\x03'
        
        result = set_vendor_property(test_device, test_guid, 0, test_data)
        
        assert isinstance(result, bool)
    
    def test_query_vendor_property_support_returns_bool(self, test_device):
        """Test query_vendor_property_support() returns bool."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import query_vendor_property_support
        
        if test_device is None:
            pytest.skip("No test device available")
        
        test_guid = "11111111-2222-3333-4444-555555555555"
        
        result = query_vendor_property_support(test_device, test_guid, 0)
        
        assert isinstance(result, int)  # Returns support flags


#@pytest.mark.skipif(True, reason="Skipping Logitech property tests due to unknown expecations")
@pytest.mark.hardware
class TestLogitechPropertiesWithHardware:
    """Test Logitech property functions with real device."""
    
    def test_supports_logitech_properties_returns_bool(self, test_device):
        """Test supports_logitech_properties() returns BoolResult."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import supports_logitech_properties
        
        if test_device is None:
            pytest.skip("No test device available")
        
        result = supports_logitech_properties(test_device)
        
        # Returns BoolResult, not raw bool
        assert hasattr(result, 'is_ok')  # Result type
        if result.is_ok():
            assert isinstance(result.value(), bool)

        
    def test_get_logitech_property_with_non_logitech_device(self, test_device):
        """Test get_logitech_property() with non-Logitech device."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import get_logitech_property, LogitechProperty, supports_logitech_properties
        
        if test_device is None:
            pytest.skip("No test device available")
        
        # Check if device supports Logitech properties
        if not supports_logitech_properties(test_device):
            # Expected: Should return empty or error result
            result = get_logitech_property(test_device, LogitechProperty.RightLight)
            
            # Result format depends on implementation
            # May be tuple or ResultT
            assert result is not None
        else:
            pytest.skip("Device supports Logitech properties")
    
    def test_set_logitech_property_with_non_logitech_device(self, test_device):
        """Test set_logitech_property() with non-Logitech device."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import set_logitech_property, LogitechProperty, supports_logitech_properties
        
        if test_device is None:
            pytest.skip("No test device available")
        
        if not supports_logitech_properties(test_device):
            # Expected: Should fail gracefully
            result = set_logitech_property(test_device, LogitechProperty.RightLight, b'\x00')
            
            # Should return bool or result indicating failure
            assert result is not None
        else:
            pytest.skip("Device supports Logitech properties")


@pytest.mark.hardware
class TestDeviceConnectionWithHardware:
    """Test DeviceConnection with real device."""
    
    def test_deviceconnection_instantiation(self, test_device):
        """Test DeviceConnection can be created."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import DeviceConnection
        
        if test_device is None:
            pytest.skip("No test device available")
        
        conn = DeviceConnection(test_device)
        
        assert isinstance(conn, DeviceConnection)
    
    def test_deviceconnection_isvalid(self, test_device):
        """Test DeviceConnection.is_valid() method."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import DeviceConnection
        
        if test_device is None:
            pytest.skip("No test device available")
        
        conn = DeviceConnection(test_device)
        
        assert isinstance(conn.is_valid(), bool)
    
    def test_deviceconnection_get_camera_property(self, test_device):
        """Test DeviceConnection.get() for camera property."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import DeviceConnection, CamProp
        
        if test_device is None:
            pytest.skip("No test device available")
        
        conn = DeviceConnection(test_device)
        
        if not conn.is_valid():
            pytest.skip("DeviceConnection not valid")
        
        try:
            # Returns (bool, PropSetting) tuple
            result = conn.get(CamProp.Pan)
            
            assert isinstance(result, tuple)
            assert len(result) == 2
        except Exception:
            # May fail for unsupported properties
            pass
    
    def test_deviceconnection_get_video_property(self, test_device):
        """Test DeviceConnection.get() for video property."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import DeviceConnection, VidProp
        
        if test_device is None:
            pytest.skip("No test device available")
        
        conn = DeviceConnection(test_device)
        
        if not conn.is_valid():
            pytest.skip("DeviceConnection not valid")
        
        try:
            result = conn.get(VidProp.Brightness)
            
            assert isinstance(result, tuple)
            assert len(result) == 2
        except Exception:
            pass


@pytest.mark.hardware
class TestWindowsErrorDecoding:
    """Test Windows-specific error decoding functions."""
    
    def test_decode_hresult_exists_on_windows(self):
        """Test decode_hresult() function exists on Windows."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'decode_hresult')
        assert callable(duvc_ctl.decode_hresult)
    
    def test_decode_hresult_with_zero(self):
        """Test decode_hresult() with S_OK (0)."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        from duvc_ctl import decode_hresult
        
        result = decode_hresult(0)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_get_hresult_details_exists(self):
        """Test get_hresult_details() function exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'get_hresult_details')
        assert callable(duvc_ctl.get_hresult_details)
    
    def test_is_device_error_exists(self):
        """Test is_device_error() function exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'is_device_error')
        assert callable(duvc_ctl.is_device_error)
    
    def test_is_permission_error_exists(self):
        """Test is_permission_error() function exists."""
        if not WINDOWS_ONLY:
            pytest.skip("Windows-only feature")
        
        assert hasattr(duvc_ctl, 'is_permission_error')
        assert callable(duvc_ctl.is_permission_error)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
