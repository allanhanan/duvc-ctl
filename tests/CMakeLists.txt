# tests/CMakeLists.txt
cmake_minimum_required(VERSION 3.16)

include(FetchContent)

# ============================================================================
# Test Framework Setup - Catch2
# ============================================================================
FetchContent_Declare(
    catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.5.2
)

FetchContent_MakeAvailable(catch2)

enable_testing()

# ============================================================================
# Test Helper Function
# ============================================================================
function(duvc_add_cpp_test test_name sources)
    add_executable(${test_name} ${sources})
    
    target_link_libraries(${test_name} PRIVATE 
        duvc::core 
        Catch2::Catch2WithMain
    )
    
    target_include_directories(${test_name} PRIVATE 
        ${CMAKE_SOURCE_DIR}/src
        ${CMAKE_SOURCE_DIR}/include
    )
    
    # Apply same compiler flags as main project
    duvc_set_target_properties(${test_name})
    
    # Auto-discover tests
    include(CTest)
    include(Catch)
    catch_discover_tests(${test_name}
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )
    
    # Coverage if enabled
    if(DUVC_ENABLE_COVERAGE)
        target_compile_options(${test_name} PRIVATE --coverage)
        target_link_libraries(${test_name} PRIVATE --coverage)
    endif()
endfunction()

# ============================================================================
# Unit Tests
# ============================================================================
duvc_add_cpp_test(core_tests cpp/unit/core_tests.cpp)
duvc_add_cpp_test(platform_tests cpp/unit/platform_tests.cpp)
duvc_add_cpp_test(vendor_tests cpp/unit/vendor_tests.cpp)
duvc_add_cpp_test(utils_tests cpp/unit/utils_tests.cpp)

# ============================================================================
# Integration Tests
# ============================================================================
duvc_add_cpp_test(device_integration_tests cpp/integration/device_integration_tests.cpp)

# ============================================================================
# Functional Tests
# ============================================================================
duvc_add_cpp_test(camera_workflow_tests cpp/functional/camera_workflow_tests.cpp)

# ============================================================================
# Custom Test Targets
# ============================================================================
# Run only unit tests
add_custom_target(test_unit
    COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure --label-regex "unit"
    DEPENDS core_tests platform_tests vendor_tests utils_tests
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
)

# Run only integration tests
add_custom_target(test_integration
    COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure --label-regex "integration"
    DEPENDS device_integration_tests
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
)

# Run only functional tests
add_custom_target(test_functional
    COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure --label-regex "functional"
    DEPENDS camera_workflow_tests
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
)
