
include(CMakeMacroParseArguments)

#==============================================================================#

cmake_policy(PUSH)
if(NOT CMAKE_VERSION VERSION_LESS 3.1)
    cmake_policy(SET CMP0054 NEW)
endif()

################################################################################
#
#   Write a config file for installation (writes preprocessor definitions)
#
################################################################################

function(write_toast_config_file)

    cmake_parse_arguments(CONF
                          ""
                          "TEMPLATE;FILE_NAME;WRITE_PATH;INSTALL_PATH"
                          "DEFINE_VARS;UNDEFINE_VARS"
                          ${ARGN}
                         )

    get_directory_property(_defs DIRECTORY ${CMAKE_SOURCE_DIR} COMPILE_DEFINITIONS)

    if(CONF_TEMPLATE)
        configure_file(${CONF_TEMPLATE} ${CONF_WRITE_PATH}/.${CONF_FILE_NAME}.tmp @ONLY)
        file(READ ${CONF_WRITE_PATH}/.${CONF_FILE_NAME}.tmp _orig)
    endif()
    
    STRING(TOLOWER ${PROJECT_NAME} _project)
    STRING(TOLOWER ${CONF_FILE_NAME} _file)
    set(_name "${_project}_${_file}")
    STRING(REPLACE "." "_" _name "${_name}")
    STRING(REPLACE "/" "_" _name "${_name}")
    STRING(TOLOWER "${_name}" _name)

    set(header1 "#ifndef ${_name}_")
    set(header2 "#define ${_name}_")

    set(_output "${_orig}//\n//\n//\n//\n//\n\n${header1}\n${header2}\n")

    if(DEFINED ${PROJECT_NAME}_VERSION)
        define_version_00(${PROJECT_NAME} MAJOR)
        define_version_00(${PROJECT_NAME} MINOR)
        define_version_00(${PROJECT_NAME} PATCH)

        set(_prefix ${PROJECT_NAME})
        if("${${_prefix}_PATCH}" GREATER 0)
          set(VERSION_STRING "${${_prefix}_MAJOR_VERSION}_${${_prefix}_MINOR_VERSION}_${${_prefix}_PATCH_VERSION}")
        else()
          set(VERSION_STRING "${${_prefix}_MAJOR_VERSION}_${${_prefix}_MINOR_VERSION}")
        endif()

        set(s1 "//")
        set(s2 "//  Caution, this is the only ${PROJECT_NAME} header that is guaranteed")
        set(s3 "//  to change with every release, including this header")
        set(s4 "//  will cause a recompile every time a new ${PROJECT_NAME} version is")
        set(s5 "//  released.")
        set(s6 "//")
        set(s7 "//  ${PROJECT_NAME}_VERSION % 100 is the patch level")
        set(s8 "//  ${PROJECT_NAME}_VERSION / 100 % 1000 is the minor version")
        set(s9 "//  ${PROJECT_NAME}_VERSION / 100000 is the major version")

        set(_output "${_output}\n${s1}\n${s2}\n${s3}\n${s4}\n${s5}\n${s6}\n${s7}\n${s8}\n${s9}\n")
        set(_output "${_output}\n#define ${PROJECT_NAME}_VERSION")
        set(_output "${_output} ${${_prefix}_MAJOR_VERSION_00}${${_prefix}_MINOR_VERSION_00}${${_prefix}_PATCH_VERSION_00}\n")

        set(s1 "//")
        set(s2 "//  ${PROJECT_NAME}_LIB_VERSION must be defined to be the same as")
        set(s3 "//  ${PROJECT_NAME}_VERSION but as a *string* in the form \"x_y[_z]\" where x is")
        set(s4 "//  the major version number, y is the minor version number, and z is the patch")
        set(s5 "//  level if not 0.")

        set(_output "${_output}\n${s1}\n${s2}\n${s3}\n${s4}\n${s5}\n")
        set(_output "${_output}\n#define ${PROJECT_NAME}_LIB_VERSION \"${VERSION_STRING}\"\n")
    endif()

    set(_output "${_output}\n\n//\n// TOAST CONFIG\n//\n")

    foreach(_def ${CONF_DEFINE_VARS})
        set(_str0 "/* Define ${${_def}_LABEL} ${${_def}_MSG} */")
        set(_str1 "#define ${${_def}_NAME} ${${_def}_ENTRY}")
        set(_output "${_output}\n${_str0}\n${_str1}\n")
    endforeach()

    foreach(_def ${CONF_UNDEFINE_VARS})
        set(_str0 "/* Define ${${_def}_LABEL} ${${_def}_MSG} */")
        set(_str1 "/* #undef ${${_def}_LABEL} */")
        set(_output "${_output}\n${_str0}\n${_str1}\n")
    endforeach()

    set(_output "${_output}\n\n//\n// DEFINES\n//\n")
    
    # if DEBUG, add ${PROJECT_NAME}_DEBUG and same for NDEBUG
    foreach(_def ${_defs})
        if("${_def}" STREQUAL "DEBUG")
            list(APPEND _defs ${PROJECT_NAME}_DEBUG)
        elseif("${_def}" STREQUAL "NDEBUG")
            list(APPEND _defs ${PROJECT_NAME}_NDEBUG)
        endif()
    endforeach()

    list(REMOVE_ITEM _defs DEBUG)
    list(REMOVE_ITEM _defs NDEBUG)

    foreach(_def ${_defs})
        set(_str1 "#if !defined(${_def})")
        set(_str2 "#   define ${_def}")
        set(_str3 "#endif")
        set(_output "${_output}\n${_str1}\n${_str2}\n${_str3}\n")
    endforeach()

    list(APPEND _defs ${CMAKE_PROJECT_NAME}_DEBUG)
    list(APPEND _defs ${CMAKE_PROJECT_NAME}_NDEBUG)
    list(REMOVE_DUPLICATES _defs)

    set(_output "${_output}\n\n//\n// To avoid any of the definitions, define DONT_{definition}\n//\n")
    foreach(_def ${_defs})
        set(_str1 "#if defined(DONT_${_def})")
        set(_str2 "#   if defined(${_def})")
        set(_str3 "#       undef ${_def}")
        set(_str4 "#   endif")
        set(_str5 "#endif")
        set(_output "${_output}\n${_str1}\n${_str2}\n${_str3}\n${_str4}\n${_str5}\n")
    endforeach()

    set(_output "${_output}\n\n#endif // end ${_name}_\n\n")

    get_filename_component(_fname ${CONF_FILE_NAME} NAME)
    if(NOT EXISTS ${CONF_WRITE_PATH}/${_fname})
        file(WRITE ${CONF_WRITE_PATH}/${_fname} ${_output})
    else()
        file(WRITE ${CMAKE_BINARY_DIR}/.config_diff/${_fname} ${_output})
        file(STRINGS ${CONF_WRITE_PATH}/${_fname} _existing)
        file(STRINGS ${CMAKE_BINARY_DIR}/.config_diff/${_fname} _just_written)
        string(COMPARE EQUAL "${_existing}" "${_just_written}" _diff)
        if(NOT _diff)
            file(WRITE ${CONF_WRITE_PATH}/${_fname} ${_output})
        endif()
    endif()

    if(NOT "${CONF_INSTALL_PATH}" STREQUAL "")
        install(FILES ${CONF_WRITE_PATH}/${_fname} DESTINATION ${CONF_INSTALL_PATH})
    endif()

endfunction()

#==============================================================================#

#function(FIND_HEADER_FILE VAR FILE_PATH)

#    find_file(

#endfunction(FIND_HEADER_FILE VAR FILE_PATH)

#==============================================================================#

function(GET_TYPE VAR QUERY)
    
    if(${QUERY})
        SET(${VAR} DEFINE PARENT_SCOPE)
    else()
        SET(${VAR} UNDEFINE PARENT_SCOPE)
    endif(${QUERY})
    
endfunction(GET_TYPE VAR QUERY)

#==============================================================================#

function(SET_VAR)
    cmake_parse_arguments(
        VAR
        "DEFINE;UNDEFINE"
        "NAME;ENTRY;LABEL;MSG"
        ""
        ${ARGN})

    set(${VAR_LABEL}_NAME   "${VAR_NAME}"   PARENT_SCOPE)
    set(${VAR_LABEL}_ENTRY  "${VAR_ENTRY}"  PARENT_SCOPE)
    set(${VAR_LABEL}_LABEL  "${VAR_LABEL}"  PARENT_SCOPE)
    set(${VAR_LABEL}_MSG    "${VAR_MSG}"    PARENT_SCOPE)
    
    if(VAR_DEFINE)
        set(DEFINE_VARIABLES ${DEFINE_VARIABLES} ${VAR_LABEL} PARENT_SCOPE)
    elseif(VAR_UNDEFINE)
        set(UNDEFINE_VARIABLES ${UNDEFINE_VARIABLES} ${VAR_LABEL} PARENT_SCOPE)    
    endif()
    
endfunction(SET_VAR)

#==============================================================================#

function(FIND_HEADER VAR HEADER)

    get_property(dirs DIRECTORY 
        ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY INCLUDE_DIRECTORIES)
    
    set(HEADER_FILE ${HEADER}) 
    configure_file(${CMAKE_SOURCE_DIR}/cmake/Templates/header-test.cc.in
        ${CMAKE_BINARY_DIR}/header-test.cc @ONLY)
    
    try_compile(RET
        ${CMAKE_BINARY_DIR} 
        ${CMAKE_BINARY_DIR}/header-test.cc
        CMAKE_FLAGS ${CMAKE_CXX_FLAGS}
        INCLUDE_DIRECTORIES ${dirs}
        OUTPUT_VARIABLE RET_OUT)
                
    IF(RET)
        set(${VAR} ON PARENT_SCOPE)
    ELSE()
        set(${VAR} OFF PARENT_SCOPE)        
    ENDIF()
    
endfunction()

#==============================================================================#

find_program(GIT_COMMAND git)

#==============================================================================#

SET_VAR(DEFINE
    NAME    "F77_FUNC(name)"
    ENTRY   "name ## _"
    LABEL   "F77_FUNC"
    MSG     "to a macro mangling the given Fortran function name")

#==============================================================================#

GET_TYPE(HAS USE_BLAS)
SET_VAR(${HAS}
    NAME    "HAVE_BLAS"
    ENTRY   "1"
    LABEL   "HAVE_BLAS"
    MSG     "if you have a BLAS library")

#==============================================================================#

GET_TYPE(HAS USE_LAPACK)
SET_VAR(${HAS}
    NAME    "HAVE_LAPACK"
    ENTRY   "1"
    LABEL   "HAVE_LAPACK"
    MSG     "if you have a LAPACK library")
    
#==============================================================================#

GET_TYPE(HAS USE_OPENBLAS)
SET_VAR(${HAS}
    NAME    "HAVE_OPENBLAS"
    ENTRY   "1"
    LABEL   "HAVE_OPENBLAS"
    MSG     "if you have a OpenBLAS library")

#==============================================================================#

FIND_HEADER(CMATH_FILE "cmath")
GET_TYPE(HAS CMATH_FILE)
SET_VAR(${HAS}
    LABEL   "HAVE_MATH"
    NAME    "HAVE_MATH"
    ENTRY   "1"
    MSG     "if you have the C math library")

SET_VAR(${HAS}
    LABEL   "HAVE_MATH"
    NAME    "HAVE_MATH"
    ENTRY   "1"
    MSG     "to 1 if you have the ANSI C header files.")

#==============================================================================#

FIND_HEADER(MATH_H_FILE "math.h")
GET_TYPE(HAS MATH_H_FILE)
SET_VAR(${HAS}
    LABEL   "STDC_HEADERS"
    NAME    "STDC_HEADERS"
    ENTRY   "1"
    MSG     "if you have the <math.h> library")

#==============================================================================#

FIND_HEADER(MEMORY_FILE "memory.h")
GET_TYPE(HAS MEMORY_FILE)
SET_VAR(${HAS}
    LABEL   "HAVE_MEMORY_H"
    NAME    "HAVE_MEMORY_H"
    ENTRY   "1"
    MSG     "if you have the <memory.h> library")

#==============================================================================#

FIND_HEADER(HEADER_FILE "inttypes.h")
GET_TYPE(HAS HEADER_FILE)
SET_VAR(${HAS}
    LABEL   "HAVE_INTTYPES_H"
    NAME    "HAVE_INTTYPES_H"
    ENTRY   "1"
    MSG     "to 1 if you have the <inttypes.h> header file.")

#==============================================================================#

FIND_HEADER(HEADER_FILE "stdint.h")
GET_TYPE(HAS HEADER_FILE)
SET_VAR(${HAS}
    LABEL   "HAVE_STDINT_H"
    NAME    "HAVE_STDINT_H"
    ENTRY   "1"
    MSG     "to 1 if you have the <stdint.h> header file.")

#==============================================================================#

FIND_HEADER(HEADER_FILE "stdlib.h")
GET_TYPE(HAS HEADER_FILE)
SET_VAR(${HAS}
    LABEL   "HAVE_STDLIB_H"
    NAME    "HAVE_STDLIB_H"
    ENTRY   "1"
    MSG     "to 1 if you have the <stdlib.h> header file.")

#==============================================================================#

FIND_HEADER(HEADER_FILE "strings.h")
GET_TYPE(HAS HEADER_FILE)
SET_VAR(${HAS}
    LABEL   "HAVE_STRINGS_H"
    NAME    "HAVE_STRINGS_H"
    ENTRY   "1"
    MSG     "to 1 if you have the <strings.h> header file.")

#==============================================================================#

FIND_HEADER(HEADER_FILE "string.h")
GET_TYPE(HAS HEADER_FILE)
SET_VAR(${HAS}
    LABEL   "HAVE_STRING_H"
    NAME    "HAVE_STRING_H"
    ENTRY   "1"
    MSG     "to 1 if you have the <string.h> header file.")

#==============================================================================#

FIND_HEADER(HEADER_FILE "sys/stat.h")
GET_TYPE(HAS HEADER_FILE)
SET_VAR(${HAS}
    LABEL   "HAVE_SYS_STAT_H"
    NAME    "HAVE_SYS_STAT_H"
    ENTRY   "1"
    MSG     "to 1 if you have the <sys/stat.h> header file.")

#==============================================================================#

FIND_HEADER(HEADER_FILE "sys/types.h")
GET_TYPE(HAS HEADER_FILE)
SET_VAR(${HAS}
    LABEL   "HAVE_SYS_TYPES_H"
    NAME    "HAVE_SYS_TYPES_H"
    ENTRY   "1"
    MSG     "to 1 if you have the <sys/types.h> header file.")

#==============================================================================#

FIND_HEADER(HEADER_FILE "unistd.h")
GET_TYPE(HAS HEADER_FILE)
SET_VAR(${HAS}
    LABEL   "HAVE_UNISTD_H"
    NAME    "HAVE_UNISTD_H"
    ENTRY   "1"
    MSG     "to 1 if you have the <unistd.h> header file.")

#==============================================================================#

GET_TYPE(HAS wcslib_FOUND)
SET_VAR(${HAS}
    LABEL   "HAVE_WCSLIB"
    NAME    "HAVE_WCSLIB"
    ENTRY   "1"
    MSG     "if you are using wcslib")

#==============================================================================#

FIND_HEADER(HEADER_FILE "wcslib/wcs.h")
GET_TYPE(HAS HEADER_FILE)
SET_VAR(${HAS}
    LABEL   "HAVE_WCSLIB_WCS_H"
    NAME    "HAVE_WCSLIB_WCS_H"
    ENTRY   "1"
    MSG     "to 1 if you have the <wcslib/wcs.h> header file.")

#==============================================================================#

GET_TYPE(HAS USE_MKL)
SET_VAR(${HAS}
    LABEL   "HAVE_MKL"
    NAME    "HAVE_MKL"
    ENTRY   "1"
    MSG     "if you are using MKL")

#==============================================================================#

GET_TYPE(HAS Threads_FOUND)
SET_VAR(${HAS}
    LABEL   "HAVE_PTHREAD"
    NAME    "HAVE_PTHREAD"
    ENTRY   "1"
    MSG     "if you have POSIX threads libraries and header files. ")

#==============================================================================#

GET_TYPE(HAS OpenMP_FOUND)
SET_VAR(${HAS}
    LABEL   "HAVE_OPENMP"
    NAME    "HAVE_OPENMP"
    ENTRY   "1"
    MSG     "if OpenMP is enabled.")

#==============================================================================#

FIND_HEADER(MKL_DFTI_FILE "mkl_dfti.h")
GET_TYPE(HAS MKL_DFTI_FILE)
SET_VAR(${HAS}
    LABEL   "HAVE_MKL_DFTI_H"
    NAME    "HAVE_MKL_DFTI_H"
    ENTRY   "1"
    MSG     "if to 1 if you have the <mkl_dfti.h> header file.")

#==============================================================================#

STRING(TOLOWER "${CMAKE_PROJECT_NAME}" LOWER_CMAKE_PROJECT_NAME)
SET_VAR(DEFINE
    NAME    "PACKAGE"
    ENTRY   "\"${LOWER_CMAKE_PROJECT_NAME}\""
    LABEL   "PACKAGE"
    MSG     "of package")


#==============================================================================#

SET_VAR(DEFINE
    NAME    "PACKAGE_NAME"
    ENTRY   "\"${CMAKE_PROJECT_NAME}\""
    LABEL   "PACKAGE_NAME"
    MSG     "to the full name of the package")

#==============================================================================#

execute_process(COMMAND ${GIT_COMMAND} describe --tags --abbrev=0
    OUTPUT_VARIABLE GIT_LAST_TAG
    OUTPUT_STRIP_TRAILING_WHITESPACE)

execute_process(COMMAND ${GIT_COMMAND} rev-list --count --branches
    OUTPUT_VARIABLE GIT_DEV_NUMBER
    OUTPUT_STRIP_TRAILING_WHITESPACE)

SET_VAR(DEFINE
    NAME    "PACKAGE_VERSION"
    ENTRY   "\"${GIT_LAST_TAG}.dev${GIT_DEV_NUMBER}\""
    LABEL   "PACKAGE_VERSION"
    MSG     "to the version of this package.")

#==============================================================================#

execute_process(COMMAND ${GIT_COMMAND} remote get-url origin
    OUTPUT_VARIABLE GIT_URL
    OUTPUT_STRIP_TRAILING_WHITESPACE)

SET_VAR(DEFINE
    NAME    "PACKAGE_URL"
    ENTRY   "\"${GIT_URL}\""
    LABEL   "PACKAGE_URL"
    MSG     "to the home page for this package.")

#==============================================================================#

STRING(REPLACE "/" ";" GIT_TARNAME "${GIT_URL}")
LIST(LENGTH GIT_TARNAME GIT_TARNAME_LENGTH)
MATH(EXPR GIT_TARNAME_LENGTH "${GIT_TARNAME_LENGTH}-1")
LIST(GET GIT_TARNAME ${GIT_TARNAME_LENGTH} GIT_TARNAME) 
STRING(REPLACE ".git" "" GIT_TARNAME "${GIT_TARNAME}")

SET_VAR(DEFINE
    NAME    "PACKAGE_TARNAME"
    ENTRY   "\"${GIT_TARNAME}\""
    LABEL   "PACKAGE_TARNAME"
    MSG     "to the one symbol short name of this package.")

#==============================================================================#






















STRING(TOLOWER "${PROJECT_NAME}" LOWER_PROJECT_NAME)

# write a build specific config.h header file
write_toast_config_file(
    TEMPLATE
        ${CMAKE_SOURCE_DIR}/cmake/Templates/config.hh.in
    FILE_NAME 
        config.h
    WRITE_PATH 
        ${PROJECT_SOURCE_DIR}
    INSTALL_PATH
        ${CMAKE_INSTALL_CMAKEDIR}/${CMAKE_BUILD_TYPE}/${LOWER_PROJECT_NAME}
    DEFINE_VARS
        "${DEFINE_VARIABLES}"
    UNDEFINE_VARS
        "${UNDEFINE_VARIABLES}"
)


cmake_policy(POP)


