#!/usr/bin/env python

# Copyright (c) 2015-2017 by the parties listed in the AUTHORS file.
# All rights reserved.  Use of this source code is governed by
# a BSD-style license that can be found in the LICENSE file.

# This script creates CES schedule file that can be used as input
# to toast_ground_sim.py

import argparse
from datetime import datetime
import dateutil.parser

import numpy as np
import ephem
from scipy.constants import degree


def to_JD(t):
    # Unix time stamp to Julian date
    # (days since -4712-01-01 12:00:00 UTC)
    return t / 86400. + 2440587.5

def to_MJD(t):
    # Convert Unix time stamp to modified Julian date
    # (days since 1858-11-17 00:00:00 UTC)
    return to_JD(t) - 2400000.5

def to_DJD(t):
    # Convert Unix time stamp to Dublin Julian date
    # (days since 1899-12-31 12:00:00)
    # This is the time format used by PyEphem
    return to_JD(t) - 2415020

def build_schedule(
        start_timestamp, stop_timestamp, gap, gap_small, fn,
        site_name, site_lat, site_lon, site_alt, debug,
        sun_el_max, sun_avoidance_angle,
        sun_angle_min, moon_angle_min,
        el_min, el_max, fp_radius,
        ces_max_time, patches):

    fout = open(fn, 'w')

    fout.write('#{:15} {:15} {:15} {:15}\n'.format(
        'Site', 'Latitude [deg]', 'Longitude [deg]', 'Altitude [m]'))
    fout.write(' {:15} {:15} {:15} {:15.6f}\n'.format(
        site_name, site_lat, site_lon, site_alt))

    fout_fmt0 = '#{:20} {:20} {:14} {:14} ' \
                '{:15} {:8} {:8} {:8} {:5} ' \
                '{:8} {:8} {:8} {:8} ' \
                '{:8} {:8} {:8} {:8} {:5} ' \
                '{:5} {:3}\n'

    fout_fmt = ' {:20} {:20} {:14.6f} {:14.6f} ' \
               '{:15} {:8.2f} {:8.2f} {:8.2f} {:5} ' \
               '{:8.2f} {:8.2f} {:8.2f} {:8.2f} ' \
               '{:8.2f} {:8.2f} {:8.2f} {:8.2f} {:5.2f} ' \
               '{:5} {:3}\n'

    fout.write(
        fout_fmt0.format(
            'Start time UTC', 'Stop time UTC', 'Start MJD', 'Stop MJD',
            'Patch name', 'Az min', 'Az max', 'El', 'R/S',
            'Sun el1', 'Sun az1', 'Sun el2', 'Sun az2',
            'Moon el1', 'Moon az1', 'Moon el2', 'Moon az2', 'Phase',
            'Pass', 'Sub'))

    observer = ephem.Observer()
    observer.lon = site_lon
    observer.lat = site_lat
    observer.elevation = site_alt # In meters
    observer.epoch = '2000'
    observer.temp = 0 # in Celcius
    observer.compute_pressure()

    hits = {}
    for patch in patches:
        hits[patch[0]] = 0

    t = start_timestamp
    sun = ephem.Sun()
    moon = ephem.Moon()
    tstep = 600

    while t < stop_timestamp:
        # Determine which patches are observable at time t.

        if debug:
            tstring = datetime.utcfromtimestamp(t).strftime(
                '%Y-%m-%d %H:%M:%S %Z')
            print('t =  {}'.format(tstring), flush=True)
        # Determine which patches are visible
        observer.date = to_DJD(t)
        sun.compute(observer)
        if sun.alt > sun_el_max:
            if debug:
                print('Sun elevation is {:.2f} > {:.2f}. Moving on.'.format(
                    sun.alt/degree, sun_el_max/degree), flush=True)
            t += tstep
            continue
        moon.compute(observer)

        visible = []
        not_visible = []
        for (name, weight, corners) in patches:
            # Reject all patches that have even one corner too close
            # to the Sun or the Moon and patches that are completely
            # below the horizon
            in_view = False
            ncorner = len(corners)
            for i, corner in enumerate(corners):
                corner.compute(observer)
                if corner.alt > el_min:
                    # At least one corner is visible
                    in_view = True
                if sun.alt > sun_avoidance_angle:
                    # Sun is high enough to apply sun_angle_min check
                    angle = ephem.separation(sun, corner)
                    if angle < sun_angle_min:
                        # Patch is too close to the Sun
                        not_visible.append((
                            name,
                            'Too close to Sun {:.2f}'.format(angle / degree)))
                        in_view = False
                        break
                if moon.alt > 0:
                    angle = ephem.separation(moon, corner)
                    if angle < moon_angle_min:
                        # Patch is too close to the Moon
                        not_visible.append((
                            name,
                            'Too close to Moon {:.2f}'.format(angle / degree)))
                        in_view = False
                        break
                if i == ncorner-1 and not in_view:
                    not_visible.append((
                        name, 'Below the horizon.'))
            if in_view:
                visible.append((name, weight, corners))

        if len(visible) == 0:
            if debug:
                tstring = datetime.utcfromtimestamp(t).strftime(
                    '%Y-%m-%d %H:%M:%S %Z')
                print('No patches visible at {}: {}'.format(tstring, not_visible))
            t += tstep
            continue

        # Order the targets by priority and attempt to observe with both
        # a rising and setting scans until we find one that can be
        # succesfully scanned.
        # If the criteria are not met, advance the time by a step
        # and try again

        for i in range(len(visible)-1):
            for j in range(i+1, len(visible)):
                iname, iweight, icorners = visible[i]
                ihit = hits[iname]
                jname, jweight, jcorners = visible[i]
                jhit = hits[jname]
                if ihit*jweight < jhit*iweight:
                    visible[i], visible[j] = visible[j], visible[i]

        success = False
        for (name, weight, corners) in visible:
            for rising in [True, False]:
                observer.date = to_DJD(t)
                for corner in corners:
                    corner.compute(observer)
                # Then determine an elevation that all corners will cross
                ncorner = len(corners)
                azs = np.zeros(ncorner)
                els = np.zeros(ncorner)
                for i, corner in enumerate(corners):
                    azs[i] = corner.az
                    els[i] = corner.alt
                if rising:
                    ind = azs <= np.pi
                    if np.sum(ind) == 0:
                        not_visible.append((
                            name, 'No rising corners'))
                        continue
                    el = np.amax(els[ind]) + fp_radius
                else:
                    ind = azs >= np.pi
                    if np.sum(ind) == 0:
                        not_visible.append((
                            name, 'No setting corners'))
                        continue
                    el = np.amin(els[ind]) - fp_radius
                if el < el_min:
                    not_visible.append((
                        name,
                        'el < el_min ({:.2f} < {:.2f}) rising = {}'.format(
                            el/degree, el_min/degree, rising)))
                    continue
                if el > el_max:
                    not_visible.append((
                        name,
                        'el > el_max ({:.2f} > {:.2f}) rising = {}'.format(
                            el/degree, el_max/degree, rising)))
                    continue
                azmin = 1e10
                azmax = -1e10
                # and now track when all corners are past the elevation
                tstop = t
                to_cross = np.ones(len(corners), dtype=np.bool)
                old_az = azs.copy()
                old_el = els.copy()
                old_to_cross = to_cross.copy()
                azmins = []
                azmaxs = []
                aztimes = []
                while True:
                    tstop += tstep / 10
                    if tstop > stop_timestamp or tstop - t > 86400:
                        not_visible.append((name, 'Ran out of time rising = {}'
                                            ''.format(rising)))
                        break
                    observer.date = to_DJD(tstop)
                    sun.compute(observer)
                    if sun.alt > sun_el_max:
                        not_visible.append((
                            name,
                            'Sun too high {:.2f} rising = {}'
                            ''.format(sun.alt/degree, rising)))
                        break
                    for i, corner in enumerate(corners):
                        corner.compute(observer)
                        azs[i] = corner.az
                        els[i] = corner.alt
                    if rising:
                        good = azs <= np.pi
                        to_cross[np.logical_and(els > el+fp_radius, good)] \
                            = False
                    else:
                        good = azs >= np.pi
                        to_cross[np.logical_and(els < el-fp_radius, good)] \
                            = False
                    # Find the pairs of corners that are on opposite sides
                    # of the CES line.  Record the crossing azimuth of a
                    # line between the corners.
                    azs_cross = []
                    for i in range(ncorner):
                        j = (i + 1) % ncorner
                        for el0 in [el,
                                    el - fp_radius,
                                    el - fp_radius]:
                            if (els[i] - el0)*(els[j] - el0) < 0:
                                az1 = azs[i]
                                az2 = azs[j]
                                el1 = els[i] - el0
                                el2 = els[j] - el0
                                if az1 - az2 < -2*np.pi:
                                    az2 += 2*np.pi
                                az_cross = az1 + el1*(az2 - az1)/(el1 - el2)
                                if (rising and az_cross <= np.pi) or \
                                   (not rising and az_cross >= np.pi):
                                    azs_cross.append(az_cross)
                    if len(azs_cross) > 0:
                        azs_cross = np.sort(azs_cross)
                        azmins.append(azs_cross[0])
                        azmaxs.append(azs_cross[-1])
                        aztimes.append(tstop)
                    if np.all(np.logical_not(to_cross)):
                        # All corners made it across the CES line.
                        success = True
                        break
                    old_az = azs.copy()
                    old_el = els.copy()
                    old_to_cross = to_cross.copy()
                if success:
                    break
            if not success:
                # CES failed.  Try observing the next patch.
                continue
            ces_time = tstop - t
            if ces_time > ces_max_time:
                nsub = np.int(np.ceil(ces_time / ces_max_time))
                ces_time /= nsub
            aztimes = np.array(aztimes)
            azmins = np.array(azmins)
            azmaxs = np.array(azmaxs)
            rising_string = 'R' if rising else 'S'
            hits[name] += 1
            t1 = t
            isub = -1
            while t1 < tstop:
                isub += 1
                t2 = min(t1 + ces_time, tstop)
                ind = np.logical_and(aztimes >= t1, aztimes <= t2)
                if np.all(aztimes > t2):
                    ind[0] = True
                if np.all(aztimes < t1):
                    ind[-1] = True
                azmin = np.amin(azmins[ind])
                azmax = np.amax(azmaxs[ind])
                # Check if we are scanning across the zero meridian
                if azmax - azmin > np.pi:
                    # we are, scan from the maximum to the minimum
                    azmin = np.amin(azmaxs[ind])
                    azmax = np.amax(azmin[ind])
                # Add the focal plane radius to the scan width
                fp_radius_eff = fp_radius / np.cos(el)
                azmin = (azmin - fp_radius_eff) % (2*np.pi)
                azmax = (azmax + fp_radius_eff) % (2*np.pi)
                ces_start = datetime.utcfromtimestamp(t1).strftime(
                    '%Y-%m-%d %H:%M:%S %Z')
                ces_stop = datetime.utcfromtimestamp(t2).strftime(
                    '%Y-%m-%d %H:%M:%S %Z')
                # Get the Sun and Moon locations at the beginning and end
                observer.date = to_DJD(t1)
                sun.compute(observer)
                moon.compute(observer)
                sun_az1, sun_el1 = sun.az/degree, sun.alt/degree
                moon_az1, moon_el1 = moon.az/degree, moon.alt/degree
                moon_phase1 = moon.phase
                observer.date = to_DJD(t2)
                sun.compute(observer)
                moon.compute(observer)
                sun_az2, sun_el2 = sun.az/degree, sun.alt/degree
                moon_az2, moon_el2 = moon.az/degree, moon.alt/degree
                moon_phase2 = moon.phase
                # Create an entry in the schedule
                fout.write(
                    fout_fmt.format(
                        ces_start, ces_stop, to_MJD(t1), to_MJD(t2),
                        name,
                        azmin/degree, azmax/degree, el/degree,
                        rising_string,
                        sun_el1, sun_az1, sun_el2, sun_az2,
                        moon_el1, moon_az1, moon_el2, moon_az2,
                        0.005*(moon_phase1 + moon_phase2), hits[name], isub))
                t1 = t2 + gap_small
            # Advance the time
            t = tstop
            # Add the gap
            t += gap
            break

        if not success:
            if debug:
                tstring = datetime.utcfromtimestamp(t).strftime(
                    '%Y-%m-%d %H:%M:%S %Z')
                print('No patches could be scanned at {}: {}'.format(
                    tstring, not_visible), flush=True)
            t += tstep

    fout.close()


def main():

    parser = argparse.ArgumentParser(
        description='Generate ground observation schedule.',
        fromfile_prefix_chars='@')

    parser.add_argument('--site_name',
                        required=False, default='LBL',
                        help='Observing site name')
    parser.add_argument('--site_lon',
                        required=False, default='-122.247',
                        help='Observing site longitude [PyEphem string]')
    parser.add_argument('--site_lat',
                        required=False, default='37.876',
                        help='Observing site latitude [PyEphem string]')
    parser.add_argument('--site_alt',
                        required=False, default=100.0, type=np.float,
                        help='Observing site altitude [meters]')
    parser.add_argument('--patch',
                        required=True, action='append',
                        help='Patch definition: '
                        'name,weight,lon1,lat1,lon2,lat2 ... '
                        'OR name,weight,lon,lat,width')
    parser.add_argument('--patch_coord',
                        required=False, default='C',
                        help='Sky patch coordinate system [C,E,G]')
    parser.add_argument('--el_min',
                        required=False, default=30.0, type=np.float,
                        help='Minimum elevation for a CES')
    parser.add_argument('--el_max',
                        required=False, default=80.0, type=np.float,
                        help='Maximum elevation for a CES')
    parser.add_argument('--fp_radius',
                        required=False, default=0.0, type=np.float,
                        help='Focal plane radius [deg]')
    parser.add_argument('--sun_avoidance_angle',
                        required=False, default=-15.0, type=np.float,
                        help='Solar elevation above which to apply '
                        'sun_angle_min [deg]')
    parser.add_argument('--sun_angle_min',
                        required=False, default=30.0, type=np.float,
                        help='Minimum distance between the Sun and '
                        'the bore sight [deg]')
    parser.add_argument('--moon_angle_min',
                        required=False, default=20.0, type=np.float,
                        help='Minimum distance between the Moon and '
                        'the bore sight [deg]')
    parser.add_argument('--sun_el_max',
                        required=False, default=90.0, type=np.float,
                        help='Maximum allowed sun elevation [deg]')
    parser.add_argument('--start',
                        required=False, default='2000-01-01 00:00:00',
                        help='UTC start time of the schedule')
    parser.add_argument('--stop',
                        required=False, default='2000-01-02 00:00:00',
                        help='UTC stop time of the schedule')
    parser.add_argument('--gap',
                        required=False, default=100, type=np.float,
                        help='Gap between CES:es [seconds]')
    parser.add_argument('--gap_small',
                        required=False, default=10, type=np.float,
                        help='Gap between split CES:es [seconds]')
    parser.add_argument('--ces_max_time',
                        required=False, default=900, type=np.float,
                        help='Maximum length of a CES [seconds]')
    parser.add_argument('--debug',
                        required=False, default=False, action='store_true',
                        help='Write diagnostics')
    parser.add_argument('--out',
                        required=False, default='schedule.txt',
                        help='Output filename')

    args = parser.parse_args()

    try:
        start_time = dateutil.parser.parse(args.start + ' +0000')
        stop_time = dateutil.parser.parse(args.stop + ' +0000')
    except:
        start_time = dateutil.parser.parse(args.start)
        stop_time = dateutil.parser.parse(args.stop)

    start_timestamp = start_time.timestamp()
    stop_timestamp = stop_time.timestamp()

    if args.debug:
        import healpy as hp
        import matplotlib.pyplot as plt

    # Parse the patch definitions

    patches = []
    total_weight = 0
    for patch_def in args.patch:
        parts = patch_def.split(',')
        name = parts[0]
        weight = float(parts[1])
        total_weight += weight
        i = 2
        corners = []
        print('Adding patch "{}" {} '.format(name, weight), end='')
        if len(parts[i:]) == 3:
            print('Center-and-width format ', end='')
            # Patch center and width format
            try:
                # Assume coordinates in degrees
                lon = float(parts[i]) * degree
                lat = float(parts[i+1]) * degree
            except:
                # Failed simple interpreration, assume pyEphem strings
                lon = parts[i]
                lat = parts[i+1]
            width = float(parts[i+2]) * degree
            if args.patch_coord == 'C':
                center = ephem.Equatorial(lon, lat, epoch='2000')
            elif args.patch_coord == 'E':
                center = ephem.Ecliptic(lon, lat, epoch='2000')
            elif args.patch_coord == 'G':
                center = ephem.Galactic(lon, lat, epoch='2000')
            else:
                raise RuntimeError('Unknown coordinate system: {}'.format(
                    args.patch_coord))
            center = ephem.Equatorial(center)
            # Synthesize 8 corners around the center
            phi = center.ra
            theta = center.dec
            r = width / 2
            ncorner = 8
            angstep = 2 * np.pi / ncorner
            for icorner in range(ncorner):
                ang = angstep * icorner
                delta_theta = np.cos(ang) * r
                delta_phi = np.sin(ang) * r / np.cos(theta + delta_theta)
                patch_corner = ephem.FixedBody()
                patch_corner._ra = phi + delta_phi
                patch_corner._dec = theta + delta_theta
                corners.append(patch_corner)
        elif len(parts[i:]) == 4:
            print('Rectangular format ', end='')
            # Rectangle format
            try:
                # Assume coordinates in degrees
                lon_min = float(parts[i]) * degree
                lat_max = float(parts[i+1]) * degree
                lon_max = float(parts[i+2]) * degree
                lat_min = float(parts[i+3]) * degree
            except:
                # Failed simple interpreration, assume pyEphem strings
                lon_min = parts[i]
                lat_max = parts[i+1]
                lon_max = parts[i+2]
                lat_min = parts[i+3]
            if args.patch_coord == 'C':
                fun = ephem.Equatorial
            elif args.patch_coord == 'E':
                fun = ephem.Ecliptic
            elif args.patch_coord == 'G':
                fun = ephem.Galactic
            else:
                raise RuntimeError('Unknown coordinate system: {}'.format(
                    args.patch_coord))
            nw_corner = fun(lon_min, lat_max, epoch='2000')
            ne_corner = fun(lon_max, lat_max, epoch='2000')
            se_corner = fun(lon_max, lat_min, epoch='2000')
            sw_corner = fun(lon_min, lat_min, epoch='2000')
            # If the patch is very large, we add extra control points
            # between the corners
            corners_temp = []
            step = 5 * degree
            # NW corner
            corners_temp.append(ephem.Equatorial(nw_corner))
            lat = nw_corner.dec
            step_eff = step / np.cos(lat)
            lon1 = nw_corner.ra
            lon2 = ne_corner.ra
            if lon2 > lon1:
                lon2 -= 2*np.pi
            ninterp = int((lon1 - lon2) // step_eff)
            if ninterp > 0:
                interp_step = (lon1 - lon2) / (ninterp + 1)
                for iinterp in range(ninterp):
                    lon = (lon1 - iinterp*interp_step) % (2*np.pi)
                    corners_temp.append(
                        ephem.Equatorial(fun(lon, lat, epoch='2000')))
            # NE corner
            corners_temp.append(ephem.Equatorial(ne_corner))
            lon = ne_corner.ra
            lat1 = se_corner.dec
            lat2 = ne_corner.dec
            ninterp = int((lat2 - lat1) // step)
            if ninterp > 0:
                interp_step = (lat2 - lat1) / (ninterp + 1)
                for iinterp in range(ninterp):
                    lat = lat2 - iinterp*interp_step
                    corners_temp.append(
                        ephem.Equatorial(fun(lon, lat, epoch='2000')))
            # SE corner
            corners_temp.append(ephem.Equatorial(se_corner))
            lat = se_corner.dec
            step_eff = step / np.cos(lat)
            lon1 = sw_corner.ra
            lon2 = se_corner.ra
            if lon1 < lon2:
                lon2 -= 2*np.pi
            ninterp = int((lon1 - lon2) // step_eff)
            if ninterp > 0:
                interp_step = (lon1 - lon2) / (ninterp + 1)
                for iinterp in range(ninterp):
                    lon = (lon2 + iinterp*interp_step) % (2*np.pi)
                    corners_temp.append(
                        ephem.Equatorial(fun(lon, lat, epoch='2000')))
            # NE corner
            corners_temp.append(ephem.Equatorial(sw_corner))
            lon = sw_corner.ra
            lat1 = sw_corner.dec
            lat2 = nw_corner.dec
            ninterp = int((lat2 - lat1) // step)
            if ninterp > 0:
                interp_step = (lat2 - lat1) / (ninterp + 1)
                for iinterp in range(ninterp):
                    lat = lat1 + iinterp*interp_step
                    corners_temp.append(
                        ephem.Equatorial(fun(lon, lat, epoch='2000')))
            for corner in corners_temp:
                if corner.dec > 80*degree or corner.dec < -80*degree:
                    raise RuntimeError(
                        '{} has at least one circumpolar corner. '
                        'Circumpolar targeting not yet implemented'.format(name))
                patch_corner = ephem.FixedBody()
                patch_corner._ra = corner.ra
                patch_corner._dec = corner.dec
                corners.append(patch_corner)
        else:
            # Explicit patch corners
            print('Explicit-corners format ', end='')
            while i < len(parts):
                print(' ({}, {})'.format(parts[i], parts[i+1]), end='')
                try:
                    # Assume coordinates in degrees
                    lon = float(parts[i]) * degree
                    lat = float(parts[i+1]) * degree
                except:
                    # Failed simple interpreration, assume pyEphem strings
                    lon = parts[i]
                    lat = parts[i+1]
                i += 2
                if args.patch_coord == 'C':
                    corner = ephem.Equatorial(lon, lat, epoch='2000')
                elif args.patch_coord == 'E':
                    corner = ephem.Ecliptic(lon, lat, epoch='2000')
                elif args.patch_coord == 'G':
                    corner = ephem.Galactic(lon, lat, epoch='2000')
                else:
                    raise RuntimeError('Unknown coordinate system: {}'.format(
                        args.patch_coord))
                corner = ephem.Equatorial(corner)
                if corner.dec > 80*degree or corner.dec < -80*degree:
                    raise RuntimeError(
                        '{} has at least one circumpolar corner. '
                        'Circumpolar targeting not yet implemented'.format(name))
                patch_corner = ephem.FixedBody()
                patch_corner._ra = corner.ra
                patch_corner._dec = corner.dec
                corners.append(patch_corner)
        print('')
        patches.append([name, weight, corners])

    if args.debug:
        plt.figure(figsize=[18,12])
        for iplot, coord in enumerate('CEG'):
            hp.mollview(None, coord=coord, title='Patch locations',
                        sub=[2, 2, 1+iplot])
            hp.graticule(30)
            for name, weight, corners in patches:
                lon = [corner._ra/degree for corner in corners]
                lat = [corner._dec/degree for corner in corners]
                lon.append(lon[0])
                lat.append(lat[0])
                print('{} corners:\n lon = {}\n lat= {}'.format(name, lon, lat),
                      flush=True)
                hp.projplot(lon, lat, 'r-', threshold=1, lonlat=True, coord='C',
                            lw=2)
                hp.projtext(lon[0], lat[0], name, lonlat=True, coord='C',
                            fontsize=14)

    if args.debug:
        plt.savefig('patches.png')
        plt.close()

    # Normalize the weights
    for i in range(len(patches)):
        patches[i][1] /= total_weight

    build_schedule(
        start_timestamp, stop_timestamp, args.gap, args.gap_small, args.out,
        args.site_name, args.site_lat, args.site_lon, args.site_alt, args.debug,
        args.sun_el_max*degree, args.sun_avoidance_angle*degree,
        args.sun_angle_min*degree, args.moon_angle_min*degree,
        args.el_min*degree, args.el_max*degree, args.fp_radius*degree,
        args.ces_max_time, patches)

if __name__ == '__main__':
    main()
