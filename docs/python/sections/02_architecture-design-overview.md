## 2. Architecture & Design Overview


### 2.1 Two-Tier Architecture

duvc-ctl uses a layered design with two distinct Python APIs sitting on top of a shared C++ core. Both APIs access the same underlying DirectShow functionality but present different models to the user.

#### High-level overview

```
┌─────────────────────────────────────────────────┐
│          Python User Code                       │
├──────────────────────┬──────────────────────────┤
│ Pythonic API         │ Result-Based API         │
│ (CameraController)   │ (open_camera, Result<T>)│
├──────────────────────┴──────────────────────────┤
│   pybind11 Python Bindings                      │
├─────────────────────────────────────────────────┤
│        C++ Core Library (duvc-ctl)              │
│  (Device enumeration, property access, etc.)   │
├─────────────────────────────────────────────────┤
│      Windows DirectShow & COM                   │
└─────────────────────────────────────────────────┘
```

Both Python APIs call the same C++ code. The difference is in how they handle device lifecycle, errors, and API design.

#### Pythonic API (Exception-based)

The Pythonic API, implemented in `CameraController`, wraps the C++ core and adds Python conventions:

- **Error handling**: Exceptions (`DuvcError` and subclasses) are raised for failures. Callers use `try-except` blocks.
- **Device management**: Automatic device selection (first camera, or by name). Connection/disconnection handled via context manager (`with` statement).
- **API style**: Property-based access (`cam.brightness = 75`) and method calls (`cam.pan_relative(15)`).
- **State**: The controller maintains internal state—the active device, connection handle, property cache—so the user doesn't think about it.

**Example**:

```python
import duvc_ctl as duvc

try:
    with duvc.CameraController() as cam:
        cam.brightness = 80
        print(f"Brightness: {cam.brightness}")
except duvc.PropertyNotSupportedError as e:
    print(f"Cannot set brightness: {e}")
```

**When to use**: Learning, scripting, simple applications where you want minimal boilerplate.

#### Result-Based API (Explicit error handling)

The Result-Based API, in the `init.py` module, provides low-level control without exceptions:

- **Error handling**: Functions return `Result<T>` types. Callers check `is_ok()` or `is_error()` and access the value or error explicitly.
- **Device management**: Explicit. You pass a `Device` or device index to each function.
- **API style**: Functional (`open_camera(device)`, `camera.get(property)` returns `Result<PropSetting>`).
- **State**: Minimal and explicit. You own the Device and Camera objects.

**Example**:

```python
import duvc_ctl as duvc

devices = duvc.list_devices()
if not devices:
    print("No devices found")
else:
    device = devices[0]
    camera_result = duvc.open_camera(device)
    
    if camera_result.is_ok():
        camera = camera_result.value()
        brightness_result = camera.get(duvc.VidProp.Brightness)
        
        if brightness_result.is_ok():
            setting = brightness_result.value()
            print(f"Brightness: {setting.value}")
        else:
            print(f"Error: {brightness_result.error().description()}")
    else:
        print(f"Error: {camera_result.error().description()}")
```

**When to use**: Production code, detailed error recovery, systems that need to handle failures gracefully without exception overhead.

#### Design rationale

**Two APIs instead of one?**

The Pythonic API is easier to use for most cases. But production systems often need explicit error handling and minimal overhead. Rather than compromise with a single API, we provide both:

- Beginners and scripts use the simpler Pythonic API.
- Production code that needs fine-grained control uses the Result-Based API.
- Both use the same C++ backend, so there's no code duplication in the core logic.

**Why exceptions vs. results?**

- **Pythonic API (exceptions)**: Python developers expect exceptions. They're idiomatic. Errors are detected early (at the point of failure) and propagate up without explicit checks.
- **Result-Based API (results)**: No exceptions mean no exception-throwing overhead. Each operation is explicit—you see exactly where errors are handled. This is valuable in production systems where you need to recover from failures gracefully.


#### C++ bindings layer (pybind11)

The bridge between Python and C++ is pybind11. It handles:

- Type conversion (Python `int` ↔ C++ `int32_t`, Python `str` ↔ C++ `std::string`, etc.)
- Lifetime management (Python garbage collection ↔ C++ RAII and reference counting)
- Exception translation (C++ exceptions to Python exceptions in the Pythonic API)
- Module organization (separate namespaces for Pythonic and Result-based APIs)

The Result-Based API types (`Result<T>`, `Device`, `PropSetting`, etc.) are bound directly from C++ to Python. The Pythonic API (CameraController) is written entirely in Python and uses the Result-based bindings internally.

#### Thread safety

Both APIs are **thread-safe** at the module level, but individual devices are **not thread-safe**:

- Multiple threads can safely call `list_devices()`, open different cameras, etc.
- If two threads access the same camera (same `CameraController` or `Camera` object), data races can occur. Use a lock or ensure only one thread accesses a camera at a time.

Example of thread-safe usage (different cameras per thread):

```python
import duvc_ctl as duvc
import threading

def camera_worker(camera_index):
    with duvc.CameraController(camera_index) as cam:
        cam.brightness = 75
        print(f"Camera {camera_index}: brightness set")

devices = duvc.list_devices()
threads = [threading.Thread(target=camera_worker, args=(i,)) for i in range(len(devices))]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

The C++ core uses a mutex internally to protect shared state (DirectShow device enumeration). Individual camera operations do not hold this mutex long; property get/set operations lock only the minimal necessary time to avoid contention.

#### Connection state machine

A camera connection goes through these states:

1. **Closed**: No active connection.
2. **Opening**: Connecting to the device (transitional).
3. **Open**: Connected; properties can be read and written.
4. **Closing**: Disconnecting (transitional).

The Pythonic API (`CameraController`) manages these transitions automatically via the context manager. You enter the `with` block → connection opens. You exit the `with` block → connection closes.

The Result-Based API requires you to manage state explicitly:

```python
camera_result = duvc.open_camera(device)  # Opens connection
if camera_result.is_ok():
    camera = camera_result.value()
    # Use camera...
    # Connection closes when camera object is destroyed or explicitly closed
```


#### Error propagation

**Pythonic API**:

- Errors are raised as exceptions. The exception propagates up the call stack until caught or reaches the top level (where Python prints a traceback).

**Result-Based API**:

- Errors are wrapped in the Result type. You check `is_ok()` or `is_error()` and access the error via `error()`. No automatic propagation; you decide how to handle each error.


#### Why this design?

1. **Separation of concerns**: Pythonic API handles convenience; Result-Based API handles control.
2. **Flexibility**: Users pick the API that fits their use case.
3. **Performance**: The Result-Based API avoids exception overhead if desired.
4. **Production-ready**: Both are suitable for production; the choice is about error handling philosophy.


### 2.2 API Comparison \& Selection

This section compares both APIs head-to-head so you can choose the right one for your use case.

#### When to use each API

| Scenario | Recommended API | Why |
| :-- | :-- | :-- |
| Learning or prototyping | Pythonic | Fewer lines of code, quick iteration |
| Quick script or automation | Pythonic | Automatic device selection, built-in defaults |
| Production application with error handling | Result-based | Explicit error checks, no exceptions, full control |
| High-frequency camera control loop | Result-based | Lower overhead; no exception throwing |
| Handling multiple cameras concurrently | Either | Both are thread-safe; choose based on error handling preference |
| Interactive or CLI application | Pythonic | Users expect exceptions; easier debugging |
| Embedded or headless system | Result-based | Explicit error handling fits production patterns |
| Real-time or time-critical code | Result-based | Predictable performance; no exception overhead |

#### Detailed feature comparison

| Feature | Pythonic | Result-Based |
| :-- | :-- | :-- |
| **Device Selection** | Automatic (first device or by name) | Manual (you pass Device) |
| **Error Handling** | Exceptions (`try-except`) | Result types (`is_ok()` / `is_error()`) |
| **Property Access** | Direct (`cam.brightness = 75`) | Method call (`camera.set(VidProp.Brightness, ...)`) |
| **Code Style** | Object-oriented | Functional |
| **Boilerplate** | Minimal | More verbose |
| **Exception Overhead** | Yes (thrown on error) | No (checks Result) |
| **Error Details** | Exception message + type | Error code + detailed description |
| **Device Lifecycle** | Context manager (`with`) | Manual (you control lifetime) |
| **State Management** | Automatic (maintained by controller) | Manual (you own state) |
| **Learning Curve** | Beginner-friendly | Moderate |
| **IDE Autocomplete** | Good (Python class) | Good (types exported) |
| **Type Hints** | Yes (CameraController class) | Yes (Result<T> and types) |

#### Device management lifecycle

Both APIs handle device discovery, connection, and disconnection, but at different levels.

**Pythonic API lifecycle:**

```python
import duvc_ctl as duvc

# 1. Discovery (implicit)
# First camera found automatically during construction
with duvc.CameraController() as cam:
    # 2. Connected
    cam.brightness = 75
    # 3. Auto-disconnect on exit
```

**Result-based API lifecycle:**

```python
import duvc_ctl as duvc

# 1. Explicit discovery
devices = duvc.list_devices()

# 2. Explicit connection
camera_result = duvc.open_camera(devices[0])
if camera_result.is_ok():
    camera = camera_result.value()
    
    # 3. Use camera
    brightness_result = camera.get(duvc.VidProp.Brightness)
    
    # 4. Implicit disconnect when camera object is destroyed
```


#### Error handling strategies

**Pythonic API (exception-based):**

```python
import duvc_ctl as duvc

try:
    with duvc.CameraController() as cam:
        cam.brightness = 999  # Out of range
except duvc.InvalidValueError as e:
    print(f"Invalid value: {e}")
except duvc.PropertyNotSupportedError:
    print("Brightness not supported")
except duvc.DeviceNotFoundError:
    print("No camera found")
```

Advantages:

- Errors interrupt execution; you can't accidentally ignore them.
- Idiomatic Python; most libraries use exceptions.
- Compact code for the happy path.

Disadvantages:

- Exception handling adds overhead (though typically small).
- Stack unwinding can complicate debugging in some cases.

**Result-based API (explicit):**

```python
import duvc_ctl as duvc

devices = duvc.list_devices()
if not devices:
    print("No camera found")
else:
    device = devices[0]
    camera_result = duvc.open_camera(device)
    
    if camera_result.is_ok():
        camera = camera_result.value()
        brightness_result = camera.get(duvc.VidProp.Brightness)
        
        if brightness_result.is_ok():
            setting = brightness_result.value()
            print(f"Brightness: {setting.value}")
        else:
            error = brightness_result.error()
            print(f"Error: {error.description()}")
    else:
        error = camera_result.error()
        print(f"Failed to open camera: {error.description()}")
```

Advantages:

- No hidden control flow; every error is explicit.
- No exception overhead.
- Detailed error codes and descriptions available.

Disadvantages:

- More boilerplate (more `if` statements).
- Error handling is mandatory; harder to "forget."


#### Performance comparison

Both APIs ultimately call the same C++ code, so performance differences are small. However, there are measurable differences in specific scenarios:


| Operation | Pythonic | Result-Based | Notes |
| :-- | :-- | :-- | :-- |
| Single property read (success) | ~100 µs | ~95 µs | Pythonic has minimal overhead; difference negligible |
| Single property read (error path) | ~200 µs | ~100 µs | Exceptions slow down error handling |
| Rapid property reads (1000x) | ~100 ms | ~95 ms | Exception overhead adds up over many calls |
| Device enumeration | ~10 ms | ~10 ms | Same code path; no difference |
| Context manager overhead | ~5 µs | N/A | Negligible |

(These values are estimates and not entirely accurate, timings may differ depending on the system and devices)
**Practical takeaway**: For most use cases, the performance difference is imperceptible. Only if you're performing thousands of property operations in a tight loop should you consider the Result-based API for performance.

#### Trade-offs summary

**Choose Pythonic if**:

- You're learning or prototyping.
- Your code is straightforward with few error cases.
- You like Python idioms and exceptions.
- You want less boilerplate.
- Performance is not critical.

**Choose Result-based if**:

- You need detailed error recovery logic.
- You're building a production system that must handle failures gracefully.
- You want explicit, predictable control flow (no exception throwing).
- You're processing high volumes of property operations.
- You need to distinguish between different error types programmatically.
- You prefer functional APIs and explicit error handling.


#### Mixing both APIs

You can use both APIs in the same application. The Pythonic API's `CameraController` has a `.core` property that gives you the underlying Result-based `Camera` object:

```python
import duvc_ctl as duvc

with duvc.CameraController() as cam:
    # Use Pythonic API
    cam.brightness = 75
    
    # Drop down to Result-based API for detailed control
    core_camera = cam.core
    brightness_result = core_camera.get(duvc.VidProp.Brightness)
    
    if brightness_result.is_ok():
        setting = brightness_result.value()
        print(f"Current brightness: {setting.value}")
```

This gives you flexibility: start simple with the Pythonic API, and switch to explicit Result handling when you need more control.

### 2.3 Core Design Patterns

This section explains the key design principles that shape duvc-ctl's architecture, threading model, and internal behavior.

#### Resource ownership and RAII

duvc-ctl follows the **Resource Acquisition Is Initialization (RAII)** principle throughout its C++ core. Every resource (COM objects, device handles, property state) is tied to an object's lifetime.

**In C++**:

```cpp
class Device {
public:
    Device() { /* acquire DirectShow resources */ }
    ~Device() { /* release DirectShow resources */ }
private:
    IMFDeviceEnumerator* enumerator;  // Owned; freed in destructor
};
```

When a Device object is destroyed, all associated DirectShow resources are automatically released. This prevents memory leaks and dangling pointers.

**In Python (Pythonic API)**:

The `CameraController` manages a device lifecycle implicitly:

```python
with duvc.CameraController() as cam:
    # Resources acquired at __enter__
    cam.brightness = 75
# Resources released at __exit__, even if an exception occurred
```

The `with` statement ensures cleanup happens, following Python's context manager protocol.

**In Python (Result-based API)**:

Resources are explicitly managed:

```python
camera_result = duvc.open_camera(device)
if camera_result.is_ok():
    camera = camera_result.value()
    # Use camera
    # Destructor called when camera goes out of scope
```

Python's garbage collector triggers the destructor, which releases C++ resources via pybind11.

#### Threading and concurrency model

duvc-ctl is designed for **multi-threaded environments** but with careful constraints.

**Module-level thread safety**:

The module's global state (device enumeration cache, module initialization) is protected by an internal mutex. Multiple threads can safely call:

```python
import duvc_ctl as duvc
import threading

def thread_worker(index):
    devices = duvc.list_devices()  # Safe; uses module lock internally
    print(f"Thread {index} found {len(devices)} devices")

threads = [threading.Thread(target=thread_worker, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

**Per-camera thread safety**:

Once a device is opened, accessing a single camera from multiple threads is **not thread-safe** without external synchronization. Each camera is a single-threaded object and must be accessed from the thread it was marshalled from. This is a result of the COM model used by windows.

```python
# BAD: Race condition
import duvc_ctl as duvc
import threading

with duvc.CameraController() as cam:
    def thread_worker():
        cam.brightness = 50  # Unsafe if another thread accesses cam simultaneously
    
    threads = [threading.Thread(target=thread_worker) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()

# GOOD: Multiple cameras, one per thread
import duvc_ctl as duvc
import threading

devices = duvc.list_devices()

def thread_worker(device_index):
    with duvc.CameraController(device_index) as cam:
        cam.brightness = 50  # Each thread has its own camera; safe

threads = [threading.Thread(target=thread_worker, args=(i,)) for i in range(len(devices))]
for t in threads: t.start()
for t in threads: t.join()
```

**Concurrency strategy**:

- Share devices across threads: Use a lock around camera operations.
- Don't share devices: Each thread gets its own camera (preferred).
- Module-level operations (`list_devices()`, `open_camera()`) are always safe.


#### C++ core vs. Python wrapper layer

duvc-ctl's architecture has two distinct layers:

**C++ Core**:

- Pure C++17 with minimal dependencies.
- Direct access to Windows COM interfaces (DirectShow).
- Handles device enumeration, property access, and DirectShow API calls.
- No Python knowledge; can be used independently or from other languages via C bindings.

**Python Wrapper (pybind11)**:

- Binds C++ types to Python (Device, Camera, Result<T>, etc.).
- Translates Python exceptions to C++ exceptions and vice versa.
- Manages object lifetime (Python GC ↔ C++ destructors).
- Provides type conversion (Python `str` ↔ C++ `std::string`).

The Pythonic API (`CameraController`) is written entirely in Python and uses the pybind11 bindings internally:

```
User Python Code
    ↓
CameraController (Python)
    ↓
pybind11 Bindings (Device, Camera, Result<T>)
    ↓
C++ Core
    ↓
DirectShow & Windows COM
```

This layering allows:

- The C++ core to evolve independently of Python bindings.
- Python code to be simple and Pythonic (using Python idioms).
- The pybind11 layer to be thin (mostly type translations, not business logic).


#### Move semantics in Python bindings

The C++ core uses **move semantics** to efficiently transfer ownership of resources without copying:

```cpp
// C++
Result<Camera> open_camera(const Device& device) {
    auto camera = std::make_unique<Camera>(device);
    return Result<Camera>(std::move(camera));  // Move, don't copy
}
```

pybind11 preserves this semantic when binding to Python. When you receive a Camera from Python, it's a move-constructed object with full ownership:

```python
camera_result = duvc.open_camera(device)
if camera_result.is_ok():
    camera = camera_result.value()  # Efficient transfer of ownership
```

Internally, pybind11 uses holder types to manage the C++ object's lifetime through Python's garbage collector. When `camera` goes out of scope in Python, the C++ object is destroyed and its resources freed.

#### Connection management state machine

A camera connection follows these states:


| State | Description | Valid Transitions |
| :-- | :-- | :-- |
| Closed | No active connection to device | → Opening |
| Opening | Attempting to connect | → Open, → Closed (on failure) |
| Open | Connected; properties can be read/written | → Closing |
| Closing | Disconnecting | → Closed |
| Error | Connection failed or lost | → Opening (retry) |

**Pythonic API state transitions**:

```python
with duvc.CameraController() as cam:  # Closed → Opening → Open
    cam.brightness = 75                # Operations in Open state
# Open → Closing → Closed
```

**Result-based API state transitions**:

```python
camera_result = duvc.open_camera(device)  # Closed → Opening
if camera_result.is_ok():                  # Succeeded; now Open
    camera = camera_result.value()
    brightness_result = camera.get(duvc.VidProp.Brightness)
    if brightness_result.is_ok():
        setting = brightness_result.value()
# Open → Closing → Closed (on camera destruction)
```

State violations (e.g., trying to access a property in Closed state) raise an exception or return an error.

#### Device discovery patterns

Device discovery follows a **lazy enumeration** pattern:

1. **On demand**: Devices are discovered when `list_devices()` is called, not at module import.
2. **Caching**: The device list is cached; repeated calls are fast.
3. **Invalidation**: The cache is invalidated if device hotplug events are detected (if callback registered).

**Example**:

```python
import duvc_ctl as duvc

# First call: actual enumeration via DirectShow
devices1 = duvc.list_devices()

# Second call: returns cached list (no DirectShow overhead)
devices2 = duvc.list_devices()

# Register for device change notifications
def on_device_change(added, device_path):
    print(f"Device {'added' if added else 'removed'}: {device_path}")

duvc.register_device_change_callback(on_device_change)

# When a device is plugged/unplugged, the callback fires and the cache is invalidated
```


#### Thread safety guarantees

duvc-ctl provides these thread-safety guarantees:


| Operation | Thread-Safe | Notes |
| :-- | :-- | :-- |
| `list_devices()` | ✓ Yes | Internally synchronized |
| `open_camera(device)` | ✓ Yes | Returns independent Camera object |
| `camera.get(property)` (single camera) | ✗ No | Use lock if accessing from multiple threads |
| `camera.set(property, value)` (single camera) | ✗ No | Use lock if accessing from multiple threads |
| Multiple cameras in different threads | ✓ Yes | Each camera is isolated |
| Device change callbacks | ✓ Yes | Callbacks are thread-safe; executed on internal worker thread |
| `register_device_change_callback()` | ✓ Yes | Safe to call from any thread |

**Safe multi-threaded pattern**:

```python
import duvc_ctl as duvc
import threading
from threading import Lock

devices = duvc.list_devices()

# One camera per thread: no lock needed
def worker(device_index):
    with duvc.CameraController(device_index) as cam:
        cam.brightness = 75

threads = [threading.Thread(target=worker, args=(i,)) for i in range(len(devices))]
for t in threads: t.start()
for t in threads: t.join()
```

**Unsafe pattern (and how to fix it)**:

```python
# UNSAFE: Multiple threads accessing same camera
with duvc.CameraController() as cam:
    def worker():
        cam.brightness = 75  # Race condition!
    
    threads = [threading.Thread(target=worker) for _ in range(4)]
    # ...

# SAFE: Use a lock
with duvc.CameraController() as cam:
    lock = Lock()
    
    def worker():
        with lock:
            cam.brightness = 75  # Protected by lock
    
    threads = [threading.Thread(target=worker) for _ in range(4)]
    # ...
```

