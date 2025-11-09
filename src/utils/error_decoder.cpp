/**
 * @file error_decoder.cpp
 * @brief Error decoding and diagnostic utilities implementation
 */

#include <duvc-ctl/utils/error_decoder.h>
#include <iomanip>
#include <sstream>

#ifdef _WIN32
#include <comdef.h>
#include <dshow.h>
#include <windows.h>
#endif

#ifdef _WIN32
#include <vfwmsgs.h>
// If vfwmsgs.h not available, define manually:
#ifndef VFW_E_DEVICE_IN_USE
#define VFW_E_DEVICE_IN_USE 0x80040228L
#endif
#endif

namespace duvc {

std::string decode_system_error(unsigned long error_code) {
#ifdef _WIN32
  LPWSTR buffer = nullptr;
  DWORD flags = FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM |
                FORMAT_MESSAGE_IGNORE_INSERTS;

  DWORD size = FormatMessageW(flags, nullptr, error_code,
                              MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
                              reinterpret_cast<LPWSTR>(&buffer), 0, nullptr);

  std::string result;
  if (size > 0 && buffer) {
    // Convert wide string to UTF-8
    int utf8_size = WideCharToMultiByte(CP_UTF8, 0, buffer, size, nullptr, 0,
                                        nullptr, nullptr);
    if (utf8_size > 0) {
      result.resize(utf8_size);
      WideCharToMultiByte(CP_UTF8, 0, buffer, size, result.data(), utf8_size,
                          nullptr, nullptr);
    }
    LocalFree(buffer);
  }

  if (result.empty()) {
    std::ostringstream ss;
    ss << "System error 0x" << std::hex << error_code;
    result = ss.str();
  }

  // Remove trailing whitespace
  while (!result.empty() && std::isspace(result.back())) {
    result.pop_back();
  }

  return result;
#else
  std::ostringstream ss;
  ss << "System error " << error_code;
  return ss.str();
#endif
}

#ifdef _WIN32

std::string decode_hresult(HRESULT hr) {
  _com_error error(hr);
  std::string description;

  if (error.ErrorMessage()) {
    // Convert wide string to UTF-8
    const wchar_t *wide_msg = error.ErrorMessage();
    int utf8_size = WideCharToMultiByte(CP_UTF8, 0, wide_msg, -1, nullptr, 0,
                                        nullptr, nullptr);
    if (utf8_size > 0) {
      description.resize(utf8_size - 1); // -1 for null terminator
      WideCharToMultiByte(CP_UTF8, 0, wide_msg, -1, description.data(),
                          utf8_size, nullptr, nullptr);
    }
  }

  if (description.empty()) {
    // Fallback to system error message
    description = decode_system_error(static_cast<unsigned long>(hr));
  }

  return description;
}

std::string get_hresult_details(HRESULT hr) {
  std::ostringstream ss;

  ss << "HRESULT: 0x" << std::hex << std::uppercase << hr << std::dec;

  // Extract facility and code
  unsigned short facility = HRESULT_FACILITY(hr);
  unsigned short code = HRESULT_CODE(hr);

  ss << " (Facility: " << facility << ", Code: " << code << ")";

  // Add severity
  if (FAILED(hr)) {
    ss << " [FAILURE]";
  } else {
    ss << " [SUCCESS]";
  }

  // Add description
  std::string description = decode_hresult(hr);
  if (!description.empty()) {
    ss << " - " << description;
  }

  return ss.str();
}

bool is_device_error(HRESULT hr) {
  // Common device-related error codes
  switch (hr) {
  case E_ACCESSDENIED:
  case HRESULT_FROM_WIN32(ERROR_DEVICE_NOT_CONNECTED):
  case HRESULT_FROM_WIN32(ERROR_DEVICE_IN_USE):
  case HRESULT_FROM_WIN32(ERROR_NOT_FOUND):
  case HRESULT_FROM_WIN32(ERROR_FILE_NOT_FOUND):
  case VFW_E_CANNOT_CONNECT:
  case VFW_E_CANNOT_RENDER:
  case VFW_E_DEVICE_IN_USE:
    return true;
  default:
    return false;
  }
}

bool is_permission_error(HRESULT hr) {
  switch (hr) {
  case E_ACCESSDENIED:
    return true;
  default:
    return false;
  }
}

#endif // _WIN32

std::string get_diagnostic_info() {
  std::ostringstream ss;

  ss << "duvc-ctl Diagnostic Information\n";
  ss << "==============================\n";

#ifdef _WIN32
  // Windows version
  ss << "Platform: Windows\n";

  OSVERSIONINFOW version_info = {};
  version_info.dwOSVersionInfoSize = sizeof(version_info);

#pragma warning(push)
#pragma warning(disable : 4996) // GetVersionEx is deprecated
  if (GetVersionExW(&version_info)) {
    ss << "Windows Version: " << version_info.dwMajorVersion << "."
       << version_info.dwMinorVersion << " (Build "
       << version_info.dwBuildNumber << ")\n";
  }
#pragma warning(pop)

  // Process architecture
  SYSTEM_INFO sys_info;
  GetSystemInfo(&sys_info);

  const char *arch = "Unknown";
  switch (sys_info.wProcessorArchitecture) {
  case PROCESSOR_ARCHITECTURE_AMD64:
    arch = "x64";
    break;
  case PROCESSOR_ARCHITECTURE_INTEL:
    arch = "x86";
    break;
  case PROCESSOR_ARCHITECTURE_ARM64:
    arch = "ARM64";
    break;
  case PROCESSOR_ARCHITECTURE_ARM:
    arch = "ARM";
    break;
  }
  ss << "Architecture: " << arch << "\n";

  // COM initialization status
  HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
  if (SUCCEEDED(hr)) {
    ss << "COM Status: Available\n";
    CoUninitialize();
  } else if (hr == RPC_E_CHANGED_MODE) {
    ss << "COM Status: Already initialized (different mode)\n";
  } else {
    ss << "COM Status: Error - " << decode_hresult(hr) << "\n";
  }

  // DirectShow availability
  ICreateDevEnum *dev_enum = nullptr;
  hr = CoCreateInstance(CLSID_SystemDeviceEnum, nullptr, CLSCTX_INPROC_SERVER,
                        IID_ICreateDevEnum,
                        reinterpret_cast<void **>(&dev_enum));
  if (SUCCEEDED(hr) && dev_enum) {
    ss << "DirectShow: Available\n";
    dev_enum->Release();
  } else {
    ss << "DirectShow: Error - " << decode_hresult(hr) << "\n";
  }

#else
  ss << "Platform: Non-Windows (stub implementation)\n";
#endif

  return ss.str();
}

} // namespace duvc
