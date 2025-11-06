## 11. Building, Contributing \& pybind11 Integration


### 11.1 Installation \& Build Methods

Three installation paths: prebuilt wheels (fastest), source build with cibuildwheel (CI automation), manual source build with CMake.

***

#### Installation from PyPI

Simplest approach for end users. Binary wheels available for Python 3.8–3.12, Windows 64-bit.

```bash
pip install duvc-ctl
```

**Verify**:

```python
import duvc_ctl as duvc
print(duvc.__version__)
```


***

#### Building from source with cibuildwheel

Automated cross-Python wheel building via cibuildwheel. Used in CI/CD pipeline for PyPI distribution.

**Local testing**:

```bash
pip install cibuildwheel
cibuildwheel --only cp310-win_amd64
```

Builds wheels for Python 3.10 on Windows AMD64 using local environment. Outputs to `wheelhouse/`.

**CI usage** (GitHub Actions):

```yaml
- uses: pypa/cibuildwheel@v2.15.0
  with:
    only: cp38-win_amd64 cp39-win_amd64 cp310-win_amd64 cp311-win_amd64 cp312-win_amd64
```


***

#### Build prerequisites

**Windows SDK/Runtime**:

- Visual Studio 2019+ or Build Tools
- Windows SDK (includes DirectShow headers)
- Microsoft Visual C++ Redistributable (end-user runtime)

**CMake**:

- CMake 3.16+
- Ensure in PATH: `cmake --version`

**Python**:

- Python 3.8+
- Development headers (included with standard distribution)
- Verify: `python -m pip --version`

**DirectShow**:

- Built into Windows; no separate install needed
- Headers provided by Windows SDK

***

#### Development installation

For source code modification and testing:

```bash
git clone https://github.com/allanhanan/duvc-ctl
cd duvc-ctl
pip install -e .
```

Compiles extension in place. Changes to Python files immediately visible; C++ requires recompile.

***

#### Wheel generation with delvewheel

Post-build tool to repair wheels by bundling runtime dependencies (DLLs). Run after cibuildwheel.

```bash
pip install delvewheel
delvewheel repair dist/duvc_ctl-*.whl
```

Outputs fixed wheels to `wheelhouse/`. Required for redistributing without external DLL dependencies.

***

#### Build system configuration details

**CMake options** (passed to first `cmake` invocation):


| Option | Default | Purpose |
| :-- | :-- | :-- |
| `DUVCBUILDSHARED` | ON | Build shared core library (.dll) |
| `DUVCBUILDSTATIC` | ON | Build static core library (.lib) |
| `DUVCBUILDCAPI` | ON | Build C ABI bindings for pybind11 |
| `DUVCBUILDCLI` | ON | Build command-line tool (duvc-ctl.exe) |
| `DUVCBUILDPYTHON` | ON | Build Python extension (required for PyPI) |
| `DUVCBUILDTESTS` | OFF | Build test suite |
| `DUVCBUILDEXAMPLES` | OFF | Build example programs |

**pyproject.toml configuration** (scikit-build-core):

```toml
[tool.scikit-build]
cmake.version = ">=3.16"
cmake.build-type = "Release"
wheel.packages = ["src/duvcctl"]
```

Instructs build system where Python sources live and minimum CMake version.

***

#### CMake options documentation

**Minimal Python build** (wheels only):

```bash
cmake -B build -G "Visual Studio 17 2022" -A x64 \
  -DDUVCBUILDSHARED=ON \
  -DDUVCBUILDSTATIC=OFF \
  -DDUVCBUILDCAPI=OFF \
  -DDUVCBUILDCLI=OFF \
  -DDUVCBUILDPYTHON=ON
```

**Full development build** (all components):

```bash
cmake -B build -G "Visual Studio 17 2022" -A x64 \
  -DDUVCBUILDSHARED=ON \
  -DDUVCBUILDSTATIC=ON \
  -DDUVCBUILDCAPI=ON \
  -DDUVCBUILDCLI=ON \
  -DDUVCBUILDPYTHON=ON \
  -DDUVCBUILDTESTS=ON \
  -DDUVCBUILDEXAMPLES=ON
```

**Release vs Debug**:

```bash
# Release (optimized, no debug symbols)
cmake -B build -DCMAKE_BUILD_TYPE=Release ...

# Debug (symbols, no optimization)
cmake -B build -DCMAKE_BUILD_TYPE=Debug ...
```


***

#### CI/CD pipeline setup

**GitHub Actions workflow** (build-wheels.yml):

Triggers on push/tag. Builds wheels for all Python versions.

```yaml
name: Build Wheels
on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install cibuildwheel
      - run: cibuildwheel
      - uses: actions/upload-artifact@v3
        with:
          path: wheelhouse/
```

**PyPI publish** (build-and-publish.yml):

Automatically uploads wheels after successful build.

```yaml
- run: pip install twine
- run: twine upload wheelhouse/*.whl --skip-existing
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```


***

#### Windows-specific build issues \& solutions

**Issue: MSBuild not found**

```
CMake Error: Could not find a package configuration file...
```

**Solution**: Run from Visual Studio Developer Command Prompt or specify toolset:

```bash
cmake -B build -T "v143" ...
```

**Issue: DirectShow headers missing**

```
fatal error C1083: Cannot open include file: 'Mmsystem.h'
```

**Solution**: Install Windows SDK from Visual Studio Installer, ensure "Windows 10 SDK" or later selected.

**Issue: Python headers not found during build**

```
fatal error C1083: Cannot open include file: 'Python.h'
```

**Solution**: Install Python development package:

```bash
pip install --upgrade pip setuptools
# Or download from python.org with dev headers option
```

**Issue: delvewheel fails on repaired wheel**

```
Could not find DLL dependencies
```

**Solution**: Ensure all runtime dependencies included in build:

```bash
delvewheel show dist/*.whl  # Debug output
delvewheel repair --add-path . dist/*.whl  # Explicit path
```

### 11.2 pybind_module.cpp Architecture

Core pybind11 bindings architecture mapping C++ layer to Python. Includes conversion helpers, abstract trampolines, Result specializations, and GIL management patterns.

***

#### String conversion helpers

**wstring_to_utf8()** - UTF-16 → UTF-8

```cpp
static std::string wstring_to_utf8(const std::wstring& wstr) {
  int size = WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), -1, nullptr, 0, nullptr, nullptr);
  std::string result(size - 1, 0);
  WideCharToMultiByte(CP_UTF8, 0, wstr.c_str(), -1, &result[^0], size, nullptr, nullptr);
  return result;
}
```

Used for Device.name and Device.path properties (wide internally, UTF-8 to Python).

**utf8_to_wstring()** - UTF-8 → UTF-16

```cpp
static std::wstring utf8_to_wstring(const std::string& str) {
  int size = MultiByteToWideChar(CP_UTF8, 0, str.c_str(), -1, nullptr, 0);
  std::wstring result(size - 1, L'\0');
  MultiByteToWideChar(CP_UTF8, 0, str.c_str(), -1, &result[^0], size);
  return result;
}
```

Converts Python strings to DirectShow APIs.

***

#### Error handling helpers

**throw_duvc_error()** - exception wrapper

```cpp
static void throw_duvc_error(const duvc::Error& error) {
  throw std::runtime_error(
    "duvc error: " + std::to_string(static_cast<int>(error.code)) + 
    " - " + error.description()
  );
}
```

Used by exception-throwing convenience functions (e.g., `open_camera_or_throw`).

**unwrap_or_throw\<T>()** - copyable version

```cpp
template <typename T>
static T unwrap_or_throw(const duvc::Result<T>& result) {
  if (result.is_ok()) return result.value();
  throw_duvc_error(result.error());
}
```

Extracts value from Result or throws. Copies value (OK for small types).

**unwrap_or_throw\<T>()** - rvalue move version

```cpp
template <typename T>
static T unwrap_or_throw(duvc::Result<T>&& result) {
  if (result.is_ok()) return std::move(result.value());
  throw_duvc_error(result.error());
}
```

Moves non-copyable values (e.g., `shared_ptr<Camera>`).

**unwrap_void_or_throw()** - void version

```cpp
static void unwrap_void_or_throw(const duvc::Result<void>& result) {
  if (!result.is_ok())
    throw_duvc_error(result.error());
}
```

Check void Result for errors and throw if failed.

***

#### Abstract trampolines

**PyIPlatformInterface** - Python subclassing

```cpp
class PyIPlatformInterface : public IPlatformInterface {
  using IPlatformInterface::IPlatformInterface;
  
  Result<std::vector<Device>> list_devices() override {
    PYBIND11_OVERRIDE_PURE(
      Result<std::vector<Device>>,
      IPlatformInterface,
      list_devices
    );
  }
  // ... other methods with PYBIND11_OVERRIDE_PURE
};
```

Enables Python subclasses to override C++ interface methods. Automatic GIL acquisition during Python→C++ calls.

**PyIDeviceConnection** - device connection override

```cpp
class PyIDeviceConnection : public IDeviceConnection {
  using IDeviceConnection::IDeviceConnection;
  
  Result<PropSetting> get_camera_property(CamProp prop) override {
    PYBIND11_OVERRIDE_PURE(
      Result<PropSetting>,
      IDeviceConnection,
      get_camera_property,
      prop
    );
  }
  // ... all methods with PYBIND11_OVERRIDE_PURE
};
```

Custom device backends for non-standard hardware or testing.

***

#### PyGUID implementation

**parse_from_string()** - flexible GUID parsing

```cpp
bool parse_from_string(const std::string& guidstr) {
  // Support XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
  // Support XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX (no dashes)
  // Support {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX} (with braces)
  
  // Parse with sscanf and validate format
  unsigned long data1;
  unsigned int data2, data3;
  unsigned int data4[^8];
  
  int matches = sscanf(guidstr.c_str(), "%8lx-%4x-%4x-%2x%2x-%2x%2x%2x%2x%2x%2x",
    data1, &data2, &data3, &data4[^0], &data4[^1], ...);
  
  if (matches != 11) return false;
  guid.Data1 = static_cast<ULONG>(data1);
  // ... assign Data2-Data4 components
  return true;
}
```

**guid_from_pyobj()** - comprehensive input handling

```cpp
static GUID guid_from_pyobj(py::handle obj) {
  // PyGUID instance: direct cast
  if (py::isinstance<PyGUID>(obj))
    return obj.cast<PyGUID>().guid;
  
  // uuid.UUID object: extract .hex
  if (py::isinstance(obj, uuid_class)) {
    std::string hexstr = obj.attr("hex").cast<std::string>();
    PyGUID pyguid;
    if (pyguid.parse_from_string(hexstr))
      return pyguid.guid;
  }
  
  // String representation
  if (py::isinstance<py::str>(obj)) {
    std::string guidstr = obj.cast<std::string>();
    PyGUID pyguid;
    if (pyguid.parse_from_string(guidstr))
      return pyguid.guid;
  }
  
  // 16-byte buffer
  if (py::isinstance<py::bytes>(obj) || py::isinstance<py::bytearray>(obj)) {
    py::buffer_info info = py::buffer(obj.cast<py::object>()).request();
    if (info.size * info.itemsize == 16) {
      GUID result;
      std::memcpy(&result, info.ptr, 16);
      return result;
    }
  }
  
  throw std::invalid_argument("Unsupported GUID input type");
}
```


***

#### Result\<T> specializations

**DeviceConnectionResult** - unique_ptr handling

```cpp
py::class_<Result<std::unique_ptr<IDeviceConnection>>>(
  m, "DeviceConnectionResult", py::module_local(),
  "Result containing device connection or error"
)
  .def("is_ok", &Result<std::unique_ptr<IDeviceConnection>>::is_ok)
  .def("value", [](Result<std::unique_ptr<IDeviceConnection>>& r) {
    // Move unique_ptr out, invalidating result
    return std::move(r.value());
  });
```

**Uint32Result** - numeric values

```cpp
py::class_<Result<uint32_t>>(
  m, "Uint32Result", py::module_local(),
  "Result containing uint32_t or error"
)
  .def("value", [](const Result<uint32_t>& r) { return r.value(); });
```

**VectorUint8Result** - binary data

```cpp
py::class_<Result<std::vector<uint8_t>>>(
  m, "VectorUint8Result", py::module_local(),
  "Result containing vector<uint8_t> or error"
)
  .def("value", [](const Result<std::vector<uint8_t>>& r) {
    return r.value();  // Returns copy
  }, py::return_value_policy::automatic_reference);
```

**BoolResult** - boolean queries

```cpp
py::class_<Result<bool>>(
  m, "BoolResult", py::module_local(),
  "Result containing bool or error"
)
  .def("value", [](const Result<bool>& r) { return r.value(); });
```


***

#### Move semantics documentation

**Move-only Camera**:

```cpp
// Camera is move-only (non-copyable RAII)
PYBIND11_MAKE_OPAQUE(Camera)  // Prevents pybind11 copy generation

// Binding uses move semantics
py::class_<Camera>(m, "Camera")
  .def("__init__", [](Camera& self, const Device& dev) {
    new (&self) Camera(dev);  // Placement new for move-only type
  });

// Python can move Camera but not copy
```

Move-only semantics enforced through RAII camera handle.

***

#### GIL release patterns

**Callback with GIL management**:

```cpp
// Register device change callback with GIL handling
m.def("register_device_change_callback",
  [](py::function callback) {
    static py::function stored_callback = callback;
    register_device_change_callback(
      [](const std::string& event_type, const std::string& device_name) {
        py::gil_scoped_acquire gil;  // Acquire before Python call
        try {
          stored_callback(event_type, device_name);
        } catch (const py::error_already_set&) {
          PyErr_Clear();  // Don't let Python exceptions leak to C++
        }
      }
    );
  }, py::arg("callback"),
  "Register callback for device hotplug events"
);
```

GIL acquired before calling Python callbacks, released after.

**Logging callback**:

```cpp
m.def("set_log_callback",
  [](py::function callback) {
    static py::function stored_log_callback = callback;
    set_log_callback(
      [](LogLevel level, const std::string& message) {
        py::gil_scoped_acquire gil;  // GIL scope
        try {
          stored_log_callback(level, message);
        } catch (const py::error_already_set&) {
          PyErr_Clear();
        }
      }
    );
  }
);
```


***

#### Device/PropSetting/PropRange/PropertyCapability bindings

**Device**:

```cpp
py::class_<Device>(m, "Device", py::module_local(),
  "Represents a camera device")
  .def_property_readonly("name", 
    [](const Device& d) { return wstring_to_utf8(d.name); },
    "Human-readable device name (UTF-8)")
  .def_property_readonly("path",
    [](const Device& d) { return wstring_to_utf8(d.path); },
    "Unique device path identifier (UTF-8)")
  .def("__eq__", [](const Device& a, const Device& b) {
    return a.path == b.path;
  })
  .def("__hash__", [](const Device& d) {
    return std::hash<std::wstring>()(d.path);
  });
```

**PropSetting**:

```cpp
py::class_<PropSetting>(m, "PropSetting", py::module_local(),
  "Property setting with value and control mode")
  .def_readwrite("value", &PropSetting::value,
    "Property value")
  .def_readwrite("mode", &PropSetting::mode,
    "Control mode (auto/manual)");
```

**PropRange**:

```cpp
py::class_<PropRange>(m, "PropRange", py::module_local(),
  "Valid range constraints for a property")
  .def_readwrite("min", &PropRange::min, "Minimum value")
  .def_readwrite("max", &PropRange::max, "Maximum value")
  .def_readwrite("step", &PropRange::step, "Step size")
  .def_readwrite("default_val", &PropRange::default_val, "Default value")
  .def_readwrite("default_mode", &PropRange::default_mode, "Default mode")
  .def("is_valid", &PropRange::is_valid, py::arg("value"));
```

**PropertyCapability**:

```cpp
py::class_<PropertyCapability>(m, "PropertyCapability", py::module_local(),
  "Property capability information")
  .def_readwrite("supported", &PropertyCapability::supported)
  .def_readwrite("range", &PropertyCapability::range)
  .def_readwrite("current", &PropertyCapability::current)
  .def("supports_auto", &PropertyCapability::supports_auto);
```


***

#### Logitech submodule with 10 properties

```cpp
py::module logitech_module = m.def_submodule(
  "logitech", "Logitech vendor-specific extensions"
);

py::enum_<duvc::logitech::LogitechProperty>(
  logitech_module, "Property", "Logitech vendor-specific properties"
)
  .value("RightLight", duvc::logitech::LogitechProperty::RightLight)
  .value("RightSound", duvc::logitech::LogitechProperty::RightSound)
  .value("FaceTracking", duvc::logitech::LogitechProperty::FaceTracking)
  .value("LedIndicator", duvc::logitech::LogitechProperty::LedIndicator)
  .value("ProcessorUsage", duvc::logitech::LogitechProperty::ProcessorUsage)
  .value("RawDataBits", duvc::logitech::LogitechProperty::RawDataBits)
  .value("FocusAssist", duvc::logitech::LogitechProperty::FocusAssist)
  .value("VideoStandard", duvc::logitech::LogitechProperty::VideoStandard)
  .value("DigitalZoomROI", duvc::logitech::LogitechProperty::DigitalZoomROI)
  .value("TiltPan", duvc::logitech::LogitechProperty::TiltPan)
  .export_values();
```


***

#### All enum bindings (48 values)

| Category | Count | Examples |
| :-- | :-- | :-- |
| CamProp | 20 | Pan, Tilt, Zoom, Focus, Exposure, Privacy, ... |
| VidProp | 10 | Brightness, Contrast, Saturation, Gamma, ... |
| CamMode | 2 | Auto, Manual |
| ErrorCode | 9 | Success, DeviceNotFound, PermissionDenied, ... |
| LogLevel | 5 | Debug, Info, Warning, Error, Critical |
| **Total** | **48** |  |

All bound via `py::enum_<T>(m, "Name")`.


#### Code formatting requirement

All C++ code **must use clang-format with LLVM style**:

```bash
clang-format -i --style=llvm pybind_module.cpp
```

Key rules: 2-space indent, 80-column soft limit, `BreakBeforeBraces: Attach`, `ColumnLimit: 100`.

### 11.3 Contributing \& Extension

Extensibility patterns for adding new features, bindings, and exception types. Follows open-source workflow: fork, implement, test, submit PR.

***

#### Binding patterns \& examples

**Adding a simple property binding**

Extend `pybind_module.cpp` to expose a new C++ function. Use `py::module_local()` for isolation.

```cpp
m.def("get_device_serial", [](const Device& dev) {
  Result<std::string> result = getDeviceSerialNumber(dev);
  return unwrap_or_throw(result);
}, py::arg("device"), "Get device serial number (throws on error)");
```

Accessible as `duvc_ctl.get_device_serial(device)`.

**Adding a Result specialization**

New Result type (e.g., `Result<std::string>`) requires binding. Add to pybind_module.cpp after other Result types:

```cpp
py::class_<Result<std::string>>(
  m, "StringResult", py::module_local(),
  "Result containing string or error"
)
  .def("is_ok", &Result<std::string>::is_ok)
  .def("error", &Result<std::string>::error)
  .def("value", [](const Result<std::string>& r) {
    return r.value();
  });
```


***

#### Adding new property types

**Add enum value** in C++ header `duvc/properties.h`:

```cpp
enum class CamProp {
  Pan, Tilt, Zoom, Focus,
  // ... existing values ...
  NewCustomProperty = 42  // New value
};
```

**Bind in pybind_module.cpp**:

```cpp
py::enum_<duvc::CamProp>(m, "CamProp")
  .value("Pan", duvc::CamProp::Pan)
  // ... existing bindings ...
  .value("NewCustomProperty", duvc::CamProp::NewCustomProperty)
  .export_values();
```

**Usage in Python**:

```python
import duvc_ctl as duvc
result = duvc.get_camera_property(device, duvc.CamProp.NewCustomProperty)
```


***

#### Extending Result specializations

When adding a complex return type (e.g., `Result<std::vector<PropRange>>`):

**C++ header**:

```cpp
std::vector<PropRange> get_all_property_ranges(const Device& dev);
Result<std::vector<PropRange>> safe_get_all_property_ranges(const Device& dev);
```

**pybind_module.cpp binding**:

```cpp
py::class_<Result<std::vector<PropRange>>>(
  m, "PropRangeVectorResult", py::module_local(),
  "Result containing vector of property ranges"
)
  .def("is_ok", &Result<std::vector<PropRange>>::is_ok)
  .def("error", [](const Result<std::vector<PropRange>>& r) {
    return r.error();
  })
  .def("value", [](const Result<std::vector<PropRange>>& r) {
    return r.value();
  }, py::return_value_policy::automatic_reference);

m.def("get_property_ranges", 
  [](const Device& dev) {
    return safe_get_all_property_ranges(dev);
  }, py::arg("device"));
```


***

#### Adding new exceptions with ErrorCode mapping

**Define exception** in `duvc/errors.h`:

```cpp
enum class ErrorCode {
  Success = 0,
  // ... existing codes ...
  NetworkTimeout = 50,
  NetworkError = 51,
};

class NetworkError : public DuvcError {
public:
  explicit NetworkError(const std::string& msg = "Network error")
    : DuvcError(ErrorCode::NetworkError, msg) {}
};
```

**Register in pybind_module.cpp**:

```cpp
py::register_exception<duvc::NetworkError>(m, "NetworkError")
  .def_property_readonly("error_code", [](const duvc::NetworkError& e) {
    return e.code();
  });

// Map C++ exception to Python
register_exception_translator(
  [](std::exception_ptr p) {
    try {
      std::rethrow_exception(p);
    } catch (const duvc::NetworkError& e) {
      PyErr_SetString(PyExc_RuntimeError, e.what());
    }
  }
);
```

**Update ErrorCode mapping** in `duvc/errors.h`:

```cpp
static inline const char* error_code_to_string(ErrorCode code) {
  switch (code) {
    case ErrorCode::NetworkTimeout: return "Network timeout";
    case ErrorCode::NetworkError: return "Network communication failed";
    // ... other codes ...
    default: return "Unknown error";
  }
}
```


***

#### Exception translation patterns

**Automatic C++ → Python exception conversion**

In pybind_module.cpp:

```cpp
py::register_exception_translator([](std::exception_ptr p) {
  try {
    std::rethrow_exception(p);
  } catch (const duvc::PermissionDeniedError& e) {
    PyErr_SetString(DuvcPermissionDeniedError, e.what());
  } catch (const duvc::DeviceNotFoundError& e) {
    PyErr_SetString(DuvcDeviceNotFoundError, e.what());
  } catch (const std::runtime_error& e) {
    PyErr_SetString(PyExc_RuntimeError, e.what());
  }
});
```

**Custom exception class definition**:

```cpp
static PyObject* DuvcPermissionDeniedError = nullptr;

// In module init:
DuvcPermissionDeniedError = PyErr_NewException(
  "duvc_ctl.PermissionDeniedError", nullptr, nullptr
);
PyModule_AddObject(m.ptr(), "PermissionDeniedError", 
  DuvcPermissionDeniedError);
```


***

#### Testing procedures \& patterns (INCOMPLETE SECTION)

**Unit test structure** in `tests/test_bindings.py`:

```python
import pytest
import duvc_ctl as duvc

class TestDeviceDiscovery:
    def test_list_devices(self):
        """Test device enumeration returns list."""
        devices = duvc.list_devices()
        assert isinstance(devices, list)
    
    def test_device_properties(self):
        """Test device has required attributes."""
        devices = duvc.devices()
        if devices:  # Only if cameras present
            dev = devices[0]
            assert hasattr(dev, 'name')
            assert hasattr(dev, 'path')
            assert isinstance(dev.name, str)

class TestPropertyAccess:
    def test_get_brightness(self):
        """Test reading brightness property."""
        devices = duvc.devices()
        if not devices:
            pytest.skip("No devices available")
        
        cam = duvc.CameraController(0)
        brightness = cam.brightness
        assert 0 <= brightness <= 100
        cam.close()
    
    def test_set_out_of_range(self):
        """Test out-of-range value raises exception."""
        cam = duvc.CameraController(0)
        with pytest.raises(duvc.PropertyValueOutOfRangeError):
            cam.brightness = 999
        cam.close()

class TestErrorHandling:
    def test_invalid_device_index(self):
        """Test invalid device index raises error."""
        with pytest.raises(duvc.DeviceNotFoundError):
            cam = duvc.CameraController(9999)
    
    def test_device_disconnection(self):
        """Test graceful handling of disconnected device."""
        # Simulate disconnection (requires test fixture)
        # Verify no crash, appropriate exception raised
        pass
```

**Run tests**:

```bash
pip install pytest
pytest tests/test_bindings.py -v
```


***

#### CI/CD integration \& setup

**GitHub Actions workflow** to verify binding changes:

```yaml
name: Test Bindings
on: [pull_request, push]

jobs:
  test:
    runs-on: windows-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e .
      - run: pip install pytest
      - run: pytest tests/ -v
```

When submitting PR, CI verifies:

- All tests pass on multiple Python versions
- No new compiler warnings (clang-format check)
- Documentation builds without errors

***

#### Code review guidelines

Checklist for PR reviews:

**C++ changes** (pybind_module.cpp):

- [ ] Code formatted with `clang-format -i --style=llvm`
- [ ] RAII semantics correct (move-only types marked with `PYBIND11_MAKE_OPAQUE`)
- [ ] GIL properly managed in callbacks (`py::gil_scoped_acquire`)
- [ ] Result type properly unwrapped or handled
- [ ] Error message strings are descriptive

**Python bindings** (.pyi stub):

- [ ] New functions documented
- [ ] Type hints complete
- [ ] Docstrings follow NumPy style
- [ ] Examples in docstrings work

**Tests** (tests/):

- [ ] New code has test coverage (>90%)
- [ ] Edge cases covered (out-of-range, None, empty)
- [ ] Tests pass on all Python versions

**Documentation** (docs/):

- [ ] API reference updated
- [ ] Usage examples provided
- [ ] Windows-only features clearly marked

***

#### Internal test patterns

**Mock device testing** (when hardware unavailable):

```python
class TestWithMockDevice:
    @pytest.fixture(autouse=True)
    def mock_platform(self, monkeypatch):
        """Inject mock platform."""
        mock_impl = MockPlatformInterface()
        mock_impl.add_device(Device(name="MockCamera", path="mock://0"))
        duvc_ctl.create_platform_interface(mock_impl)
        yield
        duvc_ctl.create_platform_interface(None)  # Reset

    def test_camera_operations(self):
        """Test with simulated camera."""
        devices = duvc_ctl.devices()
        assert len(devices) == 1
        assert devices[0].name == "MockCamera"
```

**Error injection** (test error paths):

```python
class TestErrorRecovery:
    def test_recovery_on_timeout(self):
        """Test automatic retry on timeout."""
        with patch('duvc_ctl._internal.get_property') as mock_get:
            # Fail twice, succeed on third
            mock_get.side_effect = [
                duvc_ctl.DeviceBusyError(),
                duvc_ctl.DeviceBusyError(),
                42  # Success
            ]
            result = resilient_get_property(device, prop)
            assert result == 42
            assert mock_get.call_count == 3
```

