#!/bin/env python
#
# Python-written tasks to automate the data reduction for XMM data
import os
import subprocess
import glob
import astropy.io.fits as fits


def definesasvar():
    ''' Define some SAS environment variables like
        level of verbosity, memory use and imageviewer'''

    os.environ['SAS_IMAGEVIEWER']='ds9'
    os.environ['SAS_MEMORY_MODEL']='high'
    os.environ['SAS_VERBOSITY']='5'
    os.environ['XPA_METHOD']='local'

    return os.getcwd()


def rpcdata(odffolder):
    ' creates a new Summary File for the observation and Reprocess XMM data'

    os.chdir('rpcdata/')
    xmm_rpcdata=os.getcwd()

    #Point to Raw Observation Data directory
    os.environ['SAS_ODF']=odffolder

    #Build calibration files index
    subprocess.call(['cifbuild'])

    #Point to the calibration index
    os.environ['SAS_CCF']=os.getcwd()+'/ccf.cif'

    #Create observation summary
    subprocess.call(['odfingest'])

    #Point to the Summary file
    os.environ['SAS_ODF']=glob.glob('*SUM.SAS')[0]

    #Reprocess data
    subprocess.call(['epproc'])  # PN camera
    subprocess.call(['emproc'])  # MOS cameras
    #(one can use "(ep/em)chain" instead, see the SAS documentation)
    os.chdir('..')

    return xmm_rpcdata


def clearpnevents():
    ' Clear PN event file for times with hight background flares '

    os.chdir('pn')
    pnevtfile=glob.glob('rpcdata/*PN*Evts.ds')[0]
    argtable='table='+pnevtfile+':EVENTS'

    # Extract lightcurve for energy 10keV < E < 12keV and pattern='single'
    subprocess.call(['evselect', argtable, 'withrateset=yes',
    'rateset=PN_rate.ds', 'maketimecolumn=yes', 'makeratecolumn=yes',
    'timebinsize=100', 'timecolumn="TIME"',
    'expression="#XMMEA_EP && (PI > 10000 && PI < 12000) && (PATTERN==0)"'])

    # Saves a plot of the lightcurve created
    subprocess.call(['dsplot', 'table=PN_rate.ds:RATE',
    'withx=yes', 'x=TIME', 'withy=yes', 'y=RATE',
    'plotter="xmgrace -hardcopy -printfile "PN_rate.ps""'])

    # Creates a GTI (good time interval) when RATE < 0.4
    subprocess.call(['tabgtigen', 'table=PN_rate.ds', 'gtiset=PN_gti.ds',
    'expression="RATE<=0.4"'])

    # Creates a clean Events File with the events on the GTI
    subprocess.call(['evselect', argtable, 'withfilteredset=yes',
    'filteredset=PN_clean.ds', 'keepfilteroutput=yes',
    'expression="#XMMEA_EP && gti(PN_gti.ds, TIME) && (PI > 150)"'])

    # Creates a lightcurve like PN_rate.ds but cleaned, for comparison
    subprocess.call(['evselect', 'table=PN_clean.ds:EVENTS', 'withrateset=yes',
    'rateset=PN_rate_clean.ds', 'maketimecolumn=yes', 'makeratecolumn=yes',
    'timecolumn="TIME"', 'timebinsize=100',
    'expression="#XMMEA_EP && (PI > 10000 && PI < 12000) && (PATTERN==0)"'])

    # Saves a plot of the cleaned lightcurve
    subprocess.call(['dsplot', 'table=PN_rate_clean.ds:RATE', 'withx=yes',
    'x=TIME', 'withy=yes', 'y=RATE',
    'plotter="xmgrace -hardcopy -printfile "PN_rate_clean.ps""'])

    # Creates before/after images for doubled-check visual analysis
    subprocess.call(['evselect', argtable[:-7], 'withimageset=true',
    'imageset=PN_image.ds', 'xcolumn=X', 'ycolumn=Y',
    'ximagebinsize=80', 'yimagebinsize=80', 'imagebinning=binSize',
    'expression="#XMMEA_EP && (PI>300 && PI<12000) && PATTERN<=4 && FLAG==0"'])

    subprocess.call(['evselect', 'table=PN_clean.ds', 'withimageset=true',
    'imageset=PN_image_clean.ds', 'xcolumn=X', 'ycolumn=Y',
    'ximagebinsize=80', 'yimagebinsize=80', 'imagebinning=binSize',
    'expression="#XMMEA_EP && (PI>300 && PI<12000) && PATTERN<=4 && FLAG==0"'])

    os.chdir('../')
    return True


def copyregions(ppsfolder, workfolder, camera='pn'):
    ' copy the *REGION* file from the ppsfolder to the camera folder '

    os.chdir(ppsfolder)

    origin=glob.glob('*REGION*')
    destiny=workfolder+'/'+camera+'/regions.reg'
    subprocess.call(['cp', regionfile, destiny])

    os.chdir(workfolder)
    return True


def findinterval():
    ' Find common interval for time analysis '

    pnevents=fits.open(glob.glob('rpcdata/*PN*ImagingEvts.ds')[0])
    mos1events=fits.open(glob.glob('rpcdata/*MOS1*ImagingEvts.ds')[0])
    mos2events=fits.open(glob.glob('rpcdata/*MOS2*ImagingEvts.ds')[0])

    listtimes1 = [pnevents['EVENTS'].header['TSTART'],
        mos1events['EVENTS'].header['TSTART'],
        mos2events['EVENTS'].header['TSTART']]

    listtimes2 = [PNevents['EVENTS'].header['TSTOP'],
        mos1events['EVENTS'].header['TSTOP'],
        mos2events['EVENTS'].header['TSTOP']]

    tstart=max(t1)
    tstop=min(t2)

    pnevents.close()
    mos1events.close()
    mos2events.close()

    return tstart, tstop


def promptforregions():
    ' Prompt the user to select the necessary region file '

    print "Select the regions src.reg, bkg.reg and src_evt.reg"
    print ""

    subprocess.call(['ds9', 'PN_image_clean.ds', '-regions', 'load',
        'regions.reg', '-cmap', 'Heat', '-log', '-zoom', '2'])

    return True


def pnspec():
    ' Extract a spectra for the PN camera '

    os.chdir('pn/spec')
    subprocess.call(['cp', '../src.reg', './'])
    subprocess.call(['cp', '../bkg.reg', './'])

    src = open('src.reg')
    srcregion = src.readlines()[-1].strip()
    src.close()

    bkg = open('bkg.reg')
    bkgregion = bkg.readlines()[-1].strip()
    bkg.close()

    pnsrcspc="PN_srcspc.ds"
    pnsrcimg="PN_srcimg.ds"
    pnbkgspc="PN_bkgspc.ds"
    pnbkgimg="PN_bkgimg.ds"
    pnrmf="PN.rmf"
    pnarf="PN.arf"
    pntable='../PN_clean.ds'

    # Extracts a source+background spectrum
    subprocess.call(['evselect', 'table={0}:EVENTS'.format(pntable),
    'withspectrumset=yes', 'spectrumset={0}'.format(pnsrcspc),
    'energycolumn="PI"', 'withspecranges=yes', 'specchannelmax=20479',
    'specchannelmin=0', 'spectralbinsize=5', 'withimageset=yes',
    'imageset={0}'.format(pnsrcimg), 'xcolumn="X"', 'ycolumn="Y"',
    'expression="#XMMEA_EP && PATTERN<=4 && FLAG==0 && ((X,Y) IN "$srcregion")"'.format(srcregion)])

    # Scale the areas of src and bkg regions used
    subprocess.call(['backscale', 'spectrumset={0}'.format(pnsrcspc),
    'withbadpixcorr=yes', 'badpixlocation={0}'.format(pntable)])

    # Extracts a background spectrum
    subprocess.call(['evselect', 'table={0}:EVENTS'.format(pntable),
    'withspectrumset=yes', 'spectrumset={0}'.format(pnbkgspc),
    'energycolumn="PI"', 'withspecranges=yes', 'specchannelmax=20479',
    'specchannelmin=0', 'spectralbinsize=5', 'withimageset=yes',
    'imageset={0}'.format(pnbkgimg), 'xcolumn="X"', 'ycolumn="Y"',
    'expression="#XMMEA_EP && PATTERN<=4 && FLAG==0 && ((X,Y) IN "{0}")"'.format(bkgregion)])

    # Scale the are of the bkg region used
    subprocess.call(['backscale', 'spectrumset={0}'.format(pnbkgspc),
    'withbadpixcorr=yes', 'badpixlocation={0}'.format(pntable)])

    # Generates response matrix
    subprocess.call(['rmfgen', 'rmfset={0}'.format(pnrmf),
    'spectrumset={0}'.format(pnsrcspc)])

    # Generates ana Ancillary response file
    subprocess.call(['arfgen', 'arfset={0}'.format(pnarf),
    'spectrumset={0}'.format(pnsrcspc), '--withrmfset=yes', 'detmaptype=psf',
    'rmfset={0}'.format(pnrmf), 'badpixlocation={0}'.format(pntable)])

    # Rebin the spectrum and link associated files (output:PNspec.pi)
    # can be replaced by grppha tool from HEASOFT
    subprocess.call(['specgroup', 'spectrumset={0}'.format(pnsrcspc),
    'mincounts=25', 'oversample=3', 'backgndset={0}'.format(pnbkgspc),
    'rmfset={0}'.format(pnrmf), 'arfset={0}'.format(pnarf),
    'groupedset=PNspec.pha'])

    os.chdir('../../')
    return True


def extractevents(pntable, fsrcname, fimgname, emin, emax, srcregion):
    ' extract event file from passed region and energy range '

    subprocess.call(['evselect', 'table={0}'.format(pntable),
    'energycolumn="PI"', 'xcolumn="X"', 'ycolumn="Y"',
    'keepfilteroutput=yes', 'withfilteredset=yes', 'withimageset=yes',
    'filteredset={0}'.format(fsrcname), 'imageset={0}'.format(fimgname),
    'expression="#XMMEA_EP && (PI IN [{0}:{1}]) && PATTERN <=4 && FLAG==0 && ((X,Y) IN {2})"'.format(emin, emax, srcregion)])

    return True


def showevtreg(fimgname):
    ' Show extracted image and region to visual check '

    subprocess.call(['ds9', fimgname, '-zoom', '2', '-log', '-cmap', 'heat',
    '-region', 'load', 'src_evt.reg'])
    return True


def pnevents():
    ' Extract event files for the src in diferents energy ranges '

    pnevt = glob.glob('rpcdata/*PN*Evts.ds')[0]
    subprocess.call(['cp', pnevt, 'pn/events/pnevts_barycen.ds'])
    subprocess.call(['cp', 'pn/src_evt.reg', 'pn/events/'])

    os.chdir('pn/events/')

    # Make barycentric correction on the clean event file
    subprocess.call(['barycen', 'table=pnevts_barycen.ds:EVENTS'])

    # Get the coordinates from the .reg file
    src.open('src_evt.reg')
    srcregion=src.readlines()[-1].strip()
    src.close()

    pntable='pnevts_barycen.ds'

    ranges=['0310', '032', '245', '4510']
    emins=[300, 300, 2000, 4500]
    emaxs=[10000, 2000, 4500, 10000]

    for i in xrange(len(ranges)):
        fsrcname='pnevts_src_{0}keV.ds'.format(ranges[i])
        fimgname='pnevts_src_img_{0}keV.ds'.format(ranges[i])
        emin=emins[i]
        emax=emaxs[i]
        extractevents(pntable, fsrcname, fimgname, emin, emax, srcregion)

    showevtreg(fimgname)
    os.chdir('../../')

    return True
