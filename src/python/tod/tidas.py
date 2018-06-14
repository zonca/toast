# Copyright (c) 2015-2017 by the parties listed in the AUTHORS file.
# All rights reserved.  Use of this source code is governed by
# a BSD-style license that can be found in the LICENSE file.

from ..mpi import MPI, MPILock

import sys
import os
import re

import numpy as np

from .. import qarray as qa
from .. import timing as timing

from ..dist import Data, distribute_discrete
from ..op import Operator

from .tod import TOD
from .interval import Interval

available = True
try:
    import tidas as tds
    from tidas.mpi import MPIVolume
except:
    available = False


# Module-level constants

STR_QUAT = "QUAT"
STR_FLAG = "FLAG"
STR_COMMON = "COMMON"
STR_BORE = "BORE"
STR_POS = "POS"
STR_VEL = "VEL"
STR_DISTINTR = "chunks"
STR_DETGROUP = "detectors"


def create_tidas_schema(detlist, datatype, units):
    """
    Create a schema for a list of detectors.

    All detector timestreams will be set to the same type and units.  A flag
    field will be created for each detector.  Additional built-in fields will
    also be added to the schema.

    Args:
        detlist (list): a list of detector names
        datatype (tidas.DataType): the tidas datatype assigned to all detector
            fields.
        units (str): the units string assigned to all data fields.

    Returns (tidas.Schema):
        Schema containing the data and flag fields.
    """
    fields = list()
    for c in ["X", "Y", "Z", "W"]:
        f = "{}_{}{}".format(STR_BORE, STR_QUAT, c)
        fields.append( tds.Field(f, tds.DataType.float64, "NA") )

    for c in ["X", "Y", "Z"]:
        f = "{}{}".format(STR_POS, c)
        fields.append( tds.Field(f, tds.DataType.float64, "NA") )

    for c in ["X", "Y", "Z"]:
        f = "{}{}".format(STR_VEL, c)
        fields.append( tds.Field(f, tds.DataType.float64, "NA") )

    fields.append( tds.Field("{}_{}".format(STR_FLAG, STR_COMMON),
        tds.DataType.uint8, "NA") )

    for d in detlist:
        fields.append( tds.Field(d, datatype, units) )
        fields.append( tds.Field("{}_{}".format(STR_FLAG, d),
            tds.DataType.uint8, "NA") )

    return tds.Schema(fields)


def create_tidas_obs(vol, parent, name, groups=None, intervals=None):
    """
    Create a single TIDAS block that represents an observation.

    This creates a new block to represent an observation, and then creates
    zero or more groups and intervals inside that block.  When writing to a
    new TIDAS volume, this function can be used in the pipeline script
    to set up the "leaf nodes" of the volume, each of which is a single
    observation.

    The detector group will have additional fields added to the schema
    that are expected by the TODTidas class for boresight pointing and
    telescope position / velocity.

    NOTE: This function should only be called by one process, for example,
    the root process of the group communicator for the group that will be
    assigned this observation.

    Args:
        vol (tidas.MPIVolume):  the volume.
        parent (str):  the path to the parent block.
        name (str):  the name of the observation block.
        groups (dict):  dictionary where the key is the group name and the
            value is a tuple containing the (tidas.Schema, tidas.Dictionary,
            size) of the group.  The objects in the tuple are exactly the
            arguments to the constructor of the tidas.Group object.
        intervals (dict):  dictionary where the key is the intervals name
            and the value is a tuple containing the (tidas.Dictionary, size) of
            the intervals.  The objects in the tuple are exactly the arguments
            to the constructor of the tidas.Intervals object.
        detgroup (str):  The name of the TIDAS group containing detector
            and other telescope information at the detector sample rate.
            If there is only one data group, then this is optional.

    Returns (tidas.Block):
        The newly created block.
    """
    if not available:
        raise RuntimeError("tidas is not available")
        return

    autotimer = timing.auto_timer()
    # The root block
    root = vol.root()

    par = root
    if parent != "":
        # Descend tree to the parent node
        parentnodes = parent.split("/")
        for pn in parentnodes:
            if pn != "":
                par = par.block_get(pn)

    # Create the observation block
    obs = par.block_add(name, tds.Block())

    # Create the groups
    if groups is not None:
        for grp, args in groups.items():
            g = obs.group_add(grp, tds.Group(args[0], args[1], args[2]))

    # Create the intrvals
    if intervals is not None:
        for intrvl, args in intervals.items():
            intr = obs.intervals_add(intrvl,
                tds.Intervals(args[0], args[1]))

    return obs


def decode_tidas_quats(props):
    """
    Read detector quaternions from a TIDAS property dictionary.

    This extracts and assembles the quaternion offsets for each detector from
    the metadata properties from a TIDAS group.

    Args:
        props (tidas.Dictionary):  the dictionary of properties associated with
            a TIDAS detector group.

    Returns (dict):
        a dictionary of detectors and their quaternions, each stored as a 4
        element numpy array.
    """
    autotimer = timing.auto_timer()
    quatpat = re.compile(r"(.*)_{}([XYZW])".format(STR_QUAT))
    loc = {"X":0, "Y":1, "Z":2, "W":3}
    quats = {}

    # Extract all quaternions from the properties based on the key names
    for key in props.keys():
        mat = quatpat.match(key)
        if mat is not None:
            det = mat.group(1)
            comp = mat.group(2)
            if det not in quats:
                quats[det] = np.zeros(4, dtype=np.float64)
            quats[det][loc[comp]] = props.get_float64(key)

    return quats


def encode_tidas_quats(detquats, props=None):
    """
    Append detector quaternions to a dictionary.

    This takes a dictionary of detector quaternions and encodes the elements
    into named dictionary values suitable for creating a TIDAS group.  The
    entries are merged with the input dictionary and the result is returned.

    This extracts and assembles the quaternion offsets for each detector from
    the metadata of a particular group (the one containing the detector data).

    Args:
        detquats (dict):  a dictionary with keys of detector names and values
            containing 4-element numpy arrays with the quaternion.
        props (tidas.Dictionary):  the starting dictionary of properties.
            The updated properties are returned.

    Returns (tidas.Dictionary):
        a dictionary of detector quaternion values appended to the input.
    """
    autotimer = timing.auto_timer()
    ret = props
    if ret is None:
        ret = tds.Dictionary()

    qname = ["X", "Y", "Z", "W"]
    for det, quat in detquats.items():
        for q in range(4):
            key = "{}_{}{}".format(det, STR_QUAT, qname[q])
            ret.put_float64(key, float(quat[q]))

    return ret


class TODTidas(TOD):
    """
    This class provides an interface to a single TIDAS data block.

    An instance of this class reads and writes to a single TIDAS block which
    represents a TOAST observation.  The volume and specific block should
    already exist.  Groups and intervals within the observation may already
    exist or may be created with the provided helper methods.  All groups
    and intervals must exist prior to reading or writing from them.

    Detector pointing offsets from the boresight are given as quaternions,
    and are expected to be contained in the dictionary of properties
    found in the TIDAS group containing detector timestreams.

    Args:
        mpicomm (mpi4py.MPI.Comm): the MPI communicator over which this
            observation data is distributed.
        vol (tidas.MPIVolume):  the volume.
        path (str):  the path to this observation block.
        detranks (int):  The dimension of the process grid in the detector
            direction.  The MPI communicator size must be evenly divisible
            by this number.
        detbreaks (list):  Optional list of hard breaks in the detector
            distribution.
        detgroup (str):  The name of the TIDAS group containing detector
            and other telescope information at the detector sample rate.
            If there is only one data group, then this is optional.
        distintervals (str):  Optional name of the TIDAS intervals that
            determines how the data should be distributed along the time
            axis.  Default is to distribute only by detector.

    """

    # FIXME: currently the data flags are stored in the same group as
    # the data.  Once TIDAS supports per-group backend options like
    # compression, we should move the flags to a separate group:
    #   https://github.com/hpc4cmb/tidas/issues/13

    def __init__(self, mpicomm, vol, path, detranks=1, detbreaks=None,
        detgroup=None, distintervals=None):

        if not available:
            raise RuntimeError("tidas is not available")

        # The root block
        root = vol.root()

        # Descend tree to the observation node
        blk = root
        if path != "":
            nodes = path.split("/")
            for nd in nodes:
                if nd != "":
                    blk = blk.block_get(nd)

        self._block = blk

        # Get the detector group
        self._dgrpname = None
        self._dgrp = None
        grpnames = self._block.group_names()

        if len(grpnames) == 1:
            self._dgrpname = grpnames[0]
            self._dgrp = self._block.group_get(grpnames[0])
        else:
            if detgroup is None:
                raise RuntimeError("You must specify the detector group if "
                    "multiple groups exist")
            else:
                self._dgrpname = detgroup
                self._dgrp = self._block.group_get(detgroup)

        # Get the detector quaternion offsets
        self._detquats = decode_tidas_quats(self._dgrp.dictionary())
        self._detlist = sorted(list(self._detquats.keys()))

        # We need to assign a unique integer index to each detector.  This
        # is used when seeding the streamed RNG in order to simulate
        # timestreams.  For simplicity, and assuming that detector names
        # are not too long, we can convert the detector name to bytes and
        # then to an integer.

        self._detindx = {}
        for det in self._detlist:
            bdet = det.encode("utf-8")
            ind = None
            try:
                ind = int.from_bytes(bdet, byteorder="little")
            except:
                raise RuntimeError("Cannot convert detector name {} to a "
                    "unique integer- maybe it is too long?".format(det))
            self.detindx[det] = ind

        # Create an MPI lock to use for writing to the TIDAS volume.  We must
        # have only one writing process at a time.  Note that this lock is over
        # the communicator for this single observation (TIDAS block).
        # Processes writing to separate blocks have no restrictions.

        self._writelock = MPILock(mpicomm)

        # read intervals and set up distribution chunks.

        sampsizes = None
        self._distintervals = None
        self._intervals = None
        self._distint = None

        if distintervals is not None:
            self._distintervals = distintervals
            self._distint = self._block.intervals_get(distintervals)
            # Rank zero process reads and broadcasts intervals
            if mpicomm.rank == 0:
                self._intervals = self._distint.read()
            self._intervals = mpicomm.bcast(self._intervals, root=0)
            # Compute the contiguous spans of time for data distribution
            # based on the starting points of all intervals.
            sampsizes = [ (x[1].first - x[0].first) for x in
                zip(self._intervals[:-1], self._intervals[1:]) ]
            sampsizes.append( self._dgrp.size() -
                self._intervals[-1].first )

        # Convert the group metadata into a python dictionary
        meta = dict()
        td = self._dgrp.dictionary()
        for k in td.keys():
            tp = td.get_type(k)
            if (tp == "d"):
                meta[k] = td.get_float64(k)
            elif (tp == "f"):
                meta[k] = td.get_float32(k)
            elif (tp == "l"):
                meta[k] = td.get_int64(k)
            elif (tp == "L"):
                meta[k] = td.get_uint64(k)
            elif (tp == "i"):
                meta[k] = td.get_int32(k)
            elif (tp == "I"):
                meta[k] = td.get_uint32(k)
            elif (tp == "h"):
                meta[k] = td.get_int16(k)
            elif (tp == "H"):
                meta[k] = td.get_uint16(k)
            elif (tp == "b"):
                meta[k] = td.get_int8(k)
            elif (tp == "B"):
                meta[k] = td.get_uint8(k)
            else:
                meta[k] = td.get_string(k)

        # call base class constructor to distribute data
        super().__init__(mpicomm, self._detlist, self._dgrp.size(),
            detindx=self._detindx, detranks=detranks, detbreaks=detbreaks,
            sampsizes=sampsizes, meta=meta)


    @property
    def block(self):
        """
        The TIDAS block for this TOD.

        This can be used for arbitrary access to other groups and intervals
        associated with this observation.
        """
        return self._block


    @property
    def group(self):
        """
        The TIDAS group for the detectors in this TOD.
        """
        return self._dgrp


    @property
    def groupname(self):
        """
        The TIDAS group name for the detectors in this TOD.
        """
        return self._dgrpname


    def detoffset(self):
        """
        Return dictionary of detector quaternions.

        This returns a dictionary with the detector names as the keys and the
        values are 4-element numpy arrays containing the quaternion offset
        from the boresight.

        Args:
            None

        Returns (dict):
            the dictionary of quaternions.
        """
        return dict(self._detquats)


    def _read_cache_helper(self, prefix, comps, start, n, usecache):
        """
        Helper function to read multi-component data, pack into an
        array, optionally cache it, and return.
        """
        autotimer = timing.auto_timer(type(self).__name__)
        # Number of components we have
        ncomp = len(comps)

        # Compute the sample offset of our local data
        offset = self.local_samples[0] + start

        if self.cache.exists(prefix):
            return self.cache.reference(prefix)[start:start+n,:]
        else:
            if usecache:
                # We cache the whole observation, regardless of what sample
                # range we will return.
                data = self.cache.create(prefix, np.float64,
                    (self.local_samples[1], ncomp))
                for c in range(ncomp):
                    field = "{}{}".format(prefix, comps[c])
                    d = self._dgrp.read(field, offset, self.local_samples[1])
                    data[:,c] = d
                # Return just the desired slice
                return data[start:start+n,:]
            else:
                # Read and return just the slice we want
                data = np.zeros((n, ncomp), dtype=np.float64)
                for c in range(ncomp):
                    field = "{}{}".format(prefix, comps[c])
                    d = self._dgrp.read(field, offset, n)
                    dat[:,c] = d
                return data


    def _write_helper(self, data, prefix, comps, start):
        """
        Helper function to write multi-component data.
        """
        # Number of components we have
        ncomp = len(comps)

        # Compute the sample offset of our local data
        offset = self.local_samples[0] + start

        tmpdata = np.empty(data.shape[0], dtype=data.dtype, order="C")
        for c in range(ncomp):
            field = "{}{}".format(prefix, comps[c])
            tmpdata[:] = data[:,c]
            self._dgrp.write(field, offset, tmpdata)

        return


    def _get_boresight(self, start, n, usecache=True):
        # Cache name
        cachebore = "{}_{}".format(STR_BORE, STR_QUAT)
        # Read and optionally cache the boresight pointing.
        return self._read_cache_helper(cachebore, ["X", "Y", "Z", "W"],
            start, n, usecache)


    def _put_boresight(self, start, data):
        # Data name
        borename = "{}_{}".format(STR_BORE, STR_QUAT)
        # Write data
        #self._writelock.lock()
        self._write_helper(data, borename, ["X", "Y", "Z", "W"],
            start)
        #self._writelock.unlock()
        return


    def _get(self, detector, start, n):
        # Compute the sample offset of our local data
        offset = self.local_samples[0] + start
        # Read from the data group and return
        return self._dgrp.read(detector, offset, n)


    def _put(self, detector, start, data):
        # Compute the sample offset of our local data
        offset = self.local_samples[0] + start
        # Write to the data group
        #self._writelock.lock()
        self._dgrp.write(detector, offset, data)
        #self._writelock.unlock()
        return


    def _get_flags(self, detector, start, n):
        # Field name
        field = "{}_{}".format(STR_FLAG, detector)
        # Compute the sample offset of our local data
        offset = self.local_samples[0] + start
        return self._dgrp.read(field, offset, n)


    def _put_flags(self, detector, start, flags):
        # Field name
        field = "{}_{}".format(STR_FLAG, detector)
        # Compute the sample offset of our local data
        offset = self.local_samples[0] + start
        # Write to the data group
        #self._writelock.lock()
        self._dgrp.write(field, offset, flags)
        #self._writelock.unlock()
        return


    def _get_common_flags(self, start, n):
        # Field name
        field = "{}_{}".format(STR_FLAG, STR_COMMON)
        # Compute the sample offset of our local data
        offset = self.local_samples[0] + start
        # Read from the data group and return
        return self._dgrp.read(field, offset, n)


    def _put_common_flags(self, start, flags):
        # Field name
        field = "{}_{}".format(STR_FLAG, STR_COMMON)
        # Compute the sample offset of our local data
        offset = self.local_samples[0] + start
        # Write to the data group
        #self._writelock.lock()
        self._dgrp.write(field, offset, flags)
        #self._writelock.unlock()
        return


    def _get_times(self, start, n):
        # Compute the sample offset of our local data
        offset = self.local_samples[0] + start
        return self._dgrp.read_times(offset, n)


    def _put_times(self, start, stamps):
        # Compute the sample offset of our local data
        offset = self.local_samples[0] + start
        # Write to the data group
        #self._writelock.lock()
        self._dgrp.write_times(offset, stamps)
        #self._writelock.unlock()
        return


    def _get_pntg(self, detector, start, n):
        # Get boresight pointing (from disk or cache)
        bore = self._get_boresight(start, n)
        # Apply detector quaternion and return
        return qa.mult(bore, self._detquats[detector])


    def _put_pntg(self, detector, start, data):
        raise RuntimeError("TODTidas computes detector pointing on the fly."
            " Use the write_boresight() method instead.")
        return


    def _get_position(self, start, n, usecache=False):
        # Read and optionally cache the telescope position.
        return self._read_cache(STR_POS, ["X", "Y", "Z"], start, n, usecache)


    def _put_position(self, start, pos):
        #self._writelock.lock()
        self._write_helper(pos, STR_POS, ["X", "Y", "Z"], start)
        #self._writelock.unlock()
        return


    def _get_velocity(self, start, n, usecache=False):
        # Read and optionally cache the telescope velocity.
        return self._read_cache(STR_VEL, ["X", "Y", "Z"], start, n, usecache)


    def _put_velocity(self, start, vel):
        #self._writelock.lock()
        self._write_helper(vel, STR_VEL, ["X", "Y", "Z"], start)
        #self._writelock.unlock()
        return


def load_tidas(comm, path, mode="r", detranks=1, detbreaks=None, detgroup=None,
    distintervals=None):
    """
    Loads an existing TOAST dataset in TIDAS format.

    This takes a 2-level TOAST communicator and opens an existing TIDAS
    volume using the global communicator.  The opened volume handle is stored
    in the observation dictionary with the "tidas" key.  Similarly, the
    metadata path to the block within the volume is stored in the
    "tidas_block" key.

    The leaf nodes of the hierarchy are assumed to be the "observations".
    the observations are assigned to the process groups in a load-balanced
    way based on the number of samples in each detector group.

    For each observation, the TOD data distribution parameters and the group
    communicator are passed to the TODTidas class.

    Args:
        comm (toast.Comm): the toast Comm class for distributing the data.
        path (str):  the TIDAS volume path.
        mode (string): whether to open the file in read-only ("r") or
                       read-write ("w") mode.  Default is read-only.
        detranks (int):  The dimension of the process grid in the detector
            direction.  The MPI group communicator size must be evenly
            divisible by this number.
        detbreaks (list):  Optional list of hard breaks in the detector
            distribution.
        detgroup (str):  The name of the TIDAS group containing detector
            and other telescope information at the detector sample rate.
            If there is only one data group, then this is optional.
        distintervals (str):  Optional name of the TIDAS intervals that
            determines how the data should be distributed along the time
            axis.  Default is to distribute only by detector.

    Returns (toast.Data):
        The distributed data object.
    """
    if not available:
        raise RuntimeError("tidas is not available")
        return None
    autotimer = timing.auto_timer()
    # the global communicator
    cworld = comm.comm_world
    # the communicator within the group
    cgroup = comm.comm_group
    # the communicator with all processes with
    # the same rank within their group
    crank = comm.comm_rank

    # Collectively open the volume.  We cannot use a context manager here,
    # since we are keeping a handle to the volume around for future use.
    # This means the volume will remain open for the life of the program,
    # or (hopefully) will get closed if the distributed data object is
    # destroyed.

    tm = None
    if mode == "w":
        tm = tds.AccessMode.write
    else:
        tm = tds.AccessMode.read
    vol = MPIVolume(cworld, path, tm)

    # Traverse the blocks of the volume and get the properties of the
    # observations so we can distribute them.

    obslist = []
    obspath = {}
    obssize = {}

    def procblock(pth, nm, current):
        subs = current.block_names()
        pthnm = "{}/{}".format(pth, nm)
        for s in subs:
            chld = current.block_get(s)
            procblock(pthnm, s, chld)
        if len(subs) == 0:
            # this is a leaf node
            obslist.append(nm)
            obspath[nm] = pthnm
            grpnames = current.group_names()
            grpnm = detgroup
            if len(grpnames) == 1:
                grpnm = grpnames[0]
            grp = current.group_get(grpnm)
            obssize[nm] = grp.size()
        return

    if cworld.rank == 0:
        root = vol.root()
        toplist = root.block_names()
        for b in toplist:
            bk = root.block_get(b)
            procblock("", b, bk)

    obslist = cworld.bcast(obslist, root=0)
    obspath = cworld.bcast(obspath, root=0)
    obssize = cworld.bcast(obssize, root=0)

    # Distribute the observations among groups

    obssizelist = [ obssize[x] for x in obslist ]
    distobs = distribute_discrete(obssizelist, comm.ngroups)

    # Distributed data

    data = Data(comm)

    # Now every group adds its observations to the list

    firstobs = distobs[comm.group][0]
    nobs = distobs[comm.group][1]
    for ob in range(firstobs, firstobs+nobs):
        obs = {}
        obs["name"] = obslist[ob]
        obs["tidas"] = vol
        obs["tidas_block"] = obspath[obslist[ob]]
        obs["tod"] = TODTidas(cgroup, vol, obspath[obslist[ob]],
            detranks=detranks, detgroup=detgroup, distintervals=distintervals)

        gd = obs["tod"].group.dictionary()
        gdk = gd.keys()
        if "obs_id" in gdk:
            obs["id"] = gd.get_int64("obs_id")
        if "obs_telescope_id" in gdk:
            obs["telescope_id"] = gd.get_int64("obs_telescope_id")
        if "obs_site_id" in gdk:
            obs["site_id"] = gd.get_int64("obs_site_id")

        data.obs.append(obs)

    return data


class OpTidasExport(Operator):
    """
    Operator which writes data to a TIDAS volume.

    The volume is created at construction time, and the full metadata
    path inside the volume can be given for each observation.  If not given,
    all observations are exported to TIDAS blocks under the root block.

    Timestream data, flags, and boresight pointing are read from the
    current TOD for the observation and written to the TIDAS TOD.  Data can
    be read directly or copied from the cache.

    Args:
        path (str): the output TIDAS volume path (must not exist).
        backend (str): the TIDAS backend type.
        comp (str): the TIDAS compression type.
        backopts (dict): extra options to the TIDAS backend.
        obspath (dict): (optional) each observation has a "name" and these
            should be the keys of this dictionary.  The values of the dict
            should be the metadata parent path of the observation inside
            the volume.
        name (str): the name of the cache object (<name>_<detector>) to
            use for the detector timestream.  If None, use the TOD.
        common_flag_name (str):  the name of the cache object to use for
            common flags.  If None, use the TOD.
        flag_name (str):  the name of the cache object (<name>_<detector>) to
            use for the detector flags.  If None, use the TOD.
        units (str):  the units of the detector timestreams.
        usedist (bool):  if True, use the TOD total_chunks() method to get
            the chunking used for data distribution and replicate that as a
            set of TIDAS intervals.  Otherwise do not write any intervals
            to the output.
    """
    def __init__(self, path, backend="hdf5", comp="none", backopts=dict(),
        obspath=None, name=None, common_flag_name=None, flag_name=None,
        units="unknown", usedist=False):

        if not available:
            raise RuntimeError("tidas is not available")

        self._path = path.rstrip("/")
        self._backend = None
        if backend == "hdf5":
            self._backend = tds.BackendType.hdf5
        self._comp = None
        if comp == "none":
            self._comp = tds.CompressionType.none
        elif comp == "gzip":
            self._comp = tds.CompressionType.gzip
        elif comp == "bzip2":
            self._comp = tds.CompressionType.bzip2
        self._backopts = backopts
        self._obspath = obspath
        self._cachename = name
        self._cachecomm = common_flag_name
        self._cacheflag = flag_name
        self._usedist = usedist
        self._units = units

        # We call the parent class constructor
        super().__init__()


    def exec(self, data):
        """
        Export data to a TIDAS volume.

        Each group will write its list of observations as TIDAS blocks.

        For errors that prevent the export, this function will directly call
        MPI Abort() rather than raise exceptions.  This could be changed in
        the future if additional logic is implemented to ensure that all
        processes raise an exception when one process encounters an error.

        Args:
            data (toast.Data): The distributed data.
        """
        autotimer = timing.auto_timer(type(self).__name__)
        # the two-level toast communicator
        comm = data.comm
        # the global communicator
        cworld = comm.comm_world
        # the communicator within the group
        cgroup = comm.comm_group
        # the communicator with all processes with
        # the same rank within their group
        crank = comm.comm_rank

        # One process checks that the path is OK
        if cworld.rank == 0:
            dname = os.path.dirname(self._path)
            if not os.path.isdir(dname):
                print("Directory for exported TIDAS volume ({}) does not "
                      "exist".format(dname), flush=True)
                cworld.Abort()
            if os.path.exists(self._path):
                print("Path for exported TIDAS volume ({}) already "
                      "exists".format(self._path), flush=True)
                cworld.Abort()
        cworld.barrier()

        # Collectively create the volume

        vol = MPIVolume(cworld, self._path, self._backend, self._comp,
            self._backopts)

        # First, we go through and add all observations and then sync
        # so that all processes have the full metadata.  Only the root
        # process in each group creates the observations used by that
        # group.

        if cgroup.rank == 0:
            for obs in data.obs:
                # The existing TOD
                tod = obs["tod"]

                # Sanity check- the group communicator should be the same
                comp = MPI.Comm.Compare(tod.mpicomm, cgroup)
                if comp not in (MPI.IDENT, MPI.CONGRUENT):
                    print("On export, original TOD comm is different from "
                        "group comm")
                    cworld.Abort()

                # Get the name
                if "name" not in obs:
                    print("observation does not have a name, cannot export",
                          flush=True)
                    cworld.Abort()
                obsname = obs["name"]

                # Get the metadata path
                blockpath = ""
                if self._obspath is not None:
                    blockpath = self._obspath[obsname]

                detranks, sampranks = tod.grid_size
                rankdet, ranksamp = tod.grid_ranks
                metadata = tod.meta()
                props = tds.Dictionary()
                for key, val in metadata.items():
                    if isinstance(val, float):
                        props.put_float64(key, val)
                    elif isinstance(val, int):
                        props.put_int64(key, val)
                    else:
                        props.put_string(key, str(val))

                # Get the observation ID (used for RNG)
                obsid = 0
                if "id" in obs:
                    obsid = int(obs["id"])
                props.put_int64("obs_id", obsid)

                # Get the telescope ID (used for RNG)
                obstele = 0
                if "telescope_id" in obs:
                    obstele = int(obs["telescope_id"])
                props.put_int64("obs_telescope_id", obstele)

                obssite = 0
                if "site_id" in obs:
                    obssite = int(obs["site_id"])
                props.put_int64("obs_site_id", obssite)

                # Optionally setup intervals for future data distribution
                intervals = None
                if self._usedist:
                    # This means that the distribution chunks in the time
                    # direction were intentional (not just the boundaries of
                    # some uniform distribution), and we want to write them
                    # out to tidas intervals so that we can use them for data
                    # distribution when this volume is read in later.
                    intervals = {STR_DISTINTR : (tds.Dictionary(),
                        len(tod.total_chunks))}

                # Get detector quaternions and encode them for use in the
                # properties of the tidas group.  Combine this with the
                # existing observation properties into a single dictionary.

                props = encode_tidas_quats(tod.detoffset(), props=props)

                # Configure the detector group

                schm = create_tidas_schema(tod.detectors, tds.DataType.float64,
                    self._units)
                groups = {STR_DETGROUP : (schm, props, tod.total_samples)}

                # Create the block in the volume that corresponds to this
                # observation.

                tob = create_tidas_obs(vol, blockpath, obsname, groups=groups,
                    intervals=intervals)

                if self._usedist:
                    # Actually write the interval data that will be used later
                    # for the data distribution.  We don't need the timestamps
                    # here, so set them to -1.
                    it = tob.intervals_get(STR_DISTINTR)
                    tint = list()
                    chfirst = 0
                    for ch in tod.total_chunks:
                        tint.append(tds.Intrvl(-1.0, -1.0, chfirst, chfirst + ch - 1))
                        chfirst = chfirst + ch
                    it.write(tint)

        # Sync metadata so all processes have all metadata.
        vol.meta_sync()

        # Now every process group goes through its observations and
        # actually writes the data.

        for obs in data.obs:
            # Get the name
            obsname = obs["name"]

            # Get the metadata path
            blockpath = obsname
            if self._obspath is not None:
                blockpath = "{}/{}".format(self._obspath[obsname], obsname)

            # The existing TOD
            tod = obs["tod"]
            detranks, sampranks = tod.grid_size
            rankdet, ranksamp = tod.grid_ranks

            # The new TIDAS TOD
            distintervals = None
            if self._usedist:
                distintervals = STR_DISTINTR

            tidastod = TODTidas(tod.mpicomm, vol, blockpath,
                detranks=detranks, detgroup=STR_DETGROUP,
                distintervals=distintervals)

            blk = tidastod.block

            # Some data is common across all processes that share the same
            # time span (timestamps, boresight pointing, common flags).
            # Since we only need to write these once, we let the first
            # process row handle that.

            # We are going to gather the timestamps to a single process
            # since we need them to convert between the existing TOD
            # chunks and times for the intervals.  The interval list is
            # common between all processes.

            if rankdet == 0:
                grp = blk.group_get(STR_DETGROUP)

                # Only the first row of the process grid does this...
                # First process timestamps

                stamps = tod.read_times()
                rowdata = tod.grid_comm_row.gather(stamps, root=0)

                if ranksamp == 0:
                    full = np.concatenate(rowdata)
                    grp.write_times(0, full)
                    if self._usedist:
                        ilist = []
                        off = 0
                        for sz in tod.total_chunks:
                            ilist.append(tds.Intrvl(full[off],
                                full[off+sz-1], off, (off+sz-1)))
                            off += sz
                        intr = blk.intervals_get(STR_DISTINTR)
                        intr.write(ilist)

                    del full
                del rowdata

                # Next the boresight data. Serialize the writing
                for rs in range(sampranks):
                    if ranksamp == rs:
                        tidastod.write_boresight(data=tod.read_boresight())
                    tod.grid_comm_row.barrier()

                # Same with the common flags
                ref = None
                if self._cachecomm is not None:
                    ref = tod.cache.reference(self._cachecomm)
                else:
                    ref = tod.read_common_flags()
                for rs in range(sampranks):
                    if ranksamp == rs:
                        tidastod.write_common_flags(flags=ref)
                    tod.grid_comm_row.barrier()
                del ref

            tod.mpicomm.barrier()

            # Now each process can write their unique data slice.

            # FIXME:  Although every write should be guarded by a mutex
            # lock, this does not seem to work in practice- there is a bug
            # in the MPILock class when applied to HDF5 calls (despite
            # extensive unit tests).  For now, we will serialize writes over
            # the process grid.

            for p in range(tod.mpicomm.size):
                if tod.mpicomm.rank == p:
                    for det in tod.local_dets:
                        ref = None
                        if self._cachename is not None:
                            ref = tod.cache.reference("{}_{}"\
                                .format(self._cachename, det))
                        else:
                            ref = tod.read(detector=det)
                        tidastod.write(detector=det, data=ref)
                        del ref
                        ref = None
                        if self._cacheflag is not None:
                            ref = tod.cache.reference(
                                "{}_{}".format(self._cacheflag, det))
                        else:
                            ref = tod.read_flags(detector=det)
                        tidastod.write_flags(detector=det, flags=ref)
                        del ref
                tod.mpicomm.barrier()

            # for det in tod.local_dets:
            #     ref = None
            #     if self._cachename is not None:
            #         ref = tod.cache.reference("{}_{}"\
            #             .format(self._cachename, det))
            #     else:
            #         ref = tod.read(detector=det)
            #     tidastod.write(detector=det, data=ref)
            #     del ref
            #     ref = None
            #     if self._cacheflag is not None:
            #         ref = tod.cache.reference(
            #             "{}_{}".format(self._cacheflag, det))
            #     else:
            #         ref = tod.read_flags(detector=det)
            #     tidastod.write_flags(detector=det, flags=ref)
            #     del ref

            del tidastod

        del vol

        return
