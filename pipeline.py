#!/bin/env python
#
# A Python script to automate the generation of scientific products

import sasmetatasks as pysas

#===========================================================================
print "--- Pipeline to data reduction of the XMM-NEWTON space telescope ---"
print "----------------- intended to point sources only -------------------"
#===========================================================================

# the XMM observation folder path
obsfolder='/home/evandromr/XMM/OBS/hd161103/2012sep08'
ppsfolder=obsfolder+'/pps/'
odffolder=obsfolder+'/odf/'
# define secondary SAS variables (verbosity, memory level, etc)
workfolder = pysas.definesasvar()

# ========================== Reprocess data ============================
print "Reprocessing data"
xmm_rpcdata = pysas.rpcdata(odffolder)
print "End of data reprocessesment"
#------------------------------------------------------------------------

print "Starting the generation of scientific products"

# =========================== Clear events =============================
print "Cleaning events..."
pysas.clearevents('pn')
pysas.clearevents('mos1')
pysas.clearevents('mos2')
print "DONE"

# =========================== Spectrum ==================================
print "Starting spectrum extraction..."

pysas.copyregions(ppsfolder, workfolder, 'pn')
pysas.promptforregions('pn')
pysas.extractspec('pn')

pysas.copyregions(ppsfolder, workfolder, 'mos1')
pysas.promptforregions('mos1')
pysas.extractspec('mos1')

pysas.copyregions(ppsfolder, workfolder, 'mos2')
pysas.promptforregions('mos2')
pysas.extractspec('mos2')

print "DONE"

# ====================== Events Files ====================================
print "Starting event files extraction..."
pysas.events('pn')
pysas.events('mos1')
pysas.events('mos2')
print "DONE"

# ======================== Light Curves ==================================
print "Starting light curve extraction (full time)"
pysas.lightcurves('pn')
pysas.lightcurves('mos1')
pysas.lightcurves('mos2')
print "DONE"

# ===================== Timed Light Curves PN ============================
print "Starting light curve extraction (timed)"
pysas.timed_lightcurves('pn')
pysas.timed_lightcurves('mos1')
pysas.timed_lightcurves('mos2')
print "DONE"

# ========================================================================
print ""
print "Scientific products ready to analysis"
print ""
print "check the results and log files"
print "----------------------------END---------------------------------------"
