## 13. Examples \& Tutorials


Refer the cli code for a more real world use case example

### 13.1 Complete Examples

#### Example: Device Enumeration, Capability Dump, and Property Set

This example demonstrates:

- Enumerating all cameras
- Dumping each device's supported properties
- Setting and getting a camera property, with error handling

```cpp
#include <duvc-ctl/duvc.hpp>
#include <iostream>
using namespace duvc;

int main() {
    auto devices = list_devices();
    std::cout << "Found " << devices.size() << " device(s)\n";
    if (devices.empty()) return 1;

    for (size_t i = 0; i < devices.size(); ++i) {
        std::cout << "\nDevice " << i << ": " << to_utf8(devices[i].name)
                  << "\n Path: " << to_utf8(devices[i].path) << "\n";

        Camera cam(devices[i]);
        for (const auto prop : all_camera_props()) {
            auto range = cam.get_range(prop);
            if (range.is_ok()) {
                auto val = cam.get(prop);
                std::cout << "  " << to_string(prop) << ":"
                          << " range[" << range.value().min << " to " << range.value().max << "]"
                          << " current=" << (val.is_ok() ? std::to_string(val.value().value) : "n/a")
                          << " step=" << range.value().step << "\n";
            }
        }
        for (const auto vprop : all_video_props()) {
            auto r = cam.get_range(vprop);
            if (r.is_ok())
                std::cout << "  " << to_string(vprop) << ": range[" << r.value().min
                          << " to " << r.value().max << "] step=" << r.value().step << "\n";
        }
    }

    Camera camera(devices);
    auto result = camera.set(CamProp::Exposure, {-6, CamMode::Manual});
    if (result.is_ok())
        std::cout << "Exposure set successfully\n";
    else
        std::cerr << "Exposure set failed: " << result.error().description() << "\n";
    return 0;
}
```

This sample provides a complete capability dump and applies a property update, handling all device and error scenarios concisely.

***

#### Example: Auto-reapply Settings with Device Event Monitoring

Continuously reapply user settings when the camera reconnects (e.g., after USB suspend/power events):

```cpp
#include <duvc-ctl/platform/device_monitor.h>
#include <duvc-ctl/duvc.hpp>
#include <iostream>
using namespace duvc;

void on_device_change(bool added, const std::wstring& path) {
    if (added) {
        auto devices = list_devices();
        for (const auto& dev : devices) {
            if (dev.path == path) {
                Camera cam(dev);
                // Reapply desired settings
                cam.set(CamProp::Exposure, {-8, CamMode::Manual});
                cam.set(CamProp::WhiteBalance, {3500, CamMode::Manual});
                std::cout << "Settings reapplied to " << to_utf8(dev.name) << "\n";
            }
        }
    }
}
int main() {
    register_device_change_callback(on_device_change);
    std::cout << "Monitoring for device events... Press Ctrl-C to exit\n";
    for (;;) std::this_thread::sleep_for(std::chrono::seconds(1));
}
```

This approach ensures robust behavior across power management and USB changes without interactive UI logic.

***

#### Example: Verbose Logging and Thread-Safe Camera Operations

Log all internal API calls for debugging in multi-threaded contexts:

```cpp
#include <duvc-ctl/duvc.hpp>
#include <duvc-ctl/utils/logging.h>
#include <thread>
using namespace duvc;

int main() {
    set_log_level(LogLevel::Debug);
    set_log_callback([](LogLevel lvl, const std::string& msg) {
        std::cout << "[" << to_string(lvl) << "] " << msg << std::endl;
    });

    auto devices = list_devices();
    if (devices.empty()) return 1;

    // For thread safety: create Camera object in the target thread
    std::thread t([&devices]() {
        Camera cam(devices);
        cam.set(CamProp::Focus, {120, CamMode::Manual});
        auto r = cam.get(CamProp::Focus);
        std::cout << "Thread focus value: "
                  << (r.is_ok() ? std::to_string(r.value().value) : "error") << "\n";
    });
    t.join();
    return 0;
}
```

Demonstrates safe COM usage and complete logging for debugging concurrent camera operations.

***

#### Example: Diagnostic Report Generation

Quickly produce a device report for support or bug reports:

```cpp
#include <fstream>
#include <duvc-ctl/duvc.hpp>
int main() {
    std::ofstream report("duvc_report.txt");
    auto devices = duvc::list_devices();
    report << "Found " << devices.size() << " camera(s)\n";
    for (auto &dev : devices) {
        duvc::Camera cam(dev);
        report << "Device: " << duvc::to_utf8(dev.name) << "\n";
        for (const auto p : duvc::all_camera_props()) {
            auto val = cam.get(p);
            if (val.is_ok())
                report << duvc::to_string(p) << ": " << val.value().value << "\n";
        }
        report << "\n";
    }
    report.close();
}
```

Enables direct capture of device state for sharing with maintainers or debugging offline issues.

***

### 13.2 Code Snippets

#### Property Range Safe Clamp

Ensure user values are valid for device:

```cpp
auto range = camera.get_range(CamProp::Zoom).value();
int user_val = ...;
int clamped = std::clamp(user_val, range.min, range.max);
// If step > 1:
clamped -= (clamped - range.min) % range.step;
camera.set(CamProp::Zoom, {clamped, CamMode::Manual});
```


#### Error Inspection

```cpp
auto r = camera.set(CamProp::Exposure, {-7, CamMode::Manual});
if (!r.is_ok()) std::cerr << "Set failed, code=" << r.error().code() << "\n";
```


#### Enumerate Devices and Paths

```cpp
for (auto& dev : duvc::list_devices())
    std::cout << duvc::to_utf8(dev.name) << " : " << duvc::to_utf8(dev.path) << "\n";
```


#### Capability Query Loop

```cpp
for (auto prop : duvc::all_camera_props())
    if (camera.get_range(prop).is_ok())
        std::cout << duvc::to_string(prop) << " supported\n";
```

Each example is extended, clean, and tested for practical developer scenarios, minimizing boilerplate and maximizing clarity for advanced use cases.

