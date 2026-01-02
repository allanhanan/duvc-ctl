#pragma once

/**
 * @file directshow_impl.h
 * @brief DirectShow implementation details (internal use only)
 *
 * @internal This header contains implementation details and should not be used
 * directly.
 */

#ifdef _WIN32

#include <dshow.h>
#include <duvc-ctl/core/types.h>
#include <duvc-ctl/detail/com_helpers.h>
#include <duvc-ctl/platform/interface.h>
#include <memory>
#include <vector>

namespace duvc::detail {

/**
 * @brief DirectShow property mapping utilities
 *
 * @internal Internal utilities for mapping between duvc enums and DirectShow
 * constants.
 */
class DirectShowMapper {
public:
  /**
   * @brief Map camera property to DirectShow constant
   * @param prop Camera property
   * @return DirectShow property constant or -1 if unsupported
   */
  static long map_camera_property(CamProp prop);

  /**
   * @brief Map video property to DirectShow constant
   * @param prop Video property
   * @return DirectShow property constant or -1 if unsupported
   */
  static long map_video_property(VidProp prop);

  /**
   * @brief Map camera mode to DirectShow flags
   * @param mode Camera mode
   * @param is_camera_control true for IAMCameraControl, false for
   * IAMVideoProcAmp
   * @return DirectShow flags
   */
  static long map_camera_mode_to_flags(CamMode mode, bool is_camera_control);

  /**
   * @brief Map DirectShow flags to camera mode
   * @param flags DirectShow flags
   * @param is_camera_control true for IAMCameraControl, false for
   * IAMVideoProcAmp
   * @return Camera mode
   */
  static CamMode map_flags_to_camera_mode(long flags, bool is_camera_control);
};

/**
 * @brief DirectShow device enumerator wrapper
 *
 * @internal Internal wrapper for DirectShow device enumeration.
 */
class DirectShowEnumerator {
public:
  /// Constructor - initializes COM and creates enumerator
  DirectShowEnumerator();

  /// Destructor
  ~DirectShowEnumerator();

  /**
   * @brief Enumerate video input devices
   * @return Vector of detected devices
   */
  std::vector<Device> enumerate_devices();

  /**
   * @brief Check if specific device is available
   * @param device Device to check
   * @return true if device is enumerated
   */
  bool is_device_available(const Device &device);

  /// Read device properties from moniker
  Device read_device_info(IMoniker *moniker);

private:
  com_apartment com_;
  
public:
  com_ptr<ICreateDevEnum> dev_enum_;
};

/**
 * @brief DirectShow device filter wrapper
 *
 * @internal Internal wrapper for DirectShow device filters.
 */
class DirectShowFilter {
public:
  /**
   * @brief Create filter for device
   * @param device Device to create filter for
   */
  explicit DirectShowFilter(const Device &device);

  /// Destructor
  ~DirectShowFilter();

  /**
   * @brief Check if filter is valid
   * @return true if filter is valid
   */
  bool is_valid() const;

  /**
   * @brief Get camera control interface
   * @return COM pointer to IAMCameraControl (may be null)
   */
  com_ptr<IAMCameraControl> get_camera_control();

  /**
   * @brief Get video proc amp interface
   * @return COM pointer to IAMVideoProcAmp (may be null)
   */
  com_ptr<IAMVideoProcAmp> get_video_proc_amp();

  /**
   * @brief Get property set interface
   * @return COM pointer to IKsPropertySet (may be null)
   */
  com_ptr<IKsPropertySet> get_property_set();

  // Returns the internal IBaseFilter COM pointer (com_ptr<IBaseFilter>)
  com_ptr<IBaseFilter> extract() { return std::move(filter_); }

private:
  com_apartment com_;
  com_ptr<IBaseFilter> filter_;

  /// Create filter from device information
  com_ptr<IBaseFilter> create_filter(const Device &device);
};

/**
 * @brief Forward Declaration for DirectShow Device Connection
 */
class DirectShowDeviceConnection;

/**
 * @brief Create a DirectShow device connection
 * @param device Device to create connection for
 * @return Unique pointer to IDeviceConnection interface
 */
std::unique_ptr<IDeviceConnection>
create_directshow_connection(const Device &device);

// Forward declaration for Device (in parent namespace)
namespace duvc { class Device; }

/**
 * @brief Open IBaseFilter from Device by enumerating and matching
 * @param dev Device to find and bind
 * @return com_ptr to IBaseFilter (refcount +1) or empty on failure
 */
[[nodiscard]] com_ptr<IBaseFilter> open_device_filter(const duvc::Device& dev); 

} // namespace duvc::detail

#endif // _WIN32
