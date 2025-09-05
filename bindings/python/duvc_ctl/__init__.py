"""
duvc-ctl: DirectShow UVC Camera Control Library
===============================================

Python bindings for controlling DirectShow UVC cameras.

Features:
- PTZ (Pan/Tilt/Zoom) operations
- Camera & video property control (exposure, brightness, etc.)
- Device capabilities & hotplug monitoring
- Vendor-specific extensions (Windows only)
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
import sys
import warnings
import uuid as _uuid

__version__ = "2.0.0"
__author__ = "allanhanan"
__email__ = "allan.hanan04@gmail.com"
__license__ = "MIT"
__project__ = "duvc-ctl"

try:
    from . import _duvc_ctl
    from ._duvc_ctl import *  # re-export core bindings
except ImportError as e:
    msg = "Could not import C++ extension module for duvc-ctl. This library is Windows-only."
    if sys.platform != "win32":
        msg += "\n\nNote: duvc-ctl uses DirectShow APIs and requires Windows."
    raise ImportError(f"{msg}\nOriginal error: {e}") from e

# ---------------------------------------------------------------------
# GUID Helpers for Vendor Properties
# ---------------------------------------------------------------------

# Expose GUID struct if available
GUID = getattr(_duvc_ctl, "PyGUID", None)

def guid_from_uuid(u: "uuid.UUID") -> GUID:
    """
    Convert a Python uuid.UUID into a duvc_ctl GUID/PyGUID object.
    """
    try:
        # Use the binding's helper directly (C++ lambda handles uuid.UUID)
        return _duvc_ctl.guid_from_uuid(u)
    except AttributeError:
        raise RuntimeError("duvc_ctl was built without PyGUID support")


def _normalize_guid(g: str | bytes | GUID | _uuid.UUID) -> GUID:
    """Normalize various Python types into a duvc_ctl GUID."""
    if isinstance(g, GUID):
        return g
    if isinstance(g, _uuid.UUID):
        return guid_from_uuid(g)
    if isinstance(g, str):
        return guid_from_uuid(_uuid.UUID(g))
    if isinstance(g, (bytes, bytearray)) and len(g) == 16:
        return GUID(bytes(g))
    raise TypeError(f"Unsupported GUID type: {type(g)}")

def write_vendor_property(device: Device, guid: GUID, prop_id: int, data: Any) -> bool:
    """
    Write a vendor-specific property.
    
    Args:
        device: Target device
        guid: Property set GUID (uuid.UUID or GUID)
        prop_id: Property ID
        data: Either bytes or list[int]
    """
    if isinstance(data, list):
        data = bytes(data)
    return _duvc_ctl.write_vendor_property(device, guid, prop_id, data)


def read_vendor_property(device: Device, guid: GUID, prop_id: int) -> tuple[bool, bytes]:
    """
    Read a vendor-specific property.

    Returns:
        (success, data as bytes)
    """
    return _duvc_ctl.read_vendor_property(device, guid, prop_id)


# ---------------------------------------------------------------------
# Convenience utilities
# ---------------------------------------------------------------------

def find_device_by_name(name: str) -> Optional[Device]:
    """
    Find a device by (partial, case-insensitive) name.
    """
    for dev in list_devices():
        if name.lower() in dev.name.lower():
            return dev
    return None

def get_device_info(device: Device) -> Dict[str, Any]:
    """
    Get detailed information about a device (properties & ranges).
    """
    info: Dict[str, Any] = {
        "name": device.name,
        "path": device.path,
        "connected": is_device_connected(device),
        "camera_properties": {},
        "video_properties": {},
    }

    caps_result = get_device_capabilities(device)
    if not caps_result.is_ok():
        return info
    caps = caps_result.value()

    for prop in caps.supported_camera_properties():
        try:
            setting = device.get_camera_property(prop)
            rng = device.get_camera_property_range(prop)
            info["camera_properties"][cam_prop_to_string(prop)] = {
                "current": {"value": setting.value, "mode": setting.mode},
                "range": {
                    "min": rng.min, "max": rng.max,
                    "step": rng.step, "default": rng.default_val
                },
            }
        except Exception:
            info["camera_properties"][cam_prop_to_string(prop)] = {"supported": False}

    for prop in caps.supported_video_properties():
        try:
            setting = device.get_video_property(prop)
            rng = device.get_video_property_range(prop)
            info["video_properties"][vid_prop_to_string(prop)] = {
                "current": {"value": setting.value, "mode": setting.mode},
                "range": {
                    "min": rng.min, "max": rng.max,
                    "step": rng.step, "default": rng.default_val
                },
            }
        except Exception:
            info["video_properties"][vid_prop_to_string(prop)] = {"supported": False}

    return info

def reset_device_to_defaults(device: Device) -> Dict[str, bool]:
    """
    Reset all supported properties of a device to their defaults.
    """
    results: Dict[str, bool] = {}
    caps_result = get_device_capabilities(device)
    if not caps_result.is_ok():
        return results
    caps = caps_result.value()

    for prop in caps.supported_camera_properties():
        try:
            rng = device.get_camera_property_range(prop)
            ok = device.set_camera_property(prop, PropSetting(rng.default_val, rng.default_mode))
            results[f"cam_{cam_prop_to_string(prop)}"] = bool(ok)
        except Exception:
            results[f"cam_{cam_prop_to_string(prop)}"] = False

    for prop in caps.supported_video_properties():
        try:
            rng = device.get_video_property_range(prop)
            ok = device.set_video_property(prop, PropSetting(rng.default_val, rng.default_mode))
            results[f"vid_{vid_prop_to_string(prop)}"] = bool(ok)
        except Exception:
            results[f"vid_{vid_prop_to_string(prop)}"] = False

    return results

# ---------------------------------------------------------------------
# Python exceptions
# ---------------------------------------------------------------------

class DuvcError(Exception): """Base error for duvc-ctl."""; pass
class DeviceNotFoundError(DuvcError): """Device not found or disconnected."""; pass
class DeviceBusyError(DuvcError): """Device is busy or in use."""; pass
class PropertyNotSupportedError(DuvcError): """Property not supported by device."""; pass
class InvalidValueError(DuvcError): """Invalid or out-of-range value."""; pass

# ---------------------------------------------------------------------
# Platform warning
# ---------------------------------------------------------------------

if sys.platform != "win32":
    warnings.warn("duvc-ctl is designed for Windows only.", RuntimeWarning, stacklevel=2)

# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

__all__ = [
    # Core types
    "Device", "Camera", "PropSetting", "PropRange",
    "CamMode", "CamProp", "VidProp", "ErrorCode", "CppError",
    "LogLevel", "PropSettingResult", "PropRangeResult",
    "VoidResult", "CameraResult", "DeviceCapabilities",
    "DeviceCapabilitiesResult", "PropertyCapability", "GUID",

    # Core functions
    "list_devices", "is_device_connected",
    "get_camera_property_direct", "get_camera_property_range_direct",
    "get_device_capabilities", "get_device_capabilities_by_index",
    "open_camera",
    "read_vendor_property", "write_vendor_property",
    "register_device_change_callback", "unregister_device_change_callback",

    # Convenience functions
    "find_device_by_name", "get_device_info", "reset_device_to_defaults",
    "guid_from_uuid",

    # String conversion
    "cam_prop_to_string", "vid_prop_to_string",
    "cam_mode_to_string", "error_code_to_string",

    # Exceptions
    "DuvcError", "DeviceNotFoundError", "DeviceBusyError",
    "PropertyNotSupportedError", "InvalidValueError",
]
