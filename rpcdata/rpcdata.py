#!/usr/bin/env python3
#
# Script to reprocess observation data files
import subprocess
import shutil
import glob
import os
import astropy.io.fits as fits


# === EDIT HERE ===============================================================
# odffolder = '/data/xmm/0691760101/odf'
odffolder = os.path.abspath(input("Enter path to ODF data: "))
os.environ['SAS_IMAGEVIEWER'] = 'ds9'
os.environ['SAS_MEMORY_MODEL'] = 'high'
os.environ['SAS_VERBOSITY'] = '0'
os.environ['XPA_METHOD'] = 'local'
# =============================================================================

# Point SAS_ODF to the raw observation data directory
os.environ['SAS_ODF'] = odffolder

print('Building calibration files index...')
subprocess.call(['cifbuild'])

# Point to the calibration index
os.environ['SAS_CCF'] = os.path.abspath('ccf.cif')

# Create observation summary
print('Creating observation summary...')
subprocess.call(['odfingest'])

# Point to the Summary file
os.environ['SAS_ODF'] = os.path.abspath(glob.glob('*SUM.SAS')[0])

# Reprocess data
print('Running epproc...')
subprocess.call(['epproc'])  # PN camera
print('Running emproc...')
subprocess.call(['emproc'])  # MOS cameras
# (one can use "(ep/em)chain" instead, see the SAS documentation)

shutil.copyfile(glob.glob('*PN*ImagingEvts.ds')[0], 'pnevents.ds')
shutil.copyfile(glob.glob('*MOS1*ImagingEvts.ds')[0], 'mos1events.ds')
shutil.copyfile(glob.glob('*MOS2*ImagingEvts.ds')[0], 'mos2events.ds')

# Check everything
subprocess.call(['sasversion'])

shutil.copyfile('pnevents.ds', 'pnevents_barycen.ds')
shutil.copyfile('mos1events.ds', 'mos1events_barycen.ds')
shutil.copyfile('mos2events.ds', 'mos2events_barycen.ds')

subprocess.call(['barycen', 'table=pnevents_barycen.ds:EVENTS'])
subprocess.call(['barycen', 'table=mos1events_barycen.ds:EVENTS'])
subprocess.call(['barycen', 'table=mos2events_barycen.ds:EVENTS'])

# Writes observation times to file times.dat
timefile = open('times.dat', 'w')

tstarts = [fits.getval('pnevents_barycen.ds', 'TSTART', extname='EVENTS'),
           fits.getval('mos1events_barycen.ds', 'TSTART', extname='EVENTS'),
           fits.getval('mos2events_barycen.ds', 'TSTART', extname='EVENTS')]

tstops = [fits.getval('pnevents_barycen.ds', 'TSTOP', extname='EVENTS'),
          fits.getval('mos1events_barycen.ds', 'TSTOP', extname='EVENTS'),
          fits.getval('mos2events_barycen.ds', 'TSTOP', extname='EVENTS')]

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

timefile.close()
