## 12. Troubleshooting \& Debugging


### 12.1 Common Issues

**Quick reference for frequent problems and solutions.**

***

#### Issue: No Cameras Detected

**Symptom:**

```cpp
auto devices = duvc::list_devices();
std::cout << "Found " << devices.size() << " cameras\n";  // Prints: Found 0 cameras
```

**Possible causes:**

**Camera not UVC-compliant:**

```cpp
// Check Device Manager → Imaging devices
// If camera appears under "Other devices" or requires vendor driver, it's not UVC
```

**DirectShow not available:**

- Windows N/KN editions lack Media Feature Pack
- Install: Settings → Apps → Optional features → Media Feature Pack

**Antivirus blocking:**

- Check Windows Security → Camera privacy settings
- Ensure application has camera permission

**USB connection issues:**

- Try different USB port
- Check USB selective suspend settings
- Verify camera works in Windows Camera app

***

#### Issue: Property Operations Fail

**Symptom:**

```cpp
auto result = camera.set(CamProp::Exposure, {-5, CamMode::Manual});
if (result.is_error()) {
    std::cout << result.error().description() << std::endl;
    // "Property not supported" or "Operation failed"
}
```

**Check property support:**

```cpp
auto range_result = camera.get_range(CamProp::Exposure);
if (range_result.is_error()) {
    std::cout << "Exposure not supported by this camera\n";
}
```

**Device in use by another application:**

```cpp
// Close: Windows Camera, Skype, Teams, OBS, Zoom, etc.
// Then retry operation
```

**Camera needs reinitialization:**

```cpp
// Unplug and replug camera
// Or use device monitor to detect reconnection
```


***

#### Issue: COM Initialization Failed

**Symptom:**

```
Runtime error: COM initialization failed
```

**Cause:** COM already initialized with incompatible threading model.

**Solution:**

```cpp
// Let duvc-ctl manage COM automatically
Camera camera(0);  // Works

// If you must initialize COM yourself:
HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
// duvc-ctl will detect and use existing COM initialization
```


***

#### Issue: Crashes or Access Violations

**Common causes:**

**Using camera object after device disconnect:**

```cpp
Camera camera(0);
// ... camera unplugged ...
camera.set(CamProp::Pan, {0, CamMode::Manual});  // CRASH

// Fix: Always check validity
if (!camera.is_valid()) {
    std::cerr << "Camera disconnected\n";
    return;
}
```

**Thread safety violation:**

```cpp
// WRONG: Passing camera between threads
Camera camera(0);
std::thread t([&camera]() {
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});  // CRASH
});

// CORRECT: Create camera in worker thread
std::thread t([]() {
    Camera camera(0);  // COM initialized in this thread
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
});
```


***

#### Issue: Slow Performance

**Symptom:** Operations take several hundred milliseconds.

**Expected timing:** Property queries can take 50-200ms on some cameras.

**Optimization:**

```cpp
// Cache property ranges
std::map<CamProp, PropRange> ranges;
for (auto prop : {CamProp::Pan, CamProp::Tilt}) {
    auto range = camera.get_range(prop);
    if (range.is_ok()) {
        ranges[prop] = range.value();
    }
}

// Use cached values for validation
if (ranges[CamProp::Pan].is_valid(value)) {
    camera.set(CamProp::Pan, {value, CamMode::Manual});
}
```


***

#### Issue: Property Values Incorrect

**Symptom:** `get()` returns unexpected value after `set()`.

**Cameras may clamp to nearest valid value:**

```cpp
camera.set(CamProp::Brightness, {127, CamMode::Manual});
auto result = camera.get(CamProp::Brightness);
std::cout << result.value().value << std::endl;  // May print 128 (step size)
```

**Check property range:**

```cpp
auto range = camera.get_range(CamProp::Brightness);
if (range.is_ok()) {
    std::cout << "Step: " << range.value().step << std::endl;
    // Use step-aligned value
    int aligned = (value / range.value().step) * range.value().step;
}
```


***

#### Issue: DLL Load Failures (Python/C API)

**Symptom:**

```
ImportError: DLL load failed: The specified module could not be found.
```

**Solutions:**

**Install Visual C++ Redistributable:**

- Download: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Install and restart

**Check DLL dependencies:**

```powershell
# Use Dependencies.exe or dumpbin
dumpbin /dependents duvc-core.dll
```

**Python-specific:**

```bash
# Ensure correct Python version
python --version  # Should be 3.8+

# Reinstall package
pip uninstall duvc-ctl
pip install duvc-ctl --force-reinstall
```


***

### 12.2 Debugging Techniques

#### Enable Verbose Logging

**Enable full debug output:**

```cpp
#include <duvc-ctl/utils/logging.h>

// Set log level before any operations
duvc::set_log_level(duvc::LogLevel::Debug);

// Set custom log handler
duvc::set_log_callback([](duvc::LogLevel level, const std::string& msg) {
    std::cout << "[" << duvc::to_string(level) << "] " << msg << std::endl;
});

// Now all operations log detailed information
auto devices = duvc::list_devices();
Camera camera(devices);
auto result = camera.set(CamProp::Exposure, {-5, CamMode::Manual});
```

**Output:**

```
[Debug] Initializing COM
[Debug] Enumerating video input devices
[Info] Found 2 camera(s)
[Debug] Creating connection to device: Logitech C920
[Debug] Querying IAMCameraControl interface
[Debug] Setting CamProp::Exposure to -5 (Manual)
[Debug] DirectShow Set() returned 0x00000000 (S_OK)
```


***

#### Inspect HRESULT Error Codes

**Decode Windows error codes:**

```cpp
#include <duvc-ctl/utils/error_decoder.h>

auto result = camera.set(CamProp::Pan, {0, CamMode::Manual});
if (result.is_error()) {
    std::cout << "Error: " << result.error().description() << std::endl;
    
    // Get detailed DirectShow error
    #ifdef _WIN32
    HRESULT hr = /* extract from error */;
    std::string details = duvc::decode_hresult(hr);
    std::cout << "HRESULT: " << details << std::endl;
    
    // Check error category
    if (duvc::is_device_error(hr)) {
        std::cout << "Device-specific error\n";
    }
    if (duvc::is_permission_error(hr)) {
        std::cout << "Permission denied\n";
    }
    #endif
}
```

**Common HRESULT values:**


| HRESULT | Code | Meaning |
| :-- | :-- | :-- |
| `S_OK` | `0x00000000` | Success |
| `E_FAIL` | `0x80004005` | Unspecified failure |
| `E_INVALIDARG` | `0x80070057` | Invalid argument |
| `E_PROP_ID_UNSUPPORTED` | `0x80070490` | Property not supported |
| `VFW_E_NOT_CONNECTED` | `0x80040209` | Filter not connected |


***

#### Device Capability Inspection

**Complete capability dump:**

```cpp
void dump_camera_capabilities(const Device& device) {
    std::cout << "=== Camera Capabilities ===" << std::endl;
    std::cout << "Name: " << duvc::to_utf8(device.name) << std::endl;
    std::cout << "Path: " << duvc::to_utf8(device.path) << std::endl << std::endl;
    
    Camera camera(device);
    
    // Camera properties
    std::cout << "Camera Properties (IAMCameraControl):" << std::endl;
    std::vector<CamProp> cam_props = {
        CamProp::Pan, CamProp::Tilt, CamProp::Roll, CamProp::Zoom,
        CamProp::Exposure, CamProp::Iris, CamProp::Focus,
        CamProp::Privacy, CamProp::BacklightCompensation
    };
    
    for (auto prop : cam_props) {
        auto range = camera.get_range(prop);
        if (range.is_ok()) {
            const auto& r = range.value();
            std::cout << "  " << to_string(prop) << ":" << std::endl;
            std::cout << "    Range: [" << r.min << ", " << r.max << "]" << std::endl;
            std::cout << "    Step: " << r.step << std::endl;
            std::cout << "    Default: " << r.default_val 
                      << " (" << to_string(r.default_mode) << ")" << std::endl;
            
            // Current value
            auto current = camera.get(prop);
            if (current.is_ok()) {
                std::cout << "    Current: " << current.value().value
                          << " (" << to_string(current.value().mode) << ")" << std::endl;
            }
        }
    }
    
    // Video properties
    std::cout << "\nVideo Properties (IAMVideoProcAmp):" << std::endl;
    std::vector<VidProp> vid_props = {
        VidProp::Brightness, VidProp::Contrast, VidProp::Hue,
        VidProp::Saturation, VidProp::Sharpness, VidProp::Gamma,
        VidProp::WhiteBalance, VidProp::BacklightCompensation, VidProp::Gain
    };
    
    for (auto prop : vid_props) {
        auto range = camera.get_range(prop);
        if (range.is_ok()) {
            const auto& r = range.value();
            std::cout << "  " << to_string(prop) << ": [" 
                      << r.min << ", " << r.max << "], step=" << r.step << std::endl;
        }
    }
}
```


***

#### Monitor Device Events

**Track connect/disconnect:**

```cpp
#include <duvc-ctl/platform/device_monitor.h>

void monitor_devices() {
    auto callback = [](bool added, const std::wstring& path) {
        if (added) {
            std::wcout << L"Camera connected: " << path << std::endl;
            
            // Reapply settings
            auto devices = duvc::list_devices();
            for (const auto& dev : devices) {
                if (dev.path == path) {
                    Camera camera(dev);
                    // Apply saved settings
                    break;
                }
            }
        } else {
            std::wcout << L"Camera disconnected: " << path << std::endl;
        }
    };
    
    duvc::register_device_change_callback(callback);
    
    // Keep monitoring (blocking or in separate thread)
    std::cout << "Monitoring for device changes... Press Enter to stop" << std::endl;
    std::cin.get();
}
```


***

#### Step-by-Step Operation Trace

**Trace each DirectShow call:**

```cpp
// Enable maximum verbosity
duvc::set_log_level(duvc::LogLevel::Debug);

std::cout << "Step 1: Initialize platform" << std::endl;
auto platform = duvc::create_platform_interface();

std::cout << "Step 2: List devices" << std::endl;
auto devices_result = platform->list_devices();
if (!devices_result.is_ok()) {
    std::cout << "Failed: " << devices_result.error().description() << std::endl;
    return;
}

std::cout << "Step 3: Create connection" << std::endl;
auto connection_result = platform->create_connection(devices_result.value());
if (!connection_result.is_ok()) {
    std::cout << "Failed: " << connection_result.error().description() << std::endl;
    return;
}

auto connection = std::move(connection_result.value());

std::cout << "Step 4: Query property range" << std::endl;
auto range_result = connection->get_camera_property_range(CamProp::Pan);
if (!range_result.is_ok()) {
    std::cout << "Failed: " << range_result.error().description() << std::endl;
    return;
}

std::cout << "Step 5: Set property" << std::endl;
PropSetting setting{0, CamMode::Manual};
auto set_result = connection->set_camera_property(CamProp::Pan, setting);
if (!set_result.is_ok()) {
    std::cout << "Failed: " << set_result.error().description() << std::endl;
    return;
}

std::cout << "Success!" << std::endl;
```


***

### 12.3 Diagnostic Tools

#### Built-in Diagnostic Script

**Create comprehensive diagnostic report:**

```cpp
#include <duvc-ctl/duvc.hpp>
#include <duvc-ctl/utils/logging.h>
#include <duvc-ctl/utils/error_decoder.h>
#include <fstream>

void generate_diagnostic_report(const std::string& filename) {
    std::ofstream report(filename);
    
    // System information
    report << "=== System Diagnostics ===" << std::endl;
    report << "Operating System: Windows" << std::endl;
    report << "duvc-ctl Version: " << DUVC_VERSION << std::endl;
    report << std::endl;
    
    // COM initialization test
    report << "=== COM Initialization ===" << std::endl;
    HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    if (SUCCEEDED(hr)) {
        report << "Status: OK" << std::endl;
        CoUninitialize();
    } else {
        report << "Status: FAILED (0x" << std::hex << hr << ")" << std::endl;
        report << "Details: " << duvc::decode_hresult(hr) << std::endl;
    }
    report << std::endl;
    
    // Device enumeration
    report << "=== Device Enumeration ===" << std::endl;
    auto devices = duvc::list_devices();
    report << "Found " << devices.size() << " camera(s)" << std::endl;
    
    for (size_t i = 0; i < devices.size(); ++i) {
        report << std::endl << "Camera " << i << ":" << std::endl;
        report << "  Name: " << duvc::to_utf8(devices[i].name) << std::endl;
        report << "  Path: " << duvc::to_utf8(devices[i].path) << std::endl;
        
        // Test connection
        try {
            Camera camera(devices[i]);
            report << "  Connection: OK" << std::endl;
            
            // Test basic property
            auto range = camera.get_range(VidProp::Brightness);
            if (range.is_ok()) {
                report << "  Basic property access: OK" << std::endl;
            } else {
                report << "  Basic property access: FAILED" << std::endl;
                report << "    " << range.error().description() << std::endl;
            }
            
        } catch (const std::exception& e) {
            report << "  Connection: FAILED" << std::endl;
            report << "    " << e.what() << std::endl;
        }
    }
    
    report << std::endl << "=== Diagnostic Complete ===" << std::endl;
    report.close();
    
    std::cout << "Diagnostic report saved to: " << filename << std::endl;
}
```


***

#### GraphEdit (DirectShow Debugging)

**Use Microsoft GraphEdit to inspect DirectShow:**

**Download:** Windows SDK Tools

**Usage:**

1. Open GraphEdit.exe
2. Graph → Insert Filters → Video Input Device
3. Select your camera
4. Right-click filter → Properties
5. Inspect IAMCameraControl and IAMVideoProcAmp tabs

**Benefits:**

- See raw DirectShow capabilities
- Test property changes directly
- Identify if issue is camera or library

***

#### Windows Device Manager

**Check camera registration:**

1. Open Device Manager (devmgmt.msc)
2. Expand "Imaging devices" or "Cameras"
3. Right-click camera → Properties

**Check:**

- Driver status (should be "Working properly")
- Device class GUID: `{ca3e7ab9-b4c3-4ae6-8251-579ef933890f}` (video capture)
- Hardware IDs contain `USB\VID_` and `PID_`

**If camera appears under "Other devices:"**

- Not recognized as UVC device
- Requires vendor driver
- duvc-ctl won't work

***

#### Process Monitor (Sysinternals)

**Track library interactions:**

**Download:** https://learn.microsoft.com/en-us/sysinternals/downloads/procmon

**Usage:**

1. Run procmon.exe as Administrator
2. Add filter: Process Name → your_app.exe
3. Add filter: Path → contains → "duvc" or "camera"
4. Run your application
5. Observe file, registry, and DLL access

**Look for:**

- Missing DLL dependencies
- Registry access denied
- Device path lookups

***

#### WinDbg (Advanced Crash Analysis)

**Debug crashes in DirectShow:**

**Download:** Windows SDK

**Usage:**

```
windbg.exe your_app.exe
> .sympath+ C:\path\to\duvc-ctl\symbols
> g  (run)
> (crash occurs)
> !analyze -v
> k  (stack trace)
```

**Common crash causes:**

- COM interface called from wrong thread
- Use-after-free of device filter
- NULL pointer from failed QueryInterface

***

#### Custom Test Harness

**Minimal reproduction case:**

```cpp
// test_camera.cpp
#include <duvc-ctl/duvc.hpp>
#include <duvc-ctl/utils/logging.h>
#include <iostream>

int main() {
    try {
        // Enable logging
        duvc::set_log_level(duvc::LogLevel::Debug);
        duvc::set_log_callback([](duvc::LogLevel level, const std::string& msg) {
            std::cout << "[" << duvc::to_string(level) << "] " << msg << std::endl;
        });
        
        std::cout << "Test 1: List devices" << std::endl;
        auto devices = duvc::list_devices();
        std::cout << "Result: " << devices.size() << " device(s)" << std::endl;
        
        if (devices.empty()) {
            std::cout << "No cameras found. Test complete." << std::endl;
            return 0;
        }
        
        std::cout << "\nTest 2: Create camera" << std::endl;
        Camera camera(devices);
        std::cout << "Result: Success" << std::endl;
        
        std::cout << "\nTest 3: Get brightness range" << std::endl;
        auto range = camera.get_range(VidProp::Brightness);
        if (range.is_ok()) {
            std::cout << "Result: [" << range.value().min 
                      << ", " << range.value().max << "]" << std::endl;
        } else {
            std::cout << "Result: " << range.error().description() << std::endl;
        }
        
        std::cout << "\nTest 4: Set brightness" << std::endl;
        auto result = camera.set(VidProp::Brightness, {128, CamMode::Manual});
        if (result.is_ok()) {
            std::cout << "Result: Success" << std::endl;
        } else {
            std::cout << "Result: " << result.error().description() << std::endl;
        }
        
        std::cout << "\nAll tests complete." << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
```

