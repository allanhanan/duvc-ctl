## 16. Architecture Decision Records


### 16.1 Design Decisions

**Two-tier API rationale**: The library exposes both `CameraController` (Pythonic, exception-based) and Result-based API (explicit `Result<T>` types). This dual approach accommodates two user groups: developers preferring try-except patterns and those needing explicit error handling. Both APIs share identical C bindings, reducing maintenance overhead while providing maximum flexibility. Users choose based on application error-handling philosophy rather than being forced into one style.

```
**Exception vs Result API trade-offs**: Exception-based API raises specific exceptions (`DeviceNotFoundError`, `PropertyNotSupportedError`, `PermissionDeniedError`) for failed operations. Result-based API returns `Result<T>` containing success value or detailed error code. Trade-offs: Exceptions cleaner for happy-path code but require knowledge of all exception types; `Result<T>` forces explicit error checking but is verbose. The dual approach lets each user choose based on their codebase structure. 
```

**Threading model justification**: Python GIL released during C++ I/O operations (property get/set via DirectShow). Allows Python threads to run in parallel during blocking camera operations. No built-in locking—caller manages device access serialization with `threading.Lock`. Justification: DirectShow filter handles are inherently thread-unsafe; delegating synchronization to caller enables granular control without forced global locks. Different devices can be accessed concurrently safely.

**Error handling strategy**: Errors categorized into specific exception types in Pythonic API, mapped from Windows HRESULT values and library-specific error codes. Result-based API uses `Result<T>` discriminated union with explicit `ErrorCode` enum. HRESULT values from DirectShow decoded via `decodehresult()` into semantic error codes (DeviceNotFound, PermissionDenied, etc.). Strategy enables precise error recovery and clear error semantics across both APIs.

**Connection management design**: Each `Camera` instance maintains single persistent connection to device via `std::shared_ptr<Camera>`. No connection pooling—OS manages underlying USB connection lifecycle. Context manager protocol (`__enter__/__exit__`) ensures RAII cleanup automatically. Justification: DirectShow filter handles require careful lifecycle management; `shared_ptr` + context manager provides safe automation without caller boilerplate. Creating new `Camera` instances for same device is inefficient; reuse instances.

### 16.2 Implementation Rationale

**Why pybind11**: Modern C++ binding library with minimal boilerplate, automatic type conversions, excellent Python 3.8+ support, and move semantics handling. Avoids ctypes fragility and SWIG complexity. Enables opaque RAII types (`PYBIND11_MAKE_OPAQUE(Camera)`) to be passed safely to Python without generating copy constructors. Module-local types prevent symbol collisions when multiple modules import duvc-ctl.

**Why DirectShow**: Windows standard for USB Video Class (UVC) device enumeration and property control. All consumer UVC cameras expose DirectShow interfaces; no alternative unified Windows API achieves comparable coverage. WinRT camera APIs are newer and not universally available. DirectShow provides `IAMCameraControl` and `IAMVideoProcAmp` COM interfaces for standard camera properties (Pan, Tilt, Zoom, Exposure, Brightness, Contrast, etc.).

**Why property enums**: Enum-based property access (`CamProp.Pan`, `VidProp.Brightness`) provides type safety and IDE autocomplete. Avoids string-based property names prone to typos. Enables compile-time validation. Property descriptor objects (`PropSetting`, `PropRange`) encapsulate value + control mode (auto/manual), reducing boilerplate.

```
**Why Result types**: Explicit `Result<T>` error handling without exceptions enables embedded and hot-path use cases. Allows chaining operations with `.is_ok()` checks without exception overhead. Mirrors Rust Result pattern for clarity and predictability. C++ naturally expresses this via template specialization (`Result<PropSetting>`, `Result<PropRange>`, etc.). Enables caller to decide: handle per-operation or propagate via exception wrapper. 
```

**Why abstract interfaces**: `IPlatformInterface` and `IDeviceConnection` enable platform abstraction (future Linux support) and testing via Python subclassing. Trampoline classes (`PyIPlatformInterface`, `PyIDeviceConnection`) let Python override methods for mock implementations or custom backends. Decouples DirectShow specifics from Python API contract.

### 16.3 Future Planning

**Roadmap items (planned for future)**: Linux support via v4l2-ctl or custom backends; batch property operations (`set_multiple()`, `get_multiple()` with partial failure tracking); connection pooling for multi-device scenarios; property change callbacks and subscriptions; query caching API to avoid redundant device queries; MacOS support via AVFoundation; performance optimization profiles. Mediafoundation support for Windows fallback

**Planned features NOT currently implemented**: Deprecated function list, version-specific feature availability matrix, migration guides from older versions, performance comparison matrices, threading safety matrix, MyPy `.pyi` type stubs, resource pooling API, advanced connection management. Current inline type annotations in `__init__.py` sufficient for mypy; `.pyi` stubs planned if bindings grow.

**Backwards compatibility strategy**: Dual-API approach ensures compatibility across major versions. New features added without breaking existing signatures. Planned: semantic versioning (MAJOR.MINOR.PATCH) with clear deprecation policy. Breaking changes require major version bump with deprecation warnings in prior releases.

**Deprecation strategy**: Planned for future. Will follow PEP 387: mark function deprecated via `DeprecationWarning`, maintain for 2+ minor versions, remove in next major version. Deprecation notices in docstrings and changelog. No deprecated functions currently.

**Version planning**: Current stable: 2.0.0. Future 2.1+, 2.2+ for new features (planned items above) without breaking changes. x.x.1, x.x.2 for minor Bug fixes. Major version 3.0 for breaking changes or complete API redesigns. Roadmap tracked in GitHub issues and milestones. Release cycle: idk

