# generates svn_version.cc if it does not exist

execute_process(COMMAND ${CMAKE_COMMAND}
                        -DPROJECT_NAME=${PROJECT_NAME}
                        -DMAJOR_VERSION=${${PROJECT_NAME}_VERSION_MAJOR}
                        -DMINOR_VERSION=${${PROJECT_NAME}_VERSION_MINOR}
                        -DPATCH_VERSION=${${PROJECT_NAME}_VERSION_PATCH}
                        -DOUTPUT_DIR=${CMAKE_SOURCE_DIR}/source
                        -P ${CMAKE_SOURCE_DIR}/cmake/Scripts/Version.cmake
)
