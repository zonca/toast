
include(MacroDefineModule)

DEFINE_MODULE(NAME libtoast.main
    HEADERS     ${CMAKE_SOURCE_DIR}/config.h
    EXCLUDE     toast_test
    HEADER_EXT  .hpp .hh .h
    SOURCE_EXT  .cpp .cc .c
)

