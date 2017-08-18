
include(MacroDefineModule)

if(USE_ELEMENTAL)

    DEFINE_MODULE(NAME libtoast.atm
        HEADER_EXT ".h"
        SOURCE_EXT ".cpp"
    )

endif(USE_ELEMENTAL)

