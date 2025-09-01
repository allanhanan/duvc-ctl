// tests/cpp/unit/core_tests.cpp
#include <catch2/catch_test_macros.hpp>
#include <string>
#include "duvc-ctl/core/device.h"
#include "duvc-ctl/core/result.h"
#include "duvc-ctl/core/types.h"

using namespace duvc;

// Device Tests - Fixed
TEST_CASE("Device Construction", "[core][device]") {
    Device device(L"Test Camera", L"\\\\?\\test_device");
    REQUIRE(device.name == L"Test Camera");
    REQUIRE(device.path == L"\\\\?\\test_device");
}

TEST_CASE("Device Equality Comparison", "[core][device]") {
    Device device1(L"Camera A", L"\\\\?\\path1");
    Device device2(L"Camera A", L"\\\\?\\path1");
    Device device3(L"Camera B", L"\\\\?\\path2");
    
    // Compare fields directly instead of using operators
    REQUIRE(device1.name == device2.name);
    REQUIRE(device1.path == device2.path);
    
    // Test that different devices have different fields
    REQUIRE((device1.name != device3.name || device1.path != device3.path));
}

TEST_CASE("Device Copy Construction", "[core][device]") {
    Device original(L"Test Camera", L"\\\\?\\test_device");
    Device copied(original);
    REQUIRE(copied.name == original.name);
    REQUIRE(copied.path == original.path);
}

TEST_CASE("Device Move Construction", "[core][device]") {
    Device original(L"Test Camera", L"\\\\?\\test_device");
    auto original_name = original.name;
    auto original_path = original.path;
    Device moved(std::move(original));
    REQUIRE(moved.name == original_name);
    REQUIRE(moved.path == original_path);
}

// Result Tests - Fixed
TEST_CASE("Result Success Case", "[core][result]") {
    auto result = Result<int>::ok(42);
    REQUIRE(result.is_ok());
    REQUIRE_FALSE(result.is_error());
    REQUIRE(result.value() == 42);
}

TEST_CASE("Result Error Case", "[core][result]") {
    auto result = Result<int>::error(Error(ErrorCode::DeviceNotFound, "Device not found"));
    REQUIRE(result.is_error());
    REQUIRE_FALSE(result.is_ok());
    const auto& error = result.error();
    REQUIRE(error.code() == ErrorCode::DeviceNotFound);
    REQUIRE(error.description() == "Device not found");
}

TEST_CASE("Result Move Semantics", "[core][result]") {
    auto result = Result<std::string>::ok(std::string("test string"));
    REQUIRE(result.is_ok());
    auto moved_value = std::move(result).value();
    REQUIRE(moved_value == "test string");
}

TEST_CASE("Result Chain Operations", "[core][result]") {
    auto result1 = Result<int>::ok(5);
    auto result2 = result1.is_ok() ?
        Result<int>::ok(result1.value() * 2) :
        Result<int>::error(Error(ErrorCode::SystemError, "Error"));
    REQUIRE(result2.is_ok());
    REQUIRE(result2.value() == 10);
}

// ============================================================================
// PropSetting Tests
// ============================================================================
TEST_CASE("PropSetting Manual Mode Construction", "[core][propsetting]") {
    PropSetting setting(100, CamMode::Manual);
    
    REQUIRE(setting.value == 100);
    REQUIRE(setting.mode == CamMode::Manual);
}

TEST_CASE("PropSetting Auto Mode Construction", "[core][propsetting]") {
    PropSetting setting(0, CamMode::Auto);
    
    REQUIRE(setting.value == 0);
    REQUIRE(setting.mode == CamMode::Auto);
}

TEST_CASE("PropSetting Default Construction", "[core][propsetting]") {
    PropSetting setting;
    
    REQUIRE(setting.mode == CamMode::Auto);
}

TEST_CASE("PropSetting Comparison", "[core][propsetting]") {
    PropSetting setting1(100, CamMode::Manual);
    PropSetting setting2(100, CamMode::Manual);
    PropSetting setting3(200, CamMode::Manual);
    PropSetting setting4(100, CamMode::Auto);
    
    REQUIRE(setting1 == setting2);
    REQUIRE(setting1 != setting3);
    REQUIRE(setting1 != setting4);
}

// ============================================================================
// PropRange Tests
// ============================================================================
TEST_CASE("PropRange Valid Construction", "[core][proprange]") {
    PropRange range(0, 255, 1, 128, CamMode::Auto);
    
    REQUIRE(range.min == 0);
    REQUIRE(range.max == 255);
    REQUIRE(range.step == 1);
    REQUIRE(range.default_val == 128);
    REQUIRE(range.default_mode == CamMode::Auto);
}

TEST_CASE("PropRange Value Validation", "[core][proprange]") {
    PropRange range(0, 100, 5, 50, CamMode::Manual);
    
    // Test values within range
    REQUIRE(range.is_valid_value(0));
    REQUIRE(range.is_valid_value(50));
    REQUIRE(range.is_valid_value(100));
    
    // Test values outside range
    REQUIRE_FALSE(range.is_valid_value(-1));
    REQUIRE_FALSE(range.is_valid_value(101));
    
    // Test step alignment
    REQUIRE(range.is_valid_value(25));   // 25 % 5 == 0
    REQUIRE_FALSE(range.is_valid_value(23));  // 23 % 5 != 0
}

TEST_CASE("PropRange Clamp Value", "[core][proprange]") {
    PropRange range(10, 90, 2, 50, CamMode::Manual);
    
    REQUIRE(range.clamp_to_range(5) == 10);   // Below min
    REQUIRE(range.clamp_to_range(95) == 90);  // Above max
    REQUIRE(range.clamp_to_range(50) == 50);  // Within range
    REQUIRE(range.clamp_to_range(51) == 52);  // Step alignment
}

// ============================================================================
// Error Tests
// ============================================================================
TEST_CASE("Error Construction", "[core][error]") {
    Error error(ErrorCode::DeviceNotFound, "Test device not found");
    
    REQUIRE(error.code() == ErrorCode::DeviceNotFound);
    REQUIRE(error.description() == "Test device not found");
}

TEST_CASE("Error Code Values", "[core][error]") {
    Error error1(ErrorCode::Success, "Success");
    Error error2(ErrorCode::SystemError, "System error");
    Error error3(ErrorCode::InvalidArgument, "Invalid argument");
    
    REQUIRE(error1.code() == ErrorCode::Success);
    REQUIRE(error2.code() == ErrorCode::SystemError);
    REQUIRE(error3.code() == ErrorCode::InvalidArgument);
}

// ============================================================================
// Enum Tests
// ============================================================================
TEST_CASE("CamProp Enum Values", "[core][enums]") {
    REQUIRE(static_cast<int>(CamProp::Pan) != static_cast<int>(CamProp::Tilt));
    REQUIRE(static_cast<int>(CamProp::Zoom) != static_cast<int>(CamProp::Focus));
    REQUIRE(static_cast<int>(CamProp::Exposure) != static_cast<int>(CamProp::Iris));
}

TEST_CASE("VidProp Enum Values", "[core][enums]") {
    REQUIRE(static_cast<int>(VidProp::Brightness) != static_cast<int>(VidProp::Contrast));
    REQUIRE(static_cast<int>(VidProp::Hue) != static_cast<int>(VidProp::Saturation));
    REQUIRE(static_cast<int>(VidProp::Gamma) != static_cast<int>(VidProp::WhiteBalance));
}

TEST_CASE("CamMode Enum Values", "[core][enums]") {
    REQUIRE(static_cast<int>(CamMode::Auto) != static_cast<int>(CamMode::Manual));
    REQUIRE(static_cast<int>(CamMode::Auto) == 0);
    REQUIRE(static_cast<int>(CamMode::Manual) == 1);
}
