# duvc-ctl: Windows Camera Control Library

[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](README.md)
[![Language](https://img.shields.io/badge/C%2B%2B-17-blue.svg)](src/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](pyproject.toml)
![Pepy Total Downloads](https://img.shields.io/pepy/dt/duvc-ctl?style=flat&label=pip%20installs)




Windows DirectShow UVC camera control library with C++, Python, and CLI interfaces.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Build Instructions](#build-instructions)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Architecture](#architecture)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Overview

duvc-ctl provides direct control over DirectShow API for UVC cameras on Windows. Control PTZ operations, exposure, focus, brightness, and other camera properties without any additional drivers or vendor SDKs

**Key Features:**
- UVC camera enumeration and control
- PTZ (Pan/Tilt/Zoom) operations
- Camera properties (exposure, focus, iris)
- Video properties (brightness, contrast, white balance)
- Device monitoring with hotplug detection
- Connection pooling for performance
- C++17, Python, and CLI interfaces

---

## Installation

### Python
```

pip install duvc-ctl

```

### C++ Package Managers
> **Coming Soon**
```
# vcpkg

vcpkg install duvc-ctl

# Conan

conan install duvc-ctl

# conda-forge

conda install -c conda-forge duvc-ctl

```

### CLI Tool
```
# Chocolatey (coming soon)

choco install duvc-cli
```
**Alternative:** [Download from Releases](https://github.com/allanhanan/duvc-ctl/releases)

### Language Bindings
> **Coming Soon**

| Language | Command | Status |
|:---------|:--------|:-------|
| **Rust** | `cargo add duvc-ctl` | In Development |
| **Go** | `go get github.com/allanhanan/duvc-ctl` | In Development |
| **Node.js** | `npm install duvc-ctl` | In Development |

---

## Quick Start

<table>
<tr>
<td width="50%">

**C++ Example**
```
\#include "duvc-ctl/core.h"

// List cameras
auto devices = duvc::list_devices();
if (devices.empty()) return;

// Get camera property range
duvc::PropRange range;
if (duvc::get_range(devices, duvc::CamProp::Pan, range)) {
std::cout << "Pan range: " << range.min
<< " to " << range.max << std::endl;
}

// Set camera property
duvc::PropSetting setting{0, duvc::CamMode::Manual};
duvc::set(devices, duvc::CamProp::Pan, setting);

```

</td>
<td width="50%">

**Python Example**
```
import duvc_ctl as duvc

# List cameras

devices = duvc.list_devices()
if not devices:
return

# Get property value

setting = duvc.PropSetting()
if duvc.get(devices, duvc.CamProp.Pan, setting):
print(f"Current pan: {setting.value}")

# Set brightness

brightness = duvc.PropSetting(50, duvc.CamMode.Manual)
duvc.set(devices, duvc.VidProp.Brightness, brightness)

```

</td>
</tr>
</table>

### Command Line
```
# List cameras

duvc-cli list

# Get property value

duvc-cli get 0 cam Pan

# Set property value

duvc-cli set 0 cam Pan 0 manual

# Monitor device changes

duvc-cli monitor 30

```

---

## Build Instructions

### Prerequisites
- Windows 10/11
- Visual Studio 2019/2022 or MinGW-w64 (MSVC preferred)
- CMake 3.16+
- Python 3.8+ (for Python bindings)

### Basic Build
```
git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl
mkdir build \&\& cd build

# Configure

cmake -G "Visual Studio 17 2022" -A x64 \
-DDUVC_BUILD_STATIC=ON \
-DDUVC_BUILD_CLI=ON \
-DDUVC_BUILD_PYTHON=ON \
..

# Build

cmake --build . --config Release

```

### Build Options

| Option | Default | Description |
|:-------|:-------:|:------------|
| `DUVC_BUILD_STATIC` | **ON** | Build static library |
| `DUVC_BUILD_SHARED` | OFF | Build shared library |
| `DUVC_BUILD_CLI` | **ON** | Build command-line tool |
| `DUVC_BUILD_PYTHON` | OFF | Build Python bindings |
| `DUVC_WARNINGS_AS_ERRORS` | OFF | Treat warnings as errors |

### Python Package Build
From project root:
```

python -m build

```

---

## API Reference

### Core Types
```
struct Device {
std::wstring name;  // Camera name
std::wstring path;  // Device path
};

struct PropSetting {
int value;          // Property value
CamMode mode;       // Auto or Manual
};

struct PropRange {
int min, max, step; // Value constraints
int default_val;    // Default value
CamMode default_mode;
};

```

### Camera Properties (IAMCameraControl)
```

enum class CamProp {
Pan, Tilt, Roll, Zoom, Exposure, Iris, Focus,
ScanMode, Privacy, PanRelative, TiltRelative,
RollRelative, ZoomRelative, ExposureRelative,
IrisRelative, FocusRelative, PanTilt,
PanTiltRelative, FocusSimple, DigitalZoom,
DigitalZoomRelative, BacklightCompensation, Lamp
};

```

### Video Properties (IAMVideoProcAmp)
```

enum class VidProp {
Brightness, Contrast, Hue, Saturation,
Sharpness, Gamma, ColorEnable, WhiteBalance,
BacklightCompensation, Gain
};

```

### Device Operations
```

// Device enumeration
std::vector<Device> list_devices();
bool is_device_connected(const Device\& dev);
void clear_connection_cache();

// Property control
bool get_range(const Device\&, CamProp, PropRange\&);
bool get(const Device\&, CamProp, PropSetting\&);
bool set(const Device\&, CamProp, const PropSetting\&);
bool get_range(const Device\&, VidProp, PropRange\&);
bool get(const Device\&, VidProp, PropSetting\&);
bool set(const Device\&, VidProp, const PropSetting\&);

// Device monitoring
using DeviceChangeCallback = std::function<void(bool added, const std::wstring\& path)>;
void register_device_change_callback(DeviceChangeCallback callback);
void unregister_device_change_callback();

```

---

## Examples

### Camera Centering
```

// Center PTZ camera
duvc::PropSetting center{0, duvc::CamMode::Manual};
duvc::set(device, duvc::CamProp::Pan, center);
duvc::set(device, duvc::CamProp::Tilt, center);

```

### Property Validation
```

// Check property range before setting
duvc::PropRange range;
if (duvc::get_range(device, duvc::CamProp::Zoom, range)) {
int zoom_value = 50;
if (zoom_value >= range.min \&\& zoom_value <= range.max) {
duvc::PropSetting setting{zoom_value, duvc::CamMode::Manual};
duvc::set(device, duvc::CamProp::Zoom, setting);
}
}

```

### Device Monitoring
```

// Monitor device changes
duvc::register_device_change_callback([](bool added, const std::wstring\& path) {
std::wcout << (added ? L"Added: " : L"Removed: ") << path << std::endl;
});

```

### Python Interactive Demo
```


# Run interactive camera controller

python examples/example.py

```

---

## Architecture

### DirectShow Integration
duvc-ctl uses DirectShow APIs for camera control:
- **ICreateDevEnum**: Device enumeration
- **IAMCameraControl**: PTZ and camera properties
- **IAMVideoProcAmp**: Video processing properties
- **IKsPropertySet**: Vendor-specific extensions

### Connection Pooling
Automatic connection caching improves performance:
- Reduces DirectShow binding overhead (10-50ms per operation)
- Thread-safe connection management
- Automatic cleanup on device disconnect

### Error Handling
Comprehensive error reporting with HRESULT details:
```

try {
auto devices = duvc::list_devices();
} catch (const std::exception\& e) {
std::cout << "Error: " << e.what() << std::endl;
// Includes detailed DirectShow error information
}

```

---

## Testing

### C++ Unit Tests
```

cd tests
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build

```

### Python Import Test
```

cd tests
python test_import.py

```

### Manual Testing
```


# Test CLI

./build/bin/duvc-cli list

# Test Python bindings

cd build/py
python -c "import duvc_ctl; print(len(duvc_ctl.list_devices()))"

```

---

## Platform Support

| Platform | Support Level | Notes |
|:---------|:--------------|:------|
| **Windows 11** | Full Support | Recommended |
| **Windows 10** | Full Support | Fully tested |
| **Windows 8.1** | Compatible | Not actively tested |
| **Other Platforms** | Not Supported | DirectShow is Windows-only |

---

## Performance

### Benchmarks

| Operation | Cold Start | Cached Performance |
|:----------|:-----------|:-------------------|
| Device enumeration | ~50-200ms | ~50-200ms |
| Property operations | ~10-50ms | ~1-5ms |
| Connection pool hit rate | N/A | >95% |

### Threading Model

| Operation | Thread Safety | Notes |
|:----------|:-------------|:------|
| Device enumeration | Thread-safe | Multiple threads OK |
| Property operations | Multi-device safe | Different devices only |
| Same device access | Requires synchronization | Use external mutex |

---

## Troubleshooting

### Common Issues

**No devices found:**
- Check Device Manager for camera under "Imaging devices"
- Test camera with Windows Camera app
- Run as Administrator to check permissions

**Property control fails:**
- Verify property is supported with `get_range()`
- Check value is within valid range
- Ensure no other application is using camera

**Python import fails:**
- Install Visual C++ Redistributable
- Check .pyd file exists in build/py/
- Verify Python path includes build directory

### Debug Build
```

cmake -DCMAKE_BUILD_TYPE=Debug -DDUVC_WARNINGS_AS_ERRORS=ON ..

```

### Verbose Errors
```

// Enable detailed COM error reporting
\#define DUVC_VERBOSE_ERRORS
\#include "duvc-ctl/core.h"

```

---

## Contributing

1. Fork repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request

### Code Style
- C++17 modern features
- RAII for resource management
- Thread-safety documentation
- Comprehensive error handling

### Development Installation
```

pip install git+https://github.com/allanhanan/duvc-ctl.git

```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
