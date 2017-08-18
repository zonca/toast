
include_directories(${CMAKE_SOURCE_DIR}/source)

include(MacroDefineModule)

DEFINE_MODULE(NAME Common
                   HEADER_DIR ""
                   SOURCE_DIR ""
                   HEADER_EXT ".h;.hh"
                   SOURCE_EXT ".cc;.cpp"
                   EXCLUDE "svn_version;version"
                   LINK_LIBRARIES ""
)
