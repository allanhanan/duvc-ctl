"""
Test Suite 15: Error Handling
==============================

Tests exception hierarchy, error decoding, and error handling mechanisms.

Exception Hierarchy Tested (8):
  - DuvcError (base exception)
  - DeviceNotFoundError
  - DeviceBusyError
  - PropertyNotSupportedError
  - InvalidValueError
  - PermissionDeniedError
  - SystemError
  - InvalidArgumentError
  - NotImplementedError

Total: 9 exception types + 4 specialized exceptions + error decoding

Test Organization:
  1. Exception Class Tests - Structure and hierarchy
  2. Exception Instantiation Tests - Creation and attributes
  3. Error Code Mapping Tests - ErrorCode to exception mapping
  4. Specialized Exception Tests - Custom exception types
  5. Exception String Tests - __str__ and __repr__

Run: pytest tests/test_15_error_handling.py -v
"""

import pytest
import sys
from typing import List

import duvc_ctl
from duvc_ctl import (
    # Base exception
    DuvcError, DuvcErrorCode,
    # Core exceptions
    DeviceNotFoundError, DeviceBusyError,
    PropertyNotSupportedError, InvalidValueError,
    PermissionDeniedError, SystemError,
    InvalidArgumentError, NotImplementedError,
    # Exception utilities
    ERROR_CODE_TO_EXCEPTION, create_exception_from_error_code,
    # Specialized exceptions
    PropertyValueOutOfRangeError, PropertyModeNotSupportedError,
    BulkOperationError, ConnectionHealthError,
    # Core enums
    ErrorCode,
)


# ============================================================================
# EXCEPTION CLASS TESTS - Structure and hierarchy
# ============================================================================

class TestExceptionHierarchy:
    """Test exception class hierarchy structure."""
    
    def test_duvc_error_is_exception(self):
        """Test DuvcError inherits from Exception."""
        assert issubclass(DuvcError, Exception)
    
    def test_device_not_found_error_inherits_duvc_error(self):
        """Test DeviceNotFoundError inherits from DuvcError."""
        assert issubclass(DeviceNotFoundError, DuvcError)
        assert issubclass(DeviceNotFoundError, Exception)
    
    def test_device_busy_error_inherits_duvc_error(self):
        """Test DeviceBusyError inherits from DuvcError."""
        assert issubclass(DeviceBusyError, DuvcError)
        assert issubclass(DeviceBusyError, Exception)
    
    def test_property_not_supported_error_inherits_duvc_error(self):
        """Test PropertyNotSupportedError inherits from DuvcError."""
        assert issubclass(PropertyNotSupportedError, DuvcError)
        assert issubclass(PropertyNotSupportedError, Exception)
    
    def test_invalid_value_error_inherits_duvc_error(self):
        """Test InvalidValueError inherits from DuvcError."""
        assert issubclass(InvalidValueError, DuvcError)
        assert issubclass(InvalidValueError, Exception)
    
    def test_permission_denied_error_inherits_duvc_error(self):
        """Test PermissionDeniedError inherits from DuvcError."""
        assert issubclass(PermissionDeniedError, DuvcError)
        assert issubclass(PermissionDeniedError, Exception)
    
    def test_system_error_inherits_duvc_error(self):
        """Test SystemError inherits from DuvcError."""
        assert issubclass(SystemError, DuvcError)
        assert issubclass(SystemError, Exception)
    
    def test_invalid_argument_error_inherits_duvc_error(self):
        """Test InvalidArgumentError inherits from DuvcError."""
        assert issubclass(InvalidArgumentError, DuvcError)
        assert issubclass(InvalidArgumentError, Exception)
    
    def test_not_implemented_error_inherits_duvc_error(self):
        """Test NotImplementedError inherits from DuvcError."""
        assert issubclass(NotImplementedError, DuvcError)
        assert issubclass(NotImplementedError, Exception)
    
    def test_all_exceptions_catchable_as_duvc_error(self):
        """Test all duvc-ctl exceptions can be caught as DuvcError."""
        exceptions_to_test = [
            DeviceNotFoundError,
            DeviceBusyError,
            PropertyNotSupportedError,
            InvalidValueError,
            PermissionDeniedError,
            SystemError,
            InvalidArgumentError,
            NotImplementedError,
        ]
        
        for exc_class in exceptions_to_test:
            try:
                raise exc_class("Test exception")
            except DuvcError:
                pass  # Should be caught
            except Exception:
                pytest.fail(f"{exc_class.__name__} not catchable as DuvcError")


class TestExceptionInstantiation:
    """Test exception instantiation and attributes."""
    
    def test_duvc_error_basic_instantiation(self):
        """Test DuvcError can be instantiated with message."""
        error = DuvcError("Test error message")
        
        assert isinstance(error, DuvcError)
        assert str(error) == "Test error message"
    
    def test_duvc_error_with_error_code(self):
        """Test DuvcError can include error code."""
        error = DuvcError("Test error", error_code=DuvcErrorCode.DEVICE_NOT_FOUND)
        
        assert error.error_code == DuvcErrorCode.DEVICE_NOT_FOUND
        assert "DEVICE_NOT_FOUND" in str(error)
    
    def test_duvc_error_with_context(self):
        """Test DuvcError can include context information."""
        error = DuvcError("Test error", context="Additional context")
        
        assert error.context == "Additional context"
        assert "Additional context" in str(error)
    
    def test_device_not_found_error_instantiation(self):
        """Test DeviceNotFoundError instantiation."""
        error = DeviceNotFoundError("Device not found")
        
        assert isinstance(error, DeviceNotFoundError)
        assert isinstance(error, DuvcError)
        assert "not found" in str(error).lower()
    
    def test_device_busy_error_instantiation(self):
        """Test DeviceBusyError instantiation."""
        error = DeviceBusyError("Device is busy")
        
        assert isinstance(error, DeviceBusyError)
        assert "busy" in str(error).lower()
    
    def test_property_not_supported_error_instantiation(self):
        """Test PropertyNotSupportedError instantiation."""
        error = PropertyNotSupportedError("Property not supported")
        
        assert isinstance(error, PropertyNotSupportedError)
        assert "not supported" in str(error).lower()
    
    def test_invalid_value_error_instantiation(self):
        """Test InvalidValueError instantiation."""
        error = InvalidValueError("Invalid value")
        
        assert isinstance(error, InvalidValueError)
        assert "invalid" in str(error).lower()
    
    def test_permission_denied_error_instantiation(self):
        """Test PermissionDeniedError instantiation."""
        error = PermissionDeniedError("Permission denied")
        
        assert isinstance(error, PermissionDeniedError)
        assert "permission" in str(error).lower()
    
    def test_system_error_instantiation(self):
        """Test SystemError instantiation."""
        error = SystemError("System error occurred")
        
        assert isinstance(error, SystemError)
        assert "system" in str(error).lower() or "error" in str(error).lower()
    
    def test_invalid_argument_error_instantiation(self):
        """Test InvalidArgumentError instantiation."""
        error = InvalidArgumentError("Invalid argument")
        
        assert isinstance(error, InvalidArgumentError)
        assert "invalid" in str(error).lower() or "argument" in str(error).lower()
    
    def test_not_implemented_error_instantiation(self):
        """Test NotImplementedError instantiation."""
        error = NotImplementedError("Not implemented")
        
        assert isinstance(error, NotImplementedError)
        assert "not implemented" in str(error).lower()


class TestErrorCodeEnum:
    """Test DuvcErrorCode enum."""
    
    def test_duvc_error_code_exists(self):
        """Test DuvcErrorCode enum exists."""
        assert hasattr(duvc_ctl, 'DuvcErrorCode')
    
    def test_duvc_error_code_values(self):
        """Test DuvcErrorCode has all expected values."""
        expected_codes = [
            'SUCCESS',
            'DEVICE_NOT_FOUND',
            'DEVICE_BUSY',
            'PROPERTY_NOT_SUPPORTED',
            'INVALID_VALUE',
            'PERMISSION_DENIED',
            'SYSTEM_ERROR',
            'INVALID_ARGUMENT',
            'NOT_IMPLEMENTED',
        ]
        
        for code_name in expected_codes:
            assert hasattr(DuvcErrorCode, code_name), \
                   f"DuvcErrorCode missing {code_name}"
    
    def test_duvc_error_code_is_int_enum(self):
        """Test DuvcErrorCode values are integers."""
        assert isinstance(DuvcErrorCode.SUCCESS, int)
        assert isinstance(DuvcErrorCode.DEVICE_NOT_FOUND, int)
        assert isinstance(DuvcErrorCode.INVALID_VALUE, int)
    
    def test_duvc_error_code_success_is_zero(self):
        """Test DuvcErrorCode.SUCCESS is 0."""
        assert DuvcErrorCode.SUCCESS == 0
    
    def test_duvc_error_code_unique_values(self):
        """Test DuvcErrorCode values are unique."""
        codes = [
            DuvcErrorCode.SUCCESS,
            DuvcErrorCode.DEVICE_NOT_FOUND,
            DuvcErrorCode.DEVICE_BUSY,
            DuvcErrorCode.PROPERTY_NOT_SUPPORTED,
            DuvcErrorCode.INVALID_VALUE,
            DuvcErrorCode.PERMISSION_DENIED,
            DuvcErrorCode.SYSTEM_ERROR,
            DuvcErrorCode.INVALID_ARGUMENT,
            DuvcErrorCode.NOT_IMPLEMENTED,
        ]
        
        assert len(codes) == len(set(codes)), "DuvcErrorCode values not unique"


class TestErrorCodeMapping:
    """Test ERROR_CODE_TO_EXCEPTION mapping."""
    
    def test_error_code_to_exception_exists(self):
        """Test ERROR_CODE_TO_EXCEPTION dict exists."""
        assert hasattr(duvc_ctl, 'ERROR_CODE_TO_EXCEPTION')
        assert isinstance(ERROR_CODE_TO_EXCEPTION, dict)
    
    def test_error_code_to_exception_device_not_found(self):
        """Test mapping for DEVICE_NOT_FOUND."""
        exc_class = ERROR_CODE_TO_EXCEPTION.get(DuvcErrorCode.DEVICE_NOT_FOUND)
        
        assert exc_class == DeviceNotFoundError
    
    def test_error_code_to_exception_device_busy(self):
        """Test mapping for DEVICE_BUSY."""
        exc_class = ERROR_CODE_TO_EXCEPTION.get(DuvcErrorCode.DEVICE_BUSY)
        
        assert exc_class == DeviceBusyError
    
    def test_error_code_to_exception_property_not_supported(self):
        """Test mapping for PROPERTY_NOT_SUPPORTED."""
        exc_class = ERROR_CODE_TO_EXCEPTION.get(DuvcErrorCode.PROPERTY_NOT_SUPPORTED)
        
        assert exc_class == PropertyNotSupportedError
    
    def test_error_code_to_exception_invalid_value(self):
        """Test mapping for INVALID_VALUE."""
        exc_class = ERROR_CODE_TO_EXCEPTION.get(DuvcErrorCode.INVALID_VALUE)
        
        assert exc_class == InvalidValueError
    
    def test_error_code_to_exception_permission_denied(self):
        """Test mapping for PERMISSION_DENIED."""
        exc_class = ERROR_CODE_TO_EXCEPTION.get(DuvcErrorCode.PERMISSION_DENIED)
        
        assert exc_class == PermissionDeniedError
    
    def test_error_code_to_exception_system_error(self):
        """Test mapping for SYSTEM_ERROR."""
        exc_class = ERROR_CODE_TO_EXCEPTION.get(DuvcErrorCode.SYSTEM_ERROR)
        
        assert exc_class == SystemError
    
    def test_error_code_to_exception_invalid_argument(self):
        """Test mapping for INVALID_ARGUMENT."""
        exc_class = ERROR_CODE_TO_EXCEPTION.get(DuvcErrorCode.INVALID_ARGUMENT)
        
        assert exc_class == InvalidArgumentError
    
    def test_error_code_to_exception_not_implemented(self):
        """Test mapping for NOT_IMPLEMENTED."""
        exc_class = ERROR_CODE_TO_EXCEPTION.get(DuvcErrorCode.NOT_IMPLEMENTED)
        
        assert exc_class == NotImplementedError
    
    def test_error_code_to_exception_complete_mapping(self):
        """Test all error codes (except SUCCESS) are mapped."""
        # SUCCESS shouldn't be in the mapping (it's not an error)
        expected_count = 8  # All error codes except SUCCESS
        
        assert len(ERROR_CODE_TO_EXCEPTION) == expected_count


class TestCreateExceptionFromErrorCode:
    """Test create_exception_from_error_code() function."""
    
    def test_create_exception_from_error_code_exists(self):
        """Test create_exception_from_error_code() exists."""
        assert hasattr(duvc_ctl, 'create_exception_from_error_code')
        assert callable(create_exception_from_error_code)
    
    def test_create_exception_device_not_found(self):
        """Test creating DeviceNotFoundError."""
        error = create_exception_from_error_code(
            DuvcErrorCode.DEVICE_NOT_FOUND,
            "Device not found"
        )
        
        assert isinstance(error, DeviceNotFoundError)
        assert "not found" in str(error).lower()
    
    def test_create_exception_device_busy(self):
        """Test creating DeviceBusyError."""
        error = create_exception_from_error_code(
            DuvcErrorCode.DEVICE_BUSY,
            "Device busy"
        )
        
        assert isinstance(error, DeviceBusyError)
    
    def test_create_exception_with_context(self):
        """Test creating exception with context."""
        error = create_exception_from_error_code(
            DuvcErrorCode.INVALID_VALUE,
            "Invalid value",
            context="Property: brightness"
        )
        
        assert isinstance(error, InvalidValueError)
        assert error.context == "Property: brightness"
    
    def test_create_exception_unknown_code(self):
        """Test creating exception with unknown error code."""
        error = create_exception_from_error_code(
            9999,  # Unknown code
            "Unknown error"
        )
        
        # Should return base DuvcError for unknown codes
        assert isinstance(error, DuvcError)


# ============================================================================
# SPECIALIZED EXCEPTION TESTS
# ============================================================================

class TestPropertyValueOutOfRangeError:
    """Test PropertyValueOutOfRangeError specialized exception."""
    
    def test_property_value_out_of_range_error_exists(self):
        """Test PropertyValueOutOfRangeError class exists."""
        assert hasattr(duvc_ctl, 'PropertyValueOutOfRangeError')
    
    def test_property_value_out_of_range_error_inherits(self):
        """Test PropertyValueOutOfRangeError inherits from InvalidValueError."""
        assert issubclass(PropertyValueOutOfRangeError, InvalidValueError)
        assert issubclass(PropertyValueOutOfRangeError, DuvcError)
    
    def test_property_value_out_of_range_error_instantiation(self):
        """Test PropertyValueOutOfRangeError instantiation."""
        error = PropertyValueOutOfRangeError(
            property_name="brightness",
            value=300,
            min_val=0,
            max_val=255
        )
        
        assert error.property_name == "brightness"
        assert error.value == 300
        assert error.min_val == 0
        assert error.max_val == 255
        assert "brightness" in str(error)
        assert "300" in str(error)
    
    def test_property_value_out_of_range_error_with_current(self):
        """Test PropertyValueOutOfRangeError with current value."""
        error = PropertyValueOutOfRangeError(
            property_name="contrast",
            value=150,
            min_val=0,
            max_val=100,
            current_val=50
        )
        
        assert error.current_val == 50
        assert "50" in str(error) or "current" in str(error).lower()
    
    def test_property_value_out_of_range_error_with_step(self):
        """Test PropertyValueOutOfRangeError with step information."""
        error = PropertyValueOutOfRangeError(
            property_name="zoom",
            value=105,
            min_val=0,
            max_val=200,
            step=10
        )
        
        assert error.step == 10


class TestPropertyModeNotSupportedError:
    """Test PropertyModeNotSupportedError specialized exception."""
    
    def test_property_mode_not_supported_error_exists(self):
        """Test PropertyModeNotSupportedError class exists."""
        assert hasattr(duvc_ctl, 'PropertyModeNotSupportedError')
    
    def test_property_mode_not_supported_error_inherits(self):
        """Test PropertyModeNotSupportedError inherits from PropertyNotSupportedError."""
        assert issubclass(PropertyModeNotSupportedError, PropertyNotSupportedError)
        assert issubclass(PropertyModeNotSupportedError, DuvcError)
    
    def test_property_mode_not_supported_error_instantiation(self):
        """Test PropertyModeNotSupportedError instantiation."""
        error = PropertyModeNotSupportedError(
            property_name="exposure",
            mode="auto"
        )
        
        assert error.property_name == "exposure"
        assert error.mode == "auto"
        assert "exposure" in str(error)
        assert "auto" in str(error)
    
    def test_property_mode_not_supported_error_with_supported_modes(self):
        """Test PropertyModeNotSupportedError with supported modes list."""
        error = PropertyModeNotSupportedError(
            property_name="focus",
            mode="continuous",
            supported_modes=["manual", "auto"]
        )
        
        assert error.supported_modes == ["manual", "auto"]
        assert "manual" in str(error) or "auto" in str(error)


class TestBulkOperationError:
    """Test BulkOperationError specialized exception."""
    
    def test_bulk_operation_error_exists(self):
        """Test BulkOperationError class exists."""
        assert hasattr(duvc_ctl, 'BulkOperationError')
    
    def test_bulk_operation_error_inherits(self):
        """Test BulkOperationError inherits from DuvcError."""
        assert issubclass(BulkOperationError, DuvcError)
    
    def test_bulk_operation_error_instantiation(self):
        """Test BulkOperationError instantiation."""
        failed_props = {
            "brightness": "Out of range",
            "contrast": "Not supported"
        }
        
        error = BulkOperationError(
            operation="set_multiple",
            failed_properties=failed_props,
            successful_count=3,
            total_count=5
        )
        
        assert error.operation == "set_multiple"
        assert error.failed_properties == failed_props
        assert error.successful_count == 3
        assert error.total_count == 5
        assert "3/5" in str(error) or "3" in str(error)
    
    def test_bulk_operation_error_get_recovery_suggestions(self):
        """Test BulkOperationError.get_recovery_suggestions()."""
        failed_props = {
            "zoom": "Property not supported",
            "brightness": "Value out of range"
        }
        
        error = BulkOperationError(
            operation="set_multiple",
            failed_properties=failed_props,
            successful_count=1,
            total_count=3
        )
        
        suggestions = error.get_recovery_suggestions()
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0


class TestConnectionHealthError:
    """Test ConnectionHealthError specialized exception."""
    
    def test_connection_health_error_exists(self):
        """Test ConnectionHealthError class exists."""
        assert hasattr(duvc_ctl, 'ConnectionHealthError')
    
    def test_connection_health_error_inherits(self):
        """Test ConnectionHealthError inherits from DuvcError."""
        assert issubclass(ConnectionHealthError, DuvcError)
    
    def test_connection_health_error_instantiation(self):
        """Test ConnectionHealthError instantiation."""
        health_issues = [
            "Connection timeout",
            "Property read failure"
        ]
        
        error = ConnectionHealthError(
            device_name="USB Camera",
            health_issues=health_issues
        )
        
        assert error.device_name == "USB Camera"
        assert error.health_issues == health_issues
        assert "USB Camera" in str(error)
    
    def test_connection_health_error_with_last_working_operation(self):
        """Test ConnectionHealthError with last working operation."""
        error = ConnectionHealthError(
            device_name="Test Camera",
            health_issues=["Timeout"],
            last_working_operation="get_brightness"
        )
        
        assert error.last_working_operation == "get_brightness"
        assert "get_brightness" in str(error)
    
    def test_connection_health_error_get_recovery_suggestions(self):
        """Test ConnectionHealthError.get_recovery_suggestions()."""
        error = ConnectionHealthError(
            device_name="Test Camera",
            health_issues=["Connection timeout", "Property read failure"]
        )
        
        suggestions = error.get_recovery_suggestions()
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0


# ============================================================================
# EXCEPTION STRING REPRESENTATION TESTS
# ============================================================================

class TestExceptionStringRepresentations:
    """Test exception __str__ and __repr__ methods."""
    
    def test_duvc_error_str(self):
        """Test DuvcError.__str__()."""
        error = DuvcError("Test message")
        
        result = str(error)
        
        assert isinstance(result, str)
        assert "Test message" in result
    
    def test_duvc_error_repr(self):
        """Test DuvcError.__repr__()."""
        error = DuvcError("Test message")
        
        result = repr(error)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_device_not_found_error_str(self):
        """Test DeviceNotFoundError.__str__()."""
        error = DeviceNotFoundError("Device not found")
        
        result = str(error)
        
        assert "not found" in result.lower()
    
    def test_property_not_supported_error_str(self):
        """Test PropertyNotSupportedError.__str__()."""
        error = PropertyNotSupportedError("Property not supported")
        
        result = str(error)
        
        assert "not supported" in result.lower()
    
    def test_exception_str_includes_error_code(self):
        """Test exception string includes error code when present."""
        error = DuvcError(
            "Test error",
            error_code=DuvcErrorCode.DEVICE_NOT_FOUND
        )
        
        result = str(error)
        
        assert "DEVICE_NOT_FOUND" in result or "device" in result.lower()
    
    def test_exception_str_includes_context(self):
        """Test exception string includes context when present."""
        error = DuvcError(
            "Test error",
            context="Additional info"
        )
        
        result = str(error)
        
        assert "Additional info" in result or "context" in result.lower()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
