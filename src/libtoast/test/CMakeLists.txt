
include(MacroLibraryTargets)

GLOBAL_OBJECT_TARGET(NAME libtoast-test-object
    COMPONENTS
        sources.cmake
        ../capi/sources.cmake
        gtest/sources.cmake
)

