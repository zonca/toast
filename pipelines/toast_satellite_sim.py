#!/usr/bin/env python

# Copyright (c) 2015-2017 by the parties listed in the AUTHORS file.
# All rights reserved.  Use of this source code is governed by 
# a BSD-style license that can be found in the LICENSE file.

from toast.mpi import MPI

import os

import re
import argparse

import pickle

import numpy as np

import toast
import toast.tod as tt
import toast.map as tm

import toast.qarray as qa

from toast.vis import set_backend


def main():

    if MPI.COMM_WORLD.rank == 0:
        print("Running with {} processes".format(MPI.COMM_WORLD.size))

    global_start = MPI.Wtime()

    parser = argparse.ArgumentParser( description="Simulate satellite "
        "boresight pointing and make a noise map.", fromfile_prefix_chars="@" )

    parser.add_argument( "--groupsize", required=False, type=int, default=0, 
        help="size of processor groups used to distribute observations" )

    parser.add_argument( "--samplerate", required=False, type=float, 
        default=40.0, help="Detector sample rate (Hz)" )

    parser.add_argument( "--starttime", required=False, type=float, 
        default=0.0, help="The overall start time of the simulation" )
    
    parser.add_argument( "--spinperiod", required=False, type=float, 
        default=10.0, help="The period (in minutes) of the rotation about the "
        "spin axis" )
    parser.add_argument( "--spinangle", required=False, type=float, 
        default=30.0, help="The opening angle (in degrees) of the boresight "
        "from the spin axis" )
    
    parser.add_argument( "--precperiod", required=False, type=float, 
        default=50.0, help="The period (in minutes) of the rotation about the "
        "precession axis" )
    parser.add_argument( "--precangle", required=False, type=float, 
        default=65.0, help="The opening angle (in degrees) of the spin axis "
        "from the precession axis" )
    
    parser.add_argument( "--hwprpm", required=False, type=float, 
        default=0.0, help="The rate (in RPM) of the HWP rotation" )
    parser.add_argument( "--hwpstep", required=False, default=None, 
        help="For stepped HWP, the angle in degrees of each step" )
    parser.add_argument( "--hwpsteptime", required=False, type=float, 
        default=0.0, help="For stepped HWP, the the time in seconds between "
        "steps" )

    parser.add_argument( "--obs", required=False, type=float, default=1.0, 
        help="Number of hours in one science observation" )
    parser.add_argument( "--gap", required=False, type=float, default=0.0, 
        help="Cooler cycle time in hours between science obs" )
    parser.add_argument( "--numobs", required=False, type=int, default=1, 
        help="Number of complete observations" )
    
    parser.add_argument( "--outdir", required=False, default="out", 
        help="Output directory" )
    parser.add_argument( "--debug", required=False, default=False, 
        action="store_true", help="Write diagnostics" )

    parser.add_argument( "--nside", required=False, type=int, default=64, 
        help="Healpix NSIDE" )
    parser.add_argument( "--subnside", required=False, type=int, default=4, 
        help="Distributed pixel sub-map NSIDE" )

    parser.add_argument( "--baseline", required=False, type=float, 
        default=60.0, help="Destriping baseline length (seconds)" )
    parser.add_argument( "--noisefilter", required=False, default=False, 
        action="store_true", help="Destripe with the noise filter enabled" )

    parser.add_argument( "--madam", required=False, default=False, 
        action="store_true", help="If specified, use libmadam for map-making" )
    parser.add_argument( "--madampar", required=False, default=None, 
        help="Madam parameter file" )

    parser.add_argument( "--MC_start", required=False, type=int, default=0, 
        help="First Monte Carlo noise realization" )
    parser.add_argument( "--MC_count", required=False, type=int, default=1, 
        help="Number of Monte Carlo noise realizations" )
    
    parser.add_argument( "--fp", required=False, default=None, 
        help="Pickle file containing a dictionary of detector properties.  "
        "The keys of this dict are the detector names, and each value is also "
        "a dictionary with keys \"quat\" (4 element ndarray), \"fwhm\" "
        "(float, arcmin), \"fknee\" (float, Hz), \"alpha\" (float), and \"NET\" "
        "(float).  For optional plotting, the key \"color\" can specify a "
        "valid matplotlib color string." )

    parser.add_argument('--tidas',
                        required=False, default=None,
                        help='Output TIDAS export path')
    
    args = parser.parse_args()

    if args.tidas is not None:
        if not tt.tidas_available:
            raise RuntimeError("TIDAS not found- cannot export")

    groupsize = args.groupsize
    if groupsize == 0:
        groupsize = MPI.COMM_WORLD.size

    # This is the 2-level toast communicator.

    if MPI.COMM_WORLD.size % groupsize != 0:
        if MPI.COMM_WORLD.rank == 0:
            print("WARNING:  process groupsize does not evenly divide into "
                "total number of processes")
    comm = toast.Comm(world=MPI.COMM_WORLD, groupsize=groupsize)

    # get options

    hwpstep = None
    if args.hwpstep is not None:
        hwpstep = float(args.hwpstep)

    npix = 12 * args.nside * args.nside

    subnside = args.subnside
    if subnside > args.nside:
        subnside = args.nside
    subnpix = 12 * subnside * subnside

    submap = npix // subnpix

    start = MPI.Wtime()

    fp = None

    # Load focalplane information

    if comm.comm_world.rank == 0:
        if args.fp is None:
            # in this case, create a fake detector at the boresight
            # with a pure white noise spectrum.
            fake = {}
            fake["quat"] = np.array([0.0, 0.0, 1.0, 0.0])
            fake["fwhm"] = 30.0
            fake["fknee"] = 0.0
            fake["alpha"] = 1.0
            fake["NET"] = 1.0
            fake["color"] = "r"
            fp = {}
            fp["bore"] = fake
        else:
            with open(args.fp, "rb") as p:
                fp = pickle.load(p)
    fp = comm.comm_world.bcast(fp, root=0)

    stop = MPI.Wtime()
    elapsed = stop - start
    if comm.comm_world.rank == 0:
        print("Create focalplane:  {:.2f} seconds".format(stop-start))
    start = stop

    if args.debug:
        if comm.comm_world.rank == 0:
            outfile = "{}_focalplane.png".format(args.outdir)
            set_backend()
            tt.plot_focalplane(fp, 10.0, 10.0, outfile)

    # Since we are simulating noise timestreams, we want
    # them to be contiguous and reproducible over the whole
    # observation.  We distribute data by detector within an
    # observation, so ensure that our group size is not larger
    # than the number of detectors we have.

    if groupsize > len(fp.keys()):
        if comm.comm_world.rank == 0:
            print("process group is too large for the number of detectors")
            comm.comm_world.Abort()

    # Detector information from the focalplane

    detectors = sorted(fp.keys())
    detquats = {}
    detindx = None
    if "index" in fp[detectors[0]]:
        detindx = {}

    for d in detectors:
        detquats[d] = fp[d]["quat"]
        if detindx is not None:
            detindx[d] = fp[d]["index"]

    # Distribute the observations uniformly

    groupdist = toast.distribute_uniform(args.numobs, comm.ngroups)

    # Compute global time and sample ranges of all observations

    obsrange = tt.regular_intervals(args.numobs, args.starttime, 0, 
        args.samplerate, 3600*args.obs, 3600*args.gap)

    # Create the noise model used for all observations

    fmin = {}
    fknee = {}
    alpha = {}
    NET = {}
    rates = {}
    for d in detectors:
        rates[d] = args.samplerate
        fmin[d] = fp[d]["fmin"]
        fknee[d] = fp[d]["fknee"]
        alpha[d] = fp[d]["alpha"]
        NET[d] = fp[d]["NET"]

    noise = tt.AnalyticNoise(rate=rates, fmin=fmin, detectors=detectors, 
        fknee=fknee, alpha=alpha, NET=NET)

    # The distributed timestream data

    data = toast.Data(comm)
    
    # Every process group creates its observations

    group_firstobs = groupdist[comm.group][0]
    group_numobs = groupdist[comm.group][1]

    for ob in range(group_firstobs, group_firstobs + group_numobs):
        tod = tt.TODSatellite(
            comm.comm_group, 
            detquats,
            obsrange[ob].samples,
            firsttime=obsrange[ob].start,
            rate=args.samplerate,
            spinperiod=args.spinperiod,
            spinangle=args.spinangle,
            precperiod=args.precperiod,
            precangle=args.precangle,
            detindx=detindx,
            detranks=comm.group_size
        )

        obs = {}
        obs["name"] = "science_{:05d}".format(ob)
        obs["tod"] = tod
        obs["intervals"] = None
        obs["baselines"] = None
        obs["noise"] = noise
        obs["id"] = ob

        data.obs.append(obs)

    stop = MPI.Wtime()
    elapsed = stop - start
    if comm.comm_world.rank == 0:
        print("Read parameters, compute data distribution:  "
            "{:.2f} seconds".format(stop-start))
    start = stop

    # we set the precession axis now, which will trigger calculation
    # of the boresight pointing.

    for ob in range(group_numobs):
        curobs = data.obs[ob]
        tod = curobs["tod"]

        # Constantly slewing precession axis
        degday = 360.0 / 365.25
        precquat = tt.slew_precession_axis(nsim=tod.local_samples[1], 
            firstsamp=tod.local_samples[0], samplerate=args.samplerate, 
            degday=degday)

        tod.set_prec_axis(qprec=precquat)

    stop = MPI.Wtime()
    elapsed = stop - start
    if comm.comm_world.rank == 0:
        print("Construct boresight pointing:  "
            "{:.2f} seconds".format(stop-start))
    start = stop

    # make a Healpix pointing matrix.

    pointing = tt.OpPointingHpix(nside=args.nside, nest=True, mode="IQU", 
        hwprpm=args.hwprpm, hwpstep=hwpstep, hwpsteptime=args.hwpsteptime)
    pointing.exec(data)

    comm.comm_world.barrier()
    stop = MPI.Wtime()
    elapsed = stop - start
    if comm.comm_world.rank == 0:
        print("Pointing generation took {:.3f} s".format(elapsed))
    start = stop

    # Mapmaking.  For purposes of this simulation, we use detector noise
    # weights based on the NET (white noise level).  If the destriping
    # baseline is too long, this will not be the best choice.

    detweights = {}
    for d in detectors:
        net = fp[d]["NET"]
        detweights[d] = 1.0 / (args.samplerate * net * net)

    if not args.madam:
        if comm.comm_world.rank == 0:
            print("Not using Madam, will only make a binned map!")

        # get locally hit pixels
        lc = tm.OpLocalPixels()
        localpix = lc.exec(data)

        # find the locally hit submaps.
        localsm = np.unique(np.floor_divide(localpix, submap))

        # construct distributed maps to store the covariance,
        # noise weighted map, and hits

        invnpp = tm.DistPixels(comm=comm.comm_group, size=npix, nnz=6, 
            dtype=np.float64, submap=submap, local=localsm)
        hits = tm.DistPixels(comm=comm.comm_group, size=npix, nnz=1, 
            dtype=np.int64, submap=submap, local=localsm)
        zmap = tm.DistPixels(comm=comm.comm_group, size=npix, nnz=3, 
            dtype=np.float64, submap=submap, local=localsm)

        # compute the hits and covariance once, since the pointing and noise
        # weights are fixed.

        invnpp.data.fill(0.0)
        hits.data.fill(0)

        build_invnpp = tm.OpAccumDiag(detweights=detweights, invnpp=invnpp, 
            hits=hits)
        build_invnpp.exec(data)

        invnpp.allreduce()
        hits.allreduce()

        comm.comm_world.barrier()
        stop = MPI.Wtime()
        elapsed = stop - start
        if comm.comm_world.rank == 0:
            print("Building hits and N_pp^-1 took {:.3f} s".format(elapsed))
        start = stop

        hits.write_healpix_fits("{}_hits.fits".format(args.outdir))
        invnpp.write_healpix_fits("{}_invnpp.fits".format(args.outdir))

        comm.comm_world.barrier()
        stop = MPI.Wtime()
        elapsed = stop - start
        if comm.comm_world.rank == 0:
            print("Writing hits and N_pp^-1 took {:.3f} s".format(elapsed))
        start = stop

        # invert it
        tm.covariance_invert(invnpp, 1.0e-3)

        comm.comm_world.barrier()
        stop = MPI.Wtime()
        elapsed = stop - start
        if comm.comm_world.rank == 0:
            print("Inverting N_pp^-1 took {:.3f} s".format(elapsed))
        start = stop

        invnpp.write_healpix_fits("{}_npp.fits".format(args.outdir))

        comm.comm_world.barrier()
        stop = MPI.Wtime()
        elapsed = stop - start
        if comm.comm_world.rank == 0:
            print("Writing N_pp took {:.3f} s".format(elapsed))
        start = stop

        # in debug mode, print out data distribution information
        if args.debug:
            handle = None
            if comm.comm_world.rank == 0:
                handle = open("{}_distdata.txt".format(args.outdir), "w")
            data.info(handle)
            if comm.comm_world.rank == 0:
                handle.close()
            
            comm.comm_world.barrier()
            stop = MPI.Wtime()
            elapsed = stop - start
            if comm.comm_world.rank == 0:
                print("Dumping debug data distribution took "
                    "{:.3f} s".format(elapsed))
            start = stop

        mcstart = start

        # Loop over Monte Carlos

        firstmc = int(args.MC_start)
        nmc = int(args.MC_count)

        for mc in range(firstmc, firstmc+nmc):
            # create output directory for this realization
            outpath = "{}_{:03d}".format(args.outdir, mc)
            if comm.comm_world.rank == 0:
                if not os.path.isdir(outpath):
                    os.makedirs(outpath)

            comm.comm_world.barrier()
            stop = MPI.Wtime()
            elapsed = stop - start
            if comm.comm_world.rank == 0:
                print("Creating output dir {:04d} took {:.3f} s".format(mc, 
                    elapsed))
            start = stop

            # clear all noise data from the cache, so that we can generate
            # new noise timestreams.
            tod.cache.clear("noise_.*")

            # simulate noise

            nse = tt.OpSimNoise(out="noise", realization=mc)
            nse.exec(data)

            if mc == firstmc:
                # For the first realization, optionally export the 
                # timestream data to a TIDAS volume.
                if args.tidas is not None:
                    from toast.tod.tidas import OpTidasExport
                    tidas_path = os.path.abspath(args.tidas)
                    export = OpTidasExport(tidas_path, name="noise")
                    export.exec(data)

            comm.comm_world.barrier()
            stop = MPI.Wtime()
            elapsed = stop - start
            if comm.comm_world.rank == 0:
                print("  Noise simulation {:04d} took {:.3f} s".format(mc, 
                    elapsed))
            start = stop

            zmap.data.fill(0.0)
            build_zmap = tm.OpAccumDiag(zmap=zmap, name="noise")
            build_zmap.exec(data)
            zmap.allreduce()

            comm.comm_world.barrier()
            stop = MPI.Wtime()
            elapsed = stop - start
            if comm.comm_world.rank == 0:
                print("  Building noise weighted map {:04d} took {:.3f} s".format(
                    mc, elapsed))
            start = stop

            tm.covariance_apply(invnpp, zmap)

            comm.comm_world.barrier()
            stop = MPI.Wtime()
            elapsed = stop - start
            if comm.comm_world.rank == 0:
                print("  Computing binned map {:04d} took {:.3f} s".format(mc,
                    elapsed))
            start = stop
        
            zmap.write_healpix_fits(os.path.join(outpath, "binned.fits"))

            comm.comm_world.barrier()
            stop = MPI.Wtime()
            elapsed = stop - start
            if comm.comm_world.rank == 0:
                print("  Writing binned map {:04d} took {:.3f} s".format(mc, 
                    elapsed))
            elapsed = stop - mcstart
            if comm.comm_world.rank == 0:
                print("  Mapmaking {:04d} took {:.3f} s".format(mc, elapsed))
            start = stop

    else:

        # Set up MADAM map making.

        pars = {}

        cross = args.nside // 2

        pars[ "temperature_only" ] = "F"
        pars[ "force_pol" ] = "T"
        pars[ "kfirst" ] = "T"
        pars[ "concatenate_messages" ] = "T"
        pars[ "write_map" ] = "T"
        pars[ "write_binmap" ] = "T"
        pars[ "write_matrix" ] = "T"
        pars[ "write_wcov" ] = "T"
        pars[ "write_hits" ] = "T"
        pars[ "nside_cross" ] = cross
        pars[ "nside_submap" ] = subnside

        if args.madampar is not None:
            pat = re.compile(r"\s*(\S+)\s*=\s*(\S+(\s+\S+)*)\s*")
            comment = re.compile(r"^#.*")
            with open(args.madampar, "r") as f:
                for line in f:
                    if comment.match(line) is None:
                        result = pat.match(line)
                        if result is not None:
                            key, value = result.group(1), result.group(2)
                            pars[key] = value

        pars[ "base_first" ] = args.baseline
        pars[ "nside_map" ] = args.nside
        if args.noisefilter:
            pars[ "kfilter" ] = "T"
        else:
            pars[ "kfilter" ] = "F"
        pars[ "fsample" ] = args.samplerate

        # Loop over Monte Carlos

        firstmc = int(args.MC_start)
        nmc = int(args.MC_count)

        for mc in range(firstmc, firstmc+nmc):
            # clear all noise data from the cache, so that we can generate
            # new noise timestreams.
            tod.cache.clear("noise_.*")

            # simulate noise

            nse = tt.OpSimNoise(out="noise", realization=mc)
            nse.exec(data)

            comm.comm_world.barrier()
            stop = MPI.Wtime()
            elapsed = stop - start
            if comm.comm_world.rank == 0:
                print("Noise simulation took {:.3f} s".format(elapsed))
            start = stop

            # create output directory for this realization
            pars[ "path_output" ] = "{}_{:03d}".format(args.outdir, mc)
            if comm.comm_world.rank == 0:
                if not os.path.isdir(pars["path_output"]):
                    os.makedirs(pars["path_output"])

            # in debug mode, print out data distribution information
            if args.debug:
                handle = None
                if comm.comm_world.rank == 0:
                    handle = open(os.path.join(pars["path_output"],
                        "distdata.txt"), "w")
                data.info(handle)
                if comm.comm_world.rank == 0:
                    handle.close()

            madam = tm.OpMadam(params=pars, detweights=detweights, 
                name="noise")
            madam.exec(data)

            comm.comm_world.barrier()
            stop = MPI.Wtime()
            elapsed = stop - start
            if comm.comm_world.rank == 0:
                print("Mapmaking took {:.3f} s".format(elapsed))

    comm.comm_world.barrier()
    stop = MPI.Wtime()
    elapsed = stop - global_start
    if comm.comm_world.rank == 0:
        print("Total Time:  {:.2f} seconds".format(elapsed))
    MPI.Finalize()


if __name__ == "__main__":
    main()

