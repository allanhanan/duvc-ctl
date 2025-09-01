#pragma once

/**
 * @file error_decoder.h
 * @brief HRESULT decoder and diagnostics utilities
 */

#include <string>

#ifdef _WIN32
#include <windows.h>
#endif

namespace duvc {

/**
 * @brief Decode system error code to human-readable string
 * @param error_code System error code
 * @return Human-readable error description
 */
std::string decode_system_error(unsigned long error_code);

#ifdef _WIN32
/**
 * @brief Decode HRESULT to human-readable string
 * @param hr HRESULT value
 * @return Human-readable error description
 */
std::string decode_hresult(HRESULT hr);

/**
 * @brief Get detailed HRESULT information
 * @param hr HRESULT value
 * @return Detailed error information including facility and code
 */
std::string get_hresult_details(HRESULT hr);

/**
 * @brief Check if HRESULT indicates a device-related error
 * @param hr HRESULT value
 * @return true if device-related error
 */
bool is_device_error(HRESULT hr);

/**
 * @brief Check if HRESULT indicates permission/access error
 * @param hr HRESULT value
 * @return true if permission error
 */
bool is_permission_error(HRESULT hr);
#endif

/**
 * @brief Get diagnostic information for troubleshooting
 * @return Diagnostic information string
 */
std::string get_diagnostic_info();

} // namespace duvc
