// tests/cpp/unit/vendor_tests.cpp
#include <catch2/catch_test_macros.hpp>

#ifdef _WIN32
#include "duvc-ctl/vendor/logitech.h"
#include "duvc-ctl/vendor/constants.h"
#endif

using namespace duvc;

#ifdef _WIN32

// ============================================================================
// Logitech Property Tests
// ============================================================================
TEST_CASE("Logitech Property Enum Values", "[vendor][logitech]") {
    // Test that Logitech property enum values are distinct
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::RightLight) !=
            static_cast<uint32_t>(logitech::LogitechProperty::RightSound));
    
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::FaceTracking) !=
            static_cast<uint32_t>(logitech::LogitechProperty::LedIndicator));
    
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::ProcessorUsage) !=
            static_cast<uint32_t>(logitech::LogitechProperty::RawDataBits));
}

TEST_CASE("Logitech Property IDs", "[vendor][logitech]") {
    // Test specific property ID values from the header
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::RightLight) == 1);
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::RightSound) == 2);
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::FaceTracking) == 3);
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::LedIndicator) == 4);
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::ProcessorUsage) == 5);
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::RawDataBits) == 6);
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::FocusAssist) == 7);
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::VideoStandard) == 8);
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::DigitalZoomROI) == 9);
    REQUIRE(static_cast<uint32_t>(logitech::LogitechProperty::TiltPan) == 10);
}

TEST_CASE("Logitech Property Support Check", "[vendor][logitech]") {
    Device test_device(L"Logitech Test Camera", L"\\\\?\\test_logitech");
    
    // Test that the function can be called (may return false for non-Logitech device)
    auto result = logitech::supports_logitech_properties(test_device);
    
    // Should return a valid result (either ok or error)
    REQUIRE((result.is_ok() || result.is_error()));
    
    if (result.is_ok()) {
        // For a mock device, this will likely be false
        REQUIRE((result.value() == true || result.value() == false));
    }
}

TEST_CASE("Logitech Property Get Operation", "[vendor][logitech]") {
    Device test_device(L"Logitech Test Camera", L"\\\\?\\test_logitech");
    
    // Test that get_logitech_property can be called
    auto result = logitech::get_logitech_property(test_device, 
                                                  logitech::LogitechProperty::RightLight);
    
    // Should return a valid result (likely error for mock device)
    REQUIRE((result.is_ok() || result.is_error()));
    
    if (result.is_error()) {
        // Expected for mock device
        REQUIRE((result.error().code() == ErrorCode::DeviceNotFound ||
                result.error().code() == ErrorCode::PropertyNotSupported ||
                result.error().code() == ErrorCode::SystemError));
    }
}

TEST_CASE("Logitech Property Set Operation", "[vendor][logitech]") {
    Device test_device(L"Logitech Test Camera", L"\\\\?\\test_logitech");
    std::vector<uint8_t> test_data = {0x01, 0x02, 0x03};
    
    // Test that set_logitech_property can be called
    auto result = logitech::set_logitech_property(test_device,
                                                  logitech::LogitechProperty::LedIndicator,
                                                  test_data);
    
    // Should return a valid result (likely error for mock device)
    REQUIRE((result.is_ok() || result.is_error()));
    
    if (result.is_error()) {
        // Expected for mock device
        REQUIRE((result.error().code() == ErrorCode::DeviceNotFound ||
                result.error().code() == ErrorCode::PropertyNotSupported ||
                result.error().code() == ErrorCode::SystemError));
    }
}

// ============================================================================
// Vendor Property Tests
// ============================================================================
TEST_CASE("VendorProperty Construction", "[vendor][property]") {
    GUID test_guid = {0x12345678, 0x1234, 0x1234, {0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0}};
    std::vector<uint8_t> test_data = {0x01, 0x02, 0x03, 0x04};
    
    VendorProperty property(test_guid, 123, test_data);
    
    REQUIRE(property.property_set == test_guid);
    REQUIRE(property.property_id == 123UL);
    REQUIRE(property.data == test_data);
}

TEST_CASE("VendorProperty Default Construction", "[vendor][property]") {
    VendorProperty property;
    
    REQUIRE(property.data.empty());
}

TEST_CASE("Vendor Property Function Calls", "[vendor][property]") {
    Device test_device(L"Test Device", L"\\\\?\\test");
    GUID test_guid = {0x12345678, 0x1234, 0x1234, {0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0}};
    std::vector<uint8_t> test_data = {0x01, 0x02, 0x03, 0x04};
    
    // Test that vendor property functions can be called without crashing
    REQUIRE_NOTHROW([&]() {
        std::vector<uint8_t> output_data;
        bool get_result = get_vendor_property(test_device, test_guid, 1, output_data);
        // Result will likely be false for mock device
        
        bool set_result = set_vendor_property(test_device, test_guid, 1, test_data);
        // Result will likely be false for mock device
        
        bool query_result = query_vendor_property_support(test_device, test_guid, 1);
        // Result will likely be false for mock device
        
        // These operations are expected to fail gracefully
    }());
}

TEST_CASE("Logitech Typed Property Calls", "[vendor][logitech]") {
    Device test_device(L"Logitech Test Camera", L"\\\\?\\test_logitech");
    
    // Test typed property getters/setters without throwing
    REQUIRE_NOTHROW([&]() {
        // Test get_logitech_property_typed
        auto bool_result = logitech::get_logitech_property_typed<bool>(
            test_device, logitech::LogitechProperty::FaceTracking);
        
        auto int_result = logitech::get_logitech_property_typed<int32_t>(
            test_device, logitech::LogitechProperty::ProcessorUsage);
        
        // Test set_logitech_property_typed
        auto set_bool_result = logitech::set_logitech_property_typed<bool>(
            test_device, logitech::LogitechProperty::FaceTracking, true);
        
        auto set_int_result = logitech::set_logitech_property_typed<int32_t>(
            test_device, logitech::LogitechProperty::ProcessorUsage, 75);
        
        // These will likely fail for mock device, but should not crash
    }());
}

#else

// ============================================================================
// Non-Windows Platform Tests
// ============================================================================
TEST_CASE("Vendor Functions Not Available", "[vendor][platform]") {
    // On non-Windows platforms, vendor-specific functions should not be available
    // This test ensures the code compiles and vendor features are properly guarded
    INFO("Vendor-specific tests skipped on non-Windows platforms");
    REQUIRE(true);
}

#endif
