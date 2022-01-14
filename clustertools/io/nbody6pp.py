import numpy as np
try:
    from galpy.util import conversion
except:
    import galpy.util.bovy_conversion as conversion

import os, struct
from ..cluster.cluster import StarCluster
from ..analysis.orbits import initialize_orbit
from ..planet.clusterwplanets import StarClusterwPlanets
from .orbit import _get_cluster_orbit

#Try importing hdf5. Only necessary with Nbody6++ and hdf5 output
try: 
    import h5py
except:
    pass

def _get_nbody6pp(conf3, bev82=None, sev83=None, snap40=None, ofile=None, advance=False, **kwargs):
    """Extract a single snapshot from NBODY6++ output

       - Note that for snap40=False, individual binary stars are loaded in the main position, velocity, and mass arrays
       - for snap40=True, binary centre of masses are loaded in the position, velocity and mass arrays as per nbody6

    Parameters
    ----------
    conf3 : file
        opened conf3 file
    bev82 : file
        opened bev82 file containing BSE data (default: None)
    sev83 : file
        opened sev83 file containing SSE data (default: None)
    snap40 : file
        opened snap40 file containing hdf5 data (default: None)
    ofile : file
        opened file containing orbital information
    advance : bool
        is this a snapshot that has been advanced to from initial  load_cluster? (default: False)

    Returns
    -------
    cluster : class
        StarCluster

    Other Parameters
    ----------------
    Same as load_cluster

    History
    -------
    2021 - Written - Webb (UofT)
    """
    
    initialize = kwargs.get("initialize", False)
    nsnap = kwargs.pop("nsnap", 0)
    wdir = kwargs.get("wdir", './')
    deltat=kwargs.get('deltat',1)

    planets = kwargs.pop("planets", False)


    if snap40 is not None:
        ngroup=kwargs.pop('ngroup',0)
        tphys,ntot,x,y,z,vx,vy,vz,m,i_d,pot,kw,lum,rc,rs,te,binaries=_get_nbody6pp_hdf5(snap40,ngroup=ngroup,**kwargs)

        if binaries:
            bdata=_get_nbody6pp_hdf5_binaries(snap40,ngroup=ngroup,**kwargs)
            semi,ecc,gb,kw1,kw2,kwb,zl1b,zl2b,m1b,m2b,mc1,mc2,i_d1,i_d2,idc,pb,potb,rc1,rc2,r1b,r2b,te1,te2,vc1,vc2,vc3,vr1,vr2,vr3,xc1,xc2,xc3,xr1,xr2,xr3=bdata
            mbtot=np.asarray(m1b)+np.asarray(m2b)
            lbtot=np.log10(10.0**np.asarray(zl1b)+10.0**np.asarray(zl2b))
            nb=len(semi)
        else:
            nb=0

        if planets:

            cluster = StarClusterwPlanets(
                tphys,
                units="pckms",
                origin="cluster",
                ctype="nbody6++",
                sfile=snap40,
                nsnap=nsnap,
                wdir=wdir,
            )

        else:

            cluster = StarCluster(
                tphys,
                units="pckms",
                origin="cluster",
                ctype="nbody6++",
                sfile=snap40,
                nsnap=nsnap,
                wdir=wdir,
            )

        cluster.hdf5=True
        cluster.ngroups=len(snap40)
        cluster.ngroup=ngroup
        
        if binaries:
            cluster.add_stars(xc1,xc2,xc3,vc1,vc2,vc3,mbtot,i_d1)

            pb=(10.0**np.array(pb))/cluster.tbar_days
            semi=(10.0**np.array(semi))/cluster.rbar_su
            m1b=np.array(m1b)/cluster.zmbar
            m2b=np,array(m2b)/cluster.zmbar

            cluster.add_bse(i_d1,i_d2,kw1,kw2,kwb,ecc,pb,semi,m1b,m2b,zl1b,zl2b,r1b,r2b,ep1=te1,ep2=te2)
            cluster.add_sse(kw1,lbtot,np.maximum(r1b,r2b))

        cluster.add_stars(x, y, z, vx, vy, vz, m, i_d)
        cluster.add_sse(kw,lum,rs)

        if binaries: 
            cluster.pot=np.append(potb,pot)
        else:
            cluster.pot=pot

        if conf3 is not None:
            ntot,alist,x,y,z,vx,vy,vz,m,i_d,rhos,xns,pot=_get_nbody6pp_conf3(conf3,nsnap=nsnap,**kwargs)
            cluster.add_nbody6(
            alist[13], alist[12], alist[2], alist[4], alist[6], alist[7], alist[8], alist[3], alist[11],alist[10],alist[17], ntot, nb, ntot+alist[1])
            cluster.xc*=cluster.rbar
            cluster.yc*=cluster.rbar
            cluster.zc*=cluster.rbar
            cluster.tphys*=cluster.tbar
            cluster.to_nbody()

        else:
            if binaries: cluster.nb = len(semi)


    else:
        ntot,alist,x,y,z,vx,vy,vz,m,i_d,rhos,xns,pot=_get_nbody6pp_conf3(conf3,nsnap=nsnap,**kwargs)


        if planets:

            cluster = StarClusterwPlanets(
                alist[0],
                units="nbody",
                origin="cluster",
                ctype="nbody6++",
                sfile=conf3,
                nsnap=nsnap,
                wdir=wdir,
            )

        else:

            cluster = StarCluster(
                alist[0],
                units="nbody",
                origin="cluster",
                ctype="nbody6++",
                sfile=conf3,
                nsnap=nsnap,
                wdir=wdir,
            )

        if ntot > 0:
            cluster.add_nbody6(
            alist[13], alist[12], alist[2], alist[4], alist[6], alist[7], alist[8], alist[3], alist[11],alist[10],alist[17], ntot, alist[1], ntot+alist[1]
        )
            cluster.add_stars(x, y, z, vx, vy, vz, m, i_d)
            cluster.rhos=rhos

            v=np.sqrt(vx**2.+vy**2.+vz**2.)
            ek=0.5*m*v**2.
            cluster.add_energies(ek,pot)

        if bev82 is not None and sev83 is not None:
            arg,i_d,kw,ri,m1,zl1,r1,te,i_d1,i_d2,kw1,kw2,kwb,rib,ecc,pb,semi,m1b,m2b,zl1b,zl2b,r1b,r2b,te1,te2=_get_nbody6pp_ev(bev82,sev83,nsnap=nsnap,**kwargs)
            #Convert from fortran array address to python
            arg-=1

            cluster.add_sse(kw,zl1,r1)

            pb=(10.0**pb)/cluster.tbar_days
            semi=(10.0**semi)/cluster.rbar_su
            m1b/=cluster.zmbar
            m2b/=cluster.zmbar

            cluster.add_bse(i_d1,i_d2,kw1,kw2,kwb,ecc,pb,semi,m1b,m2b,zl1b,zl2b,r1b,r2b)
    
            sseindx=np.logical_or(np.logical_or(np.in1d(cluster.id,i_d),np.in1d(cluster.id,i_d1)),np.in1d(cluster.id,i_d2))

            if np.sum(sseindx) != cluster.ntot:
                print('SSE/BSE NBODY6++ ERROR',cluster.ntot-np.sum(sseindx))
                nextra=cluster.ntot-np.sum(sseindx)
                cluster.add_sse(np.zeros(nextra),np.ones(nextra)*-10,np.ones(nextra))



    if kwargs.get("analyze", True) and cluster.ntot>0:
        sortstars=kwargs.get("sortstars", True)
        cluster.analyze(sortstars=sortstars)

    if ofile != None:
        _get_cluster_orbit(cluster, ofile, advance=advance, nsnap=int(nsnap/deltat),**kwargs)
           

    return cluster

def _get_nbody6pp_conf3(f,**kwargs): 

    #Read in header
    try:
        start_header_block_size = struct.unpack('i',f.read(4))[0]
    except:
        return 0,np.zeros(20),0,0,0,0,0,0,0,0,0,0,0
        
    ntot = struct.unpack('i',f.read(4))[0] 
    model = struct.unpack('i',f.read(4))[0] 
    nrun = struct.unpack('i',f.read(4))[0]
    nk = struct.unpack('i',f.read(4))[0]
             
    end_header_block_size = struct.unpack('i',f.read(4))[0]
    
    if start_header_block_size != end_header_block_size:
        print('Error reading CONF3')
        return -1

    if ntot > 0:

        # Read in stellar data
        start_data_block_size = struct.unpack('i',f.read(4))[0] #begin data block size

        #Read in alist array from NBODY6
        alist = []
        for i in range(nk):
            alist.append(struct.unpack('f',f.read(4))[0]) #Sverre's 'as'

        #Read in masses, positions, velocities, and id's
        m=np.array([])
        rhos=np.array([])
        xns=np.array([])
        x,y,z=np.array([]),np.array([]),np.array([])
        vx,vy,vz=np.array([]),np.array([]),np.array([])
        phi=np.array([])
        i_d=np.array([])
     
        for i in range(ntot):
            m=np.append(m,struct.unpack('f',f.read(4))[0])

        for i in range(ntot):
            rhos=np.append(rhos,struct.unpack('f',f.read(4))[0])
            
        for i in range(ntot):
            xns=np.append(xns,struct.unpack('f',f.read(4))[0])

        for i in range(ntot):           
            x=np.append(x,struct.unpack('f',f.read(4))[0])
            y=np.append(y,struct.unpack('f',f.read(4))[0])
            z=np.append(z,struct.unpack('f',f.read(4))[0]) 

        for i in range(ntot):           
            vx=np.append(vx,struct.unpack('f',f.read(4))[0])
            vy=np.append(vy,struct.unpack('f',f.read(4))[0])
            vz=np.append(vz,struct.unpack('f',f.read(4))[0]) 

        for i in range(ntot):
            phi=np.append(phi,struct.unpack('i',f.read(4))[0])            

        for i in range(ntot):
            i_d=np.append(i_d,struct.unpack('i',f.read(4))[0])

        end_data_block_size = struct.unpack('i',f.read(4))[0] #begin data block size
        
        if start_data_block_size != end_data_block_size:
            print('Error reading CONF3')
            return -1

        return ntot,alist,x,y,z,vx,vy,vz,m,i_d,rhos,xns,phi
    else:
        return 0,np.zeros(20),0,0,0,0,0,0,0,0,0,0,0

def _get_nbody6pp_ev(bev, sev, **kwargs):
    
    arg=np.array([])
    i_d=np.array([])
    kw=np.array([])
    ri=np.array([])
    m1=np.array([])
    zl1=np.array([])
    r1=np.array([])
    te=np.array([])


    #Read in binary data first 
  
    header=bev.readline().split()
    nb,tphys=int(header[0]),float(header[1])

    i_d1=np.array([])
    i_d2=np.array([])
    kw1=np.array([])
    kw2=np.array([])
    kwb=np.array([])
    rib=np.array([])
    ecc=np.array([])
    pb=np.array([])
    semi=np.array([])
    m1b=np.array([])
    m2b=np.array([])
    zl1b=np.array([])
    zl2b=np.array([])
    r1b=np.array([])
    r2b=np.array([])
    te1=np.array([])
    te2=np.array([])

    if nb>0:

        for i in range(0,nb):
            data=bev.readline().split()
            if len(data)==0:
                print('Missing stars in BEV Star')
                break
            arg1=int(data[1])
            arg2=int(data[2])
            i_d1=np.append(i_d1,int(data[3]))
            i_d2=np.append(i_d2,int(data[4]))
            kw1=np.append(kw1,int(data[5]))
            kw2=np.append(kw2,int(data[6]))
            kwb=np.append(kwb,int(data[7]))
            rib=np.append(rib,float(data[8]))
            ecc=np.append(ecc,float(data[9]))
            pb=np.append(pb,float(data[10]))
            semi=np.append(semi,float(data[11]))
            m1b=np.append(m1b,float(data[12]))
            m2b=np.append(m2b,float(data[13]))

            if data[14]=='NaN':
                zl1b=np.append(zl1b,0.)
                zl2b=np.append(zl2b,0.)
                r1b=np.append(r1b,0.)
                r2b=np.append(r2b,0.)
                te1=np.append(te1,0.)
                te2=np.append(te2,0.)
            else:
                zl1b=np.append(zl1b,float(data[14]))
                zl2b=np.append(zl2b,float(data[15]))
                r1b=np.append(r1b,float(data[16]))
                r2b=np.append(r2b,float(data[17]))
                te1=np.append(te1,float(data[18]))
                te2=np.append(te2,float(data[19]))

            #Add select parameters to single star array
            arg=np.append(arg,arg1)
            arg=np.append(arg,arg2)
            i_d=np.append(i_d,i_d1[-1])
            i_d=np.append(i_d,i_d2[-1])
            kw=np.append(kw,kw1[-1])
            kw=np.append(kw,kw2[-1])
            zl1=np.append(zl1,zl1b[-1])
            zl1=np.append(zl1,zl2b[-1])
            r1=np.append(r1,r1b[-1])
            r1=np.append(r1,r2b[-1])

    header=sev.readline().split()
    ntot,tphys=int(header[0]),float(header[1])

    for i in range(0,ntot):
        data=sev.readline().split()

        if len(data)==0:
            print('Missing stars in SEV Star',i,ntot)
            break

        arg=np.append(arg,int(data[1]))
        i_d=np.append(i_d,int(data[2]))
        kw=np.append(kw,int(data[3]))
        ri=np.append(ri,float(data[4]))
        m1=np.append(m1,float(data[5]))

        if data[6]=='NaN':
            zl1=np.append(zl1,0.)
            r1=np.append(r1,0.)
            te=np.append(te,0.)
        else:
            zl1=np.append(zl1,float(data[6]))
            r1=np.append(r1,float(data[7]))
            te=np.append(te,float(data[8]))

    return arg,i_d,kw,ri,m1,zl1,r1,te,i_d1,i_d2,kw1,kw2,kwb,rib,ecc,pb,semi,m1b,m2b,zl1b,zl2b,r1b,r2b,te1,te2


def _get_nbody6pp_hdf5(f,ngroup=0,**kwargs):
        
    #datakeys=['NAM', 'X1', 'X2', 'X3', 'V1', 'V2', 'V3', 'A1', 'A2', 'A3', 'J1', 'J2', 'J3', 'M']       
    snapshot=f['/Step#%d' % ngroup]

    ntot=snapshot.attrs['N_SINGLE']
    tphys=snapshot.attrs['Time']
    
    i_d=snapshot['NAM']
    x,y,z=snapshot['X1'],snapshot['X2'],snapshot['X3']
    vx,vy,vz=snapshot['V1'],snapshot['V2'],snapshot['V3']
    m=snapshot['M']
    
    kw,lum,rc,rs,te=snapshot['KW'],np.log10(snapshot['L']),snapshot['RC'],snapshot['RS'],snapshot['TE']
    pot=snapshot['POT']

    if 'Binaries' in snapshot:
        binaries=True
    else:
        binaries=False

    return tphys,ntot,x,y,z,vx,vy,vz,m,i_d,pot,kw,lum,rc,rs,te,binaries
    
def _get_nbody6pp_hdf5_binaries(f,ngroup=0,**kwargs):
        
    #datakeys=['A', 'ECC', 'G', 'KW1', 'KW2', 'KWC', 'L1', 'L2', 'M1', 'M2', 'MC1', 'MC2', 'NAM1', 'NAM2', 'NAMC', 'P', 'POT', 'RC1', 'RC2', 'RS1', 'RS2', 'TE1', 'TE2', 'VC1', 'VC2', 'VC3', 'VR1', 'VR2', 'VR3', 'XC1', 'XC2', 'XC3', 'XR1', 'XR2', 'XR3']      
    snapshot=f['/Step#%d/Binaries' % ngroup]

    a,ecc,gb=snapshot['A'],snapshot['ECC'],snapshot['G']
    kw1,kw2,kwc=snapshot['KW1'],snapshot['KW2'],snapshot['KWC']
    l1,l2,m1,m2,mc1,mc2=np.log10(snapshot['L1']),np.log10(snapshot['L2']),snapshot['M1'],snapshot['M2'],snapshot['MC1'],snapshot['MC2']
    id1,id2,idc=snapshot['NAM1'],snapshot['NAM2'],snapshot['NAMC']
    pb,pot,rc1,rc2,rs1,rs2,te1,te2=snapshot['P'],snapshot['POT'],snapshot['RC1'],snapshot['RC2'],snapshot['RS1'],snapshot['RS2'],snapshot['TE1'],snapshot['TE2']
    vc1,vc2,vc3,vr1,vr2,vr3=snapshot['VC1'],snapshot['VC2'],snapshot['VC3'],snapshot['VR1'],snapshot['VR2'],snapshot['VR3']
    xc1,xc2,xc3,xr1,xr2,xr3=snapshot['XC1'],snapshot['XC2'],snapshot['XC3'],snapshot['XR1'],snapshot['XR2'],snapshot['XR3']

    return a,ecc,gb,kw1,kw2,kwc,l1,l2,m1,m2,mc1,mc2,id1,id2,idc,pb,pot,rc1,rc2,rs1,rs2,te1,te2,vc1,vc2,vc3,vr1,vr2,vr3,xc1,xc2,xc3,xr1,xr2,xr3