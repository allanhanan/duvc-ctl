# duvc-cli

Command-line tool for DirectShow UVC camera control on Windows.

# Table of Contents

- [duvc-cli](#duvc-cli)
- [Table of Contents](#table-of-contents)
  - [Build](#build)
  - [Syntax](#syntax)
  - [Global Flags](#global-flags)
  - [Commands](#commands)
    - [list](#list)
    - [get](#get)
    - [set](#set)
    - [range](#range)
    - [reset](#reset)
    - [snapshot](#snapshot)
    - [capabilities](#capabilities)
    - [status](#status)
    - [monitor](#monitor)
  - [Properties](#properties)
    - [Camera (cam domain)](#camera-cam-domain)
    - [Video (vid domain)](#video-vid-domain)
  - [Exit Codes](#exit-codes)
  - [Scripting](#scripting)
    - [PowerShell](#powershell)
    - [Bash](#bash)
  - [Limitations](#limitations)
  - [Testing](#testing)
  - [Common Issues](#common-issues)
  - [Examples](#examples)
  - [See Also](#see-also)


## Build

```

cmake -B build
cmake --build build --config Release

```

Binary: `build/bin/Release/duvc-cli.exe`

## Syntax

```

duvc-cli [flags] <command> [args]

```

## Global Flags

| Flag | Description |
|------|-------------|
| `-v, --verbose` | Detailed output with debug info |
| `-q, --quiet` | Errors only |
| `-j, --json` | JSON output format |
| `-h, --help` | Show help |

## Commands

### list

Enumerate devices.

```
duvc-cli list [--detailed|-d]

```

**Options:**
- `--detailed, -d`: Show supported properties

**Output:**
```
Devices: 2
[0] Integrated Camera
    Path: \\?\usb#vid_5986&pid_215f&mi_00#7&164a69c3&0&0000#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\global
    Status: CONNECTED
    Supported properties:
      Camera: Exposure, Privacy, DigitalZoom (3)
      Video: Brightness, Contrast, Hue, Saturation, Sharpness, Gamma, WhiteBalance, BacklightCompensation (8)
[1] OBS Virtual Camera
    Path: @device:sw:{860BB310-5D01-11D0-BD3B-00A0C911CE86}\{A3FCE0F5-3493-419F-958A-ABA1250EC20B}
    Status: CONNECTED
    Supported properties:
      Camera:  (0)       
      Video:  (0)
```

### get

Read property value.

```
duvc-cli get <index> <domain> <prop>[,<prop>...]
```


**Parameters:**
- `index`: Device index (from `list`, 0-based)
- `domain`: `cam` or `vid`
- `prop`: Property name (comma-separated for batch)

**Example:**
```

duvc-cli get 0 vid Brightness

# Brightness=128 (MANUAL)

duvc-cli get 0 cam Pan,Tilt

# Pan=0 (MANUAL)

# Tilt=0 (MANUAL)

```

### set

Write property value.

```
# Absolute value

duvc-cli set <index> <domain> <prop>=<val>[,<prop>=<val>...]

duvc-cli set <index> <domain> <prop> <value> [auto|manual]


# Relative value (adds/subtracts from current)

duvc-cli set --relative <index> <domain> <prop> <delta>

duvc-cli set -r <index> <domain> <prop> <delta>


# Mode only

duvc-cli set <index> <domain> <prop> <auto|manual>

```

**Parameters:**
- `index`: Device index
- `domain`: `cam` or `vid`
- `prop`: Property name
- `value`: Integer value
- `delta`: Signed integer for relative operations (+5, -3)
- Mode: `auto` or `manual` (default: manual for value sets)

**Examples:**
```
# Set absolute value

duvc-cli set 0 vid Brightness 200

# Set with explicit mode

duvc-cli set 0 vid Brightness 180 manual

# Batch set

duvc-cli set 0 vid Brightness=180,Contrast=140

# Relative operations (reads current, adds delta, writes new value)

duvc-cli set --relative 0 cam Exposure +2   \# increase by 2
duvc-cli set -r 0 cam Exposure -3           \# decrease by 3

# Mode only (preserves current value)

duvc-cli set 0 vid WhiteBalance auto

```

**Relative Operations:**
Uses get-modify-set pattern. More compatible than DirectShow `*Relative` properties.
Validates result is within range before writing.

### range

Query valid values for property.

```

duvc-cli range <index> <domain> <prop>[,<prop>...|all]

```

**Example:**
```

duvc-cli range 0 vid Brightness

# Brightness:  step=1 default=128 (AUTO)

duvc-cli range 0 cam all

# Exposure: [-12,-3] step=1 default=-6 (AUTO)

# ...

```

### reset

Reset properties to default.

```

duvc-cli reset <index> <domain|all> <prop>[,<prop>...|all]

```

**Examples:**
```

duvc-cli reset 0 vid Brightness       \# Reset single property
duvc-cli reset 0 vid all              \# Reset all video properties
duvc-cli reset 0 all                  \# Reset everything

```

### snapshot

Dump all current values.

```
duvc-cli snapshot <index> [-o <file>]
```

**Formats:**
- Text: `cam.Exposure=-6:MANUAL`
- JSON: `{"device":0,"properties":{...}}`

**Example:**
```
duvc-cli snapshot 0 -o backup.txt
duvc-cli -j snapshot 0 -o config.json

```

### capabilities

List supported properties with current values.

```
duvc-cli capabilities <index>

```

**Output:**
```
Capabilities: Integrated Camera
  CAM Exposure: [-12,-3] step=1 default=-6 current=-4 (AUTO)
  CAM Privacy: [0,1] step=1 default=0 current=0 (MANUAL)
  CAM DigitalZoom: [0,0] step=0 default=0 current=0 (MANUAL)
  VID Brightness: [0,255] step=1 default=128 current=128 (MANUAL)
  VID Contrast: [0,100] step=1 default=32 current=32 (MANUAL)
  VID Hue: [-180,180] step=1 default=0 current=0 (MANUAL)
  VID Saturation: [0,100] step=1 default=64 current=64 (MANUAL)
  VID Sharpness: [0,7] step=1 default=3 current=3 (MANUAL)
  VID Gamma: [90,150] step=1 default=120 current=120 (MANUAL)
  VID WhiteBalance: [2800,6500] step=1 default=4600 current=4604 (AUTO)
  VID BacklightCompensation: [0,2] step=1 default=1 current=1 (MANUAL)

```

### status

Check device connection state.

```
duvc-cli status <index>

```

**Output:**
```
Integrated Camera: CONNECTED
```

### monitor

Watch for device changes or property updates.

```
# Device hotplug events

duvc-cli monitor [seconds]

# Property monitoring

duvc-cli monitor <index> <domain> <prop> [--interval=<seconds>]

```

**Examples:**
```
duvc-cli monitor 60                           \# Watch device add/remove
duvc-cli monitor 0 vid Brightness --interval=2  \# Poll property

```

## Properties

### Camera (cam domain)

```
Pan, Tilt, Roll, Zoom, Exposure, Iris, Focus, ScanMode, Privacy,
PanRelative, TiltRelative, RollRelative, ZoomRelative, 
ExposureRelative, IrisRelative, FocusRelative, 
PanTilt, PanTiltRelative, FocusSimple, 
DigitalZoom, DigitalZoomRelative, 
BacklightCompensation, Lamp
```

DirectShow `IAMCameraControl` interface.

### Video (vid domain)

```
Brightness, Contrast, Hue, Saturation, Sharpness, Gamma, 
ColorEnable, WhiteBalance, BacklightCompensation, Gain
```

DirectShow `IAMVideoProcAmp` interface.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid syntax |
| 2 | Device not found |
| 3 | Unknown property |
| 4 | Operation failed |

## Scripting

### PowerShell

```
# Check exit code

.\duvc-cli.exe set 0 vid Brightness 200
if (\$LASTEXITCODE -eq 0) {
Write-Host "Success"
}

# Parse output

\$brightness = (.\duvc-cli.exe get 0 vid Brightness) -replace '.*=(\d+).*', '\$1'

# JSON output

\$data = .\duvc-cli.exe -j get 0 vid Brightness | ConvertFrom-Json
\$value = \$data.properties.value

```

### Bash

```
# Error handling

if ! duvc-cli set 0 vid Brightness 200; then
echo "Failed to set brightness"
exit 1
fi

# Parse value

brightness=\$(duvc-cli get 0 vid Brightness | grep -oP 'Brightness=\K\d+')

# JSON parsing

value=\$(duvc-cli -j get 0 vid Brightness | jq -r '.properties.value')

```

## Limitations

1. **Windows only**: Uses DirectShow API
2. **Property support varies by camera**: Check with `capabilities` or `range`
3. **Relative properties**: Some cameras don't support `*Relative` DirectShow properties - use `--relative` flag instead
4. **No streaming control**: Only affects camera settings, not capture

## Testing

Capability-aware test suite included:

```
.\tests\cli\auto.ps1 -CLI ".\build\bin\Debug\duvc-cli.exe" -Verbose

```

Tests adapt to camera capabilities. Expected failures for unsupported properties.

## Common Issues

**No devices found:**
- Check Device Manager
- Close other applications using camera
- Try as Administrator

**Property not supported:**
```
duvc-cli capabilities 0  \# List what's actually supported

```

**Value out of range:**
```

duvc-cli range 0 vid Brightness  \# Check valid range first

```

**Set fails but other bindings works:**
- Camera may be in AUTO mode (blocks manual changes)
- Switch to MANUAL first: `duvc-cli set 0 cam Exposure manual`

## Examples

```
# Query capabilities

duvc-cli capabilities 0
duvc-cli range 0 vid all

# Basic control

duvc-cli get 0 vid Brightness
duvc-cli set 0 vid Brightness 180 manual
duvc-cli reset 0 vid Brightness

# Batch operations

duvc-cli set 0 vid Brightness=180,Contrast=140,Saturation=130

# Relative adjustments

duvc-cli set --relative 0 cam Exposure +2
duvc-cli set -r 0 vid Brightness -10

# Save/restore

duvc-cli snapshot 0 -o backup.txt

# ... make changes ...

# (restoration requires parsing backup file)

# Automation

for i in {0..5}; do
duvc-cli set --relative 0 cam Exposure +1
sleep 1
done

```

## See Also

- API Documentation: https://allanhanan.github.io/duvc-ctl/sphinx/index.html
- DirectShow Reference: https://learn.microsoft.com/en-us/windows/win32/directshow/
- Test Suite: https://github.com/allanhanan/duvc-ctl/tree/main/tests/cli/auto.ps1
```