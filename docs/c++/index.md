# duvc-ctl C++ API Documentation

A guide to using the `duvc-ctl` C++ library/API for controlling USB Video Class (UVC) cameras on Windows.

---

Refer the Doxygen docs here!: [C++ API (Doxygen)](../../doxygen/html/index.html)

## Contents

**Getting Started**

- [1. Overview & Getting Started](sections/01_overview-getting-started.md)
    - [1.1 Introduction](sections/01_overview-getting-started.md#1-1-introduction)
    - [1.2 Installation & Setup](sections/01_overview-getting-started.md#1-2-installation-setup)
    - [1.3 Quick Start Examples](sections/01_overview-getting-started.md#1-3-quick-start-examples)

**Core Concepts**

- [2. Core API & Public Headers](sections/02_core-api-public-headers.md)
    - [2.1 Device Discovery & Management](sections/02_core-api-public-headers.md#2-1-device-discovery-management)
    - [2.2 Camera Control Class](sections/02_core-api-public-headers.md#2-2-camera-control-class)
    - [2.3 Device Capabilities](sections/02_core-api-public-headers.md#2-3-device-capabilities)
    - [2.4 Core Types & Enumerations](sections/02_core-api-public-headers.md#2-4-core-types-enumerations)
    - [2.5 Result Type & Error Handling](sections/02_core-api-public-headers.md#2-5-result-type-error-handling)
    - [2.6 Main Include Header](sections/02_core-api-public-headers.md#2-6-main-include-header)

**Utility Functions & Helpers**

- [3. Utility Functions & Helpers](sections/03_utility-functions-helpers.md)
    - [3.1 Logging System](sections/03_utility-functions-helpers.md#3-1-logging-system)
    - [3.2 String Conversion](sections/03_utility-functions-helpers.md#3-2-string-conversion)
    - [3.3 Error Decoding](sections/03_utility-functions-helpers.md#3-3-error-decoding)

**Platform Abstraction**

- [4. Platform Abstraction Layer](sections/04_platform-abstraction-layer.md)
    - [4.1 Platform Interfaces](sections/04_platform-abstraction-layer.md#4-1-platform-interfaces)

**Vendor-Specific Extensions**

- [5. Vendor-Specific Extensions](sections/05_vendor-specific-extensions.md)
    - [5.1 Logitech Extensions](sections/05_vendor-specific-extensions.md#5-1-logitech-extensions)
    - [5.2 Kernel Streaming Properties](sections/05_vendor-specific-extensions.md#5-2-kernel-streaming-properties)
    - [5.3 Vendor Property Structure](sections/05_vendor-specific-extensions.md#5-3-vendor-property-structure)

**Internal Implementation**

- [6. Internal Implementation Details](sections/06_internal-implementation-details.md)
    - [6.1 Device Connection Pool](sections/06_internal-implementation-details.md#6-1-device-connection-pool)
    - [6.2 COM Helpers](sections/06_internal-implementation-details.md#6-2-com-helpers)
    - [6.3 DirectShow Integration](sections/06_internal-implementation-details.md#6-3-directshow-integration)
    - [6.4 Windows Internals](sections/06_internal-implementation-details.md#6-4-windows-internals)
    - [6.5 Device Monitoring](sections/06_internal-implementation-details.md#6-5-device-monitoring)
    - [6.6 Factory Implementation](sections/06_internal-implementation-details.md#6-6-factory-implementation)

**Property Reference**

- [7. Property Reference Details](sections/07_property-reference-details.md)
    - [7.1 Camera Properties Complete Reference](sections/07_property-reference-details.md#7-1-camera-properties-complete-reference)
    - [7.2 Video Properties Complete Reference](sections/07_property-reference-details.md#7-2-video-properties-complete-reference)
    - [7.3 Property Range Discovery](sections/07_property-reference-details.md#7-3-property-range-discovery)
    - [7.4 Auto vs Manual Modes](sections/07_property-reference-details.md#7-4-auto-vs-manual-modes)

**Usage Patterns & Best Practices**

- [8. Usage Patterns & Best Practices](sections/08_usage-patterns-best-practices.md)
    - [8.1 Basic Usage Patterns](sections/08_usage-patterns-best-practices.md#8-1-basic-usage-patterns)
    - [8.2 Advanced Patterns](sections/08_usage-patterns-best-practices.md#8-2-advanced-patterns)
    - [8.3 Error Handling Strategies](sections/08_usage-patterns-best-practices.md#8-3-error-handling-strategies)
    - [8.4 Thread Safety Guidelines](sections/08_usage-patterns-best-practices.md#8-4-thread-safety-guidelines)
    - [8.5 Performance Optimization](sections/08_usage-patterns-best-practices.md#8-5-performance-optimization)

**Build System Integration**

- [9. Build System Integration](sections/09_build-system-integration.md)
    - [9.1 CMake Integration](sections/09_build-system-integration.md#9-1-cmake-integration)
    - [9.2 Building from Source](sections/09_build-system-integration.md#9-2-building-from-source)
    - [9.3 Package Managers](sections/09_build-system-integration.md#9-3-package-managers)

**Platform-Specific Information**

- [10. Platform-Specific Information](sections/10_platform-specific-information.md)
    - [10.1 Windows-Specific Details](sections/10_platform-specific-information.md#10-1-windows-specific-details)
    - [10.2 DirectShow Background](sections/10_platform-specific-information.md#10-2-directshow-background)
    - [10.3 UVC Camera Standards](sections/10_platform-specific-information.md#10-3-uvc-camera-standards)

**Device Support & Compatibility**

- [11. Device Support & Compatibility](sections/11_device-support-compatibility.md)
    - [11.1 Tested Devices](sections/11_device-support-compatibility.md#11-1-tested-devices)
    - [11.2 Device Capability Matrix](sections/11_device-support-compatibility.md#11-2-device-capability-matrix)
    - [11.3 Known Issues & Workarounds](sections/11_device-support-compatibility.md#11-3-known-issues-workarounds)

**Troubleshooting & Debugging**

- [12. Troubleshooting & Debugging](sections/12_troubleshooting-debugging.md)
    - [12.1 Common Issues](sections/12_troubleshooting-debugging.md#12-1-common-issues)
    - [12.2 Debugging Techniques](sections/12_troubleshooting-debugging.md#12-2-debugging-techniques)
    - [12.3 Diagnostic Tools](sections/12_troubleshooting-debugging.md#12-3-diagnostic-tools)

**Examples & Tutorials**

- [13. Examples & Tutorials](sections/13_examples-tutorials.md)
    - [13.1 Complete Examples](sections/13_examples-tutorials.md#13-1-complete-examples)
    - [13.2 Code Snippets](sections/13_examples-tutorials.md#13-2-code-snippets)

**Contributing & Extending**

- [14. Contributing & Extending](sections/14_contributing-extending.md)
    - [14.1 Architecture Overview](sections/14_contributing-extending.md#14-1-architecture-overview)
    - [14.2 Adding New Features](sections/14_contributing-extending.md#14-2-adding-new-features)
    - [14.3 Testing [INCOMPLETE]](sections/14_contributing-extending.md#14-3-testing-incomplete)

**FAQ**

- [15. FAQ](sections/15_faq.md)
    - [15.1 General Questions](sections/15_faq.md#15-1-general-questions)
    - [15.2 Technical Questions](sections/15_faq.md#15-2-technical-questions)

**Appendices**

- [16. Appendices](sections/16_appendices.md)
    - [16.1 DirectShow Property Constants](sections/16_appendices.md#16-1-directshow-property-constants)
    - [16.2 Error Code Reference](sections/16_appendices.md#16-2-error-code-reference)
    - [16.3 GUID Reference](sections/16_appendices.md#16-3-guid-reference)
    - [16.4 Glossary](sections/16_appendices.md#16-4-glossary)

## Overview
duvc-ctl is a C++ library for controlling UVC cameras on Windows through the DirectShow API. The library exposes camera properties (pan, tilt, zoom, exposure, focus) and video properties (brightness, contrast, white balance) without requiring vendor-specific drivers or SDKs.

**Supported operations:**

- Device enumeration and connection
- Camera properties: pan, tilt, roll, zoom, exposure, iris, focus, scan mode, privacy, digital zoom, backlight compensation, lamp
- Video properties: brightness, contrast, hue, saturation, sharpness, gamma, color enable, white balance, backlight compensation, gain
- Hot-plug detection and device change notifications
- Vendor-specific extensions (Logitech cameras supported)

**Requirements:**

- Windows 7 SP1 or later (Windows 10/11 recommended)
- C++17 compiler: Visual Studio 2019/2022, or MinGW-w64 with GCC 9+
- CMake 3.16 or later
- DirectShow (included with Windows)    