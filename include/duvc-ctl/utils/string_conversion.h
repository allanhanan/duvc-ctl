#pragma once

/**
 * @file string_conversion.h
 * @brief String conversion utilities for enums and types
 */

#include <duvc-ctl/core/types.h>
#include <string>

namespace duvc {

/**
 * @brief Convert camera property enum to string
 * @param prop Camera property to convert
 * @return Property name as C string
 */
const char *to_string(CamProp prop);

/**
 * @brief Convert video property enum to string
 * @param prop Video property to convert
 * @return Property name as C string
 */
const char *to_string(VidProp prop);

/**
 * @brief Convert camera mode enum to string
 * @param mode Camera mode to convert
 * @return Mode name as C string ("AUTO" or "MANUAL")
 */
const char *to_string(CamMode mode);

/**
 * @brief Convert camera property enum to wide string
 * @param prop Camera property to convert
 * @return Property name as wide C string
 */
const wchar_t *to_wstring(CamProp prop);

/**
 * @brief Convert video property enum to wide string
 * @param prop Video property to convert
 * @return Property name as wide C string
 */
const wchar_t *to_wstring(VidProp prop);

/**
 * @brief Convert camera mode enum to wide string
 * @param mode Camera mode to convert
 * @return Mode name as wide C string (L"AUTO" or L"MANUAL")
 */
const wchar_t *to_wstring(CamMode mode);

/**
 * @brief Converts a wide string (UTF-16 on Windows) to a UTF-8 string
 * @param wstr Wide string to convert (UTF-16 encoded on Windows)
 * @return UTF-8 encoded string
 */
std::string to_utf8(const std::wstring &wstr);

/**
 * @brief Converts a wide string (UTF-16 on Windows) to a UTF-8 string
 * @param wstr Wide string to convert (UTF-16 encoded on Windows)
 * @return UTF-8 encoded string
 */
std::string to_utf8(const std::wstring &wstr);

/**
 * @brief Converts a UTF-8 string to a wide string (UTF-16 on Windows)
 * @param str UTF-8 encoded string to convert
 * @return Wide string (UTF-16 encoded on Windows)
 */
std::wstring to_wstring(const std::string &str);


} // namespace duvc
