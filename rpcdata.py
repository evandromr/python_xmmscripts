#!/usr/bin/env python
#
# Script to reprocess observation data files
#
import os
import subprocess
import glob


#Raw observation data directory
odffolder = '/home/evandro/xmm/obs/hd000000/2000jan01/odf'

# Pipeline processed data directory
# ppsfolder = '/home/evandro/xmm/obs/hd000000/2000jan01/pps'
# cp $ppsfolder/*REGION* ./regions.reg

os.environ['SAS_IMAGEVIEWER'] = 'ds9'
os.environ['SAS_MEMORY_MODEL'] = 'high'
os.environ['SAS_VERBOSITY'] = '3'
os.environ['XPA_METHOD'] = 'local'

os.mkdir('rpcdata/')
os.chdir('rpcdata/')

#Point SAS_ODF to the raw observation data directory
os.environ['SAS_ODF'] = odffolder

#Build calibration files index
subprocess.call(['cifbuild'])

#Point to the calibration index
os.environ['SAS_CCF'] = os.getcwd()+'/ccf.cif'

#Create observation summary
subprocess.call(['odfingest'])

#Point to the Summary file
os.environ['SAS_ODF'] = os.getcwd()+'/'+glob.glob('*SUM.SAS')[0]

#Reprocess data
subprocess.call(['epproc'])  # PN camera
subprocess.call(['emproc'])  # MOS cameras
#(one can use "(ep/em)chain" instead, see the SAS documentation)

#Check everything
subprocess.call(['sasversion'])
os.chdir('../')
