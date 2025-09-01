/**
 * @file core_legacy.cpp  
 * @brief Bridge from legacy core.h API to new modular implementation
 */

#include <duvc-ctl/legacy/core.h>
#include <duvc-ctl/duvc.hpp>

// This file provides the legacy API by forwarding calls to the new modular implementation.
// All the actual implementation is now in the new modular structure.

// The legacy header just includes the new header, so no implementation is needed here.
// This file exists as a placeholder for any future legacy-specific bridge code.

namespace duvc {

// Legacy API functions are now implemented directly in terms of the new API
// through the legacy header includes. No additional implementation needed.

} // namespace duvc
