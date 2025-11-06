## 9. Logging, Diagnostics \& Callbacks


### 9.1 Logging Functions \& Level Management

Core logging control with per-level message functions and optional callbacks for structured event handling.

***

#### set_log_level() - configure minimum log level

Set the minimum log level for library output. Levels: Debug, Info, Warning, Error, Critical.

```python
def set_log_level(level: LogLevel) -> None:
    """Set minimum log level to capture."""
```

**LogLevel enum values**:


| Level | Order | Use Case |
| :-- | :-- | :-- |
| `LogLevel.Debug` | 0 (lowest) | Verbose tracing of all operations |
| `LogLevel.Info` | 1 | General information, device enumeration |
| `LogLevel.Warning` | 2 | Recoverable issues, degraded operation |
| `LogLevel.Error` | 3 | Operation failures, retryable errors |
| `LogLevel.Critical` | 4 (highest) | Severe failures, unrecoverable states |

**Usage**:

```python
import duvc_ctl as duvc

# Set to debug level
duvc.set_log_level(duvc.LogLevel.Debug)

# Operations now logged at debug level
devices = duvc.devices()
camera = duvc.CameraController(0)
```


***

#### get_log_level() - query current level

Query the currently configured minimum log level.

```python
def get_log_level() -> LogLevel:
    """Get current minimum log level."""
```

**Usage**:

```python
current = duvc.get_log_level()
print(f"Current level: {duvc.tostring(current)}")

# Check if debug enabled
if current == duvc.LogLevel.Debug:
    print("Debug logging active")
```


***

#### log_message() - emit log message

Emit message at specified level. Respects set_log_level() filter.

```python
def log_message(level: LogLevel, message: str) -> None:
    """Log message at specified level."""
```

**Usage**:

```python
duvc.log_message(duvc.LogLevel.Info, "Camera operation started")
duvc.log_message(duvc.LogLevel.Warning, "Device may be disconnecting")
```


***

#### log_debug/info/warning/error/critical() - convenience functions

Level-specific logging functions. Shorthand for common levels.

```python
def log_debug(message: str) -> None: ...
def log_info(message: str) -> None: ...
def log_warning(message: str) -> None: ...
def log_error(message: str) -> None: ...
def log_critical(message: str) -> None: ...
```

**Usage**:

```python
duvc.log_debug("Checking device connection")
duvc.log_info("Device enumeration complete")
duvc.log_warning("Brightness at maximum")
duvc.log_error("Failed to set property")
duvc.log_critical("Device disconnected unexpectedly")
```


***

#### set_log_callback() - custom message handler

Register callback to receive all log messages. Callback signature: `(level: LogLevel, message: str) -> None`.

```python
def set_log_callback(
    callback: Callable[[LogLevel, str], None]
) -> None:
    """Register callback for log messages."""
```

**Callback contract**:

- Called synchronously for each log message
- No exceptions should escape callback
- Called from library threads (may not be main thread)

**Usage**:

```python
import logging

# Direct to standard logging module
def logging_adapter(level: duvc.LogLevel, message: str):
    level_name = duvc.tostring(level)
    level_num = {
        "Debug": logging.DEBUG,
        "Info": logging.INFO,
        "Warning": logging.WARNING,
        "Error": logging.ERROR,
        "Critical": logging.CRITICAL,
    }.get(level_name, logging.INFO)
    logging.log(level_num, message)

duvc.set_log_callback(logging_adapter)

# Now all library logs go to Python logging
duvc.set_log_level(duvc.LogLevel.Debug)
camera = duvc.CameraController(0)  # Logs appear in logging output
```

**File logging**:

```python
log_file = open("duvc.log", "a")

def file_logger(level: duvc.LogLevel, message: str):
    level_name = duvc.tostring(level)
    log_file.write(f"[{level_name}] {message}\n")
    log_file.flush()

duvc.set_log_callback(file_logger)
```

**Thread-safe callback**:

```python
from threading import Lock

log_lock = Lock()
messages = []

def thread_safe_logger(level: duvc.LogLevel, message: str):
    with log_lock:
        messages.append((duvc.tostring(level), message))
    # Process outside lock to avoid blocking library threads

duvc.set_log_callback(thread_safe_logger)
```

### 9.2 Error Decoding \& Windows Diagnostics

Platform-level error interpretation and detailed Windows diagnostics. All functions in this section are **Windows-only**.

***

#### decode_system_error() - interpret system error codes

Decode system error code to human-readable message. Cross-references Windows error codes with common causes.

```python
def decode_system_error(error_code: int) -> str:
    """Decode system error code to message."""
```

**Usage**:

```python
import duvc_ctl as duvc

# When catching SystemError
try:
    camera = duvc.CameraController(0)
except duvc.SystemError as e:
    if e.error_code:
        decoded = duvc.decode_system_error(e.error_code)
        print(f"System error: {decoded}")
```


***

#### get_diagnostic_info() - comprehensive system analysis

Query detailed system state: device list, driver status, permissions, connection state.

```python
def get_diagnostic_info() -> dict[str, Any]:
    """
    Collect system diagnostic information.
    
    Returns:
        Dict with keys:
            - devices: List of cameras (name, path, connected)
            - driver_info: DirectShow driver status
            - os_info: Windows version
            - permissions: Current user camera permissions
            - errors: Any initialization errors
    """
```

**Usage**:

```python
import duvc_ctl as duvc
import json

# Capture full diagnostics
diag = duvc.get_diagnostic_info()
print(json.dumps(diag, indent=2))

# Output:
# {
#   "devices": [
#     {"name": "Logitech USB HD", "path": "...", "connected": true}
#   ],
#   "driver_info": {"status": "ok", "version": "..."},
#   "os_info": {"version": "Windows 10", "build": "19045"},
#   "permissions": {"camera_access": "granted"},
#   "errors": []
# }
```


***

#### decode_hresult() - HRESULT interpretation (Windows-only)

Decode Windows HRESULT value to error category and description.

```python
def decode_hresult(hr: int) -> str:
    """Decode HRESULT to human-readable message."""
```

**Usage**:

```python
import duvc_ctl as duvc

# HRESULT from DirectShow operation
hr = 0x80070005  # ACCESS_DENIED

decoded = duvc.decode_hresult(hr)
print(f"HRESULT 0x{hr:08X}: {decoded}")
# Output: "HRESULT 0x80070005: Access Denied"
```


***

#### get_hresult_details() - detailed HRESULT analysis (Windows-only)

Analyze HRESULT with recovery suggestions and common causes.

```python
def get_hresult_details(hr: int) -> dict[str, str]:
    """
    Analyze HRESULT with detailed information.
    
    Returns:
        Dict with:
            - code: Hex representation
            - facility: HRESULT facility code
            - message: Human-readable message
            - causes: List of common causes
            - suggestions: List of recovery steps
    """
```

**Usage**:

```python
import duvc_ctl as duvc

hr = 0x80004005  # E_FAIL

details = duvc.get_hresult_details(hr)
print(f"Code: {details['code']}")
print(f"Message: {details['message']}")
print(f"Common causes:")
for cause in details['causes']:
    print(f"  - {cause}")
print(f"Suggestions:")
for suggestion in details['suggestions']:
    print(f"  - {suggestion}")
```


***

#### is_device_error() - device-specific error detection (Windows-only)

Check if HRESULT or error code indicates device-level failure (not driver/system).

```python
def is_device_error(hr: int | error_code: int) -> bool:
    """Check if error is device-specific."""
```

**Usage**:

```python
import duvc_ctl as duvc

hr = 0x80070015  # DEVICE_NOT_READY

if duvc.is_device_error(hr):
    print("Device error - check physical connection")
else:
    print("System/driver error - reinstall or restart")
```


***

#### is_permission_error() - permission failure detection (Windows-only)

Check if HRESULT or error code indicates permission/access denied.

```python
def is_permission_error(hr: int | error_code: int) -> bool:
    """Check if error is permission-denied."""
```

**Usage**:

```python
import duvc_ctl as duvc

try:
    camera = duvc.CameraController(0)
except duvc.PermissionDeniedError as e:
    if hasattr(e, 'hresult'):
        if duvc.is_permission_error(e.hresult):
            print("Grant camera access in Settings")
```


***

#### Error message templates and patterns

Common Windows errors and their standard meanings:


| HRESULT | Facility | Meaning | Recovery |
| :-- | :-- | :-- | :-- |
| 0x80070005 | WIN32 | ACCESS_DENIED | Check privacy settings, run as admin |
| 0x80070002 | WIN32 | FILE_NOT_FOUND | Camera driver missing or corrupted |
| 0x80070015 | WIN32 | DEVICE_NOT_READY | Camera disconnected, reconnect USB |
| 0x8004DF00 | COM | Device creation failed | Device in use by other app |
| 0x80004005 | COM | E_FAIL (generic) | Check driver logs, try USB restart |

**Usage**:

```python
import duvc_ctl as duvc

try:
    camera = duvc.CameraController(0)
except Exception as e:
    if hasattr(e, 'error_code'):
        details = duvc.get_hresult_details(e.error_code)
        for suggestion in details['suggestions']:
            print(f"Try: {suggestion}")
```


***

#### Internal error recovery patterns

Library uses multi-level recovery when errors occur:

**Level 1: Retry with backoff**

- Transient errors (timeout, busy) → retry 2-3x with 100ms delay
- Connection drops → attempt reconnect

**Level 2: Query and adapt**

- Unsupported property → query capabilities, use alternative
- Out of range → query range, clamp value
- Permission denied → suggest user action

**Level 3: Escalate and fallback**

- Driver error → log, suggest driver reinstall
- System error → recommend restart
- Unrecoverable → fail gracefully

**Example recovery pattern**:

```python
import duvc_ctl as duvc
import time

def resilient_set_brightness(device, value, retries=3):
    """Set brightness with automatic recovery."""
    for attempt in range(retries):
        try:
            camera = duvc.CameraController(device)
            camera.set_brightness(value)
            return True
        except duvc.PropertyValueOutOfRangeError as e:
            # Level 1: Adapt value
            corrected = max(e.min_val, min(e.max_val, value))
            camera = duvc.CameraController(device)
            camera.set_brightness(corrected)
            return True
        except duvc.DeviceBusyError:
            # Level 2: Retry with backoff
            if attempt < retries - 1:
                time.sleep(0.1 * (2 ** attempt))
                continue
        except duvc.PermissionDeniedError:
            # Level 3: Escalate
            print("Camera access denied. Grant permission in Settings > Privacy")
            return False
        except duvc.SystemError as e:
            # Level 3: Diagnose
            details = duvc.get_hresult_details(e.error_code)
            print(f"System error: {details['message']}")
            for suggestion in details['suggestions']:
                print(f"  - {suggestion}")
            return False
    return False
```

### 9.3 Device Callbacks \& Hot-Plug

Event-driven device hot-plug detection with thread-safe callback registration.

***

#### register_device_change_callback() - watch for device changes

Register callback to receive notifications when cameras connect/disconnect. Callback runs in library thread pool.

```python
def register_device_change_callback(
    callback: Callable[[str, str], None]
) -> None:
    """
    Register callback for device connect/disconnect events.
    
    Args:
        callback: Function(event_type: str, device_name: str)
                  event_type: "connected" or "disconnected"
                  device_name: Name of changed device
    """
```

**Callback signature**:

- `event_type` (str): Either `"connected"` or `"disconnected"`
- `device_name` (str): Camera name that changed

**Usage**:

```python
import duvc_ctl as duvc

def on_device_change(event_type: str, device_name: str):
    print(f"{device_name}: {event_type}")

# Register callback
duvc.register_device_change_callback(on_device_change)

# Physical hot-plug events now trigger callback
# When user plugs in camera: "Logitech USB HD: connected"
# When user unplugs camera: "Logitech USB HD: disconnected"
```


***

#### unregister_device_change_callback() - stop watching

Unregister previously registered device change callback.

```python
def unregister_device_change_callback(
    callback: Callable[[str, str], None]
) -> None:
    """Unregister device change callback."""
```

**Usage**:

```python
import duvc_ctl as duvc

def on_device_change(event_type: str, device_name: str):
    print(f"{device_name}: {event_type}")

duvc.register_device_change_callback(on_device_change)

# Later: stop listening
duvc.unregister_device_change_callback(on_device_change)
```


***

#### GIL management in callbacks

Library automatically acquires Python GIL before calling callback. Safe to call Python APIs from callback. Callback must complete quickly.

**Callback execution context**:

- Called from C++ thread pool
- GIL held during callback execution
- Other Python threads may block waiting for GIL
- Exceptions in callback are logged, not propagated

**Quick callback requirement**: Keep callbacks under 10ms. Long operations may block device enumeration.

**Usage**:

```python
import duvc_ctl as duvc
from queue import Queue

# CORRECT: Queue event for processing elsewhere
event_queue = Queue()

def on_device_change(event_type: str, device_name: str):
    event_queue.put((event_type, device_name))

duvc.register_device_change_callback(on_device_change)

# Separate thread processes events
while True:
    event_type, device_name = event_queue.get()
    # Process event (may be slow)
    if event_type == "connected":
        print(f"Camera {device_name} connected")
```

**Incorrect: Long operations in callback**:

```python
import duvc_ctl as duvc
import time

def on_device_change(event_type: str, device_name: str):
    # WRONG: This blocks library threads
    time.sleep(5)  # Don't do this!
    print(f"{device_name}: {event_type}")

duvc.register_device_change_callback(on_device_change)
```


***

#### Threading patterns with callbacks

**Pattern 1: Queue-based event processing**

```python
import duvc_ctl as duvc
from queue import Queue
from threading import Thread

event_queue = Queue()

def on_device_change(event_type: str, device_name: str):
    event_queue.put((event_type, device_name))

def event_processor():
    while True:
        event_type, device_name = event_queue.get()
        if event_type == "connected":
            print(f"Handling new camera: {device_name}")
            # Long operations OK here
        elif event_type == "disconnected":
            print(f"Camera removed: {device_name}")

duvc.register_device_change_callback(on_device_change)
processor_thread = Thread(target=event_processor, daemon=True)
processor_thread.start()
```

**Pattern 2: Device pool with auto-recovery**

```python
import duvc_ctl as duvc
from threading import Lock

active_cameras = {}
camera_lock = Lock()

def on_device_change(event_type: str, device_name: str):
    if event_type == "connected":
        try:
            cam = duvc.CameraController(device_name)
            with camera_lock:
                active_cameras[device_name] = cam
            print(f"Auto-connected: {device_name}")
        except Exception as e:
            print(f"Failed to connect {device_name}: {e}")
    elif event_type == "disconnected":
        with camera_lock:
            if device_name in active_cameras:
                active_cameras[device_name].close()
                del active_cameras[device_name]
            print(f"Auto-closed: {device_name}")

duvc.register_device_change_callback(on_device_change)

# Cameras automatically managed as connected/disconnected
```

**Pattern 3: Listener pattern with state tracking**

```python
import duvc_ctl as duvc
from threading import Lock

class DeviceMonitor:
    def __init__(self):
        self.connected = set()
        self.lock = Lock()
        duvc.register_device_change_callback(self.on_change)
    
    def on_change(self, event_type: str, device_name: str):
        with self.lock:
            if event_type == "connected":
                self.connected.add(device_name)
            else:
                self.connected.discard(device_name)
    
    def get_active(self):
        with self.lock:
            return list(self.connected)
    
    def wait_for(self, device_name, timeout=5):
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            if device_name in self.get_active():
                return True
            time.sleep(0.1)
        return False

monitor = DeviceMonitor()

# Later: wait for specific camera
if monitor.wait_for("Logitech", timeout=10):
    print("Camera connected!")
```

**Pattern 4: Event listener with weak references** (Prevents memory leaks)

```python
import duvc_ctl as duvc
import weakref

class CameraListener:
    def __init__(self, name):
        self.name = name
        duvc.register_device_change_callback(self.on_change)
    
    def on_change(self, event_type: str, device_name: str):
        print(f"{self.name}: {device_name} {event_type}")
    
    def cleanup(self):
        duvc.unregister_device_change_callback(self.on_change)

listener = CameraListener("MyApp")

# Later: clean up properly
listener.cleanup()
del listener
```

