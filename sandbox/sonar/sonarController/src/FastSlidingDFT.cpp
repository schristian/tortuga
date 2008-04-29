/*
 *  FastSlidingDFT.cpp
 *  sonarController
 *
 *  Created by Tom Capon on 01/20/08.
 *  Based on work by Leo Singer.
 *  Copyright 2008 Robotics@Maryland. All rights reserved.
 *
 */


#include "FastSlidingDFT.h"


#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>
#include <stdio.h>


namespace ram {
namespace sonar {
	

int16_t floatToQ15(float x)
{
	float y = round(x * ((int16_t) 1 << 15));
	if (y >= 32768)
		return 32767;
	else
		return (int16_t) y;
}


int32_t int32ToQ31(int32_t x)
{
	return x >> 4;
}


template<int nchannels, int k, int N>
FastSlidingDFT<nchannels, k, N>::FastSlidingDFT()
{
	setupCoefficients();
	setupWindow();
}


/** Update the one selected Fourier amplitude using a sliding DFT
 */
template<int nchannels, int k, int N>
void FastSlidingDFT<nchannels, k, N>::update(const adcdata_t * sample)
{
	for (int channel = 0 ; channel < nchannels ; channel ++)
	{
		
		//	After http://www.comm.toronto.edu/~dimitris/ece431/slidingdft.pdf
		
		/*	Step 1: Subtract the old data from the real part sum.
		 *	This removes the x(0) term from the DFT, corresponding to the
		 *	data point that is getting pushed out of the window.
		 *	Since all ADC data is real, we do not touch the imaginary part.
		 */
		
		sumreal[channel] -= window[channel][curidx];
		
		/*	Step 2: Add the new data point in the x(0) position.
		 *	Also store new data in the buffer.
		 */
		
		sumreal[channel] += sample[channel];
		window[channel][curidx] = sample[channel];

		/*	Step 3: Phase-shift the DFT sum.
		 *	Note that after step 2, the point that should be x(N-1) is in the
		 *	x(0) position.  We can correct this simply "rotating" the DFT *backwards*
		 *	one index.  We use a single complex multiplication to achieve this, using a
		 *	constanst factor:
		 *	
		 *	coef = exp(2*pi*i*k/N)
		 *
		 *	Note that the exponent is positive; this causes the backwards shift.
		 */
		
		adcmath_t tmp    = coefreal * sumreal[channel] - coefimag * sumimag[channel];
		sumimag[channel] = coefreal * sumimag[channel] + coefimag * sumreal[channel];
		sumreal[channel] = tmp;
		
		/*	We compute the L1 norm (|a|+|b|) instead of the L2 norm 
		 *	sqrt(a^2+b^2) in order to aovid integer overflow.  Since we are only
		 *	using the magnitude for thresholding, this is an acceptable 
		 *	approximation.
		 */
		
		mag[channel] = abs(sumreal[channel]) + abs(sumimag[channel]);
	}
	
	/*	curidx represents the index into the circular buffers 
	 *	windowreal[channel] and windowimag[channel] at which the just-received
	 *	sample will be added to the DFT sum.
	 */
	
	++curidx;
	if (curidx == N)
		curidx = 0;
}


template<int nchannels, int k, int N>
void FastSlidingDFT<nchannels, k, N>::setupCoefficients()
{
	coefreal = cos(2 * M_PI * k / N) * ADCDATA_MAXAMPLITUDE;
	coefimag = sin(2 * M_PI * k / N) * ADCDATA_MAXAMPLITUDE;
}


template<int nchannels, int k, int N>
void FastSlidingDFT<nchannels, k, N>::setupWindow() {
	purge();
}


template<int nchannels, int k, int N>
void FastSlidingDFT<nchannels, k, N>::purge()
{
	bzero(sumreal, sizeof(*sumreal) * nchannels);
	bzero(sumimag, sizeof(*sumimag) * nchannels);
	bzero(mag, sizeof(*mag) * nchannels);
	for (int i = 0 ; i < nchannels ; i ++)
	{
		bzero(window[i], sizeof(**window) * N);
	}
	curidx = 0;
}


template<int nchannels, int k, int N>
adcmath_t FastSlidingDFT<nchannels, k, N>::getMagL1(int channel) const
{
	assert(channel < nchannels);
	return mag[channel];
}


template<int nchannels, int k, int N>
adcmath_t FastSlidingDFT<nchannels, k, N>::getReal(int channel) const
{
	assert(channel < nchannels);
	return sumreal[channel];
}


template<int nchannels, int k, int N>
adcmath_t FastSlidingDFT<nchannels, k, N>::getImag(int channel) const
{
	assert(channel < nchannels);
	return sumimag[channel];
}


} // namespace sonar
} // namespace ram
