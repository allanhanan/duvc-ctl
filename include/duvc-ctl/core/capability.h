#pragma once

/**
 * @file capability.h
 * @brief Device capability detection and snapshots using Camera API
 */

#include <vector>
#include <unordered_map>
#include <memory>
#include "camera.h"
#include "result.h"
#include "types.h"

namespace duvc {

/**
 * @brief Property capability information
 */
struct PropertyCapability {
    bool supported = false; ///< Property is supported by device
    PropRange range;        ///< Valid range for property
    PropSetting current;    ///< Current property value

    /**
     * @brief Check if property supports automatic mode
     * @return true if auto mode is supported
     */
    bool supports_auto() const {
        return range.default_mode == CamMode::Auto;
    }
};

/**
 * @brief Complete device capability snapshot
 */
class DeviceCapabilities {
public:
    /**
     * @brief Create capabilities snapshot for device
     * @param device Device to analyze
     */
    explicit DeviceCapabilities(const Device& device);

    /**
     * @brief Get camera property capability
     * @param prop Camera property
     * @return Property capability info
     */
    const PropertyCapability& get_camera_capability(CamProp prop) const;

    /**
     * @brief Get video property capability
     * @param prop Video property
     * @return Property capability info
     */
    const PropertyCapability& get_video_capability(VidProp prop) const;

    /**
     * @brief Check if camera property is supported
     * @param prop Camera property
     * @return true if supported
     */
    bool supports_camera_property(CamProp prop) const;

    /**
     * @brief Check if video property is supported
     * @param prop Video property
     * @return true if supported
     */
    bool supports_video_property(VidProp prop) const;

    /**
     * @brief Get list of supported camera properties
     * @return Vector of supported camera properties
     */
    std::vector<CamProp> supported_camera_properties() const;

    /**
     * @brief Get list of supported video properties
     * @return Vector of supported video properties
     */
    std::vector<VidProp> supported_video_properties() const;

    /**
     * @brief Get the device this capability snapshot is for
     * @return Device reference
     */
    const Device& device() const { return device_; }

    /**
     * @brief Check if device is connected and accessible
     * @return true if device is accessible
     */
    bool is_device_accessible() const { return device_accessible_; }

    /**
     * @brief Refresh capability snapshot
     * @return Result indicating success or error
     */
    Result<void> refresh();

private:
    Device device_;
    bool device_accessible_;
    std::unordered_map<CamProp, PropertyCapability> camera_capabilities_;
    std::unordered_map<VidProp, PropertyCapability> video_capabilities_;

    /// Scan all properties and build capability map
    void scan_capabilities();

    /// Empty capability for unsupported properties
    static const PropertyCapability empty_capability_;
};

/**
 * @brief Create device capability snapshot
 * @param device Device to analyze
 * @return Result containing DeviceCapabilities or error
 */
Result<DeviceCapabilities> get_device_capabilities(const Device& device);

/**
 * @brief Create device capability snapshot by index
 * @param device_index Device index from list_devices()
 * @return Result containing DeviceCapabilities or error
 */
Result<DeviceCapabilities> get_device_capabilities(int device_index);

} // namespace duvc
