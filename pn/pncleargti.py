#!/usr/bin/env python3

# Script to clear the events file of hight background flare events
# For the pn camera
import subprocess
import glob
import os


# EDIT HERE ===================================================================
os.environ['SAS_ODF'] = os.path.abspath(glob.glob('../rpcdata/*SUM.SAS')[0])
os.environ['SAS_CCF'] = os.path.abspath(glob.glob('../rpcdata/ccf.cif')[0])

pnevents = os.path.abspath('../rpcdata/pnevents.ds')

rateset = "pn_rate.ds"
imgset = "pn_image.ds"
origexp = "#XMMEA_EP && (PI > 10000 && PI < 12000) && (PATTERN==0)"

gtifile = "pn_gti.ds"
gtiexp = "RATE<=0.4"

cleanevt = "pn_clean.ds"
cleanrate = "pn_rate_clean.ds"
cleanimg = "pn_image_clean.ds"
cleanexp = "#XMMEA_EP && gti({0}, TIME) && (PI > 150)".format(gtifile)

imgexp = "#XMMEA_EP && (PI>300 && PI<12000) && PATTERN<=4 && FLAG==0"

# =============================================================================

# Extract lightcurve for energy 10keV < E < 12keV and pattern='single'
subprocess.call(
    ['evselect', 'table={0}:EVENTS'.format(pnevents),
     'withrateset=yes', 'rateset={0}'.format(rateset), 'maketimecolumn=yes',
     'makeratecolumn=yes', 'timebinsize=100', 'timecolumn=TIME',
     'expression={0}'.format(origexp)])

# Saves a plot of the lightcurve created
subprocess.call(
    ['dsplot', 'table={0}:RATE'.format(rateset), 'withx=yes',
     'x=TIME', 'withy=yes', 'y=RATE',
     'plotter=xmgrace -hardcopy -printfile {0}.ps'.format(rateset[:-2])])

# Creates a GTI (good time interval) when RATE < 0.4
subprocess.call(
    ['tabgtigen', 'table={0}'.format(rateset),
     'gtiset={0}'.format(gtifile), 'expression={0}'.format(gtiexp)])

# Creates a clean Events File with the events on the GTI
subprocess.call(
    ['evselect', 'table={0}:EVENTS'.format(pnevents),
     'withfilteredset=yes', 'filteredset={0}'.format(cleanevt),
     'keepfilteroutput=yes',
     'expression={0}'.format(cleanexp)])

# Creates a lightcurve cleaned, for comparison
subprocess.call(
    ['evselect', 'table={0}:EVENTS'.format(cleanevt),
     'withrateset=yes', 'rateset={0}'.format(cleanrate),
     'maketimecolumn=yes', 'makeratecolumn=yes',
     'timecolumn=TIME', 'timebinsize=100',
     'expression={0}'.format(origexp)])

# Saves a plot of the cleaned lightcurve
subprocess.call(
    ['dsplot', 'table={0}:RATE'.format(cleanrate), 'withx=yes',
     'x=TIME', 'withy=yes', 'y=RATE',
     'plotter=xmgrace -hardcopy -printfile {0}.ps'.format(cleanrate[:-2])])

# Creates before/after images for doubled-check visual analysis
subprocess.call(
    ['evselect', 'table={0}'.format(pnevents), 'withimageset=true',
     'imageset={0}'.format(imgset), 'xcolumn=X', 'ycolumn=Y',
     'ximagebinsize=80', 'yimagebinsize=80', 'imagebinning=binSize',
     'expression={0}'.format(imgexp)])

subprocess.call(
    ['evselect', 'table={0}'.format(cleanevt), 'withimageset=true',
     'imageset={0}'.format(cleanimg), 'xcolumn=X', 'ycolumn=Y',
     'ximagebinsize=80', 'yimagebinsize=80', 'imagebinning=binSize',
     'expression={0}'.format(imgexp)])
