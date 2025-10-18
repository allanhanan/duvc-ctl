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
        self.current_camera = None
        self.refresh_devices()

    def refresh_devices(self):
        """Refresh the device list"""
        self.devices = duvc.list_devices()
        if self.current_device_index >= len(self.devices):
            self.current_device = None
            self.current_device_index = -1
            self.current_camera = None

    def open_current_camera(self):
        """Open camera for current device if not already open"""
        if self.current_device_index < 0 or self.current_device_index >= len(self.devices):
            return False

        if not self.current_camera:
            try:
                # Get the Result<Camera>
                camera_result = duvc.open_camera(self.current_device_index)
                
                # Check if the result is successful
                if camera_result.is_ok():
                    # Extract the Camera from the Result
                    self.current_camera = camera_result.value()
                    return True
                else:
                    print(f"Error opening camera: {camera_result.error().description()}")
                    return False
                    
            except Exception as e:
                print(f"Error opening camera: {e}")
                return False

        return True

    def list_cameras(self):
        """List all available cameras"""
        print("\n" + "="*60)
        print("         Available Cameras")
        print("="*60)

        self.refresh_devices()
        if not self.devices:
            print("No cameras found!")
        else:
            for i, device in enumerate(self.devices):
                connected = duvc.is_device_connected(device)
                status = "CONNECTED" if connected else "DISCONNECTED"
                current = "*" if i == self.current_device_index else " "
                print(f"{current}[{i}] {device.name} - {status}")

        input("\nPress Enter to continue...")

    def select_camera(self):
        """Select a camera to work with"""
        print("\n" + "="*60)
        print("         Select Camera")
        print("="*60)

        self.refresh_devices()
        if not self.devices:
            print("No cameras found!")
            input("Press Enter to continue...")
            return

        print("Available cameras:")
        for i, device in enumerate(self.devices):
            connected = duvc.is_device_connected(device)
            status = "CONNECTED" if connected else "DISCONNECTED"
            print(f"[{i}] {device.name} - {status}")

        try:
            choice = int(input(f"\nEnter camera index (0-{len(self.devices)-1}): "))
            if 0 <= choice < len(self.devices):
                self.current_device_index = choice
                self.current_device = self.devices[choice]
                self.current_camera = None  # Reset camera handle
                print(f"Selected: {self.current_device.name}")
            else:
                print("Invalid camera index!")
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

        if connected and self.open_current_camera():
            # Now self.current_camera is the actual Camera object, not a Result
            print(f"Camera handle: {'Valid' if self.current_camera.is_valid() else 'Invalid'}")

        input("\nPress Enter to continue...")

    def get_property_safely(self, prop_type, prop, prop_name):
        """Safely get a property and return the result or error message"""
        try:
            if not self.open_current_camera():
                return None, "Failed to open camera"

            # Get the property - this returns a Result<PropSetting>
            if prop_type == "camera":
                result = self.current_camera.get(prop)
            else:  # video
                result = self.current_camera.get(prop)
                
            if result.is_ok():
                setting = result.value()
                return setting, None
            else:
                return None, result.error().description()
        except Exception as e:
            return None, str(e)

    def set_property_safely(self, prop_type, prop, setting, prop_name):
        """Safely set a property and return success/error"""
        try:
            if not self.open_current_camera():
                return False, "Failed to open camera"

            # Set the property - this returns a Result<void>
            if prop_type == "camera":
                result = self.current_camera.set(prop, setting)
            else:  # video
                result = self.current_camera.set(prop, setting)
                
            if result.is_ok():
                return True, None
            else:
                return False, result.error().description()
        except Exception as e:
            return False, str(e)

    def get_range_safely(self, prop_type, prop, prop_name):
        """Safely get a property range and return the result or error message"""
        try:
            if not self.open_current_camera():
                return None, "Failed to open camera"

            # Get the property range - this returns a Result<PropRange>
            if prop_type == "camera":
                result = self.current_camera.get_range(prop)
            else:  # video
                result = self.current_camera.get_range(prop)
                
            if result.is_ok():
                prop_range = result.value()
                return prop_range, None
            else:
                return None, result.error().description()
        except Exception as e:
            return None, str(e)

    def control_single_property(self, prop_type, prop, prop_name):
        """Generic property control interface"""
        if not self.current_device:
            print("No camera selected!")
            input("Press Enter to continue...")
            return

        print(f"\n--- {prop_name} Control ---")

        # Get current value
        setting, error = self.get_property_safely(prop_type, prop, prop_name)
        if error:
            print(f"Error reading {prop_name}: {error}")
            input("Press Enter to continue...")
            return

        # Get range
        prop_range, error = self.get_range_safely(prop_type, prop, prop_name)
        if error:
            print(f"Error getting {prop_name} range: {error}")
            input("Press Enter to continue...")
            return

        print(f"Current {prop_name}: {setting.value} (Mode: {duvc.to_string(setting.mode)})")
        print(f"Range: {prop_range.min} to {prop_range.max}, step: {prop_range.step}")
        print(f"Default: {prop_range.default_val} (Mode: {duvc.to_string(prop_range.default_mode)})")

        print(f"\n1. Set {prop_name} value")
        print("2. Set to auto mode")
        print("3. Set to manual mode")
        print("4. Reset to default")
        print("0. Back")

        try:
            choice = int(input("Enter option: "))
            if choice == 1:
                new_value = int(input(f"Enter new {prop_name} value ({prop_range.min}-{prop_range.max}): "))
                new_setting = duvc.PropSetting(new_value, duvc.CamMode.Manual)
                success, error = self.set_property_safely(prop_type, prop, new_setting, prop_name)
                if success:
                    print(f"{prop_name} set to {new_value}")
                else:
                    print(f"Error setting {prop_name}: {error}")

            elif choice == 2:
                new_setting = duvc.PropSetting(setting.value, duvc.CamMode.Auto)
                success, error = self.set_property_safely(prop_type, prop, new_setting, prop_name)
                if success:
                    print(f"{prop_name} set to auto mode")
                else:
                    print(f"Error setting {prop_name} to auto: {error}")

            elif choice == 3:
                new_setting = duvc.PropSetting(setting.value, duvc.CamMode.Manual)
                success, error = self.set_property_safely(prop_type, prop, new_setting, prop_name)
                if success:
                    print(f"{prop_name} set to manual mode")
                else:
                    print(f"Error setting {prop_name} to manual: {error}")

            elif choice == 4:
                new_setting = duvc.PropSetting(prop_range.default_val, prop_range.default_mode)
                success, error = self.set_property_safely(prop_type, prop, new_setting, prop_name)
                if success:
                    print(f"{prop_name} reset to default")
                else:
                    print(f"Error resetting {prop_name}: {error}")

        except ValueError:
            print("Invalid input!")

        input("Press Enter to continue...")

    def ptz_control(self):
        """PTZ control menu"""
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
                    self.control_single_property("camera", duvc.CamProp.Pan, "Pan")
                elif choice == 2:
                    self.control_single_property("camera", duvc.CamProp.Tilt, "Tilt")
                elif choice == 3:
                    self.control_single_property("camera", duvc.CamProp.Zoom, "Zoom")
                elif choice == 4:
                    self.control_single_property("camera", duvc.CamProp.Focus, "Focus")
                elif choice == 5:
                    self.control_single_property("camera", duvc.CamProp.Exposure, "Exposure")
                elif choice == 6:
                    self.center_camera()
                else:
                    print("Invalid option!")
            except ValueError:
                print("Invalid input!")

    def center_camera(self):
        """Center camera (Pan=0, Tilt=0)"""
        print("\n--- Centering Camera ---")
        
        # Center Pan
        pan_setting = duvc.PropSetting(0, duvc.CamMode.Manual)
        success, error = self.set_property_safely("camera", duvc.CamProp.Pan, pan_setting, "Pan")
        if success:
            print("Pan centered to 0")
        else:
            print(f"Error centering Pan: {error}")

        # Center Tilt
        tilt_setting = duvc.PropSetting(0, duvc.CamMode.Manual)
        success, error = self.set_property_safely("camera", duvc.CamProp.Tilt, tilt_setting, "Tilt")
        if success:
            print("Tilt centered to 0")
        else:
            print(f"Error centering Tilt: {error}")

        input("Press Enter to continue...")

    def video_properties(self):
        """Video properties control menu"""
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
                    self.control_single_property("video", duvc.VidProp.Brightness, "Brightness")
                elif choice == 2:
                    self.control_single_property("video", duvc.VidProp.Contrast, "Contrast")
                elif choice == 3:
                    self.control_single_property("video", duvc.VidProp.Saturation, "Saturation")
                elif choice == 4:
                    self.control_single_property("video", duvc.VidProp.WhiteBalance, "White Balance")
                elif choice == 5:
                    self.control_single_property("video", duvc.VidProp.Hue, "Hue")
                elif choice == 6:
                    self.control_single_property("video", duvc.VidProp.Gamma, "Gamma")
                else:
                    print("Invalid option!")
            except ValueError:
                print("Invalid input!")

    def camera_properties(self):
        """Camera properties control menu"""
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

    def show_all_properties(self):
        """Show all supported properties and their current values"""
        print(f"\n--- Supported Properties: {self.current_device.name} ---")

        camera_props = [
            (duvc.CamProp.Pan, "Pan"),
            (duvc.CamProp.Tilt, "Tilt"),
            (duvc.CamProp.Roll, "Roll"),
            (duvc.CamProp.Zoom, "Zoom"),
            (duvc.CamProp.Exposure, "Exposure"),
            (duvc.CamProp.Iris, "Iris"),
            (duvc.CamProp.Focus, "Focus"),
        ]

        video_props = [
            (duvc.VidProp.Brightness, "Brightness"),
            (duvc.VidProp.Contrast, "Contrast"),
            (duvc.VidProp.Saturation, "Saturation"),
            (duvc.VidProp.WhiteBalance, "WhiteBalance"),
            (duvc.VidProp.Hue, "Hue"),
            (duvc.VidProp.Gamma, "Gamma"),
        ]

        print("\nCamera Properties:")
        for prop, name in camera_props:
            setting, error = self.get_property_safely("camera", prop, name)
            if error:
                print(f"  {name}: Error - {error}")
            else:
                print(f"  {name}: {setting.value} ({duvc.to_string(setting.mode)})")

        print("\nVideo Properties:")
        for prop, name in video_props:
            setting, error = self.get_property_safely("video", prop, name)
            if error:
                print(f"  {name}: Error - {error}")
            else:
                print(f"  {name}: {setting.value} ({duvc.to_string(setting.mode)})")

        input("\nPress Enter to continue...")

    def custom_property_control(self):
        """Custom property control interface"""
        print("\n--- Custom Property Control ---")
        print("Camera Properties:")
        print("1. Pan  2. Tilt  3. Roll  4. Zoom")
        print("5. Exposure  6. Iris  7. Focus")
        print("\nVideo Properties:")
        print("11. Brightness  12. Contrast  13. Saturation")
        print("14. White Balance  15. Hue  16. Gamma")

        try:
            choice = int(input("\nEnter property number: "))
            
            prop_map = {
                1: ("camera", duvc.CamProp.Pan, "Pan"),
                2: ("camera", duvc.CamProp.Tilt, "Tilt"),
                3: ("camera", duvc.CamProp.Roll, "Roll"),
                4: ("camera", duvc.CamProp.Zoom, "Zoom"),
                5: ("camera", duvc.CamProp.Exposure, "Exposure"),
                6: ("camera", duvc.CamProp.Iris, "Iris"),
                7: ("camera", duvc.CamProp.Focus, "Focus"),
                11: ("video", duvc.VidProp.Brightness, "Brightness"),
                12: ("video", duvc.VidProp.Contrast, "Contrast"),
                13: ("video", duvc.VidProp.Saturation, "Saturation"),
                14: ("video", duvc.VidProp.WhiteBalance, "White Balance"),
                15: ("video", duvc.VidProp.Hue, "Hue"),
                16: ("video", duvc.VidProp.Gamma, "Gamma"),
            }

            if choice in prop_map:
                prop_type, prop, name = prop_map[choice]
                self.control_single_property(prop_type, prop, name)
            else:
                print("Invalid property number!")
                input("Press Enter to continue...")

        except ValueError:
            print("Invalid input!")
            input("Press Enter to continue...")

    def show_device_capabilities(self):
        """Show device capabilities"""
        if not self.current_device:
            print("No camera selected!")
            input("Press Enter to continue...")
            return

        print(f"\n--- Device Capabilities: {self.current_device.name} ---")

        try:
            # Get device capabilities - this returns a Result<DeviceCapabilities>
            caps_result = duvc.get_device_capabilities(self.current_device)
            if not caps_result.is_ok():
                print(f"Error getting capabilities: {caps_result.error().description()}")
                input("Press Enter to continue...")
                return

            capabilities = caps_result.value()

            print(f"\nDevice accessible: {capabilities.is_device_accessible()}")
            
            print("\nSupported Camera Properties:")
            cam_props = capabilities.supported_camera_properties()
            for prop in cam_props:
                print(f"  - {duvc.to_string(prop)}")

            print("\nSupported Video Properties:")
            vid_props = capabilities.supported_video_properties()
            for prop in vid_props:
                print(f"  - {duvc.to_string(prop)}")

        except Exception as e:
            print(f"Error: {e}")

        input("\nPress Enter to continue...")

    def run(self):
        """Main menu loop"""
        while True:
            print("\n" + "="*60)
            print("         DirectShow UVC Camera Controller")
            print("="*60)
            print(f"Found {len(self.devices)} camera(s)")
            
            if self.current_device:
                print(f"Current device: [{self.current_device_index}] {self.current_device.name}")
            else:
                print("No camera selected")

            print("\nMain Menu:")
            print("1. List all cameras")
            print("2. Select camera")
            print("3. Check camera status")
            print("4. PTZ Control")
            print("5. Video Properties")
            print("6. Camera Properties")
            print("7. Show device capabilities")
            print("0. Exit")
            print("-" * 60)

            try:
                choice = int(input("Enter your choice: "))
                if choice == 0:
                    break
                elif choice == 1:
                    self.list_cameras()
                elif choice == 2:
                    self.select_camera()
                elif choice == 3:
                    self.check_status()
                elif choice == 4:
                    self.ptz_control()
                elif choice == 5:
                    self.video_properties()
                elif choice == 6:
                    self.camera_properties()
                elif choice == 7:
                    self.show_device_capabilities()
                else:
                    print("Invalid choice!")
                    input("Press Enter to continue...")

            except ValueError:
                print("Invalid input!")
                input("Press Enter to continue...")
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break

def main():
    """Main function"""
    print("Starting DirectShow UVC Camera Controller...")
    
    try:
        controller = CameraController()
        controller.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
