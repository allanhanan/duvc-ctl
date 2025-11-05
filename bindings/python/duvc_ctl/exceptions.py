"""
Custom exception classes for duvc-ctl.

This module provides Python-specific exception classes that map to 
the C++ error codes for better Pythonic error handling.
"""

from typing import Optional, List, Dict
from enum import IntEnum

class DuvcErrorCode(IntEnum):
    """Error codes matching the C++ ErrorCode enum."""
    SUCCESS = 0
    DEVICE_NOT_FOUND = 1
    DEVICE_BUSY = 2
    PROPERTY_NOT_SUPPORTED = 3
    INVALID_VALUE = 4
    PERMISSION_DENIED = 5
    SYSTEM_ERROR = 6
    INVALID_ARGUMENT = 7
    NOT_IMPLEMENTED = 8

class DuvcError(Exception):
    """
    Base exception class for all duvc-ctl errors.
    
    This exception includes the error code and provides additional
    context for troubleshooting.
    """
    
    def __init__(self, message: str, error_code: Optional[DuvcErrorCode] = None, 
                 context: Optional[str] = None):
        self.error_code = error_code
        self.context = context
        super().__init__(message)
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.error_code is not None:
            base_msg = f"[{self.error_code.name}] {base_msg}"
        if self.context:
            base_msg += f" (Context: {self.context})"
        return base_msg

class DeviceNotFoundError(DuvcError):
    """
    Raised when a camera device is not found or has been disconnected.
    
    This typically indicates:
    - The device is not physically connected
    - The device is not recognized by the system
    - Driver issues
    """
    
    def __init__(self, message: str = "Camera device not found or disconnected", 
                 context: Optional[str] = None):
        super().__init__(message, DuvcErrorCode.DEVICE_NOT_FOUND, context)

class DeviceBusyError(DuvcError):
    """
    Raised when a camera device is busy or in use by another application.
    
    This typically indicates:
    - Another application is using the camera
    - The device is locked by another process
    - Previous connections were not properly closed
    """
    
    def __init__(self, message: str = "Camera device is busy or in use", 
                 context: Optional[str] = None):
        super().__init__(message, DuvcErrorCode.DEVICE_BUSY, context)

class PropertyNotSupportedError(DuvcError):
    """
    Raised when trying to access a property that is not supported by the device.
    
    This typically indicates:
    - The camera doesn't support the requested feature
    - The property is not available in the current mode
    - Driver limitations
    """
    
    def __init__(self, message: str = "Property not supported by device", 
                 context: Optional[str] = None):
        super().__init__(message, DuvcErrorCode.PROPERTY_NOT_SUPPORTED, context)

class InvalidValueError(DuvcError):
    """
    Raised when trying to set a property to an invalid value.
    
    This typically indicates:
    - Value is outside the supported range
    - Value is not aligned with the step size
    - Value type is incorrect
    """
    
    def __init__(self, message: str = "Property value is out of range or invalid", 
                 context: Optional[str] = None):
        super().__init__(message, DuvcErrorCode.INVALID_VALUE, context)

class PermissionDeniedError(DuvcError):
    """
    Raised when there are insufficient permissions to access the device.
    
    This typically indicates:
    - Camera privacy settings are blocking access
    - Application doesn't have required privileges
    - System security policies are preventing access
    """
    
    def __init__(self, message: str = "Insufficient permissions to access device", 
                 context: Optional[str] = None):
        super().__init__(message, DuvcErrorCode.PERMISSION_DENIED, context)

class SystemError(DuvcError):
    """
    Raised when a system or platform-specific error occurs.
    
    This typically indicates:
    - DirectShow/COM errors
    - Driver issues
    - System resource problems
    """
    
    def __init__(self, message: str = "System or platform error occurred", 
                 context: Optional[str] = None):
        super().__init__(message, DuvcErrorCode.SYSTEM_ERROR, context)

class InvalidArgumentError(DuvcError):
    """
    Raised when an invalid argument is passed to a function.
    
    This typically indicates:
    - Null pointer or invalid object
    - Invalid enum value
    - Programming error
    """
    
    def __init__(self, message: str = "Invalid function argument provided", 
                 context: Optional[str] = None):
        super().__init__(message, DuvcErrorCode.INVALID_ARGUMENT, context)

class NotImplementedError(DuvcError):
    """
    Raised when a feature is not implemented on the current platform.
    
    This typically indicates:
    - Feature is Windows-only but running on another platform
    - Functionality not yet implemented
    - Platform-specific limitations
    """
    
    def __init__(self, message: str = "Feature not implemented on this platform", 
                 context: Optional[str] = None):
        super().__init__(message, DuvcErrorCode.NOT_IMPLEMENTED, context)

# Mapping from C++ error codes to Python exceptions
ERROR_CODE_TO_EXCEPTION = {
    DuvcErrorCode.DEVICE_NOT_FOUND: DeviceNotFoundError,
    DuvcErrorCode.DEVICE_BUSY: DeviceBusyError,
    DuvcErrorCode.PROPERTY_NOT_SUPPORTED: PropertyNotSupportedError,
    DuvcErrorCode.INVALID_VALUE: InvalidValueError,
    DuvcErrorCode.PERMISSION_DENIED: PermissionDeniedError,
    DuvcErrorCode.SYSTEM_ERROR: SystemError,
    DuvcErrorCode.INVALID_ARGUMENT: InvalidArgumentError,
    DuvcErrorCode.NOT_IMPLEMENTED: NotImplementedError,
}

def create_exception_from_error_code(error_code: int, message: str, 
                                   context: Optional[str] = None) -> DuvcError:
    """
    Create an appropriate exception instance based on the error code.
    
    Args:
        error_code: The error code from the C++ library
        message: Error message
        context: Additional context information
        
    Returns:
        Appropriate exception instance
    """
    try:
        code_enum = DuvcErrorCode(error_code)
        exception_class = ERROR_CODE_TO_EXCEPTION.get(code_enum, DuvcError)
        return exception_class(message, context)
    except ValueError:
        # Unknown error code
        return DuvcError(f"Unknown error code {error_code}: {message}", None, context)
    
# ========================================================================
# PROPERTY-SPECIFIC EXCEPTIONS (Enhanced Error Context)
# ========================================================================

class PropertyValueOutOfRangeError(InvalidValueError):
    """Raised when a property value is outside the valid range.
    
    This is a specialized InvalidValueError that includes range information
    and suggested values for better user experience.
    """
    
    def __init__(self, property_name: str, value: int, min_val: int, max_val: int, 
                 current_val: Optional[int] = None, step: Optional[int] = None):
        self.property_name = property_name
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.current_val = current_val
        self.step = step
        
        # Create detailed error message
        message = f"Value {value} is out of range for '{property_name}'. Valid range: {min_val} to {max_val}"
        
        if step and step > 1:
            message += f" (step: {step})"
        
        if current_val is not None:
            message += f". Current value: {current_val}"
            
        # Add recovery suggestions
        suggested_value = max(min_val, min(max_val, value))
        if suggested_value != value:
            message += f". Try: {suggested_value}"
        
        super().__init__(message, context=f"Property: {property_name}, Range: [{min_val}, {max_val}]")


class PropertyModeNotSupportedError(PropertyNotSupportedError):
    """Raised when a property mode (auto/manual) is not supported.
    
    This helps distinguish between unsupported properties and unsupported modes.
    """
    
    def __init__(self, property_name: str, mode: str, supported_modes: Optional[List[str]] = None):
        self.property_name = property_name
        self.mode = mode
        self.supported_modes = supported_modes or []
        
        message = f"Mode '{mode}' not supported for property '{property_name}'"
        
        if supported_modes:
            message += f". Supported modes: {', '.join(supported_modes)}"
        else:
            message += ". Try 'manual' or 'auto'"
            
        super().__init__(message, context=f"Property: {property_name}, Mode: {mode}")


class BulkOperationError(DuvcError):
    """Raised when bulk property operations partially fail.
    
    Contains information about which properties succeeded/failed.
    """
    
    def __init__(self, operation: str, failed_properties: Dict[str, str], 
                 successful_count: int, total_count: int):
        self.operation = operation
        self.failed_properties = failed_properties
        self.successful_count = successful_count
        self.total_count = total_count
        
        message = f"{operation} partially failed: {successful_count}/{total_count} properties successful"
        
        if failed_properties:
            failed_list = [f"{prop}: {error}" for prop, error in failed_properties.items()]
            message += f". Failed: {', '.join(failed_list)}"
            
        super().__init__(message, context=f"Operation: {operation}")
        
    def get_recovery_suggestions(self) -> List[str]:
        """Get specific recovery suggestions based on failure types."""
        suggestions = []
        
        for prop, error in self.failed_properties.items():
            if "not supported" in error.lower():
                suggestions.append(f"Property '{prop}' not supported by this camera model")
            elif "out of range" in error.lower():
                suggestions.append(f"Check valid range for '{prop}' using get_property_range()")
            elif "busy" in error.lower():
                suggestions.append(f"Property '{prop}' may be locked by another application")
                
        if not suggestions:
            suggestions.append("Check camera connection and try individual property operations")
            
        return suggestions


class ConnectionHealthError(DuvcError):
    """Raised when connection health checks fail.
    
    Provides detailed diagnostics and recovery suggestions.
    """
    
    def __init__(self, device_name: str, health_issues: List[str], 
                 last_working_operation: Optional[str] = None):
        self.device_name = device_name
        self.health_issues = health_issues
        self.last_working_operation = last_working_operation
        
        message = f"Camera '{device_name}' connection health check failed"
        
        if health_issues:
            message += f": {', '.join(health_issues)}"
            
        if last_working_operation:
            message += f". Last working operation: {last_working_operation}"
            
        super().__init__(message, context=f"Device: {device_name}")
        
    def get_recovery_suggestions(self) -> List[str]:
        """Get specific recovery suggestions based on health issues."""
        suggestions = []
        
        for issue in self.health_issues:
            if "timeout" in issue.lower():
                suggestions.append("Try reconnecting to the camera")
            elif "property" in issue.lower():
                suggestions.append("Camera may be in a locked state - try reset_to_defaults()")
            elif "response" in issue.lower():
                suggestions.append("Check if camera is being used by another application")
                
        suggestions.append(f"Try: cam.reconnect() or restart the camera application")
        
        return suggestions



__all__ = [
    'DuvcError', 'DuvcErrorCode',
    'DeviceNotFoundError', 'DeviceBusyError', 'PropertyNotSupportedError',
    'InvalidValueError', 'PermissionDeniedError', 'SystemError',
    'InvalidArgumentError', 'NotImplementedError',
    'ERROR_CODE_TO_EXCEPTION', 'create_exception_from_error_code',
    'PropertyValueOutOfRangeError', 'PropertyModeNotSupportedError',
    'BulkOperationError', 'ConnectionHealthError'
]
