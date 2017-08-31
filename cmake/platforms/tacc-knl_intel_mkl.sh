#!/bin/bash

# This script assumes that the "toast-deps" module has been loaded.
# To install to my scratch directory, I might run this script with:
#
# $> ./cmake/platforms/tacc-knl_intel_mkl.sh \
#    -DCMAKE_PREFIX_PATH=$SCRATCH/software/toast-knl
#

echo "THIS SCRIPT REQUIRES CROSS-COMPILING! The current cmake configuration doesn't support this yet!"
exit 1

ROOT=${PWD}
DIR=${PWD}/build-toast/tacc-knl-intel-mkl/release
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
    -DUSE_MKL=ON -DMKL_ROOT=${TACC_INTEL_DIR}/linux/mkl \
    -DUSE_TBB=ON -DTBB_ROOT=${TACC_INTEL_DIR}/linux/tbb \
    -DUSE_MATH=ON \
    -DCMAKE_TOOLCHAIN_FILE=${ROOT}/Toolchains/TACC-KNL.cmake \ # to be written later
    -DTARGET_ARCHITECTURE=knl \
    ${OPTS} ${ROOT}


