/**
 * @file com_helpers.cpp
 * @brief Internal COM utility implementations
 */

#ifdef _WIN32

#include <comdef.h>
#include <duvc-ctl/detail/com_helpers.h>
#include <sstream>

namespace duvc::detail {

com_apartment::com_apartment() {
  hr_ = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
  if (FAILED(hr_) && hr_ != RPC_E_CHANGED_MODE) {
    throw_hr(hr_, "CoInitializeEx");
  }
}

com_apartment::~com_apartment() noexcept {
  if (SUCCEEDED(hr_)) {
    CoFreeUnusedLibraries();  // Frees global COM resources (moniker factories, CLSIDs)
    // No need for CoRevokeClassObject - CoFreeUnused covers activations
  }
  if (hr_ != S_FALSE) {
    CoUninitialize();
  }
}

std::string wide_to_utf8(const wchar_t *ws) {
  if (!ws)
    return {};

  int sz =
      WideCharToMultiByte(CP_UTF8, 0, ws, -1, nullptr, 0, nullptr, nullptr);
  std::string out(sz > 0 ? sz - 1 : 0, '\0');
  if (sz > 0) {
    WideCharToMultiByte(CP_UTF8, 0, ws, -1, out.data(), sz, nullptr, nullptr);
  }
  return out;
}

void throw_hr(HRESULT hr, const char *where) {
  _com_error err(hr);
  std::ostringstream oss;
  oss << where << " failed (hr=0x" << std::hex << hr << ")";

  if (err.ErrorMessage()) {
#ifdef UNICODE
    oss << " - " << wide_to_utf8(err.ErrorMessage());
#else
    oss << " - " << err.ErrorMessage();
#endif
  }

  throw std::runtime_error(oss.str());
}

} // namespace duvc::detail

#endif // _WIN32
