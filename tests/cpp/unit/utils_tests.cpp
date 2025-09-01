// tests/cpp/unit/utils_tests.cpp
#include <catch2/catch_test_macros.hpp>

#include "duvc-ctl/utils/logging.h"
#include "duvc-ctl/utils/error_decoder.h"
#include "duvc-ctl/utils/string_conversion.h"

#include <memory>
#include <vector>

using namespace duvc;

// ============================================================================
// Logging Tests
// ============================================================================
class LogCapture {
public:
    void setup() {
        set_log_level(LogLevel::Info);
        captured_messages_.clear();
        set_log_callback([this](LogLevel level, const std::string& message) {
            captured_messages_.emplace_back(level, message);
        });
    }
    
    void teardown() {
        set_log_callback(nullptr);
    }
    
    std::vector<std::pair<LogLevel, std::string>> captured_messages_;
};

TEST_CASE("Basic Logging", "[utils][logging]") {
    LogCapture capture;
    capture.setup();
    
    log_info("Test info message");
    log_warning("Test warning message");
    log_error("Test error message");
    
    REQUIRE(capture.captured_messages_.size() == 3);
    
    REQUIRE(capture.captured_messages_[0].first == LogLevel::Info);
    REQUIRE(capture.captured_messages_[0].second == "Test info message");
    
    REQUIRE(capture.captured_messages_[1].first == LogLevel::Warning);
    REQUIRE(capture.captured_messages_[1].second == "Test warning message");
    
    REQUIRE(capture.captured_messages_[2].first == LogLevel::Error);
    REQUIRE(capture.captured_messages_[2].second == "Test error message");
    
    capture.teardown();
}

TEST_CASE("Log Level Filtering", "[utils][logging]") {
    LogCapture capture;
    capture.setup();
    
    set_log_level(LogLevel::Warning);
    
    log_debug("Debug message");
    log_info("Info message");
    log_warning("Warning message");
    log_error("Error message");
    log_critical("Critical message");
    
    // Should only capture Warning, Error, and Critical
    REQUIRE(capture.captured_messages_.size() == 3);
    
    REQUIRE(capture.captured_messages_[0].first == LogLevel::Warning);
    REQUIRE(capture.captured_messages_[1].first == LogLevel::Error);
    REQUIRE(capture.captured_messages_[2].first == LogLevel::Critical);
    
    capture.teardown();
}

TEST_CASE("Log Level Get/Set", "[utils][logging]") {
    set_log_level(LogLevel::Debug);
    REQUIRE(get_log_level() == LogLevel::Debug);
    
    set_log_level(LogLevel::Critical);
    REQUIRE(get_log_level() == LogLevel::Critical);
    
    set_log_level(LogLevel::Info);
    REQUIRE(get_log_level() == LogLevel::Info);
}

TEST_CASE("Log Level String Conversion", "[utils][logging]") {
    REQUIRE(std::string(to_string(LogLevel::Debug)) == "Debug");
    REQUIRE(std::string(to_string(LogLevel::Info)) == "Info");
    REQUIRE(std::string(to_string(LogLevel::Warning)) == "Warning");
    REQUIRE(std::string(to_string(LogLevel::Error)) == "Error");
    REQUIRE(std::string(to_string(LogLevel::Critical)) == "Critical");
}

TEST_CASE("Direct Log Message", "[utils][logging]") {
    LogCapture capture;
    capture.setup();
    
    log_message(LogLevel::Info, "Direct log message");
    
    REQUIRE(capture.captured_messages_.size() == 1);
    REQUIRE(capture.captured_messages_[0].first == LogLevel::Info);
    REQUIRE(capture.captured_messages_[0].second == "Direct log message");
    
    capture.teardown();
}

TEST_CASE("No Callback Logging", "[utils][logging]") {
    set_log_callback(nullptr);
    
    // Should not crash when no callback is set
    REQUIRE_NOTHROW([&]() {
        log_info("Message with no callback");
        log_error("Error with no callback");
    }());
}

TEST_CASE("Logging Macros", "[utils][logging]") {
    LogCapture capture;
    capture.setup();
    
    // Test logging macros
    DUVC_LOG_INFO("Info macro message");
    DUVC_LOG_WARNING("Warning macro message");
    DUVC_LOG_ERROR("Error macro message");
    
    // Should capture messages since default level allows them
    REQUIRE(capture.captured_messages_.size() >= 3);
    
    // Check that macro messages are properly formatted
    bool found_info = false;
    for (const auto& msg : capture.captured_messages_) {
        if (msg.second == "Info macro message") {
            found_info = true;
            REQUIRE(msg.first == LogLevel::Info);
            break;
        }
    }
    REQUIRE(found_info);
    
    capture.teardown();
}

// ============================================================================
// String Conversion Tests
// ============================================================================
TEST_CASE("CamProp String Conversion", "[utils][string]") {
    REQUIRE(std::string(to_string(CamProp::Pan)) == "Pan");
    REQUIRE(std::string(to_string(CamProp::Tilt)) == "Tilt");
    REQUIRE(std::string(to_string(CamProp::Zoom)) == "Zoom");
    REQUIRE(std::string(to_string(CamProp::Exposure)) == "Exposure");
    REQUIRE(std::string(to_string(CamProp::Focus)) == "Focus");
    REQUIRE(std::string(to_string(CamProp::Iris)) == "Iris");
}

TEST_CASE("VidProp String Conversion", "[utils][string]") {
    REQUIRE(std::string(to_string(VidProp::Brightness)) == "Brightness");
    REQUIRE(std::string(to_string(VidProp::Contrast)) == "Contrast");
    REQUIRE(std::string(to_string(VidProp::Hue)) == "Hue");
    REQUIRE(std::string(to_string(VidProp::Saturation)) == "Saturation");
    REQUIRE(std::string(to_string(VidProp::Sharpness)) == "Sharpness");
    REQUIRE(std::string(to_string(VidProp::Gamma)) == "Gamma");
}

TEST_CASE("CamMode String Conversion", "[utils][string]") {
    REQUIRE(std::string(to_string(CamMode::Auto)) == "AUTO");
    REQUIRE(std::string(to_string(CamMode::Manual)) == "MANUAL");
}

TEST_CASE("CamProp Wide String Conversion", "[utils][string]") {
    REQUIRE(std::wstring(to_wstring(CamProp::Pan)) == L"Pan");
    REQUIRE(std::wstring(to_wstring(CamProp::Tilt)) == L"Tilt");
    REQUIRE(std::wstring(to_wstring(CamProp::Zoom)) == L"Zoom");
    REQUIRE(std::wstring(to_wstring(CamProp::Exposure)) == L"Exposure");
}

TEST_CASE("VidProp Wide String Conversion", "[utils][string]") {
    REQUIRE(std::wstring(to_wstring(VidProp::Brightness)) == L"Brightness");
    REQUIRE(std::wstring(to_wstring(VidProp::Contrast)) == L"Contrast");
    REQUIRE(std::wstring(to_wstring(VidProp::Hue)) == L"Hue");
    REQUIRE(std::wstring(to_wstring(VidProp::Saturation)) == L"Saturation");
}

TEST_CASE("CamMode Wide String Conversion", "[utils][string]") {
    REQUIRE(std::wstring(to_wstring(CamMode::Auto)) == L"AUTO");
    REQUIRE(std::wstring(to_wstring(CamMode::Manual)) == L"MANUAL");
}

// ============================================================================
// Error Decoder Tests
// ============================================================================
TEST_CASE("Decode System Error", "[utils][error]") {
    // Test system error decoding
    std::string result = decode_system_error(0);
    REQUIRE_FALSE(result.empty());
    
    std::string error_result = decode_system_error(2); // File not found
    REQUIRE_FALSE(error_result.empty());
    REQUIRE(result != error_result);
}

#ifdef _WIN32
TEST_CASE("Decode HRESULT", "[utils][error]") {
    // Test HRESULT decoding
    std::string success_result = decode_hresult(S_OK);
    REQUIRE_FALSE(success_result.empty());
    
    std::string error_result = decode_hresult(E_FAIL);
    REQUIRE_FALSE(error_result.empty());
    REQUIRE(success_result != error_result);
}

TEST_CASE("HRESULT Details", "[utils][error]") {
    std::string details = get_hresult_details(E_INVALIDARG);
    REQUIRE_FALSE(details.empty());
    
    // Should contain facility and code information
    REQUIRE(details.find("0x") != std::string::npos);
}

TEST_CASE("Device Error Detection", "[utils][error]") {
    // Test device error detection
    REQUIRE(is_device_error(0x80070015));  // ERROR_NOT_READY
    REQUIRE_FALSE(is_device_error(E_INVALIDARG));
}

TEST_CASE("Permission Error Detection", "[utils][error]") {
    // Test permission error detection
    REQUIRE(is_permission_error(E_ACCESSDENIED));
    REQUIRE_FALSE(is_permission_error(S_OK));
}
#endif

TEST_CASE("Diagnostic Information", "[utils][error]") {
    std::string diagnostics = get_diagnostic_info();
    
    REQUIRE_FALSE(diagnostics.empty());
    // Should contain some system information
    REQUIRE(diagnostics.length() > 10);
}

// ============================================================================
// Error Handling Edge Cases
// ============================================================================
TEST_CASE("Empty String Handling", "[utils][error]") {
    // Test that functions handle operations properly
    REQUIRE_NOTHROW([&]() {
        decode_system_error(0);
        get_diagnostic_info();
    }());
}

TEST_CASE("Invalid Error Codes", "[utils][error]") {
    // Test handling of invalid error codes
    REQUIRE_NOTHROW([&]() {
        std::string result = decode_system_error(0xFFFFFFFF);
        REQUIRE_FALSE(result.empty()); // Should still return something
    }());
}

// ============================================================================
// Integration Tests
// ============================================================================
TEST_CASE("Logging with String Conversion", "[utils][integration]") {
    LogCapture capture;
    capture.setup();
    
    // Use string conversion with logging
    std::string prop_name = to_string(CamProp::Brightness);
    log_info("Property: " + prop_name);
    
    REQUIRE(capture.captured_messages_.size() == 1);
    REQUIRE(capture.captured_messages_[0].second.find("Brightness") != std::string::npos);
    
    capture.teardown();
}

TEST_CASE("Error Decoding with Logging", "[utils][integration]") {
    LogCapture capture;
    capture.setup();
    
    // Log decoded error
    std::string error_desc = decode_system_error(2);
    log_error("System error: " + error_desc);
    
    REQUIRE(capture.captured_messages_.size() == 1);
    REQUIRE(capture.captured_messages_[0].first == LogLevel::Error);
    REQUIRE(capture.captured_messages_[0].second.find("System error") != std::string::npos);
    
    capture.teardown();
}
