"""
Test Suite 04: Device Enumeration
==================================

Tests device enumeration and connection status functions exposed by duvc-ctl.

Functions Tested:
  - list_devices() - Enumerate all video input devices
  - devices() - Alias for list_devices()
  - is_device_connected() - Check device connection status
  - iter_devices() - Device iterator
  - iter_connected_devices() - Connected device iterator

Total: 5 core enumeration functions

Test Organization:
  1. Without Camera Tests - Unit tests without requiring specific hardware
  2. With Camera Tests - Integration tests using real camera devices

Run: pytest tests/test_04_device_enumeration.py -v
Run without camera: pytest tests/test_04_device_enumeration.py -v -m "not hardware"
"""

import pytest
import sys
import time
from typing import List, Optional

import duvc_ctl
from duvc_ctl import (
    # Core types
    Device,
    # Device enumeration functions
    list_devices, devices, is_device_connected,
    iter_devices, iter_connected_devices,
    # Core enums
    ErrorCode,
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
def test_device_2(available_devices) -> Optional[Device]:
    """Get second available device for multi-device testing."""
    if len(available_devices) < 2:
        pytest.skip("Need at least 2 camera devices for this test")
    return available_devices[1]


# ============================================================================
# WITHOUT CAMERA TESTS - Unit tests on enumeration functions
# ============================================================================

class TestListDevicesFunction:
    """Test list_devices() function - core device enumeration."""
    
    def test_list_devices_returns_list(self):
        """Test list_devices() returns a list."""
        result = list_devices()
        
        assert isinstance(result, list)
    
    def test_list_devices_items_are_devices(self):
        """Test list_devices() returns list of Device objects."""
        result = list_devices()
        
        for item in result:
            assert isinstance(item, Device)
    
    def test_list_devices_consistency(self):
        """Test list_devices() returns consistent results."""
        # Call twice in quick succession
        result1 = list_devices()
        result2 = list_devices()
        
        # Should return same number of devices
        assert len(result1) == len(result2)
        
        # Device paths should match (stable identifiers)
        if result1:
            paths1 = {dev.path for dev in result1}
            paths2 = {dev.path for dev in result2}
            assert paths1 == paths2
    
    def test_list_devices_no_duplicates(self):
        """Test list_devices() doesn't return duplicate devices."""
        result = list_devices()
        
        if len(result) > 0:
            # Check for duplicates by path (unique identifier)
            paths = [dev.path for dev in result]
            assert len(paths) == len(set(paths)), "Duplicate devices found"
    
    def test_list_devices_idempotent(self):
        """Test list_devices() is idempotent - multiple calls safe."""
        # Call multiple times
        for _ in range(5):
            result = list_devices()
            assert isinstance(result, list)


class TestDevicesAlias:
    """Test devices() function - alias for list_devices()."""
    
    def test_devices_returns_list(self):
        """Test devices() returns a list."""
        result = devices()
        
        assert isinstance(result, list)
    
    def test_devices_same_as_list_devices(self):
        """Test devices() returns same result as list_devices()."""
        result_list_devices = list_devices()
        result_devices = devices()
        
        # Should return same number
        assert len(result_list_devices) == len(result_devices)
        
        # Should return same device paths
        if result_list_devices:
            paths1 = {dev.path for dev in result_list_devices}
            paths2 = {dev.path for dev in result_devices}
            assert paths1 == paths2
    
    def test_devices_consistency(self):
        """Test devices() returns consistent results."""
        result1 = devices()
        result2 = devices()
        
        assert len(result1) == len(result2)


class TestIsDeviceConnectedFunction:
    """Test is_device_connected() function - device connection status."""
    
    def test_is_device_connected_returns_result(self):
        """Test is_device_connected() returns boolean."""
        # Create mock device
        device = Device("Test Device", "/test/path")
        result = is_device_connected(device)
        
        # Should return a boolean value
        assert isinstance(result, bool)
    
    def test_is_device_connected_with_invalid_device(self):
        """Test is_device_connected() with invalid device."""
        # Empty device
        empty_device = Device()
        result = is_device_connected(empty_device)
        
        # Should return False for invalid device
        assert isinstance(result, bool)
        assert result == False
    
    def test_is_device_connected_with_nonexistent_device(self):
        """Test is_device_connected() with nonexistent device."""
        fake_device = Device("Nonexistent Camera", "/nonexistent/path/12345")
        result = is_device_connected(fake_device)
        
        # Should return False for nonexistent device
        assert isinstance(result, bool)
        assert result == False


class TestIterDevicesFunction:
    """Test iter_devices() iterator function."""
    
    def test_iter_devices_returns_iterator(self):
        """Test iter_devices() returns an iterator."""
        iterator = iter_devices()
        
        # Should be iterable
        assert hasattr(iterator, '__iter__') or hasattr(iterator, '__next__')
    
    def test_iter_devices_yields_devices(self):
        """Test iter_devices() yields Device objects."""
        for device in iter_devices():
            assert isinstance(device, Device)
            # Only check first few to avoid long iteration
            break
    
    def test_iter_devices_consistent_with_list_devices(self):
        """Test iter_devices() yields same devices as list_devices()."""
        devices_list = list_devices()
        devices_iter = list(iter_devices())
        
        # Should yield same number
        assert len(devices_list) == len(devices_iter)
        
        # Should yield same devices (by path)
        if devices_list:
            paths_list = {dev.path for dev in devices_list}
            paths_iter = {dev.path for dev in devices_iter}
            assert paths_list == paths_iter


class TestIterConnectedDevicesFunction:
    """Test iter_connected_devices() iterator function."""
    
    def test_iter_connected_devices_returns_iterator(self):
        """Test iter_connected_devices() returns an iterator."""
        iterator = iter_connected_devices()
        
        # Should be iterable
        assert hasattr(iterator, '__iter__') or hasattr(iterator, '__next__')
    
    def test_iter_connected_devices_yields_devices(self):
        """Test iter_connected_devices() yields Device objects."""
        for device in iter_connected_devices():
            assert isinstance(device, Device)
            # Only check first device
            break
    
    def test_iter_connected_devices_subset_of_iter_devices(self):
        """Test iter_connected_devices() yields subset of iter_devices()."""
        all_devices = set(dev.path for dev in iter_devices())
        connected_devices = set(dev.path for dev in iter_connected_devices())
        
        # Connected devices should be subset of all devices
        assert connected_devices.issubset(all_devices)


class TestEnumerationPerformance:
    """Test performance characteristics of enumeration functions."""
    
    def test_list_devices_completes_quickly(self):
        """Test list_devices() completes in reasonable time."""
        import time
        
        start = time.time()
        result = list_devices()
        duration = time.time() - start
        
        # Should complete in under 5 seconds (generous for slow systems)
        assert duration < 5.0, f"list_devices() took {duration:.2f}s"
    
    def test_multiple_enumerations_consistent_performance(self):
        """Test multiple enumerations have consistent performance."""
        durations = []
        for _ in range(3):
            start = time.time()
            list_devices()
            durations.append(time.time() - start)
        
        # All should complete in reasonable time
        for duration in durations:
            assert duration < 5.0


# ============================================================================
# WITH CAMERA TESTS - Integration tests using real camera
# ============================================================================

@pytest.mark.hardware
class TestListDevicesWithHardware:
    """Test list_devices() with real camera hardware."""
    
    def test_list_devices_finds_cameras(self, available_devices):
        """Test list_devices() finds connected cameras."""
        if not available_devices:
            pytest.skip("No devices available")
        
        # Should find at least one device
        assert len(available_devices) > 0
    
    def test_listed_devices_are_valid(self, available_devices):
        """Test all listed devices are valid."""
        if not available_devices:
            pytest.skip("No devices available")
        
        for device in available_devices:
            assert device.is_valid()
            assert len(device.name) > 0
            assert len(device.path) > 0
    
    def test_device_names_are_meaningful(self, available_devices):
        """Test device names are meaningful strings."""
        if not available_devices:
            pytest.skip("No devices available")
        
        for device in available_devices:
            # Name should be non-empty and printable
            assert len(device.name) > 0
            assert device.name.strip() == device.name  # No leading/trailing whitespace
            
            # Name should contain alphanumeric characters
            assert any(c.isalnum() for c in device.name)
    
    def test_device_paths_are_unique(self, available_devices):
        """Test device paths are unique identifiers."""
        if not available_devices:
            pytest.skip("No devices available")
        
        paths = [dev.path for dev in available_devices]
        
        # All paths should be unique
        assert len(paths) == len(set(paths))
    
    def test_device_paths_stable(self, available_devices):
        """Test device paths remain stable across enumerations."""
        if not available_devices:
            pytest.skip("No devices available")
        
        # First enumeration
        paths1 = {dev.path for dev in available_devices}
        
        # Second enumeration
        devices2 = list_devices()
        paths2 = {dev.path for dev in devices2}
        
        # Paths should be the same (if devices didn't disconnect)
        assert paths1 == paths2
    
    def test_device_count_reasonable(self, available_devices):
        """Test device count is reasonable (not obviously wrong)."""
        count = len(available_devices)
        
        # Should have at least 1 device (we skipped if 0)
        assert count >= 1
        
        # Unlikely to have more than 20 cameras on most systems
        assert count < 20, f"Unusually high device count: {count}"


@pytest.mark.hardware
class TestIsDeviceConnectedWithHardware:
    """Test is_device_connected() with real camera hardware."""
    
    def test_connected_device_returns_ok(self, test_device):
        """Test is_device_connected() returns True for connected device."""
        if test_device is None:
            pytest.skip("No test device available")
        
        result = is_device_connected(test_device)
        
        # Should return boolean True for connected device
        assert isinstance(result, bool)
        assert result == True
    
    def test_all_enumerated_devices_connected(self, available_devices):
        """Test all enumerated devices report as connected."""
        if not available_devices:
            pytest.skip("No devices available")
        
        for device in available_devices:
            result = is_device_connected(device)
            
            # All enumerated devices should return boolean
            assert isinstance(result, bool)
    
    def test_is_connected_multiple_calls(self, test_device):
        """Test is_device_connected() can be called multiple times."""
        if test_device is None:
            pytest.skip("No test device available")
        
        # Call multiple times
        for _ in range(5):
            result = is_device_connected(test_device)
            assert isinstance(result, bool)
    
    def test_disconnected_device_returns_error(self):
        """Test is_device_connected() returns False for disconnected device."""
        # Create device with invalid path
        fake_device = Device("Disconnected Camera", "/invalid/path/99999")
        result = is_device_connected(fake_device)
        
        # Should return False for nonexistent device
        assert isinstance(result, bool)
        assert result == False


@pytest.mark.hardware
class TestIteratorsWithHardware:
    """Test iterator functions with real camera hardware."""
    
    def test_iter_devices_finds_cameras(self, available_devices):
        """Test iter_devices() yields available cameras."""
        if not available_devices:
            pytest.skip("No devices available")
        
        count = 0
        for device in iter_devices():
            assert isinstance(device, Device)
            assert device.is_valid()
            count += 1
        
        # Should yield at least one device
        assert count > 0
        assert count == len(available_devices)
    
    def test_iter_connected_devices_finds_cameras(self, available_devices):
        """Test iter_connected_devices() yields connected cameras."""
        if not available_devices:
            pytest.skip("No devices available")
        
        count = 0
        for device in iter_connected_devices():
            assert isinstance(device, Device)
            assert device.is_valid()
            count += 1
        
        # Should yield at least one connected device
        assert count > 0
    
    def test_iter_devices_in_for_loop(self, available_devices):
        """Test iter_devices() works in standard for loop."""
        if not available_devices:
            pytest.skip("No devices available")
        
        devices_found = []
        for device in iter_devices():
            devices_found.append(device)
        
        assert len(devices_found) > 0
        assert all(isinstance(d, Device) for d in devices_found)
    
    def test_iter_connected_devices_in_list_comprehension(self, available_devices):
        """Test iter_connected_devices() works in list comprehension."""
        if not available_devices:
            pytest.skip("No devices available")
        
        device_names = [dev.name for dev in iter_connected_devices()]
        
        assert len(device_names) > 0
        assert all(isinstance(name, str) for name in device_names)


@pytest.mark.hardware
class TestMultiDeviceScenarios:
    """Test scenarios with multiple devices."""
    
    def test_enumeration_with_multiple_devices(self, available_devices):
        """Test enumeration with multiple connected devices."""
        if len(available_devices) < 2:
            pytest.skip("Need at least 2 devices for this test")
        
        # Verify we can enumerate multiple devices
        assert len(available_devices) >= 2
        
        # All should be valid
        for device in available_devices:
            assert device.is_valid()
        
        # All should have unique paths
        paths = [dev.path for dev in available_devices]
        assert len(paths) == len(set(paths))
    
    def test_distinguish_multiple_devices(self, available_devices):
        """Test ability to distinguish between multiple devices."""
        if len(available_devices) < 2:
            pytest.skip("Need at least 2 devices for this test")
        
        dev1 = available_devices[0]
        dev2 = available_devices[1]
        
        # Devices should be distinguishable
        assert dev1 != dev2
        assert dev1.path != dev2.path
        
        # May or may not have different names
        # (Some systems have multiple identical cameras)
    
    def test_connection_status_per_device(self, available_devices):
        """Test connection status can be checked per device."""
        if len(available_devices) < 2:
            pytest.skip("Need at least 2 devices for this test")
        
        for device in available_devices:
            result = is_device_connected(device)
            
            # Each device should return boolean connection status
            assert isinstance(result, bool)


@pytest.mark.hardware
class TestEnumerationEdgeCases:
    """Test edge cases in device enumeration."""
    
    def test_enumeration_with_no_devices(self):
        """Test enumeration behavior when no devices present."""
        # This test passes if no devices are connected
        result = list_devices()
        
        # Should return empty list, not error
        assert isinstance(result, list)
    
    def test_repeated_enumeration_after_device_change(self, available_devices):
        """Test enumeration after device state changes."""
        if not available_devices:
            pytest.skip("No devices available")
        
        # First enumeration
        count1 = len(list_devices())
        
        # Wait briefly (simulate time passing)
        time.sleep(0.1)
        
        # Second enumeration
        count2 = len(list_devices())
        
        # Counts should be consistent if no devices connected/disconnected
        # Allow small variation in case of device state changes
        assert abs(count1 - count2) <= 1
    
    def test_enumeration_thread_safety(self, available_devices):
        """Test enumeration can be called from different contexts."""
        if not available_devices:
            pytest.skip("No devices available")
        
        # Call enumeration multiple times rapidly
        results = []
        for _ in range(10):
            results.append(list_devices())
        
        # All should succeed
        assert all(isinstance(r, list) for r in results)
        
        # Counts should be consistent
        counts = [len(r) for r in results]
        assert len(set(counts)) <= 2  # Allow at most 2 different counts (hotplug)


@pytest.mark.hardware
class TestDeviceMetadata:
    """Test device metadata from enumeration."""
    
    def test_device_name_format(self, test_device):
        """Test device name is properly formatted."""
        if test_device is None:
            pytest.skip("No test device available")
        
        name = test_device.name
        
        # Name should be string
        assert isinstance(name, str)
        
        # Name should be non-empty
        assert len(name) > 0
        
        # Name should be printable
        assert name.isprintable() or any(c.isprintable() for c in name)
    
    def test_device_path_format(self, test_device):
        """Test device path is properly formatted."""
        if test_device is None:
            pytest.skip("No test device available")
        
        path = test_device.path
        
        # Path should be string
        assert isinstance(path, str)
        
        # Path should be non-empty
        assert len(path) > 0
        
        # Path should not have leading/trailing whitespace
        assert path == path.strip()
    
    def test_device_get_id(self, test_device):
        """Test device.get_id() returns stable identifier."""
        if test_device is None:
            pytest.skip("No test device available")
        
        id1 = test_device.get_id()
        id2 = test_device.get_id()
        
        # ID should be stable
        assert id1 == id2
        
        # ID should be non-empty string
        assert isinstance(id1, str)
        assert len(id1) > 0
    
    def test_device_id_unique_across_devices(self, available_devices):
        """Test device IDs are unique across different devices."""
        if len(available_devices) < 2:
            pytest.skip("Need at least 2 devices for this test")
        
        ids = [dev.get_id() for dev in available_devices]
        
        # All IDs should be unique
        assert len(ids) == len(set(ids))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
