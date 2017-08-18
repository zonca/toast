cmake_minimum_required(VERSION 3.1.3 FATAL_ERROR)

project(TOAST C CXX)

set(CMAKE_MODULE_PATH 
    ${PROJECT_SOURCE_DIR}/cmake/${PROJECT_NAME} 
    ${PROJECT_SOURCE_DIR}/cmake/Modules 
    ${CMAKE_MODULE_PATH})

set(CMAKE_USER_MAKE_RULES_OVERRIDE_CXX
    ${CMAKE_SOURCE_DIR}/cmake/Modules/MakeRulesCXX.cmake)

include(MakeRulesCXX)
include(GenericCMakeFunctions)
SET_PROJECT_VERSION("2" "2" "0" "Time Ordered Astrophysics Scalable Tools")
SET(CMAKE_POSITION_INDEPENDENT_CODE ON)
SET(CMAKE_INSTALL_MESSAGE LAZY)
STRING(TOUPPER "${CMAKE_BUILD_TYPE}" UPPER_BUILD_TYPE)

include(InstallDirs)
include(GenericCMakeOptions)
include(LibraryBuildOptions)
include(Packages)
include(MacroUtilities)

add_feature(CMAKE_INSTALL_PREFIX "Installation prefix")
add_feature(CMAKE_CXX_FLAGS "CXX flags")
add_feature(CMAKE_BUILD_TYPE "Build type")
add_feature(CMAKE_CXX_FLAGS_${UPPER_BUILD_TYPE} "CXX flags for ${CMAKE_BUILD_TYPE}")

foreach(_INCLUDE_DIR ${EXTERNAL_INCLUDE_DIRS})
    include_directories(SYSTEM ${_INCLUDE_DIR})
endforeach()
include_directories(${PROJECT_SOURCE_DIR})

#-----------------------------------------------------------------------
# BUILD_CXXSTD
# Choose C++ Standard to build against, if supported.
# Mark as advanced because most users will not need it.
include(ConfigureCXXSTD)

add_subdirectory(src)

#------------------------------------------------------------------------------#

print_features()

include(CMakeUninstallTarget)

