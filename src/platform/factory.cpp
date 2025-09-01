/**
 * @file factory.cpp
 * @brief Platform detection and factory implementation
 */

#include <duvc-ctl/platform/interface.h>
#include <duvc-ctl/detail/directshow_impl.h>
#include <memory>

#ifdef _WIN32
#include <duvc-ctl/platform/windows/directshow.h>
#endif

namespace duvc {

#ifdef _WIN32

/**
 * @brief Windows DirectShow platform implementation
 */
class WindowsPlatformInterface : public IPlatformInterface {
public:
    Result<std::vector<Device>> list_devices() override {
        try {
            detail::DirectShowEnumerator enumerator;
            auto devices = enumerator.enumerate_devices();
            return Ok(std::move(devices));
        } catch (const std::exception& e) {
            return Err<std::vector<Device>>(ErrorCode::SystemError, e.what());
        }
    }
    
    Result<bool> is_device_connected(const Device& device) override {
        try {
            detail::DirectShowEnumerator enumerator;
            return Ok(enumerator.is_device_available(device));
        } catch (const std::exception& e) {
            return Err<bool>(ErrorCode::SystemError, e.what());
        }
    }
    
    Result<std::unique_ptr<IDeviceConnection>> create_connection(const Device& device) override {
        try {
            auto connection = detail::create_directshow_connection(device);
            if (!connection) {
                return Err<std::unique_ptr<IDeviceConnection>>(
                    ErrorCode::DeviceNotFound, "Failed to create device connection");
            }
            return Ok(std::move(connection));
        } catch (const std::exception& e) {
            return Err<std::unique_ptr<IDeviceConnection>>(ErrorCode::SystemError, e.what());
        }
    }
};

#endif // _WIN32

std::unique_ptr<IPlatformInterface> create_platform_interface() {
#ifdef _WIN32
    return std::make_unique<WindowsPlatformInterface>();
#else
    // Return null for unsupported platforms
    return nullptr;
#endif
}

} // namespace duvc
