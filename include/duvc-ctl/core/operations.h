#pragma once

/**
 * @file operations.h
 * @brief Core property operations for camera control
 */

#include <duvc-ctl/core/types.h>

namespace duvc {

/**
 * @brief Get valid range for a camera control property
 * @param dev Target device
 * @param prop Camera property to query
 * @param range Output range information
 * @return true if range was retrieved successfully
 */
bool get_range(const Device& dev, CamProp prop, PropRange& range);

/**
 * @brief Get current value of a camera control property
 * @param dev Target device
 * @param prop Camera property to query
 * @param val Output current setting
 * @return true if value was retrieved successfully
 */
bool get(const Device& dev, CamProp prop, PropSetting& val);

/**
 * @brief Set value of a camera control property
 * @param dev Target device
 * @param prop Camera property to set
 * @param val New property setting
 * @return true if value was set successfully
 */
bool set(const Device& dev, CamProp prop, const PropSetting& val);

/**
 * @brief Get valid range for a video processing property
 * @param dev Target device
 * @param prop Video property to query
 * @param range Output range information
 * @return true if range was retrieved successfully
 */
bool get_range(const Device& dev, VidProp prop, PropRange& range);

/**
 * @brief Get current value of a video processing property
 * @param dev Target device
 * @param prop Video property to query
 * @param val Output current setting
 * @return true if value was retrieved successfully
 */
bool get(const Device& dev, VidProp prop, PropSetting& val);

/**
 * @brief Set value of a video processing property
 * @param dev Target device
 * @param prop Video property to set
 * @param val New property setting
 * @return true if value was set successfully
 */
bool set(const Device& dev, VidProp prop, const PropSetting& val);

} // namespace duvc
