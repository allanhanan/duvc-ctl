## 10. Vendor-Specific Extensions


### 10.1 Logitech Extensions

Logitech-specific camera properties and control functions for PTZ, LED, and audio features. Available on supported Logitech camera models (C922, C930, C925, etc.).

***

#### LogitechProperty enum

10 vendor properties specific to Logitech cameras. Integer enum values mapped to hardware controls.

**Properties**:


| Property | Value | Purpose |
| :-- | :-- | :-- |
| `LED_Mode` | 0 | LED indicator on/off/auto |
| `Brightness_Enhancement` | 1 | Automatic brightness adjustment |
| `Face_Detection` | 2 | Enable/disable face detection |
| `Low_Light_Compensation` | 3 | Low-light mode |
| `Automatic_Exposure` | 4 | Auto-exposure control |
| `Automatic_Whitebalance` | 5 | Auto white balance control |
| `Automatic_Lowlight_Compensation` | 6 | Auto low-light adjustment |
| `Pan_Speed` | 7 | PTZ pan movement speed |
| `Tilt_Speed` | 8 | PTZ tilt movement speed |
| `Zoom_Speed` | 9 | PTZ zoom movement speed |

**Usage**:

```python
import duvc_ctl as duvc

device = duvc.devices()[^0]
result = duvc.get_logitech_property(device, duvc.LogitechProperty.LED_Mode)
if result.is_ok():
    print(f"LED Mode: {result.value()}")
```


***

#### get_logitech_property() - read Logitech property

Get Logitech-specific property value. Returns Result type with error on unsupported models.

```python
def get_logitech_property(
    device: Device,
    prop: LogitechProperty
) -> Okuint32 | Erruint32:
    """
    Get Logitech property value.
    
    Returns:
        Okuint32 with value, or Erruint32 if unsupported/failed
    """
```

**Usage**:

```python
import duvc_ctl as duvc

device = duvc.devices()[^0]

# Read LED mode
result = duvc.get_logitech_property(device, duvc.LogitechProperty.LED_Mode)
if result.is_ok():
    print(f"LED: {result.value()}")
else:
    print(f"Error: {result.error().description()}")
```


***

#### set_logitech_property() - write Logitech property

Set Logitech-specific property value. Range varies by property.

```python
def set_logitech_property(
    device: Device,
    prop: LogitechProperty,
    value: int
) -> Okvoid | Errvoid:
    """
    Set Logitech property value.
    
    Returns:
        Okvoid on success, Errvoid on error
    """
```

**Usage**:

```python
import duvc_ctl as duvc

device = duvc.devices()[^0]

# Set LED to auto (value = 2)
result = duvc.set_logitech_property(
    device,
    duvc.LogitechProperty.LED_Mode,
    2
)
if result.is_ok():
    print("LED set to auto")
else:
    print(f"Failed: {result.error().description()}")

# Set pan speed (0-100)
duvc.set_logitech_property(device, duvc.LogitechProperty.Pan_Speed, 75)
```


***

#### supports_logitech_properties() - capability check

Query if device supports Logitech extensions. Some models lack vendor features.

```python
def supports_logitech_properties(device: Device) -> bool:
    """Check if device supports Logitech extensions."""
```

**Usage**:

```python
import duvc_ctl as duvc

device = duvc.devices()[^0]

if duvc.supports_logitech_properties(device):
    print(f"{device.name} supports Logitech extensions")
    
    # Safe to use Logitech-specific functions
    result = duvc.get_logitech_property(
        device,
        duvc.LogitechProperty.LED_Mode
    )
else:
    print(f"{device.name} does not support Logitech extensions")
```

**Capability detection**:

```python
import duvc_ctl as duvc

for device in duvc.devices():
    has_logitech = duvc.supports_logitech_properties(device)
    marker = "✓" if has_logitech else "✗"
    print(f"{marker} {device.name}")
```

### 10.2 GUID \& Vendor Properties

Low-level GUID handling for Windows COM interfaces and generic vendor property access. **All GUID functions are Windows-only.**

***

#### GUID wrapper type (Windows-only)

GUID object encapsulates Windows GUID structure. Immutable wrapper for interface identification and vendor-specific control.

```python
class GUID:
    """Windows GUID wrapper (128-bit UUID)."""
    def __str__(self) -> str: ...
    def __bytes__(self) -> bytes: ...
```


***

#### guid_from_uuid() - UUID to GUID conversion (Windows-only)

Convert Python UUID to Windows GUID format.

```python
def guid_from_uuid(uuid_obj: uuid.UUID) -> GUID:
    """Convert Python UUID to GUID."""
```

**Usage**:

```python
import duvc_ctl as duvc
import uuid

standard_uuid = uuid.UUID("6994ad05-93f7-406d-611d-4222d440c8a0")
guid = duvc.guid_from_uuid(standard_uuid)
print(guid)
```


***

#### guid_from_pyobj() - flexible GUID creation (Windows-only)

Create GUID from string, bytes, or UUID object.

```python
def guid_from_pyobj(obj: str | bytes | uuid.UUID) -> GUID:
    """Create GUID from string, bytes, or UUID."""
```

**String formats**:

- `{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}` (with braces)
- `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX` (no braces)
- `XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` (hex only)

**Usage**:

```python
import duvc_ctl as duvc

# From string
guid1 = duvc.guid_from_pyobj("{6994ad05-93f7-406d-611d-4222d440c8a0}")

# From bytes (16 bytes, little-endian GUID)
guid2 = duvc.guid_from_pyobj(b'\x05\xad\x94\x69\xf7\x93\x6d\x40...')

# From UUID
import uuid
guid3 = duvc.guid_from_pyobj(uuid.UUID("6994ad05-93f7-406d-611d-4222d440c8a0"))
```


***

#### VendorProperty type

Structured vendor property descriptor with metadata. Contains GUID, property ID, and access mode.

```python
class VendorProperty:
    """Vendor-specific property descriptor."""
    vendor_guid: GUID
    property_id: int
    access_mode: str  # "read", "write", "read_write"
    data_type: str    # "int", "bytes", "string"
```


***

#### DeviceConnection type

Device connection context for vendor property operations. Wraps open camera handle.

```python
class DeviceConnection:
    """Device connection for vendor operations."""
    device: Device
    is_open: bool
    error: str | None
```


***

#### read_vendor_property() - get vendor property (Windows-only)

Read vendor-specific property using GUID and property ID.

```python
def read_vendor_property(
    device: Device,
    vendor_guid: GUID,
    property_id: int,
    data_type: str = "int"
) -> Result[bytes | int]:
    """Read vendor property."""
```

**Data types**: `"int"` → int, `"bytes"` → bytes, `"string"` → str

**Usage**:

```python
import duvc_ctl as duvc

device = duvc.devices()[0]
guid = duvc.guid_from_pyobj("{6994ad05-93f7-406d-611d-4222d440c8a0}")

result = duvc.read_vendor_property(device, guid, prop_id=0, data_type="int")
if result.is_ok():
    value = result.value()
    print(f"Property value: {value}")
else:
    print(f"Error: {result.error().description()}")
```


***

#### write_vendor_property() - set vendor property (Windows-only)

Write vendor-specific property value.

```python
def write_vendor_property(
    device: Device,
    vendor_guid: GUID,
    property_id: int,
    value: bytes | int | str,
    data_type: str = "int"
) -> Result[None]:
    """Write vendor property."""
```

**Usage**:

```python
import duvc_ctl as duvc

device = duvc.devices()[0]
guid = duvc.guid_from_pyobj("{6994ad05-93f7-406d-611d-4222d440c8a0}")

result = duvc.write_vendor_property(
    device, guid, prop_id=0, value=100, data_type="int"
)
if result.is_ok():
    print("Property set successfully")
else:
    print(f"Error: {result.error().description()}")
```


***

#### get_vendor_property() - wrapper with error handling

High-level wrapper for `read_vendor_property()`. Raises exception on error.

```python
def get_vendor_property(
    device: Device,
    vendor_guid: GUID,
    property_id: int,
    data_type: str = "int"
) -> bytes | int | str:
    """Read vendor property (exception on error)."""
```

**Usage**:

```python
import duvc_ctl as duvc

device = duvc.devices()[0]
guid = duvc.guid_from_pyobj("{6994ad05-93f7-406d-611d-4222d440c8a0}")

try:
    value = duvc.get_vendor_property(device, guid, 0, "int")
    print(f"Property: {value}")
except duvc.DuvcError as e:
    print(f"Error: {e}")
```


***

#### set_vendor_property() - wrapper with error handling

High-level wrapper for `write_vendor_property()`. Raises exception on error.

```python
def set_vendor_property(
    device: Device,
    vendor_guid: GUID,
    property_id: int,
    value: bytes | int | str,
    data_type: str = "int"
) -> None:
    """Write vendor property (exception on error)."""
```

**Usage**:

```python
import duvc_ctl as duvc

device = duvc.devices()[0]
guid = duvc.guid_from_pyobj("{6994ad05-93f7-406d-611d-4222d440c8a0}")

try:
    duvc.set_vendor_property(device, guid, 0, 100, "int")
    print("Property set")
except duvc.DuvcError as e:
    print(f"Error: {e}")
```

### 10.3 Abstract Interfaces for Extension

Plugin-style extensibility through abstract interface implementation. Python subclasses can override C++ interface methods using pybind11 trampolines.

***

#### IPlatformInterface abstract (Windows-only)

Abstract base for platform-specific operations. Defines hooks for device enumeration, property access, and system queries. Not used directly; subclass via Python or use built-in implementation.

```python
class IPlatformInterface:
    """Platform implementation contract."""
    def enumerate_devices(self) -> list[Device]: ...
    def query_device_capabilities(self, device: Device) -> DeviceCapabilities: ...
    def get_property(self, device: Device, prop_id: int) -> int: ...
    def set_property(self, device: Device, prop_id: int, value: int) -> bool: ...
```


***

#### IDeviceConnection abstract (Windows-only)

Abstract connection context for vendor operations. Manages device lifecycle and low-level I/O. Override for custom transport layers or simulation.

```python
class IDeviceConnection:
    """Device connection contract."""
    def open(self, device: Device) -> bool: ...
    def close(self) -> None: ...
    def is_connected(self) -> bool: ...
    def read_property(self, prop_id: int) -> bytes: ...
    def write_property(self, prop_id: int, data: bytes) -> bool: ...
```


***

#### PyIPlatformInterface - Python subclassing trampoline

Pybind11 trampoline enabling Python classes to override interface methods. Automatic GIL management for C++→Python calls.

**Usage**:

```python
import duvc_ctl as duvc

class CustomPlatform(duvc.IPlatformInterface):
    def enumerate_devices(self):
        print("Custom enumeration")
        devices = []
        # Custom device discovery logic
        return devices
    
    def query_device_capabilities(self, device):
        # Custom capability query
        return duvc.DeviceCapabilities()
    
    def get_property(self, device, prop_id):
        # Custom property read
        return 0
    
    def set_property(self, device, prop_id, value):
        # Custom property write
        return True

# Register with library
platform = CustomPlatform()
duvc.create_platform_interface(platform)
```


***

#### PyIDeviceConnection - Python subclassing trampoline

Trampoline for device connection override. Custom implementations handle non-standard transports or mock devices.

**Usage**:

```python
import duvc_ctl as duvc

class MockConnection(duvc.IDeviceConnection):
    def open(self, device):
        print(f"Mock open: {device.name}")
        return True
    
    def close(self):
        print("Mock close")
    
    def is_connected(self):
        return True
    
    def read_property(self, prop_id):
        # Return mock data
        return b'\x00\x01\x02\x03'
    
    def write_property(self, prop_id, data):
        print(f"Mock write: {len(data)} bytes")
        return True

conn = MockConnection()
# Pass to device operations
```


***

#### PYBIND11_OVERRIDE_PURE macro pattern

Macros used internally to forward Python method calls to C++. Not directly called by users, but understanding helps with debugging.

**Invocation** (internal):

```cpp
// C++ side (pybind11 binding code)
class PyIPlatformInterface : public IPlatformInterface {
    std::vector<Device> enumerate_devices() override {
        PYBIND11_OVERRIDE_PURE(
            std::vector<Device>,
            IPlatformInterface,
            enumerate_devices
        );
    }
};
```

When Python calls `enumerate_devices()`, pybind11 routes it through this macro, acquiring GIL and calling the Python implementation.

***

#### create_platform_interface() - factory registration

Register custom platform implementation. Library uses it for all subsequent operations.

```python
def create_platform_interface(impl: IPlatformInterface) -> None:
    """Register custom platform implementation."""
```

**Usage**:

```python
import duvc_ctl as duvc

class CustomPlatform(duvc.IPlatformInterface):
    # ... implementation ...
    pass

duvc.create_platform_interface(CustomPlatform())

# All library operations now use custom implementation
devices = duvc.devices()  # Uses CustomPlatform.enumerate_devices()
```


***

#### Python custom implementation patterns

**Pattern 1: Simulation/Testing**

```python
import duvc_ctl as duvc

class SimulatedPlatform(duvc.IPlatformInterface):
    def __init__(self):
        self.device_list = []
    
    def enumerate_devices(self):
        # Return mock devices
        return self.device_list
    
    def query_device_capabilities(self, device):
        caps = duvc.DeviceCapabilities()
        caps.supported_camera_properties = [duvc.CamProp.Pan, duvc.CamProp.Tilt]
        return caps
    
    def get_property(self, device, prop_id):
        return 50  # Mock value
    
    def set_property(self, device, prop_id, value):
        return True  # Always succeed

# Use simulated environment
duvc.create_platform_interface(SimulatedPlatform())
```

**Pattern 2: Logging/Debugging wrapper**

```python
import duvc_ctl as duvc

class LoggingPlatform(duvc.IPlatformInterface):
    def __init__(self, real_impl):
        self.real = real_impl
    
    def enumerate_devices(self):
        print("TRACE: enumerate_devices called")
        result = self.real.enumerate_devices()
        print(f"TRACE: found {len(result)} devices")
        return result
    
    def get_property(self, device, prop_id):
        print(f"TRACE: get_property device={device.name} prop={prop_id}")
        value = self.real.get_property(device, prop_id)
        print(f"TRACE: result={value}")
        return value
    
    def set_property(self, device, prop_id, value):
        print(f"TRACE: set_property device={device.name} prop={prop_id} value={value}")
        success = self.real.set_property(device, prop_id, value)
        print(f"TRACE: success={success}")
        return success
```

**Pattern 3: Custom device transport**

```python
import duvc_ctl as duvc

class NetworkConnection(duvc.IDeviceConnection):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
    
    def open(self, device):
        # Connect to remote device
        import socket
        self.socket = socket.socket()
        self.socket.connect((self.host, self.port))
        return True
    
    def is_connected(self):
        return self.socket is not None
    
    def read_property(self, prop_id):
        # Send read request over network
        self.socket.send(f"READ {prop_id}".encode())
        return self.socket.recv(256)
    
    def write_property(self, prop_id, data):
        # Send write request over network
        self.socket.send(f"WRITE {prop_id} {len(data)}".encode())
        self.socket.send(data)
        return True
    
    def close(self):
        if self.socket:
            self.socket.close()
```

**Important Notes**:

- Custom implementations must implement all abstract methods
- GIL is held during Python method calls; avoid blocking
- Exceptions in Python methods are converted to C++ exceptions
- Return types must match interface contract exactly

