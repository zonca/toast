# Copyright (c) 2015-2017 by the parties listed in the AUTHORS file.
# All rights reserved.  Use of this source code is governed by
# a BSD-style license that can be found in the LICENSE file.

from ..mpi import MPI
from .mpi import MPITestCase

from ..cache import *

import sys
import warnings


class CacheTest(MPITestCase):

    def setUp(self):
        self.nsamp = 1000
        self.cache = Cache(pymem=False)
        self.pycache = Cache(pymem=True)
        self.types = {
            'f64': np.float64,
            'f32': np.float32,
            'i64': np.int64,
            'u64': np.uint64,
            'i32': np.int32,
            'u32': np.uint32,
            'i16': np.int16,
            'u16': np.uint16,
            'i8': np.int8,
            'u8': np.uint8
        }

    def tearDown(self):
        del self.cache
        del self.pycache


    def test_create(self):
        start = MPI.Wtime()

        for k, v in self.types.items():
            ref = self.cache.create('test-{}'.format(k), v, (self.nsamp,4))
            del ref

        for k, v in self.types.items():
            data = self.cache.reference('test-{}'.format(k))
            data[:] += np.repeat(np.arange(self.nsamp, dtype=v), 4).reshape(-1,4)
            del data

        for k, v in self.types.items():
            ex = self.cache.exists('test-{}'.format(k))
            self.assertTrue(ex)

        for k, v in self.types.items():
            self.cache.destroy('test-{}'.format(k))

        self.cache.clear()

        for k, v in self.types.items():
            ref = self.pycache.create('test-{}'.format(k), v, (self.nsamp,4))
            del ref

        for k, v in self.types.items():
            data = self.pycache.reference('test-{}'.format(k))
            data[:] += np.repeat(np.arange(self.nsamp, dtype=v), 4).reshape(-1,4)
            del data

        for k, v in self.types.items():
            ex = self.pycache.exists('test-{}'.format(k))
            self.assertTrue(ex)

        for k, v in self.types.items():
            self.pycache.destroy('test-{}'.format(k))

        self.cache.clear()

        stop = MPI.Wtime()
        elapsed = stop - start
        self.print_in_turns("cache create test took {:.3f} s".format(elapsed))


    def test_create_none(self):
        start = MPI.Wtime()

        try:
            ref = self.cache.create(None, np.float, (1,10))
            raise RuntimeError('Creating object with None key succeeded')
        except ValueError:
            pass

        self.cache.clear()

        stop = MPI.Wtime()
        elapsed = stop - start
        self.print_in_turns(
            "cache create none test took {:.3f} s".format(elapsed))


    def test_put_none(self):
        start = MPI.Wtime()

        try:
            ref = self.cache.put(None, np.float, np.arange(10))
            raise RuntimeError('Putting an object with None key succeeded')
        except ValueError:
            pass

        self.cache.clear()

        stop = MPI.Wtime()
        elapsed = stop - start
        self.print_in_turns("cache put none test took {:.3f} s".format(elapsed))


    def test_clear(self):
        start = MPI.Wtime()

        for k, v in self.types.items():
            ref = self.cache.create('test-{}'.format(k), v, (self.nsamp,4))
            del ref

        warnings.filterwarnings('error')
        self.cache.clear('.*')
        self.cache.clear('.*')
        warnings.resetwarnings()

        self.cache.clear()

        stop = MPI.Wtime()
        elapsed = stop - start
        self.print_in_turns("cache clear test took {:.3f} s".format(elapsed))


    def test_alias(self):
        start = MPI.Wtime()

        ref = self.cache.put('test', np.arange(10))
        del ref

        self.cache.add_alias('test-alias', 'test')
        self.cache.add_alias('test-alias-2', 'test')

        data = self.cache.reference('test-alias')
        del data

        self.cache.destroy('test-alias')

        data = self.cache.reference('test-alias-2')
        del data

        self.cache.destroy('test')

        ex = self.cache.exists('test-alias-2')
        self.assertFalse(ex)

        stop = MPI.Wtime()
        elapsed = stop - start
        self.print_in_turns("cache alias test took {:.3f} s".format(elapsed))
