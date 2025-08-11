cmake_minimum_required(VERSION 3.16)
project(duvc-ctl VERSION 1.0.0 LANGUAGES CXX)

# Options
option(DUVC_BUILD_STATIC "Build duvc static library" ON)
option(DUVC_BUILD_SHARED "Build duvc shared library" OFF)
option(DUVC_BUILD_CLI "Build duvc CLI" ON)
option(DUVC_BUILD_PYTHON "Build Python bindings (pybind11)" OFF)
option(DUVC_WARNINGS_AS_ERRORS "Treat warnings as errors" OFF)

# Global settings
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Output dirs (nice layout for MSVC multi-config and Makefile single-config)
foreach(OUTPUTCONFIG ${CMAKE_CONFIGURATION_TYPES})
    string(TOUPPER ${OUTPUTCONFIG} OUTPUTCONFIG_UC)
    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_${OUTPUTCONFIG_UC} ${CMAKE_BINARY_DIR}/lib)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_${OUTPUTCONFIG_UC} ${CMAKE_BINARY_DIR}/bin)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_${OUTPUTCONFIG_UC} ${CMAKE_BINARY_DIR}/bin)
endforeach()
if(NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
endif()

# Helper: warning flags
function(duvc_apply_warnings target)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /permissive-)
        if(DUVC_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE /WX)
        endif()
        target_compile_definitions(${target} PRIVATE UNICODE _UNICODE NOMINMAX)
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
        if(DUVC_WARNINGS_AS_ERRORS)
            target_compile_options(${target} PRIVATE -Werror)
        endif()
    endif()
endfunction()

# Helper: link DirectShow on Windows
function(duvc_link_directshow target)
    if(WIN32)
        target_link_libraries(${target} PRIVATE ole32 oleaut32 strmiids)
    endif()
endfunction()

# Helper: MinGW console subsystem fix
function(duvc_fix_mingw_console target)
    if(MINGW)
        target_link_options(${target} PRIVATE -mconsole -Wl,--subsystem,console)
    endif()
endfunction()

# Include dirs
set(DUVC_INCLUDE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/include)

# Library target(s)
set(DUVC_SOURCES
    src/core.cpp
    src/bindings.cpp
)

if(DUVC_BUILD_STATIC)
    add_library(duvc STATIC ${DUVC_SOURCES})
    target_include_directories(duvc PUBLIC ${DUVC_INCLUDE_DIR})
    target_compile_features(duvc PUBLIC cxx_std_17)
    duvc_apply_warnings(duvc)
    duvc_link_directshow(duvc)
endif()

if(DUVC_BUILD_SHARED)
    add_library(duvc_shared SHARED ${DUVC_SOURCES})
    target_include_directories(duvc_shared PUBLIC ${DUVC_INCLUDE_DIR})
    target_compile_features(duvc_shared PUBLIC cxx_std_17)
    target_compile_definitions(duvc_shared PRIVATE DUVCC_DLL_BUILD)
    set_target_properties(duvc_shared PROPERTIES OUTPUT_NAME duvc)
    duvc_apply_warnings(duvc_shared)
    duvc_link_directshow(duvc_shared)
endif()

# CLI
if(DUVC_BUILD_CLI)
    add_executable(duvc-cli cli/main.cpp)
    target_include_directories(duvc-cli PRIVATE ${DUVC_INCLUDE_DIR})
    if(DUVC_BUILD_STATIC)
        target_link_libraries(duvc-cli PRIVATE duvc)
    elseif(DUVC_BUILD_SHARED)
        target_link_libraries(duvc-cli PRIVATE duvc_shared)
    else()
        message(FATAL_ERROR "CLI requested but no library variant enabled. Enable DUVC_BUILD_STATIC or DUVC_BUILD_SHARED.")
    endif()
    duvc_apply_warnings(duvc-cli)
    duvc_link_directshow(duvc-cli)
    duvc_fix_mingw_console(duvc-cli)
endif()

# Python bindings via pybind11 (optional)
option(DUVC_USE_SYSTEM_PYBIND11 "Use system-installed pybind11" OFF)

if(DUVC_BUILD_PYTHON)
    # Locate Python
    find_package(Python COMPONENTS Interpreter Development REQUIRED)

    # pybind11
    if(DUVC_USE_SYSTEM_PYBIND11)
        find_package(pybind11 CONFIG REQUIRED)
    else()
        # Use FetchContent to grab pybind11
        include(FetchContent)
        FetchContent_Declare(
            pybind11
            GIT_REPOSITORY https://github.com/pybind/pybind11.git
            GIT_TAG v2.11.1
        )
        FetchContent_MakeAvailable(pybind11)
    endif()

    # Python binding source
    set(DUVC_PY_SOURCES src/py/pybind_module.cpp)

    if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/src/py/pybind_module.cpp)
        pybind11_add_module(_duvc_ctl ${DUVC_PY_SOURCES})
        
        # For MSVC, handle configuration-specific output directories
        if(CMAKE_GENERATOR_PLATFORM)
            set_target_properties(_duvc_ctl PROPERTIES 
                OUTPUT_NAME "_duvc_ctl"
                LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/py
                RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/py
                LIBRARY_OUTPUT_DIRECTORY_RELEASE ${CMAKE_BINARY_DIR}/py
                RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_BINARY_DIR}/py
                LIBRARY_OUTPUT_DIRECTORY_DEBUG ${CMAKE_BINARY_DIR}/py
                RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_BINARY_DIR}/py
            )
        else()
            set_target_properties(_duvc_ctl PROPERTIES 
                OUTPUT_NAME "_duvc_ctl"
                LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/py
                RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/py
            )
        endif()
        
        target_include_directories(_duvc_ctl PRIVATE ${DUVC_INCLUDE_DIR})
        
        if(DUVC_BUILD_STATIC)
            target_link_libraries(_duvc_ctl PRIVATE duvc)
        elseif(DUVC_BUILD_SHARED)
            target_link_libraries(_duvc_ctl PRIVATE duvc_shared)
        else()
            target_sources(_duvc_ctl PRIVATE ${DUVC_SOURCES})
            duvc_link_directshow(_duvc_ctl)
        endif()
        
        duvc_apply_warnings(_duvc_ctl)
        duvc_link_directshow(_duvc_ctl)
             
    else()
        message(WARNING "DUVC_BUILD_PYTHON=ON but src/py/pybind_module.cpp not found. Skipping Python module.")
    endif()
endif()

# Installation (optional, basic)
include(GNUInstallDirs)

if(DUVC_BUILD_STATIC OR DUVC_BUILD_SHARED)
    install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
endif()

if(TARGET duvc)
    install(TARGETS duvc
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
endif()

if(TARGET duvc_shared)
    install(TARGETS duvc_shared
        ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
        LIBRARY DESTINATION ${CMAKE_LIBRARY_DIR}
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
endif()

if(TARGET duvc-cli)
    install(TARGETS duvc-cli
        RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
endif()

if(DUVC_BUILD_PYTHON AND TARGET _duvc_ctl)
    # Install the Python extension module to the correct location within the package
    install(TARGETS _duvc_ctl
        DESTINATION ${SKBUILD_PLATLIB_DIR}/duvc_ctl)
endif()