import numpy as np


def riley(fil, **kwargs):
    """ Read info from riley's pik files
    """
    names = ['lat', 'lon', 'roll', 'rng', 'srfi', 'srfq', 'thick', 'bedi', 'bedq']
    out = np.genfromtxt(fil, delimiter=',', names=names)
    return out


def srf(fil, **kwargs):
    """ Get surface echo
    """
    a = riley(fil, **kwargs)
    out = a['srfi'] + a['srfq']*1j
    return out

def bed(fil, **kwargs):
    """Get bed echo
    """
    a = riley(fil, **kwargs)
    out = a['bedi'] + a['bedq']*1j
    return out
