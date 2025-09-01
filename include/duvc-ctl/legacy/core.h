#pragma once

/**
 * @file legacy/core.h  
 * @brief Legacy compatibility header - will be deprecated in v2.0
 * 
 * This header provides backward compatibility with the original API.
 * New code should use #include <duvc-ctl/duvc.hpp> instead.
 */

#include <duvc-ctl/duvc.hpp>

// Re-export everything in global duvc namespace for compatibility
// This maintains exact same API as before
