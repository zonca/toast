#
# build cbuffer
#
#------------------------------------------------------------------------------#
#
set_source_files_properties(cbuffer.c PROPERTIES LANGUAGE C)
add_library(cbuffer-shared SHARED cbuffer.c)
if(CMAKE_C_COMPILER_IS_GNU AND NOT APPLE)
    set(_LINK_FLAGS "-Xlinker -export-dynamic -Wl,-O1 -Wl,-Bsymbolic-functions")
else()
    set(_LINK_FLAGS "")
endif()
set_target_properties(cbuffer-shared
    PROPERTIES OUTPUT_NAME      "cbuffer"
               VERSION          "${${PROJECT_NAME}_SHORT_VERSION}"
               SOVERSION        "${${PROJECT_NAME}_MAJOR_VERSION}"
               LINK_FLAGS       "${_LINK_FLAGS}"
               PREFIX           ""
               SUFFIX           ${DEFAULT_SHARED_LIBRARY_SUFFIX}
               COMPILE_FLAGS    "${CMAKE_C_FLAGS_EXTRA}"
               RPATH            ${CMAKE_INSTALL_FULL_PYTHONDIR}
               LANGUAGE         C)
# py libs
set(PYLIBS )
foreach(_LIB dl util m)
    find_library(${_LIB}_LIBRARY
        NAMES ${_LIB}
        PATH_SUFFIXES ${CMAKE_INSTALL_LIBDIR_DEFAULT} lib lib64)
    if(${_LIB}_LIBRARY)
        list(APPEND PYLIBS ${${_LIB}_LIBRARY})
    endif()
endforeach()
target_link_libraries(cbuffer-shared ${PYLIBS}
    ${PROJECT_LINK_TARGETS}
    ${MPI_C_LIBRARIES} ${MPI_EXTRA_LIBRARY}
    ${PYTHON_LIBRARIES}
    )
install(TARGETS cbuffer-shared DESTINATION ${CMAKE_INSTALL_PYTHONDIR})


# =============================================================================#
#   configuration variables
# =============================================================================#
find_program(GIT_COMMAND git)
mark_as_advanced(GIT_COMMAND)

execute_process(COMMAND ${GIT_COMMAND} describe --tags --abbrev=0
    OUTPUT_VARIABLE GIT_LAST_TAG
    OUTPUT_STRIP_TRAILING_WHITESPACE
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

execute_process(COMMAND ${GIT_COMMAND} rev-list --count --branches
    OUTPUT_VARIABLE GIT_DEV_NUMBER
    OUTPUT_STRIP_TRAILING_WHITESPACE
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

set(VERSION "${GIT_LAST_TAG}.dev${GIT_DEV_NUMBER}")

set(TOAST_LIB "${CMAKE_SHARED_LIBRARY_PREFIX}toast${CMAKE_SHARED_LIBRARY_SUFFIX}")
set(LIBTOAST_PATH ${CMAKE_INSTALL_FULL_LIBDIR}/${TOAST_LIB})
if(USE_MPI)
    set(HAVE_MPI True)
else()
    set(HAVE_MPI False)
endif()

# =============================================================================#
#   configuration files
# =============================================================================#

file(GLOB PYTHON_FILES          ${CMAKE_CURRENT_LIST_DIR}/*.py)
file(GLOB PYTHON_CONFIG_FILES   ${CMAKE_CURRENT_LIST_DIR}/*.py.in)

foreach(PYCONFIG ${PYTHON_CONFIG_FILES})
    get_filename_component(PYCONFIG_NAME ${PYCONFIG} NAME_WE)
    configure_file(${PYCONFIG}
        ${CMAKE_BINARY_DIR}/InstallTreeFiles/${PYCONFIG_NAME}.py
        @ONLY)
    list(APPEND PYTHON_FILES ${CMAKE_BINARY_DIR}/InstallTreeFiles/${PYCONFIG_NAME}.py)
endforeach()

install(FILES ${PYTHON_FILES} DESTINATION ${CMAKE_INSTALL_PYTHONDIR}
    #PERMISSIONS
    #OWNER_READ    GROUP_READ    WORLD_READ
    #OWNER_WRITE
    #OWNER_EXECUTE GROUP_EXECUTE WORLD_EXECUTE
)

# install the python sub-directories
install(DIRECTORY
    ${CMAKE_CURRENT_LIST_DIR}/fod
    ${CMAKE_CURRENT_LIST_DIR}/map
    ${CMAKE_CURRENT_LIST_DIR}/tests
    ${CMAKE_CURRENT_LIST_DIR}/tod
    DESTINATION ${CMAKE_INSTALL_PYTHONDIR})

# ensure all the python files are executable
foreach(DIR fod map tests tod)
    file(GLOB _FILES ${CMAKE_CURRENT_LIST_DIR}/${DIR}/*.py)
    install(FILES ${_FILES} DESTINATION ${CMAKE_INSTALL_PYTHONDIR}/${DIR}
        #PERMISSIONS
        #OWNER_READ    GROUP_READ    WORLD_READ
        #OWNER_WRITE
        #OWNER_EXECUTE GROUP_EXECUTE WORLD_EXECUTE
    )
endforeach()
