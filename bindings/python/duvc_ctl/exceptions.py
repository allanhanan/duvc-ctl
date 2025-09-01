"""
Custom exception classes for duvc-ctl.

This module provides Python-specific exception classes that map to 
the C++ error codes for better Pythonic error handling.
"""

from typing import Optional
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

__all__ = [
    'DuvcError', 'DuvcErrorCode',
    'DeviceNotFoundError', 'DeviceBusyError', 'PropertyNotSupportedError',
    'InvalidValueError', 'PermissionDeniedError', 'SystemError',
    'InvalidArgumentError', 'NotImplementedError',
    'ERROR_CODE_TO_EXCEPTION', 'create_exception_from_error_code'
]
