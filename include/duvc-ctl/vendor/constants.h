#pragma once

/**
 * @file constants.h
 * @brief Vendor-specific property constants and definitions
 */

#ifdef _WIN32
#include <windows.h>
#include <vector>
#include <duvc-ctl/core/types.h>

namespace duvc {

/**
 * @brief Vendor-specific property data
 */
struct VendorProperty {
    GUID property_set;          ///< Property set GUID
    ULONG property_id;          ///< Property ID within set
    std::vector<uint8_t> data;  ///< Property data payload
    
    /// Default constructor
    VendorProperty() = default;
    
    /**
     * @brief Construct vendor property
     * @param set Property set GUID
     * @param id Property ID
     * @param payload Initial data
     */
    VendorProperty(const GUID& set, ULONG id, const std::vector<uint8_t>& payload = {})
        : property_set(set), property_id(id), data(payload) {}
};

/**
 * @brief Get vendor-specific property data
 * @param dev Target device
 * @param property_set Property set GUID
 * @param property_id Property ID within set
 * @param data Output data buffer
 * @return true if property was read successfully
 */
bool get_vendor_property(const Device& dev, const GUID& property_set, ULONG property_id,
                        std::vector<uint8_t>& data);

/**
 * @brief Set vendor-specific property data
 * @param dev Target device
 * @param property_set Property set GUID
 * @param property_id Property ID within set
 * @param data Property data to write
 * @return true if property was written successfully
 */
bool set_vendor_property(const Device& dev, const GUID& property_set, ULONG property_id,
                        const std::vector<uint8_t>& data);

/**
 * @brief Query support for vendor-specific property
 * @param dev Target device
 * @param property_set Property set GUID
 * @param property_id Property ID within set
 * @return true if property is supported for get/set operations
 */
bool query_vendor_property_support(const Device& dev, const GUID& property_set, ULONG property_id);

} // namespace duvc

#endif // _WIN32
