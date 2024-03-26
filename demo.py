###############################
#simulating Danish observations
###############################
#!/usr/bin/env python

from astropy.io import fits

import datetime
import time

import sys
import os
import subprocess
import pandas as pd
import json

from termcolor import colored, cprint

from dk154_control.dfosc import dfosc
from dk154_control.tcs.ascol import Ascol

###############################
#First step - connect to ESO VPN
#need multiple factor authentication - obtained from ESO
#this operation must be done before using this code

###############################
#initialize DFOSC wheels (only at startup/power cycle) 

cprint('\n**** Initializing DFOSC wheels, and Reading Telescope State ****', 'red', attrs=['blink'])
time.sleep(2)

tcs = Ascol()

slit = dfosc.Slit()
grism = dfosc.Grism()
filter = dfosc.Filter()

slit.a_init()
grism.g_init()
filter.f_init()

tcs.ters()


###############################
#now, let's start to work with the data list and the telescope
# Read list file into dictionary

cprint('\n**** Reading target list ****', 'red', attrs=['blink'])
time.sleep(5)

#os.chdir('Access/Access/')
#filename = sys.argv[1]
filename = 'lasilla_ranked_list.csv'
data_dict = pd.read_csv(filename)

# Define variables
target_name = data_dict['objectId']
RA = data_dict['ra']
DEC = data_dict['dec']
mag = data_dict['mag']

# Read dfosc setup
dfosc_wheels = json.load(open('dfosc/dfosc_setup.json'))
grism = dfosc_wheels['grism']
slit = dfosc_wheels['slit']
filt = dfosc_wheels['filter']


"""
#TODO use magnitudes (that should be included in ranked_list) to calculate exposure time using NTE exp time calculator.

for i in range(len(target_name)):
    EXP_TIME = nte_exp_time_calc(mag[i], slit, grism)
    EXP_TIME.append(data_dict['expt'])   #does this create a new column?

expotime = data_dict['expt']


###############################
#now, let's start to work with the data list and the telescope
# Read list file into dictionary

cprint('\n**** Reading telescope setup ****', 'red', attrs=['blink'])
time.sleep(5)

filename = 'lasilla_setup.csv'
tel_dict = pd.read_csv(filename)

mode = tel_dict['mode']
aperture = tel_dict['aperture']
ADC = tel_dict['ADC']
#slit = tel_dict['slit']
slit_pa = tel_dict['PA']
#grism = tel_dict['grism']
#filt = tel_dict['filter']
acquitime = tel_dict['acquisition']
numexpose = tel_dict['numexpose']
#maxseeing  = obdict['maxseeing']
#moondit = obdict['moondit']
#visibility = obdict['visibility']

###############################
#pointing first target

#create a list of target
target_observed = []

cprint('\n**** Pointing telescope ****', 'red', attrs=['blink'])
time.sleep(1)

for i in range(len(target_name)):
    if target_name[i] not in target_observed:
        target_obs = target_name[i]
        cprint('\n**** Observing target no. {:d} ****'.format(i+1), 'red', attrs=['blink'])
        time.sleep(1)

        # Point to a target
        cprint('\n**** Pointing target no. {:d} ****'.format(i+1), 'red', attrs=['blink'])
        time.sleep(5)

        tcs.tsra(ra=str(RA[i]), dec=str(DEC[i]), position=str()) #position 0 for East, 1 for West
          
        # tcs.focus(RA, DEC)
        # Start preparation movements of the instrument
        
        grism.goto(grism['G3']) # define the grism
        slit.goto(slit['1.0']) # define the slit position
        filter.goto(filt['Empty']) # define the filter

        # Image Acquisition and display
        # Point to a target
        cprint('\n**** Acquisition target no. {:d} ****'.format(i+1), 'red', attrs=['blink'])
        time.sleep(5)

        # Take first positioning image?

        os.system('dfosc.target target_name ;'
                  'dfosc.mode mode ;'
                  'dfosc.aperture aperture ;'
                  'dfosc.filter filter ')
        
        tip ='yes'
        while tip == 'yes':
            os.system('dfosc.slit 0 ;'
                      'dfosc.slit_pa 0 ;'
                      'dfosc.grism 0 ;'
                      'dfosc.wait_dfosc_ready ;'
                      'dfosc.acquisition acquitime ;'
                      'dfosc.display ;'
                      # Slit acquisition，display and offsets
                      # Check commands, and write some new commands as needed in dfosc.py
                      # See dfosc.slitoff, dfosc.slitrot on https://www.not.iac.es/observing/seq/new/docserver.php?i=ALFOSC&t=ANY&u=GENERAL&m=ANY&d=SHORT
                      'dfosc.slit slit ;'
                      'dfosc.slit_pa slitpangel ;'

                      'dfosc.grism 0 ;'
                      'dfosc.wait_dfosc_ready;'
                      'dfosc.acquisition acquitime ;'
                      'dfosc.display')
            tip = input('Do you want to make offset? please input yes or no : ')
            if tip == 'yes':
                ra = input('Please input the offset for RA (arcsec): ')
                dec = input('Please input the offset for DEC (arcsec): ')
                os.system(f'tcs.ra_delta (ra) ;'
                          f'tcs.dec_delta (dec) ')
                tip = 'yes'
            elif tip == 'no':
                break
            else:
                tip = 'yes'
        # Slit position angle offset
        patip='yes'
        while patip == 'yes':
            patip = input('Do you want to make offset for slit position angle? please input yes or no : ')
            if patip == 'yes':
                padel = input('Please input the offset of slit position angle (arcsec): ')
                os.system('dfosc.slit_pa_delta padel;'
                          'dfosc.wait_dfosc_ready;'
                          'dfosc.acquisition acquitime;'
                          'dfosc.display')
                patip = 'yes'
            elif patip == 'no':
                break
            else:
                tip = 'yes'
        # Exposure
        cprint('\n**** Observing target no. {:d} ****'.format(i+1), 'red', attrs=['blink'])
        os.system('dfosc.grism grism;'
                  'dfosc.wait_dfosc_ready')
        count = 0
        date = datetime.date.today()
        for index in range(numexpose[0]):
            os.system('dfosc.exposure expotime')
            # Save exposure data and add header information into fits format
            imgdata = subprocess.getoutput('dfosc.readout()').strip("'")
            hdr = fits.Header()
            #hdr.append(('filter', filter), end=True)
            hdr.append(('slit', slit[0]), end=True)
            hdr.append(('grism',grism[0]), end=True)
            hdu = fits.PrimaryHDU(imgdata,hdr)
            # Creat the path and name for fits file and save
            count = count +1
            now = time.strftime("%H-%M-%S")
            impath= 'target_name' +'_' + str(date) +'_' + str(now) +'_' + '%04d' %count + '.fits'
            # End of observing block and write to OBlog
            cprint('\n**** Update log of the night ****'.format(i), 'red', attrs=['blink'])
            with open('OBlog_'+ str(date)+'.txt','a',encoding='utf-8') as f:
                text = str(filter)+','+str(grism)+','+str(expotime)+'\n'
                f.write(text)
        target_observed.append(target_name[i])
    else:
        continue

"""