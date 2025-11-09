/**
 * @file constants.cpp
 * @brief Vendor-specific property implementation
 */

#ifdef _WIN32

#include <dshow.h>
#include <duvc-ctl/detail/com_helpers.h>
#include <duvc-ctl/vendor/constants.h>
#include <ks.h>
#include <ksproxy.h>

namespace duvc {

using namespace detail;

// Forward declarations
extern com_ptr<IBaseFilter> open_device_filter(const Device &dev);

static com_ptr<IKsPropertySet> get_property_set(IBaseFilter *f) {
  com_ptr<IKsPropertySet> props;
  if (FAILED(f->QueryInterface(IID_IKsPropertySet,
                               reinterpret_cast<void **>(props.put())))) {
    return {};
  }
  return props;
}

bool get_vendor_property(const Device &dev, const GUID &property_set,
                         ULONG property_id, std::vector<uint8_t> &data) {
  try {
    com_apartment com;
    auto filter = open_device_filter(dev);
    auto props = get_property_set(filter.get());
    if (!props)
      return false;

    ULONG bytes_returned = 0;
    HRESULT hr = props->Get(property_set, property_id, nullptr, 0, nullptr, 0,
                            &bytes_returned);
    if (FAILED(hr) || bytes_returned == 0)
      return false;

    data.resize(bytes_returned);
    hr = props->Get(property_set, property_id, nullptr, 0, data.data(),
                    bytes_returned, &bytes_returned);
    return SUCCEEDED(hr);
  } catch (...) {
    return false;
  }
}

bool set_vendor_property(const Device &dev, const GUID &property_set,
                         ULONG property_id, const std::vector<uint8_t> &data) {
  try {
    com_apartment com;
    auto filter = open_device_filter(dev);
    auto props = get_property_set(filter.get());
    if (!props)
      return false;

    HRESULT hr = props->Set(property_set, property_id, nullptr, 0,
                            const_cast<uint8_t *>(data.data()), data.size());
    return SUCCEEDED(hr);
  } catch (...) {
    return false;
  }
}

bool query_vendor_property_support(const Device &dev, const GUID &property_set,
                                   ULONG property_id) {
  try {
    com_apartment com;
    auto filter = open_device_filter(dev);
    auto props = get_property_set(filter.get());
    if (!props)
      return false;

    ULONG type_support = 0;
    HRESULT hr =
        props->QuerySupported(property_set, property_id, &type_support);
    return SUCCEEDED(hr) &&
           (type_support & (KSPROPERTY_SUPPORT_GET | KSPROPERTY_SUPPORT_SET));
  } catch (...) {
    return false;
  }
}

} // namespace duvc

#endif // _WIN32
