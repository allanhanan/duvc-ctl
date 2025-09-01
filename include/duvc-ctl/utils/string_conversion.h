#pragma once

/**
 * @file string_conversion.h
 * @brief String conversion utilities for enums and types
 */

#include <duvc-ctl/core/types.h>

namespace duvc {

/**
 * @brief Convert camera property enum to string
 * @param prop Camera property to convert
 * @return Property name as C string
 */
const char* to_string(CamProp prop);

/**
 * @brief Convert video property enum to string
 * @param prop Video property to convert
 * @return Property name as C string
 */
const char* to_string(VidProp prop);

/**
 * @brief Convert camera mode enum to string
 * @param mode Camera mode to convert
 * @return Mode name as C string ("AUTO" or "MANUAL")
 */
const char* to_string(CamMode mode);

/**
 * @brief Convert camera property enum to wide string
 * @param prop Camera property to convert
 * @return Property name as wide C string
 */
const wchar_t* to_wstring(CamProp prop);

/**
 * @brief Convert video property enum to wide string
 * @param prop Video property to convert
 * @return Property name as wide C string
 */
const wchar_t* to_wstring(VidProp prop);

/**
 * @brief Convert camera mode enum to wide string
 * @param mode Camera mode to convert
 * @return Mode name as wide C string (L"AUTO" or L"MANUAL")
 */
const wchar_t* to_wstring(CamMode mode);

} // namespace duvc
