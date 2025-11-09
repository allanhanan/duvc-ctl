/**
 * @file logging.cpp
 * @brief Logging system implementation
 */

#include <chrono>
#include <duvc-ctl/utils/logging.h>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <sstream>

namespace duvc {

// Global logging state
static std::mutex g_log_mutex;
static LogCallback g_log_callback = nullptr;
static LogLevel g_min_log_level = LogLevel::Info;

const char *to_string(LogLevel level) {
  switch (level) {
  case LogLevel::Debug:
    return "DEBUG";
  case LogLevel::Info:
    return "INFO";
  case LogLevel::Warning:
    return "WARNING";
  case LogLevel::Error:
    return "ERROR";
  case LogLevel::Critical:
    return "CRITICAL";
  default:
    return "UNKNOWN";
  }
}

/**
 * @brief Get current timestamp as string
 * @return Formatted timestamp string
 */
static std::string get_timestamp() {
  auto now = std::chrono::system_clock::now();
  auto time_t = std::chrono::system_clock::to_time_t(now);
  auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                now.time_since_epoch()) %
            1000;

  std::ostringstream ss;
  ss << std::put_time(std::localtime(&time_t), "%Y-%m-%d %H:%M:%S");
  ss << '.' << std::setfill('0') << std::setw(3) << ms.count();
  return ss.str();
}

/**
 * @brief Default logging callback that writes to stderr
 * @param level Log level
 * @param message Log message
 */
static void default_log_callback(LogLevel level, const std::string &message) {
  std::ostringstream ss;
  ss << "[" << get_timestamp() << "] "
     << "[" << to_string(level) << "] " << message << std::endl;

  if (level >= LogLevel::Error) {
    std::cerr << ss.str();
    std::cerr.flush();
  } else {
    std::cout << ss.str();
    std::cout.flush();
  }
}

void set_log_callback(LogCallback callback) {
  std::lock_guard<std::mutex> lock(g_log_mutex);
  g_log_callback = callback;
}

void set_log_level(LogLevel level) {
  std::lock_guard<std::mutex> lock(g_log_mutex);
  g_min_log_level = level;
}

LogLevel get_log_level() {
  std::lock_guard<std::mutex> lock(g_log_mutex);
  return g_min_log_level;
}

void log_message(LogLevel level, const std::string &message) {
  std::lock_guard<std::mutex> lock(g_log_mutex);

  // Check minimum log level
  if (level < g_min_log_level) {
    return;
  }

  // Use callback if set, otherwise use default
  if (g_log_callback) {
    try {
      g_log_callback(level, message);
    } catch (...) {
      // If user callback throws, fall back to default
      default_log_callback(LogLevel::Error,
                           "Exception in user log callback - " + message);
    }
  } else {
    default_log_callback(level, message);
  }
}

void log_debug(const std::string &message) {
  log_message(LogLevel::Debug, message);
}

void log_info(const std::string &message) {
  log_message(LogLevel::Info, message);
}

void log_warning(const std::string &message) {
  log_message(LogLevel::Warning, message);
}

void log_error(const std::string &message) {
  log_message(LogLevel::Error, message);
}

void log_critical(const std::string &message) {
  log_message(LogLevel::Critical, message);
}

} // namespace duvc
