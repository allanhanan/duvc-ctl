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
#include "duvc-ctl/core/types.h"
#include "duvc-ctl/core/result.h"
#include "duvc-ctl/core/device.h"
#include "duvc-ctl/platform/interface.h"
#include "duvc-ctl/platform/windows/connection_pool.h"
#include "duvc-ctl/utils/logging.h"
#include "duvc-ctl/utils/string_conversion.h"
#include "duvc-ctl/utils/error_decoder.h"
#include "duvc-ctl/vendor/logitech.h"

#ifdef _WIN32
#include "duvc-ctl/platform/windows/ks_properties.h"
#include "duvc-ctl/vendor/constants.h"
#endif

#include <memory>
#include <vector>
#include <string>
#include <mutex>
#include <unordered_map>
#include <atomic>
#include <codecvt>
#include <locale>
#include <cstring>
#include <algorithm>
#include <sstream>

// Version information - should be defined in a version header
#ifndef DUVC_ABI_VERSION
#define DUVC_ABI_VERSION ((2 << 16) | (0 << 8) | 0)  // 2.0.0
#endif

#ifndef DUVC_ABI_VERSION_STRING
#define DUVC_ABI_VERSION_STRING "2.0.0"
#endif

// Global state management
namespace {
    /** @brief Global initialization state */
    std::atomic<bool> g_initialized{false};
    
    /** @brief Global library mutex for thread safety */
    std::mutex g_library_mutex;
    
    /** @brief Platform interface instance */
    std::unique_ptr<duvc::IPlatformInterface> g_platform_interface;
    
    /** @brief Thread-local error details storage */
    thread_local std::string g_last_error_details;
    
    /** @brief Log callback state */
    duvc_log_callback_t g_log_callback = nullptr;
    void* g_log_callback_user_data = nullptr;
    std::mutex g_log_mutex;
    
    /** @brief Hotplug callback state */
    duvc_hotplug_callback_t g_hotplug_callback = nullptr;
    void* g_hotplug_callback_user_data = nullptr;
    
    /** @brief Device storage for C API lifetime management */
    std::vector<std::unique_ptr<duvc::Device>> g_device_storage;
    std::mutex g_device_storage_mutex;
    
    /** @brief Connection storage for C API */
    std::unordered_map<duvc_connection_t*, std::unique_ptr<duvc::DeviceConnection>> g_connections;
    std::mutex g_connection_mutex;

    /**
     * @brief Convert C++ string to UTF-8 C string with buffer management
     * @param cpp_str C++ string to convert
     * @param buffer Output buffer (can be nullptr to query size)
     * @param buffer_size Size of output buffer
     * @param required_size Required buffer size (including null terminator)
     * @return DUVC_SUCCESS or DUVC_ERROR_BUFFER_TOO_SMALL
     */
    duvc_result_t copy_string_to_buffer(const std::string& cpp_str, 
                                        char* buffer, 
                                        size_t buffer_size,
                                        size_t* required_size) {
        size_t needed = cpp_str.length() + 1;
        if (required_size) *required_size = needed;
        
        if (!buffer || buffer_size < needed) {
            return DUVC_ERROR_BUFFER_TOO_SMALL;
        }
        
        std::memcpy(buffer, cpp_str.c_str(), needed);
        return DUVC_SUCCESS;
    }

    /**
     * @brief Convert wide string to UTF-8 with buffer management
     * @param wide_str Wide string to convert
     * @param buffer Output buffer (can be nullptr to query size)
     * @param buffer_size Size of output buffer
     * @param required_size Required buffer size (including null terminator)
     * @return DUVC_SUCCESS or DUVC_ERROR_BUFFER_TOO_SMALL
     */
    duvc_result_t copy_wstring_to_buffer(const std::wstring& wide_str,
                                         char* buffer,
                                         size_t buffer_size,
                                         size_t* required_size) {
        try {
            // Convert wide string to UTF-8
            std::wstring_convert<std::codecvt_utf8<wchar_t>> converter;
            std::string utf8_str = converter.to_bytes(wide_str);
            return copy_string_to_buffer(utf8_str, buffer, buffer_size, required_size);
        } catch (const std::exception& e) {
            g_last_error_details = std::string("String conversion failed: ") + e.what();
            if (required_size) *required_size = 0;
            return DUVC_ERROR_SYSTEM_ERROR;
        }
    }

    /**
     * @brief Convert C++ ErrorCode to C duvc_result_t
     */
    duvc_result_t convert_error_code(duvc::ErrorCode code) {
        switch (code) {
            case duvc::ErrorCode::Success: return DUVC_SUCCESS;
            case duvc::ErrorCode::DeviceNotFound: return DUVC_ERROR_DEVICE_NOT_FOUND;
            case duvc::ErrorCode::DeviceBusy: return DUVC_ERROR_DEVICE_BUSY;
            case duvc::ErrorCode::PropertyNotSupported: return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
            case duvc::ErrorCode::InvalidValue: return DUVC_ERROR_INVALID_VALUE;
            case duvc::ErrorCode::PermissionDenied: return DUVC_ERROR_PERMISSION_DENIED;
            case duvc::ErrorCode::SystemError: return DUVC_ERROR_SYSTEM_ERROR;
            case duvc::ErrorCode::InvalidArgument: return DUVC_ERROR_INVALID_ARGUMENT;
            case duvc::ErrorCode::NotImplemented: return DUVC_ERROR_NOT_IMPLEMENTED;
            default: return DUVC_ERROR_SYSTEM_ERROR;
        }
    }

    /**
     * @brief Handle C++ Result and store error details
     */
    template<typename T>
    duvc_result_t handle_cpp_result(const duvc::Result<T>& result) {
        if (result.is_ok()) {
            g_last_error_details.clear();
            return DUVC_SUCCESS;
        }
        
        const auto& error = result.error();
        g_last_error_details = error.description();
        return convert_error_code(error.code());
    }

    /**
     * @brief Convert C enums to C++ enums
     */
    duvc::CamProp convert_cam_prop(duvc_cam_prop_t prop) {
        return static_cast<duvc::CamProp>(prop);
    }

    duvc::VidProp convert_vid_prop(duvc_vid_prop_t prop) {
        return static_cast<duvc::VidProp>(prop);
    }

    duvc_cam_mode_t convert_cam_mode_to_c(duvc::CamMode mode) {
        return (mode == duvc::CamMode::Auto) ? DUVC_CAM_MODE_AUTO : DUVC_CAM_MODE_MANUAL;
    }

    duvc::CamMode convert_cam_mode_from_c(duvc_cam_mode_t mode) {
        return (mode == DUVC_CAM_MODE_AUTO) ? duvc::CamMode::Auto : duvc::CamMode::Manual;
    }

    /**
     * @brief Convert between C and C++ property structures
     */
    duvc_prop_setting_t convert_prop_setting_to_c(const duvc::PropSetting& setting) {
        duvc_prop_setting_t c_setting;
        c_setting.value = setting.value;
        c_setting.mode = convert_cam_mode_to_c(setting.mode);
        return c_setting;
    }

    duvc::PropSetting convert_prop_setting_from_c(const duvc_prop_setting_t& c_setting) {
        return duvc::PropSetting(c_setting.value, convert_cam_mode_from_c(c_setting.mode));
    }

    duvc_prop_range_t convert_prop_range_to_c(const duvc::PropRange& range) {
        duvc_prop_range_t c_range;
        c_range.min = range.min;
        c_range.max = range.max;
        c_range.step = range.step;
        c_range.default_val = range.default_val;
        c_range.default_mode = convert_cam_mode_to_c(range.default_mode);
        return c_range;
    }

    /**
     * @brief C++ log callback wrapper
     */
    void cpp_log_callback_wrapper(duvc::LogLevel level, const std::string& message) {
        std::lock_guard<std::mutex> lock(g_log_mutex);
        if (g_log_callback) {
            duvc_log_level_t c_level = static_cast<duvc_log_level_t>(static_cast<int>(level));
            try {
                g_log_callback(c_level, message.c_str(), g_log_callback_user_data);
            } catch (...) {
                // Ignore exceptions from user callback
            }
        }
    }
}

extern "C" {

/* ========================================================================
 * Version and ABI Management
 * ======================================================================== */

uint32_t duvc_get_version(void) {
    return DUVC_ABI_VERSION;
}

const char* duvc_get_version_string(void) {
    return DUVC_ABI_VERSION_STRING;
}

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
 * Library Management
 * ======================================================================== */

duvc_result_t duvc_initialize(void) {
    std::lock_guard<std::mutex> lock(g_library_mutex);
    
    if (g_initialized.load()) {
        return DUVC_SUCCESS; // Already initialized
    }
    
    try {
        // Clear any previous error state
        g_last_error_details.clear();
        
        // Initialize platform interface
        g_platform_interface = duvc::create_platform_interface();
        if (!g_platform_interface) {
            g_last_error_details = "Failed to create platform interface - platform not supported";
            return DUVC_ERROR_NOT_IMPLEMENTED;
        }
        
        // Initialize logging with default level
        duvc::set_log_level(duvc::LogLevel::Info);
        
        // Clear storage containers
        g_device_storage.clear();
        g_connections.clear();
        
        g_initialized.store(true);
        duvc::log_info("duvc-ctl C API initialized successfully");
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
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
        
        // Clear callbacks
        {
            std::lock_guard<std::mutex> log_lock(g_log_mutex);
            g_log_callback = nullptr;
            g_log_callback_user_data = nullptr;
        }
        
        g_hotplug_callback = nullptr;
        g_hotplug_callback_user_data = nullptr;
        
        // Reset platform interface
        g_platform_interface.reset();
        
        g_initialized.store(false);
        duvc::log_info("duvc-ctl C API shutdown complete");
        
    } catch (...) {
        // Ignore exceptions during shutdown
    }
}

int duvc_is_initialized(void) {
    return g_initialized.load() ? 1 : 0;
}

/* ========================================================================
 * Logging System
 * ======================================================================== */

duvc_result_t duvc_set_log_callback(duvc_log_callback_t callback, void* user_data) {
    if (!g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
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
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to set log callback: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_set_log_level(duvc_log_level_t level) {
    if (!g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        duvc::LogLevel cpp_level = static_cast<duvc::LogLevel>(static_cast<int>(level));
        duvc::set_log_level(cpp_level);
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to set log level: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_get_log_level(duvc_log_level_t* level) {
    if (!level || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        duvc::LogLevel cpp_level = duvc::get_log_level();
        *level = static_cast<duvc_log_level_t>(static_cast<int>(cpp_level));
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get log level: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_log_message(duvc_log_level_t level, const char* message) {
    if (!message || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        duvc::LogLevel cpp_level = static_cast<duvc::LogLevel>(static_cast<int>(level));
        duvc::log_message(cpp_level, std::string(message));
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        // Don't update error details to avoid recursion
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

/* ========================================================================
 * Device Enumeration and Management
 * ======================================================================== */

duvc_result_t duvc_list_devices(duvc_device_t*** devices, size_t* count) {
    if (!devices || !count || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        std::lock_guard<std::mutex> lock(g_device_storage_mutex);
        
        // Clear previous device storage
        g_device_storage.clear();
        
        // Get devices from platform interface
        auto result = g_platform_interface->list_devices();
        if (!result.is_ok()) {
            return handle_cpp_result(result);
        }
        
        const auto& device_list = result.value();
        
        // Allocate C device array
        duvc_device_t** c_devices = static_cast<duvc_device_t**>(
            std::malloc(device_list.size() * sizeof(duvc_device_t*)));
        if (!c_devices && device_list.size() > 0) {
            g_last_error_details = "Failed to allocate memory for device list";
            return DUVC_ERROR_SYSTEM_ERROR;
        }
        
        // Store devices and create C pointers
        for (size_t i = 0; i < device_list.size(); ++i) {
            auto stored_device = std::make_unique<duvc::Device>(device_list[i]);
            c_devices[i] = reinterpret_cast<duvc_device_t*>(stored_device.get());
            g_device_storage.push_back(std::move(stored_device));
        }
        
        *devices = c_devices;
        *count = device_list.size();
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to list devices: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

void duvc_free_device_list(duvc_device_t** devices, size_t count) {
    if (devices) {
        std::free(devices);
    }
    // Note: Individual devices are managed by g_device_storage
}

duvc_result_t duvc_is_device_connected(const duvc_device_t* device, int* connected) {
    if (!device || !connected || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        auto result = g_platform_interface->is_device_connected(*cpp_device);
        
        if (!result.is_ok()) {
            return handle_cpp_result(result);
        }
        
        *connected = result.value() ? 1 : 0;
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to check device connection: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_get_device_name(const duvc_device_t* device, 
                                   char* name_buffer, 
                                   size_t buffer_size,
                                   size_t* required_size) {
    if (!device || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        return copy_wstring_to_buffer(cpp_device->name, name_buffer, buffer_size, required_size);
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get device name: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_get_device_path(const duvc_device_t* device,
                                   char* path_buffer,
                                   size_t buffer_size,
                                   size_t* required_size) {
    if (!device || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        return copy_wstring_to_buffer(cpp_device->path, path_buffer, buffer_size, required_size);
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get device path: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_enable_hotplug_monitoring(duvc_hotplug_callback_t callback, void* user_data) {
    if (!g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    // Store callback information
    g_hotplug_callback = callback;
    g_hotplug_callback_user_data = user_data;
    
    // Note: Actual hotplug implementation would go here
    // This is a placeholder for the platform-specific implementation
    g_last_error_details = "Hotplug monitoring not yet implemented";
    return DUVC_ERROR_NOT_IMPLEMENTED;
}

duvc_result_t duvc_disable_hotplug_monitoring(void) {
    if (!g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    g_hotplug_callback = nullptr;
    g_hotplug_callback_user_data = nullptr;
    
    // Note: Actual hotplug cleanup would go here
    return DUVC_SUCCESS;
}

/* ========================================================================
 * Connection Management
 * ======================================================================== */

duvc_result_t duvc_create_connection(const duvc_device_t* device, duvc_connection_t** connection) {
    if (!device || !connection || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        std::lock_guard<std::mutex> lock(g_connection_mutex);
        
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Create new connection
        auto cpp_connection = std::make_unique<duvc::DeviceConnection>(*cpp_device);
        if (!cpp_connection->is_valid()) {
            g_last_error_details = "Failed to establish device connection";
            return DUVC_ERROR_CONNECTION_FAILED;
        }
        
        // Store connection and return handle
        duvc_connection_t* handle = reinterpret_cast<duvc_connection_t*>(cpp_connection.get());
        g_connections[handle] = std::move(cpp_connection);
        *connection = handle;
        
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to create connection: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_close_connection(duvc_connection_t* connection) {
    if (!connection || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        std::lock_guard<std::mutex> lock(g_connection_mutex);
        
        auto it = g_connections.find(connection);
        if (it == g_connections.end()) {
            g_last_error_details = "Invalid connection handle";
            return DUVC_ERROR_INVALID_ARGUMENT;
        }
        
        g_connections.erase(it);
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to close connection: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_is_connection_valid(const duvc_connection_t* connection, int* valid) {
    if (!connection || !valid || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        std::lock_guard<std::mutex> lock(g_connection_mutex);
        
        auto it = g_connections.find(const_cast<duvc_connection_t*>(connection));
        if (it == g_connections.end()) {
            *valid = 0;
            return DUVC_SUCCESS;
        }
        
        *valid = it->second->is_valid() ? 1 : 0;
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to check connection validity: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

/* ========================================================================
 * Camera Property Operations
 * ======================================================================== */

duvc_result_t duvc_get_camera_property(const duvc_device_t* device,
                                       duvc_cam_prop_t prop,
                                       duvc_prop_setting_t* setting) {
    if (!device || !setting || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Use cached connection for efficiency
        duvc::DeviceConnection* conn = duvc::get_cached_connection(*cpp_device);
        if (!conn) {
            g_last_error_details = "Failed to get device connection";
            return DUVC_ERROR_CONNECTION_FAILED;
        }
        
        duvc::PropSetting cpp_setting;
        if (conn->get(convert_cam_prop(prop), cpp_setting)) {
            *setting = convert_prop_setting_to_c(cpp_setting);
            return DUVC_SUCCESS;
        }
        
        g_last_error_details = "Camera property not supported or failed to retrieve";
        return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get camera property: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_set_camera_property(const duvc_device_t* device,
                                       duvc_cam_prop_t prop,
                                       const duvc_prop_setting_t* setting) {
    if (!device || !setting || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Use cached connection for efficiency
        duvc::DeviceConnection* conn = duvc::get_cached_connection(*cpp_device);
        if (!conn) {
            g_last_error_details = "Failed to get device connection";
            return DUVC_ERROR_CONNECTION_FAILED;
        }
        
        duvc::PropSetting cpp_setting = convert_prop_setting_from_c(*setting);
        if (conn->set(convert_cam_prop(prop), cpp_setting)) {
            return DUVC_SUCCESS;
        }
        
        g_last_error_details = "Camera property not supported or failed to set";
        return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to set camera property: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_get_camera_property_range(const duvc_device_t* device,
                                             duvc_cam_prop_t prop,
                                             duvc_prop_range_t* range) {
    if (!device || !range || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Use cached connection for efficiency
        duvc::DeviceConnection* conn = duvc::get_cached_connection(*cpp_device);
        if (!conn) {
            g_last_error_details = "Failed to get device connection";
            return DUVC_ERROR_CONNECTION_FAILED;
        }
        
        duvc::PropRange cpp_range;
        if (conn->get_range(convert_cam_prop(prop), cpp_range)) {
            *range = convert_prop_range_to_c(cpp_range);
            return DUVC_SUCCESS;
        }
        
        g_last_error_details = "Camera property range not supported or failed to retrieve";
        return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get camera property range: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_get_multiple_camera_properties(const duvc_device_t* device,
                                                  const duvc_cam_prop_t* props,
                                                  duvc_prop_setting_t* settings,
                                                  size_t count) {
    if (!device || !props || !settings || count == 0 || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Use cached connection for efficiency
        duvc::DeviceConnection* conn = duvc::get_cached_connection(*cpp_device);
        if (!conn) {
            g_last_error_details = "Failed to get device connection";
            return DUVC_ERROR_CONNECTION_FAILED;
        }
        
        // Get each property individually
        for (size_t i = 0; i < count; ++i) {
            duvc::PropSetting cpp_setting;
            if (conn->get(convert_cam_prop(props[i]), cpp_setting)) {
                settings[i] = convert_prop_setting_to_c(cpp_setting);
            } else {
                g_last_error_details = "Failed to get camera property at index " + std::to_string(i);
                return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
            }
        }
        
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get multiple camera properties: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_set_multiple_camera_properties(const duvc_device_t* device,
                                                  const duvc_cam_prop_t* props,
                                                  const duvc_prop_setting_t* settings,
                                                  size_t count) {
    if (!device || !props || !settings || count == 0 || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Use cached connection for efficiency
        duvc::DeviceConnection* conn = duvc::get_cached_connection(*cpp_device);
        if (!conn) {
            g_last_error_details = "Failed to get device connection";
            return DUVC_ERROR_CONNECTION_FAILED;
        }
        
        // Set each property individually
        for (size_t i = 0; i < count; ++i) {
            duvc::PropSetting cpp_setting = convert_prop_setting_from_c(settings[i]);
            if (!conn->set(convert_cam_prop(props[i]), cpp_setting)) {
                g_last_error_details = "Failed to set camera property at index " + std::to_string(i);
                return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
            }
        }
        
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to set multiple camera properties: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

/* ========================================================================
 * Connection-Based Camera Property Operations
 * ======================================================================== */

duvc_result_t duvc_connection_get_camera_property(duvc_connection_t* connection,
                                                  duvc_cam_prop_t prop,
                                                  duvc_prop_setting_t* setting) {
    if (!connection || !setting || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        std::lock_guard<std::mutex> lock(g_connection_mutex);
        
        auto it = g_connections.find(connection);
        if (it == g_connections.end()) {
            g_last_error_details = "Invalid connection handle";
            return DUVC_ERROR_INVALID_ARGUMENT;
        }
        
        duvc::PropSetting cpp_setting;
        if (it->second->get(convert_cam_prop(prop), cpp_setting)) {
            *setting = convert_prop_setting_to_c(cpp_setting);
            return DUVC_SUCCESS;
        }
        
        g_last_error_details = "Camera property not supported";
        return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get camera property via connection: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_connection_set_camera_property(duvc_connection_t* connection,
                                                  duvc_cam_prop_t prop,
                                                  const duvc_prop_setting_t* setting) {
    if (!connection || !setting || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        std::lock_guard<std::mutex> lock(g_connection_mutex);
        
        auto it = g_connections.find(connection);
        if (it == g_connections.end()) {
            g_last_error_details = "Invalid connection handle";
            return DUVC_ERROR_INVALID_ARGUMENT;
        }
        
        duvc::PropSetting cpp_setting = convert_prop_setting_from_c(*setting);
        if (it->second->set(convert_cam_prop(prop), cpp_setting)) {
            return DUVC_SUCCESS;
        }
        
        g_last_error_details = "Camera property not supported";
        return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to set camera property via connection: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_connection_get_camera_property_range(duvc_connection_t* connection,
                                                        duvc_cam_prop_t prop,
                                                        duvc_prop_range_t* range) {
    if (!connection || !range || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        std::lock_guard<std::mutex> lock(g_connection_mutex);
        
        auto it = g_connections.find(connection);
        if (it == g_connections.end()) {
            g_last_error_details = "Invalid connection handle";
            return DUVC_ERROR_INVALID_ARGUMENT;
        }
        
        duvc::PropRange cpp_range;
        if (it->second->get_range(convert_cam_prop(prop), cpp_range)) {
            *range = convert_prop_range_to_c(cpp_range);
            return DUVC_SUCCESS;
        }
        
        g_last_error_details = "Camera property range not supported";
        return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get camera property range via connection: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

/* ========================================================================
 * Video Processing Property Operations
 * ======================================================================== */

duvc_result_t duvc_get_video_property(const duvc_device_t* device,
                                      duvc_vid_prop_t prop,
                                      duvc_prop_setting_t* setting) {
    if (!device || !setting || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Use cached connection for efficiency
        duvc::DeviceConnection* conn = duvc::get_cached_connection(*cpp_device);
        if (!conn) {
            g_last_error_details = "Failed to get device connection";
            return DUVC_ERROR_CONNECTION_FAILED;
        }
        
        duvc::PropSetting cpp_setting;
        if (conn->get(convert_vid_prop(prop), cpp_setting)) {
            *setting = convert_prop_setting_to_c(cpp_setting);
            return DUVC_SUCCESS;
        }
        
        g_last_error_details = "Video property not supported or failed to retrieve";
        return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get video property: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_set_video_property(const duvc_device_t* device,
                                      duvc_vid_prop_t prop,
                                      const duvc_prop_setting_t* setting) {
    if (!device || !setting || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Use cached connection for efficiency
        duvc::DeviceConnection* conn = duvc::get_cached_connection(*cpp_device);
        if (!conn) {
            g_last_error_details = "Failed to get device connection";
            return DUVC_ERROR_CONNECTION_FAILED;
        }
        
        duvc::PropSetting cpp_setting = convert_prop_setting_from_c(*setting);
        if (conn->set(convert_vid_prop(prop), cpp_setting)) {
            return DUVC_SUCCESS;
        }
        
        g_last_error_details = "Video property not supported or failed to set";
        return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to set video property: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_get_video_property_range(const duvc_device_t* device,
                                            duvc_vid_prop_t prop,
                                            duvc_prop_range_t* range) {
    if (!device || !range || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Use cached connection for efficiency
        duvc::DeviceConnection* conn = duvc::get_cached_connection(*cpp_device);
        if (!conn) {
            g_last_error_details = "Failed to get device connection";
            return DUVC_ERROR_CONNECTION_FAILED;
        }
        
        duvc::PropRange cpp_range;
        if (conn->get_range(convert_vid_prop(prop), cpp_range)) {
            *range = convert_prop_range_to_c(cpp_range);
            return DUVC_SUCCESS;
        }
        
        g_last_error_details = "Video property range not supported or failed to retrieve";
        return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get video property range: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_get_multiple_video_properties(const duvc_device_t* device,
                                                 const duvc_vid_prop_t* props,
                                                 duvc_prop_setting_t* settings,
                                                 size_t count) {
    if (!device || !props || !settings || count == 0 || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Use cached connection for efficiency
        duvc::DeviceConnection* conn = duvc::get_cached_connection(*cpp_device);
        if (!conn) {
            g_last_error_details = "Failed to get device connection";
            return DUVC_ERROR_CONNECTION_FAILED;
        }
        
        // Get each property individually
        for (size_t i = 0; i < count; ++i) {
            duvc::PropSetting cpp_setting;
            if (conn->get(convert_vid_prop(props[i]), cpp_setting)) {
                settings[i] = convert_prop_setting_to_c(cpp_setting);
            } else {
                g_last_error_details = "Failed to get video property at index " + std::to_string(i);
                return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
            }
        }
        
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get multiple video properties: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_set_multiple_video_properties(const duvc_device_t* device,
                                                 const duvc_vid_prop_t* props,
                                                 const duvc_prop_setting_t* settings,
                                                 size_t count) {
    if (!device || !props || !settings || count == 0 || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Use cached connection for efficiency
        duvc::DeviceConnection* conn = duvc::get_cached_connection(*cpp_device);
        if (!conn) {
            g_last_error_details = "Failed to get device connection";
            return DUVC_ERROR_CONNECTION_FAILED;
        }
        
        // Set each property individually
        for (size_t i = 0; i < count; ++i) {
            duvc::PropSetting cpp_setting = convert_prop_setting_from_c(settings[i]);
            if (!conn->set(convert_vid_prop(props[i]), cpp_setting)) {
                g_last_error_details = "Failed to set video property at index " + std::to_string(i);
                return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
            }
        }
        
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to set multiple video properties: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

/* ========================================================================
 * Connection-Based Video Property Operations
 * ======================================================================== */

duvc_result_t duvc_connection_get_video_property(duvc_connection_t* connection,
                                                 duvc_vid_prop_t prop,
                                                 duvc_prop_setting_t* setting) {
    if (!connection || !setting || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        std::lock_guard<std::mutex> lock(g_connection_mutex);
        
        auto it = g_connections.find(connection);
        if (it == g_connections.end()) {
            g_last_error_details = "Invalid connection handle";
            return DUVC_ERROR_INVALID_ARGUMENT;
        }
        
        duvc::PropSetting cpp_setting;
        if (it->second->get(convert_vid_prop(prop), cpp_setting)) {
            *setting = convert_prop_setting_to_c(cpp_setting);
            return DUVC_SUCCESS;
        }
        
        g_last_error_details = "Video property not supported";
        return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get video property via connection: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_connection_set_video_property(duvc_connection_t* connection,
                                                 duvc_vid_prop_t prop,
                                                 const duvc_prop_setting_t* setting) {
    if (!connection || !setting || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        std::lock_guard<std::mutex> lock(g_connection_mutex);
        
        auto it = g_connections.find(connection);
        if (it == g_connections.end()) {
            g_last_error_details = "Invalid connection handle";
            return DUVC_ERROR_INVALID_ARGUMENT;
        }
        
        duvc::PropSetting cpp_setting = convert_prop_setting_from_c(*setting);
        if (it->second->set(convert_vid_prop(prop), cpp_setting)) {
            return DUVC_SUCCESS;
        }
        
        g_last_error_details = "Video property not supported";
        return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to set video property via connection: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_connection_get_video_property_range(duvc_connection_t* connection,
                                                       duvc_vid_prop_t prop,
                                                       duvc_prop_range_t* range) {
    if (!connection || !range || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        std::lock_guard<std::mutex> lock(g_connection_mutex);
        
        auto it = g_connections.find(connection);
        if (it == g_connections.end()) {
            g_last_error_details = "Invalid connection handle";
            return DUVC_ERROR_INVALID_ARGUMENT;
        }
        
        duvc::PropRange cpp_range;
        if (it->second->get_range(convert_vid_prop(prop), cpp_range)) {
            *range = convert_prop_range_to_c(cpp_range);
            return DUVC_SUCCESS;
        }
        
        g_last_error_details = "Video property range not supported";
        return DUVC_ERROR_PROPERTY_NOT_SUPPORTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get video property range via connection: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

/* ========================================================================
 * Vendor Property Operations
 * ======================================================================== */

duvc_result_t duvc_get_vendor_property(const duvc_device_t* device,
                                       const char* property_set_guid,
                                       uint32_t property_id,
                                       void* data,
                                       size_t* data_size) {
    if (!device || !property_set_guid || !data_size || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
#ifdef _WIN32
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // For now, this is a placeholder for full GUID parsing implementation
        // A complete implementation would parse the GUID string and use KsPropertySet
        g_last_error_details = "Generic vendor property support not yet fully implemented";
        return DUVC_ERROR_NOT_IMPLEMENTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get vendor property: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
#else
    g_last_error_details = "Vendor properties not supported on this platform";
    return DUVC_ERROR_NOT_IMPLEMENTED;
#endif
}

duvc_result_t duvc_set_vendor_property(const duvc_device_t* device,
                                       const char* property_set_guid,
                                       uint32_t property_id,
                                       const void* data,
                                       size_t data_size) {
    if (!device || !property_set_guid || !data || data_size == 0 || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
#ifdef _WIN32
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // For now, this is a placeholder for full GUID parsing implementation
        g_last_error_details = "Generic vendor property support not yet fully implemented";
        return DUVC_ERROR_NOT_IMPLEMENTED;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to set vendor property: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
#else
    g_last_error_details = "Vendor properties not supported on this platform";
    return DUVC_ERROR_NOT_IMPLEMENTED;
#endif
}

duvc_result_t duvc_query_vendor_property_support(const duvc_device_t* device,
                                                  const char* property_set_guid,
                                                  uint32_t property_id,
                                                  int* supported) {
    if (!device || !property_set_guid || !supported || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
#ifdef _WIN32
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // For now, assume not supported
        *supported = 0;
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to query vendor property support: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
#else
    *supported = 0;
    return DUVC_SUCCESS;
#endif
}

/* ========================================================================
 * Logitech Vendor Properties
 * ======================================================================== */

duvc_result_t duvc_supports_logitech_properties(const duvc_device_t* device, int* supported) {
    if (!device || !supported || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
#ifdef _WIN32
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        auto result = duvc::logitech::supports_logitech_properties(*cpp_device);
        
        if (!result.is_ok()) {
            return handle_cpp_result(result);
        }
        
        *supported = result.value() ? 1 : 0;
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to check Logitech support: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
#else
    *supported = 0;
    return DUVC_SUCCESS;
#endif
}

duvc_result_t duvc_get_logitech_property_int32(const duvc_device_t* device,
                                               duvc_logitech_prop_t prop,
                                               int32_t* value) {
    if (!device || !value || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
#ifdef _WIN32
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Map C enum to C++ enum (would need proper mapping)
        duvc::logitech::LogitechProperty cpp_prop = 
            static_cast<duvc::logitech::LogitechProperty>(prop);
        
        auto result = duvc::logitech::get_logitech_property_typed<int32_t>(*cpp_device, cpp_prop);
        
        if (!result.is_ok()) {
            return handle_cpp_result(result);
        }
        
        *value = result.value();
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get Logitech property: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
#else
    g_last_error_details = "Logitech properties not supported on this platform";
    return DUVC_ERROR_NOT_IMPLEMENTED;
#endif
}

duvc_result_t duvc_set_logitech_property_int32(const duvc_device_t* device,
                                               duvc_logitech_prop_t prop,
                                               int32_t value) {
    if (!device || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
#ifdef _WIN32
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Map C enum to C++ enum (would need proper mapping)
        duvc::logitech::LogitechProperty cpp_prop = 
            static_cast<duvc::logitech::LogitechProperty>(prop);
        
        auto result = duvc::logitech::set_logitech_property_typed<int32_t>(*cpp_device, cpp_prop, value);
        
        return handle_cpp_result(result);
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to set Logitech property: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
#else
    g_last_error_details = "Logitech properties not supported on this platform";
    return DUVC_ERROR_NOT_IMPLEMENTED;
#endif
}

duvc_result_t duvc_get_logitech_property_data(const duvc_device_t* device,
                                              duvc_logitech_prop_t prop,
                                              void* data,
                                              size_t* data_size) {
    if (!device || !data_size || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
#ifdef _WIN32
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Map C enum to C++ enum (would need proper mapping)
        duvc::logitech::LogitechProperty cpp_prop = 
            static_cast<duvc::logitech::LogitechProperty>(prop);
        
        auto result = duvc::logitech::get_logitech_property(*cpp_device, cpp_prop);
        
        if (!result.is_ok()) {
            return handle_cpp_result(result);
        }
        
        const auto& property_data = result.value();
        
        if (!data || *data_size < property_data.size()) {
            *data_size = property_data.size();
            return DUVC_ERROR_BUFFER_TOO_SMALL;
        }
        
        std::memcpy(data, property_data.data(), property_data.size());
        *data_size = property_data.size();
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get Logitech property data: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
#else
    g_last_error_details = "Logitech properties not supported on this platform";
    return DUVC_ERROR_NOT_IMPLEMENTED;
#endif
}

duvc_result_t duvc_set_logitech_property_data(const duvc_device_t* device,
                                              duvc_logitech_prop_t prop,
                                              const void* data,
                                              size_t data_size) {
    if (!device || !data || data_size == 0 || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
#ifdef _WIN32
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Map C enum to C++ enum (would need proper mapping)
        duvc::logitech::LogitechProperty cpp_prop = 
            static_cast<duvc::logitech::LogitechProperty>(prop);
        
        std::vector<uint8_t> property_data(static_cast<const uint8_t*>(data),
                                          static_cast<const uint8_t*>(data) + data_size);
        
        auto result = duvc::logitech::set_logitech_property(*cpp_device, cpp_prop, property_data);
        
        return handle_cpp_result(result);
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to set Logitech property data: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
#else
    g_last_error_details = "Logitech properties not supported on this platform";
    return DUVC_ERROR_NOT_IMPLEMENTED;
#endif
}

/* ========================================================================
 * Advanced Error Handling and Diagnostics
 * ======================================================================== */

const char* duvc_get_error_string(duvc_result_t result) {
    switch (result) {
        case DUVC_SUCCESS: return "Success";
        case DUVC_ERROR_DEVICE_NOT_FOUND: return "Device not found";
        case DUVC_ERROR_DEVICE_BUSY: return "Device busy";
        case DUVC_ERROR_PROPERTY_NOT_SUPPORTED: return "Property not supported";
        case DUVC_ERROR_INVALID_VALUE: return "Invalid value";
        case DUVC_ERROR_PERMISSION_DENIED: return "Permission denied";
        case DUVC_ERROR_SYSTEM_ERROR: return "System error";
        case DUVC_ERROR_INVALID_ARGUMENT: return "Invalid argument";
        case DUVC_ERROR_NOT_IMPLEMENTED: return "Not implemented";
        case DUVC_ERROR_CONNECTION_FAILED: return "Connection failed";
        case DUVC_ERROR_TIMEOUT: return "Timeout";
        case DUVC_ERROR_BUFFER_TOO_SMALL: return "Buffer too small";
        default: return "Unknown error";
    }
}

duvc_result_t duvc_get_last_error_details(char* buffer, size_t buffer_size, size_t* required_size) {
    return copy_string_to_buffer(g_last_error_details, buffer, buffer_size, required_size);
}

duvc_result_t duvc_get_diagnostic_info(char* buffer, size_t buffer_size, size_t* required_size) {
    try {
        std::string diagnostic_info = duvc::get_diagnostic_info();
        return copy_string_to_buffer(diagnostic_info, buffer, buffer_size, required_size);
        
    } catch (const std::exception& e) {
        std::string error_msg = std::string("Failed to get diagnostic info: ") + e.what();
        return copy_string_to_buffer(error_msg, buffer, buffer_size, required_size);
    }
}

int duvc_is_device_error(duvc_result_t result) {
    switch (result) {
        case DUVC_ERROR_DEVICE_NOT_FOUND:
        case DUVC_ERROR_DEVICE_BUSY:
        case DUVC_ERROR_CONNECTION_FAILED:
            return 1;
        default:
            return 0;
    }
}

int duvc_is_permission_error(duvc_result_t result) {
    return (result == DUVC_ERROR_PERMISSION_DENIED) ? 1 : 0;
}

void duvc_clear_last_error(void) {
    g_last_error_details.clear();
}

/* ========================================================================
 * String Conversion Utilities
 * ======================================================================== */

const char* duvc_get_camera_property_name(duvc_cam_prop_t prop) {
    try {
        return duvc::to_string(convert_cam_prop(prop));
    } catch (...) {
        return "Unknown";
    }
}

const char* duvc_get_video_property_name(duvc_vid_prop_t prop) {
    try {
        return duvc::to_string(convert_vid_prop(prop));
    } catch (...) {
        return "Unknown";
    }
}

const char* duvc_get_camera_mode_name(duvc_cam_mode_t mode) {
    try {
        return duvc::to_string(convert_cam_mode_from_c(mode));
    } catch (...) {
        return "Unknown";
    }
}

const char* duvc_get_log_level_name(duvc_log_level_t level) {
    try {
        duvc::LogLevel cpp_level = static_cast<duvc::LogLevel>(static_cast<int>(level));
        return duvc::to_string(cpp_level);
    } catch (...) {
        return "Unknown";
    }
}

const char* duvc_get_logitech_property_name(duvc_logitech_prop_t prop) {
    // Map Logitech property enum values to names
    switch (prop) {
        case DUVC_LOGITECH_PROP_RIGHT_LIGHT: return "RightLight";
        case DUVC_LOGITECH_PROP_RIGHT_SOUND: return "RightSound";
        case DUVC_LOGITECH_PROP_FACE_TRACKING: return "FaceTracking";
        case DUVC_LOGITECH_PROP_LED_INDICATOR: return "LEDIndicator";
        case DUVC_LOGITECH_PROP_PROCESSOR_USAGE: return "ProcessorUsage";
        case DUVC_LOGITECH_PROP_RAW_DATA_BITS: return "RawDataBits";
        case DUVC_LOGITECH_PROP_FOCUS_ASSIST: return "FocusAssist";
        case DUVC_LOGITECH_PROP_VIDEO_STANDARD: return "VideoStandard";
        case DUVC_LOGITECH_PROP_DIGITAL_ZOOM_ROI: return "DigitalZoomROI";
        case DUVC_LOGITECH_PROP_TILT_PAN: return "TiltPan";
        default: return "Unknown";
    }
}

/* ========================================================================
 * Value Validation and Utility Functions
 * ======================================================================== */

int duvc_is_value_valid(const duvc_prop_range_t* range, int32_t value) {
    if (!range) return 0;
    
    return (value >= range->min && 
            value <= range->max && 
            ((value - range->min) % range->step == 0)) ? 1 : 0;
}

int32_t duvc_clamp_value(const duvc_prop_range_t* range, int32_t value) {
    if (!range) return value;
    
    if (value <= range->min) return range->min;
    if (value >= range->max) return range->max;
    
    // Round to nearest step
    int32_t steps = (value - range->min + range->step / 2) / range->step;
    return range->min + steps * range->step;
}

duvc_result_t duvc_get_next_valid_value(const duvc_prop_range_t* range,
                                        int32_t current_value,
                                        int increment,
                                        int32_t* next_value) {
    if (!range || !next_value) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    int32_t step_direction = increment ? range->step : -range->step;
    int32_t candidate = current_value + step_direction;
    
    if (candidate < range->min || candidate > range->max) {
        return DUVC_ERROR_INVALID_VALUE;
    }
    
    *next_value = candidate;
    return DUVC_SUCCESS;
}

/* ========================================================================
 * Capability and Device Information
 * ======================================================================== */

duvc_result_t duvc_get_device_capabilities(const duvc_device_t* device,
                                           char* buffer,
                                           size_t buffer_size,
                                           size_t* required_size) {
    if (!device || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        // Create a JSON-like string with device capabilities
        // This is a simplified implementation
        std::ostringstream capabilities;
        capabilities << "{";
        capabilities << "\"camera_properties\":[";
        
        // Add camera properties (simplified)
        const char* cam_props[] = {"Pan", "Tilt", "Zoom", "Exposure", "Focus", "Brightness", "Contrast"};
        for (size_t i = 0; i < sizeof(cam_props)/sizeof(cam_props[0]); ++i) {
            if (i > 0) capabilities << ",";
            capabilities << "\"" << cam_props[i] << "\"";
        }
        
        capabilities << "],";
        capabilities << "\"video_properties\":[";
        
        // Add video properties (simplified)
        const char* vid_props[] = {"Brightness", "Contrast", "Hue", "Saturation", "Gamma"};
        for (size_t i = 0; i < sizeof(vid_props)/sizeof(vid_props[0]); ++i) {
            if (i > 0) capabilities << ",";
            capabilities << "\"" << vid_props[i] << "\"";
        }
        
        capabilities << "]";
        capabilities << "}";
        
        std::string cap_string = capabilities.str();
        return copy_string_to_buffer(cap_string, buffer, buffer_size, required_size);
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to get device capabilities: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_is_camera_property_supported(const duvc_device_t* device,
                                                duvc_cam_prop_t prop,
                                                int* supported) {
    if (!device || !supported || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Use cached connection to test property support
        duvc::DeviceConnection* conn = duvc::get_cached_connection(*cpp_device);
        if (!conn) {
            *supported = 0;
            return DUVC_SUCCESS;
        }
        
        // Try to get the property range as a test for support
        duvc::PropRange range;
        *supported = conn->get_range(convert_cam_prop(prop), range) ? 1 : 0;
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to check camera property support: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_is_video_property_supported(const duvc_device_t* device,
                                               duvc_vid_prop_t prop,
                                               int* supported) {
    if (!device || !supported || !g_initialized.load()) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        const duvc::Device* cpp_device = reinterpret_cast<const duvc::Device*>(device);
        
        // Use cached connection to test property support
        duvc::DeviceConnection* conn = duvc::get_cached_connection(*cpp_device);
        if (!conn) {
            *supported = 0;
            return DUVC_SUCCESS;
        }
        
        // Try to get the property range as a test for support
        duvc::PropRange range;
        *supported = conn->get_range(convert_vid_prop(prop), range) ? 1 : 0;
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        g_last_error_details = std::string("Failed to check video property support: ") + e.what();
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

} // extern "C"
