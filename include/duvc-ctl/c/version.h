#pragma once
#include <cstdint>

/**
 * @file version.h
 * @brief ABI versioning and build information for duvc-ctl C API
 */

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Major version number
 * 
 * Incremented for breaking ABI changes. Applications compiled against
 * a different major version are not guaranteed to be compatible.
 */
#define DUVC_ABI_VERSION_MAJOR 2

/**
 * @brief Minor version number
 * 
 * Incremented for new features that maintain backward compatibility.
 * Applications compiled against older minor versions should work.
 */
#define DUVC_ABI_VERSION_MINOR 0

/**
 * @brief Patch version number
 * 
 * Incremented for bug fixes and internal improvements that maintain
 * full ABI compatibility.
 */
#define DUVC_ABI_VERSION_PATCH 0

/**
 * @brief Combined version number as integer
 * 
 * Format: (major << 16) | (minor << 8) | patch
 * Useful for numeric version comparisons.
 */
#define DUVC_ABI_VERSION ((DUVC_ABI_VERSION_MAJOR << 16) | \
                          (DUVC_ABI_VERSION_MINOR << 8) | \
                          DUVC_ABI_VERSION_PATCH)

/**
 * @brief Version string in semantic versioning format
 */
#define DUVC_ABI_VERSION_STRING "2.0.0"

/**
 * @brief Get runtime library version
 * 
 * @return Combined version number as returned by DUVC_ABI_VERSION macro
 */
uint32_t duvc_get_version(void);

/**
 * @brief Get runtime library version string
 * 
 * @return Null-terminated version string (e.g., "2.0.0")
 * @note Returned string is statically allocated and should not be freed
 */
const char* duvc_get_version_string(void);

/**
 * @brief Check ABI compatibility
 * 
 * Verifies that the runtime library is compatible with the version
 * this application was compiled against.
 * 
 * @param compiled_version Version the application was compiled with (use DUVC_ABI_VERSION)
 * @return 1 if compatible, 0 if incompatible
 */
int duvc_check_abi_compatibility(uint32_t compiled_version);

#ifdef __cplusplus
}
#endif
