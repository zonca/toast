
################################################################################
#
#        Compilers
#
################################################################################
#
#   sets (cached):
#
#       CMAKE_C_COMPILER_IS_<TYPE>
#       CMAKE_CXX_COMPILER_IS_<TYPE>
#
#
#
#

#   include guard
if(__compilers_is_loaded)
    return()
endif()
set(__compilers_is_loaded ON)

#   languages
foreach(LANG C CXX)

    macro(SET_COMPILER_VAR VAR)
        set(CMAKE_${LANG}_COMPILER_IS_${VAR} ON CACHE STRING "CMake ${LANG} compiler identification (${VAR})")
    endmacro()

    if(("${LANG}" STREQUAL "C" AND CMAKE_COMPILER_IS_GNUCC) 
        OR 
       ("${LANG}" STREQUAL "CXX" AND CMAKE_COMPILER_IS_GNUCXX))

        # GNU compiler
        SET_COMPILER_VAR(       GNU                 )

    elseif(CMAKE_${LANG}_COMPILER MATCHES "icc.*")

        # Intel icc compiler
        SET_COMPILER_VAR(       INTEL               )
        SET_COMPILER_VAR(       INTEL_ICC           )

    elseif(CMAKE_${LANG}_COMPILER MATCHES "icpc.*")

        # Intel icpc compiler
        SET_COMPILER_VAR(       INTEL               )
        SET_COMPILER_VAR(       INTEL_ICPC          )

    elseif(CMAKE_${LANG}_COMPILER_ID MATCHES "Clang")

        # Clang/LLVM compiler
        SET_COMPILER_VAR(       CLANG               )

    elseif(CMAKE_${LANG}_COMPILER_ID MATCHES "PGI")

        # PGI compiler
        SET_COMPILER_VAR(       PGI                 )

    elseif(CMAKE_${LANG}_COMPILER MATCHES "xlC" AND UNIX)

        # IBM xlC compiler
        SET_COMPILER_VAR(       XLC                 )

    elseif(CMAKE_${LANG}_COMPILER MATCHES "aCC" AND UNIX)

        # HP aC++ compiler
        SET_COMPILER_VAR(       HP_ACC              )

    elseif(CMAKE_${LANG}_COMPILER MATCHES "CC" AND CMAKE_SYSTEM_NAME MATCHES "IRIX" AND UNIX)

        # IRIX MIPSpro CC Compiler
        SET_COMPILER_VAR(       MIPS                )

    endif()

endforeach()

