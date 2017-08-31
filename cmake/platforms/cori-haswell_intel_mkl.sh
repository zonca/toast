#!/bin/bash

# This script assumes that the "toast-deps" module has been loaded.
# To install to my scratch directory, I might run this script with:
#
# $> ./cmake/platforms/cori-haswell_intel_mkl.sh \
#    -DCMAKE_PREFIX_PATH=$SCRATCH/software/toast-haswell
#

ROOT=${PWD}
DIR=${PWD}/build-toast/cori-haswell-intel-mkl/release
OPTS="$@"

export CC=$(which icc)
export CXX=$(which icpc)
export MPICC=$(which icc)
export MPICXX=$(which icpc)

# ${OPTS} at end because last -D overrides any previous -D with same name
# on command line (e.g. -DUSE_MPI=OFF -DUSE_MPI=OFF --> USE_MPI == OFF)
mkdir -p ${DIR} 
cd ${DIR}
cmake -DCMAKE_BUILD_TYPE=Release -DUSE_OPENMP=ON \
    -DUSE_MKL=ON -DMKL_ROOT=${INTEL_PATH}/linux/mkl \
    -DUSE_TBB=ON -DTBB_ROOT=${INTEL_PATH}/linux/tbb \
    -DUSE_MATH=ON \
    -DTARGET_ARCHITECTURE=haswell \
    ${OPTS} ${ROOT}

