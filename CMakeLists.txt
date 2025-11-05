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

    target_link_libraries(_duvc_ctl PRIVATE pybind11::module)
    
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
# Documentation Building
# ============================================================================
option(DUVC_BUILD_DOCS "Build documentation with Sphinx and Doxygen" OFF)

if(DUVC_BUILD_DOCS)
    find_package(Python COMPONENTS Interpreter REQUIRED)
    
    # Find Doxygen
    find_package(Doxygen REQUIRED dot)
    if(NOT DOXYGEN_FOUND)
        message(FATAL_ERROR "Doxygen is required to build documentation")
    endif()
    
    # Verify Sphinx is available
    execute_process(
        COMMAND ${Python_EXECUTABLE} -m sphinx --version
        OUTPUT_QUIET
        ERROR_QUIET
        RESULT_VARIABLE SPHINX_CHECK_RESULT
    )
    
    if(NOT SPHINX_CHECK_RESULT EQUAL 0)
        message(FATAL_ERROR "Sphinx is required to build documentation. Install with: pip install -r docs/sphinx/requirements.txt")
    endif()
    
    # Documentation directories
    set(DOCS_DIR "${CMAKE_CURRENT_SOURCE_DIR}/docs")
    set(DOCS_BUILD_DIR "${CMAKE_CURRENT_BINARY_DIR}/docs")
    set(SPHINX_SOURCE_DIR "${DOCS_DIR}/sphinx")
    set(SPHINX_BUILD_DIR "${DOCS_BUILD_DIR}/sphinx")
    set(DOXYGEN_SOURCE_DIR "${DOCS_DIR}/doxygen")
    set(DOXYGEN_BUILD_DIR "${DOCS_BUILD_DIR}/doxygen")
    
    # Configure Doxygen
    set(DOXYGEN_INPUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/include")
    set(DOXYGEN_OUTPUT_DIR "${DOXYGEN_BUILD_DIR}")
    set(DOXYGEN_INDEX_FILE "${DOXYGEN_BUILD_DIR}/html/index.html")
    
    configure_file(
        "${DOXYGEN_SOURCE_DIR}/Doxyfile.in"
        "${CMAKE_CURRENT_BINARY_DIR}/Doxyfile"
        @ONLY
    )
    
    # Doxygen target
    add_custom_command(
        OUTPUT ${DOXYGEN_INDEX_FILE}
        COMMAND ${CMAKE_COMMAND} -E make_directory ${DOXYGEN_BUILD_DIR}
        COMMAND ${DOXYGEN_EXECUTABLE} ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        MAIN_DEPENDENCY ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile
        COMMENT "Generating C++ API documentation with Doxygen"
        VERBATIM
    )
    
    add_custom_target(doxygen ALL DEPENDS ${DOXYGEN_INDEX_FILE})
    
    # Sphinx target
    set(SPHINX_INDEX_FILE "${SPHINX_BUILD_DIR}/index.html")
    
    add_custom_command(
        OUTPUT ${SPHINX_INDEX_FILE}
        DEPENDS 
            ${SPHINX_SOURCE_DIR}/conf.py
            ${SPHINX_SOURCE_DIR}/index.rst
            ${SPHINX_SOURCE_DIR}/requirements.txt
            doxygen
        COMMAND ${CMAKE_COMMAND} -E make_directory ${SPHINX_BUILD_DIR}
        COMMAND ${Python_EXECUTABLE} -m pip install -q -r ${SPHINX_SOURCE_DIR}/requirements.txt
        COMMAND ${Python_EXECUTABLE} -m sphinx 
            -b html
            -D breathe_projects.duvc-ctl=${DOXYGEN_BUILD_DIR}/xml
            -d ${SPHINX_BUILD_DIR}/.doctrees
            ${SPHINX_SOURCE_DIR}
            ${SPHINX_BUILD_DIR}
        WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
        COMMENT "Building HTML documentation with Sphinx"
        VERBATIM
    )
    
    add_custom_target(sphinx ALL DEPENDS ${SPHINX_INDEX_FILE})
    add_dependencies(sphinx doxygen)
    
    # Combined docs target
    add_custom_target(docs
        DEPENDS sphinx doxygen
        COMMENT "Building complete documentation"
    )
    
    # Clean docs target
    add_custom_target(docs-clean
        COMMAND ${CMAKE_COMMAND} -E remove_directory ${DOCS_BUILD_DIR}
        COMMENT "Cleaning documentation build directory"
    )
    
    # Live reload development server
    find_program(SPHINX_AUTOBUILD_EXECUTABLE sphinx-autobuild)
    if(SPHINX_AUTOBUILD_EXECUTABLE)
        add_custom_target(docs-serve
            DEPENDS doxygen
            COMMAND ${SPHINX_AUTOBUILD_EXECUTABLE}
                --watch ${CMAKE_CURRENT_SOURCE_DIR}/include
                --ignore "*.tmp"
                --ignore "*/.git/*"
                -b html
                -D breathe_projects.duvc-ctl=${DOXYGEN_BUILD_DIR}/xml
                ${SPHINX_SOURCE_DIR}
                ${SPHINX_BUILD_DIR}
            COMMENT "Starting live documentation server at http://localhost:8000"
            USES_TERMINAL
        )
    endif()
    
    # Python docs build script integration
    add_custom_target(docs-build-script
        COMMAND ${Python_EXECUTABLE} ${DOCS_DIR}/build.py
            --build-dir ${DOCS_BUILD_DIR}
            --source-dir ${DOCS_DIR}
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        COMMENT "Building documentation using Python build script"
    )
    
    # Install documentation
    if(DUVC_INSTALL)
        install(
            DIRECTORY ${SPHINX_BUILD_DIR}/
            DESTINATION ${CMAKE_INSTALL_DOCDIR}
            COMPONENT Documentation
            OPTIONAL
            PATTERN ".doctrees" EXCLUDE
            PATTERN ".buildinfo" EXCLUDE
        )
        
        # Create documentation package component
        set(CPACK_COMPONENT_DOCUMENTATION_DISPLAY_NAME "Documentation")
        set(CPACK_COMPONENT_DOCUMENTATION_DESCRIPTION "HTML documentation for duvc-ctl")
        set(CPACK_COMPONENT_DOCUMENTATION_DEPENDS Runtime)
    endif()
    
    # Add to main build targets list for summary
    list(APPEND DUVC_CORE_TARGETS docs)
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
    message(STATUS "Documentation:")
    message(STATUS "  Build docs: ${DUVC_BUILD_DOCS}")
    if(DUVC_BUILD_DOCS)
        message(STATUS "  Doxygen: ${DOXYGEN_EXECUTABLE}")
        message(STATUS "  Sphinx: Available via Python")
        if(SPHINX_AUTOBUILD_EXECUTABLE)
            message(STATUS "  Live server: Available (sphinx-autobuild)")
        endif()
    endif()
    message(STATUS "")
    message(STATUS "Installation:")
    message(STATUS "  Install: ${DUVC_INSTALL}")
    message(STATUS "  Install prefix: ${CMAKE_INSTALL_PREFIX}")
    message(STATUS "")
endif()
