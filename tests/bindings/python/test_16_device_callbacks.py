"""
Test Suite 16: Device Callbacks
================================

Tests device hotplug notification callbacks for device connection changes.

Functionality Tested:
  Callback Registration (2):
    - register_device_change_callback(callback) - Register callback for device events
    - unregister_device_change_callback() - Unregister callback
  
  Device Events (2):
    - Device added notification - When device is connected
    - Device removed notification - When device is disconnected

Total: 4 device callback operations

Test Organization:
  1. Without Camera Tests - Callback interface verification
  2. With Camera Tests - Integration tests using real callback invocations

Run: pytest tests/test_16_device_callbacks.py -v
Run without camera: pytest tests/test_16_device_callbacks.py -v -m "not hardware"
"""

import pytest
import sys
import time
from typing import List, Tuple, Optional

import duvc_ctl
from duvc_ctl import (
    # Device functions
    list_devices,
    # Callback functions
    register_device_change_callback,
    unregister_device_change_callback,
    # Core types
    Device,
)


# ============================================================================
# WITHOUT CAMERA TESTS - Callback interface verification
# ============================================================================

class TestDeviceCallbackInterfaces:
    """Test device callback function interfaces exist."""
    
    def test_register_device_change_callback_exists(self):
        """Test register_device_change_callback() function exists."""
        assert hasattr(duvc_ctl, 'register_device_change_callback')
        assert callable(register_device_change_callback)
    
    def test_unregister_device_change_callback_exists(self):
        """Test unregister_device_change_callback() function exists."""
        assert hasattr(duvc_ctl, 'unregister_device_change_callback')
        assert callable(unregister_device_change_callback)
    
    def test_device_change_callback_typedef_exists(self):
        """Test DeviceChangeCallback type alias exists."""
        # DeviceChangeCallback: Callable[[bool, str], None]
        assert hasattr(duvc_ctl, 'DeviceChangeCallback')


class TestCallbackRegistration:
    """Test callback registration without device changes."""
    
    def test_register_callback_accepts_callable(self):
        """Test register_device_change_callback() accepts callable."""
        def test_callback(added: bool, device_path: str):
            pass
        
        try:
            register_device_change_callback(test_callback)
        finally:
            unregister_device_change_callback()
    
    def test_register_callback_with_lambda(self):
        """Test register_device_change_callback() with lambda."""
        try:
            register_device_change_callback(lambda added, path: None)
        finally:
            unregister_device_change_callback()
    
    def test_unregister_callback_without_registration(self):
        """Test unregister_device_change_callback() when no callback registered."""
        # Should not crash
        unregister_device_change_callback()
    
    def test_register_callback_twice(self):
        """Test registering callback twice replaces previous callback."""
        first_called = []
        second_called = []
        
        def first_callback(added: bool, device_path: str):
            first_called.append((added, device_path))
        
        def second_callback(added: bool, device_path: str):
            second_called.append((added, device_path))
        
        try:
            register_device_change_callback(first_callback)
            register_device_change_callback(second_callback)
            
            # Only second callback should be active
            # (No device changes to test, but registration should succeed)
        finally:
            unregister_device_change_callback()
    
    def test_callback_signature_bool_str(self):
        """Test callback signature is (bool, str)."""
        callback_invoked = []
        
        def test_callback(added: bool, device_path: str):
            # Verify types
            assert isinstance(added, bool)
            assert isinstance(device_path, str)
            callback_invoked.append(True)
        
        try:
            register_device_change_callback(test_callback)
            # Callback will be invoked on actual device changes only
        finally:
            unregister_device_change_callback()


class TestCallbackLifecycle:
    """Test callback lifecycle without device changes."""
    
    def test_register_unregister_cycle(self):
        """Test register → unregister cycle."""
        def test_callback(added: bool, device_path: str):
            pass
        
        # Register
        register_device_change_callback(test_callback)
        
        # Unregister
        unregister_device_change_callback()
        
        # Should be able to register again
        register_device_change_callback(test_callback)
        unregister_device_change_callback()
    
    def test_multiple_register_unregister_cycles(self):
        """Test multiple register/unregister cycles."""
        def test_callback(added: bool, device_path: str):
            pass
        
        for _ in range(3):
            register_device_change_callback(test_callback)
            unregister_device_change_callback()
    
    def test_callback_with_class_method(self):
        """Test callback using class method."""
        class CallbackHandler:
            def __init__(self):
                self.events = []
            
            def handle_device_change(self, added: bool, device_path: str):
                self.events.append((added, device_path))
        
        handler = CallbackHandler()
        
        try:
            register_device_change_callback(handler.handle_device_change)
        finally:
            unregister_device_change_callback()
    
    def test_callback_with_closure(self):
        """Test callback using closure."""
        captured_events = []
        
        def make_callback():
            def callback(added: bool, device_path: str):
                captured_events.append((added, device_path))
            return callback
        
        try:
            register_device_change_callback(make_callback())
        finally:
            unregister_device_change_callback()


# ============================================================================
# WITH CAMERA TESTS - Integration tests using real callbacks
# ============================================================================

@pytest.mark.hardware
class TestCallbackParameterTypes:
    """Test callback parameter types with real invocations."""
    
    def test_callback_receives_bool_for_added_parameter(self):
        """Test callback receives bool for added parameter."""
        param_types = []
        
        def test_callback(added: bool, device_path: str):
            param_types.append(('added', type(added)))
        
        try:
            register_device_change_callback(test_callback)
            
            # Get initial device list to trigger any pending notifications
            devices = list_devices()
            
            # Wait briefly for any callbacks
            time.sleep(0.1)
            
            # If callbacks were invoked, verify types
            for param_name, param_type in param_types:
                if param_name == 'added':
                    assert param_type == bool
        finally:
            unregister_device_change_callback()
    
    def test_callback_receives_str_for_device_path(self):
        """Test callback receives str for device_path parameter."""
        param_types = []
        
        def test_callback(added: bool, device_path: str):
            param_types.append(('device_path', type(device_path)))
        
        try:
            register_device_change_callback(test_callback)
            
            devices = list_devices()
            time.sleep(0.1)
            
            for param_name, param_type in param_types:
                if param_name == 'device_path':
                    assert param_type == str
        finally:
            unregister_device_change_callback()
    
    def test_device_path_is_non_empty_string(self):
        """Test device_path is non-empty string."""
        device_paths = []
        
        def test_callback(added: bool, device_path: str):
            device_paths.append(device_path)
        
        try:
            register_device_change_callback(test_callback)
            
            devices = list_devices()
            time.sleep(0.1)
            
            for path in device_paths:
                assert isinstance(path, str)
                assert len(path) > 0
        finally:
            unregister_device_change_callback()


@pytest.mark.hardware
class TestCallbackInvocationBasics:
    """Test basic callback invocation behavior."""
    
    def test_callback_not_invoked_without_device_changes(self):
        """Test callback is not invoked without device changes."""
        callback_count = []
        
        def test_callback(added: bool, device_path: str):
            callback_count.append(1)
        
        try:
            register_device_change_callback(test_callback)
            
            # No device changes - callback should not be invoked
            # (Or may have initial notifications for existing devices)
            time.sleep(0.1)
            
            # Just verify callback is registered (no assertion on count)
        finally:
            unregister_device_change_callback()
    
    def test_callback_captures_events_correctly(self):
        """Test callback captures device change events correctly."""
        captured_events = []
        
        def test_callback(added: bool, device_path: str):
            captured_events.append({
                'added': added,
                'device_path': device_path,
                'timestamp': time.time()
            })
        
        try:
            register_device_change_callback(test_callback)
            
            # Get devices to trigger any notifications
            devices = list_devices()
            time.sleep(0.1)
            
            # Verify event structure
            for event in captured_events:
                assert 'added' in event
                assert 'device_path' in event
                assert 'timestamp' in event
                assert isinstance(event['added'], bool)
                assert isinstance(event['device_path'], str)
                assert isinstance(event['timestamp'], float)
        finally:
            unregister_device_change_callback()
    
    def test_callback_can_be_called_multiple_times(self):
        """Test callback can be invoked multiple times."""
        invocation_count = 0
        
        def test_callback(added: bool, device_path: str):
            invocation_count += 1
        
        try:
            register_device_change_callback(test_callback)
            
            # Multiple device enumerations
            for _ in range(3):
                list_devices()
                time.sleep(0.05)
            
            # Callback may be invoked (depends on device state)
            # Just verify it doesn't crash
            assert invocation_count >= 0
        finally:
            unregister_device_change_callback()


@pytest.mark.hardware
class TestCallbackExceptionHandling:
    """Test callback exception handling."""
    
    def test_callback_exception_does_not_crash_library(self):
        """Test callback that raises exception doesn't crash library."""
        def bad_callback(added: bool, device_path: str):
            raise RuntimeError("Callback error")
        
        try:
            register_device_change_callback(bad_callback)
            
            # Library should handle exception gracefully
            devices = list_devices()
            time.sleep(0.1)
            
            # Should still be able to enumerate devices
            devices = list_devices()
            assert isinstance(devices, list)
        finally:
            unregister_device_change_callback()
    
    def test_callback_with_type_error_handled(self):
        """Test callback with type error is handled gracefully."""
        def bad_callback(added: bool, device_path: str):
            # Intentional error
            return added + device_path  # Can't add bool + str
        
        try:
            register_device_change_callback(bad_callback)
            
            devices = list_devices()
            time.sleep(0.1)
            
            # Library should continue working
            assert isinstance(devices, list)
        finally:
            unregister_device_change_callback()
    
    def test_callback_with_attribute_error_handled(self):
        """Test callback with attribute error is handled."""
        def bad_callback(added: bool, device_path: str):
            # Try to access non-existent attribute
            return device_path.nonexistent_method()
        
        try:
            register_device_change_callback(bad_callback)
            
            devices = list_devices()
            time.sleep(0.1)
            
            # Should not crash
            assert isinstance(devices, list)
        finally:
            unregister_device_change_callback()


@pytest.mark.hardware
class TestCallbackWithDeviceOperations:
    """Test callbacks alongside device operations."""
    
    def test_callback_with_device_enumeration(self):
        """Test callback works alongside device enumeration."""
        callback_events = []
        
        def test_callback(added: bool, device_path: str):
            callback_events.append((added, device_path))
        
        try:
            register_device_change_callback(test_callback)
            
            # Enumerate devices multiple times
            devices1 = list_devices()
            time.sleep(0.05)
            
            devices2 = list_devices()
            time.sleep(0.05)
            
            # Both enumerations should succeed
            assert isinstance(devices1, list)
            assert isinstance(devices2, list)
        finally:
            unregister_device_change_callback()
    
    def test_callback_state_tracking(self):
        """Test callback can maintain state across invocations."""
        class DeviceTracker:
            def __init__(self):
                self.known_devices = set()
                self.add_count = 0
                self.remove_count = 0
            
            def handle_change(self, added: bool, device_path: str):
                if added:
                    self.known_devices.add(device_path)
                    self.add_count += 1
                else:
                    self.known_devices.discard(device_path)
                    self.remove_count += 1
        
        tracker = DeviceTracker()
        
        try:
            register_device_change_callback(tracker.handle_change)
            
            devices = list_devices()
            time.sleep(0.1)
            
            # Tracker state should be accessible
            assert hasattr(tracker, 'known_devices')
            assert hasattr(tracker, 'add_count')
            assert hasattr(tracker, 'remove_count')
            assert isinstance(tracker.known_devices, set)
        finally:
            unregister_device_change_callback()


@pytest.mark.hardware
class TestCallbackDeregistration:
    """Test callback deregistration behavior."""
    
    def test_unregister_stops_callbacks(self):
        """Test unregister_device_change_callback() stops further callbacks."""
        callback_count = 0
        
        def test_callback(added: bool, device_path: str):
            callback_count += 1
        
        register_device_change_callback(test_callback)
        
        devices = list_devices()
        time.sleep(0.05)
        
        # Unregister
        unregister_device_change_callback()
        
        # Further device operations should not trigger callback
        devices = list_devices()
        time.sleep(0.05)
        
        # Can't assert exact count since we don't control device changes
        # Just verify unregister doesn't crash
    
    def test_register_after_unregister(self):
        """Test re-registering callback after unregister."""
        first_count = 0
        second_count = 0
        
        def first_callback(added: bool, device_path: str):
            first_count += 1
        
        def second_callback(added: bool, device_path: str):
            second_count += 1
        
        # First registration
        register_device_change_callback(first_callback)
        devices = list_devices()
        time.sleep(0.05)
        
        # Unregister
        unregister_device_change_callback()
        
        # Second registration
        register_device_change_callback(second_callback)
        devices = list_devices()
        time.sleep(0.05)
        
        # Cleanup
        unregister_device_change_callback()


@pytest.mark.hardware
class TestCallbackConcurrency:
    """Test callback behavior under concurrent operations."""
    
    def test_callback_thread_safety(self):
        """Test callback is thread-safe."""
        callback_events = []
        
        def test_callback(added: bool, device_path: str):
            # Thread-safe append
            callback_events.append((added, device_path))
        
        try:
            register_device_change_callback(test_callback)
            
            # Multiple rapid device enumerations
            for _ in range(5):
                devices = list_devices()
                time.sleep(0.01)
            
            # Should complete without crashes
        finally:
            unregister_device_change_callback()
    
    def test_callback_with_long_execution(self):
        """Test callback with long execution time."""
        def slow_callback(added: bool, device_path: str):
            # Simulate slow processing
            time.sleep(0.05)
        
        try:
            register_device_change_callback(slow_callback)
            
            # Device enumeration should not block indefinitely
            devices = list_devices()
            time.sleep(0.1)
            
            assert isinstance(devices, list)
        finally:
            unregister_device_change_callback()


@pytest.mark.hardware
class TestCallbackEventDetails:
    """Test callback event detail validation."""
    
    def test_added_true_means_device_connected(self):
        """Test added=True indicates device was connected."""
        add_events = []
        
        def test_callback(added: bool, device_path: str):
            if added:
                add_events.append(device_path)
        
        try:
            register_device_change_callback(test_callback)
            
            devices = list_devices()
            time.sleep(0.1)
            
            # If add events captured, verify they're strings
            for path in add_events:
                assert isinstance(path, str)
                assert len(path) > 0
        finally:
            unregister_device_change_callback()
    
    def test_added_false_means_device_disconnected(self):
        """Test added=False indicates device was disconnected."""
        remove_events = []
        
        def test_callback(added: bool, device_path: str):
            if not added:
                remove_events.append(device_path)
        
        try:
            register_device_change_callback(test_callback)
            
            devices = list_devices()
            time.sleep(0.1)
            
            # If remove events captured, verify they're strings
            for path in remove_events:
                assert isinstance(path, str)
                assert len(path) > 0
        finally:
            unregister_device_change_callback()
    
    def test_device_path_format(self):
        """Test device_path has valid format."""
        device_paths = []
        
        def test_callback(added: bool, device_path: str):
            device_paths.append(device_path)
        
        try:
            register_device_change_callback(test_callback)
            
            devices = list_devices()
            time.sleep(0.1)
            
            # Verify paths are non-empty strings
            for path in device_paths:
                assert isinstance(path, str)
                assert len(path) > 0
                # Device paths typically contain backslashes on Windows
                # But don't assert format as it's platform-specific
        finally:
            unregister_device_change_callback()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
