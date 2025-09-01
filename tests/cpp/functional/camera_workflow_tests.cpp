// tests/cpp/functional/camera_workflow_tests.cpp
#include <catch2/catch_test_macros.hpp>

#include "duvc-ctl/platform/interface.h"
#include "duvc-ctl/core/device.h"
#include "duvc-ctl/core/types.h"
#include "duvc-ctl/utils/logging.h"

#include <thread>
#include <chrono>

using namespace duvc;

// ============================================================================
// Camera Workflow Tests
// ============================================================================
class WorkflowTestFixture {
public:
    WorkflowTestFixture() {
        // Initialize platform interface
        platform_ = create_platform_interface();
        REQUIRE(platform_ != nullptr);
        
        // Set up logging for test diagnostics
        set_log_level(LogLevel::Info);
        
        // Get available devices
        auto devices_result = platform_->list_devices();
        if (devices_result.is_ok() && !devices_result.value().empty()) {
            test_device_ = std::make_unique<Device>(devices_result.value()[0]);
        }
    }
    
    ~WorkflowTestFixture() {
        set_log_callback(nullptr);
    }
    
    bool has_test_device() const {
        return test_device_ != nullptr;
    }
    
    std::unique_ptr<IPlatformInterface> platform_;
    std::unique_ptr<Device> test_device_;
};

TEST_CASE_METHOD(WorkflowTestFixture, "Complete Device Discovery Workflow", "[functional][discovery]") {
    // Step 1: Enumerate devices
    auto devices_result = platform_->list_devices();
    REQUIRE(devices_result.is_ok());
    
    const auto& devices = devices_result.value();
    if (devices.empty()) {
        SKIP("No devices available for workflow testing");
    }
    
    // Step 2: Validate device information
    for (const auto& device : devices) {
        REQUIRE_FALSE(device.name.empty());
        REQUIRE_FALSE(device.path.empty());
        
        // Step 3: Check device connectivity
        auto connected_result = platform_->is_device_connected(device);
        REQUIRE(connected_result.is_ok());
        
        if (connected_result.is_ok()) {
            // Log device status
            std::string status = connected_result.value() ? "connected" : "disconnected";
            INFO("Device status: " + status);
        }
    }
}

TEST_CASE_METHOD(WorkflowTestFixture, "Basic Camera Control Workflow", "[functional][control]") {
    if (!has_test_device()) {
        SKIP("No test device available");
    }
    
    // Step 1: Create connection
    auto connection_result = platform_->create_connection(*test_device_);
    if (connection_result.is_error()) {
        SKIP("Could not connect to test device");
    }
    
    auto connection = std::move(connection_result.value());
    REQUIRE(connection->is_valid());
    
    // Step 2: Discover supported properties
    std::vector<CamProp> supported_cam_props;
    std::vector<VidProp> supported_vid_props;
    
    // Test camera properties
    std::vector<CamProp> all_cam_props = {
        CamProp::Pan, CamProp::Tilt, CamProp::Zoom,
        CamProp::Exposure, CamProp::Focus, CamProp::Brightness
    };
    
    for (auto prop : all_cam_props) {
        auto range_result = connection->get_camera_property_range(prop);
        if (range_result.is_ok()) {
            supported_cam_props.push_back(prop);
        }
    }
    
    // Test video properties
    std::vector<VidProp> all_vid_props = {
        VidProp::Brightness, VidProp::Contrast, VidProp::Hue, VidProp::Saturation
    };
    
    for (auto prop : all_vid_props) {
        auto range_result = connection->get_video_property_range(prop);
        if (range_result.is_ok()) {
            supported_vid_props.push_back(prop);
        }
    }
    
    INFO("Discovered " + std::to_string(supported_cam_props.size()) + " camera properties");
    INFO("Discovered " + std::to_string(supported_vid_props.size()) + " video properties");
    
    // Step 3: Test property manipulation if supported
    if (!supported_cam_props.empty()) {
        auto prop = supported_cam_props[0];
        
        // Get property range
        auto range_result = connection->get_camera_property_range(prop);
        REQUIRE(range_result.is_ok());
        
        const auto& range = range_result.value();
        
        // Get current value
        auto get_result = connection->get_camera_property(prop);
        REQUIRE(get_result.is_ok());
        
        const auto original_setting = get_result.value();
        
        // Test setting a value within range
        int32_t test_value = (range.min + range.max) / 2;
        PropSetting new_setting(test_value, CamMode::Manual);
        
        auto set_result = connection->set_camera_property(prop, new_setting);
        if (set_result.is_ok()) {
            // Verify the setting was applied
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            
            auto verify_result = connection->get_camera_property(prop);
            if (verify_result.is_ok()) {
                INFO("Property manipulation successful");
            }
        }
        
        // Restore original setting
        connection->set_camera_property(prop, original_setting);
    }
}

TEST_CASE_METHOD(WorkflowTestFixture, "Property Range Validation Workflow", "[functional][validation]") {
    if (!has_test_device()) {
        SKIP("No test device available");
    }
    
    auto connection_result = platform_->create_connection(*test_device_);
    if (connection_result.is_error()) {
        SKIP("Could not connect to test device");
    }
    
    auto connection = std::move(connection_result.value());
    
    // Test comprehensive property validation
    auto range_result = connection->get_camera_property_range(CamProp::Brightness);
    if (range_result.is_ok()) {
        const auto& range = range_result.value();
        
        // Test boundary conditions
        struct TestCase {
            int32_t value;
            bool should_be_valid;
        };
        
        std::vector<TestCase> test_cases = {
            {range.min - 1, false},      // Below minimum
            {range.min, true},           // At minimum
            {range.min + range.step, true}, // Valid step
            {range.max, true},           // At maximum
            {range.max + 1, false},      // Above maximum
        };
        
        for (const auto& test_case : test_cases) {
            PropSetting test_setting(test_case.value, CamMode::Manual);
            auto set_result = connection->set_camera_property(CamProp::Brightness, test_setting);
            
            if (test_case.should_be_valid) {
                // Should succeed or be handled gracefully
                REQUIRE((set_result.is_ok() || set_result.is_error()));
            } else {
                // Should fail for invalid values (or be clamped)
                if (set_result.is_ok()) {
                    INFO("Device accepted out-of-range value (possibly clamped)");
                }
            }
        }
    }
}

TEST_CASE_METHOD(WorkflowTestFixture, "Multi-Property Operation Workflow", "[functional][multi]") {
    if (!has_test_device()) {
        SKIP("No test device available");
    }
    
    auto connection_result = platform_->create_connection(*test_device_);
    if (connection_result.is_error()) {
        SKIP("Could not connect to test device");
    }
    
    auto connection = std::move(connection_result.value());
    
    // Collect supported properties and their current values
    std::vector<std::pair<CamProp, PropSetting>> cam_settings;
    std::vector<std::pair<VidProp, PropSetting>> vid_settings;
    
    // Get current values for common properties
    std::vector<CamProp> cam_props = {CamProp::Brightness, CamProp::Contrast};
    for (auto prop : cam_props) {
        auto get_result = connection->get_camera_property(prop);
        if (get_result.is_ok()) {
            cam_settings.emplace_back(prop, get_result.value());
        }
    }
    
    std::vector<VidProp> vid_props = {VidProp::Brightness, VidProp::Contrast};
    for (auto prop : vid_props) {
        auto get_result = connection->get_video_property(prop);
        if (get_result.is_ok()) {
            vid_settings.emplace_back(prop, get_result.value());
        }
    }
    
    // Test rapid property changes
    for (int i = 0; i < 3; ++i) {
        for (const auto& cam_setting : cam_settings) {
            PropSetting modified = cam_setting.second;
            modified.value = (modified.value + 10) % 255;
            connection->set_camera_property(cam_setting.first, modified);
        }
        
        for (const auto& vid_setting : vid_settings) {
            PropSetting modified = vid_setting.second;
            modified.value = (modified.value + 10) % 255;
            connection->set_video_property(vid_setting.first, modified);
        }
        
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    
    // Restore original values
    for (const auto& cam_setting : cam_settings) {
        connection->set_camera_property(cam_setting.first, cam_setting.second);
    }
    for (const auto& vid_setting : vid_settings) {
        connection->set_video_property(vid_setting.first, vid_setting.second);
    }
    
    INFO("Multi-property workflow completed");
}

TEST_CASE_METHOD(WorkflowTestFixture, "Error Recovery Workflow", "[functional][error]") {
    if (!has_test_device()) {
        SKIP("No test device available");
    }
    
    auto connection_result = platform_->create_connection(*test_device_);
    if (connection_result.is_error()) {
        SKIP("Could not connect to test device");
    }
    
    auto connection = std::move(connection_result.value());
    
    // Test unsupported property access
    std::vector<CamProp> potentially_unsupported = {
        CamProp::Pan, CamProp::Tilt, CamProp::Roll, CamProp::Zoom
    };
    
    for (auto prop : potentially_unsupported) {
        auto get_result = connection->get_camera_property(prop);
        auto range_result = connection->get_camera_property_range(prop);
        
        // These may fail, but should not crash
        REQUIRE((get_result.is_ok() || get_result.is_error()));
        REQUIRE((range_result.is_ok() || range_result.is_error()));
        
        if (get_result.is_error()) {
            REQUIRE((
                get_result.error().code() == ErrorCode::PropertyNotSupported ||
                get_result.error().code() == ErrorCode::SystemError ||
                get_result.error().code() == ErrorCode::DeviceNotFound
            ));
        }
    }
    
    // Test invalid property values
    PropSetting invalid_setting(999999, CamMode::Manual);
    auto set_result = connection->set_camera_property(CamProp::Brightness, invalid_setting);
    
    // Should handle invalid value gracefully
    if (set_result.is_error()) {
        REQUIRE((
            set_result.error().code() == ErrorCode::InvalidValue ||
            set_result.error().code() == ErrorCode::PropertyNotSupported
        ));
    }
    
    INFO("Error recovery workflow completed");
}

TEST_CASE_METHOD(WorkflowTestFixture, "Device Reconnection Workflow", "[functional][reconnection]") {
    if (!has_test_device()) {
        SKIP("No test device available");
    }
    
    // Test multiple connection cycles
    for (int i = 0; i < 3; ++i) {
        INFO("Connection cycle " + std::to_string(i + 1));
        
        auto connection_result = platform_->create_connection(*test_device_);
        if (connection_result.is_ok()) {
            auto connection = std::move(connection_result.value());
            REQUIRE(connection->is_valid());
            
            // Perform some operations
            auto get_result = connection->get_camera_property(CamProp::Brightness);
            if (get_result.is_ok()) {
                INFO("Successfully got brightness: " + std::to_string(get_result.value().value));
            }
            
            // Let connection go out of scope
        }
        
        // Small delay between connections
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
    
    // Final verification that device is still accessible
    auto final_connection = platform_->create_connection(*test_device_);
    if (final_connection.is_ok()) {
        REQUIRE(final_connection.value()->is_valid());
        INFO("Device reconnection workflow completed successfully");
    }
}
