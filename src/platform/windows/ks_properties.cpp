/**
 * @file ks_properties.cpp
 * @brief IKsPropertySet implementation for vendor properties
 */

#ifdef _WIN32

#include <dshow.h>
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/detail/com_helpers.h>
#include <duvc-ctl/platform/windows/ks_properties.h>
#include <duvc-ctl/utils/error_decoder.h>
#include <ks.h>
#include <ksproxy.h>

namespace duvc {
namespace detail {
    // Forward declaration - function is in duvc::detail
    com_ptr<IBaseFilter> open_device_filter(const Device& dev);
}

KsPropertySet::KsPropertySet(const Device &device) : device_(device), mfksproxy_dll_(nullptr) {
    try {
        // VALIDATION 1: Check device validity before any operations
        if (!device.is_valid()) {
            throw std::invalid_argument(
                "Device must be valid and opened before creating KsPropertySet. "
                "Call open_camera(device) first.");
        }

        // VALIDATION 2: Attempt to open device filter with null check
        auto filter = detail::open_device_filter(device_);
        if (!filter) {
            throw std::runtime_error(
                "Failed to obtain device filter. Device may not be properly opened "
                "or may have been disconnected.");
        }

        // Store ONLY the base filter - this keeps the DLL loaded
        basefilter_ = std::move(filter);

        // Explicitly load the DLL and keep the handle to ensure it stays loaded
        mfksproxy_dll_ = LoadLibraryW(L"mfksproxy.dll");
        if (!mfksproxy_dll_) {
            throw std::runtime_error("Failed to load mfksproxy.dll.");
        }

        // VALIDATION 3: Verify property set is available (temporary, not stored)
        detail::com_ptr<IKsPropertySet> temp_props;
        HRESULT hr = basefilter_->QueryInterface(IID_PPV_ARGS(temp_props.put()));
        
        if (FAILED(hr)) {
            basefilter_.reset();  // cleanup on failure
            FreeLibrary(mfksproxy_dll_); // Cleanup DLL if query fails
            throw std::runtime_error(
                "Device does not support KsPropertySet interface. "
                "This device may not expose vendor-specific properties. "
                "HRESULT: " + decode_hresult(hr));
        }
        
        // VALIDATION 4: Verify pointer is non-null (double-check after SUCCEEDED)
        if (!temp_props) {
            basefilter_.reset();
            FreeLibrary(mfksproxy_dll_); // Cleanup DLL if temp_props is null
            throw std::runtime_error(
                "QueryInterface succeeded but returned null pointer. "
                "This indicates a driver or COM issue.");
        }

        // temp_props automatically released here (DLL stays loaded because basefilter_ is held)
        } catch (...) {
          basefilter_.reset();
          if (mfksproxy_dll_) { 
              FreeLibrary(mfksproxy_dll_);
        }
        throw;
    }
}

// Helper to get property set interface on-demand
detail::com_ptr<IKsPropertySet> KsPropertySet::get_property_set() const {
    if (!basefilter_) {
        return {};
    }
    detail::com_ptr<IKsPropertySet> props;
    HRESULT hr = basefilter_->QueryInterface(IID_PPV_ARGS(props.put()));
    if (FAILED(hr)) {
        return {};
    }
    return props;
}

// Destructor that ensures DLL is unloaded safely
KsPropertySet::~KsPropertySet() {
    
    // CRITICAL ORDER: Release COM objects BEFORE unloading DLL
    // COM vtables may point into the DLL
    basefilter_.reset();
    
    if (mfksproxy_dll_ != nullptr) {
        FreeLibrary(mfksproxy_dll_);
        mfksproxy_dll_ = nullptr;  // Defensive: prevent double-free
    }
}   

KsPropertySet::KsPropertySet(KsPropertySet &&other) noexcept 
    : device_(std::move(other.device_)),
      basefilter_(std::move(other.basefilter_)),
      mfksproxy_dll_(other.mfksproxy_dll_) {
    other.mfksproxy_dll_ = nullptr;  // CRITICAL: Prevent double-free
}

KsPropertySet& KsPropertySet::operator=(KsPropertySet &&other) noexcept {
    if (this != &other) {
        // Clean up current resources FIRST
        basefilter_.reset();
        if (mfksproxy_dll_ != nullptr) {
            FreeLibrary(mfksproxy_dll_);
        }
        
        // Transfer ownership from other
        device_ = std::move(other.device_);
        basefilter_ = std::move(other.basefilter_);
        mfksproxy_dll_ = other.mfksproxy_dll_;
        other.mfksproxy_dll_ = nullptr;  // CRITICAL: Prevent double-free
    }
    return *this;
}


bool KsPropertySet::is_valid() const {
    return static_cast<bool>(basefilter_);  // Check basefilter instead
}

Result<uint32_t> KsPropertySet::query_support(const GUID &property_set,
                                              uint32_t property_id) {
    auto props = get_property_set();  // Get temporary
    if (!props) {
        return Err<uint32_t>(ErrorCode::SystemError,
                             "Property set interface not available");
    }

    ULONG type_support = 0;
    HRESULT hr = props->QuerySupported(property_set, property_id, &type_support);
    // props automatically released here (DLL stays loaded because basefilter_ is held)
    
    if (FAILED(hr)) {
        return Err<uint32_t>(ErrorCode::PropertyNotSupported,
                             "Property not supported: " + decode_hresult(hr));
    }

    return Ok(static_cast<uint32_t>(type_support));
}

Result<std::vector<uint8_t>>
KsPropertySet::get_property(const GUID &property_set, uint32_t property_id) {
    auto props = get_property_set();  // Get temporary
    if (!props) {
        return Err<std::vector<uint8_t>>(ErrorCode::SystemError,
                                         "Property set interface not available");
    }

    // First, get the required buffer size
    ULONG bytes_returned = 0;
    HRESULT hr = props->Get(property_set, property_id, nullptr, 0,
                            nullptr, 0, &bytes_returned);
    if (FAILED(hr) || bytes_returned == 0) {
        return Err<std::vector<uint8_t>>(ErrorCode::PropertyNotSupported,
                                         "Failed to get property size: " +
                                             decode_hresult(hr));
    }

    // Allocate buffer and get the actual data
    std::vector<uint8_t> data(bytes_returned);
    hr = props->Get(property_set, property_id, nullptr, 0, data.data(),
                    bytes_returned, &bytes_returned);
    // props automatically released here (DLL stays loaded because basefilter_ is held)
    
    if (FAILED(hr)) {
        return Err<std::vector<uint8_t>>(ErrorCode::SystemError,
                                         "Failed to get property data: " +
                                             decode_hresult(hr));
    }

    // Resize to actual returned size
    data.resize(bytes_returned);
    return Ok(std::move(data));
}

Result<void> KsPropertySet::set_property(const GUID &property_set,
                                         uint32_t property_id,
                                         const std::vector<uint8_t> &data) {
    auto props = get_property_set();  // Get temporary
    if (!props) {
        return Err<void>(ErrorCode::SystemError,
                         "Property set interface not available");
    }

    HRESULT hr = props->Set(property_set, property_id, nullptr, 0,
                            const_cast<uint8_t *>(data.data()),
                            static_cast<ULONG>(data.size()));
    // props automatically released here (DLL stays loaded because basefilter_ is held)
    
    if (FAILED(hr)) {
        return Err<void>(ErrorCode::SystemError,
                         "Failed to set property: " + decode_hresult(hr));
    }

    return Ok();
}

template <typename T>
Result<T> KsPropertySet::get_property_typed(const GUID &property_set,
                                            uint32_t property_id) {
    auto result = get_property(property_set, property_id);
    if (!result.is_ok()) {
        return Err<T>(result.error());
    }

    const auto &data = result.value();
    if (data.size() != sizeof(T)) {
        return Err<T>(ErrorCode::InvalidValue,
                      "Property data size mismatch: expected " +
                          std::to_string(sizeof(T)) + " bytes, got " +
                          std::to_string(data.size()));
    }

    T value;
    std::memcpy(&value, data.data(), sizeof(T));
    return Ok(value);
}

template <typename T>
Result<void> KsPropertySet::set_property_typed(const GUID &property_set,
                                               uint32_t property_id,
                                               const T &value) {
    std::vector<uint8_t> data(sizeof(T));
    std::memcpy(data.data(), &value, sizeof(T));
    return set_property(property_set, property_id, data);
}

// Explicit template instantiations for common types
template Result<uint32_t>
KsPropertySet::get_property_typed<uint32_t>(const GUID &, uint32_t);
template Result<int32_t>
KsPropertySet::get_property_typed<int32_t>(const GUID &, uint32_t);
template Result<bool> KsPropertySet::get_property_typed<bool>(const GUID &,
                                                             uint32_t);

template Result<void>
KsPropertySet::set_property_typed<uint32_t>(const GUID &, uint32_t,
                                            const uint32_t &);
template Result<void>
KsPropertySet::set_property_typed<int32_t>(const GUID &, uint32_t,
                                           const int32_t &);
template Result<void>
KsPropertySet::set_property_typed<bool>(const GUID &, uint32_t, const bool &);

} // namespace duvc

#endif // _WIN32
