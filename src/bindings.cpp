#include "duvc-ctl/core.h"
#include <vector>
#include <mutex>

#ifdef _WIN32
#define DUVCC_API __declspec(dllexport)
#else
#define DUVCC_API
#endif

extern "C" {

// Thread-safe device management
static std::mutex g_devices_mutex;
static std::vector<duvc::Device> g_devices;

DUVCC_API void duvc_refresh_devices() {
    std::lock_guard<std::mutex> lock(g_devices_mutex);
    g_devices = duvc::list_devices();
}

DUVCC_API int duvc_get_device_count() {
    std::lock_guard<std::mutex> lock(g_devices_mutex);
    if (g_devices.empty()) {
        g_devices = duvc::list_devices();
    }
    return static_cast<int>(g_devices.size());
}

DUVCC_API const wchar_t* duvc_get_device_name(int index) {
    std::lock_guard<std::mutex> lock(g_devices_mutex);
    if (g_devices.empty()) {
        g_devices = duvc::list_devices();
    }
    if (index < 0 || index >= static_cast<int>(g_devices.size())) return nullptr;
    return g_devices[index].name.c_str();
}

DUVCC_API const wchar_t* duvc_get_device_path(int index) {
    std::lock_guard<std::mutex> lock(g_devices_mutex);
    if (g_devices.empty()) {
        g_devices = duvc::list_devices();
    }
    if (index < 0 || index >= static_cast<int>(g_devices.size())) return nullptr;
    return g_devices[index].path.c_str();
}

DUVCC_API int duvc_is_device_connected(int index) {
    std::lock_guard<std::mutex> lock(g_devices_mutex);
    if (g_devices.empty()) {
        g_devices = duvc::list_devices();
    }
    if (index < 0 || index >= static_cast<int>(g_devices.size())) return 0;
    return duvc::is_device_connected(g_devices[index]) ? 1 : 0;
}

DUVCC_API void duvc_clear_cache() {
    duvc::clear_connection_cache();
}

DUVCC_API int duvc_cam_get_range(int index, int camProp, int* outMin, int* outMax, int* outStep, int* outDef, int* outModeAuto) {
    std::lock_guard<std::mutex> lock(g_devices_mutex);
    if (g_devices.empty()) {
        g_devices = duvc::list_devices();
    }
    if (index < 0 || index >= static_cast<int>(g_devices.size())) return 0;
    duvc::PropRange r{};
    if (!duvc::get_range(g_devices[index], static_cast<duvc::CamProp>(camProp), r)) return 0;
    if (outMin) *outMin = r.min;
    if (outMax) *outMax = r.max;
    if (outStep) *outStep = r.step;
    if (outDef) *outDef = r.default_val;
    if (outModeAuto) *outModeAuto = (r.default_mode == duvc::CamMode::Auto) ? 1 : 0;
    return 1;
}

DUVCC_API int duvc_cam_get(int index, int camProp, int* outValue, int* outModeAuto) {
    std::lock_guard<std::mutex> lock(g_devices_mutex);
    if (g_devices.empty()) {
        g_devices = duvc::list_devices();
    }
    if (index < 0 || index >= static_cast<int>(g_devices.size())) return 0;
    duvc::PropSetting s{};
    if (!duvc::get(g_devices[index], static_cast<duvc::CamProp>(camProp), s)) return 0;
    if (outValue) *outValue = s.value;
    if (outModeAuto) *outModeAuto = (s.mode == duvc::CamMode::Auto) ? 1 : 0;
    return 1;
}

DUVCC_API int duvc_cam_set(int index, int camProp, int value, int modeAuto) {
    std::lock_guard<std::mutex> lock(g_devices_mutex);
    if (g_devices.empty()) {
        g_devices = duvc::list_devices();
    }
    if (index < 0 || index >= static_cast<int>(g_devices.size())) return 0;
    duvc::PropSetting s{ value, modeAuto ? duvc::CamMode::Auto : duvc::CamMode::Manual };
    return duvc::set(g_devices[index], static_cast<duvc::CamProp>(camProp), s) ? 1 : 0;
}

// VideoProcAmp domain
DUVCC_API int duvc_vid_get_range(int index, int vidProp, int* outMin, int* outMax, int* outStep, int* outDef, int* outModeAuto) {
    std::lock_guard<std::mutex> lock(g_devices_mutex);
    if (g_devices.empty()) {
        g_devices = duvc::list_devices();
    }
    if (index < 0 || index >= static_cast<int>(g_devices.size())) return 0;
    duvc::PropRange r{};
    if (!duvc::get_range(g_devices[index], static_cast<duvc::VidProp>(vidProp), r)) return 0;
    if (outMin) *outMin = r.min;
    if (outMax) *outMax = r.max;
    if (outStep) *outStep = r.step;
    if (outDef) *outDef = r.default_val;
    if (outModeAuto) *outModeAuto = (r.default_mode == duvc::CamMode::Auto) ? 1 : 0;
    return 1;
}

DUVCC_API int duvc_vid_get(int index, int vidProp, int* outValue, int* outModeAuto) {
    std::lock_guard<std::mutex> lock(g_devices_mutex);
    if (g_devices.empty()) {
        g_devices = duvc::list_devices();
    }
    if (index < 0 || index >= static_cast<int>(g_devices.size())) return 0;
    duvc::PropSetting s{};
    if (!duvc::get(g_devices[index], static_cast<duvc::VidProp>(vidProp), s)) return 0;
    if (outValue) *outValue = s.value;
    if (outModeAuto) *outModeAuto = (s.mode == duvc::CamMode::Auto) ? 1 : 0;
    return 1;
}

DUVCC_API int duvc_vid_set(int index, int vidProp, int value, int modeAuto) {
    std::lock_guard<std::mutex> lock(g_devices_mutex);
    if (g_devices.empty()) {
        g_devices = duvc::list_devices();
    }
    if (index < 0 || index >= static_cast<int>(g_devices.size())) return 0;
    duvc::PropSetting s{ value, modeAuto ? duvc::CamMode::Auto : duvc::CamMode::Manual };
    return duvc::set(g_devices[index], static_cast<duvc::VidProp>(vidProp), s) ? 1 : 0;
}

} // extern "C"
