#!/usr/bin/env python3
"""
DUVC-CTL Simple API Example
Semo of ALL Pythonic API features and UX patterns
Uses ONLY the high-level CameraController - NO Result<T>
"""

import duvc_ctl
import time


def separator(char="="):
    """Print visual separator"""
    print(f"\n{char*70}")


def section_header(title):
    """Print formatted section header"""
    separator("=")
    print(f"  {title}")
    separator("=")


def subsection(title):
    """Print subsection header"""
    print(f"\n--- {title} ---")


def safe_get(cam, prop_name):
    """Safely get property value, return None if unsupported"""
    try:
        return cam.get(prop_name)
    except (duvc_ctl.PropertyNotSupportedError, Exception):
        return None

def clamp_value(value, min_val, max_val):
    """Clamp value to valid range"""
    return max(min_val, min(max_val, value))


def safe_set(cam, prop_name, value, verbose=False):
    """Safely set property with range validation"""
    try:
        prop_range = cam.get_property_range(prop_name)
        if prop_range and not (prop_range['min'] <= value <= prop_range['max']):
            if verbose:
                print(f"✗ Out of range! {value} not in [{prop_range['min']}, {prop_range['max']}]")
            return False
        cam.set(prop_name, value)
        return True
    except Exception as e:
        if verbose:
            print(f"✗ Error: {e}")
        return False

def safe_property_read(cam, prop_name, supported):
    """Safely read property using supported properties dict"""
    try:
        if prop_name in supported['video']:
            return cam.get(prop_name)
        elif prop_name in supported['camera']:
            return cam.get(prop_name)
    except:
        pass
    return None

def main():
    """Demonstrate ALL simple API features"""
    print("="*70)
    print("  DUVC-CTL SIMPLE PYTHONIC API DEMO")
    print("  Showcase of all features")
    print("="*70)
    
    try:
        # =================================================================
        # PART 1: DEVICE DISCOVERY
        # =================================================================
        section_header("PART 1: Device Discovery & Connection")
        
        # Feature: List all cameras
        subsection("1.1 List Cameras")
        cameras = duvc_ctl.list_cameras()
        print(f"Found {len(cameras)} camera(s):")
        for i, name in enumerate(cameras):
            print(f"  [{i}] {name}")
        
        if not cameras:
            print("✗ No cameras found!")
            return
        
        # Feature: Find camera by name pattern
        subsection("1.2 Find Camera by Pattern")
        try:
            found_cam = duvc_ctl.find_camera("Integrated")
            if found_cam:
                print(f"✓ Found: {found_cam.device_name}")
                found_cam.close()
        except duvc_ctl.DeviceNotFoundError:
            print("  (No matching camera found)")
        
        # Feature: Context manager (recommended)
        subsection("1.3 Connect via Context Manager")
        with duvc_ctl.CameraController() as cam:
            print(f"✓ Connected to: {cam.device_name}")
            print(f"  Device path: {cam.device_path}")
            print(f"  Connected: {cam.is_connected}")
            
            # =================================================================
            # PART 2: PROPERTY ENUMERATION & DISCOVERY
            # =================================================================
            section_header("PART 2: Property Enumeration")
            
            # Feature: List all properties
            subsection("2.1 List All Properties")
            all_props = cam.list_properties()
            print(f"Total properties: {len(all_props)}")
            print(f"All: {', '.join(all_props)}")
            
            # Feature: Get supported properties by category
            subsection("2.2 Supported Properties by Category")
            supported = cam.get_supported_properties()
            print(f"Camera properties ({len(supported['camera'])}): {', '.join(supported['camera'])}")
            print(f"Video properties ({len(supported['video'])}): {', '.join(supported['video'])}")
            
            # Feature: Property aliases
            subsection("2.3 Property Aliases")
            aliases = cam.get_property_aliases()
            print("Property aliases:")
            for prop, alias_list in list(aliases.items())[:5]:
                print(f"  {prop}: {alias_list}")
            
            # =================================================================
            # PART 3: DIRECT PROPERTY ACCESS (PYTHONIC)
            # =================================================================
            section_header("PART 3: Direct Pythonic Property Access")
            
            # Feature: Direct property read
            subsection("3.1 Read Properties (Direct Access)")
            print("Reading via direct property access:")
            video_props = ['brightness', 'contrast', 'saturation', 'hue', 'gamma']
            for prop in video_props:
                value = safe_get(cam, prop)
                if value is not None:
                    print(f"  cam.{prop:15} = {value}")
            
            # Feature: Direct property write
            subsection("3.2 Write Properties (Direct Assignment)")
            if 'brightness' in supported['video']:
                original = cam.brightness
                cam.brightness = 75
                print(f"✓ cam.brightness = 75")
                print(f"  New value: {cam.brightness}")
                # Restore with clamping
                brightness_range = cam.get_property_range('brightness')
                if brightness_range:
                    restored = clamp_value(original, brightness_range['min'], brightness_range['max'])
                    cam.brightness = restored
            
            # =================================================================
            # PART 4: STRING-BASED ACCESS
            # =================================================================
            section_header("PART 4: String-Based Property Access")
            
            # Feature: get() method
            subsection("4.1 Get via String Name")
            if 'brightness' in supported['video']:
                value = safe_property_read(cam, 'brightness', supported)
                if value is not None:
                    print(f"  cam.get('brightness') = {value}")
            if 'contrast' in supported['video']:
                value = safe_property_read(cam, 'contrast', supported)
                if value is not None:
                    print(f"  cam.get('contrast') = {value}")
            if 'saturation' in supported['video']:
                value = safe_property_read(cam, 'saturation', supported)
                if value is not None:
                    print(f"  cam.get('saturation') = {value}")
            
            # Feature: set() method with value
            subsection("4.2 Set via String Name")
            if 'contrast' in supported['video']:
                if safe_set(cam, 'contrast', 60, verbose=True):
                    value = safe_property_read(cam, 'contrast', supported)
                    if value is not None:
                        print(f"  New value: {value}")
            
            # Feature: set() with mode
            subsection("4.3 Set with Mode (Manual/Auto)")
            if 'brightness' in supported['video']:
                if safe_set(cam, 'brightness', 80, verbose=True):
                    cam.set('brightness', 'auto')
                    print(f"✓ cam.set('brightness', 'auto')")
            
            # =================================================================
            # PART 5: PROPERTY RANGES & VALIDATION
            # =================================================================
            section_header("PART 5: Property Ranges & Validation")
            
            subsection("5.1 Get Property Ranges")
            for prop in ['brightness', 'contrast', 'saturation'][:2]:
                if prop in supported['video']:
                    range_info = cam.get_property_range(prop)
                    if range_info:
                        print(f"{prop.capitalize()}:")
                        print(f"  Min:     {range_info['min']}")
                        print(f"  Max:     {range_info['max']}")
                        print(f"  Step:    {range_info['step']}")
                        print(f"  Default: {range_info['default']}")
            
            # Feature: Range validation before setting
            subsection("5.2 Validate Before Setting")
            if 'brightness' in supported['video']:
                brightness_range = cam.get_property_range('brightness')
                test_value = 85
                if brightness_range and brightness_range['min'] <= test_value <= brightness_range['max']:
                    cam.brightness = test_value
                    print(f"✓ Value {test_value} within range, set successfully")
                    print(f"  Current: {cam.brightness}")
                else:
                    print(f"✗ Value {test_value} out of range!")
            
            # =================================================================
            # PART 6: BATCH OPERATIONS
            # =================================================================
            section_header("PART 6: Batch Operations")
            
            # Feature: set_multiple()
            subsection("6.1 Set Multiple Properties at Once")
            props_to_set = {}
            if 'brightness' in supported['video']:
                props_to_set['brightness'] = 70
            if 'contrast' in supported['video']:
                props_to_set['contrast'] = 65
            if 'saturation' in supported['video']:
                props_to_set['saturation'] = 75
            
            if props_to_set:
                results = cam.set_multiple(props_to_set, verbose=False)
                print(f"Set {len(props_to_set)} properties:")
                for prop, success in results.items():
                    status = "✓" if success else "✗"
                    print(f"  {status} {prop}")
            
            # Feature: get_multiple()
            subsection("6.2 Get Multiple Properties at Once")
            print("Batch get results:")
            for prop in ['brightness', 'contrast', 'saturation', 'hue']:
                if prop in supported['video']:
                    value = safe_property_read(cam, prop, supported)
                    if value is not None:
                        print(f"  {prop:15}: {value}")
            
            # =================================================================
            # PART 7: AUTO MODE CONTROL
            # =================================================================
            section_header("PART 7: Auto Mode Control")
            
            # Feature: set_property_auto()
            subsection("7.1 Set to Auto Mode")
            if 'brightness' in supported['video']:
                try:
                    cam.set('brightness', 'auto')
                    print("✓ cam.set('brightness', 'auto')")
                except Exception as e:
                    print(f"  Error: {e}")
            
            # Feature: Auto via set()
            subsection("7.2 Auto Mode via set()")
            if 'whitebalance' in supported['video'] or 'white_balance' in supported['video']:
                wb_prop = 'whitebalance' if 'whitebalance' in supported['video'] else 'white_balance'
                try:
                    cam.set(wb_prop, 'auto')
                    print(f"✓ cam.set('{wb_prop}', 'auto')")
                except Exception as e:
                    print(f"  Error: {e}")
            
            # Feature: Manual mode
            subsection("7.3 Manual Mode")
            if 'brightness' in supported['video']:
                try:
                    cam.set('brightness', 80, 'manual')
                    print(f"✓ cam.set('brightness', 80, 'manual')")
                except Exception as e:
                    print(f"  Error: {e}")
            
            # =================================================================
            # PART 8: CAMERA PROPERTIES (PTZ)
            # =================================================================
            section_header("PART 8: Camera Properties (PTZ)")
            
            if 'pan' in supported['camera'] or 'tilt' in supported['camera']:
                subsection("8.1 Absolute PTZ Positioning")
                try:
                    if 'pan' in supported['camera']:
                        pan_range = cam.get_property_range('pan')
                        pan_val = clamp_value(30, pan_range['min'], pan_range['max']) if pan_range else 30
                        cam.pan = pan_val
                        print(f"✓ cam.pan = {pan_val} → {cam.pan}°")
                    if 'tilt' in supported['camera']:
                        tilt_range = cam.get_property_range('tilt')
                        tilt_val = clamp_value(-15, tilt_range['min'], tilt_range['max']) if tilt_range else -15
                        cam.tilt = tilt_val
                        print(f"✓ cam.tilt = {tilt_val} → {cam.tilt}°")
                    if 'zoom' in supported['camera']:
                        zoom_range = cam.get_property_range('zoom')
                        zoom_val = clamp_value(150, zoom_range['min'], zoom_range['max']) if zoom_range else 150
                        cam.zoom = zoom_val
                        print(f"✓ cam.zoom = {zoom_val} → {cam.zoom}")
                except duvc_ctl.PropertyNotSupportedError:
                    print("  (PTZ not fully supported)")
                
                # Feature: Relative movements
                subsection("8.2 Relative PTZ Movements")
                try:
                    if 'pan' in supported['camera']:
                        cam.pan_relative(10)
                        print(f"✓ cam.pan_relative(10) → {cam.pan}°")
                    if 'tilt' in supported['camera']:
                        cam.tilt_relative(-5)
                        print(f"✓ cam.tilt_relative(-5) → {cam.tilt}°")
                except (duvc_ctl.PropertyNotSupportedError, AttributeError):
                    print("  (Relative movements not supported)")
                
                # Feature: Combined pan/tilt
                subsection("8.3 Combined Pan/Tilt")
                try:
                    if 'pan' in supported['camera'] and 'tilt' in supported['camera']:
                        cam.set_pan_tilt(0, 0)
                        print(f"✓ cam.set_pan_tilt(0, 0)")
                        print(f"  Pan: {cam.pan}°, Tilt: {cam.tilt}°")
                except (duvc_ctl.PropertyNotSupportedError, AttributeError):
                    print("  (Combined PTZ not supported)")
            else:
                print("  (No PTZ properties supported)")
            
            # Feature: Other camera properties
            subsection("8.4 Other Camera Properties")
            other_props = ['focus', 'exposure', 'iris', 'roll']
            for prop in other_props:
                if prop in supported['camera']:
                    value = safe_get(cam, prop)
                    if value is not None:
                        print(f"  {prop:10}: {value}")
            
            # =================================================================
            # PART 9: CONVENIENCE METHODS
            # =================================================================
            section_header("PART 9: Convenience Methods")
            
            # Feature: get_brightness() / set_brightness()
            subsection("9.1 Property-Specific Methods")
            if 'brightness' in supported['video']:
                try:
                    cam.set_brightness(90)
                    print(f"✓ cam.set_brightness(90) → {cam.get_brightness()}")
                except AttributeError:
                    print("  (Convenience methods not available)")
            
            # =================================================================
            # PART 10: PRESETS
            # =================================================================
            section_header("PART 10: Preset Management")
            
            # Feature: List presets
            subsection("10.1 Available Presets")
            presets = cam.get_preset_names()
            print(f"Built-in presets: {', '.join(presets[:5])}")
            
            # Feature: Apply preset
            subsection("10.2 Apply Preset")
            if 'daylight' in presets:
                if cam.apply_preset('daylight'):
                    print("✓ Applied 'daylight' preset")
            
            # Feature: Custom presets
            subsection("10.3 Create Custom Preset")
            custom_props = {}
            if 'brightness' in supported['video']:
                custom_props['brightness'] = cam.brightness
            if 'contrast' in supported['video']:
                custom_props['contrast'] = cam.contrast
            
            if custom_props:
                cam.create_custom_preset('demo_preset', custom_props)
                print(f"✓ Created 'demo_preset' with {len(custom_props)} properties")
            
            # Feature: List custom presets
            subsection("10.4 List Custom Presets")
            custom_presets = cam.get_custom_presets()
            print(f"Custom presets: {list(custom_presets.keys())}")
            
            # Feature: Apply custom preset
            if 'demo_preset' in custom_presets:
                cam.apply_preset('demo_preset')
                print("✓ Applied 'demo_preset'")
            
            # Feature: Delete custom preset
            subsection("10.5 Delete Custom Preset")
            if 'demo_preset' in custom_presets:
                cam.delete_custom_preset('demo_preset')
                print("✓ Deleted 'demo_preset'")

            # Feature: Relative PTZ operations
            section_header("PART 10.5: Relative PTZ Operations")

            if 'pan' in supported['camera']:
                subsection("10.5.1 Relative Pan Movement")
                try:
                    cam.pan_relative(15)  # Move right 15 degrees
                    print("✓ cam.pan_relative(15)")
                except Exception as e:
                    print(f"  Note: {e}")
            
            if 'zoom' in supported['camera']:
                subsection("10.5.2 Relative Zoom")
                try:
                    cam.zoom_relative(1)  # Zoom in
                    print("✓ cam.zoom_relative(1)")
                except Exception as e:
                    print(f"  Note: {e}")
            
            # =================================================================
            # PART 11: DEFAULTS & RESET
            # =================================================================
            section_header("PART 11: Defaults & Reset")
            
            # Feature: Smart default (single property)
            subsection("11.1 Reset All to Defaults")
            try:
                cam.reset_to_defaults()
                print("✓ cam.reset_to_defaults()")
                print("Properties reset:")
                for prop in ['brightness', 'contrast', 'saturation'][:2]:
                    if prop in supported['video']:
                        value = safe_property_read(cam, prop, supported)
                        if value is not None:
                            print(f"  {prop:15}: {value}")
            except Exception as e:
                print(f"  Error: {e}")
            
            # Feature: Reset all to defaults
            subsection("11.2 Reset All to Defaults")
            cam.reset_to_defaults()
            print("✓ cam.reset_to_defaults()")
            print("Properties reset:")
            for prop in ['brightness', 'contrast', 'saturation'][:2]:
                if prop in supported['video']:
                    print(f"  {prop:15}: {cam.get(prop)}")

            # =================================================================
            # PART 11.5: Connection Status Monitoring
            # =================================================================
            section_header("PART 11.5: Connection Monitoring")
            
            subsection("11.5.1 Check Connection Status")
            print(f"✓ Camera connected: {cam.is_connected}")
            print(f"  Device: {cam.device_name}")
            
            subsection("11.5.2 Property Change Detection")
            initial = cam.brightness
            cam.brightness = 50
            final = cam.brightness
            print(f"  Brightness: {initial} → {final} (changed: {initial != final})")
            
            # =================================================================
            # PART 12: Camera Centering (PTZ)
            # =================================================================
            
            if 'pan' in supported['camera'] and 'tilt' in supported['camera']:
                section_header("PART 12: Camera Centering")
                
                subsection("12.1 Center Camera")
                try:
                    cam.set('pan', 0)
                    cam.set('tilt', 0)
                    print("✓ Camera centered:")
                    pan_val = safe_property_read(cam, 'pan', supported)
                    tilt_val = safe_property_read(cam, 'tilt', supported)
                    if pan_val is not None and tilt_val is not None:
                        print(f"  Pan:  {pan_val}°")
                        print(f"  Tilt: {tilt_val}°")
                except Exception as e:
                    print(f"  Error: {e}")
            else:
                section_header("PART 12: Camera Centering (PTZ)")
                print("  (PTZ features not supported on this camera)")


            # =================================================================
            # PART 13: Property Aliases
            # =================================================================
            section_header("PART 13: Property Aliases Reference")
            
            subsection("13.1 Common Aliases")
            print("""
                Alias Reference (examples from this camera):
                brightness:     bright, b
                white_balance:  wb, whitebalance
                saturation:     sat
                zoom:           z
                focus:          f
                exposure:       exp
                pan:            horizontal
                tilt:           vertical

                Usage: cam.set('bright', 80)  # Same as cam.set('brightness', 80)
                            """)
            
            # =================================================================
            # PART 14: ERROR HANDLING
            # =================================================================
            section_header("PART 14: Error Handling Patterns")
            
            # Feature: Out of range error
            subsection("14.1 InvalidValueError")
            try:
                if 'brightness' in supported['video']:
                    cam.brightness = 999  # Out of range
            except duvc_ctl.InvalidValueError as e:
                print(f"✓ Caught InvalidValueError:")
                print(f"  {e}")
            
            # Feature: Unsupported property
            subsection("14.2 PropertyNotSupportedError")
            try:
                unsupported_prop = 'fake_property_12345'
                cam.set(unsupported_prop, 100)
            except (duvc_ctl.PropertyNotSupportedError, ValueError) as e:
                print(f"✓ Caught error:")
                print(f"  {type(e).__name__}: {e}")
            
            # Feature: Safe property access
            subsection("14.3 Safe Property Access Pattern")
            test_props = ['pan', 'exposure', 'privacy', 'iris']
            for prop in test_props:
                value = safe_property_read(cam, prop, supported)
                if value is not None:
                    print(f"  ✓ {prop:10}: {value}")
                else:
                    print(f"  ✗ {prop:10}: not supported or error")
            
            # =================================================================
            # PART 15: DEVICE INFORMATION
            # =================================================================
            section_header("PART 15: Device Information")
            
            subsection("15.1 Basic Device Info")
            print(f"Device Name:    {cam.device_name}")
            print(f"Device Path:    {cam.device_path}")
            print(f"Connected:      {cam.is_connected}")
            
            subsection("15.2 Property Statistics")
            print(f"Total properties:     {len(all_props)}")
            print(f"Camera properties:    {len(supported['camera'])}")
            print(f"Video properties:     {len(supported['video'])}")
            
            # =================================================================
            # PART 16: ADVANCED - CORE API ACCESS
            # =================================================================
            section_header("PART 16: Advanced - Core API Access")
            
            subsection("16.1 Access Underlying Core Camera")
            print("cam.core provides access to Result<T> based API:")
            core_camera = cam.core
            print(f"  Type: {type(core_camera).__name__}")
            print("  Use for advanced Result<T> operations when needed")
            
            # =================================================================
            # SUMMARY
            # =================================================================
            section_header("SUMMARY - Features Demonstrated")
            print("""
✓ Device discovery (list_cameras, find_camera)
✓ Context manager (with CameraController)
✓ Property enumeration (list, supported, aliases)
✓ Direct property access (cam.brightness = 80)
✓ String-based access (cam.get/set)
✓ Property ranges & validation
✓ Batch operations (set_multiple, get_multiple)
✓ Auto/Manual mode control
✓ PTZ controls (pan, tilt, zoom, relative)
✓ Convenience methods
✓ Preset management (built-in & custom)
✓ Defaults & reset
✓ Camera centering
✓ Property aliases
✓ Error handling patterns
✓ Device information
✓ Core API access
            """)
        
        # Context manager auto-closes camera
        separator()
        print("✓ Camera closed automatically (context manager)")
        separator()
        
    except duvc_ctl.DeviceNotFoundError as e:
        print(f"\n✗ ERROR: {e}")
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("  Demo Complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
