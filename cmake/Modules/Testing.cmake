
if(BUILD_TESTING)

    # ------------------------------------------------------------------------ #
    # -- Configure CTest
    # ------------------------------------------------------------------------ #

    ## -- USE_<PROJECT> and <PROJECT>_ROOT
    set(CMAKE_CONFIGURE_OPTIONS )
    foreach(_OPTION BLAS FFTW LAPACK MKL MPI OPENMP PYTHON SSE TBB WCSLIB
            ELEMENTAL MATH)
        add(CMAKE_CONFIGURE_OPTIONS "-DUSE_${_OPTION}=${USE_${_OPTION}}")
        if(NOT "${${_OPTION}_ROOT}" STREQUAL "")
            add(CMAKE_CONFIGURE_OPTIONS "-D${_OPTION}_ROOT=${${_OPTION}_ROOT}")
        endif(NOT "${${_OPTION}_ROOT}" STREQUAL "")
    endforeach()

    ## -- CTest Config
    configure_file(${CMAKE_SOURCE_DIR}/cmake/Templates/CTestConfig.cmake.in
        ${CMAKE_BINARY_DIR}/CTestConfig.cmake @ONLY)

    ENABLE_TESTING()
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
