/**
 * @file ks_properties.cpp
 * @brief IKsPropertySet implementation for vendor properties
 */

#ifdef _WIN32

#include <duvc-ctl/platform/windows/ks_properties.h>
#include <duvc-ctl/detail/com_helpers.h>
#include <duvc-ctl/utils/error_decoder.h>
#include <duvc-ctl/core/device.h>
#include <dshow.h>
#include <ks.h>
#include <ksproxy.h>

namespace duvc {

using namespace detail;

// Forward declaration from device module
extern com_ptr<IBaseFilter> open_device_filter(const Device& dev);

KsPropertySet::KsPropertySet(const Device& device) {
    try {
        auto filter = open_device_filter(device);
        if (filter) {
            // Try to get IKsPropertySet interface
            IKsPropertySet* props = nullptr;
            HRESULT hr = filter->QueryInterface(IID_IKsPropertySet, 
                                               reinterpret_cast<void**>(&props));
            if (SUCCEEDED(hr) && props) {
                property_set_ = com_ptr<IKsPropertySet>(props);
            }
        }
    } catch (...) {
        // Constructor should not throw
        property_set_.reset();
    }
}

KsPropertySet::~KsPropertySet() = default;

KsPropertySet::KsPropertySet(KsPropertySet&&) noexcept = default;
KsPropertySet& KsPropertySet::operator=(KsPropertySet&&) noexcept = default;

bool KsPropertySet::is_valid() const {
    return static_cast<bool>(property_set_);
}

Result<uint32_t> KsPropertySet::query_support(const GUID& property_set, uint32_t property_id) {
    if (!is_valid()) {
        return Err<uint32_t>(ErrorCode::SystemError, "Property set interface not available");
    }
    
    ULONG type_support = 0;
    HRESULT hr = property_set_->QuerySupported(property_set, property_id, &type_support);
    
    if (FAILED(hr)) {
        return Err<uint32_t>(ErrorCode::PropertyNotSupported, 
                            "Property not supported: " + decode_hresult(hr));
    }
    
    return Ok(static_cast<uint32_t>(type_support));
}

Result<std::vector<uint8_t>> KsPropertySet::get_property(const GUID& property_set, uint32_t property_id) {
    if (!is_valid()) {
        return Err<std::vector<uint8_t>>(ErrorCode::SystemError, 
                                        "Property set interface not available");
    }
    
    // First, get the required buffer size
    ULONG bytes_returned = 0;
    HRESULT hr = property_set_->Get(property_set, property_id, nullptr, 0,
                                   nullptr, 0, &bytes_returned);
    
    if (FAILED(hr) || bytes_returned == 0) {
        return Err<std::vector<uint8_t>>(ErrorCode::PropertyNotSupported,
                                        "Failed to get property size: " + decode_hresult(hr));
    }
    
    // Allocate buffer and get the actual data
    std::vector<uint8_t> data(bytes_returned);
    hr = property_set_->Get(property_set, property_id, nullptr, 0,
                           data.data(), bytes_returned, &bytes_returned);
    
    if (FAILED(hr)) {
        return Err<std::vector<uint8_t>>(ErrorCode::SystemError,
                                        "Failed to get property data: " + decode_hresult(hr));
    }
    
    // Resize to actual returned size
    data.resize(bytes_returned);
    return Ok(std::move(data));
}

Result<void> KsPropertySet::set_property(const GUID& property_set, uint32_t property_id,
                                        const std::vector<uint8_t>& data) {
    if (!is_valid()) {
        return Err<void>(ErrorCode::SystemError, "Property set interface not available");
    }
    
    HRESULT hr = property_set_->Set(property_set, property_id, nullptr, 0,
                                   const_cast<uint8_t*>(data.data()), 
                                   static_cast<ULONG>(data.size()));
    
    if (FAILED(hr)) {
        return Err<void>(ErrorCode::SystemError, "Failed to set property: " + decode_hresult(hr));
    }
    
    return Ok();
}

template<typename T>
Result<T> KsPropertySet::get_property_typed(const GUID& property_set, uint32_t property_id) {
    auto result = get_property(property_set, property_id);
    if (!result.is_ok()) {
        return Err<T>(result.error());
    }
    
    const auto& data = result.value();
    if (data.size() != sizeof(T)) {
        return Err<T>(ErrorCode::InvalidValue, 
                     "Property data size mismatch: expected " + std::to_string(sizeof(T)) +
                     " bytes, got " + std::to_string(data.size()));
    }
    
    T value;
    std::memcpy(&value, data.data(), sizeof(T));
    return Ok(value);
}

template<typename T>
Result<void> KsPropertySet::set_property_typed(const GUID& property_set, uint32_t property_id, 
                                              const T& value) {
    std::vector<uint8_t> data(sizeof(T));
    std::memcpy(data.data(), &value, sizeof(T));
    return set_property(property_set, property_id, data);
}

// Explicit template instantiations for common types
template Result<uint32_t> KsPropertySet::get_property_typed<uint32_t>(const GUID&, uint32_t);
template Result<int32_t> KsPropertySet::get_property_typed<int32_t>(const GUID&, uint32_t);
template Result<bool> KsPropertySet::get_property_typed<bool>(const GUID&, uint32_t);

template Result<void> KsPropertySet::set_property_typed<uint32_t>(const GUID&, uint32_t, const uint32_t&);
template Result<void> KsPropertySet::set_property_typed<int32_t>(const GUID&, uint32_t, const int32_t&);
template Result<void> KsPropertySet::set_property_typed<bool>(const GUID&, uint32_t, const bool&);

} // namespace duvc

#endif // _WIN32
