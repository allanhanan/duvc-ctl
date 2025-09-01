/**
 * @file cli/main.cpp
 * @brief CLI using the new modular duvc-ctl structure
 */

#include "duvc-ctl/duvc.hpp"  // New umbrella header

#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <cwchar>
#include <optional>
#include <iomanip>
#include <thread>
#include <chrono>

#ifdef _WIN32
#include <windows.h>
#include <combaseapi.h>  // For CLSIDFromString
#include <objbase.h>  
#endif

using duvc::Device;
using duvc::CamMode;
using duvc::CamProp;
using duvc::VidProp;
using duvc::PropRange;
using duvc::PropSetting;

// Convert char** to wchar_t** for MinGW compatibility
static std::vector<std::wstring> convert_args(int argc, char** argv) {
    std::vector<std::wstring> wargs;
    wargs.reserve(argc);
    
    for (int i = 0; i < argc; ++i) {
        // Simple ASCII to wide conversion (sufficient for command-line args)
        std::wstring warg;
        for (char c : std::string(argv[i])) {
            warg += static_cast<wchar_t>(c);
        }
        wargs.push_back(std::move(warg));
    }
    return wargs;
}

static void print_usage() {
    std::wcout << L"duvc-cli - DirectShow UVC control\n"
               << L"\n"
               << L"Usage:\n"
               << L"  duvc-cli list\n"
               << L"  duvc-cli get <index> <domain> <prop>\n"
               << L"  duvc-cli set <index> <domain> <prop> <value> [auto|manual]\n"
               << L"  duvc-cli range <index> <domain> <prop>\n"
               << L"  duvc-cli monitor [seconds]  (monitor device changes)\n"
               << L"  duvc-cli status <index>     (check device connection)\n"
               << L"  duvc-cli clear-cache        (clear connection cache)\n"
#ifdef _WIN32
               << L"  duvc-cli vendor <index> <property_set_guid> <property_id> [get|set|query] [data_hex]\n"
#endif
               << L"\n"
               << L"Domains:\n"
               << L"  cam  (IAMCameraControl)\n"
               << L"  vid  (IAMVideoProcAmp)\n"
               << L"\n"
               << L"cam props: Pan,Tilt,Roll,Zoom,Exposure,Iris,Focus,ScanMode,Privacy,PanRelative,\n"
               << L"           TiltRelative,RollRelative,ZoomRelative,ExposureRelative,IrisRelative,\n"
               << L"           FocusRelative,PanTilt,PanTiltRelative,FocusSimple,DigitalZoom,\n"
               << L"           DigitalZoomRelative,BacklightCompensation,Lamp\n"
               << L"vid props: Brightness,Contrast,Hue,Saturation,Sharpness,Gamma,ColorEnable,\n"
               << L"           WhiteBalance,BacklightCompensation,Gain\n";
}

static std::optional<CamProp> parse_cam_prop(const std::wstring& s) {
    struct Map { const wchar_t* n; CamProp p; } map[] = {
        {L"Pan",CamProp::Pan},{L"Tilt",CamProp::Tilt},{L"Roll",CamProp::Roll},{L"Zoom",CamProp::Zoom},
        {L"Exposure",CamProp::Exposure},{L"Iris",CamProp::Iris},{L"Focus",CamProp::Focus},
        {L"ScanMode",CamProp::ScanMode},{L"Privacy",CamProp::Privacy},
        {L"PanRelative",CamProp::PanRelative},{L"TiltRelative",CamProp::TiltRelative},
        {L"RollRelative",CamProp::RollRelative},{L"ZoomRelative",CamProp::ZoomRelative},
        {L"ExposureRelative",CamProp::ExposureRelative},{L"IrisRelative",CamProp::IrisRelative},
        {L"FocusRelative",CamProp::FocusRelative},{L"PanTilt",CamProp::PanTilt},
        {L"PanTiltRelative",CamProp::PanTiltRelative},{L"FocusSimple",CamProp::FocusSimple},
        {L"DigitalZoom",CamProp::DigitalZoom},{L"DigitalZoomRelative",CamProp::DigitalZoomRelative},
        {L"BacklightCompensation",CamProp::BacklightCompensation},{L"Lamp",CamProp::Lamp}
    };
    for (auto& m : map) if (_wcsicmp(s.c_str(), m.n) == 0) return m.p;
    return std::nullopt;
}

static std::optional<VidProp> parse_vid_prop(const std::wstring& s) {
    struct Map { const wchar_t* n; VidProp p; } map[] = {
        {L"Brightness",VidProp::Brightness},{L"Contrast",VidProp::Contrast},{L"Hue",VidProp::Hue},
        {L"Saturation",VidProp::Saturation},{L"Sharpness",VidProp::Sharpness},{L"Gamma",VidProp::Gamma},
        {L"ColorEnable",VidProp::ColorEnable},{L"WhiteBalance",VidProp::WhiteBalance},
        {L"BacklightCompensation",VidProp::BacklightCompensation},{L"Gain",VidProp::Gain}
    };
    for (auto& m : map) if (_wcsicmp(s.c_str(), m.n) == 0) return m.p;
    return std::nullopt;
}

static std::optional<CamMode> parse_mode(const std::wstring& s) {
    if (_wcsicmp(s.c_str(), L"auto") == 0) return CamMode::Auto;
    if (_wcsicmp(s.c_str(), L"manual") == 0) return CamMode::Manual;
    return std::nullopt;
}

static bool is_cam_domain(const std::wstring& s) {
    return _wcsicmp(s.c_str(), L"cam") == 0;
}
static bool is_vid_domain(const std::wstring& s) {
    return _wcsicmp(s.c_str(), L"vid") == 0;
}

#ifdef _WIN32
// Helper function to parse GUID from string
static std::optional<GUID> parse_guid(const std::wstring& guid_str) {
    GUID guid;
    std::wstring formatted = guid_str;
    
    // Add braces if not present
    if (formatted.front() != L'{') {
        formatted = L"{" + formatted;
    }
    if (formatted.back() != L'}') {
        formatted = formatted + L"}";
    }
    
    if (SUCCEEDED(CLSIDFromString(formatted.c_str(), &guid))) {
        return guid;
    }
    return std::nullopt;
}

// Helper function to convert hex string to bytes
static std::vector<uint8_t> hex_to_bytes(const std::wstring& hex_str) {
    std::vector<uint8_t> bytes;
    for (size_t i = 0; i < hex_str.length(); i += 2) {
        std::wstring byte_str = hex_str.substr(i, 2);
        uint8_t byte = static_cast<uint8_t>(std::wcstoul(byte_str.c_str(), nullptr, 16));
        bytes.push_back(byte);
    }
    return bytes;
}

// Helper function to convert bytes to hex string
static std::wstring bytes_to_hex(const std::vector<uint8_t>& bytes) {
    std::wostringstream oss;
    oss << std::hex << std::uppercase << std::setfill(L'0');
    for (uint8_t byte : bytes) {
        oss << std::setw(2) << static_cast<int>(byte);
    }
    return oss.str();
}
#endif

// Device change callback for monitoring
static void on_device_change(bool added, const std::wstring& device_path) {
    if (added) {
        std::wcout << L"[DEVICE ADDED] " << device_path << L"\n";
    } else {
        std::wcout << L"[DEVICE REMOVED] " << device_path << L"\n";
    }
    std::wcout.flush();
}

int main(int argc, char** argv) {
    // Convert arguments to wide strings for compatibility
    auto wargs = convert_args(argc, argv);
    std::vector<const wchar_t*> wargv;
    for (const auto& arg : wargs) {
        wargv.push_back(arg.c_str());
    }

    if (argc < 2) {
        print_usage();
        return 1;
    }

    std::wstring cmd = wargv[1];

    if (_wcsicmp(cmd.c_str(), L"list") == 0) {
        auto devices = duvc::list_devices();
        std::wcout << L"Devices: " << devices.size() << L"\n";
        for (size_t i = 0; i < devices.size(); ++i) {
            std::wcout << L"[" << i << L"] " << devices[i].name << L"\n    " << devices[i].path << L"\n";
        }
        return 0;
    }

    if (_wcsicmp(cmd.c_str(), L"monitor") == 0) {
        int duration = 30; // default 30 seconds
        if (argc >= 3) {
            duration = _wtoi(wargv[2]);
        }
        
        std::wcout << L"Monitoring device changes for " << duration << L" seconds...\n";
        std::wcout << L"Press Ctrl+C to stop early.\n\n";
        
        duvc::register_device_change_callback(on_device_change);
        
        // Monitor for specified duration
        std::this_thread::sleep_for(std::chrono::seconds(duration));
        
        duvc::unregister_device_change_callback();
        std::wcout << L"\nMonitoring stopped.\n";
        return 0;
    }

    if (_wcsicmp(cmd.c_str(), L"status") == 0) {
        if (argc < 3) { print_usage(); return 1; }
        int index = _wtoi(wargv[2]);
        
        auto devices = duvc::list_devices();
        if (index < 0 || index >= static_cast<int>(devices.size())) {
            std::wcerr << L"Invalid device index.\n";
            return 2;
        }
        
        bool connected = duvc::is_device_connected(devices[index]);
        std::wcout << L"Device [" << index << L"] " << devices[index].name 
                   << L" is " << (connected ? L"CONNECTED" : L"DISCONNECTED") << L"\n";
        return 0;
    }

    if (_wcsicmp(cmd.c_str(), L"clear-cache") == 0) {
        duvc::clear_connection_cache();
        std::wcout << L"Connection cache cleared.\n";
        return 0;
    }

#ifdef _WIN32
    if (_wcsicmp(cmd.c_str(), L"vendor") == 0) {
        if (argc < 5) { print_usage(); return 1; }
        
        int index = _wtoi(wargv[2]);
        std::wstring guid_str = wargv[3];
        ULONG property_id = static_cast<ULONG>(_wtoi(wargv[4]));
        std::wstring operation = (argc >= 6) ? wargv[5] : L"get";
        
        auto devices = duvc::list_devices();
        if (index < 0 || index >= static_cast<int>(devices.size())) {
            std::wcerr << L"Invalid device index.\n";
            return 2;
        }
        
        auto guid = parse_guid(guid_str);
        if (!guid) {
            std::wcerr << L"Invalid GUID format.\n";
            return 3;
        }
        
        if (_wcsicmp(operation.c_str(), L"get") == 0) {
            std::vector<uint8_t> data;
            if (duvc::get_vendor_property(devices[index], *guid, property_id, data)) {
                std::wcout << L"Vendor property data: " << bytes_to_hex(data) << L"\n";
            } else {
                std::wcerr << L"Failed to get vendor property.\n";
                return 4;
            }
        } else if (_wcsicmp(operation.c_str(), L"set") == 0) {
            if (argc < 7) {
                std::wcerr << L"Data required for set operation.\n";
                return 3;
            }
            std::wstring hex_data = wargv[6];
            auto data = hex_to_bytes(hex_data);
            
            if (duvc::set_vendor_property(devices[index], *guid, property_id, data)) {
                std::wcout << L"Vendor property set successfully.\n";
            } else {
                std::wcerr << L"Failed to set vendor property.\n";
                return 4;
            }
        } else if (_wcsicmp(operation.c_str(), L"query") == 0) {
            bool supported = duvc::query_vendor_property_support(devices[index], *guid, property_id);
            std::wcout << L"Vendor property " << (supported ? L"SUPPORTED" : L"NOT SUPPORTED") << L"\n";
        } else {
            std::wcerr << L"Invalid vendor operation. Use get, set, or query.\n";
            return 3;
        }
        return 0;
    }
#endif

    if (_wcsicmp(cmd.c_str(), L"get") == 0) {
        if (argc < 5) { print_usage(); return 1; }
        int index = _wtoi(wargv[2]);
        std::wstring domain = wargv[3];
        std::wstring propName = wargv[4];

        auto devices = duvc::list_devices();
        if (index < 0 || index >= static_cast<int>(devices.size())) {
            std::wcerr << L"Invalid device index.\n";
            return 2;
        }

        if (is_cam_domain(domain)) {
            auto p = parse_cam_prop(propName);
            if (!p) { std::wcerr << L"Unknown cam prop.\n"; return 3; }
            PropSetting s{};
            if (!duvc::get(devices[index], *p, s)) {
                std::wcerr << L"Property not supported or failed to read.\n"; return 4;
            }
            std::wcout << duvc::to_wstring(*p) << L" = " << s.value << L" (" << duvc::to_wstring(s.mode) << L")\n";
            return 0;
        } else if (is_vid_domain(domain)) {
            auto p = parse_vid_prop(propName);
            if (!p) { std::wcerr << L"Unknown vid prop.\n"; return 3; }
            PropSetting s{};
            if (!duvc::get(devices[index], *p, s)) {
                std::wcerr << L"Property not supported or failed to read.\n"; return 4;
            }
            std::wcout << duvc::to_wstring(*p) << L" = " << s.value << L" (" << duvc::to_wstring(s.mode) << L")\n";
            return 0;
        } else {
            std::wcerr << L"Unknown domain. Use cam or vid.\n";
            return 3;
        }
    }

    if (_wcsicmp(cmd.c_str(), L"set") == 0) {
        if (argc < 6) { print_usage(); return 1; }
        int index = _wtoi(wargv[2]);
        std::wstring domain = wargv[3];
        std::wstring propName = wargv[4];
        int value = _wtoi(wargv[5]);
        CamMode mode = CamMode::Manual;
        if (argc >= 7) {
            auto m = parse_mode(wargv[6]);
            if (!m) { std::wcerr << L"Mode must be auto or manual.\n"; return 3; }
            mode = *m;
        }

        auto devices = duvc::list_devices();
        if (index < 0 || index >= static_cast<int>(devices.size())) {
            std::wcerr << L"Invalid device index.\n";
            return 2;
        }

        if (is_cam_domain(domain)) {
            auto p = parse_cam_prop(propName);
            if (!p) { std::wcerr << L"Unknown cam prop.\n"; return 3; }
            PropSetting s{ value, mode };
            if (!duvc::set(devices[index], *p, s)) {
                std::wcerr << L"Failed to set property.\n"; return 4;
            }
            std::wcout << L"OK\n";
            return 0;
        } else if (is_vid_domain(domain)) {
            auto p = parse_vid_prop(propName);
            if (!p) { std::wcerr << L"Unknown vid prop.\n"; return 3; }
            PropSetting s{ value, mode };
            if (!duvc::set(devices[index], *p, s)) {
                std::wcerr << L"Failed to set property.\n"; return 4;
            }
            std::wcout << L"OK\n";
            return 0;
        } else {
            std::wcerr << L"Unknown domain. Use cam or vid.\n";
            return 3;
        }
    }

    if (_wcsicmp(cmd.c_str(), L"range") == 0) {
        if (argc < 5) { print_usage(); return 1; }
        int index = _wtoi(wargv[2]);
        std::wstring domain = wargv[3];
        std::wstring propName = wargv[4];

        auto devices = duvc::list_devices();
        if (index < 0 || index >= static_cast<int>(devices.size())) {
            std::wcerr << L"Invalid device index.\n";
            return 2;
        }

        PropRange r{};
        if (is_cam_domain(domain)) {
            auto p = parse_cam_prop(propName);
            if (!p) { std::wcerr << L"Unknown cam prop.\n"; return 3; }
            if (!duvc::get_range(devices[index], *p, r)) {
                std::wcerr << L"Range not available.\n"; return 4;
            }
            std::wcout << duvc::to_wstring(*p) << L": min=" << r.min << L", max=" << r.max
                       << L", step=" << r.step << L", default=" << r.default_val
                       << L", mode=" << duvc::to_wstring(r.default_mode) << L"\n";
            return 0;
        } else if (is_vid_domain(domain)) {
            auto p = parse_vid_prop(propName);
            if (!p) { std::wcerr << L"Unknown vid prop.\n"; return 3; }
            if (!duvc::get_range(devices[index], *p, r)) {
                std::wcerr << L"Range not available.\n"; return 4;
            }
            std::wcout << duvc::to_wstring(*p) << L": min=" << r.min << L", max=" << r.max
                       << L", step=" << r.step << L", default=" << r.default_val
                       << L", mode=" << duvc::to_wstring(r.default_mode) << L"\n";
            return 0;
        } else {
            std::wcerr << L"Unknown domain. Use cam or vid.\n";
            return 3;
        }
    }

    print_usage();
    return 1;
}
