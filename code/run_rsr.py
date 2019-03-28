import multiprocessing
import argparse
import sys
import numpy as np
import pandas as pd
import get
import rsr
from rsr import invert, fit
import subradar as sr
import matplotlib.pyplot as plt
import imageio
import time


def timing(func):
    """Outputs the time a function takes to execute.
    """
    def func_wrapper(*args, **kwargs):
        t1 = time.time()
        func(*args, **kwargs)
        t2 = time.time()
        print("- Processed in %.1f s.\n" % (t2-t1))
    return func_wrapper


def scale(amp):
    """Provide a factor to scale a set of amplitudes between 0 and 1
    for correct rsr processing"""
    y, x = np.histogram(np.abs(amp), bins='fd')
    pik = x[y.argmax()]
    out = 1/(pik*10)
    return out


#@timing
def rsr_processor(fil, frame=None, gain=-30., att_rate=-10., bins='stone', verbose=False, **kwargs):
    """Apply RSR from a section of a transect
    """

    if verbose is True:
        print(frame)

    #-----------
    # Load Data
    #----------

    wf, wb = 195e6, 9.5e6

    a = get.riley(fil)

    if frame is None:
        frame = [0, a['lon'].size]

    frame_id = np.mean(frame).astype('int')
    h0 = a['rng'][frame[0]:frame[1]].mean()
    lon = a['lon'][frame[0]:frame[1]].mean()
    lat = a['lat'][frame[0]:frame[1]].mean()
    roll = a['roll'][frame[0]:frame[1]].mean()
    h1 = a['thick'][frame[0]:frame[1]].mean()

    #--------------------
    # RSR Process
    #--------------------

    # Scaling

    srf = get.srf(fil)[frame[0]:frame[1]] # * 10**(gain/20.)
    bed = get.bed(fil)[frame[0]:frame[1]] # * 10**(gain/20.)
    scale_srf = scale(srf)
    scale_bed = scale(bed)
    srf = srf*scale_srf
    bed = bed*scale_bed

    # Process

    s = fit.lmfit( np.abs(srf), bins=bins)
    b = fit.lmfit( np.abs(bed), bins=bins)

    # Received Powers

    Psc = 10*np.log10( s.values['a']**2 ) - 20*np.log10(scale_srf) + gain
    Psn = 10*np.log10( 2*s.values['s']**2 ) - 20*np.log10(scale_srf) + gain
    Pbc = 10*np.log10( b.values['a']**2  ) - 20*np.log10(scale_bed) + gain
    Pbn = 10*np.log10( 2*b.values['s']**2  ) - 20*np.log10(scale_bed) + gain

    #-------------
    # Coefficients
    #-------------

    Rsc, Rsn = invert.srf_coeff(Psc=Psc, Psn=Psn, h0=h0, wb=wb )
    s_prop = invert.spm(wf, Rsc, Rsc-Psc+Psn)

    n1 = np.sqrt(s_prop['eps'])
    sh = s_prop['sh']
    Q1 = 2 * h1/1e3 * att_rate
    Rbc, Rbn = invert.bed_coeff(Psc=Psc, Psn=Psn,
                                Pbc=Pbc, Pbn=Pbn,
                                n1=n1, sh=sh, h0=h0, h1=h1, Q1=Q1,
                                wf=wf, wb=wb)

    out = {'xo':frame_id, 'xa':frame[0], 'xb':frame[1],
           'lon':lon, 'lat':lat, 'roll':roll,
           'Psc':Psc, 'Psn':Psn, 'Pbc':Pbc, 'Pbn':Pbn,
           'Rsc':Rsc, 'Rsn':Rsn, 'Rbc':Rbc, 'Rbn':Rbn,
           'crls':s.crl(), 'crlb':b.crl(),
           'e1':n1**2, 'sh':sh,
           'h0':h0, 'h1':h1, 'Q1':Q1}

    return out


def rsr_frames(fil ,winsize=1000., sampling=250, **kwargs):
    """
    Defines along-track frames coordinates for rsr application
    """

    #-----------
    # Load Data
    #----------

    a = get.riley(fil)

    #--------------------
    # Windows along-track
    #--------------------

    x = np.arange(a.size) #vector index
    #xa = x[:x.size-winsize:sampling] #windows starting coordinate
    xa = x[:np.int(x.size-winsize):np.int(sampling)] #windows starting coordinate
    xb = xa + winsize-1 #window end coordinate
    if xb[-1] > x[-1]: xb[-1] = x[-1] #cut last window in limb
    xo = [val+(xb[i]-val)/2. for i, val in enumerate(xa)]

    out = [ np.array([xa[i], xb[i]]).astype('int64') for i in np.arange(xa.size) ]

    return out


def plot(fil, sav=False):
    """
    Plot RSR results
    """
    a = np.genfromtxt(fil, delimiter=',', names=True)

    # Figure
    fig = plt.figure(figsize=(15,30), dpi= 80, )#wspace=0, hspace=0)

    ax_rdg = fig.add_subplot(211)
    ax_srf = fig.add_subplot(614)
    ax_bed = fig.add_subplot(615)
    ax_air = fig.add_subplot(616)
    ax_air_h1 = ax_air.twinx()
    ax_srf_sh = ax_srf.twinx()

    for i in [ax_srf, ax_srf_sh, ax_bed, ax_air, ax_air_h1]:
    #    i.grid()
        i.title.set_size(30)
        i.set_xlim([0, a['xo'][-1]])

    rdg = imageio.imread(fil.replace('_rsr.txt', '_echo.jpg'), format='jpg')
    ax_rdg.imshow(rdg, aspect='auto')
    ax_rdg.set_xlim(155,1087)
    ax_rdg.set_ylim(870,20)
    ax_rdg.set_axis_off()

    color = 'tab:blue'
    ax_srf.plot(a['xo'], a['e1'], ls='-', alpha=.5, lw=2,color=color)
    ax_srf.set_ylabel('Permittivity $[-]$', color=color)
    ax_srf.tick_params(axis='y', labelcolor=color)
    ax_srf.set_title('Surface', fontweight="bold", size=15)
    ax_srf.set_xticklabels([])
    ax_srf.set_ylim([1.2,3.2])
    ax_srf.grid()

    color = 'tab:red'
    ax_srf_sh.plot(a['xo'], a['sh'], ls='-', lw=2, alpha=.5, color=color)
    ax_srf_sh.set_ylabel('RMS Height $[m]$', color=color)
    ax_srf_sh.tick_params(axis='y', labelcolor=color)
    ax_srf_sh.set_ylim([0,.1])

    ax_bed.plot(a['xo'], a['Rbc'], '.5', lw=2, alpha=.8, label='Reflection Coef.')
    ax_bed.plot(a['xo'], a['Rbn'], '.8', lw=2, alpha=.8, label='Scattering Coef.')
    ax_bed.set_title('Bed', fontweight="bold", size=15)
    ax_bed.set_ylabel('Power $[dB]$')
    ax_bed.legend(ncol=2, fontsize='large')
    ax_bed.set_xticklabels([])
    ax_bed.set_ylim(-30,20)
    ax_bed.grid()

    ax_air.plot(a['xo'], np.abs(a['roll'])*360/np.pi, 'k', lw=2)
    ax_air.set_title('Aircraft', fontweight="bold", size=15)
    ax_air.set_ylabel('|Roll| $[deg]$')
    ax_air.set_xlabel('Bin #')
    ax_air.set_ylim(0,3)
    ax_air.grid()

    color = '.5'
    ax_air_h1.plot(a['xo'], a['h1'], color=color, lw=2)
    ax_air_h1.set_ylabel('Range to surface $[m]$', color=color)
    ax_air_h1.tick_params(axis='y', labelcolor=color)
    ax_air_h1.set_ylim(0,2000)

    if sav is True:
        save_file = fil.replace('.txt', '.png')
        plt.savefig(save_file, bbox_inches="tight")
        print('CREATED: ' + save_file + '\n')


@timing
def main(fil, nbcores=4, sampling=250):
    """
    RSR multiprocessing of a line
    """

    #-----------
    # Processing
    #-----------

    print('Processing ' + fil)
    win = rsr_frames(fil)
    pool = multiprocessing.Pool(nbcores)
    results =  [pool.apply_async(rsr_processor,
        (fil,), {'frame':i, 'verbose':False, 'sampling':sampling}) for i in win]

    # ------------
    # Sort Results
    #-------------

    out = pd.DataFrame(results[0].get(), index=[0])
    for i in np.arange(1, len(win)):
        out = out.append(results[i].get(), ignore_index=True)
    out = out.sort_values('xo')

    #--------
    # Archive
    #--------

    save_file = fil.replace('.txt', '_rsr.txt')
    out.to_csv(save_file, sep=',', index=False)
    print('CREATED: ' + save_file + '\n')

    save_file = fil.replace('.txt', '_rsr.txt')
    plot(save_file, sav=True)


if __name__ == "__main__":
    # execute only if run as a script

    parser = argparse.ArgumentParser()
    parser.add_argument('filename', help='File to be processed')
    parser.add_argument('-n', '--nbcores', default=8, type=int, help='Number of simultaneous cores to use')
    parser.add_argument('-s', '--sampling', default=250, type=int, help='numbers of bins between each computing window')
    parser.add_argument('-w', '--winsize', default=1000, type=int, help='number of consecutive bins in a computing window')
    args = parser.parse_args()
    main(args.filename, nbcores=args.nbcores)


