
if(BUILD_TESTING)

    # ------------------------------------------------------------------------ #
    # -- Configure CTest
    # ------------------------------------------------------------------------ #

    ## -- CTest Config (source tree)
    configure_file(${CMAKE_SOURCE_DIR}/cmake/Templates/CTestConfig.cmake.in
        ${CMAKE_SOURCE_DIR}/CTestConfig.cmake @ONLY)

    ## -- CTest Config (binary tree)
    configure_file(${CMAKE_SOURCE_DIR}/cmake/Templates/CTestConfig.cmake.in
        ${CMAKE_BINARY_DIR}/CTestConfig.cmake @ONLY)

    include(CTest)

    ## -- CTest Setup
    configure_file(${CMAKE_SOURCE_DIR}/cmake/Templates/CTestSetup.cmake.in
        ${CMAKE_BINARY_DIR}/CTestSetup.cmake @ONLY)

    ## -- CTest Custom
    configure_file(${CMAKE_SOURCE_DIR}/cmake/Templates/CTestCustom.cmake.in
        ${CMAKE_BINARY_DIR}/CTestCustom.cmake @ONLY)

    add_test(NAME toast_test
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
        COMMAND ${CMAKE_BINARY_DIR}/toast_test)

endif(BUILD_TESTING)
