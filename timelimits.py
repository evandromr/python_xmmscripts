#!/usr/bin/env python
#
# Discover a common time interval for the 3 epic cameras
#
import os
import glob
from astropy.io import fits

epnevents = os.getcwd()+'/../rpcdata/'+glob.glob('*EPN*ImagingEvts.ds')
em1events = os.getcwd()+'/../rpcdata/'+glob.glob('*MOS1*ImagingEvts.ds')
em2events = os.getcwd()+'/../rpcdata/'+glob.glob('*MOS2*ImagingEvts.ds')

pnevents = fits.open(epnevents)
mos1events = fits.open(em1events)
mos2events = fits.open(em2events)

listtimes1 = [pnevents['EVENTS'].header['TSTART'],
        mos1events['EVENTS'].header['TSTART'],
        mos2events['EVENTS'].header['TSTART']]

listtimes2 = [pnevents['EVENTS'].header['TSTOP'],
        mos1events['EVENTS'].header['TSTOP'],
        mos2events['EVENTS'].header['TSTOP']]

tstart=max(listtimes1)
tstop=min(listtimes2)

pnevents.close()
mos1events.close()
mos2events.close()

timefile = open('commontime.dat','w')
timefile.write(str(tstart)+'/n')
timefile.write(str(timestop))
timefile.close()
