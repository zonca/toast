# Copyright (c) 2015 by the parties listed in the AUTHORS file.
# All rights reserved.  Use of this source code is governed by 
# a BSD-style license that can be found in the LICENSE file.


from mpi4py import MPI
from collections import namedtuple

import unittest

import numpy as np


class Comm(object):
    """
    Class which represents a two-level hierarchy of MPI communicators.

    A Comm object splits the full set of processes into groups
    of size "group".  If group_size does not divide evenly
    into the size of the given communicator, then those processes
    remain idle.

    A Comm object stores three MPI communicators:  The "world"
    communicator given here, which contains all processes to
    consider, a "group" communicator (one per group)

    Args:
        world (mpi4py.MPI.Comm): the MPI communicator containing all processes.
        group (int): the size of each process group.
    """

    def __init__(self, world=MPI.COMM_WORLD, groupsize=0):

        self._wcomm = world
        self._wrank = self._wcomm.rank
        self._wsize = self._wcomm.size

        self._gsize = groupsize

        if( (self._gsize < 0) or (self._gsize > self._wsize) ):
            raise ValueError("Invalid groupsize ({}).  Should be between {} and {}.".format(groupsize, 0, self._wsize))

        if self._gsize == 0:
            self._gsize = self._wsize

        self._ngroups = int(self._wsize / self._gsize)
        self._group = int(self._wrank / self._gsize)

        self._grank = self._wrank % self._gsize

        if self._group >= self._ngroups:
            self._group = MPI.UNDEFINED
            self._grank = MPI.UNDEFINED

        self._gcomm = self._wcomm.Split(self._group, self._grank)
        self._rcomm = self._wcomm.Split(self._grank, self._group)

    @property
    def world_size(self):
        """
        The size of the world communicator.
        """
        return self._wsize

    @property
    def world_rank(self):
        """
        The rank of this process in the world communicator.
        """
        return self._wrank

    @property
    def ngroups(self):
        """
        The number of process groups.
        """
        return self._ngroups

    @property
    def group(self):
        """
        The group containing this process.
        """
        return self._group

    @property
    def group_size(self):
        """
        The size of the group containing this process.
        """
        return self._gsize

    @property
    def group_rank(self):
        """
        The rank of this process in the group communicator.
        """
        return self._grank

    @property
    def comm_world(self):
        """
        The world communicator.
        """
        return self._wcomm

    @property
    def comm_group(self):
        """
        The communicator shared by processes within this group.
        """
        return self._gcomm

    @property
    def comm_rank(self):
        """
        The communicator shared by processes with the same group_rank.
        """
        return self._rcomm


# This is effectively the "Painter's Partition Problem".

def distribute_required_groups(A, max_per_group):
    ngroup = 1
    total = 0
    for i in range(A.shape[0]):
        total += A[i]
        if total > max_per_group:
            total = A[i]
            ngroup += 1
    return ngroup

def distribute_partition(A, k):
    low = np.max(A)
    high = np.sum(A)
    while low < high:
        mid = low + int((high - low) / 2)
        required = distribute_required_groups(A, mid)
        if required <= k:
            high = mid
        else:
            low = mid + 1
    return low

def distribute_discrete(sizes, groups, pow=1.0):
    chunks = np.array(sizes, dtype=np.int64)
    weights = np.power(chunks.astype(np.float64), pow)
    max_per_proc = distribute_partition(weights.astype(np.int64), groups)

    dist = []
    gchunks = []

    gcur = []
    off = 0
    cur = 0
    curweight = 0
    for i in range(weights.shape[0]):
        if curweight + weights[i] > max_per_proc:
            dist.append( (off, cur) )
            gchunks.append(gcur)
            off += cur
            cur = 0
            curweight = 0
            gcur = []
        cur += chunks[i]
        curweight += weights[i]
        gcur.append(chunks[i])

    dist.append( (off, cur) )
    gchunks.append(gcur)

    return dist, gchunks


def distribute_uniform(totalsize, groups):
    """
    Uniformly distribute items between groups.

    Given some number of items and some number of groups,
    distribute the items between groups in the most Uniform
    way possible.

    Args:
        totalsize (int): The total number of items.
        groups (int): The number of groups.

    Returns:
        list of tuples: there is one tuple per group.  The 
        first element of the tuple is the first item 
        assigned to the group, and the second element is 
        the number of items assigned to the group. 
    """
    ret = []
    for i in range(groups):
        myn = totalsize // groups
        off = 0
        leftover = totalsize % groups
        if ( i < leftover ):
            myn = myn + 1
            off = i * myn
        else:
            off = ((myn + 1) * leftover) + (myn * (i - leftover))
        ret.append( (off, myn) )
    return ret


def distribute_det_samples(mpicomm, timedist, detectors, samples, sizes=None):
    dist_dets = detectors
    dist_samples = (0, samples)
    dist_sizes = sizes

    if timedist:
        if sizes is not None:
            dist_all, dist_allsizes = distribute_discrete(sizes, mpicomm.size)
            dist_sizes = dist_allsizes[mpicomm.rank]
        else:
            dist_all = distribute_uniform(samples, mpicomm.size)
        dist_samples = dist_all[mpicomm.rank]
    else:
        dist_detsindx = distribute_uniform(len(detectors), mpicomm.size)[mpicomm.rank]
        dist_dets = detectors[dist_detsindx[0]:dist_detsindx[0]+dist_detsindx[1]]

    return (dist_dets, dist_samples, dist_sizes)


Obs = namedtuple('Obs', ['tod', 'intervals', 'baselines', 'noise'])

class Data(object):
    """
    Class which represents distributed data

    A Data object contains a list of observations assigned to
    each process group in the Comm.

    Args:
        comm (toast.Comm): the toast Comm class for distributing the data.
    """

    def __init__(self, comm=Comm()):

        self._comm = comm
        self.obs = []

    @property
    def comm(self):
        """
        The toast.Comm over which the data is distributed.
        """
        return self._comm
