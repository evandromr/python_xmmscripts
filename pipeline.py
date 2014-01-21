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

#-----------------------------Reprocess data-----------------------------
print "Reprocessing data"

xmm_rpcdata = pysas.rpcdata(odffolder)

print "End of data reprocessesment"
#------------------------------------------------------------------------

# Find common interval for time analysis
tstart, tstop = pysas.findinterval()

print "Starting the generation of scientific products"

#------------------------ Camera PN -------------------------------------
print "Cleaning PN events..."
clearpnevents()
print "DONE"

# Copy the regions file the pn folder
pysas.copyregions(ppsfolder, workfolder)
pysas.promptforregions()

# -------------------- Spectrum PN --------------------------------------
print "Starting PN spectrum extraction..."
pysas.pnspec()
print "DONE"

## ------------ Events PN ---------------------------------------------------
#echo "Starting PN event files extraction..."
#cd events

#source pneventscript.sh
#cd ..
#echo "DONE"

## ------------ Light Curves PN --------------------------------------------
#echo "Starting PN light curve extraction (full time)"
#cd lightcurves

#source pnlcscript.sh

#cd ..
#echo "DONE"

## ----------- Timed Light Curves PN ---------------------------------------
#echo "Starting PN light curve extraction (timed)"
#cd timed_lightcurves

#source pnlcscript_timed.sh

#cd ..
#echo "DONE"

##============================================================================
##------------- Camera MOS1 --------------------------------------------------
#cd ../mos1
#cp ../pn/src.reg ./
#cp ../pn/bkg.reg ./
#cp ../pn/src_evt.reg ./
#cp ../pn/regions.reg ./
#echo "Cleaning MOS1 event files..."

#source clearmos1evts.sh > clear.log

#echo "DONE"

#echo "Select the regions src.reg, bkg.reg and src_evt.reg"
#ds9 MOS1_image_clean.ds -regions load regions.reg -cmap Heat -log -smooth yes \
#-zoom 4 -regions load src.reg -regions load bkg.reg -regions load src_evt.reg

## ---------- Spectrum MOS1 ------------------------------------------------
#cd spec
#echo "Extracting MOS1 spectrum..."

#source mos1spec.sh > spec.log

#cd ..
#echo "DONE"

## ------------ Events MOS1 -------------------------------------------------
#echo "Starting MOS1 event files extraction..."
#cd events

#source mos1eventscript.sh

#cd ..
#echo "DONE"

## ------------ Light Curves MOS1 -------------------------------------------
#echo "Starting MOS1 light curve extraction (full time)"
#cd lightcurves

#source mos1lcscript.sh

#cd ..
#echo "DONE"

## ----------- Timed Light Curves MOS1 ---------------------------------------
#echo "Starting MOS1 light curve extraction (timed)"
#cd timed_lightcurves

#source mos1lcscript_timed.sh

#cd ..
#echo "DONE"

##===========================================================================
## ---------- Camera MOS2 ---------------------------------------------------
#cd ../mos2
#cp ../mos1/src.reg ./
#cp ../mos1/src_evt.reg ./
#cp ../mos1/bkg.reg ./
#cp ../mos1/regions.reg ./
#echo "Cleaning MOS2 events file"

#source clearmos2evts.sh > clear.log

#echo "DONE"

#echo "Select the regions src.reg, bkg.reg and src_evt.reg"
#ds9 MOS2_image_clean.ds -regions load regions.reg -cmap Heat -log -smooth yes \
#-zoom 4 -regions load src.reg -regions load bkg.reg -regions load src_evt.reg

## ----------- Spectrum MOS2 -------------------------------------------------
#cd spec
#echo "Extracting MOS2 spectrum..."

#source mos2spec.sh > spec.log

#cd ..
#echo "DONE"

## ------------ Events MOS2 --------------------------------------------------
#echo "Starting MOS2 event files extraction..."
#cd events

#source mos2eventscript.sh

#cd ..
#echo "DONE"

## ------------ Light Curves MOS2 --------------------------------------------
#echo "Starting MOS2 light curve extraction (full time)"
#cd lightcurves

#source mos2lcscript.sh

#cd ..
#echo "DONE"

## ----------- Timed Light Curves MOS2 ---------------------------------------
#echo "Starting MOS2 light curve extraction (timed)"
#cd timed_lightcurves

#source mos2lcscript_timed.sh

#cd ..
#echo "DONE"

##---------------------------------------------------------------------------
#cd ../
#echo ""
#echo "Scientific products ready to analysis"
#echo ""
#echo "check the results and log files"
#echo "----------------------------END---------------------------------------"
