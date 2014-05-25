#!/bin/env python
#
# Python-written tasks to automate the data reduction for XMM data
import subprocess
import glob
import os
import shutil


# EDIT HERE ====================================================
os.environ['SAS_ODF'] = os.path.abspath(glob.glob('../rpcdata/*SUM.SAS')[0])
os.environ['SAS_CCF'] = os.path.abspath(glob.glob('../rpcdata/ccf.cif')[0])

shutil.copyfile('../pn_clean.ds', 'pn_clean_barycen.ds')
subprocess.call(['barycen', 'table=pn_clean_barycen.ds:EVENTS'])
table = 'pn_clean_barycen.ds'

pattern = 4

srcregionfile = 'src.reg'
bkgregionfile = 'bkg.reg'

rangestring = ['0.3-10keV', '0.3-2keV', '2-4.5keV', '4.5-10keV', '2-10keV']
emins = [300, 300, 2000, 4500, 2000]
emaxs = [10000, 2000, 4500, 10000, 10000]

# Edit only if necessary ++++++++++++++++++++++
#srcregion = 'circle(1000,2000,200)'
src = open(srcregionfile, 'r')
srcregion = src.readlines()[-1].strip()
src.close()

#bkgregion = 'circle(1000,2000,200)'
bkg = open(bkgregionfile, 'r')
bkgregion = bkg.readlines()[-1].strip()
bkg.close()

#========================================== END of EDIT block =======

for i, range in enumerate(rangestring):

    fsrcname = 'pnevts_src_{0}.ds'.format(range)
    fimgname = 'pnevts_src_img_{0}.ds'.format(range)

    exp = "expression=#XMMEA_EP && (PI IN [{0}:{1}]) && PATTERN <={3} && \
FLAG==0 && ((X,Y) IN {2})".format(emins[i], emaxs[i], srcregion, pattern)

    subprocess.call(['evselect', 'table={0}'.format(table),
        'energycolumn=PI', 'xcolumn=X', 'ycolumn=Y',
        'keepfilteroutput=yes', 'withfilteredset=yes', 'withimageset=yes',
        'filteredset={0}'.format(fsrcname), 'imageset={0}'.format(fimgname),
        exp])

subprocess.call(['ds9', fimgname, '-zoom', '2', '-log', '-cmap', 'heat',
    '-region', 'load', srcregionfile])
