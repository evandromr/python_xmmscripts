#!/usr/bin/env python
# coding: utf-8
"""
    sasmetatasks
    ------------

    tasks to automate the process of reduction for X-ray data from
    the XMM-Newton observatory.

"""

import os
import shutil
import subprocess
import glob
import astropy.io.fits as fits


def definesasvar(imgviewer='ds9', memorymodel='high', verbosity='3',
                 xpamethod='local'):
    """
        Define some SAS environment variables like
        level of verbosity, memory use and imageviewer
    """

    os.environ['SAS_IMAGEVIEWER'] = imgviewer
    os.environ['SAS_MEMORY_MODEL'] = memorymodel
    os.environ['SAS_VERBOSITY'] = verbosity
    os.environ['XPA_METHOD'] = xpamethod

    return True


def rpcdata(odffolder, process='yes'):
    """creates a new Summary File for the observation and Reprocess XMM data"""

    if not os.path.isdir('rpcdata'):
        os.mkdir('rpcdata/')

    os.chdir('rpcdata/')
    rpcdata_dir = os.getcwd()
    # Point to Raw Observation Data directory
    os.environ['SAS_ODF'] = odffolder
    # Build calibration files index
    if process == 'yes':
        subprocess.call(['cifbuild'])
        # Point to the calibration index
        os.environ['SAS_CCF'] = os.path.abspath('ccf.cif')
        # Create observation summary
        subprocess.call(['odfingest'])
        # Point to the Summary file
        os.environ['SAS_ODF'] = os.path.abspath(glob.glob('*SUM.SAS')[0])
        # Reprocess data
        subprocess.call(['epproc'])  # PN camera
        subprocess.call(['emproc'])  # MOS cameras
    elif process == 'no':
        os.environ['SAS_CCF'] = os.path.abspath('ccf.cif')
        os.environ['SAS_ODF'] = os.path.abspath(glob.glob('*SUM.SAS')[0])
    else:
        print "Something wrong: choose process = 'yes' or 'no'"
        raw_input("Please enter <Ctrl-C> to terminate, and check for errors")

    # (one can use "(ep/em)chain" instead, see the SAS documentation)
    os.chdir('../')

    return rpcdata_dir


def clearevents(camera, rpcdata_dir='../rpcdata'):
    """Clear event file from times with high background flares"""

    curdir = os.getcwd()
    cam = camera.lower()

    if cam == 'pn':
        exp1 = "expression=#XMMEA_EP && (PI>10000&&PI<12000) && (PATTERN==0)"
        expgti = "expression=RATE<=0.4"
        exp2 = "expression=#XMMEA_EP && gti(pn_gti.ds, TIME) && (PI > 150)"
        exp3 = "expression=#XMMEA_EP && (PI>300 && PI<12000) && (PATTERN<=4)\
 && FLAG==0"
    elif cam == 'mos1':
        exp1 = "expression=#XMMEA_EM && (PI>10000) && (PATTERN==0)"
        expgti = "expression=RATE<=0.35"
        exp2 = "expression=#XMMEA_EM && gti(mos1_gti.ds, TIME) && (PI > 150)"
        exp3 = "expression=#XMMEA_EM && (PI>150 && PI<10000) && (PATTERN<=12)\
 && FLAG==0"
    elif cam == 'mos2':
        exp1 = "expression=#XMMEA_EM && (PI>10000) && (PATTERN==0)"
        expgti = "expression=RATE<=0.35"
        exp2 = "expression=#XMMEA_EM && gti(mos2_gti.ds, TIME) && (PI > 150)"
        exp3 = "expression=#XMMEA_EM && (PI>150 && PI<10000) && (PATTERN<=12)\
 && FLAG==0"
    else:
        print "Something is wrong, the camera doesn't exist"
        raw_input("Please press 'Ctrl-C' to terminate and check errors")

    if not os.path.isdir(cam):
        os.mkdir(cam)

    os.chdir(cam)

    shutil.copyfile(os.path.abspath(
        glob.glob(rpcdata_dir+'/'+'*{0}*Evts.ds'.format(camera.upper()))[0]),
        'pnevents.ds')
    evtfile = 'pnevents.ds'

    # Extract lightcurve for energy 10keV < E and pattern='single'
    subprocess.call(
        ['evselect', 'table={0}:EVENTS'.format(evtfile),
         'withrateset=yes', 'rateset={0}_rate.ds'.format(cam),
         'maketimecolumn=yes', 'makeratecolumn=yes', 'timebinsize=100',
         'timecolumn=TIME', exp1])

    # Saves a plot of the lightcurve created
    subprocess.call(
        ['dsplot', 'table={0}_rate.ds:RATE'.format(cam),
         'withx=yes', 'x=TIME', 'withy=yes', 'y=RATE',
         'plotter=xmgrace -hardcopy -printfile {0}_rate.ps'.format(cam)])

    # Creates a GTI (good time interval)
    subprocess.call(
        ['tabgtigen', 'table={0}_rate.ds'.format(cam),
         'gtiset={0}_gti.ds'.format(cam), expgti])

    # Creates a clean Events File with the events on the GTI
    subprocess.call(
        ['evselect', 'table={0}:EVENTS'.format(evtfile), 'withfilteredset=yes',
         'keepfilteroutput=yes', 'filteredset={0}_clean.ds'.format(cam), exp2])

    # Creates a lightcurve like PN_rate.ds but cleaned, for comparison
    subprocess.call(
        ['evselect', 'table={0}_clean.ds:EVENTS'.format(cam),
         'withrateset=yes', 'rateset={0}_rate_clean.ds'.format(cam),
         'maketimecolumn=yes', 'makeratecolumn=yes', 'timecolumn=TIME',
         'timebinsize=100', exp1])

    # Saves a plot of the cleaned lightcurve
    subprocess.call(
        ['dsplot', 'table={0}_rate_clean.ds:RATE'.format(cam), 'withx=yes',
         'x=TIME', 'withy=yes', 'y=RATE',
         'plotter=xmgrace -hardcopy -printfile {0}_rate_clean.ps'.format(cam)])

    # Creates before/after images for doubled-check visual analysis
    subprocess.call(
        ['evselect', 'table={0}'.format(evtfile), 'withimageset=true',
         'imageset={0}_image.ds'.format(cam), 'xcolumn=X', 'ycolumn=Y',
         'ximagebinsize=80', 'yimagebinsize=80', 'imagebinning=binSize', exp3])

    subprocess.call(
        ['evselect', 'table={0}_clean.ds'.format(cam), 'withimageset=true',
         'xcolumn=X', 'ycolumn=Y', 'imageset={0}_image_clean.ds'.format(cam),
         'ximagebinsize=80', 'yimagebinsize=80', 'imagebinning=binSize', exp3])

    os.chdir(curdir)

    return True


def copyregions(ppsfolder, camera):
    """Copy the *REGION* file from the ppsfolder to the camera folder"""

    curdir = os.getcwd()

    if os.path.isdir(ppsfolder):
        os.chdir(ppsfolder)
    else:
        print "PPS folder entered doesn't exist"
        return False

    origin = glob.glob('*REGION*')[0]

    if os.path.isfile(origin):
        destiny = curdir+'/'+camera.lower()+'/regions.reg'
        shutil.copy(origin, destiny)
    else:
        print "Region file doesn't exist"
        return False

    os.chdir(curdir)

    return True


def copypnregions(camera):
    """Copy the regions from the pn camera"""

    shutil.copy('pn/src.reg', camera.lower()+'/src.reg')
    shutil.copy('pn/bkg.reg', camera.lower()+'/bkg.reg')
    shutil.copy('pn/src_evt.reg', camera.lower()+'/src_evt.reg')

    return True


def checkregions(camera):
    """Check if existent regions are consistent"""

    curdir = os.getcwd()

    os.chdir(camera.lower())
    print "Please, check if the regions are Ok"

    subprocess.call(
        ['ds9', '{0}_image_clean.ds'.format(camera.lower()),
         '-regions', 'load', 'regions.reg', '-regions', 'load', 'src.reg',
         '-regions', 'load', 'bkg.reg', '-regions', 'load', 'src_evt.reg',
         '-cmap', 'heat', '-log'])

    os.chdir(curdir)

    return True


def promptforregions(camera):
    """Prompt the user to select the necessary region file"""

    curdir = os.getcwd()

    print "Select the regions src.reg, bkg.reg and src_evt.reg"
    print "WARNING: use the names indicated above and save as a ds9 region\
 with 'Physical' coordinates"

    os.chdir(camera.lower())

    subprocess.call(
        ['ds9', '{0}_image_clean.ds'.format(camera.lower()),
         '-regions', 'load', 'regions.reg', '-cmap', 'Heat', '-log'])

    os.chdir(curdir)

    return True


def extractspec(camera, obsid, evtfile='cleaned', srcfile='src.reg',
                bkgfile='bkg.reg', pattern=99, outsubdir='spec'):
    """Extract a spectra"""

    curdir = os.getcwd()
    cam = camera.lower()

    if evtfile == 'cleaned':
        evtfile = os.path.abspath("{0}/{0}_clean.ds".format(cam))
    elif evtfile == 'original':
        evtfile = os.path.abspath(glob.glob(
            "rpcdata/*{0}*ImagingEvts.ds".format(camera.upper()))[0])
    elif not os.path.isfile(evtfile):
        print "Event file not found, using {0}_clean.ds instead".format(cam)
    else:
        print "Using event file: {0}".format(evtfile)

    if not os.path.isdir('{0}/{1}'.format(cam, outsubdir)):
        os.mkdir('{0}/{1}'.format(cam, outsubdir))

    shutil.copyfile('{0}/src.reg'.format(cam),
                    '{0}/{1}/src.reg'.format(cam, outsubdir))
    shutil.copyfile('{0}/bkg.reg'.format(cam),
                    '{0}/{1}/bkg.reg'.format(cam, outsubdir))

    os.chdir('{0}/{1}'.format(cam, outsubdir))

    src = open('src.reg', 'r')
    srcregion = src.readlines()[-1].strip()
    src.close()

    bkg = open('bkg.reg', 'r')
    bkgregion = bkg.readlines()[-1].strip()
    bkg.close()

    srcspc = '{0}_{1}_srcspc.ds'.format(cam, obsid)
    srcimg = '{0}_{1}_srcimg.ds'.format(cam, obsid)
    bkgspc = '{0}_{1}_bkgspc.ds'.format(cam, obsid)
    bkgimg = '{0}_{1}_bkgimg.ds'.format(cam, obsid)
    rmf = '{0}_{1}.rmf'.format(cam, obsid)
    arf = '{0}_{1}.arf'.format(cam, obsid)

    if cam == 'pn':
        maxchan = 20479
        if (pattern == 99):
            pattern = 4
        srcexp = "expression=#XMMEA_EP && (PATTERN<={1}) && (FLAG==0)\
 && ((X,Y) IN {0})".format(srcregion, pattern)
        bkgexp = "expression=#XMMEA_EP && (PATTERN<={1}) && (FLAG==0)\
 && ((X,Y) IN {0})".format(bkgregion, pattern)

    elif cam == 'mos1':
        if (pattern == 99):
            pattern = 12
        maxchan = 11999
        srcexp = "expression=#XMMEA_EM && (PATTERN<={1}) && (FLAG==0)\
 && ((X,Y) IN {0})".format(srcregion, pattern)
        bkgexp = "expression=#XMMEA_EM && (PATTERN<={1}) && (FLAG==0)\
 && ((X,Y) IN {0})".format(bkgregion, pattern)

    elif cam == 'mos2':
        if (pattern == 99):
            pattern = 12
        maxchan = 11999
        srcexp = "expression=#XMMEA_EM && (PATTERN<={1}) && (FLAG==0)\
 && ((X,Y) IN {0})".format(srcregion, pattern)
        bkgexp = "expression=#XMMEA_EM && (PATTERN<={1}) && (FLAG==0)\
 && ((X,Y) IN {0})".format(bkgregion, pattern)

    else:
        print "Something is wrong, the camera doesn't exist"
        raw_input("Please press 'Ctrl-C' to terminate and check for errors")

    # Extracts a source+background spectrum
    subprocess.call(
        ['evselect', 'table={0}:EVENTS'.format(evtfile), 'withspectrumset=yes',
         'spectrumset={0}'.format(srcspc), 'energycolumn=PI',
         'withspecranges=yes', 'spectralbinsize=5',
         'specchannelmax={0}'.format(maxchan), 'specchannelmin=0',
         'withimageset=yes', 'imageset={0}'.format(srcimg), 'xcolumn=X',
         'ycolumn=Y', srcexp])

    # Scale the areas of src and bkg regions used
    subprocess.call(
        ['backscale', 'spectrumset={0}'.format(srcspc), 'withbadpixcorr=yes',
         'badpixlocation={0}'.format(evtfile)])

    # Extracts a background spectrum
    subprocess.call(
        ['evselect', 'table={0}:EVENTS'.format(evtfile),
         'withspectrumset=yes', 'spectrumset={0}'.format(bkgspc),
         'energycolumn=PI', 'withspecranges=yes', 'spectralbinsize=5',
         'specchannelmax={0}'.format(maxchan), 'specchannelmin=0',
         'withimageset=yes', 'imageset={0}'.format(bkgimg), 'xcolumn=X',
         'ycolumn=Y', bkgexp])

    # Scale the are of the bkg region used
    subprocess.call(
        ['backscale', 'spectrumset={0}'.format(bkgspc),
         'withbadpixcorr=yes', 'badpixlocation={0}'.format(evtfile)])

    # Generates response matrix
    subprocess.call(['rmfgen', 'rmfset={0}'.format(rmf),
                     'spectrumset={0}'.format(srcspc)])

    # Generates ana Ancillary response file
    subprocess.call(
        ['arfgen', 'arfset={0}'.format(arf), 'spectrumset={0}'.format(srcspc),
         '--withrmfset=yes', 'detmaptype=psf', 'rmfset={0}'.format(rmf),
         'badpixlocation={0}'.format(evtfile)])

    # Rebin the spectrum and link associated files (output:EPICspec.pha)
    # can be replaced by grppha tool from HEASOFT
    subprocess.call(
        ['specgroup', 'spectrumset={0}'.format(srcspc), 'mincounts=25',
         'oversample=3', 'backgndset={0}'.format(bkgspc),
         'rmfset={0}'.format(rmf), 'arfset={0}'.format(arf),
         'groupedset={0}spec.pha'.format(cam)])

    os.chdir(curdir)

    return True


def eventsextraction(table, fsrcname, fimgname, emin, emax, srcregion, camera,
                     pattern):
    """Make the event extraction for given region and energy range"""
    cam = camera.lower()

    if cam == 'pn':
        if (pattern == 99):
            pattern = 4
        exp = 'expression=#XMMEA_EP && (PI IN [{0}:{1}]) && (PATTERN<={2})\
 && FLAG==0 && ((X,Y) IN {3})'.format(emin, emax, pattern, srcregion)

    elif cam == 'mos1':
        if (pattern == 99):
            pattern = 12
        exp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && (PATTERN<={2})\
 && FLAG==0 && ((X,Y) IN {3})'.format(emin, emax, pattern, srcregion)

    elif cam == 'mos2':
        if (pattern == 99):
            pattern = 12
        exp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && (PATTERN<={2})\
 && FLAG==0 && ((X,Y) IN {3})'.format(emin, emax, pattern, srcregion)
    else:
        print "Something is wrong, the camera doesn't exist"
        raw_input("Please press 'Ctrl-C' to terminate and check errors")

    subprocess.call(
        ['evselect', 'table={0}'.format(table), 'energycolumn=PI', 'xcolumn=X',
         'ycolumn=Y', 'keepfilteroutput=yes', 'withfilteredset=yes',
         'withimageset=yes', 'filteredset={0}'.format(fsrcname),
         'imageset={0}'.format(fimgname), exp])

    return True


def showeventimg(fimgname):
    """Show extracted image and region to visual check"""

    subprocess.call(['ds9', fimgname, '-zoom', '2', '-log', '-cmap', 'heat',
                     '-region', 'load', 'src_evt.reg'])

    return True


def extractevents(camera, evtfile='original', pattern=99, outsubdir='events'):
    """Extract event files for the source region in diferents energy ranges"""

    curdir = os.getcwd()
    cam = camera.lower()

    if evtfile == 'cleaned':
        evtfile = os.path.abspath("{0}/{0}_clean.ds".format(cam))
    elif evtfile == 'original':
        evtfile = os.path.abspath(glob.glob(
            "rpcdata/*{0}*ImagingEvts.ds".format(camera.upper()))[0])
    elif not os.path.isfile(evtfile):
        print "Event file not found, using {0}_clean.ds instead".format(cam)
    else:
        print "Using event file: {0}".format(evtfile)

    if not os.path.isdir('{0}/{1}'.format(cam, outsubdir)):
        os.mkdir('{0}/{1}'.format(cam, outsubdir))

    shutil.copyfile('{0}/src_evt.reg'.format(cam),
                    '{0}/{1}/src_evt.reg'.format(cam, outsubdir))

    os.chdir('{0}/{1}'.format(cam, outsubdir))

    shutil.copy(evtfile, 'evts_barycen.ds')

    # Make barycentric correction on the clean event file
    subprocess.call(['barycen', 'table=evts_barycen.ds:EVENTS'.format(cam)])

    # Get the coordinates from the .reg file
    src = open('src_evt.reg')
    srcregion = src.readlines()[-1].strip()
    src.close()

    table = 'evts_barycen.ds'.format(camera.lower())

    ranges = ['0310', '032', '245', '4510', '210']
    emins = [300, 300, 2000, 4500, 2000]
    emaxs = [10000, 2000, 4500, 10000, 10000]

    for i in range(len(ranges)):
        fsrcname = '{0}evts_src_{1}keV.ds'.format(cam, ranges[i])
        fimgname = '{0}evts_src_img_{1}keV.ds'.format(cam, ranges[i])
        emin = emins[i]
        emax = emaxs[i]
        eventsextraction(table, fsrcname, fimgname, emin, emax, srcregion,
                         camera, pattern)

    showeventimg(fimgname)

    os.chdir(curdir)

    return True


def findtimes(rpcdata_dir, camera):
    """Find the initial and final times of observation for the given camera"""

    evtfile = os.path.abspath(glob.glob(
        rpcdata_dir+'/'+'*{0}*ImagingEvts.ds'.format(camera.upper()))[0])

    tstart = fits.getval(evtfile, 'TSTART', ext=1)
    tstop = fits.getval(evtfile, 'TSTOP', ext=1)

    return tstart, tstop


def findcommontimes(rpcdata_dir):
    """
    Find common time of observation of the 3 EPIC cameras
    for time analysis
    """

    pnfile = os.path.abspath(glob.glob(
        rpcdata_dir+'/'+'*PN*ImagingEvts.ds')[0])
    mos1file = os.path.abspath(glob.glob(
        rpcdata_dir+'/'+'*MOS1*ImagingEvts.ds')[0])
    mos2file = os.path.abspath(glob.glob(
        rpcdata_dir+'/'+'*MOS2*ImagingEvts.ds')[0])

    listtimes1 = [fits.getval(pnfile, 'TSTART', ext=1),
                  fits.getval(mos1file, 'TSTART', ext=1),
                  fits.getval(mos2file, 'TSTART', ext=1)]

    listtimes2 = [fits.getval(pnfile, 'TSTOP', ext=1),
                  fits.getval(mos1file, 'TSTOP', ext=1),
                  fits.getval(mos2file, 'TSTOP', ext=1)]

    tstart = max(listtimes1)
    tstop = min(listtimes2)

    return tstart, tstop


def lcextraction(abin, arange, emin, emax, table, srcregion, bkgregion, camera,
                 tstart, tstop):
    ''' Extract a barycentric corrected lightcurve
        in the energy range['emin':'emax'], with time bins of 'bin'
    '''

    cam = camera.lower()

    srclc = "{0}_lc_src_{1}keV_bin{2}.ds".format(cam, arange, abin)
    bkglc = "{0}_lc_bkg_{1}keV_bin{2}.ds".format(cam, arange, abin)
    netlc = "{0}_lc_net_{1}keV_bin{2}.ds".format(cam, arange, abin)
    srcimg = "{0}_src_img_{1}keV_bin{2}.ds".format(cam, arange, abin)
    bkgimg = "{0}_bkg_img_{1}keV_bin{2}.ds".format(cam, arange, abin)
    psimg = "{0}_lc_net_{1}keV_bin{2}.ps".format(cam, arange, abin)

    if cam == 'pn':
        srcexp = 'expression=#XMMEA_EP && (PI IN [{0}:{1}]) && PATTERN <=4\
 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, srcregion)
        bkgexp = 'expression=#XMMEA_EP && (PI IN [{0}:{1}]) && PATTERN <=4\
 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, bkgregion)

    elif cam == 'mos1':
        srcexp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12\
 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, srcregion)
        bkgexp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12\
 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, bkgregion)

    elif cam == 'mos2':
        srcexp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12\
 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, srcregion)
        bkgexp = 'expression=#XMMEA_EM && (PI IN [{0}:{1}]) && PATTERN <=12\
 && FLAG==0 && ((X,Y) IN {2})'.format(emin, emax, bkgregion)
    else:
        print "Something is wrong, the camera doesn't exist"
        raw_input("Please press 'Ctrl-C' to terminate and check for errors")

    # Extract a lightcurve for the src+bkg region for single and double events
    subprocess.call(
        ['evselect', 'table={0}'.format(table), 'energycolumn=PI',
         'withrateset=yes', 'rateset={0}'.format(srclc),
         'timebinsize={0}'.format(abin), 'maketimecolumn=yes',
         'makeratecolumn=yes', 'withimageset=yes',
         'imageset={0}'.format(srcimg), 'xcolumn=X', 'ycolumn=Y',
         'timemin={0}'.format(tstart), 'timemax={0}'.format(tstop), srcexp])

    # Extract a lightcurve for the bkg region for single and double events
    subprocess.call(
        ['evselect', 'table={0}'.format(table), 'energycolumn=PI',
         'withrateset=yes', 'rateset={0}'.format(bkglc),
         'timebinsize={0}'.format(abin), 'maketimecolumn=yes',
         'makeratecolumn=yes', 'withimageset=yes',
         'imageset={0}'.format(bkgimg), 'xcolumn=X', 'ycolumn=Y',
         'timemin={0}'.format(tstart), 'timemax={0}'.format(tstop), bkgexp])

    # Apply corrections and creates the net lightcurve
    subprocess.call(
        ['epiclccorr', 'eventlist={0}'.format(table),
         'outset={0}'.format(netlc), 'srctslist={0}'.format(srclc),
         'applyabsolutecorrections=yes', 'withbkgset=yes',
         'bkgtslist={0}'.format(bkglc)])

    # Save the net lightcurve visual inspection
    subprocess.call(
        ['dsplot', 'table={0}'.format(netlc), 'withx=yes', 'withy=yes',
         'x=TIME', 'y=RATE',
         'plotter=xmgrace -hardcopy -printfile {0}'.format(psimg)])

    return True


def extractlc(camera, rpcdata_dir, evtfile='cleaned', timed='no',
              outsubdir='lightcurves', bins=[]):
    """creates lightcurves from the event files"""

    curdir = os.getcwd()
    cam = camera.lower()

    if evtfile == 'cleaned':
        evtfile = os.path.abspath("{0}/{0}_clean.ds".format(cam))
    elif evtfile == 'original':
        evtfile = os.path.abspath(glob.glob(
            "rpcdata/*{0}*ImagingEvts.ds".format(camera.upper()))[0])
    elif not os.path.isfile(evtfile):
        print "Event file not found, using {0}_clean.ds instead".format(cam)
    else:
        print "Using event file: {0}".format(evtfile)

    if not os.path.isdir('{0}/{1}'.format(cam, outsubdir)):
        os.mkdir('{0}/{1}'.format(cam, outsubdir))

    shutil.copyfile('{0}/src.reg'.format(cam),
                    '{0}/{1}/src.reg'.format(cam, outsubdir))
    shutil.copyfile('{0}/bkg.reg'.format(cam),
                    '{0}/{1}/bkg.reg'.format(cam, outsubdir))

    os.chdir('{0}/{1}'.format(cam, outsubdir))

    shutil.copy(evtfile, 'evts_barycen.ds')

    src = open('src.reg', 'r')
    srcregion = src.readlines()[-1].strip()
    src.close()

    bkg = open('bkg.reg', 'r')
    bkgregion = bkg.readlines()[-1].strip()
    bkg.close()

    # Make barycentric correction on the clean event file
    subprocess.call(['barycen', 'table=evts_barycen.ds:EVENTS'])
    table = 'evts_barycen.ds'

    if (len(bins) == 0):
        bins = [10, 50, 100, 150, 200, 350, 500]

    ranges = ['0310', '032', '245', '4510', '210']
    emins = [300, 300, 2000, 4500, 2000]
    emaxs = [10000, 2000, 4500, 10000, 10000]

    if timed == 'yes':
        print "Using common times for the 3 EPIC cameras"
        tstart, tstop = findcommontimes(rpcdata_dir)
    else:
        print "Using initial and end times for the individual camera"
        tstart, tstop = findtimes(rpcdata_dir, camera)

    for abin in bins:
        for i in range(len(ranges)):
            lcextraction(abin, ranges[i], emins[i], emaxs[i], table, srcregion,
                         bkgregion, camera, tstart, tstop)

    os.chdir(curdir)

    return True
