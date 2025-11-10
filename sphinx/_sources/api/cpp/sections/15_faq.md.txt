## 15. FAQ

### 15.1 General Questions

**Q: What is duvc-ctl?**
A: duvc-ctl is an open-source library and toolset for controlling USB UVC cameras on Windows using the DirectShow API. It provides modern C++ and Python APIs, as well as a CLI, for adjusting properties like pan, tilt, zoom, exposure, focus, and more, without vendor SDKs.

**Q: Does duvc-ctl require any special hardware or drivers?**
A: The library works with standard UVC-compliant cameras on Windows 10/11 and does not require additional drivers beyond the built-in Windows USB camera drivers.

**Q: Is Linux or Mac supported?**
A: Currently, duvc-ctl only supports Windows via DirectShow. There are plans or interest discussed for Linux support in the future, but it is not presently available.

**Q: What language bindings are supported?**
A: Official bindings exist for C++ and Python. CLI tools are provided, and Rust/Go/Node.js/C\# bindings are under development or planned.

**Q: How do I install duvc-ctl?**
A: For Python, use `pip install duvc-ctl`, or build from source for C++/CLI usage. See the README and installation instructions for full details.

***

### 15.2 Technical Questions

**Q: What camera features can I control?**
A: Any property exposed via DirectShow, including pan, tilt, zoom, focus, exposure, brightness, contrast, gamma, and vendor extensions (e.g., Logitech features).

**Q: How do I enumerate connected cameras?**
A: Use `list_devices()` in the C++/Python API or the CLI command `duvc-cli list`. Each device is identified by name and system path.

**Q: Can I safely control multiple cameras at once?**
A: Yes. The core library supports concurrent device control and thread-safe enumeration. However, access to the same device from different threads must be externally synchronized due to Windows COM rules.

**Q: How do I check if a property is supported on my camera?**
A: Always query the property range or support API (such as `get_camera_property_range`) before attempting to set a value. Unsupported properties will return an error or indicate no valid range.

**Q: How can I debug or get diagnostic information?**
A: Enable verbose logging using the logging API, or use the diagnostic utilities (e.g., `get_diagnostic_info()` in C++). All errors use a typed result or error object system to provide detail.

**Q: How do I contribute or report issues?**
A: Open issues or pull requests on the GitHub repository. See the `CONTRIBUTING.md` guide for requirements regarding code, documentation, and testing.

For detailed installation, bug reporting, building, or extending the library, always refer to the GitHub project and included documentation files (README.md, CONTRIBUTING.md, etc.).

