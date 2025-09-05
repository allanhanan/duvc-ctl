#!/usr/bin/env python3
"""
Interactive Demo for duvc-ctl Python Bindings
Menu-driven interface to control DirectShow cameras
"""

import sys
from pathlib import Path

# Add build directory to path (for development)
project_root = Path(__file__).parent.parent
build_py_dir = project_root / "build" / "py"
if build_py_dir.exists():
    sys.path.insert(0, str(build_py_dir))

try:
    import duvc_ctl as duvc
except ImportError as e:
    print(f"Error: Failed to import duvc_ctl: {e}")
    print("Make sure the Python bindings are built and the required DLLs are present.")
    sys.exit(1)

class CameraController:
    def __init__(self):
        self.devices = []
        self.current_device = None
        self.current_device_index = -1
        self.refresh_devices()
    
    def refresh_devices(self):
        """Refresh the device list"""
        self.devices = duvc.list_devices()
        if self.current_device_index >= len(self.devices):
            self.current_device = None
            self.current_device_index = -1
    
    def show_main_menu(self):
        """Display the main menu"""
        print("\n" + "="*60)
        print("         DirectShow UVC Camera Controller")
        print("="*60)
        print(f"Found {len(self.devices)} camera(s)")
        
        if self.current_device:
            print(f"Current device: [{self.current_device_index}] {self.current_device.name}")
        else:
            print("Current device: None selected")
        
        print("\nMain Menu:")
        print("1. List all cameras")
        print("2. Select camera")
        print("3. Check camera status")
        print("4. PTZ Control")
        print("5. Video Properties")
        print("6. Camera Properties")
        print("0. Exit")
        print("-" * 60)
    
    def list_cameras(self):
        """List all available cameras"""
        self.refresh_devices()
        print(f"\nAvailable cameras ({len(self.devices)}):")
        for i, device in enumerate(self.devices):
            status = "CONNECTED" if duvc.is_device_connected(device) else "DISCONNECTED"
            print(f"  [{i}] {device.name} - {status}")
        input("\nPress Enter to continue...")
    
    def select_camera(self):
        """Select a camera to work with"""
        self.refresh_devices()
        if not self.devices:
            print("No cameras available!")
            input("Press Enter to continue...")
            return
        
        print("\nSelect camera:")
        for i, device in enumerate(self.devices):
            print(f"  [{i}] {device.name}")
        
        try:
            choice = int(input(f"Enter camera index (0-{len(self.devices)-1}): "))
            if 0 <= choice < len(self.devices):
                self.current_device = self.devices[choice]
                self.current_device_index = choice
                print(f"Selected: {self.current_device.name}")
            else:
                print("Invalid selection!")
        except ValueError:
            print("Invalid input!")
        
        input("Press Enter to continue...")
    
    def check_status(self):
        """Check current camera status"""
        if not self.current_device:
            print("No camera selected!")
            input("Press Enter to continue...")
            return
        
        connected = duvc.is_device_connected(self.current_device)
        status = "CONNECTED" if connected else "DISCONNECTED"
        print(f"\nCamera [{self.current_device_index}] {self.current_device.name}")
        print(f"Status: {status}")
        input("\nPress Enter to continue...")
    
    def ptz_control_menu(self):
        """PTZ control submenu"""
        if not self.current_device:
            print("No camera selected!")
            input("Press Enter to continue...")
            return
        
        while True:
            print(f"\n--- PTZ Control: {self.current_device.name} ---")
            print("1. Pan control")
            print("2. Tilt control") 
            print("3. Zoom control")
            print("4. Focus control")
            print("5. Exposure control")
            print("6. Center camera (Pan=0, Tilt=0)")
            print("0. Back to main menu")
            
            try:
                choice = int(input("Enter option: "))
                if choice == 0:
                    break
                elif choice == 1:
                    self.control_property("cam", "Pan")
                elif choice == 2:
                    self.control_property("cam", "Tilt")
                elif choice == 3:
                    self.control_property("cam", "Zoom")
                elif choice == 4:
                    self.control_property("cam", "Focus")
                elif choice == 5:
                    self.control_property("cam", "Exposure")
                elif choice == 6:
                    self.center_camera()
                else:
                    print("Invalid option!")
            except ValueError:
                print("Invalid input!")
    
    def video_properties_menu(self):
        """Video properties submenu"""
        if not self.current_device:
            print("No camera selected!")
            input("Press Enter to continue...")
            return
        
        while True:
            print(f"\n--- Video Properties: {self.current_device.name} ---")
            print("1. Brightness")
            print("2. Contrast")
            print("3. Saturation")
            print("4. White Balance")
            print("5. Hue")
            print("6. Gamma")
            print("0. Back to main menu")
            
            try:
                choice = int(input("Enter option: "))
                if choice == 0:
                    break
                elif choice == 1:
                    self.control_property("vid", "Brightness")
                elif choice == 2:
                    self.control_property("vid", "Contrast")
                elif choice == 3:
                    self.control_property("vid", "Saturation")
                elif choice == 4:
                    self.control_property("vid", "WhiteBalance")
                elif choice == 5:
                    self.control_property("vid", "Hue")
                elif choice == 6:
                    self.control_property("vid", "Gamma")
                else:
                    print("Invalid option!")
            except ValueError:
                print("Invalid input!")
    
    def camera_properties_menu(self):
        """Camera properties submenu"""
        if not self.current_device:
            print("No camera selected!")
            input("Press Enter to continue...")
            return
        
        while True:
            print(f"\n--- Camera Properties: {self.current_device.name} ---")
            print("1. Show all supported properties")
            print("2. Custom property control")
            print("0. Back to main menu")
            
            try:
                choice = int(input("Enter option: "))
                if choice == 0:
                    break
                elif choice == 1:
                    self.show_all_properties()
                elif choice == 2:
                    self.custom_property_control()
                else:
                    print("Invalid option!")
            except ValueError:
                print("Invalid input!")
    
    def control_property(self, domain, prop_name):
        """Control a specific property"""
        print(f"\n--- {prop_name} Control ---")
        
        # Get the property enum
        if domain == "cam":
            prop = getattr(duvc.CamProp, prop_name, None)
            get_func = duvc.get_camera_property
            set_func = duvc.set_camera_property
            get_range_func = duvc.get_camera_property_range
        else:
            prop = getattr(duvc.VidProp, prop_name, None)
            get_func = duvc.get_video_property
            set_func = duvc.set_video_property
            get_range_func = duvc.get_video_property_range
        
        if not prop:
            print(f"Property {prop_name} not found!")
            input("Press Enter to continue...")
            return
        
        # Get current value
        try:
            current_setting = get_func(self.current_device, prop)
            mode_str = "Auto" if current_setting.mode == duvc.CamMode.Auto else "Manual"
            print(f"Current {prop_name}: {current_setting.value} ({mode_str})")
        except duvc.PropertyNotSupportedError:
            print(f"Cannot read {prop_name} (not supported)")
            input("Press Enter to continue...")
            return
        except Exception as e:
            print(f"Error reading {prop_name}: {e}")
            input("Press Enter to continue...")
            return
        
        # Get range
        try:
            prop_range = get_range_func(self.current_device, prop)
            print(f"Range: {prop_range.min} to {prop_range.max}, step: {prop_range.step}")
            print(f"Default: {prop_range.default_val}")
        except duvc.PropertyNotSupportedError:
            print("Range information not available")
            input("Press Enter to continue...")
            return
        except Exception as e:
            print(f"Error getting range for {prop_name}: {e}")
            input("Press Enter to continue...")
            return
        
        print("\nOptions:")
        print("1. Set to specific value")
        print("2. Set to default")
        print("3. Set to auto mode")
        print("0. Cancel")
        
        try:
            choice = int(input("Enter option: "))
            if choice == 0:
                return
            elif choice == 1:
                value = int(input(f"Enter value ({prop_range.min}-{prop_range.max}): "))
                value = prop_range.clamp(value)
                setting = duvc.PropSetting(value, duvc.CamMode.Manual)
            elif choice == 2:
                setting = duvc.PropSetting(prop_range.default_val, duvc.CamMode.Manual)
            elif choice == 3:
                setting = duvc.PropSetting(prop_range.default_val, duvc.CamMode.Auto)
            else:
                print("Invalid option!")
                return
            
            set_func(self.current_device, prop, setting)
            print(f"Set {prop_name} successfully")
        except duvc.InvalidValueError:
            print("Invalid value provided!")
        except Exception as e:
            print(f"Failed to set {prop_name}: {e}")
        
        input("Press Enter to continue...")
    
    def center_camera(self):
        """Center the camera (Pan=0, Tilt=0)"""
        print("\nCentering camera...")
        
        pan_setting = duvc.PropSetting(0, duvc.CamMode.Manual)
        tilt_setting = duvc.PropSetting(0, duvc.CamMode.Manual)
        
        pan_success = True
        tilt_success = True
        
        try:
            duvc.set_camera_property(self.current_device, duvc.CamProp.Pan, pan_setting)
        except Exception:
            pan_success = False
        
        try:
            duvc.set_camera_property(self.current_device, duvc.CamProp.Tilt, tilt_setting)
        except Exception:
            tilt_success = False
        
        if pan_success and tilt_success:
            print("Camera centered successfully")
        elif pan_success:
            print("Pan centered (Tilt not supported)")
        elif tilt_success:
            print("Tilt centered (Pan not supported)")
        else:
            print("Failed to center camera (PTZ not supported)")
        
        input("\nPress Enter to continue...")
    
    def show_all_properties(self):
        """Show all supported properties for the current device"""
        print(f"\n--- Supported Properties: {self.current_device.name} ---")
        
        print("\nCamera Properties:")
        cam_props = ["Pan", "Tilt", "Roll", "Zoom", "Exposure", "Iris", "Focus"]
        for prop_name in cam_props:
            prop = getattr(duvc.CamProp, prop_name, None)
            if prop:
                try:
                    setting = duvc.get_camera_property(self.current_device, prop)
                    mode_str = "Auto" if setting.mode == duvc.CamMode.Auto else "Manual"
                    print(f"  {prop_name}: {setting.value} ({mode_str})")
                except duvc.PropertyNotSupportedError:
                    pass  # Skip unsupported
                except Exception as e:
                    print(f"  {prop_name}: Error - {e}")
        
        print("\nVideo Properties:")
        vid_props = ["Brightness", "Contrast", "Saturation", "WhiteBalance", "Hue", "Gamma"]
        for prop_name in vid_props:
            prop = getattr(duvc.VidProp, prop_name, None)
            if prop:
                try:
                    setting = duvc.get_video_property(self.current_device, prop)
                    mode_str = "Auto" if setting.mode == duvc.CamMode.Auto else "Manual"
                    print(f"  {prop_name}: {setting.value} ({mode_str})")
                except duvc.PropertyNotSupportedError:
                    pass  # Skip unsupported
                except Exception as e:
                    print(f"  {prop_name}: Error - {e}")
        
        input("\nPress Enter to continue...")
    
    def custom_property_control(self):
        """Allow user to enter custom property name"""
        print("\nCustom Property Control")
        print("Available domains: cam, vid")
        
        domain = input("Enter domain (cam/vid): ").strip().lower()
        if domain not in ["cam", "vid"]:
            print("Invalid domain!")
            input("Press Enter to continue...")
            return
        
        prop_name = input("Enter property name: ").strip()
        self.control_property(domain, prop_name)
    
    
    def run(self):
        """Main interactive loop"""
        print("Welcome to DirectShow UVC Camera Controller!")
        
        while True:
            self.show_main_menu()
            
            try:
                choice = int(input("Enter your choice: "))
                
                if choice == 0:
                    print("Goodbye!")
                    break
                elif choice == 1:
                    self.list_cameras()
                elif choice == 2:
                    self.select_camera()
                elif choice == 3:
                    self.check_status()
                elif choice == 4:
                    self.ptz_control_menu()
                elif choice == 5:
                    self.video_properties_menu()
                elif choice == 6:
                    self.camera_properties_menu()
                else:
                    print("Invalid option! Please try again.")
                    input("Press Enter to continue...")
                    
            except ValueError:
                print("Invalid input! Please enter a number.")
                input("Press Enter to continue...")
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")


def main():
    """Entry point"""
    if sys.platform != "win32":
        print("Warning: This tool is designed for Windows only!")
        print("DirectShow APIs are not available on this platform.")
        return
    
    controller = CameraController()
    controller.run()


if __name__ == "__main__":
    main()
