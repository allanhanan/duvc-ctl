## 7. Exception Hierarchy & Handling


### 7.1 Exception Base & Device Errors

Base exception and specific device error subclasses. The Pythonic API raises these automatically; Result-based API returns error codes instead.

#### DuvcError - base exception with error context

All exceptions inherit from `DuvcError`. Provides unified error handling, error codes, and contextual information for debugging.

**Attributes**:
- `error_code` (DuvcErrorCode or None): Integer error code mapping to specific conditions.
- `context` (str or None): Additional context information describing where/why error occurred.

**Methods**:
- `__str__()`: Returns formatted string with error code name, message, and context.

**DuvcErrorCode IntEnum (0-8)**:

| Code | Name | Value | Meaning |
|------|------|-------|---------|
| Success | `DuvcErrorCode.SUCCESS` | 0 | Operation succeeded |
| DeviceNotFound | `DuvcErrorCode.DEVICE_NOT_FOUND` | 1 | Device not found or disconnected |
| DeviceBusy | `DuvcErrorCode.DEVICE_BUSY` | 2 | Device busy or in use |
| PropertyNotSupported | `DuvcErrorCode.PROPERTY_NOT_SUPPORTED` | 3 | Property not supported by device |
| InvalidValue | `DuvcErrorCode.INVALID_VALUE` | 4 | Property value out of range |
| PermissionDenied | `DuvcErrorCode.PERMISSION_DENIED` | 5 | Insufficient permissions |
| SystemError | `DuvcErrorCode.SYSTEM_ERROR` | 6 | System or platform error |
| InvalidArgument | `DuvcErrorCode.INVALID_ARGUMENT` | 7 | Invalid function argument |
| NotImplemented | `DuvcErrorCode.NOT_IMPLEMENTED` | 8 | Feature not implemented |

**Usage**:

```python
try:
    camera = duvc.CameraController(0)
except duvc.DuvcError as e:
    print(f"Error: {e}")
    print(f"Code: {e.error_code}")
    print(f"Context: {e.context}")
```


***

#### DeviceNotFoundError - device not accessible

Raised when device not found, disconnected, or not recognized by system. Device may have been physically disconnected or is not enumerable.

**Typical causes**: Device unplugged, driver issues, hardware failure, USB hub power-off.

**Recovery**: Reconnect device, check Device Manager, reinstall drivers.

```python
try:
    camera = duvc.CameraController(0)
except duvc.DeviceNotFoundError as e:
    print(f"Device not found: {e}")
    devices = duvc.list_devices()
    print(f"Available devices: {len(devices)}")
    for dev in devices:
        print(f"  - {dev.name}")
```


***

#### DeviceBusyError - device locked by another process

Raised when device is already open in another application or thread. Exclusive access prevents concurrent opens (DirectShow limitation).

**Typical causes**: Camera open in another app, another thread holding camera, previous open not properly closed.

**Recovery**: Close other apps using camera, ensure all camera objects are released.

```python
try:
    camera = duvc.CameraController(0)
except duvc.DeviceBusyError as e:
    print(f"Camera in use: {e}")
    print("Close other applications and retry")
```


***

#### PropertyNotSupportedError - property unavailable on device

Raised when querying/setting a property that device doesn't support. Not all cameras support all UVC properties.

**Typical causes**: Camera model limitation, firmware restriction, driver doesn't expose property.

**Recovery**: Query capabilities first, use different property, check camera specs.

```python
try:
    camera = duvc.CameraController(0)
    camera.set_brightness(150)  # May not exist on all cameras
except duvc.PropertyNotSupportedError as e:
    print(f"Property not available: {e}")
    caps = camera.get_capabilities()
    print(f"Supported video properties: {caps.video_properties}")
```


***

#### InvalidValueError - property value outside valid range

Raised when attempting to set property to value outside [min, max] bounds or with invalid type.

**Typical causes**: Value out of range, step size mismatch, type error.

**Recovery**: Query range first, clamp value to bounds, use correct type.

```python
try:
    camera = duvc.CameraController(0)
    camera.set_brightness(500)  # Typical range 0-255
except duvc.InvalidValueError as e:
    print(f"Invalid value: {e}")
    caps = camera.get_capabilities()
    bright_range = caps.video_properties['Brightness']['range']
    print(f"Valid range: {bright_range['min']}-{bright_range['max']}")
```


***

#### PermissionDeniedError - insufficient access permissions

Raised when lacking required permissions to access device. Can occur if privacy settings block camera or insufficient OS privileges.

**Typical causes**: Privacy mode enabled, app not granted camera permission, insufficient privileges.

**Recovery**: Grant permissions, disable privacy mode, run elevated.

```python
try:
    camera = duvc.CameraController(0)
except duvc.PermissionDeniedError as e:
    print(f"Permission denied: {e}")
    print("Check privacy settings or run with administrator privileges")
```

### 7.2 Property \& Value Errors

Specialized exception classes for property-specific failures. These provide detailed diagnostic attributes and recovery guidance for common usage errors.

***

#### PropertyValueOutOfRangeError - comprehensive range validation

Detailed `InvalidValueError` subclass for out-of-range property values. Captures and reports complete range information with suggested corrections.

**Attributes**:

- `property_name` (str): Property name (e.g., "Brightness").
- `value` (int): The attempted value that was rejected.
- `min_val` (int): Minimum valid value for this property on this device.
- `max_val` (int): Maximum valid value for this property on this device.
- `current_val` (int or None): Current property value before failed attempt. Helps understand what changed.
- `step` (int or None): Step size between valid values. Important for alignment.

**Exception message format**: Includes clamped suggestion automatically.

```
"Value 500 is out of range for 'Brightness'. Valid range: 0 to 255 
(step: 1). Current value: 128. Try: 255"
```

**Usage**:

```python
try:
    camera.set_brightness(500)  # Range typically 0-255
except duvc.PropertyValueOutOfRangeError as e:
    print(f"Error: {e}")
    print(f"  Property: {e.property_name}")
    print(f"  Attempted: {e.value}")
    print(f"  Valid range: {e.min_val}-{e.max_val}")
    print(f"  Step size: {e.step}")
    if e.current_val is not None:
        print(f"  Current: {e.current_val}")
    
    # Automatic recovery: clamp to valid range
    corrected = max(e.min_val, min(e.max_val, e.value))
    camera.set_brightness(corrected)
    print(f"  Retried with: {corrected}")
```

**Recovery algorithm**: Exception message automatically suggests clamping target (`Try: X`). Apply this value directly without re-querying range.

***

#### PropertyModeNotSupportedError - mode compatibility checking

Distinguishes mode failures from property unavailability. Raised when property exists but requested mode (auto/manual/continuous) isn't supported.

**Attributes**:

- `property_name` (str): Property name (e.g., "Pan").
- `mode` (str): Mode requested ("auto", "manual", or "continuous").
- `supported_modes` (list[str]): List of actually supported modes on this device. Empty if information unavailable.

**Usage**:

```python
try:
    camera.set_property_auto(duvc.CamProp.Pan)  # Pan typically manual-only
except duvc.PropertyModeNotSupportedError as e:
    print(f"Mode error: {e}")
    print(f"  Property: {e.property_name}")
    print(f"  Requested mode: {e.mode}")
    if e.supported_modes:
        print(f"  Supported modes: {e.supported_modes}")
        
        # Fallback to supported mode
        fallback = e.supported_modes[^0] if e.supported_modes else 'manual'
        if fallback == 'manual':
            camera.set_property_manual(duvc.CamProp.Pan, 0)
    else:
        # Mode information not available, try manual fallback
        camera.set_property_manual(duvc.CamProp.Pan, 0)
```

**Difference from PropertyNotSupportedError**: PropertyNotSupportedError = property doesn't exist. PropertyModeNotSupportedError = property exists but mode unavailable.

***

#### InvalidValueError - generic value validation failure

Base class for all value validation errors not covered by specific subclasses. Type errors, null values, invalid enum constants.

**Typical causes**: Wrong type passed (string instead of int), null/None value, invalid enum constant.

**Recovery**:

```python
try:
    camera.set(duvc.VidProp.Brightness, "bright")  # Type error
except duvc.InvalidValueError as e:
    print(f"Invalid value: {e}")
    # Verify type: must be int or PropSetting
    camera.set(duvc.VidProp.Brightness, 128)  # Correct: int
```


***

#### InvalidArgumentError - function argument validation

Raised when function receives structurally invalid argument. Catches programming errors before reaching hardware.

**Typical causes**: Null device pointer, invalid enum passed, malformed PropSetting structure.

**Recovery**:

```python
try:
    camera.set(None, duvc.PropSetting(100))  # Invalid property enum
except duvc.InvalidArgumentError as e:
    print(f"Bad argument: {e}")
    print(f"Error code: {e.error_code}")
    # Use valid enum constant
    camera.set(duvc.VidProp.Brightness, duvc.PropSetting(100))
```


***

#### BulkOperationError - batch operation diagnostics

Raised when bulk operations (e.g., setting multiple properties) partially succeed. Contains per-property failure details.

**Attributes**:

- `operation` (str): Operation name (e.g., "set_properties").
- `failed_properties` (dict): Mapping of property names to error messages.
- `successful_count` (int): Number of properties successfully modified.
- `total_count` (int): Total properties attempted.

**Methods**:

- `get_recovery_suggestions() -> list[str]`: Analyzes failures and suggests recovery actions.

**Usage**:

```python
props_to_set = {
    'Brightness': 150,
    'Contrast': 80,
    'Pan': 45,  # May fail if unsupported
}

try:
    camera.bulk_set_properties(props_to_set)
except duvc.BulkOperationError as e:
    print(f"Bulk operation failed: {e}")
    print(f"Succeeded: {e.successful_count}/{e.total_count}")
    print(f"Failed properties: {e.failed_properties}")
    
    # Get smart recovery suggestions
    for suggestion in e.get_recovery_suggestions():
        print(f"  → {suggestion}")
    
    # Retry failed properties individually
    for prop, error_msg in e.failed_properties.items():
        try:
            camera.set_single_property(prop, props_to_set[prop])
        except duvc.PropertyNotSupportedError:
            print(f"Skipping unsupported property: {prop}")
```

**Recovery suggestions algorithm**:

- "not supported" error → Suggests `get_capabilities()` query
- "out of range" error → Suggests `get_property_range()` query
- "busy" error → Suggests closing other apps
- No specific pattern → Suggests individual retry

***

#### ConnectionHealthError - connection diagnostics

Raised when connection health checks fail. Provides diagnostics and recovery patterns.

**Attributes**:

- `device_name` (str): Camera device name.
- `health_issues` (list[str]): List of detected issues (timeout, property locked, etc.).
- `last_working_operation` (str or None): Last successful operation, helps narrow troubleshooting scope.

**Methods**:

- `get_recovery_suggestions() -> list[str]`: Context-aware recovery steps.

**Usage**:

```python
try:
    # Operations fail due to connection issues
    camera.health_check()
except duvc.ConnectionHealthError as e:
    print(f"Connection health check failed: {e}")
    print(f"Device: {e.device_name}")
    print(f"Issues: {', '.join(e.health_issues)}")
    if e.last_working_operation:
        print(f"Last working operation: {e.last_working_operation}")
    
    # Get recovery suggestions based on failure pattern
    for suggestion in e.get_recovery_suggestions():
        print(f"  → {suggestion}")
    
    # Recovery: try reconnection
    try:
        camera.reconnect()
    except Exception:
        # Fallback: restart from scratch
        camera = duvc.CameraController(device_index)
```

**Recovery suggestions algorithm**:

- "timeout" issue → Suggests reconnect
- "property locked" issue → Suggests reset_to_defaults()
- "no response" issue → Suggests check for concurrent access
- Fallback → Suggests cam.reconnect() or application restart

***

#### Exception recovery suggestion algorithms

The library intelligently analyzes failure patterns and suggests targeted fixes:

**PropertyValueOutOfRangeError recovery**:

1. Extract suggested value from exception message
2. Clamp user input to [min, max]
3. Respect step size when adjusting
4. Retry with clamped value

**PropertyModeNotSupportedError recovery**:

1. Check supported_modes list
2. Fall back to first supported mode
3. If no list, try "manual" as universal fallback
4. If still failing, property may be truly unsupported

**BulkOperationError recovery**:

1. Analyze failure messages for patterns
2. Group by failure type (unsupported vs. out-of-range vs. busy)
3. Suggest property-specific diagnostics
4. Recommend individual retry if batch failed

**ConnectionHealthError recovery**:

1. Classify issue type (timeout vs. lock vs. communication)
2. Match to appropriate action (reconnect vs. reset vs. check access)
3. Provide last-working context to narrow scope
4. Escalate to full restart if basic recovery fails

### 7.3 System \& Advanced Exceptions

Platform-level exceptions for system integration, connection management, and batch operations. These handle non-property-specific failures and advanced recovery patterns.

***

#### PermissionDeniedError - access control failures

Raised when lacking OS-level permissions to access device. Privacy settings, restricted mode, or insufficient user privileges.

**Typical causes**: Privacy mode enabled, camera permission denied by OS, running without admin rights, restricted user account.

**Recovery**: Grant app camera permission in privacy settings, run elevated, check user group membership.

```python
try:
    camera = duvc.CameraController(0)
except duvc.PermissionDeniedError as e:
    print(f"Permission denied: {e}")
    print("Grant camera access in Settings > Privacy > Camera")
```


***

#### SystemError - platform/driver failures

Raised for unrecoverable system-level errors. Hardware issues, driver crashes, kernel failures, device firmware errors.

**Typical causes**: Driver bug, corrupt firmware, hardware malfunction, kernel memory access failure, USB port issue.

**Recovery**: Reinstall drivers, restart machine, update firmware, test with different USB port.

```python
try:
    result = camera.get_brightness()
except duvc.SystemError as e:
    print(f"System error: {e}")
    print(f"Code: {e.error_code}")
    print("Try restarting or reinstalling camera drivers")
```


***

#### NotImplementedError - unsupported operations

Raised when operation exists in API but isn't implemented for target camera/platform. Different from PropertyNotSupportedError (property doesn't exist vs. operation unavailable).

**Typical causes**: Feature only available on newer firmware, platform limitation, camera model doesn't support operation.

**Recovery**: Update camera firmware, use alternative method, check camera specs.

```python
try:
    camera.advanced_tracking()
except duvc.NotImplementedError as e:
    print(f"Not implemented: {e}")
    print("This camera may not support advanced tracking")
```


***

#### BulkOperationError - batch operation diagnostics

Raised when setting/getting multiple properties fails partially. Provides detailed failure analysis and per-property error information.

**Attributes**:

- `operation` (str): Operation name (e.g., "set_properties_batch").
- `failed_properties` (dict[str, str]): Maps property names to error messages.
- `successful_count` (int): Number of properties that succeeded.
- `total_count` (int): Total properties attempted.

**Methods**:

- `get_recovery_suggestions() -> list[str]`: Analyzes failure patterns and suggests fixes.

**Usage**:

```python
props_to_set = {
    'brightness': 100,
    'contrast': 80,
    'pan': 45,  # May fail
    'focus': 'auto'
}

try:
    result = camera.bulk_set_properties(props_to_set)
except duvc.BulkOperationError as e:
    print(f"Bulk set failed: {e.operation}")
    print(f"Success: {e.successful_count}/{e.total_count}")
    
    # Analyze failures by type
    for prop_name, error_msg in e.failed_properties.items():
        print(f"  {prop_name}: {error_msg}")
    
    # Get intelligent recovery suggestions
    for suggestion in e.get_recovery_suggestions():
        print(f"  → {suggestion}")
    
    # Retry failures individually
    for prop, value in props_to_set.items():
        if prop in e.failed_properties:
            try:
                camera.set(prop, value)
            except duvc.PropertyNotSupportedError:
                print(f"Skipping unsupported: {prop}")
```

**Recovery suggestion algorithm**:

- "not supported" errors → Group by property, suggest `get_supported_properties()` query
- "out of range" errors → Group by property, suggest `get_property_range()` query
- "busy" errors → Suggest close other apps using camera
- Connection errors → Suggest reconnection or driver restart
- Mixed errors → Suggest individual retry with detailed error handling

***

#### ConnectionHealthError - connection status diagnostics

Advanced exception for connection degradation and health monitoring. Indicates connection is functional but experiencing issues.

**Attributes**:

- `device_name` (str): Camera device name.
- `health_issues` (list[str]): List of detected problems (timeout, latency, property locked, etc.).
- `last_working_operation` (str or None): Last operation that succeeded, helps narrow scope.

**Methods**:

- `get_recovery_suggestions() -> list[str]`: Context-aware recovery steps based on issue pattern.

**Usage**:

```python
try:
    camera.health_check()
except duvc.ConnectionHealthError as e:
    print(f"Connection degraded: {e.device_name}")
    print(f"Issues: {', '.join(e.health_issues)}")
    
    if e.last_working_operation:
        print(f"Last working: {e.last_working_operation}")
    
    # Get specific recovery actions
    for suggestion in e.get_recovery_suggestions():
        print(f"  → {suggestion}")
    
    # Recovery pattern: reconnect
    try:
        camera.reconnect()
    except Exception:
        # Fallback: full restart
        camera.close()
        camera = duvc.CameraController(0)
```


***

#### Recovery patterns for system exceptions

**Timeout/Latency pattern**:

1. Check device still enumerated: `list_devices()`
2. Test basic operation: `get_brightness()`
3. If no response: attempt `reconnect()`
4. If still failing: restart application

**Hardware/Driver pattern**:

1. Check Device Manager for errors
2. Reinstall drivers
3. Restart system
4. Try different USB port
5. Test with USB analyzer if available

**Permission pattern**:

1. Check privacy settings (OS level)
2. Grant app camera permission
3. Run as administrator if needed
4. Check user group membership on Windows

**Connection loss pattern**:

1. Verify device still connected physically
2. Check device still in Device Manager
3. Attempt `reconnect()`
4. If persistent: power-cycle device
5. If still failing: unplug, wait 10s, reconnect

**Batch operation pattern**:

1. Identify failure types (unsupported vs. out-of-range vs. permission)
2. Query capabilities for unsupported properties
3. Query ranges for out-of-range values
4. Retry individual properties with corrected values
5. Log permanently failed properties for future skipping

### 7.4 Exception Mapping \& Recovery

Error codes map to specific exception classes through a factory function. Applications catch exceptions at varying specificity levels depending on recovery requirements.

***

#### ERROR_CODE_TO_EXCEPTION mapping

Complete bidirectional mapping between error codes and exception classes:


| Error Code | Enum Name | Exception Class | Attributes |
| :-- | :-- | :-- | :-- |
| 0 | SUCCESS | (no exception) | Operation succeeded |
| 1 | DEVICE_NOT_FOUND | `DeviceNotFoundError` | Device disconnected/unavailable |
| 2 | DEVICE_BUSY | `DeviceBusyError` | Device locked by another process |
| 3 | PROPERTY_NOT_SUPPORTED | `PropertyNotSupportedError` | Property unavailable on device |
| 4 | INVALID_VALUE | `InvalidValueError` / `PropertyValueOutOfRangeError` | Value invalid/out of range |
| 5 | PERMISSION_DENIED | `PermissionDeniedError` | Insufficient OS permissions |
| 6 | SYSTEM_ERROR | `SystemError` | Platform/driver failure |
| 7 | INVALID_ARGUMENT | `InvalidArgumentError` | Function argument invalid |
| 8 | NOT_IMPLEMENTED | `NotImplementedError` | Operation not implemented |


***

#### create_exception_from_error_code() factory function

Internal factory that maps error codes to exception instances. Used automatically by Result types when converting failures to exceptions.

**Signature**:

```python
def create_exception_from_error_code(
    code: int,
    message: str,
    context: str = None
) -> DuvcError:
    """Create appropriate exception from error code."""
```

**Usage (internal; automatic in Pythonic API)**:

```python
# Result-based API (explicit code handling)
result = camera.get(duvc.VidProp.Brightness)
if result.is_error():
    code = result.error().code()
    message = result.error().description()
    # Convert to exception if needed
    exc = duvc._create_exception_from_error_code(code, message)
    raise exc

# Pythonic API (automatic exception raising)
try:
    brightness = camera.brightness  # Raises exception on error
except duvc.PropertyNotSupportedError:
    print("Brightness not available")
```


***

#### Exception patterns with try-except

**Pattern 1: Broad error handling**

```python
try:
    camera = duvc.CameraController(0)
    camera.set_brightness(150)
except duvc.DuvcError as e:
    print(f"Camera error: {e}")
    print(f"Error code: {e.error_code}")
    print(f"Context: {e.context}")
```

**Pattern 2: Specific exception catching**

```python
try:
    camera.set_brightness(150)
except duvc.PropertyValueOutOfRangeError as e:
    # Out of range: clamp and retry
    corrected = max(e.min_val, min(e.max_val, e.value))
    camera.set_brightness(corrected)
except duvc.PropertyNotSupportedError as e:
    # Property unavailable: use alternative
    print(f"Brightness not available on this device")
    print(f"Supported: {camera.get_supported_properties()}")
except duvc.PropertyModeNotSupportedError as e:
    # Mode not available: use fallback mode
    if 'manual' in e.supported_modes:
        camera.set_property_manual(e.property_name, 100)
except duvc.DeviceNotFoundError as e:
    # Device disconnected: reconnect or restart
    camera.reconnect()
except duvc.DuvcError as e:
    # Catch-all for other errors
    print(f"Unhandled error: {e}")
```

**Pattern 3: Multi-level error handling**

```python
try:
    # Try primary operation
    result = camera.bulk_set_properties(props)
except duvc.BulkOperationError as e:
    # Partial success: handle per-property
    print(f"Succeeded: {e.successful_count}/{e.total_count}")
    
    for prop, error_msg in e.failed_properties.items():
        if "not supported" in error_msg.lower():
            print(f"Skip unsupported: {prop}")
        elif "out of range" in error_msg.lower():
            # Retry with clamped value
            try:
                camera.set_single_property(prop, props[prop])
            except duvc.PropertyValueOutOfRangeError as pe:
                corrected = max(pe.min_val, min(pe.max_val, pe.value))
                camera.set_single_property(prop, corrected)
except duvc.ConnectionHealthError as e:
    # Connection degraded: attempt recovery
    print(f"Connection issues: {e.health_issues}")
    try:
        camera.reconnect()
    except Exception:
        camera.close()
        camera = duvc.CameraController(0)
except duvc.DuvcError as e:
    log_error(e)
    raise
```


***

#### Specific exception catching strategies

**Device access errors**:

```python
try:
    camera = duvc.CameraController(device_index)
except duvc.DeviceNotFoundError:
    # List available devices
    available = duvc.list_devices()
    if not available:
        print("No cameras found")
    else:
        print("Available cameras:")
        for dev in available:
            print(f"  - {dev.name}")
except duvc.DeviceBusyError:
    print("Camera in use by another app. Close it first.")
    time.sleep(2)
    # Retry
    camera = duvc.CameraController(device_index)
except duvc.PermissionDeniedError:
    print("Camera access denied. Check privacy settings.")
```

**Property value errors**:

```python
try:
    camera.set_brightness(new_value)
except duvc.PropertyValueOutOfRangeError as e:
    # Smart recovery: auto-clamp
    corrected = max(e.min_val, min(e.max_val, e.value))
    camera.set_brightness(corrected)
    print(f"Value clamped from {e.value} to {corrected}")
except duvc.PropertyNotSupportedError as e:
    print(f"Property {e.property_name} not available")
    # Try alternative property
    available = camera.get_supported_video_properties()
    print(f"Try: {available}")
except duvc.PropertyModeNotSupportedError as e:
    print(f"Mode {e.mode} not available for {e.property_name}")
    if e.supported_modes:
        fallback = e.supported_modes[0]
        camera.set_property_mode(e.property_name, fallback)
```

**System/platform errors**:

```python
try:
    camera.perform_operation()
except duvc.SystemError as e:
    print(f"System error: {e}")
    logger.error(f"Unrecoverable system error: {e.error_code}")
    # Escalate: requires restart/driver reinstall
    raise
except duvc.NotImplementedError:
    print("Feature not available on this device")
    # Degrade gracefully
    use_fallback_method()
```


***

#### Recovery strategies with get_recovery_suggestions()

Exceptions with recovery guidance expose suggestions via method:

```python
try:
    camera.bulk_set_properties(props)
except duvc.BulkOperationError as e:
    suggestions = e.get_recovery_suggestions()
    for suggestion in suggestions:
        print(f"Try: {suggestion}")
    
    # Apply first suggestion if possible
    if suggestions:
        if "Reconnect" in suggestions[0]:
            camera.reconnect()
        elif "Query capabilities" in suggestions[0]:
            caps = camera.get_capabilities()
except duvc.ConnectionHealthError as e:
    suggestions = e.get_recovery_suggestions()
    for suggestion in suggestions:
        print(f"Suggested fix: {suggestion}")
    
    # Implement suggestion
    if any("reconnect" in s.lower() for s in suggestions):
        try:
            camera.reconnect()
        except Exception:
            print("Reconnect failed, restarting...")
            camera = duvc.CameraController(0)
except duvc.PropertyValueOutOfRangeError as e:
    # Exception message includes suggestion
    print(str(e))  # Prints with clamped value suggestion
```

**Recovery suggestion categories**:


| Error Pattern | Suggestion Category | Action |
| :-- | :-- | :-- |
| Out of range | "Try: X" (clamped value) | Apply directly |
| Not supported | "Query capabilities" | Call `get_supported_*()` |
| Busy/Locked | "Close other apps" or "Reconnect" | Specific action provided |
| Connection | "Reconnect" or "Restart device" | Progressive escalation |
| Timeout | "Check USB connection" | Hardware/driver check |

