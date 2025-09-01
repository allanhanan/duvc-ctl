#pragma once

/**
 * @file connection_pool.h
 * @brief Windows-specific device connection pooling
 */

#ifdef _WIN32

#include <duvc-ctl/core/types.h>
#include <duvc-ctl/detail/com_helpers.h>
#include <memory>

namespace duvc {

/**
 * @brief RAII wrapper for DirectShow device connections
 * 
 * Manages COM interfaces for a single device, providing
 * efficient access to camera controls without repeated
 * device enumeration and binding.
 */
class DeviceConnection {
public:
    /**
     * @brief Create connection to specified device
     * @param dev Device to connect to
     * @throws std::runtime_error if device cannot be opened
     */
    explicit DeviceConnection(const Device& dev);
    
    /// Destructor - releases all COM interfaces
    ~DeviceConnection();
    
    // Non-copyable but movable
    DeviceConnection(const DeviceConnection&) = delete;
    DeviceConnection& operator=(const DeviceConnection&) = delete;
    DeviceConnection(DeviceConnection&&) = default;
    DeviceConnection& operator=(DeviceConnection&&) = default;
    
    /**
     * @brief Get current value of a camera control property
     * @param prop Camera property to query
     * @param val Output current setting
     * @return true if value was retrieved successfully
     */
    bool get(CamProp prop, PropSetting& val);
    
    /**
     * @brief Set value of a camera control property
     * @param prop Camera property to set
     * @param val New property setting
     * @return true if value was set successfully
     */
    bool set(CamProp prop, const PropSetting& val);
    
    /**
     * @brief Get current value of a video processing property
     * @param prop Video property to query
     * @param val Output current setting
     * @return true if value was retrieved successfully
     */
    bool get(VidProp prop, PropSetting& val);
    
    /**
     * @brief Set value of a video processing property
     * @param prop Video property to set
     * @param val New property setting
     * @return true if value was set successfully
     */
    bool set(VidProp prop, const PropSetting& val);
    
    /**
     * @brief Get valid range for a camera control property
     * @param prop Camera property to query
     * @param range Output range information
     * @return true if range was retrieved successfully
     */
    bool get_range(CamProp prop, PropRange& range);
    
    /**
     * @brief Get valid range for a video processing property
     * @param prop Video property to query
     * @param range Output range information
     * @return true if range was retrieved successfully
     */
    bool get_range(VidProp prop, PropRange& range);
    
    /**
     * @brief Check if connection is valid
     * @return true if device is connected and interfaces are available
     */
    bool is_valid() const { return filter_ != nullptr; }

private:

    /// COM apartment for this connection  
    std::unique_ptr<duvc::detail::com_apartment> com_;
    
    /// DirectShow filter interface (stored as void* to avoid header dependencies)
    void* filter_;
    
    /// Camera control interface
    void* cam_ctrl_;
    
    /// Video processing interface
    void* vid_proc_;
};

/**
 * @brief Get cached connection for device (internal use)
 * @param dev Device to get connection for
 * @return Pointer to cached connection or nullptr if unavailable
 * 
 * @internal This function is used internally by the core operations.
 * Users should not call this directly.
 */
DeviceConnection* get_cached_connection(const Device& dev);

/**
 * @brief Release cached connection for device (internal use)
 * @param dev Device to release connection for
 * 
 * @internal This function is used internally for cleanup.
 * Users should not call this directly.
 */
void release_cached_connection(const Device& dev);

} // namespace duvc

#endif // _WIN32
