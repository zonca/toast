# find packages for TOAST

include(MacroUtilities)
include(GenericCMakeOptions)
include(GenericCMakeFunctions)
include(Compilers)

if(NOT CMAKE_VERSION VERSION_LESS 2.6.3)
    cmake_policy(SET CMP0011 NEW)
endif()



# - MPI
# - OpenMP
# - Python
# - BLAS
# - LAPACK
# - OpenBLAS
# - MKL
# - TBB
# - FFTW
# - wcslib
# - Elemental

add_option(USE_SSE "Use SSE/AVX optimization flags" ON)

add_option(USE_MPI "Use MPI" ON)
add_option(USE_OPENMP "Use OpenMP" ON)
add_option(USE_PYTHON "Use Python" OFF)

add_option(USE_MKL "Enable Intel Math Kernel Library (MKL)" ON)
add_option(USE_TBB "Enable Intel Thread Building Blocks (TBB)" ON)
add_option(USE_MATH "Enable Intel IMF Math library" ${CMAKE_CXX_COMPILER_IS_INTEL})

add_option(USE_BLAS "Use BLAS" ON)
add_option(USE_LAPACK "Use LAPACK" ON)
add_option(USE_OPENBLAS "Use OpenBLAS" OFF)

add_option(USE_FFTW "Use FFTW" ON)
add_option(USE_WCSLIB "Use wcslib" ON)
add_option(USE_ELEMENTAL "Use Elemental" OFF)

################################################################################
#
#        Threads (pthreads)
#
################################################################################
if(USE_PTHREADS)

    SET(CMAKE_THREAD_PREFER_PTHREADS ON)
    FIND_PACKAGE(Threads QUIET)
    #add_definitions(-DHAVE_PTHREAD)

endif()


################################################################################
#
#        MPI
#
################################################################################
if(USE_MPI)

    ConfigureRootSearchPath(MPI)
    find_package(MPI REQUIRED)

    # Add the MPI-specific compiler and linker flags
    # Also, search for #includes in MPI's paths
    add(CMAKE_C_FLAGS_EXTRA    "${MPI_C_COMPILE_FLAGS}")
    add(CMAKE_CXX_FLAGS_EXTRA  "${MPI_CXX_COMPILE_FLAGS}")
    add(CMAKE_EXE_LINKER_FLAGS "${MPI_CXX_LINK_FLAGS}")

    #add_definitions(-DHAVE_MPI=1)

endif()


################################################################################
#
#        OpenMP
#
################################################################################
if(USE_OPENMP)

    if(CMAKE_CXX_COMPILER_IS_CLANG AND ${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
        message(AUTHOR_WARNING
            "Clang on Darwin (as of OS X Mavericks) does not have OpenMP Support")
    endif()

    find_package(OpenMP REQUIRED)
    # Add the OpenMP-specific compiler and linker flags
    add(CMAKE_C_FLAGS_EXTRA   "${OpenMP_C_FLAGS}")
    add(CMAKE_CXX_FLAGS_EXTRA "${OpenMP_CXX_FLAGS}")

endif(USE_OPENMP)


################################################################################
#
#        Python
#
################################################################################
if(USE_PYTHON)

    find_package( PythonLibs 3.3 REQUIRED )
    find_package( PythonInterp 3.3 REQUIRED )

    find_package_handle_standard_args(Python3 DEFAULT_MSG
        PYTHON_VERSION_STRING PYTHON_EXECUTABLE PYTHON_INCLUDE_DIRS
        PYTHON_LIBRARIES)

endif(USE_PYTHON)


################################################################################
#
#        MKL - Intel Math Kernel Library
#
################################################################################
if(USE_MKL)

    if(NOT CMAKE_CXX_COMPILER_IS_INTEL)

        set(MKL_THREADING "Sequential")
        ConfigureRootSearchPath(MKL)
        find_package(MKL REQUIRED)

        foreach(_def ${MKL_DEFINITIONS})
            add_definitions(-D${_def})
        endforeach()
        list(APPEND EXTERNAL_LINK_FLAGS "${MKL_CXX_LINK_FLAGS}")

    elseif(CMAKE_COMPILER_IS_INTEL)

        add(CMAKE_C_FLAGS_EXTRA   "-mkl")
        add(CMAKE_CXX_FLAGS_EXTRA "-mkl")

    endif()

endif()


################################################################################
#
#        TBB - Intel Thread Building Blocks
#
################################################################################
if(USE_TBB)

    if(NOT CMAKE_COMPILER_IS_INTEL)

        ConfigureRootSearchPath(TBB)
        find_package(TBB REQUIRED COMPONENTS malloc)

    elseif(CMAKE_COMPILER_IS_INTEL)

        add(CMAKE_C_FLAGS_EXTRA   "-tbb")
        add(CMAKE_CXX_FLAGS_EXTRA "-tbb")

    endif()

    add_definitions(-DUSE_TBB)
    add_definitions(-DUSE_TBB_MALLOC)

endif()


################################################################################
#
#        Math - Intel IMF library
#
################################################################################
if(USE_MATH)

    ConfigureRootSearchPath(IMF)
    find_package(IMF REQUIRED)

endif()


################################################################################
#
#        BLAS, LAPACK, and OpenBLAS
#
################################################################################
foreach(_LIB BLAS LAPACK OpenBLAS)

    string(TOUPPER "${_LIB}" _UPPER_LIB)
    if(USE_${_UPPER_LIB})

        ConfigureRootSearchPath(${_LIB})
        find_package(${_LIB} REQUIRED)

    endif()

endforeach()


################################################################################
#
#        FFTW
#
################################################################################
if(USE_FFTW)

    ConfigureRootSearchPath(FFTW3)
    find_package(FFTW3 REQUIRED)

    if(NOT USE_MKL)
        # double precision with threads
        find_package(FFTW3 COMPONENTS threads)
    endif()

endif(USE_FFTW)


################################################################################
#
#        wcslib
#
################################################################################
if(USE_WCSLIB)

    ConfigureRootSearchPath(wcslib)
    find_package(wcslib REQUIRED)

endif(USE_WCSLIB)


################################################################################
#
#        Elemental
#
################################################################################
if(USE_ELEMENTAL)

    ConfigureRootSearchPath(Elemental)
    find_package(Elemental REQUIRED)

endif(USE_ELEMENTAL)


################################################################################
# --- setting definitions: EXTERNAL_INCLUDE_DIRS,   ---------------------------#
#                          EXTERNAL_LIBRARIES       ---------------------------#
################################################################################

set(EXTERNAL_INCLUDE_DIRS
    ${MPI_INCLUDE_PATH} ${MPI_C_INCLUDE_PATH} ${MPI_CXX_INCLUDE_PATH}
    ${PYTHON_INCLUDE_DIRS}
    ${MKL_INCLUDE_DIRS}
    ${TBB_INCLUDE_DIRS}
    ${IMF_INCLUDE_DIRS}
    ${FFTW3_INCLUDE_DIRS}
    ${wcslib_INCLUDE_DIRS}
    ${Elemental_INCLUDE_DIRS}
)

set(EXTERNAL_LIBRARIES ${CMAKE_THREAD_LIBS_INIT}
    ${MPI_C_LIBRARIES} ${MPI_CXX_LIBRARIES} ${MPI_EXTRA_LIBRARY}
    ${PYTHON_LIBRARIES}
    ${MKL_LIBRARIES}
    ${TBB_LIBRARIES}
    ${IMF_LIBRARIES}
    ${BLAS_LIBRARIES}
    ${LAPACK_LIBRARIES}
    ${OpenBLAS_LIBRARIES}
    ${FFTW3_LIBRARIES}
    ${wcslib_LIBRARIES}
    ${Elemental_LIBRARIES}
)



################################################################################
#
#        SSE
#
################################################################################
if(USE_SSE)

    include(FindSSE)

    GET_SSE_COMPILE_FLAGS(_CXX_FLAGS_EXTRA SSE_DEFINITIONS)
    foreach(_DEF ${SSE_DEFINITIONS})
        add_definitions(-D${_DEF})
    endforeach()
    unset(SSE_DEFINITIONS)

    add(CMAKE_CXX_FLAGS_EXTRA "${_CXX_FLAGS_EXTRA}")

endif()



