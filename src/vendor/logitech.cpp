/**
 * @file logitech.cpp
 * @brief Logitech-specific property implementations
 */

#ifdef _WIN32

#include <duvc-ctl/vendor/logitech.h>
#include <duvc-ctl/platform/windows/ks_properties.h>
#include <duvc-ctl/utils/logging.h>

#include <ks.h>
#include <ksproxy.h>

// IF ks.h not available, define manually:
#ifndef KSPROPERTY_SUPPORT_GET
#define KSPROPERTY_SUPPORT_GET 1
#define KSPROPERTY_SUPPORT_SET 2
#endif

namespace duvc::logitech {

Result<std::vector<uint8_t>> get_logitech_property(const Device& device, LogitechProperty prop) {
    try {
        KsPropertySet prop_set(device);
        if (!prop_set.is_valid()) {
            return Err<std::vector<uint8_t>>(ErrorCode::PropertyNotSupported, "Device does not support vendor properties");
        }
        
        return prop_set.get_property(LOGITECH_PROPERTY_SET, static_cast<uint32_t>(prop));
        
    } catch (const std::exception& e) {
        DUVC_LOG_ERROR("Exception getting Logitech property: " + std::string(e.what()));
        return Err<std::vector<uint8_t>>(ErrorCode::SystemError, e.what());
    }
}

Result<void> set_logitech_property(const Device& device, LogitechProperty prop, 
                                  const std::vector<uint8_t>& data) {
    try {
        KsPropertySet prop_set(device);
        if (!prop_set.is_valid()) {
            return Err<void>(ErrorCode::PropertyNotSupported, "Device does not support vendor properties");
        }
        
        return prop_set.set_property(LOGITECH_PROPERTY_SET, static_cast<uint32_t>(prop), data);
        
    } catch (const std::exception& e) {
        DUVC_LOG_ERROR("Exception setting Logitech property: " + std::string(e.what()));
        return Err<void>(ErrorCode::SystemError, e.what());
    }
}

Result<bool> supports_logitech_properties(const Device& device) {
    try {
        KsPropertySet prop_set(device);
        if (!prop_set.is_valid()) {
            return Ok(false);
        }
        
        // Try to query support for a basic property
        auto result = prop_set.query_support(LOGITECH_PROPERTY_SET, 
                                           static_cast<uint32_t>(LogitechProperty::RightLight));
        
        if (result.is_ok()) {
            uint32_t support_flags = result.value();
            return Ok((support_flags & (KSPROPERTY_SUPPORT_GET | KSPROPERTY_SUPPORT_SET)) != 0);
        }
        
        return Ok(false);
        
    } catch (const std::exception& e) {
        DUVC_LOG_DEBUG("Exception checking Logitech support: " + std::string(e.what()));
        return Ok(false); // Assume not supported on error
    }
}

template<typename T>
Result<T> get_logitech_property_typed(const Device& device, LogitechProperty prop) {
    auto data_result = get_logitech_property(device, prop);
    if (!data_result.is_ok()) {
        return Err<T>(data_result.error());
    }
    
    const auto& data = data_result.value();
    if (data.size() != sizeof(T)) {
        return Err<T>(ErrorCode::InvalidValue, 
                     "Property data size mismatch for Logitech property");
    }
    
    T value;
    std::memcpy(&value, data.data(), sizeof(T));
    return Ok(value);
}

template<typename T>
Result<void> set_logitech_property_typed(const Device& device, LogitechProperty prop, 
                                        const T& value) {
    std::vector<uint8_t> data(sizeof(T));
    std::memcpy(data.data(), &value, sizeof(T));
    return set_logitech_property(device, prop, data);
}

// Explicit template instantiations for common types
template Result<uint32_t> get_logitech_property_typed<uint32_t>(const Device&, LogitechProperty);
template Result<int32_t> get_logitech_property_typed<int32_t>(const Device&, LogitechProperty);
template Result<bool> get_logitech_property_typed<bool>(const Device&, LogitechProperty);

template Result<void> set_logitech_property_typed<uint32_t>(const Device&, LogitechProperty, const uint32_t&);
template Result<void> set_logitech_property_typed<int32_t>(const Device&, LogitechProperty, const int32_t&);
template Result<void> set_logitech_property_typed<bool>(const Device&, LogitechProperty, const bool&);

} // namespace duvc::logitech

#endif // _WIN32
