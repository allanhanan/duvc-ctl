/**
 * @file camera.cpp
 * @brief RAII camera handle implementation
 */

#include <duvc-ctl/core/camera.h>
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/platform/windows/connection_pool.h>

namespace duvc {

Camera::Camera(const Device& device) 
    : device_(device), connection_(nullptr) {
}

Camera::Camera(int device_index) : connection_(nullptr) {
    auto devices = list_devices();
    if (device_index >= 0 && device_index < static_cast<int>(devices.size())) {
        device_ = devices[device_index];
    }
    // Invalid index results in invalid camera (device_ will be empty)
}

Camera::~Camera() = default;

Camera::Camera(Camera&&) noexcept = default;
Camera& Camera::operator=(Camera&&) noexcept = default;

bool Camera::is_valid() const {
    return device_.is_valid() && is_device_connected(device_);
}

DeviceConnection* Camera::get_connection() const {
    if (!connection_) {
        connection_ = std::unique_ptr<DeviceConnection>(get_cached_connection(device_));
    }
    return connection_.get();
}

Result<PropSetting> Camera::get(CamProp prop) {
    auto* conn = get_connection();
    if (!conn || !conn->is_valid()) {
        return Err<PropSetting>(ErrorCode::DeviceNotFound, "Device not connected");
    }
    
    PropSetting setting;
    if (conn->get(prop, setting)) {
        return Ok(setting);
    }
    return Err<PropSetting>(ErrorCode::PropertyNotSupported, "Failed to get camera property");
}

Result<void> Camera::set(CamProp prop, const PropSetting& setting) {
    auto* conn = get_connection();
    if (!conn || !conn->is_valid()) {
        return Err<void>(ErrorCode::DeviceNotFound, "Device not connected");
    }
    
    if (conn->set(prop, setting)) {
        return Ok();
    }
    return Err<void>(ErrorCode::PropertyNotSupported, "Failed to set camera property");
}

Result<PropRange> Camera::get_range(CamProp prop) {
    auto* conn = get_connection();
    if (!conn || !conn->is_valid()) {
        return Err<PropRange>(ErrorCode::DeviceNotFound, "Device not connected");
    }
    
    PropRange range;
    if (conn->get_range(prop, range)) {
        return Ok(range);
    }
    return Err<PropRange>(ErrorCode::PropertyNotSupported, "Failed to get camera property range");
}

Result<PropSetting> Camera::get(VidProp prop) {
    auto* conn = get_connection();
    if (!conn || !conn->is_valid()) {
        return Err<PropSetting>(ErrorCode::DeviceNotFound, "Device not connected");
    }
    
    PropSetting setting;
    if (conn->get(prop, setting)) {
        return Ok(setting);
    }
    return Err<PropSetting>(ErrorCode::PropertyNotSupported, "Failed to get video property");
}

Result<void> Camera::set(VidProp prop, const PropSetting& setting) {
    auto* conn = get_connection();
    if (!conn || !conn->is_valid()) {
        return Err<void>(ErrorCode::DeviceNotFound, "Device not connected");
    }
    
    if (conn->set(prop, setting)) {
        return Ok();
    }
    return Err<void>(ErrorCode::PropertyNotSupported, "Failed to set video property");
}

Result<PropRange> Camera::get_range(VidProp prop) {
    auto* conn = get_connection();
    if (!conn || !conn->is_valid()) {
        return Err<PropRange>(ErrorCode::DeviceNotFound, "Device not connected");
    }
    
    PropRange range;
    if (conn->get_range(prop, range)) {
        return Ok(range);
    }
    return Err<PropRange>(ErrorCode::PropertyNotSupported, "Failed to get video property range");
}

Result<Camera> open_camera(int device_index) {
    auto devices = list_devices();
    if (device_index < 0 || device_index >= static_cast<int>(devices.size())) {
        return Err<Camera>(ErrorCode::DeviceNotFound, "Invalid device index");
    }
    
    return open_camera(devices[device_index]);
}

Result<Camera> open_camera(const Device& device) {
    if (!device.is_valid()) {
        return Err<Camera>(ErrorCode::InvalidArgument, "Invalid device");
    }
    
    if (!is_device_connected(device)) {
        return Err<Camera>(ErrorCode::DeviceNotFound, "Device not connected");
    }
    
    return Ok(Camera(device));
}

} // namespace duvc
