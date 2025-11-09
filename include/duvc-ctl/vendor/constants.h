#pragma once

/**
 * @file constants.h
 * @brief Vendor-specific property constants and definitions
 *
 * Provides generic vendor property access for Windows UVC devices via
 * DirectShow. Allows reading/writing vendor-specific extension units using
 * GUID-identified property sets.
 */

#ifdef _WIN32

#include <duvc-ctl/core/types.h>
#include <vector>
#include <windows.h>

namespace duvc {

/**
 * @brief Vendor-specific property data container
 *
 * Encapsulates a vendor extension unit property identified by a GUID property
 * set and numeric property ID. The data payload is opaque and vendor-defined.
 */
struct VendorProperty {
  GUID property_set; ///< Property set GUID (vendor-specific extension unit)
  ULONG property_id; ///< Property ID within set (vendor-defined numeric
                     ///< identifier)
  std::vector<uint8_t>
      data; ///< Property data payload (opaque vendor-defined binary data)

  /// Default constructor
  VendorProperty() = default;

  /**
   * @brief Construct vendor property with initial values
   * @param set Property set GUID identifying the extension unit
   * @param id Property ID within the extension unit
   * @param payload Initial data buffer (empty by default)
   */
  VendorProperty(const GUID &set, ULONG id,
                 const std::vector<uint8_t> &payload = {})
      : property_set(set), property_id(id), data(payload) {}
};

/**
 * @brief Get vendor-specific property data from device
 * @param dev Target device to query
 * @param property_set Property set GUID identifying the extension unit
 * @param property_id Property ID within the extension unit
 * @param[out] data Output buffer to receive property data
 * @return true if property was read successfully, false on error
 */
bool get_vendor_property(const Device &dev, const GUID &property_set,
                         ULONG property_id, std::vector<uint8_t> &data);

/**
 * @brief Set vendor-specific property data on device
 * @param dev Target device to modify
 * @param property_set Property set GUID identifying the extension unit
 * @param property_id Property ID within the extension unit
 * @param data Property data to write (vendor-specific binary format)
 * @return true if property was written successfully, false on error
 */
bool set_vendor_property(const Device &dev, const GUID &property_set,
                         ULONG property_id, const std::vector<uint8_t> &data);

/**
 * @brief Query whether device supports a vendor-specific property
 * @param dev Target device to check
 * @param property_set Property set GUID to query
 * @param property_id Property ID within set to query
 * @return true if property is supported for get/set operations, false otherwise
 */
bool query_vendor_property_support(const Device &dev, const GUID &property_set,
                                   ULONG property_id);

} // namespace duvc

#endif // _WIN32
