#pragma once

/**
 * @file duvc.hpp
 * @brief Main umbrella header for duvc-ctl library
 * 
 * This header provides everything users need for the duvc-ctl library.
 * Include this single header to access all functionality.
 * 
 * @example Basic usage:
 * ```
 * #include <duvc-ctl/duvc.hpp>
 * 
 * int main() {
 *     auto devices = duvc::list_devices();
 *     if (!devices.empty()) {
 *         auto camera = duvc::open_camera(0);
 *         if (camera) {
 *             auto result = camera.value().get(duvc::VidProp::Brightness);
 *             // ...
 *         }
 *     }
 * }
 * ```
 */

// Core functionality
#include <duvc-ctl/core/types.h>
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/core/camera.h>
#include <duvc-ctl/core/result.h>
#include <duvc-ctl/core/capability.h>
#include <duvc-ctl/core/operations.h>

// Utility functions
#include <duvc-ctl/utils/string_conversion.h>
#include <duvc-ctl/utils/logging.h>
#include <duvc-ctl/utils/error_decoder.h>

// Platform interface (advanced users)
#include <duvc-ctl/platform/interface.h>

// Vendor extensions
#include <duvc-ctl/vendor/constants.h>
#ifdef _WIN32
#include <duvc-ctl/vendor/logitech.h>
#endif

/**
 * @namespace duvc
 * @brief Main namespace for duvc-ctl library
 * 
 * All duvc-ctl functionality is contained within this namespace.
 * The library provides camera control functionality across different platforms,
 * with primary support for Windows DirectShow devices.
 */

/**
 * @defgroup core Core Functionality
 * @brief Core camera control functionality
 * 
 * This group contains the main API for device enumeration, camera control,
 * and property management.
 */

/**
 * @defgroup utils Utilities
 * @brief Utility functions and helpers
 * 
 * This group contains logging, error handling, and string conversion utilities.
 */

/**
 * @defgroup platform Platform Support
 * @brief Platform-specific functionality
 * 
 * This group contains platform abstraction layers and platform-specific
 * implementations.
 */

/**
 * @defgroup vendor Vendor Extensions
 * @brief Vendor-specific property support
 * 
 * This group contains vendor-specific property definitions and helpers
 * for accessing advanced device features.
 */
