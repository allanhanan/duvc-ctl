/**
 * @file result.cpp
 * @brief Result/Error type implementations
 */

#include <duvc-ctl/core/result.h>

namespace duvc {

const char *to_string(ErrorCode code) {
  switch (code) {
  case ErrorCode::Success:
    return "Success";
  case ErrorCode::DeviceNotFound:
    return "Device not found or disconnected";
  case ErrorCode::DeviceBusy:
    return "Device is busy or in use";
  case ErrorCode::PropertyNotSupported:
    return "Property not supported by device";
  case ErrorCode::InvalidValue:
    return "Property value out of range";
  case ErrorCode::PermissionDenied:
    return "Insufficient permissions";
  case ErrorCode::SystemError:
    return "System/platform error";
  case ErrorCode::InvalidArgument:
    return "Invalid function argument";
  case ErrorCode::NotImplemented:
    return "Feature not implemented on this platform";
  default:
    return "Unknown error";
  }
}

Error::Error(ErrorCode code, std::string message)
    : code_(code), message_(std::move(message)) {}

Error::Error(std::error_code code, std::string message)
    : code_(ErrorCode::SystemError), message_(std::move(message)) {
  if (message_.empty()) {
    message_ = code.message();
  } else {
    message_ += ": " + code.message();
  }
}

std::string Error::description() const {
  std::string desc = to_string(code_);
  if (!message_.empty()) {
    desc += ": " + message_;
  }
  return desc;
}

} // namespace duvc
