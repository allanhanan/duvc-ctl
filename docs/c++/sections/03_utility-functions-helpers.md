## 3. Utility Functions \& Helpers


### 3.1 Logging System

**Header:** `<duvc-ctl/utils/logging.h>`

The library provides a structured logging system for internal diagnostics and debugging. Applications can hook into this system to capture library events.

#### LogLevel enum

```cpp
enum class LogLevel {
    Debug = 0,      // Verbose debugging information
    Info = 1,       // General informational messages
    Warning = 2,    // Warning messages
    Error = 3,      // Error messages
    Critical = 4    // Critical errors
};
```

**Five severity levels** with numeric ordering (higher = more severe). Used to filter messages and route output.

**String conversion:**

```cpp
const char* to_string(LogLevel level);
```

Returns level name: "DEBUG", "INFO", "WARNING", "ERROR", or "CRITICAL".

***

#### Callback configuration

```cpp
using LogCallback = std::function<void(LogLevel level, const std::string& message)>;

void set_log_callback(LogCallback callback);
```

Registers a callback function to receive all log messages. The callback receives the severity level and message string.

```cpp
duvc::set_log_callback([](duvc::LogLevel level, const std::string& msg) {
    if (level >= duvc::LogLevel::Error) {
        std::cerr << "[DUVC] " << msg << "\n";
    } else {
        std::cout << "[DUVC] " << msg << "\n";
    }
});
```

**Callback behavior:**

- Pass `nullptr` to disable custom logging (reverts to default handler)
- Callback invoked with mutex held (implementation is thread-safe)
- If callback throws an exception, the system catches it and logs an error using the default handler
- Callback should be fast; slow operations may block library threads

**Default handler:** When no callback is set, messages are written to stdout (Debug/Info/Warning) or stderr (Error/Critical) with timestamps:

```
[2025-11-09 20:30:15.123] [INFO] Device enumeration started
[2025-11-09 20:30:15.456] [ERROR] Failed to open device: Device busy
```


***

#### Log level filtering

```cpp
void set_log_level(LogLevel level);
LogLevel get_log_level();
```

Controls the minimum severity level for logged messages. Messages below this threshold are silently discarded.

```cpp
// Only log warnings and above
duvc::set_log_level(duvc::LogLevel::Warning);

// Query current setting
auto level = duvc::get_log_level();
```

**Default level:** `LogLevel::Info` (Debug messages suppressed by default).

**Performance:** Filtering happens before formatting. Setting `LogLevel::Error` eliminates overhead of Debug/Info/Warning messages entirely.

***

#### Logging functions

```cpp
void log_message(LogLevel level, const std::string& message);

void log_debug(const std::string& message);
void log_info(const std::string& message);
void log_warning(const std::string& message);
void log_error(const std::string& message);
void log_critical(const std::string& message);
```

Functions for emitting log messages. The level-specific functions (`log_debug`, `log_info`, etc.) are convenience wrappers around `log_message`.

**Direct usage:**

```cpp
duvc::log_info("Camera opened successfully");
duvc::log_error("DirectShow enumeration failed");
duvc::log_debug("Property value: " + std::to_string(value));
```

**Message construction:** Accept `std::string`. Build formatted messages with `std::ostringstream` or `std::format` before passing:

```cpp
std::ostringstream oss;
oss << "Device " << device.name << " brightness=" << value;
duvc::log_info(oss.str());
```


***

#### Logging macros

```cpp
#define DUVC_LOG_DEBUG(msg)    duvc::log_debug(msg)
#define DUVC_LOG_INFO(msg)     duvc::log_info(msg)
#define DUVC_LOG_WARNING(msg)  duvc::log_warning(msg)
#define DUVC_LOG_ERROR(msg)    duvc::log_error(msg)
#define DUVC_LOG_CRITICAL(msg) duvc::log_critical(msg)
```

Macros for logging used internally by the library. Applications can use these or call the functions directly—they're functionally identical.

**Internal usage patterns:**

```cpp
DUVC_LOG_DEBUG("Querying property range");
DUVC_LOG_WARNING("Property not supported, trying fallback");
DUVC_LOG_ERROR("COM initialization failed");
```

**Note:** These are simple wrappers, not variadic macros. Formatting must be done before passing the message.

***

#### Thread safety

The logging system is fully thread-safe:

- Global state (`g_log_callback`, `g_min_log_level`) protected by mutex
- Callbacks invoked with lock held to prevent races
- Safe to call from multiple threads concurrently

**Mutex contention:** Heavy logging from many threads may create lock contention. Keep callbacks fast or buffer messages for async processing.

***

#### Typical log output

**Default format:**

```
[2025-11-09 20:15:30.123] [DEBUG] Enumerating DirectShow video devices
[2025-11-09 20:15:30.156] [INFO] Found 2 devices
[2025-11-09 20:15:30.201] [DEBUG] Opening device: Logitech HD Webcam
[2025-11-09 20:15:30.345] [INFO] Device connection established
[2025-11-09 20:15:31.012] [WARNING] Property Iris not supported
[2025-11-09 20:15:31.234] [ERROR] Failed to set Pan: value out of range
```

**Timestamp format:** `YYYY-MM-DD HH:MM:SS.mmm` (millisecond precision).

***

#### Integration patterns

**Redirect to application logger:**

```cpp
#include <spdlog/spdlog.h>

duvc::set_log_callback([](duvc::LogLevel level, const std::string& msg) {
    switch (level) {
        case duvc::LogLevel::Debug:   spdlog::debug(msg); break;
        case duvc::LogLevel::Info:    spdlog::info(msg); break;
        case duvc::LogLevel::Warning: spdlog::warn(msg); break;
        case duvc::LogLevel::Error:   spdlog::error(msg); break;
        case duvc::LogLevel::Critical: spdlog::critical(msg); break;
    }
});
```

**Write to file:**

```cpp
std::ofstream logfile("duvc.log", std::ios::app);
duvc::set_log_callback([&logfile](duvc::LogLevel level, const std::string& msg) {
    logfile << "[" << duvc::to_string(level) << "] " << msg << "\n";
    logfile.flush();
});
```

**Suppress all logging:**

```cpp
duvc::set_log_level(duvc::LogLevel::Critical + 1);  // No messages pass
// Or:
duvc::set_log_callback(nullptr);
duvc::set_log_level(duvc::LogLevel::Critical);
```


***

#### What the library logs

**Debug level:**

- DirectShow interface queries
- Property range queries
- Detailed operation traces

**Info level:**

- Device enumeration results
- Connection establishment
- Property changes

**Warning level:**

- Unsupported properties
- Fallback behavior
- Non-fatal errors

**Error level:**

- COM failures
- Device access errors
- Invalid operations

**Critical level:**

- Unrecoverable initialization failures
- System resource exhaustion

**Production recommendation:** Set level to `Info` or `Warning` for normal operation. Enable `Debug` only when diagnosing issues.

### 3.2 String Conversion

**Header:** `<duvc-ctl/utils/string_conversion.h>`

Utilities for converting enum values to strings and performing character encoding conversions.

#### Enum to string conversion

```cpp
const char* to_string(CamProp prop);
const char* to_string(VidProp prop);
const char* to_string(CamMode mode);
```

Converts enum values to narrow (UTF-8) C-style strings.

```cpp
duvc::CamProp prop = duvc::CamProp::Zoom;
std::cout << "Property: " << duvc::to_string(prop) << "\n";  // "Zoom"

duvc::CamMode mode = duvc::CamMode::Auto;
std::cout << "Mode: " << duvc::to_string(mode) << "\n";  // "AUTO"
```

**Returns:** String literal for known enums, "Unknown" for invalid values.

***

#### Enum to wide string conversion

```cpp
const wchar_t* to_wstring(CamProp prop);
const wchar_t* to_wstring(VidProp prop);
const wchar_t* to_wstring(CamMode mode);
```

Converts enum values to wide (UTF-16 on Windows) C-style strings. Useful for Windows APIs and logging that requires wide strings.

```cpp
duvc::VidProp prop = duvc::VidProp::Brightness;
std::wcout << L"Property: " << duvc::to_wstring(prop) << L"\n";  // L"Brightness"
```

**Note:** Mode strings are uppercase: `L"AUTO"` and `L"MANUAL"`.

***

#### UTF-16 to UTF-8 conversion

```cpp
std::string to_utf8(const std::wstring& wstr);
```

Converts a wide string (UTF-16 on Windows) to a UTF-8 encoded narrow string. Essential for working with Windows device names and paths in portable code.

```cpp
Device camera = /* from list_devices() */;
std::string utf8_name = duvc::to_utf8(camera.name);

// Safe for JSON, file I/O, cross-platform APIs
std::cout << "Camera: " << utf8_name << "\n";
```

**Implementation:** Uses Windows `WideCharToMultiByte` with `CP_UTF8` flag for proper character conversion.

**Error handling:** Throws `std::runtime_error` if conversion fails. Returns empty string for empty input.

**Use cases:**

- Logging device names to files/console
- Serializing device info to JSON/XML
- Passing device names to cross-platform APIs
- Displaying camera names in UI (UTF-8 frameworks)

***

### 3.3 Error Decoding

**Header:** `<duvc-ctl/utils/error_decoder.h>`

Utilities for decoding Windows system errors and COM HRESULTs into human-readable messages.

#### System error decoding

```cpp
std::string decode_system_error(unsigned long error_code);
```

Converts a Windows system error code (e.g., from `GetLastError()`) to a descriptive string.

```cpp
unsigned long err_code = GetLastError();
std::string description = duvc::decode_system_error(err_code);
std::cerr << "Error: " << description << "\n";
```

**Implementation:** Uses `FormatMessageW` to retrieve localized error text from Windows, then converts to UTF-8.

**Fallback:** If `FormatMessage` fails, returns `"System error 0x[hex_code]"`.

**Platform:** Windows only. On other platforms, returns `"System error [code]"`.

***

#### HRESULT decoding

```cpp
std::string decode_hresult(HRESULT hr);
std::string get_hresult_details(HRESULT hr);
```

Windows-only functions for decoding COM HRESULTs.

**`decode_hresult`:** Converts HRESULT to human-readable description using `_com_error`.

```cpp
HRESULT hr = CoCreateInstance(/* ... */);
if (FAILED(hr)) {
    std::string msg = duvc::decode_hresult(hr);
    DUVC_LOG_ERROR(msg);
}
```

**`get_hresult_details`:** Provides extended information including hex code, facility, error code, severity, and description.

```cpp
std::string details = duvc::get_hresult_details(0x8007001F);
// Returns: "HRESULT: 0x8007001F (Facility: 7, Code: 31) [FAILURE] - A device attached to the system is not functioning."
```

**Output format:**

```
HRESULT: 0x[hex] (Facility: [num], Code: [num]) [SUCCESS/FAILURE] - [description]
```


***

#### Error classification

```cpp
bool is_device_error(HRESULT hr);
bool is_permission_error(HRESULT hr);
```

Windows-only functions for categorizing HRESULTs.

**`is_device_error`:** Returns `true` for device-related failures.

Recognized codes:

- `E_ACCESSDENIED`
- `ERROR_DEVICE_NOT_CONNECTED`
- `ERROR_DEVICE_IN_USE`
- `ERROR_NOT_FOUND`
- `ERROR_FILE_NOT_FOUND`
- `VFW_E_CANNOT_CONNECT`
- `VFW_E_CANNOT_RENDER`
- `VFW_E_DEVICE_IN_USE`

```cpp
if (FAILED(hr) && duvc::is_device_error(hr)) {
    // Handle device disconnection/busy state
    return duvc::ErrorCode::DeviceNotFound;
}
```

**`is_permission_error`:** Returns `true` for access/permission failures.

Currently checks:

- `E_ACCESSDENIED`

```cpp
if (duvc::is_permission_error(hr)) {
    // Prompt user to grant camera permissions
    return duvc::ErrorCode::PermissionDenied;
}
```


***

#### Diagnostic information

```cpp
std::string get_diagnostic_info();
```

Collects system information useful for troubleshooting. Returns a formatted string with:

- Platform (Windows / Non-Windows)
- Windows version and build number
- Processor architecture (x64, x86, ARM64, ARM)
- COM initialization status
- DirectShow availability

```cpp
std::string diag = duvc::get_diagnostic_info();
std::cout << diag << "\n";
```

**Example output:**

```
duvc-ctl Diagnostic Information
==============================
Platform: Windows
Windows Version: 10.0 (Build 19045)
Architecture: x64
COM Status: Available
DirectShow: Available
```

**Error scenarios:**

- If COM initialization fails, includes error description
- If DirectShow unavailable, reports `CoCreateInstance` failure
- On non-Windows platforms, returns single line: `"Platform: Non-Windows (stub implementation)"`

**Use cases:**

- Include in bug reports
- Log at application startup
- Display in diagnostic/about dialogs
- Automated issue reporting

***

**Platform notes:** All HRESULT-related functions (`decode_hresult`, `get_hresult_details`, `is_device_error`, `is_permission_error`) are Windows-only and wrapped in `#ifdef _WIN32`. They do not exist in non-Windows builds.

