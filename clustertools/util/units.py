"""For changing units

"""
__author__ = "Jeremy J Webb"


import numpy as np
from ..util.constants import *

try:
    import amuse.units.units as u
    from amuse.io import read_set_from_file
except:
    pass

try:
    from galpy.util import coords,conversion
except:
    import galpy.util.bovy_coords as coords
    import galpy.util.bovy_conversion as conversion

def _convert_length(x,units,cluster):
    """Convert x from units to cluster.units

    Parameters
    ----------
    x : float
      measure of distance in units
    units : str
      units associated with x
    cluster : class
      StarCluster

    Returns
    -------
    x : float
      measure of distance with units the same as cluster.units

    History
    -------
    2022 - Written - Webb (UofT)
    """

    if units=='nbody':
        if cluster.units=='pckms' or cluster.units=='pcmyr' or cluster.units=='amuse':
            x*=cluster.rbar
            if cluster.units=='amuse':
                x= x | u.parsec
        elif cluster.units=='kpckms' or cluster.units=='kpcgyr' or cluster.units=='WDunits':
            x*=cluster.rbar/1000.0
        elif cluster.units=='galpy':
            x*=cluster.rbar/1000.0/cluster._ro
        elif cluster.units=='radec':
            x*=cluster.rbar/1000.0
            x=np.degrees(np.arctan2(x,cluster.zgc))

    elif units=='pckms' or units=='pcmyr' or units=='amuse':
        if units=='amuse':
            x=x.value_in(u.pc)

        if cluster.units=='nbody':
            x/=cluster.rbar
        elif cluster.units=='kpckms' or cluster.units=='kpcgyr' or cluster.units=='WDunits':
            x/=1000.0
        elif cluster.units=='galpy':
            x/=(1000.0*cluster._ro)
        elif cluster.units=='radec':
            x/=1000.0
            x=np.degrees(np.arctan2(x,cluster.zgc))
        elif cluster.units=='amuse':
            x=x | u.parsec

    elif units=='kpckms' or units=='kpcgyr' or units=='WDunits':
        if cluster.units=='nbody':
            x*=1000.0/cluster.rbar
        elif cluster.units=='pckms' or cluster.units=='pcmyr' or cluster.units=='amuse':
            x*=1000.0
            if cluster.units=='amuse':
                x= x | u.parsec
        elif cluster.units=='galpy':
            x/=cluster._ro
        elif cluster.units=='radec':
            x=np.degrees(np.arctan2(x,cluster.zgc))

    elif units=='galpy':
        if cluster.units=='pckms' or cluster.units=='pcmyr' or cluster.units=='amuse':
            x*=(1000.0*cluster._ro)
            if cluster.units=='amuse':
                x= x | u.parsec
        elif cluster.units=='kpckms' or cluster.units=='kpcgyr' or cluster.units=='WDunits':
            x*=cluster._ro
        elif cluster.units=='nbody':
            x*=(cluster._ro*1000.0/cluster.rbar)
        elif cluster.units=='radec':
            x*=cluster._ro
            x=np.degrees(np.arctan2(x,cluster.zgc))

    elif units=='radec':
        if cluster.units!='radec':
            dist=np.sqrt(cluster.xgc**2.+cluster.ygc**2.0+cluster.zgc**2.0)
            x=np.tan(np.radians(x))*dist

            if cluster.units=='nbody':
                x*=1000.0/cluster.rbar
            elif cluster.units=='pckms' or cluster.units=='pcmyr' or cluster.units=='amuse':
                x*=1000.0
                if cluster.units=='amuse':
                    x= x | u.parsec
            elif cluster.units=='galpy':
                x/=cluster._ro

    return x

def _convert_velocity(x,units,cluster):
    """Convert x from units to cluster.units

    Parameters
    ----------
    x : float
      measure of velocity in units
    units : str
      units associated with x
    cluster : class
      StarCluster

    Returns
    -------
    x : float
      measure of velocity with units the same as cluster.units

    History
    -------
    2022 - Written - Webb (UofT)
    """

    if units=='nbody':
        if cluster.units=='pckms' or cluster.units=='pcmyr' or cluster.units=='amuse':
            x*=cluster.vbar
            if cluster.units=='amuse':
                x= x | u.kms
        elif cluster.units=='kpckms' or cluster.units=='kpcgyr' or cluster.units=='WDunits':
            x*=cluster.vbar
        elif cluster.units=='galpy':
            x*=cluster.vbar/cluster._vo
        elif cluster.units=='radec':
            print('NO DIRECT CONVERSION AVAILABLE')


    elif units=='pckms' or units=='pcmyr' or units=='amuse':
        if units=='amuse':
            x=x.value_in(u.kms)

        if cluster.units=='nbody':
            x/=cluster.vbar
        elif cluster.units=='galpy':
            x/=cluster._vo
        elif cluster.units=='radec':
            print('NO DIRECT CONVERSION AVAILABLE')
        elif cluster.units=='amuse':
            x=x | u.kms

    elif units=='kpckms' or units=='kpcgyr' or units=='WDunits':
        if cluster.units=='nbody':
            x/=cluster.vbar
        elif cluster.units=='amuse':
            x= x | u.kms
        elif cluster.units=='galpy':
            x/=cluster._vo
        elif cluster.units=='radec':
            print('NO DIRECT CONVERSION AVAILABLE')

    elif units=='galpy':
        if cluster.units=='pckms' or cluster.units=='pcmyr' or cluster.units=='amuse':
            x*=cluster._vo
            if cluster.units=='amuse':
                x= x | u.kms
        elif cluster.units=='kpckms' or cluster.units=='kpcgyr' or cluster.units=='WDunits':
            x*=cluster._vo
        elif cluster.units=='nbody':
            x*=(cluster._vo/cluster.vbar)
        elif cluster.units=='radec':
            print('NO DIRECT CONVERSION AVAILABLE')

    elif units=='radec':
        print('NO DIRECT CONVERSION AVAILABLE')


    return x

def _convert_time(x,units,cluster):
    """Convert x from units to cluster.units

    Parameters
    ----------
    x : float
      measure of time in units
    units : str
      units associated with x
    cluster : class
      StarCluster

    Returns
    -------
    x : float
      measure of time with units the same as cluster.units

    History
    -------
    2022 - Written - Webb (UofT)
    """

    to=conversion.time_in_Gyr(ro=cluster._ro,vo=cluster._vo)

    if units=='nbody':
        if cluster.units=='pckms' or cluster.units=='pcmyr' or cluster.units=='amuse':
            x*=cluster.tbar
            if cluster=='amuse':
                x = x | u.Myr
        elif cluster.units=='kpckms' or cluster.units=='kpcgyr' or cluster.units=='WDunits':
            x*=cluster.tbar/1000.0
        elif cluster.units=='galpy':
            x*=cluster.tbar/1000.0/to
        elif cluster.units=='radec':
            x*=cluster.tbar/1000.0

    elif units=='pckms' or units=='pcmyr' or units=='amuse':
        if units=='amuse':
            x=x.value_in(u.Myr)
        if cluster.units=='nbody':
            x/=cluster.tbar
        elif cluster.units=='kpckms' or cluster.units=='kpcgyr' or cluster.units=='WDunits':
            x/=1000.0
        elif cluster.units=='galpy':
            x/=(1000.0*to)
        elif cluster.units=='radec':
            x/=1000.0
        elif cluster.units=='amuse':
            x=x | u.Myr

    elif units=='kpckms' or units=='kpcgyr' or units=='WDunits':
        if cluster.units=='nbody':
            x*=1000.0/cluster.tbar
        elif cluster.units=='pckms' or cluster.units=='pcmyr' or cluster.units=='amuse':
            x*=1000.0
            if cluster.units=='amuse':
                x=x | u.Myr
        elif cluster.units=='galpy':
            x/=to
 
    elif units=='galpy':
        if cluster.units=='pckms' or cluster.units=='pcmyr' or cluster.units=='amuse':
            x*=(1000.0*to)
            if cluster.units=='amuse':
                x=x | u.Myr
        elif cluster.units=='kpckms' or cluster.units=='kpcgyr' or cluster.units=='WDunits':
            x*=to
        elif cluster.units=='nbody':
            x*=(to*1000.0/cluster.tbar)
        elif cluster.units=='radec':
            x*=to

    elif units=='radec':
        if cluster.units!='radec':
            if cluster.units=='nbody':
                x*=1000.0/cluster.tbar
            elif cluster.units=='pckms' or cluster.units=='pcmyr' or cluster.units=='amuse':
                x*=1000.0
                if cluster.units=='amuse':
                    x=x | u.Myr
            elif cluster.units=='galpy':
                x/=to

    return x

def _convert_amuse(particles,cluster):
    """Convert AMUSE particles to numpy arrays with cluster.units

    Parameters
    ----------
    particles : particles
        AMUSE particle dataset
    cluster : class
      StarCluster

    Returns
    -------
    x,y,z,vx,vy,vz,m,id : float x 7, int
      positions and velocities of particles in cluster.units

    History
    -------
    2022 - Written - Webb (UofT)
    """
    ids=particles.key
    if cluster.units == "pckms" or cluster.units is None:
        m = particles.mass.value_in(u.MSun)
        x = particles.x.value_in(u.parsec)
        y = particles.y.value_in(u.parsec)
        z = particles.z.value_in(u.parsec)
        vx = particles.vx.value_in(u.kms)
        vy = particles.vy.value_in(u.kms)
        vz = particles.vz.value_in(u.kms)
    elif cluster.units == "kpckms":
        m = particles.mass.value_in(u.MSun)
        x = particles.x.value_in(u.kpc)
        y = particles.y.value_in(u.kpc)
        z = particles.z.value_in(u.kpc)
        vx = particles.vx.value_in(u.kms)
        vy = particles.vy.value_in(u.kms)
        vz = particles.vz.value_in(u.kms)
    elif cluster.units == "kpcgyr":
        m = particles.mass.value_in(u.MSun)
        x = particles.x.value_in(u.kpc)
        y = particles.y.value_in(u.kpc)
        z = particles.z.value_in(u.kpc)
        vx = particles.vx.value_in(u.kpc/u.Gyr)
        vy = particles.vy.value_in(u.kpc/u.Gyr)
        vz = particles.vz.value_in(u.kpc/u.Gyr)
    elif cluster.units == "pcmyr":
        m = particles.mass.value_in(u.MSun)
        x = particles.x.value_in(u.pc)
        y = particles.y.value_in(u.pc)
        z = particles.z.value_in(u.pc)
        vx = particles.vx.value_in(u.parsec/u.Myr)
        vy = particles.vy.value_in(u.parsec/u.Myr)
        vz = particles.vz.value_in(u.parsec/u.Myr)

    return x,y,z,vx,vy,vz,m,ids



