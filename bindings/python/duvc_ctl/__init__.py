"""
duvc-ctl: DirectShow UVC Camera Control Library
===============================================

Python bindings for controlling DirectShow UVC cameras on Windows.

This library provides comprehensive control over UVC cameras using DirectShow APIs,
supporting both basic camera operations and advanced vendor-specific features.

Features:
- PTZ (Pan/Tilt/Zoom) camera control with precise positioning
- Video property adjustment (brightness, contrast, exposure, etc.)
- Device capability detection and real-time monitoring
- Vendor-specific extensions (Logitech, etc.)
- Result-based error handling with detailed diagnostics
- Thread-safe callback system for device hotplug events
- Flexible GUID handling for vendor properties

Example Basic Usage:
    >>> import duvc_ctl
    >>> devices = duvc_ctl.list_devices()
    >>> if devices:
    ...     camera = duvc_ctl.Camera(devices[0])
    ...     if camera.is_valid():
    ...         # Get current pan value
    ...         result = camera.get(duvc_ctl.CamProp.Pan)
    ...         if result.is_ok():
    ...             print(f"Pan: {result.value().value}")
    ...         
    ...         # Set pan to center position
    ...         setting = duvc_ctl.PropSetting(0, duvc_ctl.CamMode.Manual)
    ...         camera.set(duvc_ctl.CamProp.Pan, setting)

Example Advanced Usage:
    >>> # Get comprehensive device information
    >>> info = duvc_ctl.get_device_info(devices[0])
    >>> print(f"Device: {info['name']}")
    >>> print(f"Supported camera properties: {info['camera_properties'].keys()}")
    >>> 
    >>> # Monitor device changes
    >>> def on_device_change(added, path):
    ...     print(f"Device {'added' if added else 'removed'}: {path}")
    >>> duvc_ctl.register_device_change_callback(on_device_change)
"""

from __future__ import annotations

import sys
import warnings
import uuid as _uuid
from typing import List, Optional, Dict, Any, Union, Tuple, Callable

# =============================================================================
# MODULE METADATA
# =============================================================================

__version__ = "2.0.0"
__author__ = "allanhanan"
__email__ = "allan.hanan04@gmail.com"
__license__ = "MIT"
__project__ = "duvc-ctl"

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
# IMPORT EXCEPTION HIERARCHY FROM exceptions.py MODULE
# =============================================================================

from .exceptions import (
    DuvcError, DuvcErrorCode, DeviceNotFoundError, DeviceBusyError,
    PropertyNotSupportedError, InvalidValueError, PermissionDeniedError,
    SystemError, InvalidArgumentError, NotImplementedError,
    ERROR_CODE_TO_EXCEPTION, create_exception_from_error_code
)

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
        GUID object compatible with duvc_ctl vendor functions
        
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
    """
    Normalize various Python types into a duvc_ctl GUID.
    
    Args:
        g: GUID in various formats (string, bytes, UUID, or GUID)
        
    Returns:
        Normalized GUID object
        
    Raises:
        TypeError: If the input type is not supported
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
    """
    Read a vendor-specific property with flexible GUID input.
    
    Args:
        device: Target device
        guid: Property set GUID (various formats accepted)
        prop_id: Property ID within the set
        
    Returns:
        Tuple of (success, data as bytes)
        
    Example:
        >>> success, data = duvc_ctl.read_vendor_property(
        ...     device, "12345678-1234-5678-9abc-123456789abc", 1)
        >>> if success:
        ...     print(f"Property data: {data.hex()}")
    """
    normalized_guid = _normalize_guid(guid)
    # Use the actual function name from pybind_module.cpp
    if hasattr(_duvc_ctl, 'get_vendor_property'):
        return _duvc_ctl.get_vendor_property(device, normalized_guid, prop_id)
    else:
        raise NotImplementedError("Vendor property support not available")

def write_vendor_property(device: Device, guid: Union[str, bytes, _uuid.UUID, GUID], 
                         prop_id: int, data: Union[bytes, List[int]]) -> bool:
    """
    Write a vendor-specific property with flexible inputs.
    
    Args:
        device: Target device
        guid: Property set GUID (various formats accepted)
        prop_id: Property ID within the set
        data: Property data (bytes or list of integers)
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> success = duvc_ctl.write_vendor_property(
        ...     device, vendor_guid, 1, [0x01, 0x02, 0x03])
        >>> if success:
        ...     print("Property written successfully")
    """
    normalized_guid = _normalize_guid(guid)
    if isinstance(data, list):
        data = bytes(data)
    # Use the actual function name from pybind_module.cpp
    if hasattr(_duvc_ctl, 'set_vendor_property'):
        return _duvc_ctl.set_vendor_property(device, normalized_guid, prop_id, data)
    else:
        raise NotImplementedError("Vendor property support not available")

# =============================================================================
# CONVENIENCE UTILITY FUNCTIONS
# =============================================================================

def find_device_by_name(name: str) -> Optional[Device]:
    """
    Find a device by partial, case-insensitive name matching.
    
    Args:
        name: Device name or partial name to search for
        
    Returns:
        First device whose name contains the search string (case-insensitive),
        or None if no match is found
        
    Example:
        >>> # Find a Logitech camera
        >>> device = duvc_ctl.find_device_by_name("logitech")
        >>> if device:
        ...     print(f"Found: {device.name}")
    """
    for dev in list_devices():
        if name.lower() in dev.name.lower():
            return dev
    return None

def find_devices_by_name(name: str) -> List[Device]:
    """
    Find all devices matching a partial, case-insensitive name.
    
    Args:
        name: Device name or partial name to search for
        
    Returns:
        List of devices whose names contain the search string
        
    Example:
        >>> # Find all USB cameras
        >>> usb_cameras = duvc_ctl.find_devices_by_name("usb")
        >>> for cam in usb_cameras:
        ...     print(f"USB Camera: {cam.name}")
    """
    matching_devices = []
    for dev in list_devices():
        if name.lower() in dev.name.lower():
            matching_devices.append(dev)
    return matching_devices

def get_device_info(device: Device) -> Dict[str, Any]:
    """
    Get comprehensive information about a device including all supported properties.
    
    Args:
        device: Device to analyze
        
    Returns:
        Dictionary containing device information, supported properties,
        current values, and valid ranges
        
    Example:
        >>> info = duvc_ctl.get_device_info(device)
        >>> print(f"Device: {info['name']}")
        >>> print(f"Connected: {info['connected']}")
        >>> for prop, details in info['camera_properties'].items():
        ...     if details.get('supported', True):
        ...         print(f"{prop}: {details['current']['value']}")
    """
    info: Dict[str, Any] = {
        "name": device.name,
        "path": device.path,
        "connected": is_device_connected(device),
        "camera_properties": {},
        "video_properties": {},
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
            camera = Camera(device)
            if camera.is_valid():
                # Use the exception-throwing helpers from pybind_module.cpp
                setting = camera.get_camera_property(prop)
                range_info = camera.get_camera_property_range(prop)
                
                prop_name = to_string(prop)
                info["camera_properties"][prop_name] = {
                    "supported": True,
                    "current": {
                        "value": setting.value,
                        "mode": setting.mode
                    },
                    "range": {
                        "min": range_info.min,
                        "max": range_info.max,
                        "step": range_info.step,
                        "default": range_info.default_val
                    }
                }
        except Exception as e:
            prop_name = to_string(prop)
            info["camera_properties"][prop_name] = {
                "supported": False, 
                "error": str(e)
            }
    
    # Analyze video properties
    for prop in caps.supported_video_properties():
        try:
            camera = Camera(device)
            if camera.is_valid():
                # Use the exception-throwing helpers from pybind_module.cpp
                setting = camera.get_video_property(prop)
                range_info = camera.get_video_property_range(prop)
                
                prop_name = to_string(prop)
                info["video_properties"][prop_name] = {
                    "supported": True,
                    "current": {
                        "value": setting.value,
                        "mode": setting.mode
                    },
                    "range": {
                        "min": range_info.min,
                        "max": range_info.max,
                        "step": range_info.step,
                        "default": range_info.default_val
                    }
                }
        except Exception as e:
            prop_name = to_string(prop)
            info["video_properties"][prop_name] = {
                "supported": False,
                "error": str(e)
            }
    
    return info

def reset_device_to_defaults(device: Device) -> Dict[str, bool]:
    """
    Reset all supported properties of a device to their default values.
    
    Args:
        device: Device to reset
        
    Returns:
        Dictionary mapping property names to success status
        
    Example:
        >>> results = duvc_ctl.reset_device_to_defaults(device)
        >>> failed_props = [prop for prop, success in results.items() if not success]
        >>> if failed_props:
        ...     print(f"Failed to reset: {failed_props}")
        >>> else:
        ...     print("All properties reset successfully")
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
            range_info = camera.get_camera_property_range(prop)
            setting = PropSetting(range_info.default_val, range_info.default_mode)
            camera.set_camera_property(prop, setting)
            results[f"cam_{to_string(prop)}"] = True
        except Exception:
            results[f"cam_{to_string(prop)}"] = False
    
    # Reset video properties
    for prop in caps.supported_video_properties():
        try:
            range_info = camera.get_video_property_range(prop)
            setting = PropSetting(range_info.default_val, range_info.default_mode)
            camera.set_video_property(prop, setting)
            results[f"vid_{to_string(prop)}"] = True
        except Exception:
            results[f"vid_{to_string(prop)}"] = False
    
    return results

def get_supported_properties(device: Device) -> Dict[str, List[str]]:
    """
    Get lists of supported camera and video properties for a device.
    
    Args:
        device: Device to analyze
        
    Returns:
        Dictionary with 'camera' and 'video' keys containing lists of property names
        
    Example:
        >>> props = duvc_ctl.get_supported_properties(device)
        >>> print(f"Camera properties: {props['camera']}")
        >>> print(f"Video properties: {props['video']}")
    """
    result = {"camera": [], "video": []}
    
    caps_result = get_device_capabilities(device)
    if caps_result.is_ok():
        caps = caps_result.value()
        result["camera"] = [to_string(prop) for prop in caps.supported_camera_properties()]
        result["video"] = [to_string(prop) for prop in caps.supported_video_properties()]
    
    return result

def set_property_safe(device: Device, domain: str, property_name: str, 
                     value: int, mode: str = "manual") -> Tuple[bool, str]:
    """
    Safely set a property with validation and error reporting.
    
    Args:
        device: Target device
        domain: Property domain ("cam" or "vid")
        property_name: Name of the property to set
        value: Value to set
        mode: Control mode ("auto" or "manual")
        
    Returns:
        Tuple of (success, error_message)
        
    Example:
        >>> success, error = duvc_ctl.set_property_safe(
        ...     device, "cam", "Pan", 100, "manual")
        >>> if not success:
        ...     print(f"Failed to set Pan: {error}")
    """
    try:
        camera = Camera(device)
        if not camera.is_valid():
            return False, "Camera is not valid or connected"
        
        # Parse mode
        cam_mode = CamMode.Auto if mode.lower() == "auto" else CamMode.Manual
        setting = PropSetting(value, cam_mode)
        
        # Set property based on domain
        if domain.lower() == "cam":
            # Find camera property by name
            for prop in [CamProp.Pan, CamProp.Tilt, CamProp.Roll, CamProp.Zoom,
                        CamProp.Exposure, CamProp.Iris, CamProp.Focus, CamProp.Privacy]:
                if to_string(prop).lower() == property_name.lower():
                    camera.set_camera_property(prop, setting)
                    return True, ""
            return False, f"Unknown camera property: {property_name}"
            
        elif domain.lower() == "vid":
            # Find video property by name  
            for prop in [VidProp.Brightness, VidProp.Contrast, VidProp.Hue,
                        VidProp.Saturation, VidProp.Sharpness, VidProp.Gamma,
                        VidProp.WhiteBalance, VidProp.Gain]:
                if to_string(prop).lower() == property_name.lower():
                    camera.set_video_property(prop, setting)
                    return True, ""
            return False, f"Unknown video property: {property_name}"
        else:
            return False, f"Unknown domain: {domain}. Use 'cam' or 'vid'"
            
    except Exception as e:
        return False, f"Exception occurred: {str(e)}"

def get_property_safe(device: Device, domain: str, property_name: str) -> Tuple[bool, Optional[PropSetting], str]:
    """
    Safely get a property with validation and error reporting.
    
    Args:
        device: Target device
        domain: Property domain ("cam" or "vid") 
        property_name: Name of the property to get
        
    Returns:
        Tuple of (success, property_setting, error_message)
        
    Example:
        >>> success, setting, error = duvc_ctl.get_property_safe(device, "cam", "Pan")
        >>> if success:
        ...     print(f"Pan value: {setting.value} (mode: {setting.mode})")
    """
    try:
        camera = Camera(device)
        if not camera.is_valid():
            return False, None, "Camera is not valid or connected"
        
        # Get property based on domain
        if domain.lower() == "cam":
            # Find camera property by name
            for prop in [CamProp.Pan, CamProp.Tilt, CamProp.Roll, CamProp.Zoom,
                        CamProp.Exposure, CamProp.Iris, CamProp.Focus, CamProp.Privacy]:
                if to_string(prop).lower() == property_name.lower():
                    setting = camera.get_camera_property(prop)
                    return True, setting, ""
            return False, None, f"Unknown camera property: {property_name}"
            
        elif domain.lower() == "vid":
            # Find video property by name
            for prop in [VidProp.Brightness, VidProp.Contrast, VidProp.Hue,
                        VidProp.Saturation, VidProp.Sharpness, VidProp.Gamma,
                        VidProp.WhiteBalance, VidProp.Gain]:
                if to_string(prop).lower() == property_name.lower():
                    setting = camera.get_video_property(prop)
                    return True, setting, ""
            return False, None, f"Unknown video property: {property_name}"
        else:
            return False, None, f"Unknown domain: {domain}. Use 'cam' or 'vid'"
            
    except Exception as e:
        return False, None, f"Exception occurred: {str(e)}"

# =============================================================================
# LOGGING UTILITIES
# =============================================================================

def setup_logging(level: LogLevel = LogLevel.Info, 
                 callback: Optional[Callable[[LogLevel, str], None]] = None) -> None:
    """
    Setup logging for duvc-ctl with optional custom callback.
    
    Args:
        level: Minimum log level to capture
        callback: Optional callback function for log messages
        
    Example:
        >>> def log_handler(level, message):
        ...     print(f"[{level.name}] {message}")
        >>> duvc_ctl.setup_logging(duvc_ctl.LogLevel.Debug, log_handler)
    """
    set_log_level(level)
    if callback:
        set_log_callback(callback)

def enable_debug_logging() -> None:
    """Enable debug-level logging with console output."""
    def debug_callback(level: LogLevel, message: str) -> None:
        print(f"[DUVC {level.name}] {message}")
    
    setup_logging(LogLevel.Debug, debug_callback)

# =============================================================================
# PLATFORM DETECTION AND WARNINGS
# =============================================================================

if sys.platform != "win32":
    warnings.warn(
        "duvc-ctl is designed for Windows only and uses DirectShow APIs. "
        "Some functionality may not be available on other platforms.",
        RuntimeWarning, 
        stacklevel=2
    )

# =============================================================================
# PUBLIC API DEFINITION
# =============================================================================

__all__ = [
    # Version and metadata
    "__version__", "__author__", "__email__", "__license__", "__project__",
    
    # Core enums (exported from C++)
    "CamMode", "CamProp", "VidProp", "ErrorCode", "LogLevel",
    
    # Core types (exported from C++)
    "Device", "Camera", "PropSetting", "PropRange", 
    "PropertyCapability", "DeviceCapabilities", "CppError",
    
    # Result types (exported from C++)
    "PropSettingResult", "PropRangeResult", "VoidResult", 
    "CameraResult", "DeviceCapabilitiesResult",
    
    # Core functions (exported from C++)
    "list_devices", "is_device_connected", "get_device_capabilities",
    
    # String conversion functions (exported from C++)
    "to_string",
    
    # Logging functions (exported from C++)
    "set_log_level", "get_log_level", "log_message", "log_debug", "log_info",
    "log_warning", "log_error", "log_critical", "set_log_callback",
    
    # Error handling functions (exported from C++)
    "decode_system_error", "get_diagnostic_info",
    
    # Device callback functions (exported from C++)
    "register_device_change_callback", "unregister_device_change_callback",
    
    # Quick API functions (exported from C++)
    "get_camera_property_direct",
    
    # Python exception hierarchy (from exceptions.py)
    "DuvcError", "DuvcErrorCode", "DeviceNotFoundError", "DeviceBusyError",
    "PropertyNotSupportedError", "InvalidValueError", "PermissionDeniedError", 
    "SystemError", "InvalidArgumentError", "NotImplementedError",
    "ERROR_CODE_TO_EXCEPTION", "create_exception_from_error_code",
    
    # Convenience utility functions
    "find_device_by_name", "find_devices_by_name", "get_device_info", 
    "reset_device_to_defaults", "get_supported_properties",
    "set_property_safe", "get_property_safe",
    
    # Logging utilities
    "setup_logging", "enable_debug_logging",
    
    # GUID helpers (Windows only, conditional)
    "guid_from_uuid", "read_vendor_property", "write_vendor_property",
]

# Add Windows-only exports conditionally
if sys.platform == "win32" and hasattr(_duvc_ctl, "PyGUID"):
    __all__.extend([
        "GUID", "VendorProperty", "DeviceConnection", "KsPropertySet",
        "_normalize_guid"
    ])
    
    # Add Logitech support if available
    if hasattr(_duvc_ctl, "LogitechProperty"):
        __all__.extend([
            "LogitechProperty",
            "get_logitech_property", "set_logitech_property", "supports_logitech_properties"
        ])
    
    # Add Windows-specific error decoding if available
    if hasattr(_duvc_ctl, "decode_hresult"):
        __all__.extend([
            "decode_hresult", "get_hresult_details", "is_device_error", "is_permission_error"
        ])
