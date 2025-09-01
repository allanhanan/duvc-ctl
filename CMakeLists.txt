# CMakeLists.txt - Professional CMake for duvc-ctl
cmake_minimum_required(VERSION 3.16)

# ============================================================================
# Project Definition
# ============================================================================
project(duvc-ctl 
    VERSION 2.0.0
    DESCRIPTION "DirectShow UVC Camera Control Library"
    HOMEPAGE_URL "https://github.com/allanhanan/duvc-ctl"
    LANGUAGES CXX C
)

# ============================================================================
# Build Options
# ============================================================================
# Core library options
option(DUVC_BUILD_SHARED "Build shared core library" ON)
option(DUVC_BUILD_STATIC "Build static core library" ON)

# Component options
option(DUVC_BUILD_C_API "Build C API for language bindings" ON)
option(DUVC_BUILD_CLI "Build command-line interface" ON)

# Development options
option(DUVC_BUILD_TESTS "Build unit tests" OFF)
option(DUVC_BUILD_EXAMPLES "Build example programs" OFF)
option(DUVC_WARNINGS_AS_ERRORS "Treat compiler warnings as errors" OFF)

# Installation options
option(DUVC_INSTALL "Install duvc-ctl" ON)
option(DUVC_INSTALL_CMAKE_CONFIG "Install CMake config files" ${DUVC_INSTALL})

# ============================================================================
# Global Configuration
# ============================================================================
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Build type
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE "Release" CACHE STRING "Choose build type" FORCE)
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()

# Output directories
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# ============================================================================
# Helper Functions
# ============================================================================
function(duvc_set_target_properties target)
    # Compiler-specific flags
    if(CMAKE_CXX_COMPILER_ID MATCHES "MSVC")
        target_compile_options(${target} PRIVATE /W4 /permissive-)
        target_compile_definitions(${target} PRIVATE 
            UNICODE _UNICODE NOMINMAX WIN32_LEAN_AND_MEAN
        )
        if(DUVC_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE /WX)
        endif()
    elseif(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        target_compile_options(${target} PRIVATE 
            -Wall -Wextra -Wpedantic -Wcast-qual -Wformat=2
        )
        if(DUVC_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE -Werror)
        endif()
    endif()
    
    # Platform-specific libraries
    if(WIN32)
        target_link_libraries(${target} PRIVATE 
            ole32 oleaut32 strmiids psapi advapi32
        )
    endif()
endfunction()

# ============================================================================
# Source File Organization
# ============================================================================
set(DUVC_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/include)

# Core library sources (C++ only)
set(DUVC_CORE_SOURCES
    # Core functionality
    src/core/types.cpp
    src/core/device.cpp
    src/core/camera.cpp
    src/core/result.cpp
    src/core/capability.cpp
    src/core/operations.cpp
    
    # Platform abstraction
    src/platform/factory.cpp
    
    # Utilities
    src/utils/logging.cpp
    src/utils/error_decoder.cpp
    src/utils/string_conversion.cpp
    
    # Vendor extensions
    src/vendor/constants.cpp
    src/vendor/logitech.cpp
    
    # Legacy compatibility
    src/legacy/core_legacy.cpp
    src/legacy/bindings_legacy.cpp
)

# Platform-specific sources
if(WIN32)
    list(APPEND DUVC_CORE_SOURCES
        src/platform/windows/connection_pool.cpp
        src/platform/windows/device_monitor.cpp
        src/platform/windows/ks_properties.cpp
        src/detail/com_helpers.cpp
        src/detail/directshow_impl.cpp
    )
endif()

# C API sources (separate from core)
set(DUVC_C_API_SOURCES
    src/c/api.cpp
    src/c/error_handling.cpp
)

# CLI sources
set(DUVC_CLI_SOURCES
    cli/main.cpp
)

# ============================================================================
# Core C++ Library Targets
# ============================================================================
set(DUVC_CORE_TARGETS)

# Static library
if(DUVC_BUILD_STATIC)
    add_library(duvc-core-static STATIC ${DUVC_CORE_SOURCES})
    add_library(duvc::core-static ALIAS duvc-core-static)
    
    target_include_directories(duvc-core-static
        PUBLIC
            $<BUILD_INTERFACE:${DUVC_INCLUDE_DIR}>
            $<INSTALL_INTERFACE:include>
    )
    
    target_compile_features(duvc-core-static PUBLIC cxx_std_17)
    target_compile_definitions(duvc-core-static 
        PUBLIC DUVC_STATIC_DEFINE
        PRIVATE DUVC_CORE_BUILDING
    )
    
    duvc_set_target_properties(duvc-core-static)
    
    set_target_properties(duvc-core-static PROPERTIES
        OUTPUT_NAME duvc-core
        EXPORT_NAME core-static
        VERSION ${PROJECT_VERSION}
        SOVERSION ${PROJECT_VERSION_MAJOR}
    )
    
    list(APPEND DUVC_CORE_TARGETS duvc-core-static)
endif()

# Shared library
if(DUVC_BUILD_SHARED)
    add_library(duvc-core-shared SHARED ${DUVC_CORE_SOURCES})
    add_library(duvc::core-shared ALIAS duvc-core-shared)
    
    target_include_directories(duvc-core-shared
        PUBLIC
            $<BUILD_INTERFACE:${DUVC_INCLUDE_DIR}>
            $<INSTALL_INTERFACE:include>
    )
    
    target_compile_features(duvc-core-shared PUBLIC cxx_std_17)
    target_compile_definitions(duvc-core-shared 
        PUBLIC DUVC_SHARED_DEFINE
        PRIVATE DUVC_CORE_BUILDING DUVC_CORE_DLL_EXPORT
    )
    
    duvc_set_target_properties(duvc-core-shared)
    
    set_target_properties(duvc-core-shared PROPERTIES
        OUTPUT_NAME duvc-core
        EXPORT_NAME core-shared
        VERSION ${PROJECT_VERSION}
        SOVERSION ${PROJECT_VERSION_MAJOR}
        WINDOWS_EXPORT_ALL_SYMBOLS ON
    )
    
    list(APPEND DUVC_CORE_TARGETS duvc-core-shared)
endif()

# Default core alias (prefers shared)
if(DUVC_BUILD_SHARED)
    add_library(duvc::core ALIAS duvc-core-shared)
    set(DUVC_DEFAULT_CORE_TARGET duvc-core-shared)
elseif(DUVC_BUILD_STATIC)
    add_library(duvc::core ALIAS duvc-core-static)
    set(DUVC_DEFAULT_CORE_TARGET duvc-core-static)
endif()

# ============================================================================
# C API Library Target
# ============================================================================
if(DUVC_BUILD_C_API AND DUVC_DEFAULT_CORE_TARGET)
    add_library(duvc-c-api SHARED ${DUVC_C_API_SOURCES})
    add_library(duvc::c-api ALIAS duvc-c-api)
    
    target_include_directories(duvc-c-api
        PUBLIC
            $<BUILD_INTERFACE:${DUVC_INCLUDE_DIR}>
            $<INSTALL_INTERFACE:include>
    )
    
    target_link_libraries(duvc-c-api PUBLIC ${DUVC_DEFAULT_CORE_TARGET})
    
    target_compile_definitions(duvc-c-api 
        PRIVATE DUVC_C_API_BUILDING
        PUBLIC DUVC_C_API_SHARED
    )
    
    duvc_set_target_properties(duvc-c-api)
    
    set_target_properties(duvc-c-api PROPERTIES
        OUTPUT_NAME duvc-c
        EXPORT_NAME c-api
        VERSION ${PROJECT_VERSION}
        SOVERSION ${PROJECT_VERSION_MAJOR}
        WINDOWS_EXPORT_ALL_SYMBOLS ON
        C_STANDARD 99
        C_STANDARD_REQUIRED ON
    )
    
    list(APPEND DUVC_CORE_TARGETS duvc-c-api)
endif()

# ============================================================================
# CLI Tool Target
# ============================================================================
if(DUVC_BUILD_CLI AND DUVC_DEFAULT_CORE_TARGET)
    add_executable(duvc-cli ${DUVC_CLI_SOURCES})
    add_executable(duvc::cli ALIAS duvc-cli)
    
    target_include_directories(duvc-cli PRIVATE
        ${DUVC_INCLUDE_DIR}
        cli/include
    )
    
    target_link_libraries(duvc-cli PRIVATE ${DUVC_DEFAULT_CORE_TARGET})
    
    duvc_set_target_properties(duvc-cli)
    
    set_target_properties(duvc-cli PROPERTIES
        OUTPUT_NAME duvc-cli
        EXPORT_NAME cli
    )
    
    # MinGW console subsystem fix
    if(MINGW)
        target_link_options(duvc-cli PRIVATE 
            -mconsole -Wl,--subsystem,console
        )
    endif()
    
    list(APPEND DUVC_CORE_TARGETS duvc-cli)
endif()

# ============================================================================
# Tests and Examples
# ============================================================================
if(DUVC_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

if(DUVC_BUILD_EXAMPLES)
    add_subdirectory(examples)
endif()

# ============================================================================
# Installation
# ============================================================================
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

if(DUVC_INSTALL AND DUVC_CORE_TARGETS)
    # Install targets
    install(TARGETS ${DUVC_CORE_TARGETS}
        EXPORT duvc-targets
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
            COMPONENT Development
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
            COMPONENT Runtime
            NAMELINK_COMPONENT Development
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
            COMPONENT Runtime
    )
    
    # Install headers
    install(DIRECTORY ${DUVC_INCLUDE_DIR}/
        DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
        COMPONENT Development
        FILES_MATCHING 
            PATTERN "*.h" 
            PATTERN "*.hpp"
    )
    
    # Install CMake config files
    if(DUVC_INSTALL_CMAKE_CONFIG)
        set(CONFIG_INSTALL_DIR ${CMAKE_INSTALL_LIBDIR}/cmake/duvc)
        
        # Generate version file
        write_basic_package_version_file(
            "${CMAKE_CURRENT_BINARY_DIR}/duvc-config-version.cmake"
            VERSION ${PROJECT_VERSION}
            COMPATIBILITY SameMajorVersion
        )
        
        # Generate config file
        configure_package_config_file(
            "${CMAKE_CURRENT_SOURCE_DIR}/cmake/duvc-config.cmake.in"
            "${CMAKE_CURRENT_BINARY_DIR}/duvc-config.cmake"
            INSTALL_DESTINATION ${CONFIG_INSTALL_DIR}
        )
        
        # Install config files
        install(FILES
            "${CMAKE_CURRENT_BINARY_DIR}/duvc-config.cmake"
            "${CMAKE_CURRENT_BINARY_DIR}/duvc-config-version.cmake"
            DESTINATION ${CONFIG_INSTALL_DIR}
            COMPONENT Development
        )
        
        # Install targets file
        install(EXPORT duvc-targets
            FILE duvc-targets.cmake
            NAMESPACE duvc::
            DESTINATION ${CONFIG_INSTALL_DIR}
            COMPONENT Development
        )
    endif()
    
    # Generate pkg-config file
    configure_file(
        "${CMAKE_CURRENT_SOURCE_DIR}/cmake/duvc.pc.in"
        "${CMAKE_CURRENT_BINARY_DIR}/duvc.pc"
        @ONLY
    )
    install(FILES "${CMAKE_CURRENT_BINARY_DIR}/duvc.pc"
        DESTINATION ${CMAKE_INSTALL_LIBDIR}/pkgconfig
        COMPONENT Development
    )
endif()

# ============================================================================
# Python Bindings (Optional)
# ============================================================================
option(DUVC_BUILD_PYTHON "Build Python bindings" OFF)

if(DUVC_BUILD_PYTHON AND DUVC_DEFAULT_CORE_TARGET)
    # Locate Python and pybind11
    find_package(Python COMPONENTS Interpreter Development REQUIRED)
    
    option(DUVC_USE_SYSTEM_PYBIND11 "Use system-installed pybind11" OFF)
    
    if(DUVC_USE_SYSTEM_PYBIND11)
        find_package(pybind11 CONFIG REQUIRED)
    else()
        include(FetchContent)
        FetchContent_Declare(
            pybind11
            GIT_REPOSITORY https://github.com/pybind/pybind11.git
            GIT_TAG v2.11.1
        )
        FetchContent_MakeAvailable(pybind11)
    endif()
    
    # Create the Python module
    pybind11_add_module(_duvc_ctl bindings/python/pybind_module.cpp)
    
    # Set output properties
    set_target_properties(_duvc_ctl PROPERTIES 
        OUTPUT_NAME "_duvc_ctl"
        CXX_VISIBILITY_PRESET "hidden"
        VISIBILITY_INLINES_HIDDEN YES
    )
    
    # Include directories
    target_include_directories(_duvc_ctl PRIVATE 
        ${DUVC_INCLUDE_DIR}
    )
    
    # Link with the core library (now it exists!)
    target_link_libraries(_duvc_ctl PRIVATE ${DUVC_DEFAULT_CORE_TARGET})
    
    # Apply compiler settings
    duvc_set_target_properties(_duvc_ctl)
    
    # Installation
    if(SKBUILD)
        install(TARGETS _duvc_ctl DESTINATION duvc_ctl)
    else()
        install(TARGETS _duvc_ctl DESTINATION python/duvc_ctl)
    endif()
    
    list(APPEND DUVC_CORE_TARGETS _duvc_ctl)
endif()


# ============================================================================
# Summary
# ============================================================================
if(NOT CMAKE_SCRIPT_MODE_FILE)
    message(STATUS "")
    message(STATUS "duvc-ctl v${PROJECT_VERSION} Configuration Summary:")
    message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
    message(STATUS "  C++ standard: ${CMAKE_CXX_STANDARD}")
    message(STATUS "")
    message(STATUS "Core Library:")
    message(STATUS "  Static library: ${DUVC_BUILD_STATIC}")
    message(STATUS "  Shared library: ${DUVC_BUILD_SHARED}")
    message(STATUS "")
    message(STATUS "Components:")
    message(STATUS "  C API library: ${DUVC_BUILD_C_API}")
    message(STATUS "  CLI tool: ${DUVC_BUILD_CLI}")
    message(STATUS "  Tests: ${DUVC_BUILD_TESTS}")
    message(STATUS "  Examples: ${DUVC_BUILD_EXAMPLES}")
    message(STATUS "")
    message(STATUS "Installation:")
    message(STATUS "  Install: ${DUVC_INSTALL}")
    message(STATUS "  Install prefix: ${CMAKE_INSTALL_PREFIX}")
    message(STATUS "")
endif()
