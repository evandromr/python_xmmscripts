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
    os.environ['SAS_VERBOSITY']='3'
    os.environ['XPA_METHOD']='local'

    return os.getcwd()


def rpcdata(odffolder):
    ' creates a new Summary File for the observation and Reprocess XMM data'

    os.mkdir('rpcdata/')
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
    os.environ['SAS_ODF']=os.getcwd()+'/'+glob.glob('*SUM.SAS')[0]

    #Reprocess data
    subprocess.call(['epproc'])  # PN camera
    subprocess.call(['emproc'])  # MOS cameras
    #(one can use "(ep/em)chain" instead, see the SAS documentation)
    os.chdir('../')

    return xmm_rpcdata


def clearevents(camera):
    ' Clear event file for times with hight background flares '

    if camera.upper() == 'PN':
        exp1='expression=#XMMEA_EP && (PI > 10000 && PI <12000) && PATTERN==0'
        expgti='expression=RATE<=0.4'
        exp2='expression=#XMMEA_EP && gti(PN_gti.ds, TIME) && (PI > 150)'
        exp3='expression=#XMMEA_EP && (PI>300 && PI<12000) && PATTERN<=4 && FLAG==0'
    elif camera.upper() == 'MOS1':
        exp1='expression=#XMMEA_EM && (PI > 10000) && PATTERN==0'
        expgti='expression=RATE<=0.35'
        exp2='expression=#XMMEA_EM && gti(MOS1_gti.ds, TIME) && (PI > 150)'
        exp3='expression=#XMMEA_EM && (PI>150 && PI<10000) && PATTERN<=12 && FLAG==0'
    elif camera.upper() == 'MOS2':
        exp1='expression=#XMMEA_EM && (PI > 10000) && PATTERN==0'
        expgti='expression=RATE<=0.35'
        exp2='expression=#XMMEA_EM && gti(MOS2_gti.ds, TIME) && (PI > 150)'
        exp3='expression=#XMMEA_EM && (PI>150 && PI<10000) && PATTERN<=12 && FLAG==0'
    else:
        print "Something is wrong, the camera doesn't exist"
        raw_input('Please "Ctrl-C" to terminate execution and check errors')

    os.mkdir(camera.lower())
    os.chdir(camera.lower())

    evtfile=glob.glob('../rpcdata/*{0}*Evts.ds'.format(camera.upper()))[0]

    # Extract lightcurve for energy 10keV < E and pattern='single'
    subprocess.call(['evselect', 'table={0}:EVENTS'.format(evtfile),
        'withrateset=yes', 'rateset={0}_rate.ds'.format(camera.upper()),
        'maketimecolumn=yes', 'makeratecolumn=yes', 'timebinsize=100',
        'timecolumn=TIME', exp1])

    # Saves a plot of the lightcurve created
    subprocess.call(['dsplot', 'table={0}_rate.ds:RATE'.format(camera.upper()),
    'withx=yes', 'x=TIME', 'withy=yes', 'y=RATE',
    'plotter="xmgrace -hardcopy -printfile {0}_rate.ps"'.format(camera.upper())])

    # Creates a GTI (good time interval)
    subprocess.call(['tabgtigen', 'table={0}_rate.ds'.format(camera.upper()),
        'gtiset={0}_gti.ds'.format(camera.upper()), expgti])

    # Creates a clean Events File with the events on the GTI
    subprocess.call(['evselect', 'table={0}:EVENTS'.format(evtfile),
        'withfilteredset=yes', 'keepfilteroutput=yes',
        'filteredset={0}_clean.ds'.format(camera.upper()), exp2])

    # Creates a lightcurve like PN_rate.ds but cleaned, for comparison
    subprocess.call(['evselect',
        'table={0}_clean.ds:EVENTS'.format(camera.upper()),
        'withrateset=yes', 'rateset={0}_rate_clean.ds'.format(camera.upper()),
        'maketimecolumn=yes', 'makeratecolumn=yes', 'timecolumn=TIME',
        'timebinsize=100', exp1])

    # Saves a plot of the cleaned lightcurve
    subprocess.call(['dsplot',
        'table={0}_rate_clean.ds:RATE'.format(camera.upper()), 'withx=yes',
        'x=TIME', 'withy=yes', 'y=RATE',
        'plotter=xmgrace -hardcopy -printfile {0}_rate_clean.ps'.format(camera.upper())])

    # Creates before/after images for doubled-check visual analysis
    subprocess.call(['evselect', 'table={0}'.format(evtfile),
        'withimageset=true', 'imageset={0}_image.ds'.format(camera.upper()),
        'xcolumn=X', 'ycolumn=Y', 'ximagebinsize=80', 'yimagebinsize=80',
        'imagebinning=binSize', exp3])

    subprocess.call(['evselect', 'table={0}_clean.ds'.format(camera.upper()),
        'withimageset=true', 'xcolumn=X', 'ycolumn=Y',
        'imageset={0}_image_clean.ds'.format(camera.upper()),
         'ximagebinsize=80', 'yimagebinsize=80', 'imagebinning=binSize', exp3])

    os.chdir('../')
    return True


def copyregions(ppsfolder, workfolder, camera):
    ' copy the *REGION* file from the ppsfolder to the camera folder '

    os.chdir(ppsfolder)

    origin=glob.glob('*REGION*')[0]
    destiny=workfolder+'/'+camera.lower()+'/regions.reg'
    subprocess.call(['cp', origin, destiny])

    os.chdir(workfolder)
    return True

def copypnregions(camera):
    ' copy the regions from the pn camera'

    subprocess.call(['cp', 'pn/src.reg', camera.lower()+'/src.reg'])
    subprocess.call(['cp', 'pn/bkg.reg', camera.lower()+'/bkg.reg'])
    subprocess.call(['cp', 'pn/src_evt.reg', camera.lower()+'/src_evt.reg'])

    return True


def checkregions(camera):
    ' check if existent regions are consistent '

    print 'Check if the regions are Ok'
    print ''

    os.chdir(camera.lower())

    subprocess.call(['ds9', '{0}_image_clean.ds'.format(camera.upper()),
        '-regions', 'load', 'regions.reg',
        '-regions', 'load', 'src.reg',
        '-regions', 'load', 'bkg.reg',
        '-regions', 'load', 'src_evt.reg',
        '-cmap', 'Heat', '-log', '-zoom', '2'])

    os.chdir('../')
    return True


def promptforregions(camera):
    ' Prompt the user to select the necessary region file '

    print "Select the regions src.reg, bkg.reg and src_evt.reg"
    print ""

    os.chdir(camera.lower())

    subprocess.call(['ds9', '{0}_image_clean.ds'.format(camera.upper()),
        '-regions', 'load', 'regions.reg', '-cmap', 'Heat',
        '-log', '-zoom', '2'])

    os.chdir('../')
    return True


def extractspec(camera):
    ' Extract a spectra '

    os.mkdir('{0}/spec'.format(camera.lower()))
    os.chdir('{0}/spec'.format(camera.lower()))
    subprocess.call(['cp', '../src.reg', './'])
    subprocess.call(['cp', '../bkg.reg', './'])

    src = open('src.reg')
    srcregion = src.readlines()[-1].strip()
    src.close()

    bkg = open('bkg.reg')
    bkgregion = bkg.readlines()[-1].strip()
    bkg.close()

    srcspc='{0}_srcspc.ds'.format(camera.upper())
    srcimg='{0}_srcimg.ds'.format(camera.upper())
    bkgspc='{0}_bkgspc.ds'.format(camera.upper())
    bkgimg='{0}_bkgimg.ds'.format(camera.upper())
    rmf='{0}.rmf'.format(camera.upper())
    arf='{0}.arf'.format(camera.upper())
    table='../{0}_clean.ds'.format(camera.upper())


    if camera.upper() == 'PN':
        maxchan=20479
        srcexp='expression=#XMMEA_EP && PATTERN<=4 && FLAG==0 && ((X,Y) IN {0})'.format(srcregion)
        bkgexp='expression=#XMMEA_EP && PATTERN<=4 && FLAG==0 && ((X,Y) IN {0})'.format(bkgregion)
    elif camera.upper() == 'MOS1':
        maxchan=11999
        srcexp='expression=#XMMEA_EM && PATTERN<=12 && FLAG==0 && ((X,Y) IN {0})'.format(srcregion)
        bkgexp='expression=#XMMEA_EM && PATTERN<=12 && FLAG==0 && ((X,Y) IN {0})'.format(bkgregion)
    elif camera.upper() == 'MOS2':
        maxchan=11999
        srcexp='expression=#XMMEA_EM && PATTERN<=12 && FLAG==0 && ((X,Y) IN {0})'.format(srcregion)
        bkgexp='expression=#XMMEA_EM && PATTERN<=12 && FLAG==0 && ((X,Y) IN {0})'.format(bkgregion)
    else:
        print "Something is wrong, the camera doesn't exist"
        raw_input('Please "Ctrl-C" to terminate execution and check errors')


    # Extracts a source+background spectrum
    subprocess.call(['evselect', 'table={0}:EVENTS'.format(table),
    'withspectrumset=yes', 'spectrumset={0}'.format(srcspc),
    'energycolumn=PI', 'withspecranges=yes', 'spectralbinsize=5',
    'specchannelmax={0}'.format(maxchan), 'specchannelmin=0',
    'withimageset=yes', 'imageset={0}'.format(srcimg),
    'xcolumn=X', 'ycolumn=Y', srcexp])

    # Scale the areas of src and bkg regions used
    subprocess.call(['backscale', 'spectrumset={0}'.format(srcspc),
    'withbadpixcorr=yes', 'badpixlocation={0}'.format(table)])

    # Extracts a background spectrum
    subprocess.call(['evselect', 'table={0}:EVENTS'.format(table),
    'withspectrumset=yes', 'spectrumset={0}'.format(bkgspc),
    'energycolumn=PI', 'withspecranges=yes', 'spectralbinsize=5',
    'specchannelmax={0}'.format(maxchan), 'specchannelmin=0',
    'withimageset=yes', 'imageset={0}'.format(bkgimg),
    'xcolumn=X', 'ycolumn=Y', bkgexp])

    # Scale the are of the bkg region used
    subprocess.call(['backscale', 'spectrumset={0}'.format(bkgspc),
    'withbadpixcorr=yes', 'badpixlocation={0}'.format(table)])

    # Generates response matrix
    subprocess.call(['rmfgen', 'rmfset={0}'.format(rmf),
    'spectrumset={0}'.format(srcspc)])

    # Generates ana Ancillary response file
    subprocess.call(['arfgen', 'arfset={0}'.format(arf),
    'spectrumset={0}'.format(srcspc), '--withrmfset=yes', 'detmaptype=psf',
    'rmfset={0}'.format(rmf), 'badpixlocation={0}'.format(table)])

    # Rebin the spectrum and link associated files (output:EPICspec.pha)
    # can be replaced by grppha tool from HEASOFT
    subprocess.call(['specgroup', 'spectrumset={0}'.format(srcspc),
    'mincounts=25', 'oversample=3', 'backgndset={0}'.format(bkgspc),
    'rmfset={0}'.format(rmf), 'arfset={0}'.format(arf),
    'groupedset={0}spec.pha'.format(camera.upper())])

    os.chdir('../../')
    return True


def extractevents(table, fsrcname, fimgname, emin, emax, srcregion, camera):
    ' extract event file from passed region and energy range '

    if camera.upper() == 'PN':
        exp = 'expression=#XMMEA_EP && (PI IN [{0}:{1}]) && PATTERN <=4 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, srcregion)
    elif camera.upper() == 'MOS1':
        exp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, srcregion)
    elif camera.upper() == 'MOS2':
        exp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, srcregion)
    else:
        print "Something is wrong, the camera doesn't exist"
        raw_input('Please "Ctrl-C" to terminate execution and check errors')

    subprocess.call(['evselect', 'table={0}'.format(table),
        'energycolumn=PI', 'xcolumn=X', 'ycolumn=Y',
        'keepfilteroutput=yes', 'withfilteredset=yes', 'withimageset=yes',
        'filteredset={0}'.format(fsrcname), 'imageset={0}'.format(fimgname),
        exp])

    return True


def showevtreg(fimgname):
    ' Show extracted image and region to visual check '

    subprocess.call(['ds9', fimgname, '-zoom', '2', '-log', '-cmap', 'heat',
    '-region', 'load', 'src_evt.reg'])
    return True


def events(camera):
    ' Extract event files for the src in diferents energy ranges '

    os.mkdir('{0}/events/'.format(camera.lower()))
    
    evt = glob.glob('rpcdata/*{0}*Evts.ds'.format(camera.upper()))[0]
    subprocess.call(['cp', evt,
        '{0}/events/{0}evts_barycen.ds'.format(camera.lower())])
    subprocess.call(['cp', '{0}/src_evt.reg'.format(camera.lower()),
        '{0}/events/src_evt.reg'.format(camera.lower())])

    os.chdir('{0}/events/'.format(camera.lower()))

    # Make barycentric correction on the clean event file
    subprocess.call(['barycen',
        'table={0}evts_barycen.ds:EVENTS'.format(camera.lower())])

    # Get the coordinates from the .reg file
    src = open('src_evt.reg')
    srcregion=src.readlines()[-1].strip()
    src.close()

    table='{0}evts_barycen.ds'.format(camera.lower())

    ranges=['0310', '032', '245', '4510']
    emins=[300, 300, 2000, 4500]
    emaxs=[10000, 2000, 4500, 10000]

    for i in xrange(len(ranges)):
        fsrcname='{0}evts_src_{1}keV.ds'.format(camera.lower(), ranges[i])
        fimgname='{0}evts_src_img_{1}keV.ds'.format(camera.lower(), ranges[i])
        emin=emins[i]
        emax=emaxs[i]
        extractevents(table, fsrcname, fimgname, emin, emax, srcregion, camera)

    showevtreg(fimgname)
    os.chdir('../../')

    return True


def extractlc(bin, range, emin, emax, table, srcregion, bkgregion, camera):
    ''' Extract a barycentric corrected lightcurve
        in the energy range['emin':'emax'], with time bins of 'bin'
    '''

    srclc='{0}_lc_src_{1}keV_bin{2}.ds'.format(camera.upper(), range, bin)
    bkglc='{0}_lc_bkg_{1}keV_bin{2}.ds'.format(camera.upper(), range, bin)
    netlc='{0}_lc_net_{1}keV_bin{2}.ds'.format(camera.upper(), range, bin)
    srcimg='{0}_src_img_{1}keV_bin{2}.ds'.format(camera.upper(), range, bin)
    bkgimg='{0}_bkg_img_{1}keV_bin{2}.ds'.format(camera.upper(), range, bin)
    psimg='{0}_lc_net_{1}keV_bin{2}.ps'.format(camera.upper(), range, bin)

    if camera.upper() == 'PN':
        srcexp = 'expression=#XMMEA_EP && (PI IN [{0}:{1}]) && PATTERN <=4 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, srcregion)
        bkgexp = 'expression=#XMMEA_EP && (PI IN [{0}:{1}]) && PATTERN <=4 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, bkgregion)
    elif camera.upper() == 'MOS1':
        srcexp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, srcregion)
        bkgexp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, bkgregion)
    elif camera.upper() == 'MOS2':
        srcexp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, srcregion)
        bkgexp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, bkgregion)
    else:
        print "Something is wrong, the camera doesn't exist"
        raw_input('Please "Ctrl-C" to terminate execution and check errors')

    # Extract a lightcurve for the src+bkg region for single and double events
    subprocess.call(['evselect', 'table={0}'.format(table),
    'energycolumn=PI', 'withrateset=yes', 'rateset={0}'.format(srclc),
    'timebinsize={0}'.format(bin), 'maketimecolumn=yes', 'makeratecolumn=yes',
    'withimageset=yes', 'imageset={0}'.format(srcimg),
    'xcolumn=X', 'ycolumn=Y', srcexp])

    # Extract a lightcurve for the bkg region for single and double events
    subprocess.call(['evselect', 'table={0}'.format(table),
    'energycolumn=PI', 'withrateset=yes', 'rateset={0}'.format(bkglc),
    'timebinsize={0}'.format(bin), 'maketimecolumn=yes', 'makeratecolumn=yes',
    'withimageset=yes', 'imageset={0}'.format(bkgimg),
    'xcolumn=X', 'ycolumn=Y', bkgexp])

    # Apply corrections and creates the net lightcurve
    subprocess.call(['epiclccorr', 'eventlist={0}'.format(table),
    'outset={0}'.format(netlc), 'srctslist={0}'.format(srclc),
    'applyabsolutecorrections=yes', 'withbkgset=yes',
    'bkgtslist={0}'.format(bkglc)])

    # Save the net lightcurve visualization
    subprocess.call(['dsplot', 'table={0}'.format(netlc), 'withx=yes',
    'withy=yes', 'x=TIME', 'y=RATE',
    'plotter=xmgrace -hardcopy -printfile {0}'.format(psimg)])

    return True


def lightcurves(camera):
    ' creates lightcurves from the event files '

    os.mkdir('{0}/lightcurves/'.format(camera.lower()))
    evt = glob.glob('rpcdata/*{0}*Evts.ds'.format(camera.upper()))[0]
    subprocess.call(['cp', evt,
        '{0}/lightcurves/{0}evts_barycen.ds'.format(camera.lower())])
    os.chdir('{0}/lightcurves/'.format(camera.lower()))
    subprocess.call(['cp', '../src.reg', './'])
    subprocess.call(['cp', '../bkg.reg', './'])

    src = open('src.reg', 'r')
    srcregion = src.readlines()[-1].strip()
    src.close()

    bkg = open('bkg.reg', 'r')
    bkgregion = bkg.readlines()[-1].strip()
    bkg.close()

    # Make barycentric correction on the clean event file
    subprocess.call(['barycen',
        'table={0}evts_barycen.ds:EVENTS'.format(camera.lower())])
    table='{0}evts_barycen.ds'.format(camera.lower())

    bins = [5, 10, 50, 150, 350, 500]
    ranges = ['0310', '032', '245', '4510']
    emins = [300, 300, 2000, 4500]
    emaxs = [10000, 2000, 4500, 10000]

    for bin in bins:
        for i in xrange(len(ranges)):
            extractlc(bin, ranges[i], emins[i], emaxs[i],
                    table, srcregion, bkgregion, camera)

    os.chdir('../../')
    return True


def findinterval():
    ' Find common interval for time analysis '

    pnevents=fits.open(glob.glob('../../rpcdata/*PN*ImagingEvts.ds')[0])
    mos1events=fits.open(glob.glob('../../rpcdata/*MOS1*ImagingEvts.ds')[0])
    mos2events=fits.open(glob.glob('../../rpcdata/*MOS2*ImagingEvts.ds')[0])

    listtimes1 = [pnevents['EVENTS'].header['TSTART'],
        mos1events['EVENTS'].header['TSTART'],
        mos2events['EVENTS'].header['TSTART']]

    listtimes2 = [pnevents['EVENTS'].header['TSTOP'],
        mos1events['EVENTS'].header['TSTOP'],
        mos2events['EVENTS'].header['TSTOP']]

    tstart=max(listtimes1)
    tstop=min(listtimes2)

    pnevents.close()
    mos1events.close()
    mos2events.close()

    return tstart, tstop

def extract_timedlc(bin, range, emin, emax, table, srcregion, bkgregion,
        camera, tstart, tstop):
    ''' Extract a barycentric corrected lightcurve
        in the energy range['emin':'emax'], with time bins of 'bin'
    '''

    srclc='{0}_lc_src_{1}keV_bin{2}_timed.ds'.format(camera.upper(), range, bin)
    bkglc='{0}_lc_bkg_{1}keV_bin{2}_timed.ds'.format(camera.upper(), range, bin)
    netlc='{0}_lc_net_{1}keV_bin{2}_timed.ds'.format(camera.upper(), range, bin)
    srcimg='{0}_src_img_{1}keV_bin{2}_timed.ds'.format(camera.upper(), range, bin)
    bkgimg='{0}_bkg_img_{1}keV_bin{2}_timed.ds'.format(camera.upper(), range, bin)
    psimg='{0}_lc_net_{1}keV_bin{2}_timed.ps'.format(camera.upper(), range, bin)

    if camera.upper() == 'PN':
        srcexp = 'expression=#XMMEA_EP && (PI IN [{0}:{1}]) && PATTERN <=4 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, srcregion)
        bkgexp = 'expression=#XMMEA_EP && (PI IN [{0}:{1}]) && PATTERN <=4 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, bkgregion)
    elif camera.upper() == 'MOS1':
        srcexp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, srcregion)
        bkgexp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, bkgregion)
    elif camera.upper() == 'MOS2':
        srcexp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, srcregion)
        bkgexp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, bkgregion)
    else:
        print "Something is wrong, the camera doesn't exist"
        raw_input('Please "Ctrl-C" to terminate execution and check errors')

    # Extract a lightcurve for the src+bkg region for single and double events
    subprocess.call(['evselect', 'table={0}'.format(table),
    'energycolumn=PI', 'withrateset=yes', 'rateset={0}'.format(srclc),
    'timebinsize={0}'.format(bin), 'maketimecolumn=yes', 'makeratecolumn=yes',
    'withimageset=yes', 'imageset={0}'.format(srcimg), 'xcolumn=X',
    'ycolumn=Y', 'timemin={0}'.format(tstart), 'timemax={0}'.format(tstop),
    srcexp])

    # Extract a lightcurve for the bkg region for single and double events
    subprocess.call(['evselect', 'table={0}'.format(table),
    'energycolumn=PI', 'withrateset=yes', 'rateset={0}'.format(bkglc),
    'timebinsize={0}'.format(bin), 'maketimecolumn=yes', 'makeratecolumn=yes',
    'withimageset=yes', 'imageset={0}'.format(bkgimg), 'xcolumn=X',
    'ycolumn=Y', 'timemin={0}'.format(tstart), 'timemax={0}'.format(tstop),
    bkgexp])

    # Apply corrections and creates the net lightcurve
    subprocess.call(['epiclccorr', 'eventlist={0}'.format(table),
    'outset={0}'.format(netlc), 'srctslist={0}'.format(srclc),
    'applyabsolutecorrections=yes', 'withbkgset=yes',
    'bkgtslist={0}'.format(bkglc)])

    # Save the net lightcurve visualization
    subprocess.call(['dsplot', 'table={0}'.format(netlc), 'withx=yes',
    'withy=yes', 'x=TIME', 'y=RATE',
    'plotter=xmgrace -hardcopy -printfile {0}'.format(psimg)])

    return True


def timed_lightcurves(camera):
    ' creates lightcurves from the event files '

    os.mkdir('{0}/timed_lightcurves/'.format(camera.lower()))
    evt = glob.glob('rpcdata/*{0}*Evts.ds'.format(camera.upper()))[0]
    subprocess.call(['cp', evt,
        '{0}/timed_lightcurves/{0}evts_barycen.ds'.format(camera.lower())])
    os.chdir('{0}/timed_lightcurves/'.format(camera.lower()))
    subprocess.call(['cp', '../src.reg', './'])
    subprocess.call(['cp', '../bkg.reg', './'])

    src = open('src.reg', 'r')
    srcregion = src.readlines()[-1].strip()
    src.close()

    bkg = open('bkg.reg', 'r')
    bkgregion = bkg.readlines()[-1].strip()
    bkg.close()

    # Make barycentric correction on the clean event file
    subprocess.call(['barycen',
        'table={0}evts_barycen.ds:EVENTS'.format(camera.lower())])
    table='{0}evts_barycen.ds'.format(camera.lower())

    bins = [5, 10, 50, 150, 350, 500]
    ranges = ['0310', '032', '245', '4510']
    emins = [300, 300, 2000, 4500]
    emaxs = [10000, 2000, 4500, 10000]

    tstart, tstop = findinterval()

    for bin in bins:
        for i in xrange(len(ranges)):
            extract_timedlc(bin, ranges[i], emins[i], emaxs[i], table, srcregion,
                    bkgregion, camera, tstart, tstop)

    os.chdir('../../')
    return True
