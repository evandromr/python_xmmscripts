#!/usr/bin/env python
# set environments
import os
import glob


os.environ['SAS_IMAGEVIEWER'] = 'ds9'
os.environ['SAS_MEMORY_MODEL'] = 'high'
os.environ['SAS_VERBOSITY'] = '3'
os.environ['XPA_METHOD'] = 'local'
os.environ['SAS_CCF'] = 'rpcdata/ccf.cif'
os.environ['SAS_ODF'] = 'rpcdata/'+glob.glob('*SUM.SAS')[0]
