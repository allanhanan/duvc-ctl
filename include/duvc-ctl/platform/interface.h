#pragma once

/**
 * @file interface.h
 * @brief Abstract platform interface for camera control
 */

#include <duvc-ctl/core/result.h>
#include <duvc-ctl/core/types.h>
#include <memory>
#include <vector>

namespace duvc {

/**
 * @brief Abstract interface for platform-specific camera operations
 */
class IPlatformInterface {
public:
  virtual ~IPlatformInterface() = default;

  /**
   * @brief Enumerate available devices
   * @return Result containing device list or error
   */
  virtual Result<std::vector<Device>> list_devices() = 0;

  /**
   * @brief Check if device is connected
   * @param device Device to check
   * @return Result containing connection status or error
   */
  virtual Result<bool> is_device_connected(const Device &device) = 0;

  /**
   * @brief Create device connection
   * @param device Device to connect to
   * @return Result containing connection handle or error
   */
  virtual Result<std::unique_ptr<class IDeviceConnection>>
  create_connection(const Device &device) = 0;
};

/**
 * @brief Abstract interface for device-specific operations
 */
class IDeviceConnection {
public:
  virtual ~IDeviceConnection() = default;

  /**
   * @brief Check if connection is valid
   * @return true if connection is active
   */
  virtual bool is_valid() const = 0;

  /**
   * @brief Get camera property value
   * @param prop Camera property
   * @return Result containing property setting or error
   */
  virtual Result<PropSetting> get_camera_property(CamProp prop) = 0;

  /**
   * @brief Set camera property value
   * @param prop Camera property
   * @param setting New property setting
   * @return Result indicating success or error
   */
  virtual Result<void> set_camera_property(CamProp prop,
                                           const PropSetting &setting) = 0;

  /**
   * @brief Get camera property range
   * @param prop Camera property
   * @return Result containing property range or error
   */
  virtual Result<PropRange> get_camera_property_range(CamProp prop) = 0;

  /**
   * @brief Get video property value
   * @param prop Video property
   * @return Result containing property setting or error
   */
  virtual Result<PropSetting> get_video_property(VidProp prop) = 0;

  /**
   * @brief Set video property value
   * @param prop Video property
   * @param setting New property setting
   * @return Result indicating success or error
   */
  virtual Result<void> set_video_property(VidProp prop,
                                          const PropSetting &setting) = 0;

  /**
   * @brief Get video property range
   * @param prop Video property
   * @return Result containing property range or error
   */
  virtual Result<PropRange> get_video_property_range(VidProp prop) = 0;
};

/**
 * @brief Get platform-specific interface implementation
 * @return Platform interface instance
 */
std::unique_ptr<IPlatformInterface> create_platform_interface();

} // namespace duvc
