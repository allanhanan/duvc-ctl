# py/duvc_ctl/__init__.py
"""
duvc-ctl: DirectShow UVC Camera Control Library
===============================================

A Python library for controlling DirectShow UVC cameras with support for:
- PTZ (Pan/Tilt/Zoom) operations
- Camera property control (exposure, focus, etc.)
- Video processing properties (brightness, contrast, etc.)
- Device monitoring and hotplug detection
- Vendor-specific extensions (Windows only)
"""
try:
    # Import the compiled C++ module
    from ._duvc_ctl import *
except ImportError as e:
    raise ImportError("Could not import the C++ extension module for duvc-ctl.") from e

__version__ = "1.0.0"
__author__ = "allanhanan"
__email__ = "allan.hanan04@gmail.com"
__project__ = "duvc-ctl"
