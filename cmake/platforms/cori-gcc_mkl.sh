#!/bin/bash

# This script assumes that the "toast-deps" module has been loaded.
# To install to my scratch directory, I might run this script with:
#
# $> ./cmake/platforms/cori-gcc_mkl.sh \
#    -DCMAKE_INSTALL_PREFIX=$SCRATCH/software/toast-gcc
#

ROOT=${PWD}
DIR=${PWD}/build-toast/cori-gcc-mkl/release
OPTS="$@"

export CC=$(which gcc)
export CXX=$(which g++)
export MPICC=$(which gcc)
export MPICXX=$(which g++)

# ${OPTS} at end because last -D overrides any previous -D with same name
# on command line (e.g. -DUSE_MPI=OFF -DUSE_MPI=OFF --> USE_MPI == OFF)
mkdir -p ${DIR} 
cd ${DIR}
cmake -DCMAKE_BUILD_TYPE=Release \
    -DUSE_MKL=ON -DMKL_ROOT=${INTEL_PATH}/linux/mkl \
    -DUSE_TBB=ON -DTBB_ROOT=${INTEL_PATH}/linux/tbb \
    ${OPTS} ${ROOT}

