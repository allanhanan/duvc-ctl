"""
CameraController - Pythonic camera control interface.

Property-based access to camera controls with automatic device management
and context manager support. Uses core C++ bindings internally.

Supports both property names and common aliases (e.g., 'zoom' or 'z').

Property Aliases Reference:
==========================
    Full Name       Aliases
    ----------      -------
    brightness      bright
    white_balance   wb, whitebalance  
    color_enable    color, colorenable
    saturation      sat
    zoom            z
    focus           f
    exposure        exp
    pan             horizontal
    tilt            vertical

Example Usage:
    cam.set('brightness', 80)    # Full name
    cam.set('bright', 80)        # Alias
    cam.set('wb', 'auto')        # White balance alias
    cam.set('z', 150)            # Zoom alias
"""

import warnings
from typing import Optional, Dict, Any, List, Tuple, Union

# Import ONLY the core C++ bindings - single source of truth
from ._duvc_ctl import (
    # Core functions that will stay
    list_devices, 
    open_camera,
    
    # Core types 
    VidProp, CamProp, CamMode, PropSetting,
    Device,
    Camera as CoreCamera,  # C++ Camera class - rename to avoid confusion
)

# Import our Python exceptions
from .exceptions import (
    DeviceNotFoundError, PropertyNotSupportedError, 
    InvalidValueError, SystemError as DuvcSystemError
)


class CameraController:
    """Simple property-based camera control interface.
    
    Provides automatic device selection, property-style access, and context
    manager support. Internally uses core C++ camera bindings.
    
    For lower-level Result<T> API control, import and use core functions directly:
        result = duvc_ctl.open_camera(device)
    """
    
    def __init__(self, device: Optional[Device] = None, device_index: Optional[int] = None, device_name: Optional[str] = None):
        """Connect to a camera device.
        
        Args:
            device_index: Specific device by index (default: 0, first available)
            device_name: Device by name substring match, case-insensitive
            device: Device object from list_devices()
            
        Raises:
            DeviceNotFoundError: No cameras found or specified device not found
            DuvcSystemError: Camera connection failed
        """
        import threading
        self._lock = threading.Lock()  # Simple lock for state protection
        self._core_camera: Optional[CoreCamera] = None
        self._device: Optional[Device] = None
        self._is_closed = False
        self._connect(device, device_index, device_name)

        # Property range constants
        BRIGHTNESS_MIN = 0
        BRIGHTNESS_MAX = 100
        BRIGHTNESS_DEFAULT = 50
        
        CONTRAST_MIN = 0
        CONTRAST_MAX = 100
        CONTRAST_DEFAULT = 50
        
        SATURATION_MIN = 0
        SATURATION_MAX = 100
        SATURATION_DEFAULT = 50
        
        HUE_MIN = -180
        HUE_MAX = 180
        HUE_DEFAULT = 0
        
        PAN_MIN = -180
        PAN_MAX = 180
        PAN_CENTER = 0
        
        TILT_MIN = -90
        TILT_MAX = 90
        TILT_CENTER = 0
        
        ZOOM_MIN = 100
        ZOOM_MAX = 1000
        ZOOM_DEFAULT = 100  # No zoom
        
        # Preset configurations (moved from method)
        BUILT_IN_PRESETS = {
            'daylight': {
                'brightness': 60,
                'contrast': 50,
                'white_balance': 'auto',
                'exposure': 'auto'
            },
            'indoor': {
                'brightness': 75,
                'contrast': 60,
                'white_balance': 3200,
                'exposure': 'auto'
            },
            'night': {
                'brightness': 80,
                'contrast': 70,
                'gain': 80,
                'exposure': 'auto'
            },
            'conference': {
                'brightness': 70,
                'contrast': 55,
                'white_balance': 'auto',
                'pan': PAN_CENTER,
                'tilt': TILT_CENTER,
                'zoom': ZOOM_DEFAULT
            }
        }
        
        # Smart defaults (moved from method)
        _SMART_DEFAULTS = {
            'brightness': BRIGHTNESS_DEFAULT,
            'contrast': CONTRAST_DEFAULT,
            'saturation': SATURATION_DEFAULT,
            'pan': PAN_CENTER,
            'tilt': TILT_CENTER,
            'zoom': ZOOM_DEFAULT,
            'white_balance': 'auto',
            'exposure': 'auto',
            'focus': 'auto'
        }
    
    def _connect(self, device: Optional[Device], device_index: Optional[int], device_name: Optional[str]) -> None:
        """Establish connection to camera using core C++ APIs.
        
        Priority: device > device_index > device_name > first available
        """
        # Priority 1: Direct Device object provided
        if device is not None:
            if not device.is_valid():
                raise DeviceNotFoundError(
                    f"Invalid device object: {device.name}\n"
                    "Please provide a valid Device from list_devices()"
                )
            current_devices = list_devices()
            device_paths = {d.path for d in current_devices}
            
            if device.path not in device_paths:
                available = [f"{i}: {d.name}" for i, d in enumerate(current_devices)]
                raise DeviceNotFoundError(
                    f"Device '{device.name}' not found in current enumeration.\n"
                    f"The device may have been disconnected or the Device object is invalid.\n"
                    f"Available cameras:\n" + "\n".join(available) if available else "No cameras detected."
                )
            
            self._device = device
        
        # Priority 2-4: Need to enumerate devices
        else:
            # Use ONLY the core C++ list_devices function
            devices_list = list_devices()
            if not devices_list:
                raise DeviceNotFoundError(
                    "No cameras detected. Please check:\n"
                    "• Camera is connected and powered on\n"
                    "• Camera drivers are installed\n"
                )
            
            # Priority 2: Device index specified
            if device_index is not None:
                if device_index >= len(devices_list):
                    available = [f"{i}: {d.name}" for i, d in enumerate(devices_list)]
                    raise DeviceNotFoundError(
                        f"Device index {device_index} not found.\n"
                        f"Available cameras:\n" + "\n".join(available)
                    )
                self._device = devices_list[device_index]
            
            # Priority 3: Device name pattern specified
            elif device_name is not None:
                # Implement our own device finding by name substring
                matching_devices = []
                for dev in devices_list:
                    if device_name.lower() in dev.name.lower():
                        matching_devices.append(dev)
                
                if not matching_devices:
                    available = [d.name for d in devices_list]
                    raise DeviceNotFoundError(
                        f"No camera matching '{device_name}' found.\n"
                        f"Available: {', '.join(available)}"
                    )
                self._device = matching_devices[0]
            
            # Priority 4: Default to first available
            else:
                available = [f"{i}: {d.name}" for i, d in enumerate(devices_list)]
                raise ValueError(
                    "No device specified. Provide one of:\n"
                    "• device=Device object from list_devices()\n"
                    "• device_index=0 (zero-based index)\n"
                    "• device_name='Camera Name' (substring match)\n"
                    f"\nAvailable cameras:\n" + "\n".join(available)
                )
            
        # Open camera using ONLY the core C++ API
        result = open_camera(self._device)
        if not result.is_ok():
            error_desc = result.error().description()
            raise DuvcSystemError(
                f"Failed to connect to '{self._device.name}': {error_desc}\n"
                "This might be because:\n"
                "• Camera is in use by another application\n"
                "• Insufficient permissions\n"
                "• Hardware issue"
            )
        self._core_camera = result.value()

    
    # Context manager support
    def __enter__(self) -> 'CameraController':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> bool:
        """Context manager exit - cleanup resources."""
        self.close()
        return False
        
    def close(self) -> None:
        """Close camera and release resources."""
        with self._lock:
            if self._core_camera and not self._is_closed:
                self._core_camera = None
                self._is_closed = True
    
    def _ensure_connected(self) -> None:
        """Ensure camera is still connected and not closed."""
        with self._lock:
            if self._is_closed or self._core_camera is None:
                raise RuntimeError("Camera has been closed")

    # ========================================================================
    # VIDEO PROPERTIES (VidProp)
    # ========================================================================

    def _get_dynamic_range(self, property_name: str, fallback_min: int = 0, fallback_max: int = 100) -> tuple:
        """Get actual device range for property, with fallback defaults."""
        try:
            prop_range = self.get_property_range(property_name)
            if prop_range:
                return (prop_range.get('min', fallback_min), prop_range.get('max', fallback_max))
        except:
            pass
        return (fallback_min, fallback_max)

    @property
    def brightness(self) -> int:
        """Camera brightness (uses device range, typically 0-255)."""
        return self._get_video_property(VidProp.Brightness, "brightness")

    @brightness.setter  
    def brightness(self, value: int):
        """Set brightness using actual device range."""
        min_val, max_val = self._get_dynamic_range("brightness", 0, 100)
        self._set_video_property(VidProp.Brightness, "brightness", value, min_val, max_val)

    @property
    def contrast(self) -> int:
        """Camera contrast (uses device range, typically 0-100)."""
        return self._get_video_property(VidProp.Contrast, "contrast")

    @contrast.setter
    def contrast(self, value: int):
        """Set contrast using actual device range."""
        min_val, max_val = self._get_dynamic_range("contrast", 0, 100)
        self._set_video_property(VidProp.Contrast, "contrast", value, min_val, max_val)

    @property
    def hue(self) -> int:
        """Camera hue (uses device range, often -180 to +180)."""
        return self._get_video_property(VidProp.Hue, "hue")

    @hue.setter
    def hue(self, value: int):
        """Set hue using actual device range."""
        min_val, max_val = self._get_dynamic_range("hue", -180, 180)
        self._set_video_property(VidProp.Hue, "hue", value, min_val, max_val)

    @property
    def saturation(self) -> int:
        """Camera saturation (uses device range, typically 0-100)."""
        return self._get_video_property(VidProp.Saturation, "saturation")

    @saturation.setter
    def saturation(self, value: int):
        """Set saturation using actual device range."""
        min_val, max_val = self._get_dynamic_range("saturation", 0, 100)
        self._set_video_property(VidProp.Saturation, "saturation", value, min_val, max_val)

    @property
    def sharpness(self) -> int:
        """Camera sharpness (uses device range)."""
        return self._get_video_property(VidProp.Sharpness, "sharpness")

    @sharpness.setter
    def sharpness(self, value: int):
        """Set sharpness using actual device range."""
        min_val, max_val = self._get_dynamic_range("sharpness", 0, 100)
        self._set_video_property(VidProp.Sharpness, "sharpness", value, min_val, max_val)

    @property
    def gamma(self) -> int:
        """Camera gamma (uses device range)."""
        return self._get_video_property(VidProp.Gamma, "gamma")

    @gamma.setter
    def gamma(self, value: int):
        """Set gamma using actual device range."""
        min_val, max_val = self._get_dynamic_range("gamma", 100, 300)
        self._set_video_property(VidProp.Gamma, "gamma", value, min_val, max_val)

    @property
    def color_enable(self) -> bool:
        """Color vs monochrome (True = color, False = mono)."""
        return bool(self._get_video_property(VidProp.ColorEnable, "color_enable"))

    @color_enable.setter
    def color_enable(self, value: bool):
        """Set color mode (no range needed for bool)."""
        self._set_video_property(VidProp.ColorEnable, "color_enable", int(value))

    @property
    def white_balance(self) -> int:
        """White balance temperature (uses device range, in Kelvin)."""
        return self._get_video_property(VidProp.WhiteBalance, "white_balance")

    @white_balance.setter
    def white_balance(self, value: int):
        """Set white balance using actual device range."""
        min_val, max_val = self._get_dynamic_range("white_balance", 2700, 6500)
        self._set_video_property(VidProp.WhiteBalance, "white_balance", value, min_val, max_val)

    @property
    def video_backlight_compensation(self) -> int:
        """Video backlight compensation (uses device range)."""
        return self._get_video_property(VidProp.BacklightCompensation, "video_backlight_compensation")

    @video_backlight_compensation.setter
    def video_backlight_compensation(self, value: int):
        """Set backlight compensation using actual device range."""
        min_val, max_val = self._get_dynamic_range("video_backlight_compensation", 0, 100)
        self._set_video_property(VidProp.BacklightCompensation, "video_backlight_compensation", value, min_val, max_val)

    @property
    def gain(self) -> int:
        """Sensor gain/amplification (uses device range)."""
        return self._get_video_property(VidProp.Gain, "gain")

    @gain.setter
    def gain(self, value: int):
        """Set gain using actual device range."""
        min_val, max_val = self._get_dynamic_range("gain", 0, 100)
        self._set_video_property(VidProp.Gain, "gain", value, min_val, max_val)

    # ========================================================================
    # CAMERA PROPERTIES (CamProp)
    # ========================================================================

    @property
    def pan(self) -> int:
        """Camera pan position (uses device range in degrees)."""
        return self._get_camera_property(CamProp.Pan, "pan")

    @pan.setter
    def pan(self, value: int):
        """Set camera pan using actual device range."""
        min_val, max_val = self._get_dynamic_range("pan", -180, 180)
        self._set_camera_property(CamProp.Pan, "pan", value, min_val, max_val)

    @property
    def tilt(self) -> int:
        """Camera tilt position (uses device range in degrees)."""
        return self._get_camera_property(CamProp.Tilt, "tilt")

    @tilt.setter  
    def tilt(self, value: int):
        """Set camera tilt using actual device range."""
        min_val, max_val = self._get_dynamic_range("tilt", -90, 90)
        self._set_camera_property(CamProp.Tilt, "tilt", value, min_val, max_val)

    @property
    def roll(self) -> int:
        """Camera roll rotation (uses device range in degrees)."""
        return self._get_camera_property(CamProp.Roll, "roll")

    @roll.setter
    def roll(self, value: int):
        """Set camera roll using actual device range."""
        min_val, max_val = self._get_dynamic_range("roll", -180, 180)
        self._set_camera_property(CamProp.Roll, "roll", value, min_val, max_val)

    @property
    def zoom(self) -> int:
        """Optical zoom level (uses device range)."""
        return self._get_camera_property(CamProp.Zoom, "zoom")

    @zoom.setter
    def zoom(self, value: int):
        """Set optical zoom using actual device range."""
        min_val, max_val = self._get_dynamic_range("zoom", 0, 100)
        self._set_camera_property(CamProp.Zoom, "zoom", value, min_val, max_val)

    @property
    def exposure(self) -> int:
        """Exposure time/shutter speed (uses device range)."""
        return self._get_camera_property(CamProp.Exposure, "exposure")

    @exposure.setter
    def exposure(self, value: int):
        """Set exposure using actual device range."""
        min_val, max_val = self._get_dynamic_range("exposure", -13, 1)
        self._set_camera_property(CamProp.Exposure, "exposure", value, min_val, max_val)

    @property
    def iris(self) -> int:
        """Aperture/iris diameter (uses device range)."""
        return self._get_camera_property(CamProp.Iris, "iris")

    @iris.setter
    def iris(self, value: int):
        """Set iris using actual device range."""
        min_val, max_val = self._get_dynamic_range("iris", 0, 100)
        self._set_camera_property(CamProp.Iris, "iris", value, min_val, max_val)

    @property
    def focus(self) -> int:
        """Focus distance position (uses device range)."""
        return self._get_camera_property(CamProp.Focus, "focus")

    @focus.setter
    def focus(self, value: int):
        """Set focus using actual device range."""
        min_val, max_val = self._get_dynamic_range("focus", 0, 100)
        self._set_camera_property(CamProp.Focus, "focus", value, min_val, max_val)

    @property
    def scan_mode(self) -> int:
        """Scan mode (progressive/interlaced, uses device range)."""
        return self._get_camera_property(CamProp.ScanMode, "scan_mode")

    @scan_mode.setter
    def scan_mode(self, value: int):
        """Set scan mode using actual device range."""
        min_val, max_val = self._get_dynamic_range("scan_mode", 0, 2)
        self._set_camera_property(CamProp.ScanMode, "scan_mode", value, min_val, max_val)

    @property
    def privacy(self) -> bool:
        """Privacy mode on/off."""
        return bool(self._get_camera_property(CamProp.Privacy, "privacy"))

    @privacy.setter
    def privacy(self, value: bool):
        """Set privacy mode (no range needed for bool)."""
        self._set_camera_property(CamProp.Privacy, "privacy", int(value))

    @property
    def digital_zoom(self) -> int:
        """Digital zoom level (uses device range)."""
        return self._get_camera_property(CamProp.DigitalZoom, "digital_zoom")

    @digital_zoom.setter
    def digital_zoom(self, value: int):
        """Set digital zoom using actual device range."""
        min_val, max_val = self._get_dynamic_range("digital_zoom", 100, 400)
        self._set_camera_property(CamProp.DigitalZoom, "digital_zoom", value, min_val, max_val)

    @property
    def backlight_compensation(self) -> int:
        """Camera-level backlight compensation (uses device range)."""
        return self._get_camera_property(CamProp.BacklightCompensation, "backlight_compensation")

    @backlight_compensation.setter
    def backlight_compensation(self, value: int):
        """Set backlight compensation using actual device range."""
        min_val, max_val = self._get_dynamic_range("backlight_compensation", 0, 100)
        self._set_camera_property(CamProp.BacklightCompensation, "backlight_compensation", value, min_val, max_val)

    # ========================================================================
    # RELATIVE MOVEMENT METHODS (For PTZ cameras)
    # ========================================================================

    def pan_relative(self, degrees: int):
        """Move pan by relative amount (degrees). No range validation needed."""
        self._set_camera_property(CamProp.PanRelative, "pan_relative", degrees)

    def tilt_relative(self, degrees: int):
        """Move tilt by relative amount (degrees). No range validation needed."""
        self._set_camera_property(CamProp.TiltRelative, "tilt_relative", degrees)

    def roll_relative(self, degrees: int):
        """Roll by relative amount (degrees). No range validation needed."""
        self._set_camera_property(CamProp.RollRelative, "roll_relative", degrees)

    def zoom_relative(self, steps: int):
        """Zoom by relative amount (steps). No range validation needed."""
        self._set_camera_property(CamProp.ZoomRelative, "zoom_relative", steps)

    def focus_relative(self, steps: int):
        """Focus by relative amount (steps). No range validation needed."""
        self._set_camera_property(CamProp.FocusRelative, "focus_relative", steps)

    def exposure_relative(self, steps: int):
        """Adjust exposure by relative amount (steps). No range validation needed."""
        self._set_camera_property(CamProp.ExposureRelative, "exposure_relative", steps)

    def iris_relative(self, steps: int):
        """Adjust iris by relative amount (steps). No range validation needed."""
        self._set_camera_property(CamProp.IrisRelative, "iris_relative", steps)

    def digital_zoom_relative(self, steps: int):
        """Digital zoom by relative amount (steps). No range validation needed."""
        self._set_camera_property(CamProp.DigitalZoomRelative, "digital_zoom_relative", steps)


    # ========================================================================
    # COMBINED CONTROL METHODS
    # ========================================================================
    
    def set_pan_tilt(self, pan_degrees: int, tilt_degrees: int):
        """Set both pan and tilt simultaneously."""
        self._ensure_connected()
        # Try combined control first
        try:
            pan_tilt_value = (pan_degrees << 16) | (tilt_degrees & 0xFFFF)
            self._set_camera_property(CamProp.PanTilt, "pan_tilt", pan_tilt_value)
        except (PropertyNotSupportedError, AttributeError):
            # Fallback to individual controls
            self.pan = pan_degrees
            self.tilt = tilt_degrees
    
    def pan_tilt_relative(self, pan_delta: int, tilt_delta: int):
        """Move pan and tilt by relative amounts."""
        self._ensure_connected()
        try:
            pan_tilt_value = (pan_delta << 16) | (tilt_delta & 0xFFFF)
            self._set_camera_property(CamProp.PanTiltRelative, "pan_tilt_relative", pan_tilt_value)
        except (PropertyNotSupportedError, AttributeError):
            # Fallback to individual relative moves
            self.pan_relative(pan_delta)
            self.tilt_relative(tilt_delta)

    # ========================================================================
    # INTERNAL PROPERTY HELPERS - ONLY USE CORE RESULT<T> API
    # ========================================================================
    
    def _get_video_property(self, prop, prop_name: str) -> int:
        """Get video property using core Result<T> API."""
        self._ensure_connected()
        try:
            result = self._core_camera.get(prop)
            if not result.is_ok():
                raise PropertyNotSupportedError(
                    f"Cannot get {prop_name}: {result.error().description()}"
                )
            return result.value().value
        except Exception as e:
            if isinstance(e, PropertyNotSupportedError):
                raise
            raise DuvcSystemError(f"Unexpected error reading {prop_name}: {e}")
    
    def _set_video_property(self, prop, prop_name: str, value: int, min_val: Optional[int] = None, max_val: Optional[int] = None) -> None:
        """Set video property using core Result<T> API."""
        self._ensure_connected()
        
        # Validate range
        if min_val is not None and value < min_val:
            raise InvalidValueError(f"{prop_name} must be >= {min_val}, got {value}")
        if max_val is not None and value > max_val:
            raise InvalidValueError(f"{prop_name} must be <= {max_val}, got {value}")
        
        try:
            setting = PropSetting(value, CamMode.Manual)
            result = self._core_camera.set(prop, setting)
            if not result.is_ok():
                raise PropertyNotSupportedError(
                    f"Cannot set {prop_name}: {result.error().description()}"
                )
        except Exception as e:
            if isinstance(e, (PropertyNotSupportedError, InvalidValueError)):
                raise
            raise DuvcSystemError(f"Unexpected error setting {prop_name}: {e}")
    
    def _get_camera_property(self, prop, prop_name: str) -> int:
        """Get camera property using core Result<T> API."""
        self._ensure_connected()
        try:
            result = self._core_camera.get(prop)
            if not result.is_ok():
                raise PropertyNotSupportedError(
                    f"Cannot get {prop_name}: {result.error().description()}"
                )
            return result.value().value
        except Exception as e:
            if isinstance(e, PropertyNotSupportedError):
                raise
            raise DuvcSystemError(f"Unexpected error reading {prop_name}: {e}")
    
    def _set_camera_property(self, prop, prop_name: str, value: int) -> None:
        """Set camera property using core Result<T> API."""
        self._ensure_connected()
        try:
            setting = PropSetting(value, CamMode.Manual)
            result = self._core_camera.set(prop, setting)
            if not result.is_ok():
                raise PropertyNotSupportedError(
                    f"Cannot set {prop_name}: {result.error().description()}"
                )
        except Exception as e:
            if isinstance(e, PropertyNotSupportedError):
                raise
            raise DuvcSystemError(f"Unexpected error setting {prop_name}: {e}")

    # ========================================================================
    # CONVENIENCE METHODS 
    # ========================================================================
    
    def reset_to_defaults(self):
        """Reset all supported properties to default/auto mode.
        
        Attempts to reset common properties. Warnings issued for unsupported
        properties; partial success does not raise exceptions.
        """
        self._ensure_connected()
        
        # List of common properties to reset to auto mode
        reset_properties = [
            # Video properties
            (VidProp.Brightness, CamMode.Auto, "brightness"),
            (VidProp.Contrast, CamMode.Auto, "contrast"),
            (VidProp.Saturation, CamMode.Auto, "saturation"),
            (VidProp.Hue, CamMode.Auto, "hue"),
            (VidProp.Sharpness, CamMode.Auto, "sharpness"),
            (VidProp.WhiteBalance, CamMode.Auto, "white_balance"),
            (VidProp.Gain, CamMode.Auto, "gain"),
            
            # Camera properties
            (CamProp.Exposure, CamMode.Auto, "exposure"),
            (CamProp.Focus, CamMode.Auto, "focus"),
            (CamProp.Iris, CamMode.Auto, "iris"),
            (CamProp.Pan, CamMode.Auto, "pan"),
            (CamProp.Tilt, CamMode.Auto, "tilt"),
            (CamProp.Zoom, CamMode.Auto, "zoom"),
        ]
        
        failed_props = []
        success_count = 0
        
        for prop, mode, name in reset_properties:
            try:
                # Try to get the range first to set to default value
                range_result = self._core_camera.get_range(prop)
                if range_result.is_ok():
                    range_info = range_result.value()
                    # Use the default value from range if available
                    setting = PropSetting(getattr(range_info, 'default', 0), mode)
                else:
                    # Fallback to auto mode with value 0
                    setting = PropSetting(0, mode)
                
                result = self._core_camera.set(prop, setting)
                if result.is_ok():
                    success_count += 1
                else:
                    failed_props.append(name)
                    
            except Exception:
                failed_props.append(name)
        
        if failed_props:
            warnings.warn(
                f"Reset completed with {success_count} properties successful. "
                f"Could not reset: {', '.join(failed_props)} "
                f"(these properties may not be supported by your camera)"
            )
    
    def center_camera(self):
        """Move pan/tilt to center position.
        
        Calculates center point as (min + max) / 2 for each axis.
        Warnings issued if pan/tilt not supported or centering fails.
        """
        self._ensure_connected()
        
        centered_count = 0
        failed_props = []
        
        # Center pan
        try:
            pan_range_result = self._core_camera.get_range(CamProp.Pan)
            if pan_range_result.is_ok():
                pan_range = pan_range_result.value()
                center_pan = (pan_range.min + pan_range.max) // 2
                self.pan = center_pan
                centered_count += 1
            else:
                failed_props.append("pan")
        except Exception:
            failed_props.append("pan")
        
        # Center tilt
        try:
            tilt_range_result = self._core_camera.get_range(CamProp.Tilt)
            if tilt_range_result.is_ok():
                tilt_range = tilt_range_result.value()
                center_tilt = (tilt_range.min + tilt_range.max) // 2
                self.tilt = center_tilt
                centered_count += 1
            else:
                failed_props.append("tilt")
        except Exception:
            failed_props.append("tilt")
        
        if failed_props:
            if centered_count > 0:
                warnings.warn(f"Partially centered camera. Could not center: {', '.join(failed_props)}")
            else:
                warnings.warn("Could not center camera - pan/tilt controls may not be supported")
    
    def get_supported_properties(self) -> Dict[str, List[str]]:
        """Test each property to determine which are supported by this device.
        
        Returns:
            Dict with 'camera' and 'video' keys listing supported property names
        """
        self._ensure_connected()
        
        supported = {
            'camera': [],
            'video': []
        }
        
        # Test camera properties
        camera_props = [
            (CamProp.Pan, "pan"),
            (CamProp.Tilt, "tilt"),
            (CamProp.Roll, "roll"),
            (CamProp.Zoom, "zoom"),
            (CamProp.Exposure, "exposure"),
            (CamProp.Iris, "iris"),
            (CamProp.Focus, "focus"),
            (CamProp.ScanMode, "scan_mode"),
            (CamProp.Privacy, "privacy"),
            (CamProp.DigitalZoom, "digital_zoom"),
            (CamProp.BacklightCompensation, "backlight_compensation"),
        ]
        
        for prop, name in camera_props:
            try:
                result = self._core_camera.get(prop)
                if result.is_ok():
                    supported['camera'].append(name)
            except Exception:
                pass
        
        # Test video properties
        video_props = [
            (VidProp.Brightness, "brightness"),
            (VidProp.Contrast, "contrast"),
            (VidProp.Hue, "hue"),
            (VidProp.Saturation, "saturation"),
            (VidProp.Sharpness, "sharpness"),
            (VidProp.Gamma, "gamma"),
            (VidProp.ColorEnable, "color_enable"),
            (VidProp.WhiteBalance, "white_balance"),
            (VidProp.BacklightCompensation, "video_backlight_compensation"),
            (VidProp.Gain, "gain"),
        ]
        
        for prop, name in video_props:
            try:
                result = self._core_camera.get(prop)
                if result.is_ok():
                    supported['video'].append(name)
            except Exception:
                pass
        
        return supported
    
    def get_property_range(self, property_name: str) -> Optional[Dict[str, int]]:
        """Get valid range and constraints for a property.
        
        Args:
            property_name: Property name (e.g., 'brightness', 'pan')
            
        Returns:
            Dict with 'min', 'max', 'step', 'default' keys, or None if unsupported
            
        Raises:
            ValueError: If property name not recognized
        """
        self._ensure_connected()
        
        # Map property names to enums
        prop_map = {
            # Video properties
            'brightness': VidProp.Brightness,
            'contrast': VidProp.Contrast,
            'hue': VidProp.Hue,
            'saturation': VidProp.Saturation,
            'sharpness': VidProp.Sharpness,
            'gamma': VidProp.Gamma,
            'color_enable': VidProp.ColorEnable,
            'white_balance': VidProp.WhiteBalance,
            'video_backlight_compensation': VidProp.BacklightCompensation,
            'gain': VidProp.Gain,
            
            # Camera properties
            'pan': CamProp.Pan,
            'tilt': CamProp.Tilt,
            'roll': CamProp.Roll,
            'zoom': CamProp.Zoom,
            'exposure': CamProp.Exposure,
            'iris': CamProp.Iris,
            'focus': CamProp.Focus,
            'scan_mode': CamProp.ScanMode,
            'privacy': CamProp.Privacy,
            'digital_zoom': CamProp.DigitalZoom,
            'backlight_compensation': CamProp.BacklightCompensation,
        }
        
        if property_name not in prop_map:
            raise ValueError(f"Unknown property: {property_name}")
        
        try:
            result = self._core_camera.get_range(prop_map[property_name])
            if not result.is_ok():
                return None
            
            range_info = result.value()
            return {
                'min': range_info.min,
                'max': range_info.max,
                'step': range_info.step,
                'default': getattr(range_info, 'default', 0)
            }
        except Exception:
            return None

    # ========================================================================
    # DEVICE INFORMATION PROPERTIES  
    # ========================================================================
    
    @property
    def device_name(self) -> str:
        """Get device name."""
        return self._device.name if self._device else "Unknown"
    
    @property
    def device_path(self) -> str:
        """Get device path."""
        return self._device.path if self._device else ""
    
    @property
    def is_connected(self) -> bool:
        """Check if camera is connected and actually responsive.
        
        Returns:
            True if camera is connected and responding to basic operations
        """
        # Quick checks first
        with self._lock:
            if self._is_closed or self._core_camera is None or self._device is None:
                return False
            
            # Check if core camera reports as valid
            try:
                if not self._core_camera.is_valid():
                    return False
            except Exception:
                return False
            
            # Quick responsiveness test - try a simple get operation
            try:
                test_result = self._core_camera.get(VidProp.Brightness)
                # Don't care if property is supported, just that camera responds
                return True  # Camera responded, even if property not supported
            except Exception:
                # Camera didn't respond to basic operation
                return False
 
    # Access to core API for advanced users
    @property
    def core(self) -> CoreCamera:
        """Access underlying core Camera for Result<T> operations.
        
        Returns core Camera object for advanced use cases requiring
        explicit Result<T> error handling.
        """
        self._ensure_connected()
        return self._core_camera
    
    def __repr__(self):
        """String representation of the camera controller."""
        status = "connected" if self.is_connected else "disconnected"
        return f"CameraController(device='{self.device_name}', {status})"
    
    def __str__(self):
        """User-friendly string representation."""
        return self.__repr__()

    # ========================================================================
    # PROPERTY MAPPINGS (Internal)
    # ========================================================================

    # Property mapping constants
    _VIDEO_PROPERTIES = {
        'brightness': VidProp.Brightness,
        'contrast': VidProp.Contrast,
        'hue': VidProp.Hue,
        'saturation': VidProp.Saturation,
        'sharpness': VidProp.Sharpness,
        'gamma': VidProp.Gamma,
        'color_enable': VidProp.ColorEnable,
        'white_balance': VidProp.WhiteBalance,
        'video_backlight_compensation': VidProp.BacklightCompensation,
        'gain': VidProp.Gain,
        # Aliases
        'wb': VidProp.WhiteBalance,
        'color': VidProp.ColorEnable,
        'sat': VidProp.Saturation,
        'bright': VidProp.Brightness,
    }

    _CAMERA_PROPERTIES = {
        'pan': CamProp.Pan,
        'tilt': CamProp.Tilt,
        'roll': CamProp.Roll,
        'zoom': CamProp.Zoom,
        'exposure': CamProp.Exposure,
        'iris': CamProp.Iris,
        'focus': CamProp.Focus,
        'scan_mode': CamProp.ScanMode,
        'privacy': CamProp.Privacy,
        'digital_zoom': CamProp.DigitalZoom,
        'backlight_compensation': CamProp.BacklightCompensation,
        # Aliases
        'z': CamProp.Zoom,
        'f': CamProp.Focus,
        'exp': CamProp.Exposure,
        'horizontal': CamProp.Pan,
        'vertical': CamProp.Tilt,
    }

    _BOOLEAN_PROPERTIES = {'color_enable', 'colorenable', 'color', 'privacy'}

    def set(self, property_name: str, value: Union[int, bool, str], mode: str = "manual") -> None:
        """Set property by name.
        
        Args:
            property_name: Property name (e.g., 'brightness', 'pan', 'focus')
            value: Value (int/bool) or "auto" for auto mode
            mode: "manual" or "auto" (ignored if value is "auto")
            
        Raises:
            ValueError: If property name unknown
            PropertyNotSupportedError: If property not supported by device
        """
        self._ensure_connected()
        
        # Handle "auto" value
        if isinstance(value, str) and value.lower() == "auto":
            return self._set_property_auto(property_name)
        
        # Parse mode string
        parsed_mode = self._parse_mode_string(mode, property_name)
        
        # Set property using internal methods
        if property_name in self._VIDEO_PROPERTIES:
            prop_enum = self._VIDEO_PROPERTIES[property_name]
            setting = PropSetting(int(value), parsed_mode)
            result = self._core_camera.set(prop_enum, setting)
            if not result.is_ok():
                raise PropertyNotSupportedError(
                    f"Cannot set {property_name}: {result.error().description()}"
                )
        elif property_name in self._CAMERA_PROPERTIES:
            prop_enum = self._CAMERA_PROPERTIES[property_name]
            setting = PropSetting(int(value), parsed_mode)
            result = self._core_camera.set(prop_enum, setting)
            if not result.is_ok():
                raise PropertyNotSupportedError(
                    f"Cannot set {property_name}: {result.error().description()}"
                )
        else:
            available = list(self._VIDEO_PROPERTIES.keys()) + list(self._CAMERA_PROPERTIES.keys())
            raise ValueError(f"Unknown property '{property_name}'. Available: {', '.join(available)}")

    def get(self, property_name: str) -> Union[int, bool]:
        """Get property value by name.
        
        Args:
            property_name: Property name (e.g., 'brightness', 'pan')
            
        Returns:
            Current value (bool for color_enable/privacy, int otherwise)
            
        Raises:
            ValueError: If property name unknown
            PropertyNotSupportedError: If property not supported by device
        """

        self._ensure_connected()
        
        if property_name in self._VIDEO_PROPERTIES:
            prop_enum = self._VIDEO_PROPERTIES[property_name]
            result = self._core_camera.get(prop_enum)
            if not result.is_ok():
                raise PropertyNotSupportedError(f"Cannot get {property_name}: {result.error().description()}")
            value = result.value().value
            # Convert to bool for boolean properties to match property descriptors
            return bool(value) if property_name in self._BOOLEAN_PROPERTIES else value
        elif property_name in self._CAMERA_PROPERTIES:
            prop_enum = self._CAMERA_PROPERTIES[property_name]
            result = self._core_camera.get(prop_enum)
            if not result.is_ok():
                raise PropertyNotSupportedError(f"Cannot get {property_name}: {result.error().description()}")
            value = result.value().value
            # Convert to bool for boolean properties to match property descriptors
            return bool(value) if property_name in self._BOOLEAN_PROPERTIES else value
        else:
            available = list(self._VIDEO_PROPERTIES.keys()) + list(self._CAMERA_PROPERTIES.keys())
            raise ValueError(f"Unknown property '{property_name}'. Available: {', '.join(available)}")


    def _parse_mode_string(self, mode: str, property_name: str) -> Union[CamMode, CamMode]:
        """Convert mode string to CamMode enum.
        
        Args:
            mode: Mode string ("manual", "auto", "a", "m", "automatic")
            property_name: Property name (for error messages)
            
        Returns:
            CamMode enum value
            
        Raises:
            ValueError: If mode string not recognized
        """
        mode_lower = mode.lower().strip()
        
        # Determine if this is a video or camera property
        is_video_property = property_name in self._VIDEO_PROPERTIES
        
        mode_mapping = {
            'manual': CamMode.Manual if is_video_property else CamMode.Manual,
            'auto': CamMode.Auto if is_video_property else CamMode.Auto,
            'automatic': CamMode.Auto if is_video_property else CamMode.Auto,
            'm': CamMode.Manual if is_video_property else CamMode.Manual,
            'a': CamMode.Auto if is_video_property else CamMode.Auto,
        }
        
        if mode_lower not in mode_mapping:
            available_modes = list(mode_mapping.keys())
            raise ValueError(
                f"Invalid mode '{mode}' for {property_name}. "
                f"Available modes: {', '.join(available_modes)}"
            )
        
        return mode_mapping[mode_lower]

    def _set_property_auto(self, property_name: str) -> None:
        """Set property to auto mode."""
        if property_name in self._VIDEO_PROPERTIES:
            prop_enum = self._VIDEO_PROPERTIES[property_name]
            setting = PropSetting(0, CamMode.Auto)  # Value ignored in auto mode
            result = self._core_camera.set(prop_enum, setting)
        elif property_name in self._CAMERA_PROPERTIES:
            prop_enum = self._CAMERA_PROPERTIES[property_name]
            setting = PropSetting(0, CamMode.Auto)  # Value ignored in auto mode
            result = self._core_camera.set(prop_enum, setting)
        else:
            available = list(self._VIDEO_PROPERTIES.keys()) + list(self._CAMERA_PROPERTIES.keys())
            raise ValueError(f"Unknown property '{property_name}'. Available: {', '.join(available)}")
        
        if not result.is_ok():
            raise PropertyNotSupportedError(
                f"Cannot set {property_name} to auto: {result.error().description()}"
            )

    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================
    
    def set_multiple(self, properties: Dict[str, Union[int, str]], verbose: bool = False) -> Dict[str, bool]:
        """Set multiple properties at once.
        
        Args:
            properties: Dict mapping property names to values
            verbose: If True, warn about failed properties
            
        Returns:
            Dict mapping property names to success status
        """
        self._ensure_connected()
        
        results = {}
        failed_properties = []
        
        for prop_name, value in properties.items():
            try:
                self.set(prop_name, value)
                results[prop_name] = True
            except Exception as e:
                results[prop_name] = False
                failed_properties.append((prop_name, str(e)))
        
        # Provide feedback for failed properties if requested
        if verbose and failed_properties:
            warnings.warn(
                f"Some properties failed to set: " + 
                ", ".join(f"{prop} ({error})" for prop, error in failed_properties)
            )
        
        return results
    
    def get_multiple(self, properties: List[str]) -> Dict[str, Union[int, bool]]:
        """Get multiple properties at once.
        
        Args:
            properties: List of property names to retrieve
            
        Returns:
            Dict mapping property names to values. Unsupported properties omitted.
        """
        self._ensure_connected()
        
        results = {}
        
        for prop_name in properties:
            try:
                value = self.get(prop_name)
                results[prop_name] = value
            except Exception:
                # Skip properties that can't be read (not supported, etc.)
                # This keeps the method simple and forgiving
                pass
        
        return results

    # ========================================================================
    # PRESETS
    # ========================================================================


    def apply_preset(self, preset_name: str) -> bool:
        """Apply a preset configuration.
        
        Args:
            preset_name: Built-in ('daylight', 'indoor', 'night', 'conference') or custom preset name
            
        Returns:
            True if all properties set successfully
            
        Raises:
            ValueError: If preset not found
        """
        
        # Check custom presets first
        if hasattr(self, '_custom_presets') and preset_name in self._custom_presets:
            results = self.set_multiple(self._custom_presets[preset_name])
            return all(results.values())
        
        # Check built-in presets using class constants
        if preset_name not in self.BUILT_IN_PRESETS:
            available = list(self.BUILT_IN_PRESETS.keys())
            if hasattr(self, '_custom_presets'):
                available.extend(self._custom_presets.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {', '.join(available)}")
        
        results = self.set_multiple(self.BUILT_IN_PRESETS[preset_name])
        return all(results.values())

    def set_smart_default(self, property_name: str) -> None:
        """Set property to intelligent default based on property type."""
        
        if property_name in self._SMART_DEFAULTS:
            self.set(property_name, self._SMART_DEFAULTS[property_name])
        else:
            # Fallback to auto mode for unknown properties
            self.set(property_name, 'auto')


    def get_preset_names(self) -> List[str]:
        """Get list of all available presets (built-in and custom).
        
        Returns:
            List of preset names
        """
        built_in = ['daylight', 'indoor', 'night', 'conference']
        
        if hasattr(self, '_custom_presets'):
            custom = list(self._custom_presets.keys())
            return built_in + custom
        
        return built_in


    def create_custom_preset(self, name: str, properties: Dict[str, Union[int, str]]) -> None:
        """Create a custom preset configuration.
        
        Args:
            name: Preset name
            properties: Dict mapping property names to values
        """
        if not hasattr(self, '_custom_presets'):
            self._custom_presets = {}
        
        self._custom_presets[name] = properties.copy()


    def get_custom_presets(self) -> Dict[str, Dict[str, Union[int, str]]]:
        """Get all custom presets.
        
        Returns:
            Dict mapping preset names to their property dicts
        """
        if not hasattr(self, '_custom_presets'):
            self._custom_presets = {}
        
        return self._custom_presets.copy()


    def delete_custom_preset(self, name: str) -> bool:
        """Delete a custom preset.
        
        Args:
            name: Preset name to delete
            
        Returns:
            True if deleted, False if not found
        """
        if not hasattr(self, '_custom_presets'):
            return False
        
        if name in self._custom_presets:
            del self._custom_presets[name]
            return True
        
        return False


    def clear_custom_presets(self) -> int:
        """Clear all custom presets.
        
        Returns:
            Number of presets cleared
        """
        if not hasattr(self, '_custom_presets'):
            return 0
        
        count = len(self._custom_presets)
        self._custom_presets.clear()
        return count

    def apply_preset(self, preset_name: str) -> bool:
        """Apply a preset configuration (built-in or custom).
        
        Args:
            preset_name: Preset name ('daylight', 'indoor', 'night', 'conference', or custom)
            
        Returns:
            True if all properties set successfully
            
        Raises:
            ValueError: If preset not found
        """
        # Built-in presets
        presets = {
            'daylight': {
                'brightness': 60,
                'contrast': 50,
                'white_balance': 'auto',
                'exposure': 'auto'
            },
            'indoor': {
                'brightness': 75,
                'contrast': 60,
                'white_balance': 3200,
                'exposure': 'auto'
            },
            'night': {
                'brightness': 80,
                'contrast': 70,
                'gain': 80,
                'exposure': 'auto'
            },
            'conference': {
                'brightness': 70,
                'contrast': 55,
                'white_balance': 'auto',
                'pan': 0,
                'tilt': 0,
                'zoom': 100
            }
        }
        
        # Check custom presets first
        if hasattr(self, '_custom_presets') and preset_name in self._custom_presets:
            results = self.set_multiple(self._custom_presets[preset_name])
            return all(results.values())
        
        # Check built-in presets
        if preset_name not in presets:
            available = list(presets.keys())
            if hasattr(self, '_custom_presets'):
                available.extend(self._custom_presets.keys())
            raise ValueError(f"Unknown preset '{preset_name}'. Available: {', '.join(available)}")
        
        results = self.set_multiple(presets[preset_name])
        return all(results.values())


    # ========================================================================
    # CONVENIENCE DIRECT SETTER METHODS
    # ========================================================================
    # These methods are provided for backwards compatibility and convenience.
    # They all delegate to the main set() method but provide IDE autocomplete
    # and explicit method names for all supported properties.

    # VIDEO PROPERTIES (VidProp) - Image processing and color adjustment
    def set_brightness(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set brightness - convenience shortcut for set('brightness', value).
        
        Args:
            value: Brightness value (0-100) or 'auto'
            mode: Control mode ('manual' or 'auto')
        
        Example:
            cam.set_brightness(80)      # Same as cam.set('brightness', 80)
            cam.set_brightness('auto')  # Same as cam.set('brightness', 'auto')
        """
        self.set('brightness', value, mode)

    def set_contrast(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set contrast - convenience shortcut for set('contrast', value)."""
        self.set('contrast', value, mode)

    def set_hue(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set hue - convenience shortcut for set('hue', value)."""
        self.set('hue', value, mode)

    def set_saturation(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set saturation - convenience shortcut for set('saturation', value)."""
        self.set('saturation', value, mode)

    def set_sharpness(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set sharpness - convenience shortcut for set('sharpness', value)."""
        self.set('sharpness', value, mode)

    def set_gamma(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set gamma - convenience shortcut for set('gamma', value)."""
        self.set('gamma', value, mode)

    def set_color_enable(self, value: Union[int, bool, str], mode: str = "manual") -> None:
        """Set color enable - convenience shortcut for set('color_enable', value)."""
        self.set('color_enable', value, mode)

    def set_white_balance(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set white balance - convenience shortcut for set('white_balance', value)."""
        self.set('white_balance', value, mode)

    def set_backlight_compensation(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set backlight compensation - convenience shortcut for set('backlight_compensation', value)."""
        self.set('backlight_compensation', value, mode)

    def set_gain(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set gain - convenience shortcut for set('gain', value)."""
        self.set('gain', value, mode)

    # CAMERA PROPERTIES (CamProp) - Physical camera movement and capture settings
    def set_pan(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set pan position - convenience shortcut for set('pan', value)."""
        self.set('pan', value, mode)

    def set_tilt(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set tilt position - convenience shortcut for set('tilt', value)."""
        self.set('tilt', value, mode)

    def set_roll(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set roll rotation - convenience shortcut for set('roll', value)."""
        self.set('roll', value, mode)

    def set_zoom(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set zoom level - convenience shortcut for set('zoom', value)."""
        self.set('zoom', value, mode)

    def set_exposure(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set exposure time - convenience shortcut for set('exposure', value)."""
        self.set('exposure', value, mode)

    def set_iris(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set iris/aperture - convenience shortcut for set('iris', value)."""
        self.set('iris', value, mode)

    def set_focus(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set focus position - convenience shortcut for set('focus', value)."""
        self.set('focus', value, mode)

    def set_scan_mode(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set scan mode - convenience shortcut for set('scan_mode', value)."""
        self.set('scan_mode', value, mode)

    def set_privacy(self, value: Union[int, bool, str], mode: str = "manual") -> None:
        """Set privacy mode - convenience shortcut for set('privacy', value)."""
        self.set('privacy', value, mode)

    def set_pan_relative(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set relative pan movement - convenience shortcut for set('pan_relative', value)."""
        self.set('pan_relative', value, mode)

    def set_tilt_relative(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set relative tilt movement - convenience shortcut for set('tilt_relative', value)."""
        self.set('tilt_relative', value, mode)

    def set_roll_relative(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set relative roll movement - convenience shortcut for set('roll_relative', value)."""
        self.set('roll_relative', value, mode)

    def set_zoom_relative(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set relative zoom adjustment - convenience shortcut for set('zoom_relative', value)."""
        self.set('zoom_relative', value, mode)

    def set_exposure_relative(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set relative exposure adjustment - convenience shortcut for set('exposure_relative', value)."""
        self.set('exposure_relative', value, mode)

    def set_iris_relative(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set relative iris adjustment - convenience shortcut for set('iris_relative', value)."""
        self.set('iris_relative', value, mode)

    def set_focus_relative(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set relative focus adjustment - convenience shortcut for set('focus_relative', value)."""
        self.set('focus_relative', value, mode)

    def set_pan_tilt(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set combined pan/tilt - convenience shortcut for set('pan_tilt', value)."""
        self.set('pan_tilt', value, mode)

    def set_pan_tilt_relative(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set relative pan/tilt movement - convenience shortcut for set('pan_tilt_relative', value)."""
        self.set('pan_tilt_relative', value, mode)

    def set_focus_simple(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set simple focus control - convenience shortcut for set('focus_simple', value)."""
        self.set('focus_simple', value, mode)

    def set_digital_zoom(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set digital zoom - convenience shortcut for set('digital_zoom', value)."""
        self.set('digital_zoom', value, mode)

    def set_digital_zoom_relative(self, value: Union[int, str], mode: str = "manual") -> None:
        """Set relative digital zoom - convenience shortcut for set('digital_zoom_relative', value)."""
        self.set('digital_zoom_relative', value, mode)

    def set_lamp(self, value: Union[int, bool, str], mode: str = "manual") -> None:
        """Set camera lamp/LED - convenience shortcut for set('lamp', value)."""
        self.set('lamp', value, mode)

    # ========================================================================
    # DIRECT GETTER METHODS - Convenience shortcuts for common operations
    # ========================================================================

    # VIDEO PROPERTIES GETTERS
    def get_brightness(self) -> Union[int, bool]:
        """Get brightness - convenience shortcut for get('brightness')."""
        return self.get('brightness')

    def get_contrast(self) -> Union[int, bool]:
        """Get contrast - convenience shortcut for get('contrast')."""
        return self.get('contrast')

    def get_hue(self) -> Union[int, bool]:
        """Get hue - convenience shortcut for get('hue')."""
        return self.get('hue')

    def get_saturation(self) -> Union[int, bool]:
        """Get saturation - convenience shortcut for get('saturation')."""
        return self.get('saturation')

    def get_sharpness(self) -> Union[int, bool]:
        """Get sharpness - convenience shortcut for get('sharpness')."""
        return self.get('sharpness')

    def get_gamma(self) -> Union[int, bool]:
        """Get gamma - convenience shortcut for get('gamma')."""
        return self.get('gamma')

    def get_color_enable(self) -> Union[int, bool]:
        """Get color enable - convenience shortcut for get('color_enable')."""
        return self.get('color_enable')

    def get_white_balance(self) -> Union[int, bool]:
        """Get white balance - convenience shortcut for get('white_balance')."""
        return self.get('white_balance')

    def get_backlight_compensation(self) -> Union[int, bool]:
        """Get backlight compensation - convenience shortcut for get('backlight_compensation')."""
        return self.get('backlight_compensation')

    def get_gain(self) -> Union[int, bool]:
        """Get gain - convenience shortcut for get('gain')."""
        return self.get('gain')

    # CAMERA PROPERTIES GETTERS
    def get_pan(self) -> Union[int, bool]:
        """Get pan position - convenience shortcut for get('pan')."""
        return self.get('pan')

    def get_tilt(self) -> Union[int, bool]:
        """Get tilt position - convenience shortcut for get('tilt')."""
        return self.get('tilt')

    def get_roll(self) -> Union[int, bool]:
        """Get roll rotation - convenience shortcut for get('roll')."""
        return self.get('roll')

    def get_zoom(self) -> Union[int, bool]:
        """Get zoom level - convenience shortcut for get('zoom')."""
        return self.get('zoom')

    def get_exposure(self) -> Union[int, bool]:
        """Get exposure time - convenience shortcut for get('exposure')."""
        return self.get('exposure')

    def get_iris(self) -> Union[int, bool]:
        """Get iris/aperture - convenience shortcut for get('iris')."""
        return self.get('iris')

    def get_focus(self) -> Union[int, bool]:
        """Get focus position - convenience shortcut for get('focus')."""
        return self.get('focus')

    def get_scan_mode(self) -> Union[int, bool]:
        """Get scan mode - convenience shortcut for get('scan_mode')."""
        return self.get('scan_mode')

    def get_privacy(self) -> Union[int, bool]:
        """Get privacy mode - convenience shortcut for get('privacy')."""
        return self.get('privacy')

    def get_pan_relative(self) -> Union[int, bool]:
        """Get relative pan movement - convenience shortcut for get('pan_relative')."""
        return self.get('pan_relative')

    def get_tilt_relative(self) -> Union[int, bool]:
        """Get relative tilt movement - convenience shortcut for get('tilt_relative')."""
        return self.get('tilt_relative')

    def get_roll_relative(self) -> Union[int, bool]:
        """Get relative roll movement - convenience shortcut for get('roll_relative')."""
        return self.get('roll_relative')

    def get_zoom_relative(self) -> Union[int, bool]:
        """Get relative zoom adjustment - convenience shortcut for get('zoom_relative')."""
        return self.get('zoom_relative')

    def get_exposure_relative(self) -> Union[int, bool]:
        """Get relative exposure adjustment - convenience shortcut for get('exposure_relative')."""
        return self.get('exposure_relative')

    def get_iris_relative(self) -> Union[int, bool]:
        """Get relative iris adjustment - convenience shortcut for get('iris_relative')."""
        return self.get('iris_relative')

    def get_focus_relative(self) -> Union[int, bool]:
        """Get relative focus adjustment - convenience shortcut for get('focus_relative')."""
        return self.get('focus_relative')

    def get_pan_tilt(self) -> Union[int, bool]:
        """Get combined pan/tilt - convenience shortcut for get('pan_tilt')."""
        return self.get('pan_tilt')

    def get_pan_tilt_relative(self) -> Union[int, bool]:
        """Get relative pan/tilt movement - convenience shortcut for get('pan_tilt_relative')."""
        return self.get('pan_tilt_relative')

    def get_focus_simple(self) -> Union[int, bool]:
        """Get simple focus control - convenience shortcut for get('focus_simple')."""
        return self.get('focus_simple')

    def get_digital_zoom(self) -> Union[int, bool]:
        """Get digital zoom - convenience shortcut for get('digital_zoom')."""
        return self.get('digital_zoom')

    def get_digital_zoom_relative(self) -> Union[int, bool]:
        """Get relative digital zoom - convenience shortcut for get('digital_zoom_relative')."""
        return self.get('digital_zoom_relative')

    def get_lamp(self) -> Union[int, bool]:
        """Get camera lamp/LED - convenience shortcut for get('lamp')."""
        return self.get('lamp')

    # ========================================================================
    # END DIRECT METHODS
    # ========================================================================

    def list_properties(self) -> List[str]:
        """Get all available property names for device.
        
        Returns:
            Sorted list of property names
        """
        return sorted(list(self._VIDEO_PROPERTIES.keys()) + list(self._CAMERA_PROPERTIES.keys()))

    def get_property_aliases(self) -> Dict[str, List[str]]:
        """Get mapping of property names to their aliases.
        
        Returns:
            Dict mapping canonical names to all accepted names
        """
        aliases = {
            'brightness': ['brightness', 'bright'],
            'white_balance': ['white_balance', 'wb', 'whitebalance'],
            'color_enable': ['color_enable', 'color'],
            'saturation': ['saturation', 'sat'],
            'zoom': ['zoom', 'z'],
            'focus': ['focus', 'f'], 
            'exposure': ['exposure', 'exp'],
            'pan': ['pan', 'horizontal'],
            'tilt': ['tilt', 'vertical'],
        }
        return aliases

    def set_with_validation(self, property_name: str, value: Union[int, bool, str], mode: str = "manual") -> None:
        """Set property with comprehensive validation and helpful errors.
        
        Args:
            property_name: Property name
            value: Property value or "auto"
            mode: Control mode
            
        Raises:
            ValueError: If property name or value is invalid
            PropertyNotSupportedError: If property not supported by camera
        """
        self._ensure_connected()
        
        # Handle "auto" value
        if isinstance(value, str) and value.lower() == "auto":
            return self._set_property_auto(property_name)
        
        # Get property range for validation
        range_info = self.get_property_range(property_name)
        if range_info:
            min_val, max_val = range_info['min'], range_info['max']
            
            if not isinstance(value, (int, bool)):
                raise ValueError(
                    f"Invalid value type for {property_name}: expected int or bool, got {type(value).__name__}. "
                    f"Valid range: {min_val} to {max_val}, or use 'auto'"
                )
            
            int_value = int(value)
            if int_value < min_val or int_value > max_val:
                current_val = self.get(property_name)
                from .exceptions import PropertyValueOutOfRangeError
                raise PropertyValueOutOfRangeError(
                    property_name, int_value, min_val, max_val, 
                    current_val, range_info.get('step', 1)
                )
        
        # Use the regular set method
        self.set(property_name, value, mode)

    # ========================================================================
    # CONNECTION RESOURCE MANAGEMENT
    # ========================================================================
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection status and device information.
        
        Returns:
            Dict with device name, path, connection status, and health
        """
        self._ensure_connected()
        
        # Test basic camera operations to verify health
        health_ok = True
        last_error = None
        
        try:
            # Test a simple get operation to verify camera is responsive
            test_result = self._core_camera.get(VidProp.Brightness)
            if not test_result.is_ok():
                health_ok = False
                last_error = test_result.error().description()
        except Exception as e:
            health_ok = False
            last_error = str(e)
        
        return {
            'device_name': self._device.name if self._device else 'Unknown',
            'device_path': self._device.path if self._device else 'Unknown',
            'is_connected': self.is_connected,
            'health_status': 'healthy' if health_ok else 'degraded',
            'last_error': last_error,
            'connection_method': getattr(self, '_connection_method', 'auto')
        }
    
    def test_connection_health(self) -> bool:
        """Test if the camera connection is healthy and responsive.
        
        Returns:
            True if connection is healthy, False otherwise
            
        Note:
            This is more thorough than is_connected - tests multiple operations
        """
        if not self.is_connected:
            return False
        
        try:
            # Test multiple operations to ensure camera is fully functional
            test_props = [VidProp.Brightness, VidProp.Contrast]
            
            for prop in test_props:
                try:
                    result = self._core_camera.get(prop)
                    # If camera responds (even with error), it's alive
                    # We don't require the property to be supported
                    pass
                except Exception:
                    # Camera didn't respond to this property at all
                    return False
            
            return True
            
        except Exception:
            return False

    
    def reconnect(self) -> bool:
        """Attempt to reconnect to the same device.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        with self._lock:
            if not self._device:
                return False
            
            # Close current connection
            self.close()
            
            try:
                # Attempt to reconnect
                self._connect(device_name=self._device.name)
                return self.is_connected
            except Exception:
                return False
    
    def close_with_validation(self) -> Dict[str, Any]:
        """Close connection with validation and cleanup report.
        
        Returns:
            Dict with cleanup details
        """
        cleanup_info = {
            'was_connected': self.is_connected,
            'cleanup_successful': False,
            'errors': []
        }
        
        try:
            if self.is_connected:
                # Test connection before closing
                health = self.test_connection_health()
                cleanup_info['pre_close_health'] = health
            
            # Standard close
            self.close()
            cleanup_info['cleanup_successful'] = True
            
        except Exception as e:
            cleanup_info['errors'].append(str(e))
        
        # Verify cleanup
        cleanup_info['post_close_connected'] = self.is_connected
        
        return cleanup_info

# ========================================================================
# CONTEXT MANAGER
# ========================================================================

class DeviceContextManager:
    """Context manager for direct core Camera access with proper cleanup."""    
    
    def __init__(self, device: Device):
        self._device = device
        self._camera = None
        self._is_closed = False
    
    def __enter__(self) -> CoreCamera:
        if self._is_closed:
            raise RuntimeError("Cannot reuse closed DeviceContextManager")
            
        result = open_camera(self._device)
        if not result.is_ok():
            raise RuntimeError(f"Failed to open camera: {result.error().description()}")
        self._camera = result.value()
        return self._camera
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._is_closed and self._camera is not None:
            # Camera cleanup is handled by C++ side when reference is released
            self._camera = None
            self._is_closed = True
    
    @property
    def is_closed(self) -> bool:
        """Check if context manager has been closed."""
        return self._is_closed


def open_device_context(device: Device) -> DeviceContextManager:
    """Create context manager for direct core Camera access.
    
    Args:
        device: Device to connect to
        
    Returns:
        Context manager yielding core Camera object
    """
    return DeviceContextManager(device)


def open_device_by_name_context(device_name: str) -> DeviceContextManager:
    """Create context manager for device access by name.
    
    Args:
        device_name: Device name or partial match (case-insensitive)
        
    Returns:
        Context manager yielding core Camera object
        
    Raises:
        DeviceNotFoundError: If no matching device found
    """
    devices = list_devices()
    
    for device in devices:
        if device_name.lower() in device.name.lower():
            return DeviceContextManager(device)
    
    from .exceptions import DeviceNotFoundError
    available = [d.name for d in devices]
    raise DeviceNotFoundError(
        f"No device found matching '{device_name}'. Available devices: {available}"
    )


# ========================================================================
# CONVENIENCE FUNCTIONS
# ========================================================================

def list_cameras() -> List[str]:
    """Get list of available camera names.
    
    Returns:
        List of camera display names
    """
    devices_list = list_devices()  # Core API only
    return [d.name for d in devices_list]


def find_camera(name_pattern: str) -> CameraController:
    """Find and Connect to camera by name pattern.
    
    Args:
        name_pattern: Name substring to search (case-insensitive)
        
    Returns:
        Connected CameraController instance
        
    Raises:
        DeviceNotFoundError: If no matching camera found
    """
    return CameraController(device_name=name_pattern)


def get_camera_info(device_index: int = 0) -> Dict[str, Any]:
    """Get camera information by index.
    
    Args:
        device_index: Camera index (default: 0, first available)
        
    Returns:
        Dict with name, path, and index
        
    Raises:
        DeviceNotFoundError: If index out of range
    """
    devices_list = list_devices()
    if device_index >= len(devices_list):
        raise DeviceNotFoundError(f"Camera index {device_index} not available")
    
    device = devices_list[device_index]
    return {
        'name': device.name,
        'path': device.path,
        'index': device_index
    }
