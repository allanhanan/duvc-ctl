# duvc-ctl: Windows Camera Control Library

[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](README.md)
[![Language](https://img.shields.io/badge/C%2B%2B-17-blue.svg)](src/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](pyproject.toml)
![Pepy Total Downloads](https://img.shields.io/pepy/dt/duvc-ctl?style=flat&label=pip%20installs)


Windows DirectShow UVC camera control library with C++, Python, and CLI interfaces

[<img src="https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png" width="150" alt="Buy Me A Coffee">](https://www.buymeacoffee.com/allanhanan)

#### duvc-ctl provides direct control over DirectShow API for UVC cameras on Windows programatically. Control PTZ operations, exposure, focus, brightness, and other camera properties without any additional drivers or vendor SDKs from programs with plain code without any hacky ways!

## Features

- **Multi-Language Support**: Native C/C++ API, Python bindings, and CLI tool (others coming soon!)
- **Comprehensive Control**: PTZ operations, camera properties (exposure, focus, iris), video properties (brightness, contrast, saturation)
- **UVC Standard**: Works with any UVC-compliant camera
- **Vendor Extensions**: Support for vendor-specific properties (Logitech, etc.)
- **Ease of use**: Easy to get started with and run compared to direct COM access for devices or protocols like VISCA, ONVIF, etc...

## Quick Start

### Installation

**Python:**
```
pip install duvc-ctl
```

**C/C++:**
```
# vcpkg (coming soon)

vcpkg install duvc-ctl

# Or build from source

git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl
cmake -B build -S .
cmake --build build --config Release
```

### Usage Examples

**Python:**
```
import duvc_ctl as duvc

# List available cameras

devices = duvc.list_devices()
camera = devices

# Set camera properties

camera.set_camera_property(duvc.CamProp.EXPOSURE, value=100, mode=duvc.CamMode.MANUAL)
camera.set_camera_property(duvc.CamProp.ZOOM, value=200, mode=duvc.CamMode.MANUAL)

# Get property ranges

range_info = camera.get_camera_property_range(duvc.CamProp.ZOOM)
print(f"Zoom: {range_info.min} to {range_info.max}, step: {range_info.step}")
```

**C++:**
```
\#include "duvc-ctl/duvc.hpp"

int main() {
auto devices = duvc::list_devices();
auto\& camera = devices;

    // Set manual exposure
    camera.set_camera_property(duvc::CamProp::EXPOSURE, 100, duvc::CamMode::MANUAL);
    
    // Use connection for efficiency
    auto conn = camera.create_connection();
    conn.set_camera_property(duvc::CamProp::ZOOM, 200);
    conn.set_camera_property(duvc::CamProp::FOCUS, 150);
    
    return 0;
    }
```

**CLI:**
```
# List devices

duvc-ctl list

# Get camera property

duvc-ctl get --device 0 --property exposure

# Set property

duvc-ctl set --device 0 --property zoom --value 200 --mode manual

# Center PTZ camera

duvc-ctl set --device 0 --property pan --value 0
duvc-ctl set --device 0 --property tilt --value 0

```

## Documentation

**[Full Documentation](https://allanhanan.github.io/duvc-ctl/)**

- [C API Reference](https://allanhanan.github.io/duvc-ctl/sphinx/api/c/)
- [C++ API Reference](https://allanhanan.github.io/duvc-ctl/sphinx/api/cpp/)
- [Python API Reference](https://allanhanan.github.io/duvc-ctl/sphinx/api/python/)
- [CLI Reference](https://allanhanan.github.io/duvc-ctl/sphinx/api/cli/)
- [Doxygen API Docs](https://allanhanan.github.io/duvc-ctl/doxygen/)

## Use Cases

- **Automated Testing**: Control camera settings programmatically for consistent test environments
- **Live Streaming**: Adjust camera parameters during broadcasts without manual intervention
- **Computer Vision**: Set optimal camera properties for CV pipelines (disable auto-exposure, set fixed focus, etc.)
- **Multi-Camera Systems**: Synchronize settings across multiple cameras
- **Remote Control**: Control PTZ cameras without VISCA or IP protocols

## Platform Support

- **OS**: Windows 8/10/11
- **Cameras**: Any UVC-compliant USB camera
- **Languages**: C, C++ (17+), Python (3.8+)
- **Architectures**: x86_64

## Roadmap

### Current Version
- [ ] Rust bindings
- [ ] vcpkg package
- [ ] winget package
- [ ] Node.js bindings
- [ ] Go bindings
- [ ] Chocolatey package

### Future Versions
- [ ] Connection pooling with thread safety improvements
- [ ] Linux support (v4l2 backend)
- [ ] macOS support (AVFoundation backend)
- [ ] Extended vendor property database

## Building from Source

```
# Clone repository

git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl

# Configure with CMake

cmake -B build -S . -DCMAKE_BUILD_TYPE=Release

# Build

cmake --build build --config Release

```

### Build Requirements
- CMake 3.15+
- Visual Studio 2019+ or compatible C++17 compiler
- Python 3.8+ (for Python bindings)
- pybind11 (bundled as submodule)

## Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

Do Refer [CONTRIBUTING.md](CONTRIBUTING.md) before contributing!

### Testing Requirements

**All Changes Must Include**:

1. **Unit Tests**: For isolated component functionality
2. **Integration Tests**: For real device interaction (if applicable)
3. **Documentation**: Update README and code comments
4. **Error Handling**: Comprehensive error cases


## Support and Community

- **Issues**: [GitHub Issues](https://github.com/allanhanan/duvc-ctl/issues)
- **Discussions**: [GitHub Discussions](https://github.com/allanhanan/duvc-ctl/discussions)
- **Documentation**: [Wiki](https://allanhanan.github.io/duvc-ctl/sphinx/index.html) (coming soon)
- **Examples**: [examples/](examples/) directory


***

## License

**MIT License** - see [LICENSE](LICENSE) for complete details.

**Summary**: You can use, modify, and distribute this library freely, including in commercial projects, with attribution.


## Acknowledgments

- Built on Windows DirectShow API
- Inspired by the lack of a Windows equivalent to Linux's v4l2-ctl and inablility to change camera parameters easily through python/ other languages
