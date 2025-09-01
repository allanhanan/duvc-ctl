/**
 * @file string_conversion.cpp
 * @brief String conversion utilities implementation
 */

#include <duvc-ctl/utils/string_conversion.h>

namespace duvc {

const char* to_string(CamProp p) {
    switch (p) {
        case CamProp::Pan: return "Pan";
        case CamProp::Tilt: return "Tilt";
        case CamProp::Roll: return "Roll";
        case CamProp::Zoom: return "Zoom";
        case CamProp::Exposure: return "Exposure";
        case CamProp::Iris: return "Iris";
        case CamProp::Focus: return "Focus";
        case CamProp::ScanMode: return "ScanMode";
        case CamProp::Privacy: return "Privacy";
        case CamProp::PanRelative: return "PanRelative";
        case CamProp::TiltRelative: return "TiltRelative";
        case CamProp::RollRelative: return "RollRelative";
        case CamProp::ZoomRelative: return "ZoomRelative";
        case CamProp::ExposureRelative: return "ExposureRelative";
        case CamProp::IrisRelative: return "IrisRelative";
        case CamProp::FocusRelative: return "FocusRelative";
        case CamProp::PanTilt: return "PanTilt";
        case CamProp::PanTiltRelative: return "PanTiltRelative";
        case CamProp::FocusSimple: return "FocusSimple";
        case CamProp::DigitalZoom: return "DigitalZoom";
        case CamProp::DigitalZoomRelative: return "DigitalZoomRelative";
        case CamProp::BacklightCompensation: return "BacklightCompensation";
        case CamProp::Lamp: return "Lamp";
        default: return "Unknown";
    }
}

const char* to_string(VidProp p) {
    switch (p) {
        case VidProp::Brightness: return "Brightness";
        case VidProp::Contrast: return "Contrast";
        case VidProp::Hue: return "Hue";
        case VidProp::Saturation: return "Saturation";
        case VidProp::Sharpness: return "Sharpness";
        case VidProp::Gamma: return "Gamma";
        case VidProp::ColorEnable: return "ColorEnable";
        case VidProp::WhiteBalance: return "WhiteBalance";
        case VidProp::BacklightCompensation: return "BacklightCompensation";
        case VidProp::Gain: return "Gain";
        default: return "Unknown";
    }
}

const char* to_string(CamMode m) {
    return (m == CamMode::Auto) ? "AUTO" : "MANUAL";
}

const wchar_t* to_wstring(CamProp p) {
    switch (p) {
        case CamProp::Pan: return L"Pan";
        case CamProp::Tilt: return L"Tilt";
        case CamProp::Roll: return L"Roll";
        case CamProp::Zoom: return L"Zoom";
        case CamProp::Exposure: return L"Exposure";
        case CamProp::Iris: return L"Iris";
        case CamProp::Focus: return L"Focus";
        case CamProp::ScanMode: return L"ScanMode";
        case CamProp::Privacy: return L"Privacy";
        case CamProp::PanRelative: return L"PanRelative";
        case CamProp::TiltRelative: return L"TiltRelative";
        case CamProp::RollRelative: return L"RollRelative";
        case CamProp::ZoomRelative: return L"ZoomRelative";
        case CamProp::ExposureRelative: return L"ExposureRelative";
        case CamProp::IrisRelative: return L"IrisRelative";
        case CamProp::FocusRelative: return L"FocusRelative";
        case CamProp::PanTilt: return L"PanTilt";
        case CamProp::PanTiltRelative: return L"PanTiltRelative";
        case CamProp::FocusSimple: return L"FocusSimple";
        case CamProp::DigitalZoom: return L"DigitalZoom";
        case CamProp::DigitalZoomRelative: return L"DigitalZoomRelative";
        case CamProp::BacklightCompensation: return L"BacklightCompensation";
        case CamProp::Lamp: return L"Lamp";
        default: return L"Unknown";
    }
}

const wchar_t* to_wstring(VidProp p) {
    switch (p) {
        case VidProp::Brightness: return L"Brightness";
        case VidProp::Contrast: return L"Contrast";
        case VidProp::Hue: return L"Hue";
        case VidProp::Saturation: return L"Saturation";
        case VidProp::Sharpness: return L"Sharpness";
        case VidProp::Gamma: return L"Gamma";
        case VidProp::ColorEnable: return L"ColorEnable";
        case VidProp::WhiteBalance: return L"WhiteBalance";
        case VidProp::BacklightCompensation: return L"BacklightCompensation";
        case VidProp::Gain: return L"Gain";
        default: return L"Unknown";
    }
}

const wchar_t* to_wstring(CamMode m) {
    return (m == CamMode::Auto) ? L"AUTO" : L"MANUAL";
}

} // namespace duvc
