#
# Module for locating Intel's Math Kernel Library (IMF).
#
# Customizable variables:
#   IMF_ROOT
#       Specifies IMF's root directory.
#
# Read-only variables:
#   IMF_FOUND
#       Indicates whether the library has been found.
#
#   IMF_LIBRARIES
#       Specifies IMF libraries that should be passed to target_link_libararies.
#
#   IMF_CXX_LINK_FLAGS
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
# FITNESS FOR A PARTIMFLAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

INCLUDE (FindPackageHandleStandardArgs)

IF (CMAKE_VERSION VERSION_GREATER 2.8.7)
  SET (_IMF_CHECK_COMPONENTS FALSE)
ELSE (CMAKE_VERSION VERSION_GREATER 2.8.7)
  SET (_IMF_CHECK_COMPONENTS TRUE)
ENDIF (CMAKE_VERSION VERSION_GREATER 2.8.7)


#----- IMF installation root
FIND_PATH (IMF_ROOT
  NAMES include/mathimf.h
  PATHS ${IMF_ROOT}
        ENV IMF_ROOT
        ENV IMFROOT
  DOC "IMF root directory")


#----- IMF include directory
FIND_PATH (IMF_INCLUDE_DIR
  NAMES mathimf.h
  HINTS ${IMF_ROOT}
  PATH_SUFFIXES include
  DOC "IMF include directory")
SET (IMF_INCLUDE_DIRS ${IMF_INCLUDE_DIR})


#----- Library suffix
IF (CMAKE_SIZEOF_VOID_P EQUAL 8)
  SET (_IMF_POSSIBLE_LIB_SUFFIXES lib/intel64 lib/mic)
ELSE (CMAKE_SIZEOF_VOID_P EQUAL 8)
  SET (_IMF_POSSIBLE_LIB_SUFFIXES lib/ia32 lib/mic)
ENDIF (CMAKE_SIZEOF_VOID_P EQUAL 8)
LIST (APPEND _IMF_POSSIBLE_LIB_SUFFIXES lib/$ENV{IMF_ARCH_PLATFORM})


#----- IMF runtime library
FIND_LIBRARY (IMF_LIBRARY
  NAMES imf
  HINTS ${IMF_ROOT}
  PATH_SUFFIXES ${_IMF_POSSIBLE_LIB_SUFFIXES}
  DOC "IMF library")
SET (IMF_LIBRARIES ${IMF_LIBRARY})

FIND_PACKAGE_HANDLE_STANDARD_ARGS (IMF REQUIRED_VARS IMF_ROOT
    IMF_INCLUDE_DIR IMF_LIBRARY)

SET (IMF_INCLUDE_DIRS ${IMF_INCLUDE_DIR})
SET (IMF_LIBRARIES    ${IMF_LIBRARY})

MARK_AS_ADVANCED(IMF_ROOT IMF_INCLUDE_DIR IMF_LIBRARY)

