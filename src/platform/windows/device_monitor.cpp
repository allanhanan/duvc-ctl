/**
 * @file device_monitor.cpp
 * @brief Windows device hotplug detection implementation
 */

#ifdef _WIN32

// clang-format off
#include <windows.h>
#include <dbt.h>
// clang-format on
#include <dshow.h>
#include <duvc-ctl/core/device.h>
#include <duvc-ctl/detail/com_helpers.h>
#include <duvc-ctl/utils/logging.h>

namespace duvc {

// Global state for device monitoring (declared in device.h)
extern DeviceChangeCallback g_device_callback;
extern HWND g_notification_window;
extern HDEVNOTIFY g_device_notify;

/**
 * @brief Window procedure for handling device change notifications
 * @param hwnd Window handle
 * @param msg Message type
 * @param wParam Message parameter
 * @param lParam Message parameter
 * @return Message result
 */
static LRESULT CALLBACK device_notification_wndproc(HWND hwnd, UINT msg,
                                                    WPARAM wParam,
                                                    LPARAM lParam) {
  if (msg == WM_DEVICECHANGE && g_device_callback) {
    DUVC_LOG_DEBUG("Received device change notification");

    if (wParam == DBT_DEVICEARRIVAL || wParam == DBT_DEVICEREMOVECOMPLETE) {
      PDEV_BROADCAST_HDR hdr = reinterpret_cast<PDEV_BROADCAST_HDR>(lParam);

      if (hdr && hdr->dbch_devicetype == DBT_DEVTYP_DEVICEINTERFACE) {
        PDEV_BROADCAST_DEVICEINTERFACE dev_iface =
            reinterpret_cast<PDEV_BROADCAST_DEVICEINTERFACE>(lParam);

        bool device_added = (wParam == DBT_DEVICEARRIVAL);
        std::wstring device_path = dev_iface->dbcc_name;

        DUVC_LOG_INFO(std::string("Device ") +
                      (device_added ? "added: " : "removed: ") +
                      std::string(device_path.begin(), device_path.end()));

        // Call user callback
        try {
          g_device_callback(device_added, device_path);
        } catch (const std::exception &e) {
          DUVC_LOG_ERROR("Exception in device change callback: " +
                         std::string(e.what()));
        } catch (...) {
          DUVC_LOG_ERROR("Unknown exception in device change callback");
        }
      }
    }
  }

  return DefWindowProc(hwnd, msg, wParam, lParam);
}

/**
 * @brief Register window class for device notifications
 * @return true if successful
 */
static bool register_notification_window_class() {
  WNDCLASSW wc = {};
  wc.lpfnWndProc = device_notification_wndproc;
  wc.hInstance = GetModuleHandle(nullptr);
  wc.lpszClassName = L"DuvcDeviceNotificationWindow";

  ATOM result = RegisterClassW(&wc);
  if (result == 0) {
    DWORD error = GetLastError();
    if (error != ERROR_CLASS_ALREADY_EXISTS) {
      DUVC_LOG_ERROR("Failed to register window class: " +
                     std::to_string(error));
      return false;
    }
  }

  return true;
}

/**
 * @brief Create invisible window for receiving device notifications
 * @return Window handle or nullptr if failed
 */
static HWND create_notification_window() {
  if (!register_notification_window_class()) {
    return nullptr;
  }

  HWND hwnd = CreateWindowW(L"DuvcDeviceNotificationWindow", // Class name
                            L"duvc-ctl Device Monitor",      // Window title
                            0,                               // Style
                            0, 0, 0, 0,   // Position and size (hidden)
                            HWND_MESSAGE, // Message-only window
                            nullptr,      // Menu
                            GetModuleHandle(nullptr), // Instance
                            nullptr                   // Creation parameter
  );

  if (!hwnd) {
    DUVC_LOG_ERROR("Failed to create notification window: " +
                   std::to_string(GetLastError()));
  }

  return hwnd;
}

/**
 * @brief Register for device interface notifications
 * @param hwnd Window to receive notifications
 * @return Device notification handle or nullptr if failed
 */
static HDEVNOTIFY register_device_notifications(HWND hwnd) {
  // Register for video input device interface notifications
  DEV_BROADCAST_DEVICEINTERFACE notification_filter = {};
  notification_filter.dbcc_size = sizeof(notification_filter);
  notification_filter.dbcc_devicetype = DBT_DEVTYP_DEVICEINTERFACE;
  notification_filter.dbcc_classguid = CLSID_VideoInputDeviceCategory;

  HDEVNOTIFY handle = RegisterDeviceNotification(hwnd, &notification_filter,
                                                 DEVICE_NOTIFY_WINDOW_HANDLE);

  if (!handle) {
    DUVC_LOG_ERROR("Failed to register device notifications: " +
                   std::to_string(GetLastError()));
  } else {
    DUVC_LOG_INFO("Successfully registered for device notifications");
  }

  return handle;
}

void register_device_change_callback(DeviceChangeCallback callback) {
  // Don't register multiple times
  if (g_notification_window) {
    DUVC_LOG_WARNING("Device change callback already registered");
    return;
  }

  g_device_callback = callback;

  // Create invisible window for receiving notifications
  g_notification_window = create_notification_window();
  if (!g_notification_window) {
    g_device_callback = nullptr;
    return;
  }

  // Register for device interface notifications
  g_device_notify = register_device_notifications(g_notification_window);
  if (!g_device_notify) {
    DestroyWindow(g_notification_window);
    g_notification_window = nullptr;
    g_device_callback = nullptr;
    return;
  }

  DUVC_LOG_INFO("Device change monitoring started");
}

void unregister_device_change_callback() {
  if (g_device_notify) {
    UnregisterDeviceNotification(g_device_notify);
    g_device_notify = nullptr;
    DUVC_LOG_DEBUG("Unregistered device notifications");
  }

  if (g_notification_window) {
    DestroyWindow(g_notification_window);
    g_notification_window = nullptr;
    DUVC_LOG_DEBUG("Destroyed notification window");
  }

  g_device_callback = nullptr;
  DUVC_LOG_INFO("Device change monitoring stopped");
}

} // namespace duvc

#endif // _WIN32
