"""
Test Suite 14: Logging
=======================

Tests logging functions and callback mechanisms.

Logging Functionality Tested:
  Log Level Management (2):
    - set_log_level(level) - Set minimum log level
    - get_log_level() - Get current log level
  
  Direct Logging Functions (5):
    - log_debug(message) - Log debug message
    - log_info(message) - Log info message
    - log_warning(message) - Log warning message
    - log_error(message) - Log error message
    - log_critical(message) - Log critical message
  
  Generic Logging (1):
    - log_message(level, message) - Log message at specific level
  
  Callback System (1):
    - set_log_callback(callback) - Register callback for log messages

Total: 9 logging operations

Test Organization:
  1. Basic Logging Tests - Log level and direct logging
  2. Callback Tests - Log callback registration and invocation

Run: pytest tests/test_14_logging.py -v
"""

import pytest
import sys
from typing import List, Tuple, Optional

import duvc_ctl
from duvc_ctl import (
    # Logging functions
    set_log_level, get_log_level,
    log_debug, log_info, log_warning, log_error, log_critical,
    log_message,
    set_log_callback,
    # Core enums
    LogLevel,
)


# ============================================================================
# BASIC LOGGING TESTS
# ============================================================================

class TestLogLevelManagement:
    """Test log level get/set functions."""
    
    def test_get_log_level_returns_loglevel(self):
        """Test get_log_level() returns LogLevel enum."""
        level = get_log_level()
        
        assert isinstance(level, LogLevel)
    
    def test_set_log_level_debug(self):
        """Test set_log_level() with Debug level."""
        # Save original level
        original_level = get_log_level()
        
        try:
            # Set to Debug
            set_log_level(LogLevel.Debug)
            
            # Verify it was set
            current_level = get_log_level()
            assert current_level == LogLevel.Debug
        finally:
            # Restore original level
            set_log_level(original_level)
    
    def test_set_log_level_info(self):
        """Test set_log_level() with Info level."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Info)
            
            current_level = get_log_level()
            assert current_level == LogLevel.Info
        finally:
            set_log_level(original_level)
    
    def test_set_log_level_warning(self):
        """Test set_log_level() with Warning level."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Warning)
            
            current_level = get_log_level()
            assert current_level == LogLevel.Warning
        finally:
            set_log_level(original_level)
    
    def test_set_log_level_error(self):
        """Test set_log_level() with Error level."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Error)
            
            current_level = get_log_level()
            assert current_level == LogLevel.Error
        finally:
            set_log_level(original_level)
    
    def test_set_log_level_critical(self):
        """Test set_log_level() with Critical level."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Critical)
            
            current_level = get_log_level()
            assert current_level == LogLevel.Critical
        finally:
            set_log_level(original_level)
    
    def test_set_log_level_persistence(self):
        """Test log level persists across multiple gets."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Debug)
            
            level1 = get_log_level()
            level2 = get_log_level()
            level3 = get_log_level()
            
            assert level1 == level2 == level3 == LogLevel.Debug
        finally:
            set_log_level(original_level)


class TestDirectLoggingFunctions:
    """Test direct logging functions (log_debug, log_info, etc.)."""
    
    def test_log_debug_executes(self):
        """Test log_debug() executes without error."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Debug)
            log_debug("Test debug message")
        finally:
            set_log_level(original_level)
    
    def test_log_info_executes(self):
        """Test log_info() executes without error."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Info)
            log_info("Test info message")
        finally:
            set_log_level(original_level)
    
    def test_log_warning_executes(self):
        """Test log_warning() executes without error."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Warning)
            log_warning("Test warning message")
        finally:
            set_log_level(original_level)
    
    def test_log_error_executes(self):
        """Test log_error() executes without error."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Error)
            log_error("Test error message")
        finally:
            set_log_level(original_level)
    
    def test_log_critical_executes(self):
        """Test log_critical() executes without error."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Critical)
            log_critical("Test critical message")
        finally:
            set_log_level(original_level)
    
    def test_log_functions_with_special_characters(self):
        """Test logging functions with special characters."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Debug)
            
            log_debug("Debug: Special chars !@#$%^&*()")
            log_info("Info: Unicode 日本語 test")
            log_warning("Warning: Newline\ntest")
            log_error("Error: Tab\ttest")
        finally:
            set_log_level(original_level)
    
    def test_log_functions_with_long_messages(self):
        """Test logging functions with long messages."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Debug)
            
            long_message = "X" * 1000
            log_debug(long_message)
            log_info(long_message)
        finally:
            set_log_level(original_level)
    
    def test_log_functions_with_empty_messages(self):
        """Test logging functions with empty messages."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Debug)
            
            log_debug("")
            log_info("")
            log_warning("")
        finally:
            set_log_level(original_level)


class TestGenericLogMessage:
    """Test log_message() generic logging function."""
    
    def test_log_message_debug(self):
        """Test log_message() with Debug level."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Debug)
            log_message(LogLevel.Debug, "Generic debug message")
        finally:
            set_log_level(original_level)
    
    def test_log_message_info(self):
        """Test log_message() with Info level."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Info)
            log_message(LogLevel.Info, "Generic info message")
        finally:
            set_log_level(original_level)
    
    def test_log_message_warning(self):
        """Test log_message() with Warning level."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Warning)
            log_message(LogLevel.Warning, "Generic warning message")
        finally:
            set_log_level(original_level)
    
    def test_log_message_error(self):
        """Test log_message() with Error level."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Error)
            log_message(LogLevel.Error, "Generic error message")
        finally:
            set_log_level(original_level)
    
    def test_log_message_critical(self):
        """Test log_message() with Critical level."""
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Critical)
            log_message(LogLevel.Critical, "Generic critical message")
        finally:
            set_log_level(original_level)


# ============================================================================
# CALLBACK TESTS
# ============================================================================

class TestLogCallbackRegistration:
    """Test set_log_callback() registration."""
    
    def test_set_log_callback_accepts_callable(self):
        """Test set_log_callback() accepts callable."""
        def test_callback(level: LogLevel, message: str):
            pass
        
        # Should not raise exception
        set_log_callback(test_callback)
        
        # Clear callback
        set_log_callback(None)
    
    def test_set_log_callback_with_none(self):
        """Test set_log_callback() with None to clear callback."""
        def test_callback(level: LogLevel, message: str):
            pass
        
        # Register callback
        set_log_callback(test_callback)
        
        # Clear callback
        set_log_callback(None)
    
    def test_set_log_callback_with_lambda(self):
        """Test set_log_callback() with lambda function."""
        set_log_callback(lambda level, message: None)
        
        # Clear callback
        set_log_callback(None)


class TestLogCallbackInvocation:
    """Test callback invocation when logging."""
    
    def test_callback_invoked_on_log_debug(self):
        """Test callback is invoked for log_debug()."""
        captured_logs = []
        
        def test_callback(level: LogLevel, message: str):
            captured_logs.append((level, message))
        
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Debug)
            set_log_callback(test_callback)
            
            log_debug("Test debug callback")
            
            # Callback should have been invoked
            assert len(captured_logs) >= 1
            
            # Find our message
            found = any(msg == "Test debug callback" for level, msg in captured_logs)
            assert found
        finally:
            set_log_callback(None)
            set_log_level(original_level)
    
    def test_callback_invoked_on_log_info(self):
        """Test callback is invoked for log_info()."""
        captured_logs = []
        
        def test_callback(level: LogLevel, message: str):
            captured_logs.append((level, message))
        
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Info)
            set_log_callback(test_callback)
            
            log_info("Test info callback")
            
            assert len(captured_logs) >= 1
            found = any(msg == "Test info callback" for level, msg in captured_logs)
            assert found
        finally:
            set_log_callback(None)
            set_log_level(original_level)
    
    def test_callback_invoked_on_log_warning(self):
        """Test callback is invoked for log_warning()."""
        captured_logs = []
        
        def test_callback(level: LogLevel, message: str):
            captured_logs.append((level, message))
        
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Warning)
            set_log_callback(test_callback)
            
            log_warning("Test warning callback")
            
            assert len(captured_logs) >= 1
            found = any(msg == "Test warning callback" for level, msg in captured_logs)
            assert found
        finally:
            set_log_callback(None)
            set_log_level(original_level)
    
    def test_callback_invoked_on_log_error(self):
        """Test callback is invoked for log_error()."""
        captured_logs = []
        
        def test_callback(level: LogLevel, message: str):
            captured_logs.append((level, message))
        
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Error)
            set_log_callback(test_callback)
            
            log_error("Test error callback")
            
            assert len(captured_logs) >= 1
            found = any(msg == "Test error callback" for level, msg in captured_logs)
            assert found
        finally:
            set_log_callback(None)
            set_log_level(original_level)
    
    def test_callback_invoked_on_log_critical(self):
        """Test callback is invoked for log_critical()."""
        captured_logs = []
        
        def test_callback(level: LogLevel, message: str):
            captured_logs.append((level, message))
        
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Critical)
            set_log_callback(test_callback)
            
            log_critical("Test critical callback")
            
            assert len(captured_logs) >= 1
            found = any(msg == "Test critical callback" for level, msg in captured_logs)
            assert found
        finally:
            set_log_callback(None)
            set_log_level(original_level)
    
    def test_callback_receives_correct_level(self):
        """Test callback receives correct LogLevel."""
        captured_logs = []
        
        def test_callback(level: LogLevel, message: str):
            captured_logs.append((level, message))
        
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Debug)
            set_log_callback(test_callback)
            
            log_debug("Debug level test")
            log_info("Info level test")
            log_warning("Warning level test")
            
            # Check captured levels
            for level, message in captured_logs:
                assert isinstance(level, LogLevel)
                
                if message == "Debug level test":
                    assert level == LogLevel.Debug
                elif message == "Info level test":
                    assert level == LogLevel.Info
                elif message == "Warning level test":
                    assert level == LogLevel.Warning
        finally:
            set_log_callback(None)
            set_log_level(original_level)
    
    def test_callback_receives_full_message(self):
        """Test callback receives complete message."""
        captured_logs = []
        
        def test_callback(level: LogLevel, message: str):
            captured_logs.append((level, message))
        
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Info)
            set_log_callback(test_callback)
            
            test_message = "This is a complete test message"
            log_info(test_message)
            
            found = any(msg == test_message for level, msg in captured_logs)
            assert found
        finally:
            set_log_callback(None)
            set_log_level(original_level)


class TestLogCallbackFiltering:
    """Test log level filtering with callbacks."""
    
    def test_callback_filters_by_log_level(self):
        """Test callback only receives messages at or above set level."""
        captured_logs = []
        
        def test_callback(level: LogLevel, message: str):
            captured_logs.append((level, message))
        
        original_level = get_log_level()
        
        try:
            # Set level to Warning - should filter out Debug and Info
            set_log_level(LogLevel.Warning)
            set_log_callback(test_callback)
            
            log_debug("Should be filtered")
            log_info("Should be filtered")
            log_warning("Should appear")
            log_error("Should appear")
            
            # Only Warning and Error should be captured
            messages = [msg for level, msg in captured_logs]
            
            assert "Should be filtered" not in messages
            assert "Should appear" in messages
        finally:
            set_log_callback(None)
            set_log_level(original_level)
    
    def test_callback_all_levels_with_debug(self):
        """Test callback receives all levels when set to Debug."""
        captured_logs = []
        
        def test_callback(level: LogLevel, message: str):
            captured_logs.append((level, message))
        
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Debug)
            set_log_callback(test_callback)
            
            log_debug("Debug msg")
            log_info("Info msg")
            log_warning("Warning msg")
            log_error("Error msg")
            log_critical("Critical msg")
            
            # All should be captured
            messages = [msg for level, msg in captured_logs]
            
            assert "Debug msg" in messages
            assert "Info msg" in messages
            assert "Warning msg" in messages
            assert "Error msg" in messages
            assert "Critical msg" in messages
        finally:
            set_log_callback(None)
            set_log_level(original_level)
    
    def test_callback_only_critical_with_critical_level(self):
        """Test callback only receives Critical when level is Critical."""
        captured_logs = []
        
        def test_callback(level: LogLevel, message: str):
            captured_logs.append((level, message))
        
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Critical)
            set_log_callback(test_callback)
            
            log_debug("Should be filtered")
            log_info("Should be filtered")
            log_warning("Should be filtered")
            log_error("Should be filtered")
            log_critical("Should appear")
            
            messages = [msg for level, msg in captured_logs]
            
            assert "Should be filtered" not in messages
            assert "Should appear" in messages
        finally:
            set_log_callback(None)
            set_log_level(original_level)


class TestLogCallbackEdgeCases:
    """Test edge cases with log callbacks."""
    
    def test_callback_with_exception_doesnt_crash(self):
        """Test callback that raises exception doesn't crash library."""
        def bad_callback(level: LogLevel, message: str):
            raise RuntimeError("Callback error")
        
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Info)
            set_log_callback(bad_callback)
            
            # Should not crash even if callback raises
            log_info("Test message")
        finally:
            set_log_callback(None)
            set_log_level(original_level)
    
    def test_callback_replaced(self):
        """Test replacing callback with new one."""
        first_captured = []
        second_captured = []
        
        def first_callback(level: LogLevel, message: str):
            first_captured.append((level, message))
        
        def second_callback(level: LogLevel, message: str):
            second_captured.append((level, message))
        
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Info)
            
            # Register first callback
            set_log_callback(first_callback)
            log_info("First callback message")
            
            # Replace with second callback
            set_log_callback(second_callback)
            log_info("Second callback message")
            
            # First callback should have first message only
            messages_first = [msg for level, msg in first_captured]
            assert "First callback message" in messages_first
            assert "Second callback message" not in messages_first
            
            # Second callback should have second message only
            messages_second = [msg for level, msg in second_captured]
            assert "Second callback message" in messages_second
            assert "First callback message" not in messages_second
        finally:
            set_log_callback(None)
            set_log_level(original_level)
    
    def test_multiple_log_calls_multiple_invocations(self):
        """Test multiple log calls result in multiple callback invocations."""
        captured_logs = []
        
        def test_callback(level: LogLevel, message: str):
            captured_logs.append((level, message))
        
        original_level = get_log_level()
        
        try:
            set_log_level(LogLevel.Info)
            set_log_callback(test_callback)
            
            log_info("Message 1")
            log_info("Message 2")
            log_info("Message 3")
            
            messages = [msg for level, msg in captured_logs]
            
            # All three messages should be captured
            assert "Message 1" in messages
            assert "Message 2" in messages
            assert "Message 3" in messages
        finally:
            set_log_callback(None)
            set_log_level(original_level)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
