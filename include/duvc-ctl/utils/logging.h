#pragma once

/**
 * @file logging.h
 * @brief Structured logging interface for duvc-ctl
 */

#include <functional>
#include <string>

namespace duvc {

/**
 * @brief Log levels
 */
enum class LogLevel {
  Debug = 0,   ///< Debug information
  Info = 1,    ///< Informational messages
  Warning = 2, ///< Warning messages
  Error = 3,   ///< Error messages
  Critical = 4 ///< Critical errors
};

/**
 * @brief Convert log level to string
 * @param level Log level
 * @return Log level name
 */
const char *to_string(LogLevel level);

/**
 * @brief Log message callback type
 * @param level Log level
 * @param message Log message
 */
using LogCallback =
    std::function<void(LogLevel level, const std::string &message)>;

/**
 * @brief Set global log callback
 * @param callback Callback function (nullptr to disable logging)
 */
void set_log_callback(LogCallback callback);

/**
 * @brief Set minimum log level
 * @param level Minimum level to log
 */
void set_log_level(LogLevel level);

/**
 * @brief Get current minimum log level
 * @return Current minimum log level
 */
LogLevel get_log_level();

/**
 * @brief Log a message
 * @param level Log level
 * @param message Log message
 */
void log_message(LogLevel level, const std::string &message);

/**
 * @brief Log debug message
 * @param message Debug message
 */
void log_debug(const std::string &message);

/**
 * @brief Log info message
 * @param message Info message
 */
void log_info(const std::string &message);

/**
 * @brief Log warning message
 * @param message Warning message
 */
void log_warning(const std::string &message);

/**
 * @brief Log error message
 * @param message Error message
 */
void log_error(const std::string &message);

/**
 * @brief Log critical message
 * @param message Critical message
 */
void log_critical(const std::string &message);

// Convenience macros for formatted logging

/**
 * @def DUVC_LOG_DEBUG
 * @brief Log debug message macro
 * @param msg Message string to log at debug level
 */
#define DUVC_LOG_DEBUG(msg) duvc::log_debug(msg)

/**
 * @def DUVC_LOG_INFO
 * @brief Log info message macro
 * @param msg Message string to log at info level
 */
#define DUVC_LOG_INFO(msg) duvc::log_info(msg)

/**
 * @def DUVC_LOG_WARNING
 * @brief Log warning message macro
 * @param msg Message string to log at warning level
 */
#define DUVC_LOG_WARNING(msg) duvc::log_warning(msg)

/**
 * @def DUVC_LOG_ERROR
 * @brief Log error message macro
 * @param msg Message string to log at error level
 */
#define DUVC_LOG_ERROR(msg) duvc::log_error(msg)

/**
 * @def DUVC_LOG_CRITICAL
 * @brief Log critical message macro
 * @param msg Message string to log at critical level
 */
#define DUVC_LOG_CRITICAL(msg) duvc::log_critical(msg)

} // namespace duvc
