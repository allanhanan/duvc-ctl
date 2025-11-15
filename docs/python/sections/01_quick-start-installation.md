## 1. Quick Start & Installation


### 1.1 Installation

#### System requirements

duvc-ctl is a Windows-only library that relies on the DirectShow multimedia framework. It requires:

- **Windows**: Windows 7 SP1 or later. DirectShow is included with all modern Windows versions.
- **Python**: 3.8 or later (binary wheels support 3.8–3.12).
- **C++ toolchain** (for building from source): Visual Studio 2019+ or Build Tools, CMake 3.16+, and a C++17-compatible compiler.


#### Installation from PyPI

The easiest way to get started is to install the prebuilt binary wheel:

```
pip install duvc-ctl
```

Verify the installation:

```
python -c "import duvcctl; print(duvcctl.__version__)"
```

Binary wheels are available for Windows on Python 3.8–3.12 (64-bit). If your Python version or architecture differs, you'll need to build from source.

#### Building from source

If a prebuilt wheel is not available for your configuration, or if you want to build with custom flags, build from source using CMake.

**Prerequisites:**

- Python development headers (included with most Python distributions).
- CMake 3.16 or later.
- A C++ compiler: Visual Studio 2019 or later, or Build Tools for Visual Studio.
- Git.

**Build steps:**

```
git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl
cmake -B build -G "Visual Studio 17 2022" -A x64 -DDUVCBUILDPYTHON=ON
cmake --build build --config Release
cmake --install build --config Release
```

Replace "Visual Studio 17 2022" with your Visual Studio version if different (e.g., "Visual Studio 16 2019").

**CMake configuration options:**

Common options to pass to the first `cmake` command:

- `DUVCBUILDSHARED` (ON/OFF): Build a shared core library. Default: ON.
- `DUVCBUILDSTATIC` (ON/OFF): Build a static core library. Default: ON.
- `DUVCBUILDCAPI` (ON/OFF): Build the C API for bindings. Default: ON.
- `DUVCBUILDCLI` (ON/OFF): Build the command-line tool. Default: ON.
- `DUVCBUILDPYTHON` (ON/OFF): Build Python bindings. Default: ON.
- `DUVCBUILDTESTS` (ON/OFF): Build tests. Default: OFF.
- `DUVCBUILDEXAMPLES` (ON/OFF): Build examples. Default: OFF.

For example, to build only the Python bindings:

```
cmake -B build -G "Visual Studio 17 2022" -A x64 \
  -DDUVCBUILDSHARED=ON \
  -DDUVCBUILDSTATIC=OFF \
  -DDUVCBUILDCAPI=OFF \
  -DDUVCBUILDCLI=OFF \
  -DDUVCBUILDPYTHON=ON
```


#### Editable installation (development)

For development work on the source code, install in editable mode:

```
pip install -e .
```

This compiles the extension in place and allows you to edit Python files without reinstalling. The underlying C++ code is compiled using scikit-build-core with pybind11. Ensure your toolchain is installed and on PATH before running this command.

#### Wheel repair and distribution

Binary wheels are built in CI and repaired on Windows using `delvewheel` to ensure all runtime dependencies (including required DLLs) are packaged correctly. This minimizes end-user setup complexity when installing from PyPI.

#### Using cibuildwheel

cibuildwheel uses the configured pyproject.toml that takes care of the cmake config, building and repairing wheel automatically

```bash
python -m cibuildwheel --output-dir dist
```

#### Verification

After installation, confirm that the library can enumerate devices:

```python
import duvcctl as duvc

print("duvc-ctl version:", duvc.__version__)

devices = duvc.list_devices()
print("Devices found:", len(devices))
for device in devices:
    print(f"  - {device.name}")
```

If no devices are found, verify that:

1. A camera is physically connected.
2. The camera appears in Device Manager (devmgmt.msc).
3. The camera works in the built-in Windows Camera app.

#### Troubleshooting

**ImportError or missing DLLs:**

- Install the Microsoft Visual C++ Redistributable for your Visual Studio version.
- Verify that your Python is 64-bit if your Windows is 64-bit (or both 32-bit).

**Build errors during `pip install -e .`:**

- Confirm that CMake is installed and visible in PATH: `cmake --version`.
- Confirm your C++ toolchain is on PATH. For Visual Studio, run the build in a Visual Studio Developer Command Prompt.
- Delete the build/ directory and try again: `rmdir /s /q build && pip install -e .`.

**CMake not found:**

- Add CMake to your system PATH, or specify the full path: `pip install -e . --config-settings=cmake.cmake-executable=C:\path\to\cmake.exe`.

**No devices appear:**

- Check the device is recognized by Windows: `wmic logicaldisk get name` or open Device Manager (devmgmt.msc).
- Test the camera with the Windows Camera app to rule out driver issues.
- Enable debug logging to see what the library detects.

**Platform detection warnings:**

The module checks for Windows at import time. Non-Windows platforms will raise an ImportError or warning. duvc-ctl is Windows-only.

### 1.2 Your First Program

duvc-ctl offers two distinct APIs for different needs. The Pythonic API is simpler and better for quick scripts and beginners. The Result-Based API provides explicit error handling without exceptions and is suited for production systems. Both work on the same underlying C++ engine, so you can mix them as needed.

#### Choosing your approach

| Use Case | API | Why |
| :-- | :-- | :-- |
| Quick script, single camera | Pythonic | Automatic device selection, exceptions, minimal code |
| Production application | Result-based | Explicit error handling, detailed diagnostics, no exceptions |
| Learning the library | Pythonic | Simpler syntax, clearer intent, beginner-friendly |
| Detailed error recovery | Result-based | Access error codes and recovery suggestions |
| Concurrent camera access | Either | Both are thread-safe; Result-based gives better control |

#### Pythonic API - Quick Start

The Pythonic API uses property-based access and automatic device management:

```python
import duvc_ctl as duvc

# Connect to first available camera
with duvc.CameraController() as cam:
    # Simple property read/write
    cam.brightness = 75
    print(f"Brightness: {cam.brightness}")
    
    # Direct method calls
    cam.pan = 0              # Center camera
    cam.tilt = -10           # Tilt down
    print(f"Pan: {cam.pan}°, Tilt: {cam.tilt}°")
    
    # Relative movement
    cam.pan_relative(15)     # Move 15° right
    cam.zoom_relative(1)     # Zoom in
```

Find a specific camera:

```python
import duvc_ctl as duvc

try:
    # Find by name pattern (case-insensitive substring)
    cam = duvc.find_camera("Logitech")
    cam.brightness = 80
    cam.close()
except duvc.DeviceNotFoundError:
    print("Camera not found")
```
**Connect using Device object**

The most explicit and reliable method:

```python
import duvc_ctl as duvc

#Enumerate all devices
devices = duvc.list_devices()

if devices:
# Show available cameras
for i, device in enumerate(devices):
print(f"[{i}] {device.name} - {device.path}")

# Connect to first device
with duvc.CameraController(device=devices) as cam:
    cam.brightness = 75
    print(f"Connected to: {cam.device_name}")
else:
print("No cameras found")
```
**Why use Device objects?**
- Full control over which camera to use
- Access to device metadata (name, path, ID)
- Works seamlessly with `list_devices()` enumeration
- Required for advanced scenarios (multi-camera, reconnection)

List available properties:

```python
import duvc_ctl as duvc

with duvc.CameraController() as cam:
    # Enumerate properties
    supported = cam.get_supported_properties()
    
    print("Video properties:")
    for prop in supported['video']:
        value = cam.get(prop)
        print(f"  {prop}: {value}")
    
    print("Camera properties:")
    for prop in supported['camera']:
        value = cam.get(prop)
        print(f"  {prop}: {value}")
```

Batch operations:

```python
import duvc_ctl as duvc

with duvc.CameraController() as cam:
    # Set multiple properties at once
    settings = {
        'brightness': 75,
        'contrast': 65,
        'saturation': 80
    }
    results = cam.set_multiple(settings)
    
    # Get multiple properties
    values = cam.get_multiple(['brightness', 'contrast', 'saturation'])
```

Handle errors:

```python
import duvc_ctl as duvc

with duvc.CameraController() as cam:
    try:
        cam.brightness = 999  # Out of range
    except duvc.InvalidValueError as e:
        print(f"Invalid value: {e}")
    except duvc.PropertyNotSupportedError:
        print("Brightness not supported on this camera")
```


#### Result-Based API - Production Use

The Result-Based API returns Result types instead of raising exceptions:

```python
import duvc_ctl as duvc

# List devices
devices = duvc.list_devices()
if not devices:
    print("No cameras found")
    exit(1)

device = devices[^0]

# Open camera with explicit error handling
camera_result = duvc.open_camera(device)
if camera_result.is_ok():
    camera = camera_result.value()
    
    # Get property - returns Result
    pan_result = camera.get(duvc.CamProp.Pan)
    if pan_result.is_ok():
        setting = pan_result.value()
        print(f"Pan: {setting.value} ({setting.mode})")
    else:
        print(f"Error: {pan_result.error().description()}")
else:
    print(f"Failed to open camera: {camera_result.error().description()}")
```

Set properties with range checking:

```python
import duvc_ctl as duvc

devices = duvc.list_devices()
if devices:
    device = devices[^0]
    camera_result = duvc.open_camera(device)
    
    if camera_result.is_ok():
        camera = camera_result.value()
        
        # Get range before setting
        range_result = camera.get_range(duvc.CamProp.Pan)
        if range_result.is_ok():
            prop_range = range_result.value()
            print(f"Pan range: {prop_range.min} to {prop_range.max}")
            
            # Set to center
            center = duvc.PropSetting(0, duvc.CamMode.Manual)
            set_result = camera.set(duvc.CamProp.Pan, center)
            
            if set_result.is_ok():
                print("Pan centered successfully")
            else:
                print(f"Failed to set Pan: {set_result.error().description()}")
```

Get device capabilities:

```python
import duvc_ctl as duvc

devices = duvc.list_devices()
if devices:
    caps_result = duvc.get_device_capabilities(devices[^0])
    
    if caps_result.is_ok():
        capabilities = caps_result.value()
        
        print("Supported camera properties:")
        for prop in capabilities.supported_camera_properties():
            print(f"  - {duvc.to_string(prop)}")
        
        print("Supported video properties:")
        for prop in capabilities.supported_video_properties():
            print(f"  - {duvc.to_string(prop)}")
```


#### API Comparison Table

| Feature | Pythonic | Result-Based |
| :-- | :-- | :-- |
| Device selection | Automatic (first device or by name) | Manual (explicit Device passed) |
| Error handling | Standard Python exceptions | Result types without exceptions |
| Code verbosity | Minimal | Explicit |
| Learning curve | Easy | Moderate |
| Production ready | Yes | Yes |
| Error diagnostics | Basic error message | Detailed error codes and descriptions |
| Thread-safe | Yes | Yes |
| Performance | Slightly lower (exception handling) | Slightly higher (no exception overhead) |

#### Next Steps

- For simple scripts or learning, start with the **Pythonic API** above.
- For production systems that need detailed error recovery, migrate to the **Result-Based API**.
- See the Architecture section for a detailed comparison of both APIs and their design rationale.
- Check Common Patterns \& Recipes for multi-camera control, bulk operations, and advanced scenarios.

### 1.3 Platform Requirements \& Compatibility

#### Windows support

duvc-ctl is designed for **Windows only**. It does not run on Linux, macOS, or other operating systems.

Supported Windows versions:

- Windows 7 SP1 and later (Windows 7, 8, 8.1, 10, 11, and Server editions)
- DirectShow, the multimedia framework used by duvc-ctl, is a standard component of all supported Windows versions

Attempting to import duvc-ctl on non-Windows platforms will raise an `ImportError` at module load time:

```python
# On Linux or macOS:
import duvc_ctl
# ImportError: duvc-ctl is only supported on Windows
```


#### Python version requirements

- **Minimum**: Python 3.8
- **Recommended**: Python 3.9 or later
- **Maximum tested**: Python 3.12

The library uses pybind11 for C++ bindings and has no external Python dependencies beyond the standard library. Binary wheels are built for Python 3.8, 3.9, 3.10, 3.11, and 3.12 on Windows (64-bit).

Check your Python version:

```bash
python --version
python -c "import struct; print('64-bit' if struct.calcsize('P') == 8 else '32-bit')"
```


#### Architecture compatibility

The library is built for **64-bit (x64) Windows only**.


| Architecture | Status | Notes |
| :-- | :-- | :-- |
| x64 (64-bit) | Supported | Recommended; all wheels use this |
| x86 (32-bit) | Partially Supported | No wheels built; compilation required |
| ARM64 | Not supported | Windows on ARM is not targeted |

If you are on 64-bit Windows and have 32-bit Python, install 64-bit Python instead. Mixing 32-bit Python with 64-bit Windows is not recommended for this library.

Verify your Python architecture:

```python
import platform
print(platform.architecture())  # Should show ('64bit', 'WindowsPE')
```


#### Runtime dependencies

Beyond Windows and Python, duvc-ctl requires:

- **DirectShow**: Built into all supported Windows versions; no installation needed.
- **Visual C++ Redistributable**: If installing from a prebuilt wheel, the matching MSVC runtime may be required. Modern wheels use delvewheel to bundle necessary DLLs, reducing this requirement. If you get a DLL error at runtime, install the Microsoft Visual C++ Redistributable for your Visual Studio version.
- **USB driver support**: Windows manages UVC camera drivers automatically for standard webcams. Vendor-specific cameras may require additional drivers (check Device Manager).


#### Behavior differences by Windows version

Most behavior is consistent across supported Windows versions. However, there are minor differences:


| Feature | Win7 SP1 | Win8+ | Notes |
| :-- | :-- | :-- | :-- |
| Device enumeration | Yes | Yes | DirectShow device discovery works identically |
| Property access | Yes | Yes | IAMCameraControl and IAMVideoProcAmp interfaces available |
| Hotplug detection | Yes | Yes | Device change notifications supported |
| DLL loading | Yes | Yes | DirectShow is present on all versions |

#### Binary wheel platform tags

PyPI wheels use Python's platform tagging convention. For duvc-ctl, the tags are:

```
duvc_ctl-2.0.0-cp38-cp38-win_amd64.whl
duvc_ctl-2.0.0-cp39-cp39-win_amd64.whl
duvc_ctl-2.0.0-cp310-cp310-win_amd64.whl
duvc_ctl-2.0.0-cp311-cp311-win_amd64.whl
duvc_ctl-2.0.0-cp312-cp312-win_amd64.whl
```

- `cpXY`: CPython version (3.8, 3.9, etc.)
- `win_amd64`: Windows 64-bit (x64)

pip automatically selects the correct wheel for your Python version and architecture. If pip cannot find a matching wheel, you'll need to build from source.

#### 32-bit Python on 64-bit Windows

While possible, running 32-bit Python on 64-bit Windows with duvc-ctl is not officially supported. If you must use 32-bit Python:

1. Build the extension from source (no prebuilt 32-bit wheel exists).
2. Ensure your C++ toolchain is configured for 32-bit builds.
3. Expect potential compatibility issues with device drivers and DirectShow.

We recommend using 64-bit Python on 64-bit Windows.

#### Import-time checks

When imported, duvc-ctl performs platform detection and will warn or error if:

- You are not on Windows (raises `ImportError`)
- Your Python architecture does not match your Windows architecture (warning)
- DirectShow cannot be detected or accessed (warning, but import succeeds)

These checks help catch configuration issues early:

```python
# Successful import (on Windows 64-bit with Python 3.8+):
import duvc_ctl as duvc
print(f"Module loaded: {duvc.__version__}")

# Failed import (on Linux):
import duvc_ctl
# ImportError: duvc-ctl is only supported on Windows
```


#### Forward compatibility

duvc-ctl targets stability across Windows versions. However:

- Future Windows releases may deprecate or alter DirectShow APIs, which could affect the library. However MediaFoundation support is planned to be added in the future.
- Binary wheels are tested on Windows 10 and 11; older versions (Windows 7, 8) are supported but receive less frequent testing.
- Python 3.13+ has been tested, However due do CI/CD limitations, prebuilt wheels are not available; if you need it, build from source.

For the latest supported configurations, check the project README or CI/CD matrix on GitHub.

