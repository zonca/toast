
include(MacroDefineModule)

DEFINE_MODULE(NAME libtoast.tod
    HEADERS     ${TOAST_HEADERS}
    SOURCES     ${TOAST_SOURCES}
    HEADER_EXT  ".hpp;.hh;.h"
    SOURCE_EXT  ".cpp;.cc;.c"
)

