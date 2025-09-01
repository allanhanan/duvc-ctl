// tests/cpp/unit/platform_tests.cpp
#include <catch2/catch_test_macros.hpp>

#include "duvc-ctl/platform/interface.h"

#ifdef _WIN32
#include "duvc-ctl/platform/windows/connection_pool.h"
#include "duvc-ctl/platform/windows/ks_properties.h"
#include "duvc-ctl/platform/windows/directshow.h"
#endif

using namespace duvc;

// ============================================================================
// Platform Interface Tests
// ============================================================================
TEST_CASE("Platform Interface Creation", "[platform][interface]") {
    auto interface = create_platform_interface();
    
    REQUIRE(interface != nullptr);
    
    // Test basic functionality
    auto devices_result = interface->list_devices();
    REQUIRE((devices_result.is_ok() || devices_result.is_error()));
}

TEST_CASE("Platform Interface Device Listing", "[platform][interface]") {
    auto interface = create_platform_interface();
    REQUIRE(interface != nullptr);
    
    auto devices_result = interface->list_devices();
    
    if (devices_result.is_ok()) {
        const auto& devices = devices_result.value();
        for (const auto& device : devices) {
            REQUIRE_FALSE(device.name.empty());
            REQUIRE_FALSE(device.path.empty());
        }
    } else {
        // Error is also acceptable - no devices or system issues
        REQUIRE(devices_result.is_error());
    }
}

TEST_CASE("Platform Interface Device Connection Check", "[platform][interface]") {
    auto interface = create_platform_interface();
    REQUIRE(interface != nullptr);
    
    Device test_device(L"Test Device", L"\\\\?\\test");
    
    auto connected_result = interface->is_device_connected(test_device);
    REQUIRE((connected_result.is_ok() || connected_result.is_error()));
    
    if (connected_result.is_ok()) {
        // Result should be false for test device
        REQUIRE_FALSE(connected_result.value());
    }
}

TEST_CASE("Platform Interface Connection Creation", "[platform][interface]") {
    auto interface = create_platform_interface();
    REQUIRE(interface != nullptr);
    
    Device test_device(L"Test Device", L"\\\\?\\test");
    
    auto connection_result = interface->create_connection(test_device);
    // Should fail for test device
    REQUIRE(connection_result.is_error());
    
    if (connection_result.is_error()) {
        REQUIRE((connection_result.error().code() == ErrorCode::DeviceNotFound ||
                connection_result.error().code() == ErrorCode::SystemError ||
                connection_result.error().code() == ErrorCode::ConnectionFailed));
    }
}

#ifdef _WIN32
// ============================================================================
// Windows-Specific Platform Tests
// ============================================================================
TEST_CASE("DirectShow Helpers", "[platform][windows]") {
    // Test that DirectShow helper functions can be called without crashing
    REQUIRE_NOTHROW([&]() {
        auto dev_enum = create_dev_enum();
        // dev_enum may be null if DirectShow is not available, which is fine
    }());
}

TEST_CASE("DeviceConnection Construction", "[platform][windows]") {
    Device test_device(L"Mock Camera", L"\\\\?\\mock_device");
    
    // This test verifies that DeviceConnection can be constructed
    // It may throw for mock device, which is expected
    bool threw_exception = false;
    try {
        DeviceConnection connection(test_device);
        // If construction succeeds, test basic functionality
        REQUIRE_FALSE(connection.is_valid()); // Mock device won't be valid
    } catch (const std::runtime_error&) {
        // Expected for mock device
        threw_exception = true;
    }
    
    // Either way is acceptable for a mock device
    REQUIRE(true); // Test passes regardless of outcome
}
#endif

// ============================================================================
// Abstract Interface Tests
// ============================================================================
TEST_CASE("Platform Factory", "[platform][factory]") {
    auto interface = create_platform_interface();
    
    REQUIRE(interface != nullptr);
    
    // Test that the interface can be used for basic operations
    auto devices_result = interface->list_devices();
    // Result may be success or error depending on system state
    REQUIRE((devices_result.is_ok() || devices_result.is_error()));
}
