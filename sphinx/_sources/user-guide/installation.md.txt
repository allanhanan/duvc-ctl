# Installation

Complete installation guide for duvc-ctl across Python, C/C++, CLI, and C ABI.

---

## System Requirements

### Platform

- **Windows** 7 SP1 or later (Windows 10/11 recommended)
- **DirectShow** included with all modern Windows versions
- **Architecture** 64-bit (x64) recommended; 32-bit (x86) requires building from source

### Toolchain (C/C++ Development)

- **Compiler** Visual Studio 2019+ or MinGW-w64 GCC 9+
- **CMake** 3.16 or later
- **Windows SDK** included with Visual Studio
- **Git** for cloning the repository

### Python (Python Bindings)

- **Python** 3.8–3.12 (64-bit recommended)
- **pip** latest version

---

## Python Installation

### From PyPI (Prebuilt Wheels)

Install the prebuilt binary wheel:

```

pip install duvc-ctl

```

Verify:

```

python -c "import duvcctl; print(duvcctl.__version__)"

```

**Available wheels:**
- Python 3.8, 3.9, 3.10, 3.11, 3.12
- Windows x64 (64-bit) only

If no matching wheel exists, install from source.

### From Source (Python)

Clone and build:

```

git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl
pip install .

```

For editable development install:

```

pip install -e .

```

### Python Verification

```

import duvcctl as duvc

print("duvc-ctl version:", duvc.__version__)

devices = duvc.list_devices()
print("Devices found:", len(devices))
for device in devices:
print(f"  - {device.name}")

```

---

## C/C++ Installation

### Build from Source

**Clone repository:**

```

git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl

```

**Configure (Visual Studio):**

```

cmake -B build -G "Visual Studio 17 2022" -A x64 -DDUVC_BUILD_SHARED=ON -DDUVC_BUILD_STATIC=ON

```

**Configure (MinGW):**

```

cmake -B build -G "MinGW Makefiles" -DDUVC_BUILD_SHARED=ON -DDUVC_BUILD_STATIC=ON

```

**Build:**

```

cmake --build build --config Release

```

**Install (optional):**

```

cmake --install build --config Release

```

### CMake Options

| Option | Default | Description |
|--------|---------|-------------|
| `DUVC_BUILD_SHARED` | ON | Build shared library (.dll) |
| `DUVC_BUILD_STATIC` | ON | Build static library (.lib/.a) |
| `DUVC_BUILD_CAPI` | ON | Build C ABI for FFI |
| `DUVC_BUILD_CLI` | ON | Build CLI tool |
| `DUVC_BUILD_PYTHON` | ON | Build Python bindings |
| `DUVC_BUILD_TESTS` | OFF | Build test suite |
| `DUVC_BUILD_EXAMPLES` | OFF | Build example programs |

**Example (C++ only, no Python/CLI):**

```

cmake -B build -G "Visual Studio 17 2022" -A x64 \
-DDUVC_BUILD_SHARED=ON \
-DDUVC_BUILD_STATIC=OFF \
-DDUVC_BUILD_CAPI=OFF \
-DDUVC_BUILD_CLI=OFF \
-DDUVC_BUILD_PYTHON=OFF

```

### Integration into Your Project

#### Using CMake `find_package`

After installing duvc-ctl:

```

find_package(duvc-ctl REQUIRED)
target_link_libraries(your_target PRIVATE duvc-ctl::duvc-ctl)

```

#### Manual Integration

```

target_include_directories(your_target PRIVATE /path/to/duvc-ctl/include)
target_link_libraries(your_target PRIVATE /path/to/duvc-ctl/lib/duvc-core.lib)

```

#### Headers

**Single header (recommended):**

```

\#include <duvc-ctl/duvc.hpp>

```

**Selective headers:**

```

\#include <duvc-ctl/core/camera.h>
\#include <duvc-ctl/core/device.h>
\#include <duvc-ctl/core/result.h>

```

### C++ Verification

```

\#include <duvc-ctl/duvc.hpp>
\#include <iostream>

int main() {
auto devices = duvc::list_devices();
std::cout << "Found " << devices.size() << " camera(s)\n";
for (const auto\& dev : devices)
std::cout << "  - " << duvc::to_utf8(dev.name) << "\n";
return 0;
}

```

Compile:

```


# Visual Studio

cl /EHsc /I include test.cpp /link duvc-core.lib

# MinGW

g++ -std=c++17 -I include test.cpp -L lib -lduvc-core -o test.exe

```

---

## CLI Installation

### Build CLI Tool

The CLI is built automatically when `-DDUVC_BUILD_CLI=ON` (default).

```

cmake -B build -G "Visual Studio 17 2022" -A x64 -DDUVC_BUILD_CLI=ON
cmake --build build --config Release

```

Executable location:

```

build/bin/duvc-cli.exe       \# Release build
build/bin/Debug/duvc-cli.exe \# Debug build

```

### Add to PATH (optional)

**Windows:**

```

\$env:PATH += ";C:\path\to\duvc-ctl\build\bin"

```

Or add permanently via System Properties → Environment Variables.

### CLI Verification

```

duvc-cli list

```

**Expected output:**

```

Devices: 1
0: Logitech HD Pro Webcam C920
\\?\usb\#vid_046d\&pid_082d\#...

```

---

## C ABI Installation

### Build C ABI

The C ABI is built when `-DDUVC_BUILD_CAPI=ON` (default).

```

cmake -B build -G "Visual Studio 17 2022" -A x64 -DDUVC_BUILD_CAPI=ON
cmake --build build --config Release

```

**Output files:**

- **Header:** `include/duvc-ctl/capi.h`
- **Library:** `build/lib/duvc-capi.lib` (static) or `build/bin/duvc-capi.dll` (shared)

### Integration (C ABI)

**C code:**

```

\#include <duvc-ctl/capi.h>
\#include <stdio.h>

int main() {
duvc_initialize();

    duvc_device_t* devices;
    size_t count;
    duvc_list_devices(&devices, &count);
    
    printf("Found %zu camera(s)\n", count);
    
    duvc_free_device_list(devices, count);
    duvc_shutdown();
    return 0;
    }

```

**Compile:**

```


# Visual Studio

cl test.c /I include /link duvc-capi.lib

# MinGW

gcc test.c -I include -L lib -lduvc-capi -o test.exe

```

### C ABI Verification

```

\#include <duvc-ctl/capi.h>
\#include <stdio.h>

int main() {
if (!duvc_check_abi_compatibility(DUVC_ABI_VERSION)) {
fprintf(stderr, "ABI version mismatch\n");
return 1;
}

    printf("duvc-ctl version: %s\n", duvc_get_version_string());
    
    duvc_initialize();
    duvc_shutdown();
    return 0;
    }

```

---

## Troubleshooting

### Python Issues

| Issue | Solution |
|-------|----------|
| `ImportError: DLL load failed` | Install [Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) |
| `ImportError` on non-Windows | duvc-ctl is Windows-only (DirectShow API) |
| No matching wheel | Build from source: `pip install .` |
| Build errors (`pip install -e .`) | Ensure CMake 3.16+, Visual Studio 2019+, 64-bit Python |

**Check Python architecture:**

```

python -c "import struct; print('64-bit' if struct.calcsize('P') == 8 else '32-bit')"

```

### C/C++ Build Issues

| Issue | Solution |
|-------|----------|
| CMake not found | Add CMake to PATH: `cmake --version` |
| Visual Studio not detected | Use Visual Studio Developer Command Prompt |
| MinGW build errors | Ensure MinGW-w64 GCC 9+ with `-std=c++17` |
| Missing DirectShow headers | Install Windows SDK (included with Visual Studio) |
| Linker errors (`duvc-core.lib`) | Check library path in `target_link_libraries` |

**Delete build cache:**

```


# Windows

rmdir /s /q build \&\& cmake -B build

# PowerShell

Remove-Item -Recurse -Force build; cmake -B build

```

### CLI Issues

| Issue | Solution |
|-------|----------|
| `duvc-cli.exe` not found | Check `build/bin/` or `build/bin/Debug/` |
| Exit code 1 (usage error) | Verify command syntax: `duvc-cli list` |
| No devices found | Close other apps using camera (Zoom, Teams) |
| Permission denied | Run as Administrator; check Windows Privacy Settings |

### C ABI Issues

| Issue | Solution |
|-------|----------|
| `duvc_initialize()` fails | Check Windows version (7 SP1+), DirectShow availability |
| ABI version mismatch | Recompile with matching `DUVC_ABI_VERSION` |
| Undefined symbols | Link against `duvc-capi.lib` or `duvc-capi.dll` |

---

## Platform Detection

### Windows Version Check

duvc-ctl performs runtime checks at import/initialization:

**Python:**

```

import duvcctl  \# Raises ImportError on non-Windows

```

**C++:**

```

\#ifdef _WIN32
// Windows-specific code
\#else
\#error "duvc-ctl requires Windows"
\#endif

```

**C ABI:**

```

if (duvc_initialize() != DUVC_SUCCESS) {
fprintf(stderr, "Failed to initialize (non-Windows?)\n");
return 1;
}

```

### Architecture Check

**Python:**

```

import platform
print(platform.architecture())  \# Should show ('64bit', 'WindowsPE')

```

**C/C++:**

```

\#if defined(_WIN64) || defined(__x86_64__)
// 64-bit
\#else
\#error "64-bit Windows required"
\#endif

```

---

## Binary Wheel Platform Tags

PyPI wheels use the following naming convention:

```

duvc_ctl-2.0.0-cp38-cp38-win_amd64.whl
duvc_ctl-2.0.0-cp39-cp39-win_amd64.whl
duvc_ctl-2.0.0-cp310-cp310-win_amd64.whl
duvc_ctl-2.0.0-cp311-cp311-win_amd64.whl
duvc_ctl-2.0.0-cp312-cp312-win_amd64.whl

```

- `cpXY`: CPython version (3.8, 3.9, etc.)
- `win_amd64`: Windows 64-bit (x64)

pip automatically selects the correct wheel for your Python version and architecture.

---

## Runtime Dependencies

### DirectShow

Included with all Windows 7+ versions. No installation required.

### Visual C++ Redistributable

Required if installing prebuilt wheels without bundled DLLs.

**Download:** [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

Modern wheels use `delvewheel` to bundle necessary DLLs, minimizing this requirement.

### USB Drivers

Windows automatically manages UVC camera drivers for standard webcams. Vendor-specific cameras (Logitech, etc.) may require additional drivers from Device Manager.

---

## Advanced Configuration

### Static Linking (C/C++)

Build static library and link:

```

cmake -B build -G "Visual Studio 17 2022" -A x64 -DDUVC_BUILD_STATIC=ON -DDUVC_BUILD_SHARED=OFF
cmake --build build --config Release

```

Link in your project:

```

target_link_libraries(your_target PRIVATE duvc-core-static)

```

### Debug Builds

```

cmake -B build -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=Debug
cmake --build build --config Debug

```

Enable debug logging:

**Python:**

```

import duvcctl as duvc
duvc.set_log_level(duvc.LogLevel.Debug)

```

**C++:**

```

duvc::set_log_level(duvc::LogLevel::Debug);

```

**C ABI:**

```

duvc_set_log_level(DUVC_LOGLEVEL_DEBUG);

```

### Custom Install Prefix

```

cmake -B build -G "Visual Studio 17 2022" -A x64 -DCMAKE_INSTALL_PREFIX=C:/custom/path
cmake --install build --config Release

```

---

## Next Steps

- **[Quick Start](quickstart.md)** — First program for Python, C++, CLI, C ABI
- **[C++ API Reference](index.md)** — Complete C++ documentation
- **[C ABI Documentation](index.md)** — C API for FFI
- **[Python API Reference](index.md)** — Pythonic and Result-based APIs
- **[CLI Documentation](index.md)** — Command reference and scripting
- **[Architecture Overview](02_architecture-design-overview.md)** — Design patterns, threading, error handling

---

**Questions?** Open an issue on [GitHub](https://github.com/allanhanan/duvc-ctl/issues).
```


***