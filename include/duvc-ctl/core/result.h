#pragma once

/**
 * @file result.h
 * @brief Result/Error type system for duvc-ctl
 */

#include <string>
#include <variant>
#include <system_error>
#include <optional>
#include <string>    
#include <iostream> 

namespace duvc {

/**
 * @brief Error codes for duvc operations
 */
enum class ErrorCode {
    Success = 0,           ///< Operation succeeded
    DeviceNotFound,        ///< Device not found or disconnected
    DeviceBusy,            ///< Device is busy or in use
    PropertyNotSupported,  ///< Property not supported by device
    InvalidValue,          ///< Property value out of range
    PermissionDenied,      ///< Insufficient permissions
    SystemError,           ///< System/platform error
    InvalidArgument,       ///< Invalid function argument
    NotImplemented         ///< Feature not implemented on this platform
};

/**
 * @brief Convert error code to string
 * @param code Error code
 * @return Human-readable error description
 */
const char* to_string(ErrorCode code);

/**
 * @brief Error information with context
 */
class Error {
public:
    /**
     * @brief Create error with code and message
     * @param code Error code
     * @param message Descriptive error message
     */
    Error(ErrorCode code, std::string message = "");
    
    /**
     * @brief Create error from system error
     * @param code System error code
     * @param message Additional context message
     */
    Error(std::error_code code, std::string message = "");
    
    /// Get error code
    ErrorCode code() const { return code_; }
    
    /// Get error message
    const std::string& message() const { return message_; }
    
    /// Get full error description
    std::string description() const;
    
private:
    ErrorCode code_;
    std::string message_;
};

/**
 * @brief Result type that can contain either a value or an error
 * @tparam T Value type (use void for operations that don't return values)
 */
template<typename T>
class Result {
public:
    /**
     * @brief Create successful result with value
     * @param value Result value
     */
    Result(T value) : data_(std::move(value)) {}
    
    /**
     * @brief Create error result
     * @param error Error information
     */
    Result(Error error) : data_(std::move(error)) {}
    
    /**
     * @brief Create error result from error code
     * @param code Error code
     * @param message Optional error message
     */
    Result(ErrorCode code, std::string message = "") 
        : data_(Error(code, std::move(message))) {}
    
    /**
     * @brief Check if result contains a value (success)
     * @return true if successful
     */
    bool is_ok() const {
        return std::holds_alternative<T>(data_);
    }
    
    /**
     * @brief Check if result contains an error
     * @return true if error
     */
    bool is_error() const {
        return std::holds_alternative<Error>(data_);
    }
    
    /**
     * @brief Get the value (assumes success)
     * @return Reference to value
     * @throws std::bad_variant_access if result is error
     */
    const T& value() const& {
        return std::get<T>(data_);
    }
    
    /**
     * @brief Get the value (assumes success)
     * @return Moved value
     * @throws std::bad_variant_access if result is error
     */
    T&& value() && {
        return std::get<T>(std::move(data_));
    }
    
    /**
     * @brief Get the error (assumes error)
     * @return Reference to error
     * @throws std::bad_variant_access if result is success
     */
    const Error& error() const {
        return std::get<Error>(data_);
    }
    
    /**
     * @brief Get value or default if error
     * @param default_value Default value to return on error
     * @return Value or default
     */
    T value_or(const T& default_value) const& {
        return is_ok() ? value() : default_value;
    }
    
    /**
     * @brief Get value or default if error
     * @param default_value Default value to return on error  
     * @return Value or default
     */
    T value_or(T&& default_value) && {
        return is_ok() ? std::move(*this).value() : std::move(default_value);
    }
    
    /**
     * @brief Boolean conversion (true if success)
     */
    explicit operator bool() const {
        return is_ok();
    }
    
private:
    std::variant<T, Error> data_;
};

/**
 * @brief Specialization for void results (operations that don't return values)
 */
template<>
class Result<void> {
public:
    /**
     * @brief Create successful void result
     */
    Result() : error_(std::nullopt) {}
    
    /**
     * @brief Create error result
     * @param error Error information
     */
    Result(Error error) : error_(std::move(error)) {}
    
    /**
     * @brief Create error result from error code
     * @param code Error code
     * @param message Optional error message
     */
    Result(ErrorCode code, std::string message = "") 
        : error_(Error(code, std::move(message))) {}
    
    /**
     * @brief Check if result is success
     * @return true if successful
     */
    bool is_ok() const {
        return !error_.has_value();
    }
    
    /**
     * @brief Check if result is error
     * @return true if error
     */
    bool is_error() const {
        return error_.has_value();
    }
    
    /**
     * @brief Get the error (assumes error)
     * @return Reference to error
     */
    const Error& error() const {
        return *error_;
    }
    
    /**
     * @brief Boolean conversion (true if success)
     */
    explicit operator bool() const {
        return is_ok();
    }
    
private:
    std::optional<Error> error_;
};

/**
 * @brief Helper to create successful Result
 * @tparam T Value type
 * @param value Value to wrap
 * @return Successful Result
 */
template<typename T>
Result<T> Ok(T value) {
    return Result<T>(std::move(value));
}

/**
 * @brief Helper to create successful void Result
 * @return Successful void Result
 */
inline Result<void> Ok() {
    return Result<void>();
}

/**
 * @brief Helper to create error Result
 * @tparam T Value type
 * @param error Error to wrap
 * @return Error Result
 */
template<typename T>
Result<T> Err(Error error) {
    return Result<T>(std::move(error));
}

/**
 * @brief Helper to create error Result from code
 * @tparam T Value type
 * @param code Error code
 * @param message Optional error message
 * @return Error Result
 */
template<typename T>
Result<T> Err(ErrorCode code, std::string message = "") {
    return Result<T>(code, std::move(message));
}

} // namespace duvc
