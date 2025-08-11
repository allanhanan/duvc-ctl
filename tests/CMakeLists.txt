cmake_minimum_required(VERSION 3.16)
project(duvc_core_tests LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Path to project root
set(DUVC_ROOT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/..)

# Catch2
include(FetchContent)
FetchContent_Declare(
    catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.5.2
)
FetchContent_MakeAvailable(catch2)

# Test executable that compiles duvc sources directly
add_executable(duvc_core_tests 
    test_core.cpp
    ${DUVC_ROOT_DIR}/src/core.cpp
    ${DUVC_ROOT_DIR}/src/bindings.cpp
)

target_include_directories(duvc_core_tests PRIVATE ${DUVC_ROOT_DIR}/include)
target_link_libraries(duvc_core_tests PRIVATE Catch2::Catch2WithMain)

if(WIN32)
    target_link_libraries(duvc_core_tests PRIVATE ole32 oleaut32 strmiids)
endif()

# Apply same compiler flags as main project
if(MSVC)
    target_compile_options(duvc_core_tests PRIVATE /W4 /permissive-)
    target_compile_definitions(duvc_core_tests PRIVATE UNICODE _UNICODE NOMINMAX)
else()
    target_compile_options(duvc_core_tests PRIVATE -Wall -Wextra -Wpedantic)
endif()

enable_testing()
include(CTest)
include(Catch)
catch_discover_tests(duvc_core_tests)
