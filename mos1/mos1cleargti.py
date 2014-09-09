#!/usr/bin/env python

# Script to clear the events file of hight background flare events
# For the mos1 camera
import subprocess
import glob
import os

# EDIT HERE =======================================================
os.environ['SAS_ODF'] = os.path.abspath(glob.glob('../rpcdata/*SUM.SAS')[0])
os.environ['SAS_CCF'] = os.path.abspath(glob.glob('../rpcdata/ccf.cif')[0])

mos1events = os.path.abspath('../rpcdata/mos1events.ds')

rateset = "mos1_rate.ds"
imgset = "mos1_image.ds"
origexp = "#XMMEA_EM && (PI > 10000) && (PATTERN==0)"

gtifile = "mos1_gti.ds"
gtiexp = "RATE<=0.35"

cleanevt = "mos1_clean.ds"
cleanrate = "mos1_rate_clean.ds"
cleanimg = "mos1_image_clean.ds"
cleanexp = "#XMMEA_EM && gti({0}, TIME) && (PI > 150)".format(gtifile)

imgexp = "#XMMEA_EM && (PI>150 && PI<12000) && PATTERN<=12 && FLAG==0"

# =============================================================================

# Extract lightcurve for energy 10keV < E < 12keV and pattern='single'
subprocess.call(
    ['evselect', 'table={0}:EVENTS'.format(mos1events),
     'withrateset=yes', 'rateset={0}'.format(rateset), 'maketimecolumn=yes',
     'makeratecolumn=yes', 'timebinsize=100', 'timecolumn=TIME',
     'expression={0}'.format(origexp)])

# Saves a plot of the lightcurve created
subprocess.call(
    ['dsplot', 'table={0}:RATE'.format(rateset), 'withx=yes',
     'x=TIME', 'withy=yes', 'y=RATE',
     'plotter=xmgrace -hardcopy -printfile {0}.ps'.format(rateset[:-3])])

# Creates a GTI (good time interval) when RATE < 0.4
subprocess.call(
    ['tabgtigen', 'table={0}'.format(rateset),
     'gtiset={0}'.format(gtifile), 'expression={0}'.format(gtiexp)])

# Creates a clean Events File with the events on the GTI
subprocess.call(
    ['evselect', 'table={0}:EVENTS'.format(mos1events),
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
     'plotter=xmgrace -hardcopy -printfile {0}.ps'.format(cleanrate[:-3])])

# Creates before/after images for doubled-check visual analysis
subprocess.call(
    ['evselect', 'table={0}'.format(mos1events), 'withimageset=true',
     'imageset={0}'.format(imgset), 'xcolumn=X', 'ycolumn=Y',
     'ximagebinsize=80', 'yimagebinsize=80', 'imagebinning=binSize',
     'expression={0}'.format(imgexp)])

subprocess.call(
    ['evselect', 'table={0}'.format(cleanevt), 'withimageset=true',
     'imageset={0}'.format(cleanimg), 'xcolumn=X', 'ycolumn=Y',
     'ximagebinsize=80', 'yimagebinsize=80', 'imagebinning=binSize',
     'expression={0}'.format(imgexp)])
