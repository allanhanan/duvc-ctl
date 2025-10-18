"""
test.py - duvc-ctl wheel installation test
Verifies core functionality without requiring connected cameras
"""

def test_basic_import():
    """Test module import"""
    print("Testing import...")
    try:
        import duvc_ctl as duvc
        print("PASS: Module imported successfully")
        return True, duvc
    except ImportError as e:
        print(f"FAIL: Import error - {e}")
        return False, None

def test_enums(duvc):
    """Test enum definitions"""
    print("Testing enums...")
    try:
        # Camera properties
        pan = duvc.CamProp.Pan
        tilt = duvc.CamProp.Tilt
        zoom = duvc.CamProp.Zoom
        
        # Video properties  
        brightness = duvc.VidProp.Brightness
        contrast = duvc.VidProp.Contrast
        
        # Modes
        auto = duvc.CamMode.Auto
        manual = duvc.CamMode.Manual
        
        print("PASS: All enums accessible")
        return True
    except AttributeError as e:
        print(f"FAIL: Enum error - {e}")
        return False

def test_basic_classes(duvc):
    """Test basic class creation"""
    print("Testing class creation...")
    try:
        # PropSetting
        setting = duvc.PropSetting(100, duvc.CamMode.Manual)
        assert setting.value == 100
        assert setting.mode == duvc.CamMode.Manual
        
        # PropRange
        prop_range = duvc.PropRange()
        prop_range.min = 0
        prop_range.max = 255
        prop_range.step = 1
        prop_range.default_val = 128
        prop_range.default_mode = duvc.CamMode.Auto
        
        print("PASS: Basic classes work")
        return True
    except Exception as e:
        print(f"FAIL: Class creation error - {e}")
        return False

def test_device_enumeration(duvc):
    """Test device enumeration (core functionality)"""
    print("Testing device enumeration...")
    try:
        devices = duvc.list_devices()
        print(f"PASS: Found {len(devices)} devices")
        
        if devices:
            device = devices[0]
            print(f"  Device name: {device.name}")
            print(f"  Device path: {device.path}")
            print(f"  Device valid: {device.is_valid()}")
            
            # Test connection check
            connected = duvc.is_device_connected(device)
            print(f"  Connected: {connected}")
        else:
            print("  No cameras found (expected if none connected)")
            
        return True
    except Exception as e:
        print(f"FAIL: Device enumeration error - {e}")
        return False

def test_string_functions(duvc):
    """Test string conversion utilities"""
    print("Testing string functions...")
    try:
        pan_str = duvc.to_string(duvc.CamProp.Pan)
        brightness_str = duvc.to_string(duvc.VidProp.Brightness)
        auto_str = duvc.to_string(duvc.CamMode.Auto)
        
        assert pan_str == "Pan"
        assert brightness_str == "Brightness"  
        assert auto_str == "Auto"
        
        print("PASS: String conversion works")
        return True
    except Exception as e:
        print(f"FAIL: String function error - {e}")
        return False

def test_result_types(duvc):
    """Test Result type accessibility"""
    print("Testing Result types...")
    try:
        # These should be accessible even without hardware
        devices = duvc.list_devices()
        
        # Test with device if available
        if devices:
            device = devices[0]
            
            # This returns a Result without requiring camera open
            caps_result = duvc.get_device_capabilities(device)
            print(f"  Capabilities query: {'OK' if caps_result.is_ok() else 'Error'}")
            
        print("PASS: Result types accessible")
        return True
    except Exception as e:
        print(f"FAIL: Result types error - {e}")
        return False

def run_tests():
    """Run all tests and report results"""
    print("=" * 50)
    print("duvc-ctl Wheel Installation Test")
    print("=" * 50)
    
    # Test 1: Import
    success, duvc = test_basic_import()
    if not success:
        print("\nOverall result: FAILED - Cannot import module")
        return False
    
    # Test 2-6: Core functionality
    tests = [
        ("Enums", lambda: test_enums(duvc)),
        ("Classes", lambda: test_basic_classes(duvc)),
        ("Device enumeration", lambda: test_device_enumeration(duvc)),
        ("String functions", lambda: test_string_functions(duvc)),
        ("Result types", lambda: test_result_types(duvc)),
    ]
    
    passed = 1  # Import already passed
    total = len(tests) + 1
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
            
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("Overall result: PASSED - Wheel installation successful")
        return True
    else:
        print("Overall result: FAILED - Some functionality missing")
        return False

if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
