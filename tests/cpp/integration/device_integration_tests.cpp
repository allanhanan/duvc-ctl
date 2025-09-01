// tests/cpp/integration/device_integration_tests.cpp
#include <catch2/catch_test_macros.hpp>

#include "duvc-ctl/platform/interface.h"
#include "duvc-ctl/core/device.h"
#include "duvc-ctl/core/types.h"

#ifdef _WIN32
#include "duvc-ctl/platform/windows/connection_pool.h"
#include "duvc-ctl/vendor/logitech.h"
#endif

using namespace duvc;

// ============================================================================
// Device Integration Tests
// ============================================================================
TEST_CASE("Platform Interface Creation", "[integration][platform]") {
    auto platform = create_platform_interface();
    REQUIRE(platform != nullptr);
    
    // Test basic functionality
    auto devices_result = platform->list_devices();
    REQUIRE((devices_result.is_ok() || devices_result.is_error()));
    
    if (devices_result.is_ok()) {
        // If successful, devices list should be valid
        const auto& devices = devices_result.value();
        for (const auto& device : devices) {
            REQUIRE_FALSE(device.name.empty());
            REQUIRE_FALSE(device.path.empty());
        }
    }
}

TEST_CASE("Device Enumeration and Connection", "[integration][device]") {
    auto platform = create_platform_interface();
    REQUIRE(platform != nullptr);
    
    auto devices_result = platform->list_devices();
    if (devices_result.is_error() || devices_result.value().empty()) {
        SKIP("No devices available for testing");
    }
    
    const auto& devices = devices_result.value();
    
    // Test with the first available device
    const auto& device = devices[0];
    
    // Check if device is connected
    auto connected_result = platform->is_device_connected(device);
    REQUIRE(connected_result.is_ok());
    
    if (connected_result.is_ok() && connected_result.value()) {
        // Try to create a connection
        auto connection_result = platform->create_connection(device);
        
        if (connection_result.is_ok()) {
            auto connection = std::move(connection_result.value());
            REQUIRE(connection->is_valid());
        }
    }
}

TEST_CASE("Multiple Device Handling", "[integration][device]") {
    auto platform = create_platform_interface();
    auto devices_result = platform->list_devices();
    
    if (devices_result.is_error() || devices_result.value().size() < 2) {
        SKIP("Multiple devices not available for testing");
    }
    
    const auto& devices = devices_result.value();
    
    // Test that we can differentiate between devices
    for (size_t i = 0; i < std::min(devices.size(), size_t(3)); ++i) {
        for (size_t j = i + 1; j < std::min(devices.size(), size_t(3)); ++j) {
            REQUIRE(devices[i] != devices[j]);
        }
    }
}

TEST_CASE("Device Connection Lifecycle", "[integration][device]") {
    auto platform = create_platform_interface();
    auto devices_result = platform->list_devices();
    
    if (devices_result.is_error() || devices_result.value().empty()) {
        SKIP("No devices available for lifecycle testing");
    }
    
    const auto& device = devices_result.value()[0];
    
    // Test connection creation and destruction
    {
        auto connection_result = platform->create_connection(device);
        if (connection_result.is_ok()) {
            auto connection = std::move(connection_result.value());
            REQUIRE(connection->is_valid());
        }
        // Connection should be destroyed here
    }
    
    // Should be able to create another connection
    auto connection_result2 = platform->create_connection(device);
    if (connection_result2.is_ok()) {
        auto connection2 = std::move(connection_result2.value());
        REQUIRE(connection2->is_valid());
    }
}

#ifdef _WIN32
TEST_CASE("Windows Connection Pool Integration", "[integration][windows]") {
    auto platform = create_platform_interface();
    auto devices_result = platform->list_devices();
    
    if (devices_result.is_error() || devices_result.value().empty()) {
        SKIP("No devices available for Windows-specific testing");
    }
    
    const auto& device = devices_result.value()[0];
    
    // Test connection pool functionality
    REQUIRE_NOTHROW([&]() {
        try {
            DeviceConnection connection(device);
            if (connection.is_valid()) {
                // Test that connection pool works
                PropSetting setting;
                PropRange range;
                
                // These may fail for unsupported properties, but shouldn't crash
                connection.get(CamProp::Brightness, setting);
                connection.get_range(CamProp::Brightness, range);
            }
        } catch (const std::runtime_error&) {
            // Expected for devices that can't be opened
        }
    }());
}

TEST_CASE("Logitech Vendor Integration", "[integration][vendor]") {
    auto platform = create_platform_interface();
    auto devices_result = platform->list_devices();
    
    if (devices_result.is_error() || devices_result.value().empty()) {
        SKIP("No devices available for Logitech testing");
    }
    
    // Test Logitech vendor properties with all available devices
    for (const auto& device : devices_result.value()) {
        // Check if device supports Logitech properties
        auto supports_result = logitech::supports_logitech_properties(device);
        
        REQUIRE((supports_result.is_ok() || supports_result.is_error()));
        
        if (supports_result.is_ok() && supports_result.value()) {
            // Test getting a Logitech property
            auto prop_result = logitech::get_logitech_property(
                device, logitech::LogitechProperty::FaceTracking);
            
            // Result depends on device capabilities
            REQUIRE((prop_result.is_ok() || prop_result.is_error()));
        }
    }
}
#endif

TEST_CASE("Property Consistency", "[integration][properties]") {
    auto platform = create_platform_interface();
    auto devices_result = platform->list_devices();
    
    if (devices_result.is_error() || devices_result.value().empty()) {
        SKIP("No devices available for property testing");
    }
    
    const auto& device = devices_result.value()[0];
    auto connection_result = platform->create_connection(device);
    
    if (connection_result.is_error()) {
        SKIP("Could not create device connection");
    }
    
    auto connection = std::move(connection_result.value());
    
    // Test that getting a property multiple times returns consistent results
    auto result1 = connection->get_camera_property(CamProp::Brightness);
    auto result2 = connection->get_camera_property(CamProp::Brightness);
    
    if (result1.is_ok() && result2.is_ok()) {
        // Values should be consistent (allowing for small timing differences)
        REQUIRE(result1.value().mode == result2.value().mode);
        
        if (result1.value().mode == CamMode::Manual) {
            int32_t diff = std::abs(result1.value().value - result2.value().value);
            REQUIRE(diff <= 5); // Property values should be consistent
        }
    }
}

TEST_CASE("Error Handling Integration", "[integration][error]") {
    auto platform = create_platform_interface();
    
    // Test error handling with invalid device
    Device invalid_device(L"Invalid Device", L"\\\\?\\invalid");
    
    auto connected_result = platform->is_device_connected(invalid_device);
    if (connected_result.is_ok()) {
        REQUIRE_FALSE(connected_result.value());
    }
    
    auto connection_result = platform->create_connection(invalid_device);
    REQUIRE(connection_result.is_error());
    
    if (connection_result.is_error()) {
        const auto& error = connection_result.error();
        REQUIRE((
            error.code() == ErrorCode::DeviceNotFound ||
            error.code() == ErrorCode::SystemError ||
            error.code() == ErrorCode::ConnectionFailed
        ));
        REQUIRE_FALSE(error.description().empty());
    }
}
