## 15. Advanced Architecture \& Special Methods


### 15.1 pybind11 Module Design

**Module initialization \& organization**: `PYBIND11_MODULE(duvcctl, m)` entry point defines main module. All types use `py::module_local` to prevent collision when multiple modules import duvc-ctl. Separate submodule for Windows-specific features (`logitech` submodule for vendor extensions).

**Module-local types**: Every pybind11 class declared with `.def` includes `, py::module_local` binding attribute. Prevents type identity conflicts if duvc-ctl imported via different paths. Core types: `Device`, `PropSetting`, `PropRange`, `PropertyCapability`, `Error`, all result types, enums.

**Submodules**: `logitech` submodule created via `py::module::def_submodule()`. Contains `LogitechProperty` enum and functions (`get_property()`, `set_property()`, `supports_properties()`). Access via `duvc_ctl.logitech.Property.RightLight`. Declared `#ifdef WIN32` — only available on Windows.

**Opaque RAII handling `PYBIND11_MAKE_OPAQUE`**: `Camera` class uses `PYBIND11_MAKE_OPAQUE(Camera)` declaration. Camera is **move-only, non-copyable** due to DirectShow handle management (RAII). Pybind11 normally generates copy constructors—opaque marker prevents this. Allows correct move semantics when Python receives `std::shared_ptr<Camera>`.

```
**Move semantics in Python**: Rvalue reference helper `unwrap_or_throw<T>(duvc::Result<T>&& result)` implemented for move-only types. Transfers ownership of non-copyable values (e.g., `Camera`) from result to Python via `std::move()`. Prevents "trying to copy non-copyable" errors. 
```

**Non-copyable types**: `Camera` and `DeviceCapabilities` are non-copyable C++ classes. Pybind11 bindings for these **omit copy constructors** and **omit copy helpers** (`Ok_Camera`, `Err_Camera`, `Ok_DeviceCapabilities`, `Err_DeviceCapabilities` NOT bound). Only move constructors and move assignment.

### 15.2 Pythonic Special Methods

**Context manager protocol `__enter__/__exit__`**: `Camera` class implements context manager via `.def("__enter__", ...)` and `.def("__exit__", ...)` bindings. Entering (`with cam:`) validates camera connection and returns self (shared_ptr). Exiting automatically triggers shared_ptr cleanup in destructor—DirectShow handle released by RAII. Exit method returns `false` (don't suppress exceptions). Usage: `with Camera(device) as cam: cam.set(...)`.

**Boolean conversion `__bool__()`**: All `Result<T>` types implement `.def("__bool__", ...)` returning `result.is_ok()`. Allows `if result:` pattern instead of `if result.is_ok()`. Device, PropSetting, PropRange also support boolean context. Falsy result = error state, truthy = success.

**Iterator protocol `__iter__/__len__`**: `DeviceCapabilities` class binds `.def("__iter__", ...)` to yield both camera and video properties combined into Python list. `.def("__len__", ...)` returns total property count. Enables `for prop in caps:` and `len(caps)`. Internally combines supported camera properties + supported video properties.

**Membership testing `__contains__`**: `PropRange` implements `.def("__contains__", ...)` delegating to `range.is_valid(value)`. Allows `if value in prop_range:` syntax to test if value within bounds/step.

**String representation `__str__/__repr__`**: All major types implement `.def("__str__", ...)` for user-friendly output and `.def("__repr__", ...)` for debug representation. Device: `str()` returns name, `repr()` shows name + path. PropRange: `str()` shows "min to max, step X"; `repr()` includes defaults. Error: `str()` returns message; `repr()` includes code.

**Equality \& hashing `__eq__/__ne__/__hash__`**: Device, PyGUID, PropSetting, PropRange all bind `.def("__eq__", ...)` comparing by value (Device by path, PyGUID by GUID bytes, etc.). `.def("__ne__", ...)` inverts equality. `.def("__hash__", ...)` enables dictionary/set usage. Device hashed by path; PyGUID by GUID structure. Allows `if dev1 == dev2:` and `devices_set = {device1, device2}`.

**Copy semantics `__copy__/__deepcopy__`**: Simple types (Device, PropSetting, PropRange, PyGUID, PropRange) implement `.def("__copy__", ...)` and `.def("__deepcopy__", ...)` as shallow/deep equivalents since no nested mutable state. Both return copy of self. Camera omits copy methods—move-only RAII type. VendorProperty, PropRange support full copy protocol.

### 15.3 Windows-Specific Features

**DirectShow integration COM/filter graph**: Library uses Windows DirectShow API to enumerate and control cameras via filter graphs and COM objects. `IEnumMoniker`, `IMoniker`, `IBaseFilter`, `IGraphBuilder` wrapped in pybind11 classes `PyEnumMoniker`, `PyBaseFilter`. Camera properties accessed through `IAMCameraControl`, `IAMVideoProcAmp` filter interfaces. Context manager pattern handles COM AddRef/Release lifecycle automatically.

**GUID handling PyGUID/parsing**: `PyGUID` class in pybind11 provides flexible GUID input parsing. Accepts Python `uuid.UUID` (extracts `.hex` attribute), string representations (with/without braces, dashes auto-added), 16-byte buffers (bytes, bytearray, memoryview). Parsing logic via `parsefromstring()` handles XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX format. Used in vendor property functions `getvendorproperty()`, `setvendorproperty()` for property set GUID parameter.

**HRESULT error codes decode/categorization**: Functions `decodehresult()`, `gethresultdetails()`, `isdeviceerror()`, `ispermissionerror()` decode Windows HRESULT values. `decodehresult(hresult)` returns human-readable description. Error codes categorized: `HRESULT_FROM_WIN32(ERROR_DEVICE_NOT_FOUND)` → DeviceNotFound, access denied → PermissionDenied, device busy → DeviceBusy. All platform-specific via `#ifdef WIN32`.

**KsPropertySet interface**: Wrapper class `KsPropertySet` providing Windows KsProperty access for vendor-specific properties bypassing standard DirectShow. Binds C++ `KsPropertySet` class with methods: `querysupport()`, `getproperty()` (raw bytes), `setproperty()` (raw bytes), plus typed accessors `getpropertyint()`, `setpropertyint()`, `getpropertybool()`, `setpropertybool()`, `getpropertyuint32()`, `setpropertyuint32()`. Accepts flexible GUID inputs via `guidfrompyobj()`.

**Windows-only types**: `VendorProperty` (struct wrapping property set GUID, property ID, and `vectoruint8_t` data), `DeviceConnection` (thin DirectShow wrapper for low-level property control via tuple-based returns), `KsPropertySet` (Windows KsProperty interface wrapper). All declared within `#ifdef WIN32`. Attempting to import on non-Windows raises `NotImplementedError`.

**Platform-specific behavior matrix**:


| Feature | Windows | Linux/Mac |
| :-- | :-- | :-- |
| Library availability | Full | ImportError |
| Device enumeration | DirectShow API | Not available |
| Property access | IAMCameraControl, IAMVideoProcAmp | Not available |
| GUID handling | Full PyGUID parsing | Not available |
| Vendor extensions | KsPropertySet, Logitech submodule | Not available |
| HRESULT decoding | `decodehresult()` | Not available |
| Context manager | Supported via COM lifecycle | Not available |


***

### 15.4 Type Hints \& Static Analysis

**Type hint coverage in signatures \& attributes**: Function signatures use full `Optional[]`, `Union[]`, `List[]`, `Dict[]`, `TypedDict` annotations. All public functions in `__init__.py` typed. Return types and parameter types fully specified. Example: `def getdeviceinfo(device: Device) -> DeviceInfo:`, `def setpropertysafe(...) -> Tuple[bool, str]:`. Comprehensive annotations targeting Python 3.8+.

**TypedDicts**: `PropertyInfo` TypedDict with fields `supported: bool`, `current: Dict[Literal["value", "mode"], Union[int, str]]`, `range: Dict[Literal["min", "max", "step", "default"], int]`, `error: Optional[str]`. `DeviceInfo` TypedDict: `name: str`, `path: str`, `connected: bool`, `cameraproperties: Dict[str, PropertyInfo]`, `videoproperties: Dict[str, PropertyInfo]`, `error: Optional[str]`. Enables IDE autocomplete and mypy struct checking.

**MyPy compatibility \& type stubs**: Inline type annotations in `.py` files enable mypy checking without separate `.pyi` stubs. Pybind11 C++ bindings expose types to Python type checker via annotations in `__init__.py`. Note: Planned for future—no explicit `.pyi` stub files generated yet, but inline annotations sufficient for mypy 0.910+.

**IDE support with autocomplete**: PyCharm, VSCode Pylance, and other IDE LSP clients read `__init__.py` annotations and bindings to provide function signature hints, parameter validation, return type inference. Type hints enable "Go to Definition" and type-aware refactoring. String annotations in TypedDict enable forward references.

**Type hint details and overloads**: Functions with multiple signatures use `@overload` pattern (in separate stubs or pybind11 `.def()` overloads). Example: `set()` method overloaded for `(CamProp, PropSetting)`, `(CamProp, int)` (value-only, manual mode), `(CamProp, int, str)` (value and mode string). Pybind11 bindings expose all overload signatures; Python type checker resolves via function name and argument types. Callables typed as `Callable[[Device], None]` for callbacks.

