#------------------------------------------------------------------------------
# Top Level CMakeLists.txt for ${PROJECT_NAME} Build
#
# 15th Jan 2015 Jonathan Madsen
#
#





# - Enforce an out-of-source builds before anything else
#
if(${CMAKE_SOURCE_DIR} STREQUAL ${CMAKE_BINARY_DIR})
	message(STATUS "")
	message(STATUS "")
    message(STATUS "\tProject requires an out-of-source build.")
    message(STATUS "\tPlease remove these files from ${CMAKE_BINARY_DIR} first:")
    message(STATUS "\t\tCMakeCache.txt")
    message(STATUS "\t\tCMakeFiles")
    message(STATUS "\tOnce these files are removed, create a separate directory")
    message(STATUS "\tand run CMake from there")
	message(STATUS "")
	message(STATUS "")
    message(FATAL_ERROR "in-source build detected")
endif()





# - Define CMake requirements and override make rules as needed
#
cmake_minimum_required(VERSION 2.8.8 FATAL_ERROR)
set(CMAKE_USER_MAKE_RULES_OVERRIDE_CXX
	${CMAKE_SOURCE_DIR}/cmake/Modules/MakeRules_cxx.cmake)
# - Project definition
#
project(SAMPLE_PROJECT)
# - Prepend our own CMake Modules to the search path
# This allows us to customize, add, and factor out functionality
# NB: if our custom modules include others that we don't supply, those in the
# base path will be used, so watch for incompatibilities!!
#
set(CMAKE_MODULE_PATH
    ${PROJECT_SOURCE_DIR}/cmake/Modules
    ${CMAKE_MODULE_PATH})





# - Default variables
set(EXE_NAME my_exe)
set(LIB_NAME MYLIB)
set(MAIN_PATH ${PROJECT_SOURCE_DIR})
set(MAIN ${MAIN_PATH}/main.cc)
STRING(TOLOWER "${PROJECT_NAME}" LC_PROJECT_NAME)




# - Include statements
include(CMakeDependentOption)
include(GenericCMakeOptions)
include(GenericCMakeFunctions)
include(MacroUtilities)
# Provide an 'uninstall' target.
include(CMakeUninstallTarget)
# Provide options to control how libraries are built
include(LibraryBuildOptions)
# Provide standard install directories permitting customization.
include(InstallDirs)
# using some the includes from above
OPTION_SET_BUILD_RPATH(ON)
add_feature(DEBUG_SECTIONS "Semi-colon delimited list of sections to debug. Forces compilation with -D_DEBUG_\${LIST_MEMBER} - ${DEBUG_SECTIONS}")

foreach(_section ${DEBUG_SECTIONS})
  string(TOUPPER "${_section}" _section)
  add_definitions(-D_DEBUG_${_section})
endforeach()



# - Versioning
SET_PROJECT_VERSION("1" "0" "0" "${PROJECT_NAME} is a C++ package")




# Additional search paths
include(ConfigureSearchPaths)
# Configure required components
include(RequiredComponents)
# Configure optional components (specifically the testing components)
include(OptionalComponents)
# include the external directories
include_directories(${EXTERNAL_INCLUDE_DIRS})
# generate svn_version.cc
include(SVN_Update)
# generate version.hh
include(Version_Update)



# for updating svn_version.cc
add_custom_target(dummy ALL
                  COMMAND ${CMAKE_COMMAND}
                          -DROOT_DIR=${CMAKE_SOURCE_DIR}
                          -DOUTPUT_DIR=${PROJECT_SOURCE_DIR}/source
                          -P ${CMAKE_SOURCE_DIR}/cmake/Scripts/SVN_Version.cmake
                  COMMAND ${CMAKE_COMMAND}
                          -DPROJECT_NAME=${PROJECT_NAME}
                          -DMAJOR_VERSION=${${PROJECT_NAME}_VERSION_MAJOR}
                          -DMINOR_VERSION=${${PROJECT_NAME}_VERSION_MINOR}
                          -DPATCH_VERSION=${${PROJECT_NAME}_VERSION_PATCH}
                          -DOUTPUT_DIR=${CMAKE_SOURCE_DIR}/source
                          -P ${CMAKE_SOURCE_DIR}/cmake/Scripts/Version.cmake
)

################################################################################
#
#		LIBRARIES AND EXECUTABLES
#
################################################################################

message(STATUS "SYSTEM NAME : ${CMAKE_SYSTEM_NAME}")
# Add the source and environments subdirectories
add_subdirectory(source)
# get the build tree include directories
get_property(BUILDTREE_INCLUDE_DIRS
             GLOBAL
             PROPERTY BUILDTREE_INCLUDE_DIRS)

# include the build tree include directories and the machine-dependent directory
include_directories(${BUILDTREE_INCLUDE_DIRS})
# get the input, cross-section, and rctr files
file(GLOB INPUTS ${PROJECT_SOURCE_DIR}/inputs/*.inp)

# get the global libraries
get_property(GLOBAL_LINK_LIBRARIES
             GLOBAL
             PROPERTY GLOBAL_EXPORTED_TARGETS)
# get the object libraries
get_property(GLOBAL_OBJECT_TARGETS
             GLOBAL
             PROPERTY GLOBAL_OBJECT_TARGETS)

#------------------------------#
# LIBRARIES and EXECUTABLES
#------------------------------#
# - Each category is built as an object library so linking/compiling
#   a library or executable requires no extra compilation
set(LINK_LIB )
# build shared library
if(BUILD_SHARED_LIBS)
    add_library(${LIB_NAME} SHARED ${GLOBAL_OBJECT_TARGETS})
    target_link_libraries(${LIB_NAME}
                          ${EXTERNAL_LINK_LIBRARIES}
                          ${GLOBAL_LINK_LIBRARIES}
                          ${EXTRA_LIBS}
                         )
    list(APPEND LIBRARIES ${LIB_NAME})
    set(LINK_LIB ${LIB_NAME})
    add_dependencies(${LIB_NAME} dummy)
    add_dependencies(svn_version dummy)
endif()
# build static library
if(BUILD_STATIC_LIBS)
    add_library(${LIB_NAME}-static STATIC ${GLOBAL_OBJECT_TARGETS})
    target_link_libraries(${LIB_NAME}-static
                          ${EXTERNAL_LINK_LIBRARIES}
                          ${GLOBAL_LINK_LIBRARIES}
                          ${EXTRA_LIBS}
                         )
    list(APPEND LIBRARIES ${LIB_NAME}-static)
    if(NOT BUILD_SHARED)
        set(LINK_LIB ${LIB_NAME}-static)
    endif()
    add_dependencies(${LIB_NAME}-static dummy)
    add_dependencies(svn_version dummy)
endif()
if("${LINK_LIB}" STREQUAL "")
    message(FATAL_ERROR "${EXE_NAME} could not be built because neither ${LIB_NAME} library was specified (i.e. BUILD_SHARED=OFF and BUILD_STATIC=OFF)")
endif()
# build the  executable using the object libraries
add_executable(${EXE_NAME} ${MAIN}
                           ${HEADER_FILES}
                           ${SOURCE_FILES}
                           ${INPUTS}
)
# link the executable to the external libraries
target_link_libraries(${EXE_NAME}
                      ${GLOBAL_LINK_LIBRARIES}
                      ${LINK_LIB}
)

if(NOT APPLE AND BUILD_SHARED_LIBS)
    set_target_properties(${EXE_NAME}
                          PROPERTIES
                            LINK_FLAGS "-fPIC"
    )
endif()

set_property(GLOBAL APPEND PROPERTY EXECUTABLES ${EXE_NAME})

################################################################################





# -- Configuration files
# ${PROJECT_NAME}make.sh, ${PROJECT_NAME}make.csh
include(ConfigurationScript)
# ${LC_PROJECT_NAME}-config
include(ConfigureConfigScript)
# Generate Doxyfile.${PROJECT_NAME}
include(Documentation)
if(DOXYGEN_DOCS)
    Generate_Documentation(Doxyfile.${PROJECT_NAME})
    if(EXISTS ${PROJECT_SOURCE_DIR}/doc/manual.tex)
        Generate_Manual(manual.tex doc/manual "")
    endif()
endif()

#set(INSTALL_SCRIPTS ${PROJECT_NAME}make.sh ${PROJECT_NAME}make.csh ${LC_PROJECT_NAME}-config)
#set(TEST_SCRIPTS test.py)





# Source groups for IDEs
source_group("Inputs" FILES ${INPUTS})
source_group("Source files" FILES ${MAIN})





# Final output - show what's been enabled so that user knows what's
# happening - also useful for later problem solving!
#
message(STATUS "")
PRINT_ENABLED_FEATURES()
PRINT_DISABLED_FEATURES()
message(STATUS "Build Type : ${CMAKE_BUILD_TYPE}")

set(INSTALL_HEADERS )
foreach(_header ${HEADER_FILES})
	get_filename_component(_install_header ${_header} NAME)
	list(APPEND INSTALL_HEADERS ${_install_header})
endforeach()





# header files to install
get_property(HEADER_FILES GLOBAL PROPERTY INSTALL_HEADER_FILES)
# data/input files to install
set(_share_files )
foreach(_type INPUTS)
    foreach(_file ${${_type}})
        get_filename_component(_file ${_file} NAME)
        list(APPEND _share_files inputs/${_file})
    endforeach()
endforeach()
# executables to install
get_property(EXECUTABLES GLOBAL PROPERTY EXECUTABLES)




# Install under CMAKE_INSTALL_PREFIX
install(TARGETS  ${EXECUTABLES}   DESTINATION  ${CMAKE_INSTALL_BINDIR}      )
install(FILES    ${HEADER_FILES}  DESTINATION  ${CMAKE_INSTALL_INCLUDEDIR}  )
install(TARGETS  ${LIBRARIES}     DESTINATION  ${CMAKE_INSTALL_LIBDIR}      )
install(FILES    ${_share_files}      DESTINATION  ${CMAKE_INSTALL_DATAROOTDIR} )

message(STATUS "CMAKE_INSTALL_PREFIX : \"${CMAKE_INSTALL_PREFIX}\"")
#if(NOT SET_BUILD_RPATH)
#    message(STATUS "Add \"${CMAKE_INSTALL_PREFIX}/lib\" to LD_LIBRARY_PATH (Linux) or DYLD_LIBRARY_PATH (MacOSX) after \"make install\"")
#endif()

message(STATUS "Copying input files to ${PROJECT_BINARY_DIR}")
foreach(_type INPUTS)
    set(resources )
    foreach(_file ${${_type}})
        list(APPEND resources ${_file})
        string(REPLACE "${PROJECT_SOURCE_DIR}/" "" _file ${_file})
        configure_file(${PROJECT_SOURCE_DIR}/${_file}
                       ${PROJECT_BINARY_DIR}/${_file}
                       COPYONLY)
    endforeach()
endforeach()






if(${PROJECT_NAME}_ENABLE_TESTING)
  if(NOT "${INPUTS}" STREQUAL "")
      enable_testing()
      set(MPI_EXEC_CMD "${MPIEXEC} -np")

      list(SORT INPUTS)
      set(_test_num "1")
      foreach(_input ${INPUTS})
        set(_tmp_work_dir "Test_${_test_num}")
        get_filename_component(_input ${_input} NAME)
        get_filename_component(_test_ext ${_input} NAME)
        #message(STATUS "Adding test Test_${_test_ext}")
        file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/inputs/${_tmp_work_dir})
        set(_name "Test_${_test_ext}")
        string(REPLACE "." "_" _name ${_name})
          add_test(NAME ${_name}
                   WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
                   COMMAND test.py
                           --exe=${CMAKE_BINARY_DIR}/${EXE_NAME}
                           --working_directory=${CMAKE_BINARY_DIR}/inputs/${_tmp_work_dir}
                           --inputs_directory=${CMAKE_SOURCE_DIR}/inputs
                           --mpi_cmd=${MPI_EXEC_CMD}
                           --files ${_input}
          )
          set_tests_properties(${name} PROPERTIES TIMEOUT 1800.)
          math(EXPR _test_num "${_test_num} + 1")
        endforeach()

      if(BUILD_TESTS)
        find_program(CTEST_EXE ctest)
        if("${CTEST_EXE}" STREQUAL "CTEST_EXE-NOTFOUND")
          message(FATAL_ERROR "The ctest executable could not be found. Please set BUILD_TESTS to OFF and run manually")
        else()
          set(test_cmd_args "--output-on-failure -O ctest_output.out -j2")
          add_custom_target(run_tests ALL
                            COMMAND
                              ${CTEST_EXE} --output-on-failure -O ctest_output.out -j2
                            DEPENDS
                              ${EXE_NAME}
                            WORKING_DIRECTORY
                              ${CMAKE_BINARY_DIR}
                            COMMENT
                              "\nRunning \"${CTEST_EXE} ${test_cmd_args}\" ... To disable to the automatic running of tests set BUILD_TESTS=OFF"
                            VERBATIM
          )
        endif() # ${CTEST_EXE} STREQUAL CTEST_EXE-NOTFOUND
      endif() # BUILD_TESTS

      if(NOT BUILD_TESTS)
        message(STATUS "Testing is enabled. To run regression tests, from the build directory, enter: ")
        message(STATUS "\t\"ctest $<ARGUMENTS>\", e.g. \"ctest --output-on-failure -O ctest_output.out\"")
      endif()
  endif()
endif()



