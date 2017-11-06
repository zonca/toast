//
//  Time Ordered Astrophysics Scalable Tools (TOAST)
//
//  Copyright (c) 2015-2017, The Regents of the University of California
//  All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are met:
//
//  1. Redistributions of source code must retain the above copyright notice,
//  this list of conditions and the following disclaimer.
//
//  2. Redistributions in binary form must reproduce the above copyright notice,
//  this list of conditions and the following disclaimer in the documentation
//  andther materials provided with the distribution.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
//  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
//  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
//  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
//  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
//  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
//  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
//  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
//  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
//  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
//  POSSIBILITY OF SUCH DAMAGE.
//
//

#ifndef TOAST_TEST_HPP
#define TOAST_TEST_HPP

#include <toast_internal.hpp>

#include <gtest/gtest.h>

// #include <ctoast.h>


namespace toast { namespace test {
    int runner ( int argc, char *argv[] );
}}

class timingTest : public ::testing::Test
{
public:
    timingTest () { }
    ~timingTest () { }
    virtual void SetUp() { }
    virtual void TearDown() { }
};


class qarrayTest : public ::testing::Test {

    public :

        qarrayTest () { }
        ~qarrayTest () { }
        virtual void SetUp();
        virtual void TearDown() { }

        static const double q1[];
        static const double q1inv[];
        static const double q2[];
        static const double qtonormalize[];
        static const double qnormalized[];
        static const double vec[];
        static const double vec2[];
        static const double qeasy[];
        static const double mult_result[];
        static const double rot_by_q1[];
        static const double rot_by_q2[];

};


class rngTest : public ::testing::Test {

    public :

        rngTest () { }
        ~rngTest () { }
        virtual void SetUp();
        virtual void TearDown() { }

        static const int64_t size;
        static const uint64_t counter[];
        static const uint64_t key[];
        static const uint64_t counter00[];
        static const uint64_t key00[];

        static const double array_gaussian[];
        static const double array_m11[];
        static const double array_01[];
        static const uint64_t array_uint64[];

        static const double array00_gaussian[];
        static const double array00_m11[];
        static const double array00_01[];
        static const uint64_t array00_uint64[];

};


class sfTest : public ::testing::Test {

    public :

        sfTest () { }
        ~sfTest () { }
        virtual void SetUp();
        virtual void TearDown();

        static const int size;
        toast::mem::simd_array<double> angin;
        toast::mem::simd_array<double> sinout;
        toast::mem::simd_array<double> cosout;
        toast::mem::simd_array<double> xin;
        toast::mem::simd_array<double> yin;
        toast::mem::simd_array<double> atanout;
        toast::mem::simd_array<double> sqin;
        toast::mem::simd_array<double> sqout;
        toast::mem::simd_array<double> rsqin;
        toast::mem::simd_array<double> rsqout;
        toast::mem::simd_array<double> expin;
        toast::mem::simd_array<double> expout;
        toast::mem::simd_array<double> login;
        toast::mem::simd_array<double> logout;

};


class healpixTest : public ::testing::Test {

    public :

        healpixTest () { }
        ~healpixTest () { }
        virtual void SetUp() { }
        virtual void TearDown() { }

};


class fftTest : public ::testing::Test {

    public :

        fftTest () { }
        ~fftTest () { }
        virtual void SetUp() { }
        virtual void TearDown() { }

        void runbatch(int64_t nbatch, toast::fft::r1d_p forward, 
            toast::fft::r1d_p reverse);

        static const int64_t length;
        static const int64_t n;

};


class covTest : public ::testing::Test {

    public :

        covTest () { }
        ~covTest () { }
        virtual void SetUp() { }
        virtual void TearDown() { }

        static const int64_t nsm;
        static const int64_t npix;
        static const int64_t nnz;
        static const int64_t nsamp;
        static const int64_t scale;

};


class mpiShmemTest : public ::testing::Test {

    public :

        mpiShmemTest () { }
        ~mpiShmemTest () { }
        virtual void SetUp() { }
        virtual void TearDown() { }

        static const size_t n;

};


class polyfilterTest : public ::testing::Test {

public :

    polyfilterTest () { }
    ~polyfilterTest () { }
    virtual void SetUp() { }
    virtual void TearDown() { }

    static const size_t order, n;

};



#endif
