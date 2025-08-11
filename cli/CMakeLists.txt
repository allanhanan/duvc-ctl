cmake_minimum_required(VERSION 3.16)

add_executable(duvc-cli
    main.cpp
)

target_link_libraries(duvc-cli PRIVATE duvc)

if (MSVC)
    target_compile_options(duvc-cli PRIVATE /W4 /permissive-)
    target_compile_definitions(duvc-cli PRIVATE UNICODE _UNICODE NOMINMAX)
elseif(MINGW)
    # MinGW: ensure console subsystem and proper linking
    target_link_options(duvc-cli PRIVATE -mconsole)
    target_compile_options(duvc-cli PRIVATE -Wall -Wextra)
endif()
