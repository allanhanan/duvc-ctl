## 16. Appendices


### 16.1 DirectShow Property Constants

- **Camera Properties (IAMCameraControl)**
    - `Pan` (0)
    - `Tilt` (1)
    - `Roll` (2)
    - `Zoom` (3)
    - `Exposure` (4)
    - `Iris` (5)
    - `Focus` (6)
    - `ScanMode`, `Privacy`, `PanRelative`, etc.
- **Video Properties (IAMVideoProcAmp)**
    - `Brightness` (0)
    - `Contrast` (1)
    - `Hue` (2)
    - `Saturation` (3)
    - `Sharpness` (4)
    - `Gamma`, `ColorEnable`, `WhiteBalance`, etc.

Each enum value maps directly to the property index used in native DirectShow APIs and the corresponding duvc-ctl constants. See `camera.h`, `capability.h`, and `constants.h` for full code listings.

***

### 16.2 Error Code Reference

- **Common duvc-ctl Error Codes**:
    - `E_NOTIMPL`: Operation not implemented on this platform or device.
    - `E_FAIL`: General DirectShow or Windows error, see decoded HRESULT.
    - `E_PROPERTY_UNSUPPORTED`: Queried property is not supported by the camera hardware.
    - `E_DEVICE_NOT_FOUND`: No matching device found.
    - `E_INVALID_ARG`: An API was called with an invalid argument or out-of-range value.

All error handling goes through duvc-ctl’s typed `Result<T>` and `Error` objects, which also retain decoded Windows HRESULT, details, and (where possible) string diagnostics for troubleshooting. Refer to `result.h` and error handling snippets for API usage.

***

### 16.3 GUID Reference

- **DirectShow Class and Interface GUIDs**
    - `CLSID_SystemDeviceEnum`
    - `CLSID_VideoInputDeviceCategory`
    - `IID_IAMCameraControl`: `{C6E13370-30AC-11d0-A18C-00A0C9118956}`
    - `IID_IAMVideoProcAmp`: `{C6E13360-30AC-11d0-A18C-00A0C9118956}`
    - `IID_IKsPropertySet`: `{31efac30-515c-11d0-a9aa-00aa0061be93}`

These GUIDs are defined in `windows_internal.h` and core implementation files and are required for COM interface acquisition and property control calls.

***

### 16.4 Glossary

- **UVC**: USB Video Class, the industry standard for USB camera communication and control.
- **DirectShow**: Microsoft’s legacy multimedia framework/APIs for media capture, processing, and streaming on Windows.
- **COM**: Component Object Model; Windows technology underpinning all DirectShow interfaces.
- **IAMCameraControl/IAMVideoProcAmp**: DirectShow interfaces for adjusting camera/video properties.
- **Vendor Extension**: Device-specific controls not defined by the UVC spec, such as Logitech’s FaceTracking.
- **HRESULT**: Standard Windows error/status code used by COM and API calls, convertible to codes and messages in duvc-ctl results.
- **GUID**: Globally unique identifier, a 128-bit value identifying COM interfaces and DirectShow categories.

All terminology aligns with the Windows SDK, UVC spec, or something called common sense