#
#
include(MacroLibraryTargets)

set(LIBTOAST_COMPONENTS
    sources.cmake
    atm/sources.cmake
    fod/sources.cmake
    map/sources.cmake
    math/sources.cmake
    tod/sources.cmake
    math/Random123/sources.cmake
    math/Random123/conventional/sources.cmake
    math/Random123/features/sources.cmake
)

if(NOT USE_MPI)
    list(APPEND LIBTOAST_COMPONENTS fakempi/sources.cmake)
endif()

GLOBAL_OBJECT_TARGET(NAME libtoast-object
    COMPONENTS ${LIBTOAST_COMPONENTS})

GLOBAL_OBJECT_TARGET(NAME libtoast-test-object
    COMPONENTS
        test/sources.cmake
        capi/sources.cmake
        test/gtest/sources.cmake
)
