/**
 * @file error_handling.cpp
 * @brief C ABI error handling and diagnostics implementation
 * 
 * This file implements comprehensive error handling for the C ABI, including
 * error code conversion, detailed error information management, and diagnostic
 * utilities for troubleshooting camera control issues.
 */

#include "duvc-ctl/c/api.h"

// Include all necessary C++ headers for error handling
#include "duvc-ctl/core/result.h"
#include "duvc-ctl/utils/error_decoder.h"
#include "duvc-ctl/utils/logging.h"

#ifdef _WIN32
#include <windows.h>
#include <comdef.h>
#include <psapi.h>
#endif

#include <string>
#include <sstream>
#include <mutex>
#include <unordered_map>
#include <atomic>
#include <cstring>
#include <iomanip>
#include <thread>

namespace {
    /** @brief Thread-local error details storage - matches api.cpp */
    thread_local std::string g_last_error_details; 
    
    
    /** @brief Global error statistics tracking */
    std::mutex g_error_stats_mutex;
    std::unordered_map<duvc_result_t, size_t> g_error_counts;
    std::atomic<size_t> g_total_operations{0};
    std::atomic<size_t> g_total_errors{0};
    
    /** @brief Error context information */
    struct ErrorContext {
        std::string operation;
        std::string device_info;
        std::chrono::steady_clock::time_point timestamp;
        std::thread::id thread_id;
    };
    
    thread_local ErrorContext g_last_error_context;
    
    /**
     * @brief Update error statistics (thread-safe)
     */
    void update_error_stats(duvc_result_t result) {
        g_total_operations.fetch_add(1);
        
        if (result != DUVC_SUCCESS) {
            g_total_errors.fetch_add(1);
            
            std::lock_guard<std::mutex> lock(g_error_stats_mutex);
            g_error_counts[result]++;
        }
    }
    
    /**
     * @brief Set error context for detailed reporting
     */
    void set_error_context(const char* operation, const char* device_info = nullptr) {
        g_last_error_context.operation = operation ? operation : "Unknown";
        g_last_error_context.device_info = device_info ? device_info : "";
        g_last_error_context.timestamp = std::chrono::steady_clock::now();
        g_last_error_context.thread_id = std::this_thread::get_id();
    }
}

extern "C" {


/* ========================================================================
 * Error Classification
 * ======================================================================== */


int duvc_is_temporary_error(duvc_result_t result) {
    // These errors might be resolved by retrying
    switch (result) {
        case DUVC_ERROR_DEVICE_BUSY:
        case DUVC_ERROR_TIMEOUT:
        case DUVC_ERROR_CONNECTION_FAILED:
            return 1;
        default:
            return 0;
    }
}

int duvc_is_user_error(duvc_result_t result) {
    // These errors are likely caused by incorrect usage
    switch (result) {
        case DUVC_ERROR_INVALID_ARGUMENT:
        case DUVC_ERROR_INVALID_VALUE:
        case DUVC_ERROR_BUFFER_TOO_SMALL:
            return 1;
        default:
            return 0;
    }
}

/* ========================================================================
 * Error Context Management
 * ======================================================================== */


duvc_result_t duvc_set_error_context(const char* operation, const char* device_info) {
    if (!operation) {
        return DUVC_ERROR_INVALID_ARGUMENT;
    }
    
    try {
        set_error_context(operation, device_info);
        return DUVC_SUCCESS;
    } catch (const std::exception&) {
        return DUVC_ERROR_SYSTEM_ERROR;
    }
}

duvc_result_t duvc_get_error_statistics(char* buffer, size_t buffer_size, size_t* required_size) {
    try {
        std::ostringstream stats;
        
        stats << "Error Statistics:\n";
        stats << "================\n";
        
        size_t total_ops = g_total_operations.load();
        size_t total_errs = g_total_errors.load();
        
        stats << "Total Operations: " << total_ops << "\n";
        stats << "Total Errors: " << total_errs << "\n";
        
        if (total_ops > 0) {
            double success_rate = (double)(total_ops - total_errs) / total_ops * 100.0;
            double error_rate = (double)total_errs / total_ops * 100.0;
            
            stats << "Success Rate: " << std::fixed << std::setprecision(2) << success_rate << "%\n";
            stats << "Error Rate: " << std::fixed << std::setprecision(2) << error_rate << "%\n";
        }
        
        // Detailed error breakdown
        {
            std::lock_guard<std::mutex> lock(g_error_stats_mutex);
            if (!g_error_counts.empty()) {
                stats << "\nDetailed Error Breakdown:\n";
                stats << "========================\n";
                
                for (const auto& pair : g_error_counts) {
                    double percentage = total_errs > 0 ? (double)pair.second / total_errs * 100.0 : 0.0;
                    stats << duvc_error_code_to_string(pair.first) 
                          << ": " << pair.second 
                          << " (" << std::fixed << std::setprecision(1) << percentage << "%)\n";
                }
            }
        }
        
        std::string stats_str = stats.str();
        
        // Handle buffer size requirements
        size_t needed = stats_str.length() + 1;
        if (required_size) *required_size = needed;
        
        if (!buffer || buffer_size < needed) {
            return DUVC_ERROR_BUFFER_TOO_SMALL;
        }
        
        std::memcpy(buffer, stats_str.c_str(), needed);
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        std::string fallback = std::string("Failed to get error statistics: ") + e.what();
        size_t needed = fallback.length() + 1;
        
        if (required_size) *required_size = needed;
        
        if (buffer && buffer_size >= needed) {
            std::memcpy(buffer, fallback.c_str(), needed);
        }
        
        return buffer && buffer_size >= needed ? DUVC_SUCCESS : DUVC_ERROR_BUFFER_TOO_SMALL;
    }
}

void duvc_reset_error_statistics(void) {
    g_total_operations.store(0);
    g_total_errors.store(0);
    
    std::lock_guard<std::mutex> lock(g_error_stats_mutex);
    g_error_counts.clear();
}

/* ========================================================================
 * Advanced Error Handling Utilities
 * ======================================================================== */

duvc_result_t duvc_suggest_error_resolution(duvc_result_t error_code, 
                                           char* buffer, 
                                           size_t buffer_size, 
                                           size_t* required_size) {
    try {
        std::ostringstream suggestions;
        
        suggestions << "Resolution suggestions for: " << duvc_error_code_to_string(error_code) << "\n\n";
        
        switch (error_code) {
            case DUVC_ERROR_DEVICE_NOT_FOUND:
                suggestions << "1. Check that the camera is physically connected\n";
                suggestions << "2. Verify the camera appears in Device Manager\n";
                suggestions << "3. Try reconnecting the USB cable\n";
                suggestions << "4. Restart the camera or computer\n";
                suggestions << "5. Check if device drivers are properly installed\n";
                break;
                
            case DUVC_ERROR_DEVICE_BUSY:
                suggestions << "1. Close other applications using the camera\n";
                suggestions << "2. Check for background processes using the camera\n";
                suggestions << "3. Wait a moment and try again\n";
                suggestions << "4. Restart applications that might be holding the device\n";
                break;
                
            case DUVC_ERROR_PERMISSION_DENIED:
                suggestions << "1. Run the application as Administrator (Windows)\n";
                suggestions << "2. Check camera privacy settings\n";
                suggestions << "3. Verify antivirus isn't blocking camera access\n";
                suggestions << "4. Check Windows Camera privacy settings\n";
                break;
                
            case DUVC_ERROR_PROPERTY_NOT_SUPPORTED:
                suggestions << "1. Check device capabilities before setting properties\n";
                suggestions << "2. Verify the property is supported by your camera model\n";
                suggestions << "3. Try alternative properties with similar functionality\n";
                break;
                
            case DUVC_ERROR_INVALID_VALUE:
                suggestions << "1. Check the valid range for this property\n";
                suggestions << "2. Use duvc_get_*_property_range() to get valid ranges\n";
                suggestions << "3. Ensure values are within min/max bounds\n";
                suggestions << "4. Check step size alignment\n";
                break;
                
            case DUVC_ERROR_CONNECTION_FAILED:
                suggestions << "1. Check USB connection and cable quality\n";
                suggestions << "2. Try a different USB port\n";
                suggestions << "3. Update camera drivers\n";
                suggestions << "4. Check for USB power management issues\n";
                break;
                
            case DUVC_ERROR_SYSTEM_ERROR:
                suggestions << "1. Check system logs for detailed error information\n";
                suggestions << "2. Verify DirectShow components are properly installed\n";
                suggestions << "3. Try reinstalling camera drivers\n";
                suggestions << "4. Check for Windows updates\n";
                break;
                
            default:
                suggestions << "1. Check the detailed error information\n";
                suggestions << "2. Consult the documentation for this error code\n";
                suggestions << "3. Enable debug logging for more information\n";
                suggestions << "4. Contact support with diagnostic information\n";
                break;
        }
        
        suggestions << "\nGeneral troubleshooting:\n";
        suggestions << "- Enable debug logging: duvc_set_log_level(DUVC_LOG_DEBUG)\n";
        suggestions << "- Get diagnostic info: duvc_get_diagnostic_info()\n";
        suggestions << "- Check error statistics: duvc_get_error_statistics()\n";
        
        std::string suggestions_str = suggestions.str();
        
        // Handle buffer size requirements
        size_t needed = suggestions_str.length() + 1;
        if (required_size) *required_size = needed;
        
        if (!buffer || buffer_size < needed) {
            return DUVC_ERROR_BUFFER_TOO_SMALL;
        }
        
        std::memcpy(buffer, suggestions_str.c_str(), needed);
        return DUVC_SUCCESS;
        
    } catch (const std::exception& e) {
        std::string fallback = std::string("Failed to get error suggestions: ") + e.what();
        size_t needed = fallback.length() + 1;
        
        if (required_size) *required_size = needed;
        
        if (buffer && buffer_size >= needed) {
            std::memcpy(buffer, fallback.c_str(), needed);
        }
        
        return buffer && buffer_size >= needed ? DUVC_SUCCESS : DUVC_ERROR_BUFFER_TOO_SMALL;
    }
}

int duvc_should_retry_operation(duvc_result_t error_code) {
    // Determine if an operation should be retried based on the error
    switch (error_code) {
        case DUVC_ERROR_DEVICE_BUSY:
        case DUVC_ERROR_TIMEOUT:
            return 1;  // Likely temporary, worth retrying
            
        case DUVC_ERROR_CONNECTION_FAILED:
            return 1;  // Might be transient connection issue
            
        case DUVC_ERROR_DEVICE_NOT_FOUND:
        case DUVC_ERROR_PERMISSION_DENIED:
        case DUVC_ERROR_INVALID_ARGUMENT:
        case DUVC_ERROR_INVALID_VALUE:
        case DUVC_ERROR_PROPERTY_NOT_SUPPORTED:
        case DUVC_ERROR_NOT_IMPLEMENTED:
            return 0;  // Unlikely to succeed on retry
            
        default:
            return 0;  // Conservative approach
    }
}

} // extern "C"
