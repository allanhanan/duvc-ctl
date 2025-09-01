# duvc-ctl CLI Documentation

## Table of Contents

- [CLI Overview](#cli-overview)
- [Installation \& Building](#installation--building)
- [Command Reference](#command-reference)
- [Usage Examples](#usage-examples)
- [Advanced Features](#advanced-features)
- [Error Codes](#error-codes)
- [Troubleshooting](#troubleshooting)

***

## CLI Overview

The duvc-cli is a command-line interface for the duvc-ctl library that provides direct access to UVC camera controls through the DirectShow API. It offers a simple, scriptable interface for camera property management, device monitoring, and vendor-specific operations.

### Key Features

- **Device Management**: List, monitor, and check status of connected UVC cameras
- **Property Control**: Get, set, and query ranges for camera and video processing properties
- **Real-time Monitoring**: Watch for device connect/disconnect events
- **Vendor Extensions**: Access vendor-specific properties via IKsPropertySet
- **Connection Management**: Cache control for performance optimization
- **Cross-platform**: Works with MSVC and MinGW compilers


### Supported Domains

- **cam**: Camera Control Properties (IAMCameraControl) - 24 properties
- **vid**: Video Processing Properties (IAMVideoProcAmp) - 10 properties

***

## Installation \& Building

### Build Requirements

```cmake
cmake_minimum_required(VERSION 3.16)
```


### Building the CLI

The CLI is built as part of the main duvc-ctl project:

```bash
# Configure project with CLI enabled (default)
cmake -B build -DDUVC_BUILD_CLI=ON

# Build the CLI
cmake --build build --config Release

# The executable will be at: build/bin/duvc-cli.exe
```


### Compiler-Specific Features

#### MSVC Configuration

```cmake
target_compile_options(duvc-cli PRIVATE /W4 /permissive-)
target_compile_definitions(duvc-cli PRIVATE UNICODE _UNICODE NOMINMAX)
```


#### MinGW Configuration

```cmake
target_link_options(duvc-cli PRIVATE -mconsole)
target_compile_options(duvc-cli PRIVATE -Wall -Wextra)
```


***

## Command Reference

### Basic Syntax

```
duvc-cli <command> [arguments...]
```


### Commands Overview

| Command | Purpose | Example |
| :-- | :-- | :-- |
| `list` | Enumerate connected devices | `duvc-cli list` |
| `get` | Get property value | `duvc-cli get 0 vid Brightness` |
| `set` | Set property value | `duvc-cli set 0 vid Brightness 128 manual` |
| `range` | Get property constraints | `duvc-cli range 0 cam Exposure` |
| `monitor` | Monitor device changes | `duvc-cli monitor 30` |
| `status` | Check device connection | `duvc-cli status 0` |
| `clear-cache` | Clear connection cache | `duvc-cli clear-cache` |
| `vendor` | Vendor property access | `duvc-cli vendor 0 {GUID} 1 get` |

### Device Listing

#### list

```
duvc-cli list
```

**Purpose**: Enumerate all connected UVC cameras

**Output Format**:

```
Devices: 2
[^0] Logitech HD Pro Webcam C920
 \\?\usb#vid_046d&pid_082d&mi_00#7&1234abcd&0&0000#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\global
[^1] USB Camera
 \\?\usb#vid_1234&pid_5678&mi_00#8&abcd1234&0&0000#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\global
```


### Property Operations

#### get

```
duvc-cli get <device_index> <domain> <property>
```

**Parameters**:

- `device_index`: Device index from list (0-based)
- `domain`: `cam` (camera) or `vid` (video processing)
- `property`: Property name (case-insensitive)

**Example**:

```bash
duvc-cli get 0 vid Brightness
# Output: Brightness = 128 (MANUAL)
```


#### set

```
duvc-cli set <device_index> <domain> <property> <value> [mode]
```

**Parameters**:

- `device_index`: Device index from list
- `domain`: `cam` or `vid`
- `property`: Property name
- `value`: Integer value to set
- `mode`: `auto` or `manual` (default: manual)

**Example**:

```bash
duvc-cli set 0 vid Brightness 200 manual
# Output: OK
```


#### range

```
duvc-cli range <device_index> <domain> <property>
```

**Purpose**: Get valid range and default values for a property

**Example**:

```bash
duvc-cli range 0 vid Brightness
# Output: Brightness: min=0, max=255, step=1, default=128, mode=AUTO
```


### Device Management

#### status

```
duvc-cli status <device_index>
```

**Purpose**: Check if a specific device is connected and accessible

**Example**:

```bash
duvc-cli status 0
# Output: Device [^0] Logitech HD Pro Webcam C920 is CONNECTED
```


#### monitor

```
duvc-cli monitor [seconds]
```

**Parameters**:

- `seconds`: Duration to monitor (default: 30)

**Purpose**: Watch for device connect/disconnect events in real-time

**Example**:

```bash
duvc-cli monitor 60
# Output:
# Monitoring device changes for 60 seconds...
# Press Ctrl+C to stop early.
# 
# [DEVICE ADDED] \\?\usb#vid_046d&pid_082d&mi_00#7&...
# [DEVICE REMOVED] \\?\usb#vid_046d&pid_082d&mi_00#7&...
```


#### clear-cache

```
duvc-cli clear-cache
```

**Purpose**: Clear internal connection cache (useful after device reconnection)

**Example**:

```bash
duvc-cli clear-cache
# Output: Connection cache cleared.
```


### Vendor Properties (Windows Only)

#### vendor

```
duvc-cli vendor <device_index> <guid> <property_id> <operation> [data_hex]
```

**Parameters**:

- `device_index`: Device index from list
- `guid`: Property set GUID (with or without braces)
- `property_id`: Property ID (integer)
- `operation`: `get`, `set`, or `query`
- `data_hex`: Hexadecimal data for set operations

**Examples**:

```bash
# Query property support
duvc-cli vendor 0 {82066163-7BD0-43EF-8A6F-5B8905C9A64C} 1 query
# Output: Vendor property SUPPORTED

# Get property data
duvc-cli vendor 0 82066163-7BD0-43EF-8A6F-5B8905C9A64C 1 get
# Output: Vendor property data: 01000000

# Set property data
duvc-cli vendor 0 {82066163-7BD0-43EF-8A6F-5B8905C9A64C} 1 set 00000000
# Output: Vendor property set successfully.
```


***

## Usage Examples

### Basic Camera Control

```bash
# List all connected cameras
duvc-cli list

# Get current pan value
duvc-cli get 0 cam Pan

# Set pan to center position (usually 0) in manual mode
duvc-cli set 0 cam Pan 0 manual

# Get pan range to see valid values
duvc-cli range 0 cam Pan
```


### Video Processing Control

```bash
# Check current brightness
duvc-cli get 0 vid Brightness

# Increase brightness
duvc-cli set 0 vid Brightness 200 manual

# Set auto white balance
duvc-cli set 0 vid WhiteBalance 0 auto

# Check contrast range
duvc-cli range 0 vid Contrast
```


### Batch Operations

```bash
# Save current settings (Windows batch example)
@echo off
duvc-cli get 0 vid Brightness > brightness.txt
duvc-cli get 0 vid Contrast > contrast.txt
duvc-cli get 0 vid Saturation > saturation.txt

# Apply settings
duvc-cli set 0 vid Brightness 180 manual
duvc-cli set 0 vid Contrast 150 manual  
duvc-cli set 0 vid Saturation 120 manual

echo Settings applied. Press any key to restore...
pause

# Restore from saved values (implementation needed)
```


### Scripting with Error Handling

```bash
#!/bin/bash
# Linux/MinGW example

# Check if device exists
if ! duvc-cli status 0 > /dev/null 2>&1; then
    echo "Camera not found or not accessible"
    exit 1
fi

# Set multiple properties with error checking
properties=("Brightness:180" "Contrast:140" "Saturation:130")

for prop in "${properties[@]}"; do
    IFS=':' read -r name value <<< "$prop"
    if duvc-cli set 0 vid "$name" "$value" manual; then
        echo "✓ Set $name to $value"
    else
        echo "✗ Failed to set $name"
    fi
done
```


### Device Monitoring Script

```bash
# Monitor devices and log changes
duvc-cli monitor 300 | while IFS= read -r line; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $line" >> device_changes.log
done
```


***

## Advanced Features

### Property Name Reference

#### Camera Control Properties (cam domain)

```
Pan, Tilt, Roll, Zoom, Exposure, Iris, Focus, ScanMode, Privacy,
PanRelative, TiltRelative, RollRelative, ZoomRelative, 
ExposureRelative, IrisRelative, FocusRelative, PanTilt, 
PanTiltRelative, FocusSimple, DigitalZoom, DigitalZoomRelative,
BacklightCompensation, Lamp
```


#### Video Processing Properties (vid domain)

```
Brightness, Contrast, Hue, Saturation, Sharpness, Gamma, 
ColorEnable, WhiteBalance, BacklightCompensation, Gain
```


### Control Modes

- **auto**: Camera automatically manages the property
- **manual**: User has direct control over the property value


### GUID Format Support

The vendor command accepts GUIDs in multiple formats:

```bash
# With braces (recommended)
{82066163-7BD0-43EF-8A6F-5B8905C9A64C}

# Without braces (auto-converted)
82066163-7BD0-43EF-8A6F-5B8905C9A64C
```


### Hexadecimal Data Format

Vendor property data is represented as hexadecimal strings:

```bash
# 4-byte integer value 1
01000000

# 4-byte integer value 256
00010000

# 1-byte boolean true
01

# 8-byte data
0123456789ABCDEF
```


***

## Error Codes

The CLI returns specific exit codes for different error conditions:


| Exit Code | Meaning | Example Cause |
| :-- | :-- | :-- |
| 0 | Success | Command completed successfully |
| 1 | Usage Error | Invalid command syntax or arguments |
| 2 | Device Error | Invalid device index or device not found |
| 3 | Property Error | Unknown property name or invalid mode |
| 4 | Operation Error | Property not supported or operation failed |

### Error Code Examples

```bash
# Exit code 1 - Usage error
duvc-cli get
echo $?  # Output: 1

# Exit code 2 - Invalid device index
duvc-cli get 99 vid Brightness
echo $?  # Output: 2

# Exit code 3 - Unknown property
duvc-cli get 0 vid InvalidProperty
echo $?  # Output: 3

# Exit code 4 - Property not supported
duvc-cli get 0 cam UnsupportedProperty
echo $?  # Output: 4
```


***

## Troubleshooting

### Common Issues

#### 1. No Devices Found

```bash
duvc-cli list
# Output: Devices: 0
```

**Solutions**:

- Check if camera is connected and recognized by Windows Device Manager
- Ensure camera is not being used by another application
- Try running as Administrator
- Clear connection cache: `duvc-cli clear-cache`


#### 2. Property Not Supported

```bash
duvc-cli get 0 cam Pan
# Output: Property not supported or failed to read.
```

**Solutions**:

- Check if the camera supports the property: `duvc-cli range 0 cam Pan`
- Try different property names (check spelling)
- Some cameras only support a subset of properties


#### 3. Failed to Set Property

```bash
duvc-cli set 0 vid Brightness 300 manual
# Output: Failed to set property.
```

**Solutions**:

- Check valid range: `duvc-cli range 0 vid Brightness`
- Ensure value is within min/max bounds
- Try with `auto` mode instead of `manual`


#### 4. Device Connection Issues

```bash
duvc-cli status 0
# Output: Device [^0] Camera Name is DISCONNECTED
```

**Solutions**:

- Reconnect the USB cable
- Clear connection cache: `duvc-cli clear-cache`
- Check for driver issues in Device Manager
- Try different USB port


### Debug Information

#### Enable Verbose Output

The CLI relies on the underlying library's logging. To enable verbose output in your application:

```cpp
duvc::set_log_callback([](duvc::LogLevel level, const std::string& message) {
    std::cout << "[" << duvc::to_string(level) << "] " << message << "\n";
});
duvc::set_log_level(duvc::LogLevel::Debug);
```


#### Test Device Accessibility

```bash
# Quick test sequence
duvc-cli list                          # Check if devices are detected
duvc-cli status 0                      # Check specific device status
duvc-cli range 0 vid Brightness        # Test property access
duvc-cli get 0 vid Brightness          # Test property reading
```


### Performance Tips

1. **Use Connection Caching**: Multiple operations on the same device automatically benefit from connection caching
2. **Clear Cache When Needed**: After device reconnection, use `duvc-cli clear-cache`
3. **Batch Operations**: Group multiple property changes to minimize overhead
4. **Check Ranges First**: Use `range` command before setting values to avoid errors

### Platform-Specific Notes

#### Windows (MSVC)

- Full Unicode support for device names and paths
- Complete vendor property support via IKsPropertySet
- Integrated with Windows Device Manager


#### Windows (MinGW)

- Console subsystem properly configured
- Cross-platform compatibility maintained
- All features supported
