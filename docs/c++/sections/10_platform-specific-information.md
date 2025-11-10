## 10. Platform-Specific Information


### 10.1 Windows-Specific Details

**Windows API Dependencies:**

duvc-ctl is deeply integrated with Windows platform APIs. Understanding these dependencies is essential for proper usage and troubleshooting.

***

#### Required Windows Headers

```cpp
// Core Windows headers
#include <windows.h>           // Base Windows API
#include <objbase.h>           // COM initialization
#include <dshow.h>             // DirectShow interfaces
#include <ks.h>                // Kernel streaming
#include <ksproxy.h>           // KS proxy interfaces
#include <vidcap.h>            // Video capture structures
```

**Linked libraries:**

```cmake
# Required system libraries
ole32.lib          # COM runtime
oleaut32.lib       # COM automation
strmiids.lib       # DirectShow GUIDs
uuid.lib           # Interface UUIDs
```


***

#### COM Initialization

**COM must be initialized per-thread:**

```cpp
// Automatic RAII wrapper
class ComInitializer {
public:
    ComInitializer() {
        HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
        if (FAILED(hr) && hr != RPC_E_CHANGED_MODE) {
            throw std::runtime_error("COM initialization failed");
        }
        initialized_ = SUCCEEDED(hr);
    }
    
    ~ComInitializer() {
        if (initialized_) {
            CoUninitialize();
        }
    }
    
private:
    bool initialized_;
};
```

**Library handles this automatically:**

```cpp
// duvc-ctl handles COM initialization internally
Camera camera(0);  // COM initialized if needed
```

**Manual control:**

```cpp
// If you need explicit control
HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
// ... use duvc-ctl ...
CoUninitialize();
```


***

#### Threading Model

**Single-Threaded Apartment (STA):**

DirectShow uses STA threading. COM objects are bound to the creating thread and cannot be marshaled to other threads without explicit marshaling.

```cpp
// CORRECT: Each thread initializes COM
std::thread t1([]() {
    ComInitializer com;  // COM for this thread
    Camera camera(0);
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});
});

// WRONG: Passing camera between threads
Camera camera(0);
std::thread t2([&camera]() {
    camera.set(CamProp::Exposure, {-5, CamMode::Manual});  // CRASH!
});
```


***

#### Windows Error Codes

**HRESULT values:**


| HRESULT | Value | Meaning |
| :-- | :-- | :-- |
| `S_OK` | `0x00000000` | Success |
| `E_FAIL` | `0x80004005` | Unspecified failure |
| `E_INVALIDARG` | `0x80070057` | Invalid argument |
| `E_OUTOFMEMORY` | `0x8007000E` | Out of memory |
| `E_POINTER` | `0x80004003` | NULL pointer |
| `E_NOTIMPL` | `0x80004001` | Not implemented |
| `VFW_E_NOT_CONNECTED` | `0x80040209` | Filter not connected |
| `VFW_E_CANNOT_CONNECT` | `0x80040217` | Cannot connect pins |

**Decoding errors:**

```cpp
// Use library utilities
std::string error_msg = duvc::decode_hresult(hr);
std::cout << "Error: " << error_msg << std::endl;

// Check error categories
if (duvc::is_device_error(hr)) {
    // Device-specific error
}
if (duvc::is_permission_error(hr)) {
    // Access denied
}
```


***

#### Device Paths

**DirectShow device moniker paths:**

```
\\?\usb#vid_046d&pid_0825&mi_00#7&2a2f12e8&0&0000#{65e8773d-8f56-11d0-a3b9-00a0c9223196}\global
```

**Format breakdown:**

- `\\?\` - Win32 device namespace prefix
- `usb#vid_046d&pid_0825` - USB Vendor ID and Product ID
- `mi_00` - Multiple interface index
- `{guid}` - Device class GUID (video capture)
- `\global` - System-wide device

**Parsing device info:**

```cpp
// Extract vendor/product ID
std::wstring path = device.path;
size_t vid_pos = path.find(L"vid_");
size_t pid_pos = path.find(L"pid_");

if (vid_pos != std::wstring::npos && pid_pos != std::wstring::npos) {
    std::wstring vid = path.substr(vid_pos + 4, 4);  // e.g., "046d"
    std::wstring pid = path.substr(pid_pos + 4, 4);  // e.g., "0825"
}
```


***

#### System Requirements

**Minimum Windows version:**

- **Windows 10** recommended
- **Windows 8.1** compatible (not tested)
- **Windows 7** not supported (DirectShow API changes)

**Required components:**

- Visual C++ Redistributable 2019/2022
- DirectX 9.0c or later
- Windows Media Feature Pack (if disabled)

**Checking availability:**

```cpp
// Verify DirectShow availability
HRESULT hr = CoInitialize(nullptr);
if (SUCCEEDED(hr)) {
    ICreateDevEnum* pDevEnum = nullptr;
    hr = CoCreateInstance(CLSID_SystemDeviceEnum, nullptr, 
                          CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&pDevEnum));
    if (SUCCEEDED(hr)) {
        // DirectShow available
        pDevEnum->Release();
    }
    CoUninitialize();
}
```


***

#### Permissions and Access

**Administrator rights:**
Not required for UVC camera access. Standard user permissions suffice.

**Exclusive access:**
DirectShow grants exclusive access to camera properties. If another application is controlling the camera, property changes may fail with `E_FAIL` or `VFW_E_IN_USE`.

**Antivirus interference:**
Some antivirus software blocks camera access. Check:

- Windows Security → Camera privacy settings
- Third-party antivirus camera protection

***

#### Wide Character Strings

**Windows uses UTF-16:**

```cpp
// Device names are std::wstring
Device device = devices[0];
std::wstring name = device.name;  // UTF-16

// Convert to UTF-8 for display
std::string utf8_name = duvc::to_utf8(name);
std::cout << "Device: " << utf8_name << std::endl;
```

**Conversion utilities:**

```cpp
namespace duvc {
    std::string to_utf8(const std::wstring& wstr);
    std::wstring from_utf8(const std::string& str);
}
```


***

### 10.2 DirectShow Background

**DirectShow is Microsoft's multimedia framework for capture, playback, and processing.**

***

#### Architecture Overview

**Filter graph model:**

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│ Capture     │      │ Transform   │      │ Renderer    │
│ Filter      │─────▶│ Filter      │─────▶│ Filter      │
│ (Camera)    │      │ (Optional)  │      │ (Display)   │
└─────────────┘      └─────────────┘      └─────────────┘
```

**Components:**

- **Filters** - Processing units (capture, transform, render)
- **Pins** - Connection points between filters
- **Filter Graph Manager** - Coordinates filter operation
- **Media Types** - Describes data format (video format, resolution)

***

#### Key Interfaces Used

**Device enumeration:**

```cpp
// ICreateDevEnum - Enumerate device categories
CLSID_SystemDeviceEnum
  → ICreateDevEnum::CreateClassEnumerator(CLSID_VideoInputDeviceCategory)
    → IEnumMoniker (iterate devices)
      → IMoniker::BindToObject(IBaseFilter)
```

**Camera control:**

```cpp
// IAMCameraControl - PTZ and camera-specific properties
IBaseFilter* pFilter;
IAMCameraControl* pCameraControl;
pFilter->QueryInterface(IID_IAMCameraControl, (void**)&pCameraControl);

// Set property
pCameraControl->Set(CameraControl_Pan, value, CameraControl_Flags_Manual);
pCameraControl->Get(CameraControl_Pan, &value, &flags);
```

**Video processing:**

```cpp
// IAMVideoProcAmp - Image properties
IAMVideoProcAmp* pVideoProcAmp;
pFilter->QueryInterface(IID_IAMVideoProcAmp, (void**)&pVideoProcAmp);

// Set brightness
pVideoProcAmp->Set(VideoProcAmp_Brightness, value, VideoProcAmp_Flags_Manual);
```

**Vendor extensions:**

```cpp
// IKsPropertySet - Kernel streaming properties
IKsPropertySet* pKsPropertySet;
pFilter->QueryInterface(IID_IKsPropertySet, (void**)&pKsPropertySet);

// Get/Set vendor-specific properties
GUID propSet = {/* vendor GUID */};
pKsPropertySet->Get(propSet, propId, nullptr, 0, data, dataSize, &returned);
```


***

#### Property Control Flow

**Setting a camera property:**

1. Enumerate devices → `ICreateDevEnum`
2. Bind to device filter → `IMoniker::BindToObject`
3. Query property interface → `QueryInterface(IAMCameraControl)`
4. Check property support → `GetRange()`
5. Set property value → `Set(prop, value, flags)`
6. Verify change → `Get(prop, &value, &flags)`

**Code path:**

```cpp
// duvc-ctl wraps this flow
Camera camera(device);  // Steps 1-3
auto range = camera.get_range(CamProp::Pan);  // Step 4
camera.set(CamProp::Pan, {0, CamMode::Manual});  // Steps 5-6
```


***

#### DirectShow vs Media Foundation

**DirectShow** (used by duvc-ctl):

- Legacy API (Windows XP+)
- Widely supported by hardware
- Filter graph model
- Synchronous property access
- Well-documented UVC support

**Media Foundation** (newer):

- Modern API (Windows Vista+)
- Async design
- Better performance for streaming
- Limited camera control compared to DirectShow
- Less hardware compatibility

**Why DirectShow?**

- **Universal UVC support** - Works with all compliant cameras
- **Direct property access** - No additional drivers needed
- **Mature ecosystem** - 20+ years of hardware compatibility
- **Synchronous operations** - Simpler control flow for settings

***

#### Graph Building (Not Used)

duvc-ctl does **not** build filter graphs for streaming. It only uses device filters for property control:

```cpp
// duvc-ctl does NOT do this:
IGraphBuilder* pGraph;
pGraph->AddFilter(pCaptureFilter, L"Capture");
pGraph->Render(pCapturePin);  // Build capture graph

// duvc-ctl ONLY does this:
IAMCameraControl* pControl;
pCaptureFilter->QueryInterface(IID_IAMCameraControl, (void**)&pControl);
pControl->Set(CameraControl_Pan, 0, CameraControl_Flags_Manual);
```

**Streaming is handled by:**

- Windows Camera app
- OpenCV (VideoCapture)
- FFmpeg (dshow input)
- Third-party capture applications

***

### 10.3 UVC Camera Standards

**USB Video Class (UVC) defines standard camera controls.**

***

#### UVC Specification

**USB.org UVC 1.5:**

- Standard published by USB Implementers Forum
- Defines camera control terminals and units
- Provides class-specific USB descriptors
- Maps to DirectShow `IAMCameraControl` and `IAMVideoProcAmp`

**Key concepts:**

- **Control terminals** - Camera-specific controls (pan, tilt, zoom)
- **Processing units** - Image processing (brightness, contrast)
- **Extension units** - Vendor-specific controls

***

#### Standard UVC Controls

**Camera Terminal Controls (IAMCameraControl):**


| UVC Control | DirectShow Property | Units | Typical Range |
| :-- | :-- | :-- | :-- |
| Scanning Mode | `CameraControl_ScanMode` | - | 0 (Interlaced), 1 (Progressive) |
| Auto Exposure Mode | `CameraControl_Exposure` | - | 1 (Manual), 2-8 (Auto modes) |
| Auto Exposure Priority | - | - | Camera-dependent |
| Exposure Time | `CameraControl_Exposure` | 100µs | -13 to -1 (log scale) |
| Focus | `CameraControl_Focus` | mm | 0 to max (device-specific) |
| Iris | `CameraControl_Iris` | f-stop × 10 | Device-specific |
| Zoom | `CameraControl_Zoom` | mm | Device-specific |
| Pan | `CameraControl_Pan` | degrees | -180° to +180° |
| Tilt | `CameraControl_Tilt` | degrees | -180° to +180° |
| Roll | `CameraControl_Roll` | degrees | -180° to +180° |
| Privacy Shutter | `CameraControl_Privacy` | - | 0 (Open), 1 (Closed) |

**Processing Unit Controls (IAMVideoProcAmp):**


| UVC Control | DirectShow Property | Typical Range |
| :-- | :-- | :-- |
| Brightness | `VideoProcAmp_Brightness` | 0 to 255 |
| Contrast | `VideoProcAmp_Contrast` | 0 to 255 |
| Hue | `VideoProcAmp_Hue` | -180° to +180° |
| Saturation | `VideoProcAmp_Saturation` | 0 to 255 |
| Sharpness | `VideoProcAmp_Sharpness` | 0 to 255 |
| Gamma | `VideoProcAmp_Gamma` | 100 to 500 (100 = 1.0) |
| White Balance | `VideoProcAmp_WhiteBalance` | 2800K to 6500K |
| Backlight Compensation | `VideoProcAmp_BacklightCompensation` | 0 (Off), 1 (On) |
| Gain | `VideoProcAmp_Gain` | 0 to 255 |
| Color Enable | `VideoProcAmp_ColorEnable` | 0 (B\&W), 1 (Color) |


***

#### Auto vs Manual Modes

**UVC defines automatic control:**

```cpp
// Auto mode - camera adjusts automatically
camera.set(CamProp::Exposure, {0, CamMode::Auto});

// Manual mode - explicit value
camera.set(CamProp::Exposure, {-5, CamMode::Manual});
```

**DirectShow flags:**

```cpp
CameraControl_Flags_Auto   = 0x0001  // Automatic adjustment
CameraControl_Flags_Manual = 0x0002  // Manual control
```

**UVC behavior:**

- **Auto mode** - Value parameter ignored, camera firmware controls
- **Manual mode** - Value parameter used, firmware uses specified value
- **Auto → Manual** - Locks current auto value
- **Manual → Auto** - Resumes automatic adjustment

***

#### Vendor-Specific Extensions

**Beyond UVC standard:**

Vendors implement proprietary controls via **Extension Units (XU)** using `IKsPropertySet`.

**Logitech example:**

```cpp
// Standard UVC
camera.set(CamProp::Exposure, {-5, CamMode::Manual});

// Vendor extension (Logitech)
logitech::set_logitech_property(device, LogitechProperty::RightLight, true);
```

**Common vendor extensions:**

- **Logitech** - RightLight, LED control, face tracking
- **Microsoft LifeCam** - TrueColor, noise reduction
- **Razer Kiyo** - Ring light control
- **Elgato Facecam** - Advanced color grading

***

#### UVC Compliance Levels

**Not all cameras are equal:**

**Full UVC 1.5:**

- All standard controls
- Auto/manual modes
- Proper range reporting
- Spec-compliant behavior

**Partial UVC:**

- Subset of controls (e.g., no PTZ)
- Missing auto modes
- Incorrect range values
- Quirky implementations

**Testing compliance:**

```cpp
// Check which properties are supported
for (auto prop : {CamProp::Pan, CamProp::Tilt, CamProp::Zoom}) {
    auto range_result = camera.get_range(prop);
    if (range_result.is_ok()) {
        std::cout << "Supports: " << to_string(prop) << std::endl;
    }
}
```


***

#### USB Bandwidth

**UVC streaming consumes USB bandwidth:**

**USB 2.0 limits:**

- High-speed: 480 Mbps theoretical
- Practical: ~35 MB/s for video
- 1080p30 uncompressed: ~177 MB/s (requires compression)

**USB 3.0/3.1:**

- SuperSpeed: 5 Gbps (USB 3.0), 10 Gbps (USB 3.1)
- Supports uncompressed high-resolution video

**Control bandwidth:**
Property control uses USB control transfers (separate from video data). Control operations are lightweight and don't impact streaming performance.

***

#### Descriptor Parsing

**UVC cameras expose USB descriptors:**

DirectShow automatically parses:

- Video Control Interface
- Video Streaming Interface
- Camera Terminal Descriptor
- Processing Unit Descriptor
- Extension Unit Descriptor

**duvc-ctl abstracts this:**

```cpp
// No need to parse descriptors
Camera camera(0);
auto range = camera.get_range(CamProp::Pan);  // Descriptor info extracted
```

