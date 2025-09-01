/**
 * @file operations.cpp
 * @brief Core property operations implementation
 */

#include <duvc-ctl/core/operations.h>
#include <duvc-ctl/platform/windows/connection_pool.h>

namespace duvc {

bool get_range(const Device& dev, CamProp prop, PropRange& range) {
#ifdef _WIN32
    auto* conn = get_cached_connection(dev);
    return conn ? conn->get_range(prop, range) : false;
#else
    (void)dev; (void)prop; (void)range;
    return false;
#endif
}

bool get(const Device& dev, CamProp prop, PropSetting& val) {
#ifdef _WIN32
    auto* conn = get_cached_connection(dev);
    return conn ? conn->get(prop, val) : false;
#else
    (void)dev; (void)prop; (void)val;
    return false;
#endif
}

bool set(const Device& dev, CamProp prop, const PropSetting& val) {
#ifdef _WIN32
    auto* conn = get_cached_connection(dev);
    return conn ? conn->set(prop, val) : false;
#else
    (void)dev; (void)prop; (void)val;
    return false;
#endif
}

bool get_range(const Device& dev, VidProp prop, PropRange& range) {
#ifdef _WIN32
    auto* conn = get_cached_connection(dev);
    return conn ? conn->get_range(prop, range) : false;
#else
    (void)dev; (void)prop; (void)range;
    return false;
#endif
}

bool get(const Device& dev, VidProp prop, PropSetting& val) {
#ifdef _WIN32
    auto* conn = get_cached_connection(dev);
    return conn ? conn->get(prop, val) : false;
#else
    (void)dev; (void)prop; (void)val;
    return false;
#endif
}

bool set(const Device& dev, VidProp prop, const PropSetting& val) {
#ifdef _WIN32
    auto* conn = get_cached_connection(dev);
    return conn ? conn->set(prop, val) : false;
#else
    (void)dev; (void)prop; (void)val;
    return false;
#endif
}

void clear_connection_cache() {
#ifdef _WIN32
    // Implemented in connection_pool.cpp
    extern void clear_connection_cache_impl();
    clear_connection_cache_impl();
#endif
}

} // namespace duvc
