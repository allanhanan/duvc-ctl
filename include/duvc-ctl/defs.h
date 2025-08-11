#pragma once

#include <string>

namespace duvc {

enum class CamProp {
    Pan, Tilt, Roll, Zoom, Exposure, Iris, Focus,
    ScanMode, Privacy,
    PanRelative, TiltRelative, RollRelative, ZoomRelative,
    ExposureRelative, IrisRelative, FocusRelative,
    PanTilt, PanTiltRelative, FocusSimple,
    DigitalZoom, DigitalZoomRelative,
    BacklightCompensation, Lamp
};

enum class VidProp {
    Brightness, Contrast, Hue, Saturation,
    Sharpness, Gamma, ColorEnable, WhiteBalance,
    BacklightCompensation, Gain
};

enum class CamMode { Auto, Manual };

struct PropSetting {
    int value;
    CamMode mode;
};

struct PropRange {
    int min;
    int max;
    int step;
    int default_val;
    CamMode default_mode;
};

struct Device {
    std::wstring name;
    std::wstring path;
};

}
// namespace duvc
