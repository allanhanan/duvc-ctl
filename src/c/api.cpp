/**
 * @file api.cpp
 * @brief Complete C ABI implementation for duvc-ctl library
 *
 * This file implements the comprehensive C ABI interface, providing a stable
 * C-compatible API that bridges to the underlying C++ implementation.
 * All C++ exceptions are caught and converted to appropriate C error codes.
 * Memory management is handled appropriately for C consumers.
 */

#include "duvc-ctl/c/api.h"

// Include all necessary C++ headers
#include "duvc-ctl/core/camera.h"
#include "duvc-ctl/core/capability.h"
#include "duvc-ctl/core/device.h"
#include "duvc-ctl/core/result.h"
#include "duvc-ctl/core/types.h"
#include "duvc-ctl/utils/error_decoder.h"
#include "duvc-ctl/utils/logging.h"
#include "duvc-ctl/utils/string_conversion.h"
#ifdef _WIN32
#include "duvc-ctl/platform/windows/connection_pool.h"
#endif

#include <algorithm>
#include <atomic>
#include <cstring>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

// Version information
#ifndef DUVC_ABI_VERSION
#define DUVC_ABI_VERSION ((1 << 16) | (0 << 8) | 0) // 1.0.0
#endif

#ifndef DUVC_ABI_VERSION_STRING
#define DUVC_ABI_VERSION_STRING "1.0.0"
#endif

#ifdef DeviceCapabilities
#undef DeviceCapabilities
#endif

// Global state management
namespace {

/** @brief Global initialization state */
std::atomic<bool> g_initialized{false};

/** @brief Global library mutex for thread safety */
std::mutex g_library_mutex;

/** @brief Thread-local error details storage */
thread_local std::string g_last_error_details;

/** @brief Log callback state */
duvc_log_callback g_log_callback = nullptr;
void *g_log_callback_user_data = nullptr;
std::mutex g_log_mutex;

/** @brief Device change callback state */
duvc_device_change_callback g_device_change_callback = nullptr;
void *g_device_change_user_data = nullptr;
std::mutex g_device_change_mutex;

/** @brief Device storage for C API lifetime management */
std::vector<std::unique_ptr<duvc::Device>> g_device_storage;
std::mutex g_device_storage_mutex;

/** @brief Camera connections storage for C API lifetime management */
std::unordered_map<duvc_connection_t *, std::unique_ptr<duvc::Camera>>
    g_connections;
std::mutex g_connection_mutex;

/** @brief Capabilities storage for C API */
std::vector<std::unique_ptr<duvc::DeviceCapabilities>> g_capabilities_storage;
std::mutex g_capabilities_mutex;

/**
 * @brief Convert C++ string to UTF-8 C string with buffer management
 * @param cpp_str C++ string to convert
 * @param buffer Output buffer (can be nullptr to query size)
 * @param buffer_size Size of output buffer
 * @param required_size Required buffer size (including null terminator)
 * @return DUVC_SUCCESS or DUVC_ERROR_BUFFER_TOO_SMALL
 */
duvc_result_t copy_string_to_buffer(const std::string &cpp_str, char *buffer,
                                    size_t buffer_size, size_t *required_size) {
  size_t needed = cpp_str.length() + 1;
  if (required_size)
    *required_size = needed;

  if (!buffer || buffer_size < needed) {
    return DUVC_ERROR_BUFFER_TOO_SMALL;
  }

  std::memcpy(buffer, cpp_str.c_str(), needed);
  return DUVC_SUCCESS;
}

/**
 * @brief Convert wide string to UTF-8 with buffer management
 */
duvc_result_t copy_wstring_to_buffer(const std::wstring &wide_str, char *buffer,
                                     size_t buffer_size,
                                     size_t *required_size) {
  try {
    std::string utf8_str = duvc::to_utf8(wide_str);
    return copy_string_to_buffer(utf8_str, buffer, buffer_size, required_size);
  } catch (const std::exception &e) {
    g_last_error_details = std::string("String conversion failed: ") + e.what();
    if (required_size)
      *required_size = 0;
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

/**
 * @brief Convert C++ ErrorCode to C duvc_result_t
 */
duvc_result_t convert_error_code(duvc::ErrorCode code) {
  switch (code) {
  case duvc::ErrorCode::Success:
    return DUVC_SUCCESS;
  case duvc::ErrorCode::DeviceNotFound:
    return DUVC_ERROR_DEVICE_NOT_FOUND;
  case duvc::ErrorCode::DeviceBusy:
    return DUVC_ERROR_DEVICE_BUSY;
  case duvc::ErrorCode::PropertyNotSupported:
    return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
  case duvc::ErrorCode::InvalidValue:
    return DUVC_ERROR_INVALID_VALUE;
  case duvc::ErrorCode::PermissionDenied:
    return DUVC_ERROR_PERMISSION_DENIED;
  case duvc::ErrorCode::SystemError:
    return DUVC_ERROR_SYSTEM_ERROR;
  case duvc::ErrorCode::InvalidArgument:
    return DUVC_ERROR_INVALID_ARGUMENT;
  case duvc::ErrorCode::NotImplemented:
    return DUVC_ERROR_NOT_IMPLEMENTED;
  default:
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

/**
 * @brief Handle C++ Result and store error details
 */
template <typename T>
duvc_result_t handle_cpp_result(const duvc::Result<T> &result) {
  if (result.is_ok()) {
    g_last_error_details.clear();
    return DUVC_SUCCESS;
  }

  const auto &error = result.error();
  g_last_error_details = error.description();
  return convert_error_code(error.code());
}

/**
 * @brief C++ log callback wrapper
 */
void cpp_log_callback_wrapper(duvc::LogLevel level,
                              const std::string &message) {
  std::lock_guard<std::mutex> lock(g_log_mutex);
  if (g_log_callback) {
    duvc_log_level_t c_level =
        static_cast<duvc_log_level_t>(static_cast<int>(level));
    try {
      g_log_callback(c_level, message.c_str(), g_log_callback_user_data);
    } catch (...) {
      // Ignore exceptions from user callback
    }
  }
}

// --- C <-> C++ Type Conversion Helpers ---

duvc::CamProp convert_cam_prop(duvc_cam_prop_t prop) {
  return static_cast<duvc::CamProp>(prop);
}

duvc::VidProp convert_vid_prop(duvc_vid_prop_t prop) {
  return static_cast<duvc::VidProp>(prop);
}

duvc::CamMode convert_cam_mode_from_c(duvc_cam_mode_t mode) {
  return static_cast<duvc::CamMode>(mode);
}

duvc_cam_mode_t convert_cam_mode_to_c(duvc::CamMode mode) {
  return static_cast<duvc_cam_mode_t>(mode);
}

duvc::PropSetting
convert_prop_setting_from_c(const duvc_prop_setting_t &setting) {
  duvc::PropSetting cpp_setting;
  cpp_setting.value = setting.value;
  cpp_setting.mode = convert_cam_mode_from_c(setting.mode);
  return cpp_setting;
}

duvc_prop_setting_t
convert_prop_setting_to_c(const duvc::PropSetting &setting) {
  duvc_prop_setting_t c_setting;
  c_setting.value = setting.value;
  c_setting.mode = convert_cam_mode_to_c(setting.mode);
  return c_setting;
}

duvc_prop_range_t convert_prop_range_to_c(const duvc::PropRange &range) {
  duvc_prop_range_t c_range;
  c_range.min = range.min;
  c_range.max = range.max;
  c_range.step = range.step;
  c_range.default_val = range.default_val;
  c_range.default_mode = convert_cam_mode_to_c(range.default_mode);
  return c_range;
}

} // anonymous namespace

extern "C" {

/* ========================================================================
 * Version and ABI Management
 * ======================================================================== */

uint32_t duvc_get_version(void) { return DUVC_ABI_VERSION; }

const char *duvc_get_version_string(void) { return DUVC_ABI_VERSION_STRING; }

int duvc_check_abi_compatibility(uint32_t compiled_version) {
  uint32_t runtime_version = duvc_get_version();

  // Extract major, minor versions
  uint32_t compiled_major = (compiled_version >> 16) & 0xFF;
  uint32_t runtime_major = (runtime_version >> 16) & 0xFF;

  // Major versions must match exactly for ABI compatibility
  if (compiled_major != runtime_major) {
    return 0;
  }

  // Runtime minor version must be >= compiled minor version
  uint32_t compiled_minor = (compiled_version >> 8) & 0xFF;
  uint32_t runtime_minor = (runtime_version >> 8) & 0xFF;

  return (runtime_minor >= compiled_minor) ? 1 : 0;
}

/* ========================================================================
 * Library Lifecycle
 * ======================================================================== */

duvc_result_t duvc_initialize(void) {
  std::lock_guard<std::mutex> lock(g_library_mutex);

  if (g_initialized.load()) {
    return DUVC_SUCCESS; // Already initialized
  }

  try {
    // Clear any previous error state
    g_last_error_details.clear();

    // Initialize logging with default level
    duvc::set_log_level(duvc::LogLevel::Info);

    // Clear storage containers
    g_device_storage.clear();
    g_connections.clear();
    g_capabilities_storage.clear();

    g_initialized.store(true);
    duvc::log_info("duvc-ctl C API initialized successfully");
    return DUVC_SUCCESS;

  } catch (const std::exception &e) {
    g_last_error_details = std::string("Initialization failed: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  } catch (...) {
    g_last_error_details = "Initialization failed: unknown error";
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

void duvc_shutdown(void) {
  std::lock_guard<std::mutex> lock(g_library_mutex);
  if (!g_initialized.load()) {
    return; // Already shutdown
  }

  try {
    // Unregister device monitor to stop background threads
    duvc_unregister_device_change_callback();

    // Clear all connections
    {
      std::lock_guard<std::mutex> conn_lock(g_connection_mutex);
      g_connections.clear();
    }

    // Clear device storage
    {
      std::lock_guard<std::mutex> dev_lock(g_device_storage_mutex);
      g_device_storage.clear();
    }

    // Clear capabilities storage
    {
      std::lock_guard<std::mutex> caps_lock(g_capabilities_mutex);
      g_capabilities_storage.clear();
    }

    // Clear callbacks
    {
      std::lock_guard<std::mutex> log_lock(g_log_mutex);
      g_log_callback = nullptr;
      g_log_callback_user_data = nullptr;
    }

    g_initialized.store(false);

  } catch (...) {
    // Ignore exceptions during shutdown
  }
}

int duvc_is_initialized(void) { return g_initialized.load() ? 1 : 0; }

/* ========================================================================
 * String Conversions
 * ======================================================================== */

const char *duvc_error_code_to_string(duvc_result_t code) {
  switch (code) {
  case DUVC_SUCCESS:
    return "Success";
  case DUVC_ERROR_NOT_IMPLEMENTED:
    return "Not Implemented";
  case DUVC_ERROR_INVALID_ARGUMENT:
    return "Invalid Argument";
  case DUVC_ERROR_DEVICE_NOT_FOUND:
    return "Device Not Found";
  case DUVC_ERROR_DEVICE_BUSY:
    return "Device Busy";
  case DUVC_ERROR_PROPERTY_NOT_SUPPORTED:
    return "Property Not Supported";
  case DUVC_ERROR_INVALID_VALUE:
    return "Invalid Value";
  case DUVC_ERROR_PERMISSION_DENIED:
    return "Permission Denied";
  case DUVC_ERROR_SYSTEM_ERROR:
    return "System Error";
  case DUVC_ERROR_CONNECTION_FAILED:
    return "Connection Failed";
  case DUVC_ERROR_TIMEOUT:
    return "Timeout";
  case DUVC_ERROR_BUFFER_TOO_SMALL:
    return "Buffer Too Small";
  default:
    return "Unknown Error";
  }
}

const char *duvc_cam_prop_to_string(duvc_cam_prop_t prop) {
  // This can leverage the internal C++ version if available and linked
  return duvc::to_string(static_cast<duvc::CamProp>(prop));
}

const char *duvc_vid_prop_to_string(duvc_vid_prop_t prop) {
  return duvc::to_string(static_cast<duvc::VidProp>(prop));
}

const char *duvc_cam_mode_to_string(duvc_cam_mode_t mode) {
  return duvc::to_string(static_cast<duvc::CamMode>(mode));
}

const char *duvc_log_level_to_string(duvc_log_level_t level) {
  switch (level) {
  case DUVC_LOG_DEBUG:
    return "Debug";
  case DUVC_LOG_INFO:
    return "Info";
  case DUVC_LOG_WARNING:
    return "Warning";
  case DUVC_LOG_ERROR:
    return "Error";
  case DUVC_LOG_CRITICAL:
    return "Critical";
  default:
    return "Unknown";
  }
}

/* ========================================================================
 * Logging System
 * ======================================================================== */

duvc_result_t duvc_set_log_callback(duvc_log_callback callback,
                                    void *user_data) {
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_log_mutex);
    g_log_callback = callback;
    g_log_callback_user_data = user_data;

    if (callback) {
      duvc::set_log_callback(cpp_log_callback_wrapper);
    } else {
      duvc::set_log_callback(nullptr);
    }

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to set log callback: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_set_log_level(duvc_log_level_t level) {
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    duvc::LogLevel cpp_level =
        static_cast<duvc::LogLevel>(static_cast<int>(level));
    duvc::set_log_level(cpp_level);
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details = std::string("Failed to set log level: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_get_log_level(duvc_log_level_t *level) {
  if (!level)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    duvc::LogLevel cpp_level = duvc::get_log_level();
    *level = static_cast<duvc_log_level_t>(static_cast<int>(cpp_level));
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details = std::string("Failed to get log level: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_log_message(duvc_log_level_t level, const char *message) {
  if (!message)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    // Cannot set error message if not initialized
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    duvc::LogLevel cpp_level =
        static_cast<duvc::LogLevel>(static_cast<int>(level));
    duvc::log_message(cpp_level, std::string(message));
    return DUVC_SUCCESS;
  } catch (const std::exception &) {
    // Don't update error details to avoid recursion
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_log_debug(const char *message) {
  return duvc_log_message(DUVC_LOG_DEBUG, message);
}

duvc_result_t duvc_log_info(const char *message) {
  return duvc_log_message(DUVC_LOG_INFO, message);
}

duvc_result_t duvc_log_warning(const char *message) {
  return duvc_log_message(DUVC_LOG_WARNING, message);
}

duvc_result_t duvc_log_error(const char *message) {
  return duvc_log_message(DUVC_LOG_ERROR, message);
}

duvc_result_t duvc_log_critical(const char *message) {
  return duvc_log_message(DUVC_LOG_CRITICAL, message);
}

/* ========================================================================
 * Device Management
 * ======================================================================== */

duvc_result_t duvc_list_devices(duvc_device_t ***devices, size_t *count) {
  if (!devices || !count)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_device_storage_mutex);

    // Clear previous device storage
    g_device_storage.clear();

    // Get devices from C++ core
    auto device_list = duvc::list_devices();

    // Allocate C device array
    duvc_device_t **c_devices = static_cast<duvc_device_t **>(
        std::malloc(device_list.size() * sizeof(duvc_device_t *)));
    if (!c_devices && !device_list.empty()) {
      g_last_error_details = "Failed to allocate memory for device list";
      return DUVC_ERROR_SYSTEM_ERROR;
    }

    // Store devices and create C pointers
    for (size_t i = 0; i < device_list.size(); ++i) {
      auto stored_device =
          std::make_unique<duvc::Device>(std::move(device_list[i]));
      c_devices[i] = reinterpret_cast<duvc_device_t *>(stored_device.get());
      g_device_storage.push_back(std::move(stored_device));
    }

    *devices = c_devices;
    *count = device_list.size();
    return DUVC_SUCCESS;

  } catch (const std::exception &e) {
    g_last_error_details = std::string("Failed to list devices: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  } catch (...) {
    g_last_error_details = "Unknown error while listing devices";
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_find_device_by_path(const char *device_path_utf8,
                                       duvc_device_t **device) {
  if (!device_path_utf8 || !device)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    // Convert UTF-8 to wide string
    std::wstring device_path = duvc::to_wstring(std::string(device_path_utf8));
    
    // Find device by path
    duvc::Device found_device = duvc::find_device_by_path(device_path);
    
    // Store device and return pointer
    std::lock_guard<std::mutex> lock(g_device_storage_mutex);
    auto stored_device = std::make_unique<duvc::Device>(std::move(found_device));
    *device = reinterpret_cast<duvc_device_t *>(stored_device.get());
    g_device_storage.push_back(std::move(stored_device));
    
    return DUVC_SUCCESS;
    
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to find device by path: ") + e.what();
    return DUVC_ERROR_DEVICE_NOT_FOUND;
  } catch (...) {
    g_last_error_details = "Unknown error while finding device by path";
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

void duvc_free_device_list(duvc_device_t **devices, size_t count) {
  (void)count; // Unused parameter

  if (devices) {
    std::free(devices);
  }

  // Note: Individual devices are managed by g_device_storage
}

duvc_result_t duvc_is_device_connected(const duvc_device_t *device,
                                       int *connected) {
  if (!device || !connected)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    bool is_connected = duvc::is_device_connected(*cpp_device);
    *connected = is_connected ? 1 : 0;
    return DUVC_SUCCESS;

  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to check device connection: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  } catch (...) {
    g_last_error_details = "Unknown error while checking device connection";
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_get_device_name(const duvc_device_t *device, char *buffer,
                                   size_t buffer_size, size_t *required) {
  if (!device)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    return copy_wstring_to_buffer(cpp_device->name, buffer, buffer_size,
                                  required);
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get device name: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_get_device_path(const duvc_device_t *device, char *buffer,
                                   size_t buffer_size, size_t *required) {
  if (!device)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    return copy_wstring_to_buffer(cpp_device->path, buffer, buffer_size,
                                  required);
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get device path: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_get_device_id(const duvc_device_t *device, char *buffer,
                                 size_t buffer_size, size_t *required) {
  if (!device)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    // Use path as device ID if available, otherwise use name
    const std::wstring &id_str =
        cpp_device->path.empty() ? cpp_device->name : cpp_device->path;
    return copy_wstring_to_buffer(id_str, buffer, buffer_size, required);
  } catch (const std::exception &e) {
    g_last_error_details = std::string("Failed to get device ID: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_device_is_valid(const duvc_device_t *device, int *valid) {
  if (!device || !valid)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    *valid = cpp_device->is_valid() ? 1 : 0;
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to check device validity: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

/* ========================================================================
 * Device Change Monitoring
 * ======================================================================== */

duvc_result_t
duvc_register_device_change_callback(duvc_device_change_callback callback,
                                     void *user_data) {
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_device_change_mutex);

    g_device_change_callback = callback;
    g_device_change_user_data = user_data;

    // Register with the underlying system
    duvc::register_device_change_callback(
        [=](bool added, const std::wstring &device_path) {
          std::lock_guard<std::mutex> cb_lock(g_device_change_mutex);
          if (g_device_change_callback) {
            try {
              std::string utf8_path = duvc::to_utf8(device_path);
              g_device_change_callback(added ? 1 : 0, utf8_path.c_str(),
                                       g_device_change_user_data);
            } catch (...) {
              // Ignore exceptions from user callback
            }
          }
        });

    return DUVC_SUCCESS;

  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to register device change callback: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

void duvc_unregister_device_change_callback(void) {
  if (!g_initialized.load()) {
    return;
  }

  try {
    std::lock_guard<std::mutex> lock(g_device_change_mutex);

    // Unregister with the underlying system
    duvc::unregister_device_change_callback();

    g_device_change_callback = nullptr;
    g_device_change_user_data = nullptr;

  } catch (...) {
    // Ignore exceptions during cleanup
  }
}

/* ========================================================================
 * Camera Connections
 * ======================================================================== */

duvc_result_t duvc_open_camera_by_index(int device_index,
                                        duvc_connection_t **conn) {
  if (!conn || device_index < 0)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    auto cam_result = duvc::open_camera(device_index);
    if (!cam_result.is_ok()) {
      return handle_cpp_result(cam_result);
    }

    std::lock_guard<std::mutex> conn_lock(g_connection_mutex);
    auto camera_ptr =
        std::make_unique<duvc::Camera>(std::move(cam_result).value());
    duvc_connection_t *handle =
        reinterpret_cast<duvc_connection_t *>(camera_ptr.get());
    g_connections[handle] = std::move(camera_ptr);
    *conn = handle;

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to open camera by index: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_open_camera(const duvc_device_t *device,
                               duvc_connection_t **conn) {
  if (!device || !conn)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    auto cam_result = duvc::open_camera(*cpp_device);
    if (!cam_result.is_ok()) {
      return handle_cpp_result(cam_result);
    }

    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto camera_ptr =
        std::make_unique<duvc::Camera>(std::move(cam_result).value());
    duvc_connection_t *handle =
        reinterpret_cast<duvc_connection_t *>(camera_ptr.get());
    g_connections[handle] = std::move(camera_ptr);
    *conn = handle;

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details = std::string("Failed to open camera: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

void duvc_close_camera(duvc_connection_t *conn) {
  if (!conn || !g_initialized.load()) {
    return;
  }

  try {
    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto it = g_connections.find(conn);
    if (it != g_connections.end()) {
      g_connections.erase(it);
    }
  } catch (...) {
    // Ignore exceptions during cleanup
  }
}

int duvc_camera_is_valid(const duvc_connection_t *conn) {
  if (!conn || !g_initialized.load()) {
    return 0;
  }

  try {
    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto it = g_connections.find(const_cast<duvc_connection_t *>(conn));
    if (it == g_connections.end()) {
      return 0;
    }
    return it->second->is_valid() ? 1 : 0;
  } catch (...) {
    return 0;
  }
}

/* ========================================================================
 * Property Access - Single Properties
 * ======================================================================== */

duvc_result_t duvc_get_camera_property(duvc_connection_t *conn,
                                       duvc_cam_prop_t prop,
                                       duvc_prop_setting_t *setting) {
  if (!conn || !setting)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto it = g_connections.find(conn);
    if (it == g_connections.end()) {
      g_last_error_details = "Invalid connection handle";
      return DUVC_ERROR_INVALID_ARGUMENT;
    }

    auto result = it->second->get(convert_cam_prop(prop));
    if (!result.is_ok()) {
      return handle_cpp_result(result);
    }

    *setting = convert_prop_setting_to_c(result.value());
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get camera property: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_set_camera_property(duvc_connection_t *conn,
                                       duvc_cam_prop_t prop,
                                       const duvc_prop_setting_t *setting) {
  if (!conn || !setting)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto it = g_connections.find(conn);
    if (it == g_connections.end()) {
      g_last_error_details = "Invalid connection handle";
      return DUVC_ERROR_INVALID_ARGUMENT;
    }

    duvc::PropSetting cpp_setting = convert_prop_setting_from_c(*setting);
    auto result = it->second->set(convert_cam_prop(prop), cpp_setting);
    return handle_cpp_result(result);
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to set camera property: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_get_camera_property_range(duvc_connection_t *conn,
                                             duvc_cam_prop_t prop,
                                             duvc_prop_range_t *range) {
  if (!conn || !range)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto it = g_connections.find(conn);
    if (it == g_connections.end()) {
      g_last_error_details = "Invalid connection handle";
      return DUVC_ERROR_INVALID_ARGUMENT;
    }

    auto result = it->second->get_range(convert_cam_prop(prop));
    if (!result.is_ok()) {
      return handle_cpp_result(result);
    }

    *range = convert_prop_range_to_c(result.value());
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get camera property range: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_get_video_property(duvc_connection_t *conn,
                                      duvc_vid_prop_t prop,
                                      duvc_prop_setting_t *setting) {
  if (!conn || !setting)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto it = g_connections.find(conn);
    if (it == g_connections.end()) {
      g_last_error_details = "Invalid connection handle";
      return DUVC_ERROR_INVALID_ARGUMENT;
    }

    auto result = it->second->get(convert_vid_prop(prop));
    if (!result.is_ok()) {
      return handle_cpp_result(result);
    }

    *setting = convert_prop_setting_to_c(result.value());
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get video property: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_set_video_property(duvc_connection_t *conn,
                                      duvc_vid_prop_t prop,
                                      const duvc_prop_setting_t *setting) {
  if (!conn || !setting)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto it = g_connections.find(conn);
    if (it == g_connections.end()) {
      g_last_error_details = "Invalid connection handle";
      return DUVC_ERROR_INVALID_ARGUMENT;
    }

    duvc::PropSetting cpp_setting = convert_prop_setting_from_c(*setting);
    auto result = it->second->set(convert_vid_prop(prop), cpp_setting);
    return handle_cpp_result(result);
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to set video property: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_get_video_property_range(duvc_connection_t *conn,
                                            duvc_vid_prop_t prop,
                                            duvc_prop_range_t *range) {
  if (!conn || !range)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto it = g_connections.find(conn);
    if (it == g_connections.end()) {
      g_last_error_details = "Invalid connection handle";
      return DUVC_ERROR_INVALID_ARGUMENT;
    }

    auto result = it->second->get_range(convert_vid_prop(prop));
    if (!result.is_ok()) {
      return handle_cpp_result(result);
    }

    *range = convert_prop_range_to_c(result.value());
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get video property range: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

/* ========================================================================
 * Property Access - Multiple Properties
 * ======================================================================== */

duvc_result_t duvc_get_multiple_camera_properties(duvc_connection_t *conn,
                                                  const duvc_cam_prop_t *props,
                                                  duvc_prop_setting_t *settings,
                                                  size_t count) {
  if (!conn || !props || !settings || count == 0)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto it = g_connections.find(conn);
    if (it == g_connections.end()) {
      g_last_error_details = "Invalid connection handle";
      return DUVC_ERROR_INVALID_ARGUMENT;
    }

    duvc::Camera *camera = it->second.get();
    for (size_t i = 0; i < count; ++i) {
      auto result = camera->get(convert_cam_prop(props[i]));
      if (!result.is_ok()) {
        g_last_error_details =
            "Failed to get camera property at index " + std::to_string(i);
        return handle_cpp_result(result);
      }
      settings[i] = convert_prop_setting_to_c(result.value());
    }

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get multiple camera properties: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_set_multiple_camera_properties(
    duvc_connection_t *conn, const duvc_cam_prop_t *props,
    const duvc_prop_setting_t *settings, size_t count) {
  if (!conn || !props || !settings || count == 0)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto it = g_connections.find(conn);
    if (it == g_connections.end()) {
      g_last_error_details = "Invalid connection handle";
      return DUVC_ERROR_INVALID_ARGUMENT;
    }

    duvc::Camera *camera = it->second.get();
    for (size_t i = 0; i < count; ++i) {
      duvc::PropSetting cpp_setting = convert_prop_setting_from_c(settings[i]);
      auto result = camera->set(convert_cam_prop(props[i]), cpp_setting);
      if (!result.is_ok()) {
        g_last_error_details =
            "Failed to set camera property at index " + std::to_string(i);
        return handle_cpp_result(result);
      }
    }

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to set multiple camera properties: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_get_multiple_video_properties(duvc_connection_t *conn,
                                                 const duvc_vid_prop_t *props,
                                                 duvc_prop_setting_t *settings,
                                                 size_t count) {
  if (!conn || !props || !settings || count == 0)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto it = g_connections.find(conn);
    if (it == g_connections.end()) {
      g_last_error_details = "Invalid connection handle";
      return DUVC_ERROR_INVALID_ARGUMENT;
    }

    duvc::Camera *camera = it->second.get();
    for (size_t i = 0; i < count; ++i) {
      auto result = camera->get(convert_vid_prop(props[i]));
      if (!result.is_ok()) {
        g_last_error_details =
            "Failed to get video property at index " + std::to_string(i);
        return handle_cpp_result(result);
      }
      settings[i] = convert_prop_setting_to_c(result.value());
    }

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get multiple video properties: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_set_multiple_video_properties(
    duvc_connection_t *conn, const duvc_vid_prop_t *props,
    const duvc_prop_setting_t *settings, size_t count) {
  if (!conn || !props || !settings || count == 0)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard<std::mutex> lock(g_connection_mutex);
    auto it = g_connections.find(conn);
    if (it == g_connections.end()) {
      g_last_error_details = "Invalid connection handle";
      return DUVC_ERROR_INVALID_ARGUMENT;
    }

    duvc::Camera *camera = it->second.get();
    for (size_t i = 0; i < count; ++i) {
      duvc::PropSetting cpp_setting = convert_prop_setting_from_c(settings[i]);
      auto result = camera->set(convert_vid_prop(props[i]), cpp_setting);
      if (!result.is_ok()) {
        g_last_error_details =
            "Failed to set video property at index " + std::to_string(i);
        return handle_cpp_result(result);
      }
    }

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to set multiple video properties: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

/* ========================================================================
 * Quick API - Direct Device Access
 * ======================================================================== */

duvc_result_t duvc_quick_get_camera_property(const duvc_device_t *device,
                                             duvc_cam_prop_t prop,
                                             duvc_prop_setting_t *setting) {
  if (!device || !setting)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    auto cam_result = duvc::open_camera(*cpp_device);
    if (!cam_result.is_ok()) {
      return handle_cpp_result(cam_result);
    }

    auto camera = std::move(cam_result).value();
    auto result = camera.get(convert_cam_prop(prop));
    if (!result.is_ok()) {
      return handle_cpp_result(result);
    }

    *setting = convert_prop_setting_to_c(result.value());
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to quick get camera property: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t
duvc_quick_set_camera_property(const duvc_device_t *device,
                               duvc_cam_prop_t prop,
                               const duvc_prop_setting_t *setting) {
  if (!device || !setting)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    auto cam_result = duvc::open_camera(*cpp_device);
    if (!cam_result.is_ok()) {
      return handle_cpp_result(cam_result);
    }

    auto camera = std::move(cam_result).value();
    duvc::PropSetting cpp_setting = convert_prop_setting_from_c(*setting);
    auto result = camera.set(convert_cam_prop(prop), cpp_setting);
    return handle_cpp_result(result);
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to quick set camera property: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_quick_get_camera_property_range(const duvc_device_t *device,
                                                   duvc_cam_prop_t prop,
                                                   duvc_prop_range_t *range) {
  if (!device || !range)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    auto cam_result = duvc::open_camera(*cpp_device);
    if (!cam_result.is_ok()) {
      return handle_cpp_result(cam_result);
    }

    auto camera = std::move(cam_result).value();
    auto result = camera.get_range(convert_cam_prop(prop));
    if (!result.is_ok()) {
      return handle_cpp_result(result);
    }

    *range = convert_prop_range_to_c(result.value());
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to quick get camera property range: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_quick_get_video_property(const duvc_device_t *device,
                                            duvc_vid_prop_t prop,
                                            duvc_prop_setting_t *setting) {
  if (!device || !setting)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    auto cam_result = duvc::open_camera(*cpp_device);
    if (!cam_result.is_ok()) {
      return handle_cpp_result(cam_result);
    }

    auto camera = std::move(cam_result).value();
    auto result = camera.get(convert_vid_prop(prop));
    if (!result.is_ok()) {
      return handle_cpp_result(result);
    }

    *setting = convert_prop_setting_to_c(result.value());
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to quick get video property: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t
duvc_quick_set_video_property(const duvc_device_t *device, duvc_vid_prop_t prop,
                              const duvc_prop_setting_t *setting) {
  if (!device || !setting)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    auto cam_result = duvc::open_camera(*cpp_device);
    if (!cam_result.is_ok()) {
      return handle_cpp_result(cam_result);
    }

    auto camera = std::move(cam_result).value();
    duvc::PropSetting cpp_setting = convert_prop_setting_from_c(*setting);
    auto result = camera.set(convert_vid_prop(prop), cpp_setting);
    return handle_cpp_result(result);
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to quick set video property: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_quick_get_video_property_range(const duvc_device_t *device,
                                                  duvc_vid_prop_t prop,
                                                  duvc_prop_range_t *range) {
  if (!device || !range)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    auto cam_result = duvc::open_camera(*cpp_device);
    if (!cam_result.is_ok()) {
      return handle_cpp_result(cam_result);
    }

    auto camera = std::move(cam_result).value();
    auto result = camera.get_range(convert_vid_prop(prop));
    if (!result.is_ok()) {
      return handle_cpp_result(result);
    }

    *range = convert_prop_range_to_c(result.value());
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to quick get video property range: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

/* ========================================================================
 * Device Capability Snapshots
 * ======================================================================== */

duvc_result_t duvc_get_device_capabilities(const duvc_device_t *device,
                                           duvc_device_capabilities_t **caps) {
  if (!device || !caps)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::Device *cpp_device =
        reinterpret_cast<const duvc::Device *>(device);
    auto result = duvc::get_device_capabilities(*cpp_device);
    if (!result.is_ok()) {
      return handle_cpp_result(result);
    }

    std::lock_guard lock(g_capabilities_mutex);
    auto stored_caps =
        std::make_unique<duvc::DeviceCapabilities>(std::move(result.value()));
    duvc_device_capabilities_t *handle =
        reinterpret_cast<duvc_device_capabilities_t *>(stored_caps.get());
    g_capabilities_storage.push_back(std::move(stored_caps));
    *caps = handle;

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get device capabilities: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t
duvc_get_device_capabilities_by_index(int device_index,
                                      duvc_device_capabilities_t **caps) {
  if (device_index < 0 || !caps)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    auto result = duvc::get_device_capabilities(device_index);
    if (!result.is_ok()) {
      return handle_cpp_result(result);
    }

    std::lock_guard lock(g_capabilities_mutex);
    auto stored_caps =
        std::make_unique<duvc::DeviceCapabilities>(std::move(result.value()));
    duvc_device_capabilities_t *handle =
        reinterpret_cast<duvc_device_capabilities_t *>(stored_caps.get());
    g_capabilities_storage.push_back(std::move(stored_caps));
    *caps = handle;

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get device capabilities by index: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

void duvc_free_device_capabilities(duvc_device_capabilities_t *caps) {
  if (!caps || !g_initialized.load()) {
    return;
  }

  try {
    std::lock_guard lock(g_capabilities_mutex);
    auto it = std::find_if(
        g_capabilities_storage.begin(), g_capabilities_storage.end(),
        [caps](const std::unique_ptr<duvc::DeviceCapabilities> &ptr) {
          return reinterpret_cast<duvc_device_capabilities_t *>(ptr.get()) ==
                 caps;
        });

    if (it != g_capabilities_storage.end()) {
      g_capabilities_storage.erase(it);
    }
  } catch (...) {
    // Ignore exceptions during cleanup
  }
}

duvc_result_t
duvc_refresh_device_capabilities(duvc_device_capabilities_t *caps) {
  if (!caps)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    std::lock_guard lock(g_capabilities_mutex);
    duvc::DeviceCapabilities *cpp_caps =
        reinterpret_cast<duvc::DeviceCapabilities *>(caps);
    auto result = cpp_caps->refresh();
    return handle_cpp_result(result);
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to refresh device capabilities: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

/* ========================================================================
 * Capability Queries
 * ======================================================================== */

duvc_result_t duvc_get_camera_capability(const duvc_device_capabilities_t *caps,
                                         duvc_cam_prop_t prop,
                                         duvc_prop_range_t *range,
                                         duvc_prop_setting_t *current) {
  if (!caps)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::DeviceCapabilities *cpp_caps =
        reinterpret_cast<const duvc::DeviceCapabilities *>(caps);
    const auto &capability =
        cpp_caps->get_camera_capability(convert_cam_prop(prop));

    if (!capability.supported) {
      g_last_error_details = "Camera property not supported";
      return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
    }

    if (range) {
      *range = convert_prop_range_to_c(capability.range);
    }

    if (current) {
      *current = convert_prop_setting_to_c(capability.current);
    }

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get camera capability: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_get_video_capability(const duvc_device_capabilities_t *caps,
                                        duvc_vid_prop_t prop,
                                        duvc_prop_range_t *range,
                                        duvc_prop_setting_t *current) {
  if (!caps)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::DeviceCapabilities *cpp_caps =
        reinterpret_cast<const duvc::DeviceCapabilities *>(caps);
    const auto &capability =
        cpp_caps->get_video_capability(convert_vid_prop(prop));

    if (!capability.supported) {
      g_last_error_details = "Video property not supported";
      return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
    }

    if (range) {
      *range = convert_prop_range_to_c(capability.range);
    }

    if (current) {
      *current = convert_prop_setting_to_c(capability.current);
    }

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get video capability: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t
duvc_supports_camera_property(const duvc_device_capabilities_t *caps,
                              duvc_cam_prop_t prop, int *supported) {
  if (!caps || !supported)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::DeviceCapabilities *cpp_caps =
        reinterpret_cast<const duvc::DeviceCapabilities *>(caps);
    *supported =
        cpp_caps->supports_camera_property(convert_cam_prop(prop)) ? 1 : 0;
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to check camera property support: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t
duvc_supports_video_property(const duvc_device_capabilities_t *caps,
                             duvc_vid_prop_t prop, int *supported) {
  if (!caps || !supported)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::DeviceCapabilities *cpp_caps =
        reinterpret_cast<const duvc::DeviceCapabilities *>(caps);
    *supported =
        cpp_caps->supports_video_property(convert_vid_prop(prop)) ? 1 : 0;
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to check video property support: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t
duvc_get_supported_camera_properties(const duvc_device_capabilities_t *caps,
                                     duvc_cam_prop_t *props, size_t max_count,
                                     size_t *actual_count) {
  if (!caps || !actual_count)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::DeviceCapabilities *cpp_caps =
        reinterpret_cast<const duvc::DeviceCapabilities *>(caps);
    auto supported_props = cpp_caps->supported_camera_properties();

    *actual_count = supported_props.size();

    if (!props || max_count < supported_props.size()) {
      return DUVC_ERROR_BUFFER_TOO_SMALL;
    }

    for (size_t i = 0; i < supported_props.size(); ++i) {
      props[i] =
          static_cast<duvc_cam_prop_t>(static_cast<int>(supported_props[i]));
    }

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get supported camera properties: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t
duvc_get_supported_video_properties(const duvc_device_capabilities_t *caps,
                                    duvc_vid_prop_t *props, size_t max_count,
                                    size_t *actual_count) {
  if (!caps || !actual_count)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::DeviceCapabilities *cpp_caps =
        reinterpret_cast<const duvc::DeviceCapabilities *>(caps);
    auto supported_props = cpp_caps->supported_video_properties();

    *actual_count = supported_props.size();

    if (!props || max_count < supported_props.size()) {
      return DUVC_ERROR_BUFFER_TOO_SMALL;
    }

    for (size_t i = 0; i < supported_props.size(); ++i) {
      props[i] =
          static_cast<duvc_vid_prop_t>(static_cast<int>(supported_props[i]));
    }

    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to get supported video properties: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t
duvc_capabilities_is_device_accessible(const duvc_device_capabilities_t *caps,
                                       int *accessible) {
  if (!caps || !accessible)
    return DUVC_ERROR_INVALID_ARGUMENT;
  if (!g_initialized.load()) {
    g_last_error_details = "Library not initialized";
    return DUVC_ERROR_SYSTEM_ERROR;
  }

  try {
    const duvc::DeviceCapabilities *cpp_caps =
        reinterpret_cast<const duvc::DeviceCapabilities *>(caps);
    *accessible = cpp_caps->is_device_accessible() ? 1 : 0;
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to check device accessibility: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

/* ========================================================================
 * Property Range Utilities
 * ======================================================================== */

duvc_result_t duvc_prop_range_is_valid(const duvc_prop_range_t *range,
                                       int32_t value, int *valid) {
  if (!range || !valid) {
    return DUVC_ERROR_INVALID_ARGUMENT;
  }

  try {
    // Check if value is within min/max bounds
    if (value < range->min || value > range->max) {
      *valid = 0;
      return DUVC_SUCCESS;
    }

    // Check if value aligns with step size
    if (range->step > 0) {
      int32_t offset = value - range->min;
      if (offset % range->step != 0) {
        *valid = 0;
        return DUVC_SUCCESS;
      }
    }

    *valid = 1;
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to validate property range: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_prop_range_clamp(const duvc_prop_range_t *range,
                                    int32_t value, int32_t *clamped_value) {
  if (!range || !clamped_value) {
    return DUVC_ERROR_INVALID_ARGUMENT;
  }

  try {
    int32_t clamped = value;

    // Clamp to min/max bounds
    if (clamped < range->min) {
      clamped = range->min;
    } else if (clamped > range->max) {
      clamped = range->max;
    }

    // Align to step size if specified
    if (range->step > 0) {
      int32_t offset = clamped - range->min;
      int32_t remainder = offset % range->step;
      if (remainder != 0) {
        // Round to nearest step
        if (remainder < range->step / 2) {
          clamped -= remainder;
        } else {
          clamped += (range->step - remainder);
        }

        // Ensure we didn't exceed max after rounding
        if (clamped > range->max) {
          clamped = range->max - (range->max - range->min) % range->step;
        }
      }
    }

    *clamped_value = clamped;
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to clamp property value: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

duvc_result_t duvc_prop_capability_supports_auto(const duvc_prop_range_t *range,
                                                 int *supports_auto) {
  if (!range || !supports_auto) {
    return DUVC_ERROR_INVALID_ARGUMENT;
  }

  try {
    // Check if the default mode is auto - this indicates auto mode support
    *supports_auto = (range->default_mode == DUVC_CAM_MODE_AUTO) ? 1 : 0;
    return DUVC_SUCCESS;
  } catch (const std::exception &e) {
    g_last_error_details =
        std::string("Failed to check auto mode support: ") + e.what();
    return DUVC_ERROR_SYSTEM_ERROR;
  }
}

/* ========================================================================
 * Error Handling and Diagnostics
 * ======================================================================== */

duvc_result_t duvc_get_last_error_details(char *buffer, size_t buffer_size,
                                          size_t *required_size) {
  return copy_string_to_buffer(g_last_error_details, buffer, buffer_size,
                               required_size);
}

void duvc_clear_last_error(void) { g_last_error_details.clear(); }

} // extern "C"