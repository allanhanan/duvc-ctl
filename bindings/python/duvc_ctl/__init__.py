"""
duvc-ctl - DirectShow UVC Camera Control Library

Windows-only library for USB Video Class camera control via DirectShow.

Two APIs available:
1. CameraController (Pythonic) - Simple property-based access with exceptions
2. Result-Based API (open_camera) - Explicit error handling with Result<T> types

Both APIs use the same underlying C++ bindings but differ in error strategy.
"""



from __future__ import annotations

import sys
import warnings
import uuid as _uuid
from typing import List, Optional, Dict, Any, Union, Tuple, Callable, TypedDict, Literal

# =============================================================================
# MODULE METADATA
# =============================================================================

__version__ = "2.0.0"
__author__ = "allanhanan"
__email__ = "allan.hanan04@gmail.com"
__license__ = "MIT"
__project__ = "duvc-ctl"

__all__ = []

# =============================================================================
# C++ BINDINGS IMPORT
# =============================================================================

try:
    from . import _duvc_ctl
    # Re-export all C++ bindings
    from ._duvc_ctl import *
except ImportError as e:
    msg = "Could not import C++ extension module for duvc-ctl. This library is Windows-only."
    if sys.platform != "win32":
        msg += "\n\nNote: duvc-ctl uses DirectShow APIs and requires Windows."
    raise ImportError(f"{msg}\nOriginal error: {e}") from e

# =============================================================================
# EXCEPTION HIERARCHY
# =============================================================================

from .exceptions import (
    DuvcError, DuvcErrorCode, DeviceNotFoundError, DeviceBusyError,
    PropertyNotSupportedError, InvalidValueError, PermissionDeniedError,
    SystemError, InvalidArgumentError, NotImplementedError,
    ERROR_CODE_TO_EXCEPTION, create_exception_from_error_code
)

# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class PropertyInfo(TypedDict):
    """Device property metadata and current state.
    
    Fields:
        supported: Whether property is supported by device
        current: Dict with 'value' (int) and 'mode' (str: 'manual'/'auto')
        range: Dict with 'min', 'max', 'step', 'default' (all int)
        error: Error message if read failed, None if successful
    """
    supported: bool
    current: Dict[Literal["value", "mode"], Union[int, str]]
    range: Dict[Literal["min", "max", "step", "default"], int]
    error: Optional[str]


class DeviceInfo(TypedDict):
    """Device information including all property metadata.
    
    Fields:
        name: Device name from DirectShow
        path: System device path (stable identifier)
        connected: Device currently accessible
        camera_properties: Dict mapping property names to PropertyInfo
        video_properties: Dict mapping property names to PropertyInfo
        error: Error message if analysis failed, None if successful
    """
    name: str
    path: str
    connected: bool
    camera_properties: Dict[str, PropertyInfo]
    video_properties: Dict[str, PropertyInfo]
    error: Optional[str]


# =============================================================================
# GUID HELPERS (Windows Only)
# =============================================================================

# Expose GUID class if available (Windows only)
GUID = getattr(_duvc_ctl, "PyGUID", None)

def guid_from_uuid(u: _uuid.UUID) -> GUID:
    """
    Convert a Python uuid.UUID into a duvc_ctl GUID object.

    Args:
        u: Python UUID object

    Returns:
        GUID object for vendor property functions

    Raises:
        RuntimeError: If duvc_ctl was built without GUID support

    Example:
        >>> import uuid
        >>> import duvc_ctl
        >>> vendor_guid = uuid.UUID('12345678-1234-5678-9abc-123456789abc')
        >>> duvc_guid = duvc_ctl.guid_from_uuid(vendor_guid)
    """
    if GUID is None:
        raise RuntimeError("GUID support not available (Windows only)")
    try:
        return _duvc_ctl.guid_from_uuid(u)
    except AttributeError:
        raise RuntimeError("duvc_ctl was built without GUID support")

def _normalize_guid(g: Union[str, bytes, _uuid.UUID, GUID]) -> GUID:
    """Convert various GUID formats to duvc-ctl GUID object.
    
    Args:
        g: GUID as string, bytes (16), UUID, or GUID
        
    Returns:
        Normalized GUID object
        
    Raises:
        TypeError: If input type not supported
    """
    if GUID is None:
        raise RuntimeError("GUID support not available (Windows only)")

    if isinstance(g, GUID):
        return g
    if isinstance(g, _uuid.UUID):
        return guid_from_uuid(g)
    if isinstance(g, str):
        return guid_from_uuid(_uuid.UUID(g))
    if isinstance(g, (bytes, bytearray)) and len(g) == 16:
        return GUID(bytes(g))

    raise TypeError(f"Unsupported GUID type: {type(g)}")

def read_vendor_property(device: Device, guid: Union[str, bytes, _uuid.UUID, GUID], 
                        prop_id: int) -> Tuple[bool, bytes]:
    """Read vendor-specific property data.
    
    Args:
        device: Target device
        guid: Property set GUID (string, bytes, UUID, or GUID object)
        prop_id: Property ID within set
        
    Returns:
        (success: bool, data: bytes) - data is empty if failed
    """ 
    normalized_guid = _normalize_guid(guid)

    # Use the actual function name from pybind_module.cpp
    if hasattr(_duvc_ctl, 'get_vendor_property'):
        return _duvc_ctl.get_vendor_property(device, normalized_guid, prop_id)
    else:
        raise NotImplementedError("Vendor property support not available")

def write_vendor_property(device: Device, guid: Union[str, bytes, _uuid.UUID, GUID],
                         prop_id: int, data: Union[bytes, List[int]]) -> bool:
    """Write vendor-specific property data.
    
    Args:
        device: Target device
        guid: Property set GUID (string, bytes, UUID, or GUID object)
        prop_id: Property ID within set
        data: Property data as bytes or list of integers
        
    Returns:
        True if write succeeded, False otherwise
    """
    normalized_guid = _normalize_guid(guid)

    if isinstance(data, list):
        data = bytes(data)

    # Use the actual function name from pybind_module.cpp
    if hasattr(_duvc_ctl, 'set_vendor_property'):
        return _duvc_ctl.set_vendor_property(device, normalized_guid, prop_id, data)
    else:
        raise NotImplementedError("Vendor property support not available")

# =========================================================================
# PYTHONIC API (Primary Interface)
# =========================================================================

# Import the CameraController from separate module
from .CameraController import CameraController, list_cameras, find_camera, get_camera_info
# Note: CameraController provides property-based camera control (cam.brightness = 80)
# while the Result<T> API (open_camera) provides detailed error handling.
# Both APIs use the same underlying C++ bindings but with different error handling strategies.

# =============================================================================
# CONVENIENCE UTILITY FUNCTIONS
# =============================================================================

def devices() -> List[Device]:
    """
    Get list of available camera devices.

    This is the recommended function name. Use list_devices() if you prefer
    the more verbose C++-style naming.

    Returns:
        List of available Device objects
    """
    return list_devices()

def find_device_by_name(name: str, devices_list: Optional[List[Device]] = None) -> Optional[Device]:
    """Find first device with name containing search string (case-insensitive).
    
    Args:
        name: Search string
        devices_list: Optional pre-fetched device list (avoids redundant enumeration)
        
    Returns:
        Device if found, None otherwise
    """
    if devices_list is None:
        devices_list = list_devices()
    
    for dev in devices_list:
        if name.lower() in dev.name.lower():
            return dev
    return None


    # Enhanced error message with device paths for debugging
    available_devices = [f"{dev.name} (path: {dev.path})" for dev in devices]
    from .exceptions import DeviceNotFoundError
    raise DeviceNotFoundError(
        f"Device with name containing '{name}' not found. "
        f"Available devices: {'; '.join(available_devices)}"
    )

def find_devices_by_name(name: str, devices_list: Optional[List[Device]] = None) -> List[Device]:
    """Find all devices with name containing search string (case-insensitive).
    
    Args:
        name: Search string
        devices_list: Optional pre-fetched device list (avoids redundant enumeration)
        
    Returns:
        List of matching devices (empty if none found)
    """
    if devices_list is None:
        devices_list = list_devices()
    
    matching_devices = []
    for dev in devices_list:
        if name.lower() in dev.name.lower():
            matching_devices.append(dev)
    return matching_devices


def get_device_info(device: Device) -> DeviceInfo:
    """Collect property metadata for a device.
    
    Queries device capabilities and reads all property values, ranges, and
    current settings. Failed property reads are captured with error details
    rather than raising exceptions.
    
    Args:
        device: Target device
        
    Returns:
        DeviceInfo dict with device metadata and property information
    """
    info: DeviceInfo = {
        "name": device.name,
        "path": device.path,
        "connected": is_device_connected(device),
        "camera_properties": {},
        "video_properties": {},
        "error": None
    }

    # Try to get device capabilities
    caps_result = get_device_capabilities(device)
    if not caps_result.is_ok():
        info["error"] = caps_result.error().description()
        return info

    caps = caps_result.value()

    # Analyze camera properties
    for prop in caps.supported_camera_properties():
        try:
            # Use the exception-throwing helpers from pybind_module.cpp
            camera = Camera(device)
            if camera.is_valid():
                setting_result = camera.get(prop)
                range_result = camera.get_range(prop)

                if setting_result.is_ok() and range_result.is_ok():
                    setting = setting_result.value()
                    range_info = range_result.value()
                    prop_name = to_string(prop)

                    info["camera_properties"][prop_name] = {
                        "supported": True,
                        "current": {
                            "value": setting.value,
                            "mode": to_string(setting.mode)
                        },
                        "range": {
                            "min": range_info.min,
                            "max": range_info.max,
                            "step": range_info.step,
                            "default": range_info.default_val
                        },
                        "error": None
                    }
                else:
                    prop_name = to_string(prop)
                    error_msg = setting_result.error().description() if not setting_result.is_ok() else range_result.error().description()
                    info["camera_properties"][prop_name] = {
                        "supported": False,
                        "current": {"value": 0, "mode": "unknown"},
                        "range": {"min": 0, "max": 0, "step": 0, "default": 0},
                        "error": error_msg
                    }
        except (DeviceNotFoundError, PropertyNotSupportedError, InvalidValueError) as e:
            prop_name = to_string(prop)
            info["camera_properties"][prop_name] = {
                "supported": False,
                "current": {"value": 0, "mode": "unknown"},
                "range": {"min": 0, "max": 0, "step": 0, "default": 0},
                "error": str(e)
            }
        except (SystemError, PermissionDeniedError) as e:
            prop_name = to_string(prop)
            info["camera_properties"][prop_name] = {
                "supported": False,
                "current": {"value": 0, "mode": "unknown"},
                "range": {"min": 0, "max": 0, "step": 0, "default": 0},
                "error": f"System error: {str(e)}"
            }
        except Exception as e:
            import logging
            prop_name = to_string(prop)
            
            # Log the error before suppressing it
            logging.warning(f"Failed to read camera property {prop_name} from device {device.name}: {e}")
            
            info['camera_properties'][prop_name] = {
                'supported': False, 
                'current': {'value': 0, 'mode': 'unknown'}, 
                'range': {'min': 0, 'max': 0, 'step': 0, 'default': 0}, 
                'error': f"Unexpected error: {str(e)}"
            }


    # Analyze video properties
    for prop in caps.supported_video_properties():
        try:
            camera = Camera(device)
            if camera.is_valid():
                setting_result = camera.get(prop)
                range_result = camera.get_range(prop)

                if setting_result.is_ok() and range_result.is_ok():
                    setting = setting_result.value()
                    range_info = range_result.value()
                    prop_name = to_string(prop)

                    info["video_properties"][prop_name] = {
                        "supported": True,
                        "current": {
                            "value": setting.value,
                            "mode": to_string(setting.mode)
                        },
                        "range": {
                            "min": range_info.min,
                            "max": range_info.max,
                            "step": range_info.step,
                            "default": range_info.default_val
                        },
                        "error": None
                    }
                else:
                    prop_name = to_string(prop)
                    error_msg = setting_result.error().description() if not setting_result.is_ok() else range_result.error().description()
                    info["video_properties"][prop_name] = {
                        "supported": False,
                        "current": {"value": 0, "mode": "unknown"},
                        "range": {"min": 0, "max": 0, "step": 0, "default": 0},
                        "error": error_msg
                    }
        except (DeviceNotFoundError, PropertyNotSupportedError, InvalidValueError) as e:
            prop_name = to_string(prop)
            info["video_properties"][prop_name] = {
                "supported": False,
                "current": {"value": 0, "mode": "unknown"},
                "range": {"min": 0, "max": 0, "step": 0, "default": 0},
                "error": str(e)
            }
        except (SystemError, PermissionDeniedError) as e:
            prop_name = to_string(prop)
            info["video_properties"][prop_name] = {
                "supported": False,
                "current": {"value": 0, "mode": "unknown"},
                "range": {"min": 0, "max": 0, "step": 0, "default": 0},
                "error": f"System error: {str(e)}"
            }
        except Exception as e:
            import logging
            prop_name = to_string(prop)
            
            # Log the error before suppressing it
            logging.warning(f"Failed to read video property {prop_name} from device {device.name}: {e}")
            
            info['video_properties'][prop_name] = {
                'supported': False, 
                'current': {'value': 0, 'mode': 'unknown'}, 
                'range': {'min': 0, 'max': 0, 'step': 0, 'default': 0}, 
                'error': f"Unexpected error: {str(e)}"
            }

    return info

def reset_device_to_defaults(device: Device) -> Dict[str, bool]:
    """Reset all device properties to their default values.
    
    Queries property ranges to get defaults, then sets each property.
    Individual failures do not stop processing of remaining properties.
    
    Args:
        device: Target device
        
    Returns:
        Dict mapping property names to success status (True = set, False = failed)
    """
    results: Dict[str, bool] = {}

    caps_result = get_device_capabilities(device)
    if not caps_result.is_ok():
        return results

    caps = caps_result.value()
    camera = Camera(device)
    if not camera.is_valid():
        return results

    # Reset camera properties
    for prop in caps.supported_camera_properties():
        try:
            range_result = camera.get_range(prop)
            if range_result.is_ok():
                range_info = range_result.value()
                setting = PropSetting(range_info.default_val, range_info.default_mode)
                set_result = camera.set(prop, setting)
                results[f"cam_{to_string(prop)}"] = set_result.is_ok()
            else:
                results[f"cam_{to_string(prop)}"] = False
        except Exception:
            results[f"cam_{to_string(prop)}"] = False

    # Reset video properties  
    for prop in caps.supported_video_properties():
        try:
            range_result = camera.get_range(prop)
            if range_result.is_ok():
                range_info = range_result.value()
                setting = PropSetting(range_info.default_val, range_info.default_mode)
                set_result = camera.set(prop, setting)
                results[f"vid_{to_string(prop)}"] = set_result.is_ok()
            else:
                results[f"vid_{to_string(prop)}"] = False
        except Exception:
            results[f"vid_{to_string(prop)}"] = False

    return results

def get_supported_properties(device: Device) -> Dict[str, List[str]]:
    """Get lists of supported camera and video properties.
    
    Args:
        device: Target device
        
    Returns:
        Dict with 'camera' and 'video' keys containing property name lists
    """
    result = {"camera": [], "video": []}

    caps_result = get_device_capabilities(device)
    if caps_result.is_ok():
        caps = caps_result.value()
        result["camera"] = [to_string(prop) for prop in caps.supported_camera_properties()]
        result["video"] = [to_string(prop) for prop in caps.supported_video_properties()]

    return result

def set_property_safe(device: Device, domain: str, property_enum: Union[CamProp, VidProp], 
                     value: int, mode: str = "manual") -> Tuple[bool, str]:
    """Set property with validation, returning success status and error message.
    
    Args:
        device: Target device
        domain: "cam" for CamProp or "vid" for VidProp
        property_enum: Property enum (CamProp or VidProp)
        value: Value to set
        mode: "auto" or "manual" (default: "manual")
        
    Returns:
        (success: bool, error_message: str) - error_message empty if successful
    """
    try:
        camera = Camera(device)
        if not camera.is_valid():
            return False, "Camera is not valid or connected"

        # Parse mode
        cam_mode = CamMode.Auto if mode.lower() == "auto" else CamMode.Manual
        setting = PropSetting(value, cam_mode)

        # Set property based on domain and enum
        if domain.lower() == "cam":
            if not isinstance(property_enum, CamProp):
                return False, f"Expected CamProp enum for camera domain, got {type(property_enum).__name__}"
            result = camera.set(property_enum, setting)
            if result.is_ok():
                return True, ""
            else:
                return False, result.error().description()
        elif domain.lower() == "vid":
            if not isinstance(property_enum, VidProp):
                return False, f"Expected VidProp enum for video domain, got {type(property_enum).__name__}"
            result = camera.set(property_enum, setting)
            if result.is_ok():
                return True, ""
            else:
                return False, result.error().description()
        else:
            return False, f"Invalid domain/property combination: {domain}, {property_enum}"

    except (DeviceNotFoundError, PropertyNotSupportedError, InvalidValueError) as e:
        return False, str(e)
    except (SystemError, PermissionDeniedError) as e:
        return False, f"System error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def get_property_safe(device: Device, domain: str, property_enum: Union[CamProp, VidProp]) -> Tuple[bool, Optional[PropSetting], str]:
    """Get property with validation, returning value and error message.
    
    Args:
        device: Target device
        domain: "cam" for CamProp or "vid" for VidProp
        property_enum: Property enum (CamProp or VidProp)
        
    Returns:
        (success: bool, setting: PropSetting|None, error_message: str)
    """
    try:
        camera = Camera(device)
        if not camera.is_valid():
            return False, None, "Camera is not valid or connected"

        # Get property based on domain and enum
        if domain.lower() == "cam":
            if not isinstance(property_enum, CamProp):
                return False, None, f"Expected CamProp enum for camera domain, got {type(property_enum).__name__}"
            result = camera.get(property_enum)
            if result.is_ok():
                return True, result.value(), ""
            else:
                return False, None, result.error().description()
        elif domain.lower() == "vid":
            if not isinstance(property_enum, VidProp):
                return False, None, f"Expected VidProp enum for video domain, got {type(property_enum).__name__}"
            result = camera.get(property_enum)
            if result.is_ok():
                return True, result.value(), ""
            else:
                return False, None, result.error().description()
        else:
            return False, None, f"Invalid domain/property combination: {domain}, {property_enum}"

    except (DeviceNotFoundError, PropertyNotSupportedError, InvalidValueError) as e:
        return False, None, str(e)
    except (SystemError, PermissionDeniedError) as e:
        return False, None, f"System error: {str(e)}"
    except Exception as e:
        return False, None, f"Unexpected error: {str(e)}"

# convinence iterators

def iter_devices():
    """Yield available video devices one at a time.
    
    Yields:
        Device: Each available video input device
    """
    devices = list_devices()
    for device in devices:
        yield device

def iter_connected_devices():
    """Yield only connected devices.
    
    Yields:
        Device: Each connected video input device
    """
    for device in iter_devices():
        if is_device_connected(device):
            yield device

# Add to __all__
__all__.extend(['iter_devices', 'iter_connected_devices'])


# =============================================================================
# LOGGING UTILITIES
# =============================================================================

def setup_logging(level: LogLevel = LogLevel.Info,
                 callback: Optional[Callable[[LogLevel, str], None]] = None) -> None:
    """Set log level and optional callback for log messages.
    
    Args:
        level: Minimum log level to capture (default: Info)
        callback: Optional function(level, message) called for each log event
    """
    set_log_level(level)
    if callback:
        set_log_callback(callback)

def enable_debug_logging() -> None:
    """Enable debug-level logging with console output."""
    def debug_callback(level: LogLevel, message: str) -> None:
        print(f"[DUVC {to_string(level)}] {message}")

    setup_logging(LogLevel.Debug, debug_callback)

# =============================================================================
# PLATFORM DETECTION AND WARNINGS
# =============================================================================

if sys.platform != "win32":
    warnings.warn(
        "duvc-ctl is designed for Windows only and uses DirectShow APIs. "
        "Most functionality may not be available on other platforms.",
        RuntimeWarning,
        stacklevel=2
    )

# =============================================================================
# PUBLIC API DEFINITION
# =============================================================================

__all__ = [
    # Version and metadata
    "__version__", "__author__", "__email__", "__license__", "__project__",

    # ========================================================================
    # PRIMARY PYTHONIC API (Recommended for most users)
    # ========================================================================
    'CameraController',    # Pythonic class
    'list_cameras',        # Simple camera discovery
    'find_camera',         # Find camera by name
    'get_camera_info',     # Camera information

    'open_device_context',           # Direct device context manager
    'open_device_by_name_context',   # Device context manager by name

    # Core enums (exported from C++)
    "CamMode", "CamProp", "VidProp", "ErrorCode", "LogLevel",

    # Core types (exported from C++)
    "Device", "Camera", "PropSetting", "PropRange",
    "PropertyCapability", "DeviceCapabilities",

    # Result types (exported from C++)
    "PropSettingResult", "PropRangeResult", "VoidResult", 
    "CameraResult", "DeviceCapabilitiesResult",

    # Result helper functions (exported from C++)
    "Ok_PropSetting", "Err_PropSetting", "Ok_PropRange", "Err_PropRange",
    "Ok_void", "Err_void", "Ok_bool", "Err_bool", "Ok_uint32", "Err_uint32",

    # Core functions (exported from C++)
    "list_devices", "open_camera", "is_device_connected", "get_device_capabilities",

    # Exception-throwing helpers (simple API)
    "open_camera_or_throw",
    "get_device_capabilities_or_throw",

    # String conversion functions (exported from C++)
    "to_string",

    # Logging functions (exported from C++)
    "set_log_level", "get_log_level", "log_message", "log_debug", "log_info",
    "log_warning", "log_error", "log_critical", "set_log_callback",

    # Error handling functions (exported from C++)
    "decode_system_error", "get_diagnostic_info",

    # Device callback functions (exported from C++)
    "register_device_change_callback", "unregister_device_change_callback",

    # Platform interface functions (exported from C++)
    "create_platform_interface",

    # Python exception hierarchy (from exceptions.py)
    "DuvcError", "DuvcErrorCode", "DeviceNotFoundError", "DeviceBusyError",
    "PropertyNotSupportedError", "InvalidValueError", "PermissionDeniedError", 
    "SystemError", "InvalidArgumentError", "NotImplementedError",
    "ERROR_CODE_TO_EXCEPTION", "create_exception_from_error_code",

    # Convenience utility functions
    "devices",
    "find_device_by_name", "find_devices_by_name", "get_device_info",
    "reset_device_to_defaults", "get_supported_properties", 
    "set_property_safe", "get_property_safe",

    # Logging utilities
    "setup_logging", "enable_debug_logging",

    # Type definitions
    "DeviceInfo", "PropertyInfo",

    # GUID helpers (Windows only, conditional)
    "guid_from_uuid", "read_vendor_property", "write_vendor_property",
]

# Add Logitech support
if hasattr(_duvc_ctl, "LogitechProperty"):
    __all__.extend([
        "LogitechProperty", "get_logitech_property", "set_logitech_property",
        "supports_logitech_properties"
    ])

# Add Windows-specific error decoding
if hasattr(_duvc_ctl, "decode_hresult"):
    __all__.extend([
        "decode_hresult", "get_hresult_details", "is_device_error", "is_permission_error"
    ])

# Add Windows-only exports conditionally
if sys.platform == "win32" and hasattr(_duvc_ctl, "PyGUID"):
    __all__.extend([
        "GUID", "VendorProperty", "DeviceConnection", "KsPropertySet", "_normalize_guid"
    ])