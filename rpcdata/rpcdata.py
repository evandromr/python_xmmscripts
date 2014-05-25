#!/usr/bin/env python
#
# Script to reprocess observation data files
import subprocess
import shutil
import glob
import os
import astropy.io.fits as fits


# EDIT HERE =======================================================
#odffolder = '/home/user/xmm/obs/hd000000/2000jan01/odf'
odffolder = os.path.abspath(raw_input("Enter path to ODF data: "))
os.environ['SAS_IMAGEVIEWER'] = 'ds9'
os.environ['SAS_MEMORY_MODEL'] = 'high'
os.environ['SAS_VERBOSITY'] = '0'
os.environ['XPA_METHOD'] = 'local'
# =================================================================


#Point SAS_ODF to the raw observation data directory
os.environ['SAS_ODF'] = odffolder

print 'Building calibration files index...'
subprocess.call(['cifbuild'])

#Point to the calibration index
os.environ['SAS_CCF'] = os.path.abspath('ccf.cif')

#Create observation summary
print 'Creating observation summary...'
subprocess.call(['odfingest'])

#Point to the Summary file
os.environ['SAS_ODF'] = os.path.abspath(glob.glob('*SUM.SAS')[0])

#Reprocess data
print 'Running epproc...'
subprocess.call(['epproc'])  # PN camera
print 'Running emproc...'
subprocess.call(['emproc'])  # MOS cameras
#(one can use "(ep/em)chain" instead, see the SAS documentation)

shutil.copyfile(glob.glob('*PN*ImagingEvts.ds')[0], 'pnevents.ds')
shutil.copyfile(glob.glob('*MOS1*ImagingEvts.ds')[0], 'm1events.ds')
shutil.copyfile(glob.glob('*MOS2*ImagingEvts.ds')[0], 'm2events.ds')

shutil.copyfile('pnevents.ds', 'pnevents_barycen.ds')
shutil.copyfile('m1events.ds', 'm1events_barycen.ds')
shutil.copyfile('m2events.ds', 'm2events_barycen.ds')

subprocess.call(['barycen', 'table=pnevents_barycen.ds:EVENTS'])
subprocess.call(['barycen', 'table=m1events_barycen.ds:EVENTS'])
subprocess.call(['barycen', 'table=m2events_barycen.ds:EVENTS'])

timefile = open('times.dat', 'w')

tstarts = [fits.getval('pnevents_barycen.ds', 'TSTART', extname='EVENTS'),
           fits.getval('m1events_barycen.ds', 'TSTART', extname='EVENTS'),
           fits.getval('m2events_barycen.ds', 'TSTART', extname='EVENTS')]

tstops = [fits.getval('pnevents_barycen.ds', 'TSTOP', extname='EVENTS'),
          fits.getval('m1events_barycen.ds', 'TSTOP', extname='EVENTS'),
          fits.getval('m2events_barycen.ds', 'TSTOP', extname='EVENTS')]

timefile.write('PN Times: tstart={0}, tstop={1}, duration={2}\n'.format(
    tstarts[0], tstops[0], tstops[0]-tstarts[0]))
timefile.write('MOS1 Times: tstart={0}, tstop={1}, duration={2}\n'.format(
    tstarts[0], tstops[1], tstops[1]-tstarts[1]))
timefile.write('MOS2 Times: tstart={0}, tstop={1}, duration={2}\n'.format(
    tstarts[2], tstops[2], tstops[2]-tstarts[2]))

timefile.write('\n')
timefile.write('Common Time: \n')
timefile.write('tstart={0} \n'.format(max(tstarts)))
timefile.write('tstop={0} \n'.format(min(tstops)))
timefile.write('duration={0}'.format(min(tstops)-max(tstarts)))

print timefile.readlines()

timefile.close()

#Check everything
subprocess.call(['sasversion'])
