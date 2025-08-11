"""
Comprehensive test suite for duvc_ctl Python package.

This module provides thorough testing of the duvc_ctl package installation,
API availability, and basic functionality. Designed for CI/CD integration
and local development validation.
"""

import sys
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional


class DuvcTestRunner:
    """
    Test runner for duvc_ctl package validation.
    
    Performs comprehensive checks on package installation, module structure,
    API completeness, and basic functionality without requiring actual hardware.
    """
    
    def __init__(self):
        self.test_results = {}
        self.duvc_module = None
        self.failure_count = 0
        
    def log_result(self, test_name: str, success: bool, message: str, details: Optional[str] = None):
        """Log test result with standardized format."""
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}: {message}")
        if details and not success:
            print(f"    Details: {details}")
        if not success:
            self.failure_count += 1
        self.test_results[test_name] = {"success": success, "message": message, "details": details}
    
    def test_package_import(self) -> bool:
        """
        Test basic package import functionality.
        
        Returns:
            bool: True if import succeeds, False otherwise.
        """
        try:
            import duvc_ctl as duvc
            self.duvc_module = duvc
            self.log_result("Package Import", True, "duvc_ctl imported successfully")
            return True
        except ImportError as e:
            self.log_result("Package Import", False, "Failed to import duvc_ctl", str(e))
            return False
        except Exception as e:
            self.log_result("Package Import", False, "Unexpected error during import", str(e))
            return False
    
    def test_package_metadata(self) -> bool:
        """
        Validate package metadata attributes.
        
        Returns:
            bool: True if all expected metadata is present, False otherwise.
        """
        if not self.duvc_module:
            self.log_result("Package Metadata", False, "Module not available for testing")
            return False
        
        metadata_checks = [
            ("__version__", "Package version"),
            ("__author__", "Author information"),
        ]
        
        all_passed = True
        for attr, description in metadata_checks:
            if hasattr(self.duvc_module, attr):
                value = getattr(self.duvc_module, attr)
                if value:
                    self.log_result(f"Metadata - {description}", True, f"{attr} = {value}")
                else:
                    self.log_result(f"Metadata - {description}", False, f"{attr} is empty")
                    all_passed = False
            else:
                self.log_result(f"Metadata - {description}", False, f"Missing {attr} attribute")
                all_passed = False
        
        return all_passed
    
    def test_internal_module_import(self) -> bool:
        """
        Test import of internal C++ extension module.
        
        Returns:
            bool: True if internal module imports successfully, False otherwise.
        """
        try:
            from duvc_ctl import _duvc_ctl
            self.log_result("Internal Module Import", True, "C++ extension module accessible")
            
            # Check that internal module has expected attributes
            internal_attrs = [attr for attr in dir(_duvc_ctl) if not attr.startswith('__')]
            if internal_attrs:
                self.log_result("Internal Module Content", True, f"Found {len(internal_attrs)} exported symbols")
            else:
                self.log_result("Internal Module Content", False, "No symbols exported from C++ module")
                return False
                
            return True
        except ImportError as e:
            self.log_result("Internal Module Import", False, "Cannot access C++ extension", str(e))
            return False
    
    def test_api_completeness(self) -> bool:
        """
        Verify that expected API elements are available.
        
        Returns:
            bool: True if all critical API elements exist, False otherwise.
        """
        if not self.duvc_module:
            self.log_result("API Completeness", False, "Module not available for testing")
            return False
        
        # Define expected API elements organized by category
        expected_api = {
            "Functions": ["list_devices"],
            "Classes": ["Device", "PropSetting", "PropRange"],
            "Enums": ["CamProp", "VidProp", "CamMode"]
        }
        
        missing_elements = []
        available_elements = []
        
        for category, elements in expected_api.items():
            for element in elements:
                if hasattr(self.duvc_module, element):
                    available_elements.append(f"{category}.{element}")
                else:
                    missing_elements.append(f"{category}.{element}")
        
        if missing_elements:
            self.log_result("API Completeness", False, 
                          f"Missing {len(missing_elements)} elements", 
                          f"Missing: {', '.join(missing_elements)}")
            return False
        else:
            self.log_result("API Completeness", True, 
                          f"All {len(available_elements)} expected API elements present")
            return True
    
    def test_enum_accessibility(self) -> bool:
        """
        Test that enumeration types are properly accessible and have expected values.
        
        Returns:
            bool: True if enums are accessible, False otherwise.
        """
        if not self.duvc_module:
            self.log_result("Enum Accessibility", False, "Module not available for testing")
            return False
        
        enum_tests = [
            ("CamProp", ["Pan", "Tilt", "Zoom"]),
            ("VidProp", ["Brightness", "Contrast"]),
            ("CamMode", ["Auto", "Manual"])
        ]
        
        all_passed = True
        for enum_name, expected_values in enum_tests:
            if hasattr(self.duvc_module, enum_name):
                enum_obj = getattr(self.duvc_module, enum_name)
                
                # Check if expected enum values exist
                missing_values = []
                for value in expected_values:
                    if not hasattr(enum_obj, value):
                        missing_values.append(value)
                
                if missing_values:
                    self.log_result(f"Enum - {enum_name}", False, 
                                  f"Missing values: {', '.join(missing_values)}")
                    all_passed = False
                else:
                    self.log_result(f"Enum - {enum_name}", True, 
                                  f"All expected values present")
            else:
                self.log_result(f"Enum - {enum_name}", False, f"Enum not found")
                all_passed = False
        
        return all_passed
    
    def test_basic_functionality(self) -> bool:
        """
        Test basic functionality without requiring hardware.
        
        Returns:
            bool: True if basic functions can be called, False otherwise.
        """
        if not self.duvc_module:
            self.log_result("Basic Functionality", False, "Module not available for testing")
            return False
        
        # Test list_devices function
        if not hasattr(self.duvc_module, 'list_devices'):
            self.log_result("Basic Functionality", False, "list_devices function not available")
            return False
        
        try:
            devices = self.duvc_module.list_devices()
            
            # Function should return a list (even if empty)
            if isinstance(devices, list):
                self.log_result("Basic Functionality", True, 
                              f"list_devices() returned {len(devices)} devices")
                
                # If devices are available, test basic device properties
                if devices and hasattr(devices[0], 'name'):
                    first_device = devices[0]
                    self.log_result("Device Properties", True, 
                                  f"Device has name: {getattr(first_device, 'name', 'Unknown')}")
                
                return True
            else:
                self.log_result("Basic Functionality", False, 
                              f"list_devices() returned unexpected type: {type(devices)}")
                return False
                
        except Exception as e:
            self.log_result("Basic Functionality", False, 
                          "list_devices() raised exception", str(e))
            return False
    
    def test_class_instantiation(self) -> bool:
        """
        Test that key classes can be instantiated.
        
        Returns:
            bool: True if classes can be instantiated, False otherwise.
        """
        if not self.duvc_module:
            self.log_result("Class Instantiation", False, "Module not available for testing")
            return False
        
        # Test PropSetting instantiation if available
        if hasattr(self.duvc_module, 'PropSetting'):
            try:
                # Try to create a PropSetting instance
                # This might require specific parameters based on your implementation
                prop_setting = self.duvc_module.PropSetting()
                self.log_result("Class Instantiation", True, "PropSetting can be instantiated")
                return True
            except TypeError:
                # If default constructor doesn't work, try with parameters
                try:
                    if hasattr(self.duvc_module, 'CamMode'):
                        prop_setting = self.duvc_module.PropSetting(50, self.duvc_module.CamMode.Manual)
                        self.log_result("Class Instantiation", True, "PropSetting can be instantiated with parameters")
                        return True
                except Exception as e:
                    self.log_result("Class Instantiation", False, 
                                  "PropSetting instantiation failed", str(e))
                    return False
            except Exception as e:
                self.log_result("Class Instantiation", False, 
                              "PropSetting instantiation failed", str(e))
                return False
        else:
            self.log_result("Class Instantiation", False, "PropSetting class not available")
            return False
    
    def test_module_structure(self) -> bool:
        """
        Analyze and validate overall module structure.
        
        Returns:
            bool: True if module structure is reasonable, False otherwise.
        """
        if not self.duvc_module:
            self.log_result("Module Structure", False, "Module not available for testing")
            return False
        
        # Get all public attributes (non-underscore prefixed)
        public_attrs = [attr for attr in dir(self.duvc_module) if not attr.startswith('_')]
        private_attrs = [attr for attr in dir(self.duvc_module) if attr.startswith('_') and not attr.startswith('__')]
        
        # Module should have reasonable number of public attributes
        if len(public_attrs) < 3:
            self.log_result("Module Structure", False, 
                          f"Too few public attributes ({len(public_attrs)}), expected at least 3")
            return False
        
        if len(public_attrs) > 50:
            self.log_result("Module Structure", False, 
                          f"Too many public attributes ({len(public_attrs)}), possible namespace pollution")
            return False
        
        self.log_result("Module Structure", True, 
                       f"Reasonable module structure: {len(public_attrs)} public, {len(private_attrs)} private")
        return True
    
    def run_all_tests(self) -> bool:
        """
        Execute complete test suite.
        
        Returns:
            bool: True if all tests pass, False otherwise.
        """
        print("DUVC-CTL Package Test Suite")
        print("=" * 50)
        print(f"Python version: {sys.version}")
        print(f"Platform: {sys.platform}")
        print("-" * 50)
        
        test_methods = [
            self.test_package_import,
            self.test_package_metadata,
            self.test_internal_module_import,
            self.test_api_completeness,
            self.test_enum_accessibility,
            self.test_basic_functionality,
            self.test_class_instantiation,
            self.test_module_structure
        ]
        
        # Execute all tests
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                test_name = test_method.__name__.replace('test_', '').replace('_', ' ').title()
                self.log_result(test_name, False, "Unexpected test failure", str(e))
                traceback.print_exc()
        
        # Print summary
        print("-" * 50)
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        
        print(f"Test Results: {passed_tests}/{total_tests} passed")
        
        if self.failure_count > 0:
            print(f"FAILED: {self.failure_count} test(s) failed")
            
            # List failed tests
            failed_tests = [name for name, result in self.test_results.items() if not result["success"]]
            print("Failed tests:")
            for test_name in failed_tests:
                print(f"  - {test_name}")
            
            return False
        else:
            print("SUCCESS: All tests passed")
            return True
    
    def generate_installation_report(self):
        """Generate report with installation and usage information."""
        print("\n" + "=" * 50)
        print("INSTALLATION AND USAGE INFORMATION")
        print("=" * 50)
        
        project_root = Path(__file__).parent.parent if Path(__file__).parent.parent.exists() else Path.cwd()
        dist_dir = project_root / "dist"
        
        print("Build and Installation:")
        print("  1. Build package: python -m build")
        if dist_dir.exists():
            wheels = list(dist_dir.glob("*.whl"))
            if wheels:
                print(f"  2. Install wheel: pip install {wheels[0].name}")
        print("  3. Test installation: python -c \"import duvc_ctl; print(duvc_ctl.__version__)\"")
        
        print("\nBasic Usage:")
        print("  import duvc_ctl as duvc")
        print("  devices = duvc.list_devices()")
        print("  # Configure camera properties as needed")
        
        if self.duvc_module and hasattr(self.duvc_module, '__version__'):
            print(f"\nInstalled Version: {self.duvc_module.__version__}")


def main():
    """Main test execution entry point."""
    runner = DuvcTestRunner()
    success = runner.run_all_tests()
    
    if not success:
        runner.generate_installation_report()
    
    # Return appropriate exit code for CI/CD integration
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
