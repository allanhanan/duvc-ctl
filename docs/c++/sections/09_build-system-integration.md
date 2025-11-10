## 9. Build System \& Integration


### 9.1 CMake Integration

**Using duvc-ctl in your CMake project:**[file:e3a8e954]

#### FetchContent (Recommended)

```cmake
cmake_minimum_required(VERSION 3.16)
project(my_camera_app)

include(FetchContent)

FetchContent_Declare(
    duvc-ctl
    GIT_REPOSITORY https://github.com/allanhanan/duvc-ctl.git
    GIT_TAG        v2.0.0  # Or main for latest
)

# Configure options before making available
set(DUVC_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(DUVC_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(DUVC_BUILD_CLI OFF CACHE BOOL "" FORCE)

FetchContent_MakeAvailable(duvc-ctl)

add_executable(my_app main.cpp)
target_link_libraries(my_app PRIVATE duvc::core)
```


#### find_package (Installed Library)

```cmake
cmake_minimum_required(VERSION 3.16)
project(my_camera_app)

# Find installed duvc-ctl
find_package(duvc-ctl 2.0 REQUIRED)

add_executable(my_app main.cpp)
target_link_libraries(my_app PRIVATE duvc::core)
```


#### add_subdirectory (Vendored)

```cmake
cmake_minimum_required(VERSION 3.16)
project(my_camera_app)

# Configure options
set(DUVC_BUILD_TESTS OFF CACHE BOOL "")
set(DUVC_BUILD_CLI OFF CACHE BOOL "")

add_subdirectory(third_party/duvc-ctl)

add_executable(my_app main.cpp)
target_link_libraries(my_app PRIVATE duvc::core)
```


***

#### Available CMake Targets

| Target | Description | Link | Include |
| :-- | :-- | :-- | :-- |
| `duvc::core` | Shared library (DLL) | Automatic | `<duvc-ctl/duvc.hpp>` |
| `duvc::core-static` | Static library | Automatic | `<duvc-ctl/duvc.hpp>` |
| `duvc::c-api` | C ABI library | Automatic | `<duvc-ctl/c/api.h>` |

**Usage:**

```cmake
target_link_libraries(my_app PRIVATE duvc::core)      # Shared lib
target_link_libraries(my_app PRIVATE duvc::core-static)  # Static lib
target_link_libraries(my_app PRIVATE duvc::c-api)     # C API
```


***

#### CMake Build Options

**Core library:**


| Option | Default | Description |
| :-- | :-- | :-- |
| `DUVC_BUILD_SHARED` | `ON` | Build shared library (duvc-core.dll) |
| `DUVC_BUILD_STATIC` | `ON` | Build static library (duvc-core.lib) |
| `DUVC_BUILD_C_API` | `ON` | Build C API for language bindings |

**Optional components:**


| Option | Default | Description |
| :-- | :-- | :-- |
| `DUVC_BUILD_CLI` | `ON` | Build command-line tool |
| `DUVC_BUILD_PYTHON` | `OFF` | Build Python bindings |
| `DUVC_BUILD_TESTS` | `OFF` | Build test suite |
| `DUVC_BUILD_EXAMPLES` | `OFF` | Build example applications |

**Development:**


| Option | Default | Description |
| :-- | :-- | :-- |
| `DUVC_WARNINGS_AS_ERRORS` | `OFF` | Treat warnings as errors |
| `DUVC_INSTALL` | `ON` | Enable install targets |
| `DUVC_INSTALL_CMAKE_CONFIG` | `ON` | Install CMake config files |

**Configuration:**

```cmake
# Minimal integration (no extras)
set(DUVC_BUILD_CLI OFF CACHE BOOL "")
set(DUVC_BUILD_TESTS OFF CACHE BOOL "")
set(DUVC_BUILD_EXAMPLES OFF CACHE BOOL "")
FetchContent_MakeAvailable(duvc-ctl)

# Development build (all features)
set(DUVC_BUILD_TESTS ON CACHE BOOL "")
set(DUVC_BUILD_EXAMPLES ON CACHE BOOL "")
set(DUVC_WARNINGS_AS_ERRORS ON CACHE BOOL "")
FetchContent_MakeAvailable(duvc-ctl)
```


***

#### Exported Variables

When using `find_package(duvc-ctl)`:

```cmake
duvc-ctl_FOUND            # TRUE if found
duvc-ctl_VERSION          # Version string (e.g., "2.0.0")
duvc-ctl_INCLUDE_DIRS     # Include directories
duvc-ctl_LIBRARIES        # All library targets
```


***

### 9.2 Building from Source

**Prerequisites:**

- **Windows 10/11** (Windows 8.1 compatible but not tested)
- **Compiler:** Visual Studio 2019/2022 or MinGW-w64 GCC 9+
- **CMake 3.16+**
- **Python 3.8+** (for Python bindings only)
- **Git** (for fetching dependencies)

***

#### Quick Build (Visual Studio)

```bash
git clone https://github.com/allanhanan/duvc-ctl.git
cd duvc-ctl

# Configure
cmake -B build -G "Visual Studio 17 2022" -A x64

# Build Release
cmake --build build --config Release

# Run tests
cd build && ctest --config Release --output-on-failure
```


***

#### MinGW-w64 Build

```bash
# Configure with MinGW
cmake -B build -G "MinGW Makefiles" \
    -DCMAKE_BUILD_TYPE=Release

# Build
cmake --build build -j8

# Install
cmake --install build --prefix install
```


***

#### Custom Build (All Options)

```bash
cmake -B build \
    -G "Visual Studio 17 2022" -A x64 \
    -DDUVC_BUILD_SHARED=ON \
    -DDUVC_BUILD_STATIC=ON \
    -DDUVC_BUILD_C_API=ON \
    -DDUVC_BUILD_CLI=ON \
    -DDUVC_BUILD_PYTHON=ON \
    -DDUVC_BUILD_TESTS=ON \
    -DDUVC_BUILD_EXAMPLES=ON \
    -DDUVC_WARNINGS_AS_ERRORS=OFF \
    -DCMAKE_INSTALL_PREFIX=install

cmake --build build --config Release
cmake --install build --config Release
```


***

#### Python Bindings Build

```bash
# Install Python dev dependencies
pip install pybind11

# Configure with Python enabled
cmake -B build -G "Visual Studio 17 2022" -A x64 \
    -DDUVC_BUILD_PYTHON=ON \
    -DPython_EXECUTABLE=C:/Python39/python.exe

# Build
cmake --build build --config Release

# Install Python package
cd build/python
pip install .
```


***

#### Install Locations

**Default install prefix:**

- Windows: `C:/Program Files/duvc-ctl` or `C:/Program Files (x86)/duvc-ctl`
- Custom: Specify with `-DCMAKE_INSTALL_PREFIX=path`

**Installed structure:**

```
install/
├── bin/                 # DLLs and executables
│   ├── duvc-core.dll
│   ├── duvc-cli.exe
│   └── duvc-c-api.dll
├── lib/                 # Import libraries
│   ├── duvc-core.lib
│   └── duvc-c-api.lib
├── include/             # Headers
│   └── duvc-ctl/
│       ├── duvc.hpp
│       ├── core/
│       ├── platform/
│       └── c/
└── lib/cmake/duvc-ctl/  # CMake config
    ├── duvc-ctl-config.cmake
    └── duvc-ctl-targets.cmake
```


***

#### Development Build

**With all debugging symbols and tests:**

```bash
cmake -B build -G "Visual Studio 17 2022" -A x64 \
    -DCMAKE_BUILD_TYPE=Debug \
    -DDUVC_BUILD_TESTS=ON \
    -DDUVC_BUILD_EXAMPLES=ON \
    -DDUVC_WARNINGS_AS_ERRORS=ON

cmake --build build --config Debug
```


***

### 9.3 Package Managers

#### vcpkg Integration

**Status:** In development

**Installation (future):**

```bash
# Install vcpkg port
vcpkg install duvc-ctl

# Use in CMakeLists.txt
find_package(duvc-ctl CONFIG REQUIRED)
target_link_libraries(my_app PRIVATE duvc::core)
```

**Custom vcpkg triplet:**

```cmake
# x64-windows-static.cmake
set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE dynamic)
set(VCPKG_LIBRARY_LINKAGE static)

vcpkg install duvc-ctl:x64-windows-static
```

**CMake toolchain:**

```bash
cmake -B build \
    -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake \
    -DVCPKG_TARGET_TRIPLET=x64-windows-static
```


***

#### Conan Integration

**Status:** In development

**Installation (future):**

```bash
# Add remote (if needed)
conan remote add duvc https://conan.example.com

# Install package
conan install duvc-ctl/2.0.0@

# Or use conanfile.txt
[requires]
duvc-ctl/2.0.0

[generators]
CMakeDeps
CMakeToolchain
```

**CMakeLists.txt:**

```cmake
find_package(duvc-ctl REQUIRED)
target_link_libraries(my_app PRIVATE duvc-ctl::duvc-ctl)
```

**Conan build:**

```bash
conan install . --output-folder=build --build=missing
cmake -B build -DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake
cmake --build build
```


***

#### conda-forge Integration

**Status:** Planned

**Installation (future):**

```bash
conda install -c conda-forge duvc-ctl
```

**Create environment:**

```bash
conda create -n camera-dev duvc-ctl python=3.11
conda activate camera-dev
```


***

#### Chocolatey (CLI Tool)

**Status:** Coming soon

**Installation (future):**

```powershell
choco install duvc-cli
duvc-cli list
```


***

#### Manual Portfile (vcpkg)

**Create custom overlay:**

```cmake
# ports/duvc-ctl/portfile.cmake
vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO allanhanan/duvc-ctl
    REF v2.0.0
    SHA512 <hash>
)

vcpkg_cmake_configure(
    SOURCE_PATH "${SOURCE_PATH}"
    OPTIONS
        -DDUVC_BUILD_TESTS=OFF
        -DDUVC_BUILD_CLI=OFF
)

vcpkg_cmake_install()
vcpkg_cmake_config_fixup(CONFIG_PATH lib/cmake/duvc-ctl)
vcpkg_copy_pdbs()

file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/debug/include")
file(INSTALL "${SOURCE_PATH}/LICENSE" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME copyright)
```

**Use overlay:**

```bash
vcpkg install duvc-ctl --overlay-ports=./ports
```


***

#### Cross-Compilation

**MinGW on Linux:**

```bash
cmake -B build \
    -DCMAKE_TOOLCHAIN_FILE=toolchains/mingw-w64.cmake \
    -DCMAKE_BUILD_TYPE=Release

cmake --build build
```

**Toolchain file example:**

```cmake
# toolchains/mingw-w64.cmake
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_C_COMPILER x86_64-w64-mingw32-gcc)
set(CMAKE_CXX_COMPILER x86_64-w64-mingw32-g++)
set(CMAKE_RC_COMPILER x86_64-w64-mingw32-windres)

set(CMAKE_FIND_ROOT_PATH /usr/x86_64-w64-mingw32)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
```

