/**
 * @file operations.cpp
 * @brief Core property operations implementation
 */

#include <duvc-ctl/core/operations.h>
#include <duvc-ctl/platform/windows/connection_pool.h>

namespace duvc {

bool get_range(const Device& dev, CamProp prop, PropRange& range) {
#ifdef _WIN32
    DeviceConnection conn(dev);
    return conn.is_valid() ? conn.get_range(prop, range) : false;
#else
    (void)dev; (void)prop; (void)range;
    return false;
#endif
}

bool get(const Device& dev, CamProp prop, PropSetting& val) {
#ifdef _WIN32
    DeviceConnection conn(dev);
    return conn.is_valid() ? conn.get(prop, val) : false;
#else
    (void)dev; (void)prop; (void)val;
    return false;
#endif
}

bool set(const Device& dev, CamProp prop, const PropSetting& val) {
#ifdef _WIN32
    DeviceConnection conn(dev);
    return conn.is_valid() ? conn.set(prop, val) : false;
#else
    (void)dev; (void)prop; (void)val;
    return false;
#endif
}

bool get_range(const Device& dev, VidProp prop, PropRange& range) {
#ifdef _WIN32
    DeviceConnection conn(dev);
    return conn.is_valid() ? conn.get_range(prop, range) : false;
#else
    (void)dev; (void)prop; (void)range;
    return false;
#endif
}

bool get(const Device& dev, VidProp prop, PropSetting& val) {
#ifdef _WIN32
    DeviceConnection conn(dev);
    return conn.is_valid() ? conn.get(prop, val) : false;
#else
    (void)dev; (void)prop; (void)val;
    return false;
#endif
}

bool set(const Device& dev, VidProp prop, const PropSetting& val) {
#ifdef _WIN32
    DeviceConnection conn(dev);
    return conn.is_valid() ? conn.set(prop, val) : false;
#else
    (void)dev; (void)prop; (void)val;
    return false;
#endif
}

} // namespace duvc
