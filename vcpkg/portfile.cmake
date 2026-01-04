vcpkg_check_linkage(ONLY_DYNAMIC_LIBRARY ONLY_DYNAMIC_CRT)

vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO allanhanan/duvc-ctl
    REF "v${VERSION}"
    SHA512 0
    HEAD_REF main
)

vcpkg_cmake_configure(
    SOURCE_PATH "${SOURCE_PATH}"
    OPTIONS
        -DDUVC_BUILD_SHARED=ON
        -DDUVC_BUILD_STATIC=ON
        -DDUVC_BUILD_C_API=OFF
        -DDUVC_BUILD_CLI=OFF
        -DDUVC_BUILD_TESTS=OFF
        -DDUVC_BUILD_EXAMPLES=OFF
        -DDUVC_BUILD_PYTHON=OFF
        -DDUVC_BUILD_DOCS=OFF
        -DDUVC_INSTALL=ON
        -DDUVC_INSTALL_CMAKE_CONFIG=ON
)

vcpkg_cmake_install()

vcpkg_cmake_config_fixup(CONFIG_PATH lib/cmake/duvc)

vcpkg_copy_pdbs()

file(REMOVE_RECURSE 
    "${CURRENT_PACKAGES_DIR}/debug/include"
    "${CURRENT_PACKAGES_DIR}/debug/share"
)

vcpkg_install_copyright(FILE_LIST "${SOURCE_PATH}/LICENSE")
