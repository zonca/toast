#
# build cbuffer
#
#------------------------------------------------------------------------------#
#

GLOBAL_OBJECT_TARGET(NAME libtoast-python-object COMPONENTS sources.cmake)

# =============================================================================#
#   configuration variables
# =============================================================================#
find_program(GIT_COMMAND git)

execute_process(COMMAND ${GIT_COMMAND} describe --tags --abbrev=0
    OUTPUT_VARIABLE GIT_LAST_TAG
    OUTPUT_STRIP_TRAILING_WHITESPACE
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

execute_process(COMMAND ${GIT_COMMAND} rev-list --count --branches
    OUTPUT_VARIABLE GIT_DEV_NUMBER
    OUTPUT_STRIP_TRAILING_WHITESPACE
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

set(VERSION "${GIT_LAST_TAG}.dev${GIT_DEV_NUMBER}")

set(TOAST_LIB ${CMAKE_SHARED_LIBRARY_PREFIX}${PROJECT_NAME}${CMAKE_SHARED_LIBRARY_SUFFIX})
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
    PERMISSIONS
    OWNER_READ    GROUP_READ    WORLD_READ
    OWNER_WRITE
    OWNER_EXECUTE GROUP_EXECUTE WORLD_EXECUTE)

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
        PERMISSIONS
        OWNER_READ    GROUP_READ    WORLD_READ
        OWNER_WRITE
        OWNER_EXECUTE GROUP_EXECUTE WORLD_EXECUTE)
endforeach()
