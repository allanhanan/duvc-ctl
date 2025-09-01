#pragma once

/**
 * @file ks_properties.h
 * @brief IKsPropertySet wrapper for vendor properties
 */

#ifdef _WIN32

#include <duvc-ctl/core/types.h>
#include <duvc-ctl/core/result.h>
#include <duvc-ctl/detail/com_helpers.h>
#include <windows.h>
#include <vector>

struct IKsPropertySet;

namespace duvc {

/**
 * @brief RAII wrapper for IKsPropertySet interface
 */
class KsPropertySet {
public:
    /**
     * @brief Create KsPropertySet from device
     * @param device Device to get property set from
     */
    explicit KsPropertySet(const Device& device);
    
    /// Destructor
    ~KsPropertySet();
    
    // Non-copyable but movable
    KsPropertySet(const KsPropertySet&) = delete;
    KsPropertySet& operator=(const KsPropertySet&) = delete;
    KsPropertySet(KsPropertySet&&) noexcept;
    KsPropertySet& operator=(KsPropertySet&&) noexcept;
    
    /**
     * @brief Check if property set is valid
     * @return true if property set can be used
     */
    bool is_valid() const;
    
    /**
     * @brief Query property support
     * @param property_set Property set GUID
     * @param property_id Property ID
     * @return Result containing support flags or error
     */
    Result<uint32_t> query_support(const GUID& property_set, uint32_t property_id);
    
    /**
     * @brief Get property data
     * @param property_set Property set GUID
     * @param property_id Property ID
     * @return Result containing property data or error
     */
    Result<std::vector<uint8_t>> get_property(const GUID& property_set, uint32_t property_id);
    
    /**
     * @brief Set property data
     * @param property_set Property set GUID
     * @param property_id Property ID
     * @param data Property data to set
     * @return Result indicating success or error
     */
    Result<void> set_property(const GUID& property_set, uint32_t property_id, 
                             const std::vector<uint8_t>& data);
    
    /**
     * @brief Get typed property value
     * @tparam T Property value type
     * @param property_set Property set GUID
     * @param property_id Property ID
     * @return Result containing typed value or error
     */
    template<typename T>
    Result<T> get_property_typed(const GUID& property_set, uint32_t property_id);
    
    /**
     * @brief Set typed property value
     * @tparam T Property value type
     * @param property_set Property set GUID
     * @param property_id Property ID
     * @param value Property value to set
     * @return Result indicating success or error
     */
    template<typename T>
    Result<void> set_property_typed(const GUID& property_set, uint32_t property_id, const T& value);
    
private:
    detail::com_ptr<IKsPropertySet> property_set_;
};

} // namespace duvc

#endif // _WIN32
