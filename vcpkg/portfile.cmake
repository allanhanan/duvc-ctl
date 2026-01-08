vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO allanhanan/duvc-ctl
    REF "v${VERSION}"
    SHA512 09252aa6f6ed96ca0d225543b48afe443dc69e57c193a4fc1b2b46d5f7ef8b5dcbfbfd700edba8db0db890e51071b70358a256da1ae6248f881d88b1e21a573c
    HEAD_REF main
)

vcpkg_configure_cmake(
    SOURCE_PATH ${SOURCE_PATH}
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

vcpkg_install_cmake()

vcpkg_fixup_cmake_targets(CONFIG_PATH lib/cmake/duvc-ctl)

vcpkg_copy_pdbs()

file(REMOVE_RECURSE
    "${CURRENT_PACKAGES_DIR}/debug/include"
    "${CURRENT_PACKAGES_DIR}/debug/share"
)

file(INSTALL "${SOURCE_PATH}/LICENSE" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME copyright)
