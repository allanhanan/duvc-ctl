#pragma once

/**
 * @file camera.h
 * @brief RAII camera handle for simplified device management
 */

#include <duvc-ctl/core/types.h>
#include <duvc-ctl/core/result.h>
#include <memory>

namespace duvc {

// Forward declaration
class DeviceConnection;

/**
 * @brief RAII camera handle for simplified device management
 * 
 * This class provides a high-level interface for camera control,
 * automatically managing device connections and providing a clean API.
 */
class Camera {
public:
    /**
     * @brief Create camera handle for device
     * @param device Device to connect to
     */
    explicit Camera(const Device& device);
    
    /**
     * @brief Create camera handle by device index
     * @param device_index Index from list_devices()
     */
    explicit Camera(int device_index);
    
    /// Destructor - automatically releases device connection
    ~Camera();
    
    // Non-copyable but movable
    Camera(const Camera&) = delete;
    Camera& operator=(const Camera&) = delete;
    Camera(Camera&&) noexcept;
    Camera& operator=(Camera&&) noexcept;
    
    /**
     * @brief Check if camera is valid and connected
     * @return true if camera can be used
     */
    bool is_valid() const;
    
    /**
     * @brief Get the underlying device information
     * @return Device structure
     */
    const Device& device() const { return device_; }
    
    /**
     * @brief Get camera property value
     * @param prop Camera property to query
     * @return Result containing property setting or error
     */
    Result<PropSetting> get(CamProp prop);
    
    /**
     * @brief Set camera property value
     * @param prop Camera property to set
     * @param setting New property setting
     * @return Result indicating success or error
     */
    Result<void> set(CamProp prop, const PropSetting& setting);
    
    /**
     * @brief Get camera property range
     * @param prop Camera property to query
     * @return Result containing property range or error
     */
    Result<PropRange> get_range(CamProp prop);
    
    /**
     * @brief Get video processing property value
     * @param prop Video property to query
     * @return Result containing property setting or error
     */
    Result<PropSetting> get(VidProp prop);
    
    /**
     * @brief Set video processing property value
     * @param prop Video property to set
     * @param setting New property setting
     * @return Result indicating success or error
     */
    Result<void> set(VidProp prop, const PropSetting& setting);
    
    /**
     * @brief Get video processing property range
     * @param prop Video property to query
     * @return Result containing property range or error
     */
    Result<PropRange> get_range(VidProp prop);
    
private:
    Device device_;
    mutable std::unique_ptr<DeviceConnection> connection_;
    
    /// Get or create device connection
    DeviceConnection* get_connection() const;
};

/**
 * @brief Create camera from device index
 * @param device_index Index from list_devices()
 * @return Result containing Camera or error
 */
Result<Camera> open_camera(int device_index);

/**
 * @brief Create camera from device
 * @param device Device to connect to
 * @return Result containing Camera or error
 */
Result<Camera> open_camera(const Device& device);

} // namespace duvc
