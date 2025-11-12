/**
 * @file cli/main.cpp
 * @brief Enhanced CLI with batch operations, JSON output, verbose diagnostics,
 *        validation, reset, snapshot, and explicit relative value control
 */

#include "duvc-ctl/duvc.hpp"
#include <algorithm>
#include <chrono>
#include <ctime>
#include <cwctype>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#ifdef _WIN32
#include <wchar.h>
#include <windows.h>
#pragma warning(disable : 4996)
#endif

using duvc::Camera;
using duvc::CamMode;
using duvc::CamProp;
using duvc::Device;
using duvc::PropRange;
using duvc::PropSetting;
using duvc::VidProp;

// ============================================================================
// GLOBAL STATE
// ============================================================================

enum class Verbosity { QUIET, NORMAL, VERBOSE };
enum class OutputFormat { TEXT, JSON };

struct CLIFlags {
  Verbosity verbosity = Verbosity::NORMAL;
  OutputFormat format = OutputFormat::TEXT;
};

static CLIFlags g_flags;

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

static std::vector<std::wstring> convert_args(int argc, char **argv) {
  std::vector<std::wstring> wargs;
  wargs.reserve(argc);
  for (int i = 0; i < argc; ++i) {
    std::wstring warg;
    for (char c : std::string(argv[i]))
      warg += static_cast<wchar_t>(c);
    wargs.push_back(std::move(warg));
  }
  return wargs;
}

static std::vector<std::wstring> split_string(const std::wstring &str,
                                              wchar_t delim) {
  std::vector<std::wstring> tokens;
  std::wstringstream ss(str);
  std::wstring token;
  while (std::getline(ss, token, delim)) {
    if (!token.empty())
      tokens.push_back(token);
  }
  return tokens;
}

static bool starts_with(const std::wstring &str, const std::wstring &prefix) {
  return str.size() >= prefix.size() &&
         str.compare(0, prefix.size(), prefix) == 0;
}

static void log_verbose(const std::wstring &msg) {
  if (g_flags.verbosity >= Verbosity::VERBOSE) {
    std::wcerr << L"[VERBOSE] " << msg << L"\n";
  }
}

static void log_error(const std::wstring &msg) {
  if (g_flags.verbosity >= Verbosity::QUIET) {
    std::wcerr << L"Error: " << msg << L"\n";
  }
}

static std::wstring json_escape(const std::wstring &str) {
  std::wstring result;
  for (wchar_t ch : str) {
    switch (ch) {
    case L'"':
      result += L"\\\"";
      break;
    case L'\\':
      result += L"\\\\";
      break;
    case L'\n':
      result += L"\\n";
      break;
    case L'\r':
      result += L"\\r";
      break;
    case L'\t':
      result += L"\\t";
      break;
    default:
      result += ch;
    }
  }
  return result;
}

// ============================================================================
// PROPERTY PARSING
// ============================================================================

struct PropertyMap {
  const wchar_t *name;
  CamProp prop;
};
static constexpr PropertyMap CAM_PROP_MAP[] = {
    {L"Pan", CamProp::Pan},
    {L"Tilt", CamProp::Tilt},
    {L"Roll", CamProp::Roll},
    {L"Zoom", CamProp::Zoom},
    {L"Exposure", CamProp::Exposure},
    {L"Iris", CamProp::Iris},
    {L"Focus", CamProp::Focus},
    {L"ScanMode", CamProp::ScanMode},
    {L"Privacy", CamProp::Privacy},
    {L"PanRelative", CamProp::PanRelative},
    {L"TiltRelative", CamProp::TiltRelative},
    {L"RollRelative", CamProp::RollRelative},
    {L"ZoomRelative", CamProp::ZoomRelative},
    {L"ExposureRelative", CamProp::ExposureRelative},
    {L"IrisRelative", CamProp::IrisRelative},
    {L"FocusRelative", CamProp::FocusRelative},
    {L"PanTilt", CamProp::PanTilt},
    {L"PanTiltRelative", CamProp::PanTiltRelative},
    {L"FocusSimple", CamProp::FocusSimple},
    {L"DigitalZoom", CamProp::DigitalZoom},
    {L"DigitalZoomRelative", CamProp::DigitalZoomRelative},
    {L"BacklightCompensation", CamProp::BacklightCompensation},
    {L"Lamp", CamProp::Lamp}};

struct VideoPropertyMap {
  const wchar_t *name;
  VidProp prop;
};
static constexpr VideoPropertyMap VID_PROP_MAP[] = {
    {L"Brightness", VidProp::Brightness},
    {L"Contrast", VidProp::Contrast},
    {L"Hue", VidProp::Hue},
    {L"Saturation", VidProp::Saturation},
    {L"Sharpness", VidProp::Sharpness},
    {L"Gamma", VidProp::Gamma},
    {L"ColorEnable", VidProp::ColorEnable},
    {L"WhiteBalance", VidProp::WhiteBalance},
    {L"BacklightCompensation", VidProp::BacklightCompensation},
    {L"Gain", VidProp::Gain}};

static std::optional<CamProp> parse_cam_prop(const std::wstring &s) {
  for (auto &m : CAM_PROP_MAP)
    if (_wcsicmp(s.c_str(), m.name) == 0)
      return m.prop;
  return std::nullopt;
}

static std::optional<VidProp> parse_vid_prop(const std::wstring &s) {
  for (auto &m : VID_PROP_MAP)
    if (_wcsicmp(s.c_str(), m.name) == 0)
      return m.prop;
  return std::nullopt;
}

static std::optional<CamMode> parse_mode(const std::wstring &s) {
  if (_wcsicmp(s.c_str(), L"auto") == 0)
    return CamMode::Auto;
  if (_wcsicmp(s.c_str(), L"manual") == 0)
    return CamMode::Manual;
  return std::nullopt;
}

static bool is_cam_domain(const std::wstring &s) {
  return _wcsicmp(s.c_str(), L"cam") == 0;
}
static bool is_vid_domain(const std::wstring &s) {
  return _wcsicmp(s.c_str(), L"vid") == 0;
}

static std::optional<CamProp> get_relative_cam_prop(CamProp base) {
  switch (base) {
  case CamProp::Pan:
    return CamProp::PanRelative;
  case CamProp::Tilt:
    return CamProp::TiltRelative;
  case CamProp::Roll:
    return CamProp::RollRelative;
  case CamProp::Zoom:
    return CamProp::ZoomRelative;
  case CamProp::Exposure:
    return CamProp::ExposureRelative;
  case CamProp::Iris:
    return CamProp::IrisRelative;
  case CamProp::Focus:
    return CamProp::FocusRelative;
  case CamProp::DigitalZoom:
    return CamProp::DigitalZoomRelative;
  default:
    return std::nullopt;
  }
}

// ============================================================================
// PROPERTY VALIDATION
// ============================================================================

static bool validate_value(int value, const PropRange &range,
                           std::wstring &error_msg) {
  if (value < range.min || value > range.max) {
    std::wostringstream oss;
    oss << L"Value " << value << L" out of range [" << range.min << L", "
        << range.max << L"]";
    error_msg = oss.str();
    return false;
  }

  if (range.step != 0 && (value - range.min) % range.step != 0) {
    std::wostringstream oss;
    oss << L"Value " << value << L" invalid (step=" << range.step << L"). ";

    int lower = range.min + ((value - range.min) / range.step) * range.step;
    int upper = lower + range.step;
    if (upper <= range.max) {
      oss << L"Try " << lower << L" or " << upper;
    } else {
      oss << L"Try " << lower;
    }

    error_msg = oss.str();
    return false;
  }

  return true;
}

// ============================================================================
// DEVICE CALLBACK
// ============================================================================

static void on_device_change(bool added, const std::wstring &device_path) {
  if (g_flags.format == OutputFormat::JSON) {
    std::wcout << L"{\"event\":\"" << (added ? L"added" : L"removed")
               << L"\",\"path\":\"" << json_escape(device_path) << L"\"}\n";
  } else {
    std::wcout << (added ? L"[ADDED] " : L"[REMOVED] ") << device_path << L"\n";
  }
  std::wcout.flush();
}

// ============================================================================
// COMMAND HANDLERS
// ============================================================================

static int cmd_list(const std::vector<const wchar_t *> &args) {
  bool detailed = false;

  for (size_t i = 0; i < args.size(); ++i) {
    std::wstring arg = args[i];
    if (arg == L"--detailed" || arg == L"-d") {
      detailed = true;
    }
  }

  auto devices = duvc::list_devices();

  if (g_flags.format == OutputFormat::JSON) {
    std::wcout << L"{\"devices\":[";
    for (size_t i = 0; i < devices.size(); ++i) {
      if (i > 0)
        std::wcout << L",";
      std::wcout << L"{\"index\":" << i << L",\"name\":\""
                 << json_escape(devices[i].name) << L"\"" << L",\"path\":\""
                 << json_escape(devices[i].path) << L"\"";

      if (detailed) {
        bool connected = duvc::is_device_connected(devices[i]);
        std::wcout << L",\"connected\":" << (connected ? L"true" : L"false");

        if (connected) {
          auto cam_res = duvc::open_camera(devices[i]);
          if (cam_res) {
            Camera cam = std::move(cam_res).value();
            int cam_count = 0, vid_count = 0;

            std::vector<std::wstring> cam_props, vid_props;
            for (auto &m : CAM_PROP_MAP) {
              if (cam.get_range(m.prop)) {
                cam_count++;
                cam_props.push_back(m.name);
              }
            }
            for (auto &m : VID_PROP_MAP) {
              if (cam.get_range(m.prop)) {
                vid_count++;
                vid_props.push_back(m.name);
              }
            }

            std::wcout << L",\"controls\":{\"cam\":" << cam_count
                       << L",\"vid\":" << vid_count << L"}";
            std::wcout << L",\"supported_cam\":[";
            for (size_t j = 0; j < cam_props.size(); ++j) {
              if (j > 0)
                std::wcout << L",";
              std::wcout << L"\"" << cam_props[j] << L"\"";
            }
            std::wcout << L"],\"supported_vid\":[";
            for (size_t j = 0; j < vid_props.size(); ++j) {
              if (j > 0)
                std::wcout << L",";
              std::wcout << L"\"" << vid_props[j] << L"\"";
            }
            std::wcout << L"]";
          } else {
            log_verbose(L"Failed to open camera " + std::to_wstring(i) +
                        L" for detailed scan");
          }
        }
      }

      std::wcout << L"}";
    }
    std::wcout << L"]}\n";
  } else {
    if (g_flags.verbosity >= Verbosity::NORMAL) {
      std::wcout << L"Devices: " << devices.size() << L"\n";
    }

    for (size_t i = 0; i < devices.size(); ++i) {
      std::wcout << L"[" << i << L"] " << devices[i].name << L"\n";

      if (detailed) {
        std::wcout << L"    Path: " << devices[i].path << L"\n";
        bool connected = duvc::is_device_connected(devices[i]);
        std::wcout << L"    Status: "
                   << (connected ? L"CONNECTED" : L"DISCONNECTED") << L"\n";

        if (connected) {
          auto cam_res = duvc::open_camera(devices[i]);
          if (cam_res) {
            Camera cam = std::move(cam_res).value();
            int cam_count = 0, vid_count = 0;

            std::wcout << L"    Supported properties:\n";
            std::wcout << L"      Camera: ";
            bool first_cam = true;
            for (auto &m : CAM_PROP_MAP) {
              if (cam.get_range(m.prop)) {
                if (!first_cam)
                  std::wcout << L", ";
                std::wcout << m.name;
                cam_count++;
                first_cam = false;
              }
            }
            std::wcout << L" (" << cam_count << L")\n";

            std::wcout << L"      Video: ";
            bool first_vid = true;
            for (auto &m : VID_PROP_MAP) {
              if (cam.get_range(m.prop)) {
                if (!first_vid)
                  std::wcout << L", ";
                std::wcout << m.name;
                vid_count++;
                first_vid = false;
              }
            }
            std::wcout << L" (" << vid_count << L")\n";
          } else {
            log_verbose(L"Failed to open camera for detailed scan");
            std::wcout << L"    Controls: Unable to query\n";
          }
        }
      } else if (g_flags.verbosity >= Verbosity::NORMAL) {
        std::wcout << L"    " << devices[i].path << L"\n";
      }
    }
  }

  return 0;
}

static int cmd_get(int index, const std::wstring &domain,
                   const std::vector<std::wstring> &props,
                   const std::vector<Device> &devices) {
  if (index < 0 || index >= static_cast<int>(devices.size())) {
    log_error(L"Invalid device index");
    return 2;
  }

  auto cam_res = duvc::open_camera(devices[index]);
  if (!cam_res) {
    log_error(L"Failed to open camera");
    log_verbose(L"Camera open failed for device " + std::to_wstring(index));
    return 3;
  }
  Camera cam = std::move(cam_res).value();

  bool is_cam = is_cam_domain(domain);
  bool is_vid = is_vid_domain(domain);

  if (!is_cam && !is_vid) {
    log_error(L"Invalid domain. Use 'cam' or 'vid'");
    return 3;
  }

  if (g_flags.format == OutputFormat::JSON) {
    std::wcout << L"{\"device\":" << index << L",\"domain\":\"" << domain
               << L"\"" << L",\"properties\":[";
  }

  bool first = true;
  int error_count = 0;

  for (const auto &prop_name : props) {
    if (is_cam) {
      auto p = parse_cam_prop(prop_name);
      if (!p) {
        log_error(L"Unknown camera property: " + prop_name);
        error_count++;
        continue;
      }

      auto r = cam.get(*p);
      if (!r) {
        log_verbose(L"Property not supported or read failed: " + prop_name);
        error_count++;
        continue;
      }

      auto s = r.value();

      if (g_flags.format == OutputFormat::JSON) {
        if (!first)
          std::wcout << L",";
        std::wcout << L"{\"name\":\"" << json_escape(duvc::to_wstring(*p))
                   << L"\",\"value\":" << s.value << L",\"mode\":\""
                   << duvc::to_wstring(s.mode) << L"\"}";
        first = false;
      } else {
        std::wcout << duvc::to_wstring(*p) << L"=" << s.value << L" ("
                   << duvc::to_wstring(s.mode) << L")\n";
      }
    } else {
      auto p = parse_vid_prop(prop_name);
      if (!p) {
        log_error(L"Unknown video property: " + prop_name);
        error_count++;
        continue;
      }

      auto r = cam.get(*p);
      if (!r) {
        log_verbose(L"Property not supported or read failed: " + prop_name);
        error_count++;
        continue;
      }

      auto s = r.value();

      if (g_flags.format == OutputFormat::JSON) {
        if (!first)
          std::wcout << L",";
        std::wcout << L"{\"name\":\"" << json_escape(duvc::to_wstring(*p))
                   << L"\",\"value\":" << s.value << L",\"mode\":\""
                   << duvc::to_wstring(s.mode) << L"\"}";
        first = false;
      } else {
        std::wcout << duvc::to_wstring(*p) << L"=" << s.value << L" ("
                   << duvc::to_wstring(s.mode) << L")\n";
      }
    }
  }

  if (g_flags.format == OutputFormat::JSON) {
    std::wcout << L"]}\n";
  }

  return error_count > 0 ? 4 : 0;
}

struct SetOperation {
  std::wstring prop_name;
  std::optional<int> value;
  std::optional<CamMode> mode;
  bool is_relative = false;
};

static std::optional<SetOperation>
parse_set_operation(const std::wstring &spec) {
  SetOperation op;

  size_t eq_pos = spec.find(L'=');
  if (eq_pos != std::wstring::npos) {
    op.prop_name = spec.substr(0, eq_pos);
    std::wstring value_part = spec.substr(eq_pos + 1);

    size_t colon_pos = value_part.find(L':');
    if (colon_pos != std::wstring::npos) {
      std::wstring value_str = value_part.substr(0, colon_pos);
      std::wstring mode_str = value_part.substr(colon_pos + 1);

      // No auto-detection of relative - parse as absolute value
      op.value = _wtoi(value_str.c_str());
      op.mode = parse_mode(mode_str);
    } else {
      // No auto-detection of relative - parse as absolute value
      op.value = _wtoi(value_part.c_str());
    }
  } else {
    op.prop_name = spec;
  }

  return op;
}

static int cmd_set(int index, const std::wstring &domain,
                   const std::vector<std::wstring> &set_specs,
                   const std::vector<const wchar_t *> &args, size_t start_idx,
                   const std::vector<Device> &devices,
                   bool force_relative = false) {
  (void)args;
  (void)start_idx;

  if (index < 0 || index >= static_cast<int>(devices.size())) {
    log_error(L"Invalid device index");
    return 2;
  }

  auto cam_res = duvc::open_camera(devices[index]);
  if (!cam_res) {
    log_error(L"Failed to open camera");
    log_verbose(L"Camera open failed for device " + std::to_wstring(index));
    return 3;
  }
  Camera cam = std::move(cam_res).value();

  bool is_cam = is_cam_domain(domain);
  bool is_vid = is_vid_domain(domain);

  if (!is_cam && !is_vid) {
    log_error(L"Invalid domain");
    return 3;
  }

  int error_count = 0;

  for (const auto &spec : set_specs) {
    auto op = parse_set_operation(spec);
    if (!op) {
      log_error(L"Failed to parse: " + spec);
      error_count++;
      continue;
    }

    // Handle mode-only set (no value provided)
    if (!op->value.has_value() && op->mode.has_value()) {
      if (is_cam) {
        auto p = parse_cam_prop(op->prop_name);
        if (!p) {
          log_error(L"Unknown camera property: " + op->prop_name);
          error_count++;
          continue;
        }

        auto current = cam.get(*p);
        if (!current) {
          log_error(L"Failed to get current value for: " + op->prop_name);
          log_verbose(L"Property read failed, cannot set mode-only");
          error_count++;
          continue;
        }

        PropSetting s{current.value().value, *op->mode};
        auto result = cam.set(*p, s);
        if (!result) {
          log_error(L"Failed to set mode for: " + op->prop_name);
          log_verbose(L"Set operation returned false");
          error_count++;
        } else if (g_flags.verbosity >= Verbosity::NORMAL &&
                   g_flags.format == OutputFormat::TEXT) {
          std::wcout << L"OK\n";
        }
      } else {
        auto p = parse_vid_prop(op->prop_name);
        if (!p) {
          log_error(L"Unknown video property: " + op->prop_name);
          error_count++;
          continue;
        }

        auto current = cam.get(*p);
        if (!current) {
          log_error(L"Failed to get current value for: " + op->prop_name);
          log_verbose(L"Property read failed, cannot set mode-only");
          error_count++;
          continue;
        }

        PropSetting s{current.value().value, *op->mode};
        auto result = cam.set(*p, s);
        if (!result) {
          log_error(L"Failed to set mode for: " + op->prop_name);
          log_verbose(L"Set operation returned false");
          error_count++;
        } else if (g_flags.verbosity >= Verbosity::NORMAL &&
                   g_flags.format == OutputFormat::TEXT) {
          std::wcout << L"OK\n";
        }
      }
      continue;
    }

    if (!op->value.has_value()) {
      log_error(L"No value provided for: " + op->prop_name);
      error_count++;
      continue;
    }

    int value = *op->value;
    CamMode mode = op->mode.value_or(CamMode::Manual);

    if (is_cam) {
      auto p = parse_cam_prop(op->prop_name);
      if (!p) {
        log_error(L"Unknown camera property: " + op->prop_name);
        error_count++;
        continue;
      }

      CamProp target_prop = *p;

      // If relative flag is set, calculate absolute value from current + delta
      if (force_relative || op->is_relative) {
        log_verbose(L"Relative mode: reading current value for " +
                    op->prop_name);

        auto current = cam.get(*p);
        if (!current) {
          log_error(L"Cannot apply relative change - failed to read current "
                    L"value for: " +
                    op->prop_name);
          error_count++;
          continue;
        }

        int current_val = current.value().value;
        int delta = value;
        int new_val = current_val + delta;

        // Validate the new value is in range
        auto range = cam.get_range(*p);
        if (range) {
          if (new_val < range.value().min || new_val > range.value().max) {
            log_error(op->prop_name +
                      L": Relative change would result in out-of-range value " +
                      std::to_wstring(new_val) + L" (range: [" +
                      std::to_wstring(range.value().min) + L"," +
                      std::to_wstring(range.value().max) + L"])");
            error_count++;
            continue;
          }
        }

        std::wostringstream rel_msg;
        rel_msg << L"Relative: " << op->prop_name << L" current=" << current_val
                << L" delta=" << (delta >= 0 ? L"+" : L"") << delta << L" new="
                << new_val;
        log_verbose(rel_msg.str());

        value = new_val;
        // Keep target_prop as the regular property (not *Relative)
      }

      // Validate non-relative values
      if (!force_relative && !op->is_relative) {
        auto range = cam.get_range(*p);
        if (range) {
          std::wstring error_msg;
          if (!validate_value(value, range.value(), error_msg)) {
            log_error(op->prop_name + L": " + error_msg);
            error_count++;
            continue;
          }
        } else {
          log_verbose(L"Range not available for validation: " + op->prop_name);
        }
      }

      std::wostringstream debug_msg;
      debug_msg << L"Calling cam.set(prop=" << duvc::to_wstring(target_prop)
                << L", value=" << value << L", mode=" << duvc::to_wstring(mode)
                << L")";
      log_verbose(debug_msg.str());

      PropSetting s{value, mode};
      auto result = cam.set(target_prop, s);
      if (!result) {
        log_error(L"Failed to set: " + op->prop_name);
        log_verbose(L"Set operation returned false");
        error_count++;
      } else if (g_flags.verbosity >= Verbosity::NORMAL &&
                 g_flags.format == OutputFormat::TEXT) {
        std::wcout << L"OK\n";
      }
    } else {
      auto p = parse_vid_prop(op->prop_name);
      if (!p) {
        log_error(L"Unknown video property: " + op->prop_name);
        error_count++;
        continue;
      }

      // If relative flag is set, calculate absolute value from current + delta
      if (force_relative || op->is_relative) {
        log_verbose(L"Relative mode: reading current value for " +
                    op->prop_name);

        auto current = cam.get(*p);
        if (!current) {
          log_error(L"Cannot apply relative change - failed to read current "
                    L"value for: " +
                    op->prop_name);
          error_count++;
          continue;
        }

        int current_val = current.value().value;
        int delta = value;
        int new_val = current_val + delta;

        // Validate the new value is in range
        auto range = cam.get_range(*p);
        if (range) {
          if (new_val < range.value().min || new_val > range.value().max) {
            log_error(op->prop_name +
                      L": Relative change would result in out-of-range value " +
                      std::to_wstring(new_val) + L" (range: [" +
                      std::to_wstring(range.value().min) + L"," +
                      std::to_wstring(range.value().max) + L"])");
            error_count++;
            continue;
          }
        }

        std::wostringstream rel_msg;
        rel_msg << L"Relative: " << op->prop_name << L" current=" << current_val
                << L" delta=" << (delta >= 0 ? L"+" : L"") << delta << L" new="
                << new_val;
        log_verbose(rel_msg.str());

        value = new_val;
      }

      // Validate absolute value (for non-relative or after relative
      // calculation)
      auto range = cam.get_range(*p);
      if (range) {
        std::wstring error_msg;
        if (!validate_value(value, range.value(), error_msg)) {
          log_error(op->prop_name + L": " + error_msg);
          error_count++;
          continue;
        }
      } else {
        log_verbose(L"Range not available for validation: " + op->prop_name);
      }

      PropSetting s{value, mode};
      auto result = cam.set(*p, s);

      if (!result) {
        log_error(L"Failed to set: " + op->prop_name);
        log_verbose(L"Set operation returned false");
        error_count++;
      } else if (g_flags.verbosity >= Verbosity::NORMAL &&
                 g_flags.format == OutputFormat::TEXT) {
        std::wcout << L"OK\n";
      }
    }
  }

  return error_count > 0 ? 4 : 0;
}

static int cmd_reset(int index, const std::wstring &domain,
                     const std::vector<std::wstring> &props,
                     const std::vector<Device> &devices) {
  if (index < 0 || index >= static_cast<int>(devices.size())) {
    log_error(L"Invalid device index");
    return 2;
  }

  auto cam_res = duvc::open_camera(devices[index]);
  if (!cam_res) {
    log_error(L"Failed to open camera");
    log_verbose(L"Camera open failed for device " + std::to_wstring(index));
    return 3;
  }
  Camera cam = std::move(cam_res).value();

  bool is_cam = is_cam_domain(domain);
  bool is_vid = is_vid_domain(domain);
  bool reset_all =
      (props.size() == 1 && _wcsicmp(props[0].c_str(), L"all") == 0);

  if (!is_cam && !is_vid && domain != L"all") {
    log_error(L"Invalid domain");
    return 3;
  }

  int reset_count = 0;

  if (domain == L"all") {
    for (auto &m : CAM_PROP_MAP) {
      auto range = cam.get_range(m.prop);
      if (range) {
        auto r = range.value();
        PropSetting s{r.default_val, r.default_mode};
        if (cam.set(m.prop, s)) {
          reset_count++;
          log_verbose(L"Reset " + std::wstring(m.name) + L" to default");
        }
      }
    }

    for (auto &m : VID_PROP_MAP) {
      auto range = cam.get_range(m.prop);
      if (range) {
        auto r = range.value();
        PropSetting s{r.default_val, r.default_mode};
        if (cam.set(m.prop, s)) {
          reset_count++;
          log_verbose(L"Reset " + std::wstring(m.name) + L" to default");
        }
      }
    }

    if (g_flags.verbosity >= Verbosity::NORMAL &&
        g_flags.format == OutputFormat::TEXT) {
      std::wcout << L"Reset " << reset_count << L" properties\n";
    }
    return 0;
  }

  if (is_cam) {
    if (reset_all) {
      for (auto &m : CAM_PROP_MAP) {
        auto range = cam.get_range(m.prop);
        if (range) {
          auto r = range.value();
          PropSetting s{r.default_val, r.default_mode};
          if (cam.set(m.prop, s)) {
            reset_count++;
            log_verbose(L"Reset " + std::wstring(m.name) + L" to default");
          }
        }
      }
    } else {
      for (const auto &prop_name : props) {
        auto p = parse_cam_prop(prop_name);
        if (!p) {
          log_error(L"Unknown camera property: " + prop_name);
          continue;
        }

        auto range = cam.get_range(*p);
        if (!range) {
          log_error(L"Range not available for: " + prop_name);
          log_verbose(L"Cannot reset without range information");
          continue;
        }

        auto r = range.value();
        PropSetting s{r.default_val, r.default_mode};
        if (cam.set(*p, s)) {
          reset_count++;
          log_verbose(L"Reset " + prop_name + L" to " +
                      std::to_wstring(r.default_val));
        } else {
          log_error(L"Failed to reset: " + prop_name);
        }
      }
    }
  } else if (is_vid) {
    if (reset_all) {
      for (auto &m : VID_PROP_MAP) {
        auto range = cam.get_range(m.prop);
        if (range) {
          auto r = range.value();
          PropSetting s{r.default_val, r.default_mode};
          if (cam.set(m.prop, s)) {
            reset_count++;
            log_verbose(L"Reset " + std::wstring(m.name) + L" to default");
          }
        }
      }
    } else {
      for (const auto &prop_name : props) {
        auto p = parse_vid_prop(prop_name);
        if (!p) {
          log_error(L"Unknown video property: " + prop_name);
          continue;
        }

        auto range = cam.get_range(*p);
        if (!range) {
          log_error(L"Range not available for: " + prop_name);
          log_verbose(L"Cannot reset without range information");
          continue;
        }

        auto r = range.value();
        PropSetting s{r.default_val, r.default_mode};
        if (cam.set(*p, s)) {
          reset_count++;
          log_verbose(L"Reset " + prop_name + L" to " +
                      std::to_wstring(r.default_val));
        } else {
          log_error(L"Failed to reset: " + prop_name);
        }
      }
    }
  }

  if (g_flags.verbosity >= Verbosity::NORMAL &&
      g_flags.format == OutputFormat::TEXT) {
    std::wcout << L"Reset " << reset_count << L" properties\n";
  }

  return 0;
}

static int cmd_snapshot(int index, const std::vector<Device> &devices,
                        const std::vector<const wchar_t *> &args) {
  if (index < 0 || index >= static_cast<int>(devices.size())) {
    log_error(L"Invalid device index");
    return 2;
  }

  auto cam_res = duvc::open_camera(devices[index]);
  if (!cam_res) {
    log_error(L"Failed to open camera");
    log_verbose(L"Camera open failed for device " + std::to_wstring(index));
    return 3;
  }
  Camera cam = std::move(cam_res).value();

  std::wstring output_file;
  for (size_t i = 0; i < args.size(); ++i) {
    std::wstring arg = args[i];
    if ((arg == L"-o" || arg == L"--output") && i + 1 < args.size()) {
      output_file = args[i + 1];
    }
  }

  std::wostringstream output;

  if (g_flags.format == OutputFormat::JSON) {
    output << L"{\"device\":" << index << L",\"name\":\""
           << json_escape(devices[index].name) << L"\""
           << L",\"properties\":{\"cam\":{";

    bool first_cam = true;
    for (auto &m : CAM_PROP_MAP) {
      auto val = cam.get(m.prop);
      if (val) {
        if (!first_cam)
          output << L",";
        auto v = val.value();
        output << L"\"" << m.name << L"\":{\"value\":" << v.value
               << L",\"mode\":\"" << duvc::to_wstring(v.mode) << L"\"}";
        first_cam = false;
      }
    }

    output << L"},\"vid\":{";

    bool first_vid = true;
    for (auto &m : VID_PROP_MAP) {
      auto val = cam.get(m.prop);
      if (val) {
        if (!first_vid)
          output << L",";
        auto v = val.value();
        output << L"\"" << m.name << L"\":{\"value\":" << v.value
               << L",\"mode\":\"" << duvc::to_wstring(v.mode) << L"\"}";
        first_vid = false;
      }
    }

    output << L"}}}\n";
  } else {
    for (auto &m : CAM_PROP_MAP) {
      auto val = cam.get(m.prop);
      if (val) {
        auto v = val.value();
        output << L"cam." << m.name << L"=" << v.value << L":"
               << duvc::to_wstring(v.mode) << L"\n";
      }
    }

    for (auto &m : VID_PROP_MAP) {
      auto val = cam.get(m.prop);
      if (val) {
        auto v = val.value();
        output << L"vid." << m.name << L"=" << v.value << L":"
               << duvc::to_wstring(v.mode) << L"\n";
      }
    }
  }

  if (!output_file.empty()) {
    std::wofstream file(output_file);
    if (!file) {
      log_error(L"Failed to open output file: " + output_file);
      return 4;
    }
    file << output.str();
    if (g_flags.verbosity >= Verbosity::NORMAL &&
        g_flags.format == OutputFormat::TEXT) {
      std::wcout << L"Saved to " << output_file << L"\n";
    }
  } else {
    std::wcout << output.str();
  }

  return 0;
}

static int cmd_range(int index, const std::wstring &domain,
                     const std::vector<std::wstring> &props,
                     const std::vector<Device> &devices) {
  if (index < 0 || index >= static_cast<int>(devices.size())) {
    log_error(L"Invalid device index");
    return 2;
  }

  auto cam_res = duvc::open_camera(devices[index]);
  if (!cam_res) {
    log_error(L"Failed to open camera");
    log_verbose(L"Camera open failed for device " + std::to_wstring(index));
    return 3;
  }
  Camera cam = std::move(cam_res).value();

  bool is_cam = is_cam_domain(domain);
  bool is_vid = is_vid_domain(domain);
  bool all_props =
      (props.size() == 1 && _wcsicmp(props[0].c_str(), L"all") == 0);

  if (!is_cam && !is_vid && domain != L"all") {
    log_error(L"Invalid domain");
    return 3;
  }

  if (g_flags.format == OutputFormat::JSON) {
    std::wcout << L"{\"device\":" << index << L",\"ranges\":[";
  }

  bool first = true;

  if (domain == L"all" || (is_cam && all_props)) {
    for (auto &m : CAM_PROP_MAP) {
      auto range = cam.get_range(m.prop);
      if (range) {
        auto r = range.value();
        if (g_flags.format == OutputFormat::JSON) {
          if (!first)
            std::wcout << L",";
          std::wcout << L"{\"domain\":\"cam\",\"property\":\"" << m.name
                     << L"\",\"min\":" << r.min << L",\"max\":" << r.max
                     << L",\"step\":" << r.step << L",\"default\":"
                     << r.default_val << L",\"mode\":\""
                     << duvc::to_wstring(r.default_mode) << L"\"}";
          first = false;
        } else {
          std::wcout << L"cam." << m.name << L": [" << r.min << L"," << r.max
                     << L"] step=" << r.step << L" default=" << r.default_val
                     << L" (" << duvc::to_wstring(r.default_mode) << L")\n";
        }
      }
    }
  }

  if (domain == L"all" || (is_vid && all_props)) {
    for (auto &m : VID_PROP_MAP) {
      auto range = cam.get_range(m.prop);
      if (range) {
        auto r = range.value();
        if (g_flags.format == OutputFormat::JSON) {
          if (!first)
            std::wcout << L",";
          std::wcout << L"{\"domain\":\"vid\",\"property\":\"" << m.name
                     << L"\",\"min\":" << r.min << L",\"max\":" << r.max
                     << L",\"step\":" << r.step << L",\"default\":"
                     << r.default_val << L",\"mode\":\""
                     << duvc::to_wstring(r.default_mode) << L"\"}";
          first = false;
        } else {
          std::wcout << L"vid." << m.name << L": [" << r.min << L"," << r.max
                     << L"] step=" << r.step << L" default=" << r.default_val
                     << L" (" << duvc::to_wstring(r.default_mode) << L")\n";
        }
      }
    }
  }

  if (!all_props && domain != L"all") {
    for (const auto &prop_name : props) {
      if (is_cam) {
        auto p = parse_cam_prop(prop_name);
        if (!p) {
          log_error(L"Unknown camera property: " + prop_name);
          continue;
        }

        auto range = cam.get_range(*p);
        if (!range) {
          log_error(L"Range not available for: " + prop_name);
          log_verbose(L"Property may not be supported by device");
          continue;
        }

        auto r = range.value();
        if (g_flags.format == OutputFormat::JSON) {
          if (!first)
            std::wcout << L",";
          std::wcout << L"{\"domain\":\"cam\",\"property\":\"" << prop_name
                     << L"\",\"min\":" << r.min << L",\"max\":" << r.max
                     << L",\"step\":" << r.step << L",\"default\":"
                     << r.default_val << L",\"mode\":\""
                     << duvc::to_wstring(r.default_mode) << L"\"}";
          first = false;
        } else {
          std::wcout << prop_name << L": [" << r.min << L"," << r.max
                     << L"] step=" << r.step << L" default=" << r.default_val
                     << L" (" << duvc::to_wstring(r.default_mode) << L")\n";
        }
      } else if (is_vid) {
        auto p = parse_vid_prop(prop_name);
        if (!p) {
          log_error(L"Unknown video property: " + prop_name);
          continue;
        }

        auto range = cam.get_range(*p);
        if (!range) {
          log_error(L"Range not available for: " + prop_name);
          log_verbose(L"Property may not be supported by device");
          continue;
        }

        auto r = range.value();
        if (g_flags.format == OutputFormat::JSON) {
          if (!first)
            std::wcout << L",";
          std::wcout << L"{\"domain\":\"vid\",\"property\":\"" << prop_name
                     << L"\",\"min\":" << r.min << L",\"max\":" << r.max
                     << L",\"step\":" << r.step << L",\"default\":"
                     << r.default_val << L",\"mode\":\""
                     << duvc::to_wstring(r.default_mode) << L"\"}";
          first = false;
        } else {
          std::wcout << prop_name << L": [" << r.min << L"," << r.max
                     << L"] step=" << r.step << L" default=" << r.default_val
                     << L" (" << duvc::to_wstring(r.default_mode) << L")\n";
        }
      }
    }
  }

  if (g_flags.format == OutputFormat::JSON) {
    std::wcout << L"]}\n";
  }

  return 0;
}

static int cmd_monitor(const std::vector<const wchar_t *> &args) {
  if (args.size() >= 3 && iswdigit(args[0][0])) {
    int index = _wtoi(args[0]);
    std::wstring domain = args[1];
    std::wstring prop_name = args[2];
    int interval = 1;

    for (size_t i = 3; i < args.size(); ++i) {
      std::wstring arg = args[i];
      if (starts_with(arg, L"--interval=")) {
        interval = _wtoi(arg.substr(11).c_str());
      }
    }

    auto devices = duvc::list_devices();
    if (index < 0 || index >= static_cast<int>(devices.size())) {
      log_error(L"Invalid device index");
      return 2;
    }

    auto cam_res = duvc::open_camera(devices[index]);
    if (!cam_res) {
      log_error(L"Failed to open camera");
      log_verbose(L"Camera open failed for monitoring");
      return 3;
    }
    Camera cam = std::move(cam_res).value();

    bool is_cam = is_cam_domain(domain);
    std::optional<int> last_value;
    std::optional<CamMode> last_mode;

    if (g_flags.verbosity >= Verbosity::NORMAL &&
        g_flags.format == OutputFormat::TEXT) {
      std::wcout << L"Monitoring " << prop_name << L" (interval=" << interval
                 << L"s, Ctrl+C to stop)\n";
    }

    while (true) {
      if (is_cam) {
        auto p = parse_cam_prop(prop_name);
        if (!p) {
          log_error(L"Unknown camera property");
          return 3;
        }

        auto val = cam.get(*p);
        if (val) {
          auto v = val.value();
          if (!last_value.has_value() || v.value != *last_value ||
              v.mode != *last_mode) {
            auto now = std::time(nullptr);
            auto tm = *std::localtime(&now);

            if (g_flags.format == OutputFormat::JSON) {
              std::wcout << L"{\"property\":\"" << prop_name << L"\",\"value\":"
                         << v.value << L",\"mode\":\""
                         << duvc::to_wstring(v.mode) << L"\"}\n";
            } else {
              std::wcout << L"[" << std::put_time(&tm, L"%H:%M:%S") << L"] "
                         << prop_name << L"=" << v.value << L" ("
                         << duvc::to_wstring(v.mode) << L")\n";
            }
            std::wcout.flush();

            last_value = v.value;
            last_mode = v.mode;
          }
        } else {
          log_verbose(L"Failed to read property value");
        }
      } else {
        auto p = parse_vid_prop(prop_name);
        if (!p) {
          log_error(L"Unknown video property");
          return 3;
        }

        auto val = cam.get(*p);
        if (val) {
          auto v = val.value();
          if (!last_value.has_value() || v.value != *last_value ||
              v.mode != *last_mode) {
            auto now = std::time(nullptr);
            auto tm = *std::localtime(&now);

            if (g_flags.format == OutputFormat::JSON) {
              std::wcout << L"{\"property\":\"" << prop_name << L"\",\"value\":"
                         << v.value << L",\"mode\":\""
                         << duvc::to_wstring(v.mode) << L"\"}\n";
            } else {
              std::wcout << L"[" << std::put_time(&tm, L"%H:%M:%S") << L"] "
                         << prop_name << L"=" << v.value << L" ("
                         << duvc::to_wstring(v.mode) << L")\n";
            }
            std::wcout.flush();

            last_value = v.value;
            last_mode = v.mode;
          }
        } else {
          log_verbose(L"Failed to read property value");
        }
      }

      std::this_thread::sleep_for(std::chrono::seconds(interval));
    }
  } else {
    int duration = (args.size() >= 1) ? _wtoi(args[0]) : 30;

    if (g_flags.verbosity >= Verbosity::NORMAL &&
        g_flags.format == OutputFormat::TEXT) {
      std::wcout << L"Monitoring device changes for " << duration
                 << L" seconds...\n";
    }

    duvc::register_device_change_callback(on_device_change);
    std::this_thread::sleep_for(std::chrono::seconds(duration));
    duvc::unregister_device_change_callback();

    if (g_flags.verbosity >= Verbosity::NORMAL &&
        g_flags.format == OutputFormat::TEXT) {
      std::wcout << L"Stopped\n";
    }
  }

  return 0;
}

static void print_usage() {
  std::wcout
      << L"duvc-cli - DirectShow UVC camera control\n\n"
      << L"Usage:\n"
      << L"  duvc-cli [global-flags] <command> [args...]\n\n"
      << L"Global Flags:\n"
      << L"  -v, --verbose         Verbose output with detailed errors\n"
      << L"  -q, --quiet           Minimal output (errors only)\n"
      << L"  -j, --json            Output in JSON format\n"
      << L"  -h, --help            Show this help\n\n"
      << L"Commands:\n"
      << L"  list [--detailed|-d]  List devices (--detailed shows "
         L"capabilities)\n"
      << L"  get <index> <domain> <prop>[,<prop>...]  Get property values\n"
      << L"  set [--relative|-r] <index> <domain> "
         L"<prop>=<val>[,<prop>=<val>...]  Set (batch)\n"
      << L"  set [--relative|-r] <index> <domain> <prop> <value> "
         L"[auto|manual]\n"
      << L"  set <index> <domain> <prop> <auto|manual>  Set mode only\n"
      << L"  range <index> <domain> <prop>[,<prop>...|all]  Show ranges\n"
      << L"  reset <index> <domain> <prop>[,<prop>...|all]  Reset defaults\n"
      << L"  reset <index> all     Reset all properties\n"
      << L"  snapshot <index> [-o file]  Dump all values\n"
      << L"  capabilities <index>  Show all properties\n"
      << L"  status <index>        Check connection\n"
      << L"  monitor [seconds]     Monitor device changes\n"
      << L"  monitor <index> <domain> <prop> [--interval=N]  Monitor property\n"
      << L"\nDomains: cam (camera) | vid (video)\n\n"
      << L"Relative Values:\n"
      << L"  Use --relative or -r flag with set command for relative changes:\n"
      << L"  duvc-cli set --relative 0 cam Exposure +2   # Increase by 2\n"
      << L"  duvc-cli set -r 0 cam Exposure -3           # Decrease by 3\n\n"
      << L"Camera Properties:\n"
      << L"  Pan, Tilt, Roll, Zoom, Exposure, Iris, Focus, ScanMode, Privacy,\n"
      << L"  PanRelative, TiltRelative, RollRelative, ZoomRelative, ExposureRelative, IrisRelative, FocusRelative,\n"
      << L"  PanTilt, PanTiltRelative, FocusSimple, DigitalZoom, DigitalZoomRelative,\n"
      << L"  BacklightCompensation, Lamp\n\n"
      << L"Video Properties:\n"
      << L"  Brightness, Contrast, Hue, Saturation, Sharpness, Gamma,\n"
      << L"  ColorEnable, WhiteBalance, BacklightCompensation, Gain\n\n"
      << L"Examples:\n"
      << L"  duvc-cli list --detailed\n"
      << L"  duvc-cli get 0 cam Pan,Tilt,Zoom --json\n"
      << L"  duvc-cli set 0 cam Exposure -6              # Absolute: set to "
         L"-6\n"
      << L"  duvc-cli set --relative 0 cam Exposure +2   # Relative: increase "
         L"by 2\n"
      << L"  duvc-cli set -r 0 cam Exposure -3           # Relative: decrease "
         L"by 3\n"
      << L"  duvc-cli set 0 cam Focus auto\n"
      << L"  duvc-cli reset 0 cam all\n"
      << L"  duvc-cli snapshot 0 -o backup.json --json\n"
      << L"  duvc-cli monitor 0 cam Exposure --interval=2 --verbose\n";
}

int main(int argc, char **argv) {
  auto wargs = convert_args(argc, argv);
  std::vector<const wchar_t *> wargv;
  for (const auto &a : wargs)
    wargv.push_back(a.c_str());

  if (argc < 2) {
    print_usage();
    return 1;
  }

  size_t cmd_start = 1;
  for (size_t i = 1; i < wargv.size(); ++i) {
    std::wstring arg = wargv[i];

    if (arg == L"-v" || arg == L"--verbose") {
      g_flags.verbosity = Verbosity::VERBOSE;
      cmd_start++;
    } else if (arg == L"-q" || arg == L"--quiet") {
      g_flags.verbosity = Verbosity::QUIET;
      cmd_start++;
    } else if (arg == L"-j" || arg == L"--json") {
      g_flags.format = OutputFormat::JSON;
      cmd_start++;
    } else if (arg == L"-h" || arg == L"--help") {
      print_usage();
      return 0;
    } else {
      break;
    }
  }

  if (cmd_start >= wargv.size()) {
    print_usage();
    return 1;
  }

  std::wstring cmd = wargv[cmd_start];

  if (_wcsicmp(cmd.c_str(), L"list") == 0) {
    return cmd_list(std::vector<const wchar_t *>(wargv.begin() + cmd_start + 1,
                                                 wargv.end()));
  }

  if (_wcsicmp(cmd.c_str(), L"status") == 0) {
    if (wargv.size() < cmd_start + 2) {
      log_error(L"Usage: status <index>");
      return 1;
    }
    int index = _wtoi(wargv[cmd_start + 1]);
    auto devices = duvc::list_devices();
    if (index < 0 || index >= static_cast<int>(devices.size())) {
      log_error(L"Invalid device index");
      return 2;
    }
    bool connected = duvc::is_device_connected(devices[index]);

    if (g_flags.format == OutputFormat::JSON) {
      std::wcout << L"{\"index\":" << index << L",\"name\":\""
                 << json_escape(devices[index].name) << L"\""
                 << L",\"connected\":" << (connected ? L"true" : L"false")
                 << L"}\n";
    } else {
      std::wcout << devices[index].name << L": "
                 << (connected ? L"CONNECTED" : L"DISCONNECTED") << L"\n";
    }
    return 0;
  }

  if (_wcsicmp(cmd.c_str(), L"monitor") == 0) {
    return cmd_monitor(std::vector<const wchar_t *>(
        wargv.begin() + cmd_start + 1, wargv.end()));
  }

  if (_wcsicmp(cmd.c_str(), L"capabilities") == 0) {
    if (wargv.size() < cmd_start + 2) {
      log_error(L"Usage: capabilities <index>");
      return 1;
    }
    int index = _wtoi(wargv[cmd_start + 1]);
    auto devices = duvc::list_devices();
    if (index < 0 || index >= static_cast<int>(devices.size())) {
      log_error(L"Invalid device index");
      return 2;
    }

    auto cam_res = duvc::open_camera(devices[index]);
    if (!cam_res) {
      log_error(L"Failed to open camera");
      log_verbose(L"Camera open failed for device " + std::to_wstring(index));
      return 3;
    }
    Camera cam = std::move(cam_res).value();

    if (g_flags.verbosity >= Verbosity::NORMAL &&
        g_flags.format == OutputFormat::TEXT) {
      std::wcout << L"Capabilities: " << devices[index].name << L"\n";
    }

    if (g_flags.format == OutputFormat::JSON) {
      std::wcout << L"{\"device\":" << index << L",\"capabilities\":[";
    }

    bool first = true;

    for (auto &m : CAM_PROP_MAP) {
      auto rr = cam.get_range(m.prop);
      if (!rr)
        continue;
      auto r = rr.value();

      int curVal = 0;
      CamMode curMode = r.default_mode;
      auto gv = cam.get(m.prop);
      if (gv) {
        auto v = gv.value();
        curVal = v.value;
        curMode = v.mode;
      }

      if (g_flags.format == OutputFormat::JSON) {
        if (!first)
          std::wcout << L",";
        std::wcout << L"{\"domain\":\"cam\",\"property\":\"" << m.name
                   << L"\",\"min\":" << r.min << L",\"max\":" << r.max
                   << L",\"step\":" << r.step << L",\"default\":"
                   << r.default_val << L",\"current\":" << curVal
                   << L",\"mode\":\"" << duvc::to_wstring(curMode) << L"\"}";
        first = false;
      } else {
        std::wcout << L"  CAM " << m.name << L": [" << r.min << L"," << r.max
                   << L"] step=" << r.step << L" default=" << r.default_val
                   << L" current=" << curVal << L" ("
                   << duvc::to_wstring(curMode) << L")\n";
      }
    }

    for (auto &m : VID_PROP_MAP) {
      auto rr = cam.get_range(m.prop);
      if (!rr)
        continue;
      auto r = rr.value();

      int curVal = 0;
      CamMode curMode = r.default_mode;
      auto gv = cam.get(m.prop);
      if (gv) {
        auto v = gv.value();
        curVal = v.value;
        curMode = v.mode;
      }

      if (g_flags.format == OutputFormat::JSON) {
        if (!first)
          std::wcout << L",";
        std::wcout << L"{\"domain\":\"vid\",\"property\":\"" << m.name
                   << L"\",\"min\":" << r.min << L",\"max\":" << r.max
                   << L",\"step\":" << r.step << L",\"default\":"
                   << r.default_val << L",\"current\":" << curVal
                   << L",\"mode\":\"" << duvc::to_wstring(curMode) << L"\"}";
        first = false;
      } else {
        std::wcout << L"  VID " << m.name << L": [" << r.min << L"," << r.max
                   << L"] step=" << r.step << L" default=" << r.default_val
                   << L" current=" << curVal << L" ("
                   << duvc::to_wstring(curMode) << L")\n";
      }
    }

    if (g_flags.format == OutputFormat::JSON) {
      std::wcout << L"]}\n";
    }

    return 0;
  }

  if (_wcsicmp(cmd.c_str(), L"get") == 0) {
    if (wargv.size() < cmd_start + 4) {
      log_error(L"Usage: get <index> <domain> <prop>[,<prop>...]");
      return 1;
    }
    int index = _wtoi(wargv[cmd_start + 1]);
    std::wstring domain = wargv[cmd_start + 2];
    std::wstring props_str = wargv[cmd_start + 3];
    auto props = split_string(props_str, L',');

    auto devices = duvc::list_devices();
    return cmd_get(index, domain, props, devices);
  }

  if (_wcsicmp(cmd.c_str(), L"set") == 0) {
    if (wargv.size() < cmd_start + 4) {
      log_error(
          L"Usage: set [--relative|-r] <index> <domain> <prop>=<val>[,...] OR "
          L"set <index> <domain> <prop> <val> [mode]");
      return 1;
    }

    // Check for --relative or -r flag
    bool force_relative = false;
    size_t arg_offset = 0;

    if (cmd_start + 1 < wargv.size()) {
      std::wstring maybe_flag = wargv[cmd_start + 1];
      if (maybe_flag == L"--relative" || maybe_flag == L"-r") {
        force_relative = true;
        arg_offset = 1;
        log_verbose(L"Relative mode enabled via flag");
      }
    }

    if (wargv.size() < cmd_start + 4 + arg_offset) {
      log_error(
          L"Usage: set [--relative|-r] <index> <domain> <prop>=<val>[,...] OR "
          L"set <index> <domain> <prop> <val> [mode]");
      return 1;
    }

    int index = _wtoi(wargv[cmd_start + 1 + arg_offset]);
    std::wstring domain = wargv[cmd_start + 2 + arg_offset];
    auto devices = duvc::list_devices();

    std::wstring third_arg = wargv[cmd_start + 3 + arg_offset];

    // Check if batch mode (contains = or ,)
    if (third_arg.find(L'=') != std::wstring::npos ||
        third_arg.find(L',') != std::wstring::npos) {
      auto set_specs = split_string(third_arg, L',');
      return cmd_set(index, domain, set_specs, wargv,
                     cmd_start + 4 + arg_offset, devices, force_relative);
    } else {
      // Single property mode
      std::wstring prop_name = third_arg;

      if (wargv.size() >= cmd_start + 5 + arg_offset) {
        std::wstring value_or_mode = wargv[cmd_start + 4 + arg_offset];
        auto mode_check = parse_mode(value_or_mode);

        if (mode_check) {
          // Mode-only set
          if (index < 0 || index >= static_cast<int>(devices.size())) {
            log_error(L"Invalid device index");
            return 2;
          }

          auto cam_res = duvc::open_camera(devices[index]);
          if (!cam_res) {
            log_error(L"Failed to open camera");
            log_verbose(L"Camera open failed");
            return 3;
          }
          Camera cam = std::move(cam_res).value();

          bool is_cam = is_cam_domain(domain);

          if (is_cam) {
            auto p = parse_cam_prop(prop_name);
            if (!p) {
              log_error(L"Unknown camera property");
              return 3;
            }
            auto current = cam.get(*p);
            if (!current) {
              log_error(L"Failed to get current value");
              log_verbose(L"Cannot set mode without reading current value");
              return 4;
            }
            PropSetting s{current.value().value, *mode_check};
            if (!cam.set(*p, s)) {
              log_error(L"Failed to set mode");
              log_verbose(L"Set operation returned false");
              return 4;
            }
          } else {
            auto p = parse_vid_prop(prop_name);
            if (!p) {
              log_error(L"Unknown video property");
              return 3;
            }
            auto current = cam.get(*p);
            if (!current) {
              log_error(L"Failed to get current value");
              log_verbose(L"Cannot set mode without reading current value");
              return 4;
            }
            PropSetting s{current.value().value, *mode_check};
            if (!cam.set(*p, s)) {
              log_error(L"Failed to set mode");
              log_verbose(L"Set operation returned false");
              return 4;
            }
          }

          if (g_flags.verbosity >= Verbosity::NORMAL &&
              g_flags.format == OutputFormat::TEXT) {
            std::wcout << L"OK\n";
          }
          return 0;
        } else {
          // Regular value set
          std::wostringstream spec;
          spec << prop_name << L"=" << value_or_mode;

          if (wargv.size() >= cmd_start + 6 + arg_offset) {
            spec << L":" << wargv[cmd_start + 5 + arg_offset];
          }

          std::vector<std::wstring> set_specs;
          set_specs.push_back(spec.str());
          return cmd_set(index, domain, set_specs, wargv,
                         cmd_start + 6 + arg_offset, devices, force_relative);
        }
      } else {
        log_error(L"No value or mode provided");
        return 1;
      }
    }
  }

  if (_wcsicmp(cmd.c_str(), L"reset") == 0) {
    if (wargv.size() < cmd_start + 3) {
      log_error(L"Usage: reset <index> <domain|all> <prop>[,<prop>...|all]");
      return 1;
    }
    int index = _wtoi(wargv[cmd_start + 1]);
    std::wstring domain = wargv[cmd_start + 2];

    auto devices = duvc::list_devices();

    std::vector<std::wstring> props;
    if (wargv.size() >= cmd_start + 4) {
      std::wstring props_str = wargv[cmd_start + 3];
      props = split_string(props_str, L',');
    } else {
      props.push_back(L"all");
    }

    return cmd_reset(index, domain, props, devices);
  }

  if (_wcsicmp(cmd.c_str(), L"snapshot") == 0) {
    if (wargv.size() < cmd_start + 2) {
      log_error(L"Usage: snapshot <index> [-o file]");
      return 1;
    }
    int index = _wtoi(wargv[cmd_start + 1]);
    auto devices = duvc::list_devices();

    return cmd_snapshot(index, devices,
                        std::vector<const wchar_t *>(
                            wargv.begin() + cmd_start + 2, wargv.end()));
  }

  if (_wcsicmp(cmd.c_str(), L"range") == 0) {
    if (wargv.size() < cmd_start + 4) {
      log_error(L"Usage: range <index> <domain|all> <prop>[,<prop>...|all]");
      return 1;
    }
    int index = _wtoi(wargv[cmd_start + 1]);
    std::wstring domain = wargv[cmd_start + 2];
    std::wstring props_str = wargv[cmd_start + 3];
    auto props = split_string(props_str, L',');

    auto devices = duvc::list_devices();
    return cmd_range(index, domain, props, devices);
  }

  log_error(L"Unknown command: " + cmd);
  print_usage();
  return 1;
}
