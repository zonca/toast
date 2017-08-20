#
# build cbuffer
#
#------------------------------------------------------------------------------#
#

GLOBAL_OBJECT_TARGET(NAME libtoast-python-object COMPONENTS sources.cmake)

# =============================================================================#
#   configuration files
# =============================================================================#
set(TOAST_LIB ${CMAKE_SHARED_LIBRARY_PREFIX}${PROJECT_NAME}${CMAKE_SHARED_LIBRARY_SUFFIX})
set(LIBTOAST_PATH ${CMAKE_INSTALL_FULL_LIBDIR}/${TOAST_LIB})
if(USE_MPI)
    set(HAVE_MPI True)
else()
    set(HAVE_MPI False)
endif()

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
