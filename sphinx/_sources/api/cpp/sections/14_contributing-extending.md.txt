## 14. Contributing \& Extending


### 14.1 Architecture Overview

The duvc-ctl library is built as a layered C++ system with clear separations for platform abstraction, property management, diagnostics, and extensibility via vendor extensions or language bindings. The core design provides:

- A modern C++17 API for direct device enumeration, control, and monitoring.
- An internal platform interface (DirectShow on Windows) handling all property and device I/O.
- A stable C/C ABI for language bindings (e.g., Python, CLI, planned Rust/Go) and external integration.
- Extension points for vendor-specific features (like Logitech properties) via dedicated extension headers and implementation modules.
- Utility namespaces for structured logging, error decoding, and device event monitoring.
- Thread-safe enumeration and multi-device control, with explicit documentation regarding COM/threading constraints for Windows.

For a graphical view and class breakdown, see the doxygen docs

***

### 14.2 Adding New Features

Adding a new device property or vendor extension typically involves:

- Defining new enum values in the relevant property or vendor extension header (e.g., `CamProp`, `VidProp`, or Logitech-specific types).
- Adding property query and set logic to the appropriate platform implementation (`directshow_impl.cpp` for Windows).
- If needed, writing additional getters/setters in utility/vendor extension modules, and registering these with the platform, C API, or language bindings as required.
- Documenting all new APIs and ensuring they are covered in both header comments and the markdown documentation.
- When introducing new language bindings, add and document minimal ABI-thin wrappers (see C API and Python binding source for reference patterns).

Pull requests for new features should include tests that cover new property queries, error paths, and input validation logic.

***

### 14.3 Testing [INCOMPLETE]

Testing is critical for both core and extension components:

- All new features must include C++ unit tests (located in the `tests/cpp/unit/`, `integration/`, or `functional/` folders as appropriate).
- Tests should exercise both successful and error paths using the result-based error handling mechanisms.
- The full test suite can be run with CTest for all platforms:

```
cd build
ctest --config Release --output-on-failure
```

- Integration and functional tests may require physical USB camera hardware attached; these are labeled accordingly in the test suite structure.
- For contribution, every pull request should include updated tests and relevant API documentation, in line with the project's standards (see README and CONTRIBUTING.md).

For complete details on coding standards, project layout, and community practices, contributors should review `CONTRIBUTING.md

