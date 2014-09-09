#!/usr/bin/env python
#coding: utf-8
"""
    A python script to automate the data reduction for X-ray observations from
    the XMM-Newton space telescope
"""

import sasmetatasks as tasks

print """--- Pipeline to data reduction of the XMM-NEWTON space telescope ---
----------------- intended to point sources only -------------------"""

# -------------------- EDIT HERE  --------------------------------------
# the XMM observation folder path
odffolder = str(input("Enter the path to the ODF files: "))
ppsfolder = str(input("Enter the path to the PPS files, or press <Enter>: "))
obsid = str(input("Enter observation ID (for name convention): "))
#----------------------------------------------------------------------

# define secondary SAS variables (verbosity, memory level, etc)
# default: imgviewer='ds9', memorymodel='high',verbosity='3', xpamethod='local'
tasks.definesasvar()

# ========================== Reprocess data ============================
print "Reprocessing data"
rpcdata_dir = tasks.rpcdata(odffolder)
print "End of data reprocessesment"
#------------------------------------------------------------------------

print "Starting the generation of scientific products"

# =========================== Clear events =============================
print "Cleaning events..."
tasks.clearevents(camera='pn', rpcdata_dir=rpcdata_dir)
tasks.clearevents(camera='mos1', rpcdata_dir=rpcdata_dir)
tasks.clearevents(camera='mos2', rpcdata_dir=rpcdata_dir)
print "DONE"

# =========================== Spectrum ==================================
print "Starting spectrum extraction..."
# Pipeline regions
if ppsfolder != '':
    tasks.copyregions(ppsfolder, 'pn')
    tasks.copyregions(ppsfolder, 'mos1')
    tasks.copyregions(ppsfolder, 'mos2')

# PN
tasks.promptforregions('pn')
tasks.extractspec('pn', obsid, evtfile='cleaned')
tasks.extractspec('pn', obsid, evtfile='original', pattern=0, outsubdir='specsingle')

# MOS1
tasks.copypnregions('mos1')
tasks.checkregions('mos1')
tasks.extractspec('mos1', obsid, evtfile='cleaned')
tasks.extractspec('mos1', obsid, evtfile='original', pattern=0,
                  outsubdir='specsingle')

# MOS2
tasks.copypnregions('mos2')
tasks.checkregions('mos2')
tasks.extractspec('mos2', obsid, evtfile='cleaned')
tasks.extractspec('mos2', obsid, evtfile='original', pattern=0,
                  outsubdir='specsingle')
print "DONE"

# ===================== Timed Light Curves PN ============================
print "Starting light curve extraction (timed)..."
tasks.extractlc('pn', rpcdata_dir, timed='yes', outsubdir='timed_lc')
tasks.extractlc('mos1', rpcdata_dir, timed='yes', outsubdir='timed_lc')
tasks.extractlc('mos2', rpcdata_dir, timed='yes', outsubdir='timed_lc')
print "DONE"

# ====================== Events Files ====================================
print "Starting event files extraction..."
tasks.extractevents('pn', evtfile='original')
tasks.extractevents('mos1', evtfile='original')
tasks.extractevents('mos2', evtfile='original')
print "DONE"

# ======================== Light Curves ==================================
print "Starting light curve extraction (full time)..."
tasks.extractlc('pn', rpcdata_dir, timed='no', outsubdir='lc')
tasks.extractlc('mos1', rpcdata_dir, timed='no', outsubdir='lc')
tasks.extractlc('mos2', rpcdata_dir, timed='no', outsubdir='lc')
print "DONE"

# ========================================================================
print "\nScientific products ready to analysis"
print "Check the results and log files"
print "----------------------------END-----------------------------------"
