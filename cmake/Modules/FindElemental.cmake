#
# Module for locating Elemental.
#
# Customizable variables:
#   Elemental_ROOT
#       Specifies Elemental's root directory.
#
# Read-only variables:
#   Elemental_FOUND
#       Indicates whether the library has been found.
#
#   Elemental_INCLUDE_DIRS
#       Specifies Elemental's include directory.
#
#   Elemental_LIBRARIES
#       Specifies Elemental libraries that should be passed to target_link_libararies.
#
#   Elemental_<COMPONENT>_LIBRARIES
#       Specifies the libraries of a specific <COMPONENT>.
#
#   Elemental_<COMPONENT>_FOUND
#       Indicates whether the specified <COMPONENT> was found.
#
#   Elemental_CXX_LINK_FLAGS
#       C++ linker compile flags
#
# Copyright (c) 2017 Jonathan Madsen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTElementalLAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

INCLUDE (FindPackageHandleStandardArgs)


#----- Elemental installation root
FIND_PATH (Elemental_ROOT
  NAMES include/elemental.h
  PATHS ${Elemental_ROOT}
        ENV Elemental_ROOT
        ENV ElementalROOT
  DOC "Elemental root directory")


#----- Elemental include directory
FIND_PATH (Elemental_INCLUDE_DIR
  NAMES elemental.h
  HINTS ${Elemental_ROOT}
  PATH_SUFFIXES include
  DOC "Elemental include directory")


#----- Elemental library
FIND_LIBRARY (Elemental_LIBRARY
  NAMES elemental
  HINTS ${Elemental_ROOT}
  PATH_SUFFIXES ${CMAKE_INSTALL_LIBDIR_DEFAULT} lib lib64
  DOC "Elemental library")


#----- Determine library's version
SET (_Elemental_VERSION_HEADER ${Elemental_INCLUDE_DIR}/version.h)

IF (EXISTS ${_Elemental_VERSION_HEADER})
    FILE (READ ${_Elemental_VERSION_HEADER} _Elemental_VERSION_CONTENTS)

    STRING (REGEX REPLACE ".*#define __INTEL_Elemental__[ \t]+([0-9]+).*" "\\1"
        Elemental_VERSION_MAJOR "${_Elemental_VERSION_CONTENTS}")
    STRING (REGEX REPLACE ".*#define __INTEL_Elemental_MINOR__[ \t]+([0-9]+).*" "\\1"
        Elemental_VERSION_MINOR "${_Elemental_VERSION_CONTENTS}")
    STRING (REGEX REPLACE ".*#define __INTEL_Elemental_UPDATE__[ \t]+([0-9]+).*" "\\1"
        Elemental_VERSION_PATCH "${_Elemental_VERSION_CONTENTS}")

    SET (Elemental_VERSION ${Elemental_VERSION_MAJOR}.${Elemental_VERSION_MINOR}.${Elemental_VERSION_PATCH})
    SET (Elemental_VERSION_COMPONENTS 3)
ENDIF (EXISTS ${_Elemental_VERSION_HEADER})


FIND_PACKAGE_HANDLE_STANDARD_ARGS (Elemental REQUIRED_VARS Elemental_ROOT
    Elemental_INCLUDE_DIR Elemental_LIBRARY VERSION_VAR Elemental_VERSION)

MARK_AS_ADVANCED (Elemental_INCLUDE_DIR Elemental_LIBRARY)

SET (Elemental_INCLUDE_DIRS ${Elemental_INCLUDE_DIR})
SET (Elemental_LIBRARIES ${Elemental_LIBRARY})

