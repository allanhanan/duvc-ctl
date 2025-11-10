## 14. Troubleshooting \& FAQs


### 14.1 Common Issues

**Camera not detected**

Symptoms: `DeviceNotFoundError` on `list_devices()` or `CameraController(0)`. DirectShow fails to enumerate device. Causes: Camera disconnected, not yet recognized by OS, in use by another application, or missing/outdated drivers.

Solutions: Verify camera physically connected to USB port (preferably USB 3 for speed). Check Device Manager (Windows)—camera should appear under "Imaging devices" or "Universal Serial Bus controllers". If missing, run "Scan for hardware changes". Update camera drivers from manufacturer or Windows Update. Uninstall conflicting software (OBS, Zoom, other camera apps using exclusive access). Power-cycle camera and computer. Try different USB port.

**Permission denied**

Symptoms: `PermissionDeniedError` when opening camera or setting properties. Cause: Another process holds exclusive device handle. DirectShow allows only one application full control at a time.

Solutions: Close all camera applications (VLC, Zoom, Skype, OBS, browser camera access). Disable internal laptop camera if conflicts (Device Manager → Disable). Restart camera service or restart computer. Run application as Administrator if user account lacks device access. Check Windows privacy settings: Settings → Privacy \& Security → Camera—ensure permission enabled for application.

**Property not supported**

Symptoms: `PropertyNotSupportedError` when reading/setting specific property (brightness, zoom, pan). Cause: USB camera hardware doesn't implement that property in DirectShow, or device vendor disabled it.

Solutions: Query device capabilities first with `get_supported_properties()` or `get_device_info()`. Only use properties in returned list. Check device documentation. Some USB cameras lack pan/tilt (non-PTZ models). Brightness typically supported; zoom/pan rare on consumer cameras. Test with `get_property_range()` — if returns `None`, property unsupported. Gracefully skip unsupported properties in code rather than failing. Use presets designed for device type.

***

### 14.2 Value \& Connection Issues

**Out of range values**

Symptoms: `InvalidValueError` when setting property to value outside valid bounds. Cause: Value exceeds device-reported range (e.g., brightness 300 when max is 255).

Solutions: Always query range before setting: `range_info = cam.get_property_range("brightness")`. Clamp user input to [min, max]. Some devices report incorrect ranges—catch error and retry with middle value. Check if step alignment required (e.g., some properties need multiples of step). Add validation layer: `if value in range_info` before applying.

**Device busy**

Symptoms: `DeviceBusyError` or timeout when accessing camera. Property read/write hangs or fails. Cause: Camera processing autofocus, autofocus locked, or hardware temporarily unavailable. Another thread accessing same device without synchronization.

Solutions: Use locks if multi-threaded: `with lock: cam.brightness = 100`. Add timeout to property operations (library may not expose—workaround: timeout wrapper in Python). Disable autofocus or wait for convergence before accessing focus property. Try again after 100–500ms delay. Close and reopen camera if persistent. Query simpler properties (like brightness) to verify device responsive before complex ops (like focus).

**Import failures on Python**

Symptoms: `ImportError: cannot import name 'duvcctl'` or module not found. Cause: C extension not built, installed for wrong Python version, or Windows path issues.

Solutions: Reinstall from PyPI: `pip install duvc-ctl --upgrade`. Verify Python version matches wheel: `python --version` should match `cp38`, `cp39`, etc. in wheel filename. On Windows, ensure Microsoft C++ Redistributables installed (Visual Studio Runtime). Check duvc-ctl is Windows-only; on Linux/Mac, import fails intentionally. Enable debug: `pip install -v duvc-ctl` to see build details. For development: build locally per CONTRIBUTING.md.

**Device-specific workarounds**

Logitech cameras: May not support all standard UVC properties. Check `supports_logitech_properties()` and use `get_logitech_property()` if vendor-specific properties. Brands like FLIR: Require absolute exposure calibration, may not support manual zoom. Built-in laptop cameras: Often lock saturation/gamma to fixed values (ignore `InvalidValueError`). Cheap USB 1.1 cameras: Brightness range  not ; query actual range. Motorized iris cameras: Iris setting may be slow; add 200ms delay before reading back. PTZ cameras: Pan/tilt may move asynchronously; poll position after setting to confirm arrival.

***

### 14.3 Build \& Performance Issues

**Build issues on Windows**

Symptoms: CMake fails, MSVC compiler errors, pybind11 not found, wheel build fails.

Solutions: Ensure MSVC 2019+ installed (Visual Studio Build Tools sufficient). CMake 3.15+: `cmake --version`. Install pybind11 via pip or vcpkg: `pip install pybind11`. For scikit-build-core builds: `pip install build`, then `python -m build`. DirectShow headers should be in Windows SDK (auto-located). If CMake can't find DirectShow: manually set `DIRECTSHOW_PATH` environment variable to SDK install. Build from repository: `git clone`, `pip install -e .` with editable mode for development. Check Python architecture (32 vs 64-bit) matches MSVC toolchain.

**Performance considerations**

Property read latency: Each property access is I/O over USB. Typical latency 5–50ms per operation depending on USB speed (USB 2 slower than USB 3). Avoid polling all properties every millisecond—group into batches, poll every 200–500ms. Multi-camera: Use threading; each camera can block during autofocus or property set. Main thread stays responsive if camera I/O in worker threads. Avoid rapid write-read loops (set brightness, read brightness, set zoom, read zoom serially). Instead: queue all writes, then batch-read in single pass.

**Memory efficiency**

Device list cached after `list_devices()`; doesn't auto-update on hotplug. Cache for 1–5 seconds or until user refreshes. Property ranges cached locally after first query; avoids redundant hardware I/O. String conversions (property names to/from enums) are fast; no overhead. Exception creation (catching `PropertyNotSupportedError`) has minimal cost. Avoid storing entire `DeviceInfo` dict if only name/path needed—store just those fields.

**Performance optimization guides**

Batch property operations: Set multiple properties before reading. Use `get_device_info()` once (returns all capabilities) instead of calling `get_property_range()` per property. Profile property access: `import time; t = time.time(); cam.brightness = 100; print(time.time() - t)`. Expect 10–30ms per USB transaction. For real-time control (UI feedback loop), cache ranges and avoid setting every frame—only on user input. Minimize property queries in hot loops; poll device health (via simple read) instead of full enumeration every iteration.

**Performance benchmarks**
**NOTE:** These are estimates, actual values vary from device to device and based on system

Single property read: 5–15ms (USB 2), 2–5ms (USB 3). Single property write: 10–30ms. `list_devices()`: 50–200ms (depends on number of cameras and system load). `get_device_info()`: 100–500ms (queries all properties). Multi-camera (3 cameras): Sequential 1.5s, concurrent (threads) 500ms. Autofocus operation: 500–2000ms until convergence. Pan/tilt movement: 100–500ms to destination. Avoid calling `list_devices()` in real-time loops; cache list and update on hotplug callback. For low-latency applications: pre-query ranges, pre-compute valid value sets, apply in single batch.

