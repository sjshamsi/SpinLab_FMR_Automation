import numpy
import scipy
import scipy.signal
import scipy.optimize

def Spline_Filter(arr, a=50):
    return scipy.signal.spline_filter(arr, a)

def Gaussian_Filter(arr, nf=5,  nh='nf'):
    return Smooth(arr, nf,  nh)

def Smooth(S, nf=3,  nh='nf'):
    if nh == 'nf':
        nh = nf
    nh = int(nh)
    nf = int(nf)
    x, y = numpy.mgrid[-nh:nh+1, -nf:nf+1]
    g = numpy.exp(-(x**2.0/nh + y**2.0/nf))
    g = g / g.sum()
    out = scipy.ndimage.convolve(S.real, g, mode='nearest')
    if S.dtype == 'complex':
        out = out + 1.0j*scipy.ndimage.convolve(S.imag, g, mode='nearest')
    return out

def Revove_BG_Min(arr, nf=5, nh=5):
    S = Smooth(arr, nf=nf, nh=nh)
    bg = numpy.min(S.real, axis=0)
    arr -= bg[None,:]
    return arr

def Revove_BG_Median(arr):
    S = arr.copy()
    bg = numpy.zeros_like(S[0,:].real)
    m = numpy.median(S.real, axis=0)
    for i, x in enumerate(m):
        bg[i] = numpy.mean(S.real[:,i][S[:,i].real < x])
    arr -= bg[None,:]
    return arr