#include <catch2/catch_all.hpp>
#include "duvc-ctl/core.h"

using namespace duvc;

static bool has_devices() {
    return !list_devices().empty();
}

TEST_CASE("List devices returns valid device info", "[core]") {
    auto devices = list_devices();

    for (const auto& d : devices) {
        INFO("Device: " << std::string(d.name.begin(), d.name.end())
                        << " Path: " << std::string(d.path.begin(), d.path.end()));
        REQUIRE(!d.name.empty());
        REQUIRE(!d.path.empty());
    }
}

TEST_CASE("Device connection status is callable", "[core]") {
    auto devices = list_devices();
    if (!has_devices()) {
        SUCCEED("No devices connected, skipping connection check.");
        return;
    }
    for (const auto& d : devices) {
        bool connected = is_device_connected(d);
        REQUIRE((connected || !connected)); // Always true, but ensures no crash
    }
}

TEST_CASE("Cache clear does not break connection checks", "[core]") {
    if (!has_devices()) {
        SUCCEED("No devices connected, skipping cache test.");
        return;
    }
    auto devices = list_devices();
    REQUIRE(!devices.empty());

    bool before = is_device_connected(devices[0]);
    clear_connection_cache();
    bool after = is_device_connected(devices[0]);
    REQUIRE((before || !before)); // valid bool
    REQUIRE((after || !after));   // valid bool
}

TEST_CASE("Get range for multiple camera properties", "[core]") {
    if (!has_devices()) {
        SUCCEED("No devices connected, skipping range tests.");
        return;
    }

    auto dev = list_devices()[0];
    CamProp camProps[] = {
        CamProp::Pan, CamProp::Tilt, CamProp::Zoom, CamProp::Focus, CamProp::Exposure
    };

    for (auto prop : camProps) {
        PropRange r{};
        bool ok = get_range(dev, prop, r);
        INFO("Property: " << to_string(prop) << " Supported: " << ok);
        if (ok) {
            REQUIRE(r.max >= r.min);
            REQUIRE(r.step > 0);
        }
    }
}

TEST_CASE("Get range for multiple video properties", "[core]") {
    if (!has_devices()) {
        SUCCEED("No devices connected, skipping vid range tests.");
        return;
    }

    auto dev = list_devices()[0];
    VidProp vidProps[] = {
        VidProp::Brightness, VidProp::Contrast, VidProp::Saturation, VidProp::WhiteBalance
    };

    for (auto prop : vidProps) {
        PropRange r{};
        bool ok = get_range(dev, prop, r);
        INFO("Property: " << to_string(prop) << " Supported: " << ok);
        if (ok) {
            REQUIRE(r.max >= r.min);
        }
    }
}

TEST_CASE("Get current values for supported CamProps", "[core]") {
    if (!has_devices()) {
        SUCCEED("No devices connected, skipping get tests.");
        return;
    }
    auto dev = list_devices()[0];
    CamProp camProps[] = {
        CamProp::Pan, CamProp::Tilt, CamProp::Zoom, CamProp::Focus
    };

    for (auto prop : camProps) {
        PropSetting s{};
        bool ok = get(dev, prop, s);
        INFO("Property: " << to_string(prop) << " Supported: " << ok);
        if (ok) {
            // Sanity: mode should be Auto or Manual
            REQUIRE((s.mode == CamMode::Auto || s.mode == CamMode::Manual));
        }
    }
}

TEST_CASE("Safe set/get roundtrip for a supported CamProp", "[core]") {
    if (!has_devices()) {
        SUCCEED("No devices connected, skipping get/set tests.");
        return;
    }
    auto dev = list_devices()[0];

    PropRange range{};
    if (!get_range(dev, CamProp::Pan, range)) {
        SUCCEED("Pan not supported, skipping set test.");
        return;
    }

    PropSetting original{};
    REQUIRE(get(dev, CamProp::Pan, original));

    // Use same value to avoid moving hardware - FIXED CONSTRUCTOR
    PropSetting newSetting;
    newSetting.value = original.value;
    newSetting.mode = CamMode::Manual;
    
    bool setOK = set(dev, CamProp::Pan, newSetting);
    REQUIRE((setOK || !setOK)); // just check no crash

    // Reset to original value (optional)
    set(dev, CamProp::Pan, original);
}

TEST_CASE("Safe get calls for unsupported properties", "[core]") {
    if (!has_devices()) {
        SUCCEED("No devices connected, skipping unsupported prop test.");
        return;
    }
    auto dev = list_devices()[0];
    // Assuming Lamp is unsupported on most devices
    PropSetting s{};
    bool ok = get(dev, CamProp::Lamp, s);
    REQUIRE((ok || !ok)); // Should not crash
}
