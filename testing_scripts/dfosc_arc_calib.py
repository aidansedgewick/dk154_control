# script for taking n number of arc calibrations for various slit, grism, and filter combinations with DFOSC
# useage: dfosc_arc_calib.py --grism [grism] --slit [slit] --filter [filter]
# grism slit and filter are given either as either one number or multiple numbers separated by commas
# example: dfosc_arc_calib.py --grism 1 2 3 4 5 6 7 8 --slit 1 2 3 4 5 6 7 8 --filter 1 2 3 4 5 6 7 8
# position 1 is empty for all wheels
# here the inputs are given as the positions of the wheels (see dfosc_setup.json for correct arrangement)

# only grism 15 should be used with a filter, for all other grisms, filter should be 0
# ex. dfosc_arc_calib.py 15 1,2,3,4 4,5,6  (here filters 4,5,6 have different cross dispersers in place)

# WARNING: Check that lamps have been turned on/off. This can also be bone through the lin 55 machine using:
# python3 dk154_control/cyberpower_pdu_snmp/__init__.py 192.168.132.59 5 on
# python3 dk154_control/cyberpower_pdu_snmp/__init__.py 192.168.132.59 6 on

# then remember to turn off the lamps after images are taken
# python3 dk154_control/cyberpower_pdu_snmp/__init__.py 192.168.132.59 5 off
# python3 dk154_control/cyberpower_pdu_snmp/__init__.py 192.168.132.59 6 off

import telnetlib
import time
import dk154_control.lamp as lamp
from argparse import ArgumentParser
from logging import getLogger
from dk154_control.camera.ccd3 import Ccd3
from dk154_control.tcs.ascol import Ascol

host = "192.168.132.58" 
port = 4001

def take_arc_calib(grism,slit,filt):
    # take user inputs and loop them through all configurations
    #grism = grism.split(',')
    #slit = slit.split(',')
    #filt_wheel = filt.split(',')
    print(grism, slit, filt)

    #turn on the lamps
    lamphost = '192.168.132.59'
    outlet = 5
    outlet2 = 6
    lamp.CyberPowerPdu(lamphost).set_outlet_on(outlet, 'on')
    lamp.CyberPowerPdu(lamphost).set_outlet_on(outlet2, 'on')
    time.sleep(30) # wait for lamps to warm up

    with telnetlib.Telnet(host, port) as tn:

        for g in grism:
            for s in slit:
                for f in filt:

                    tn.write(f'G{g}\n'.encode())
                    print(tn.read_until(b'\n').decode('utf-8'))
                    tn.write(f'A{s}\n'.encode())
                    print(tn.read_until(b'\n').decode('utf-8'))
                    tn.write(f'F{f}\n'.encode())
                    print(tn.read_until(b'\n').decode('utf-8'))
                    time.sleep(15)
                    

                    tn.write(b'g\n')
                    gris = tn.read_until(b'\n').decode('utf-8')
                    tn.write(b'GP\n')
                    print('Current Grism step position: ' + tn.read_until(b'\n').decode('utf-8'))
                    tn.write(b'a\n')
                    aper = tn.read_until(b'\n').decode('utf-8')
                    tn.write(b'AP\n')
                    print('Current Aperture step position: ' + tn.read_until(b'\n').decode('utf-8'))
                    tn.write(b'f\n')
                    filte = tn.read_until(b'\n').decode('utf-8')
                    tn.write(b'FP\n')
                    print('Current Filter step position: ' + tn.read_until(b'\n').decode('utf-8'))

                    # wait for wheels to return 'y'
                    #if gris == aper == filte == 'y':
                    #    print('All wheels are in position')
                    #    tn.write(b'AM+450\n')
                    #    time.sleep(5)
                    #else:
                    #    print('Wheels are not in position, waiting 10 seconds')
                    #    time.sleep(10)

                    
                with Ascol() as ascol:
                    ccd = Ccd3()
                    if g == '2' or g=='5' or g== '7' or g== '8':
                        exp_time = 10
                    elif g == '3':
                        exp_time = 40
                    elif g == '4':
                        exp_time = 20
                    elif g == '6':
                        exp_time = 150
                    
                    
                    ascol.shop('0')
                    # set the exposure parameters
                    exp_params = {}
                    exp_params['CCD3.exposure'] = str(exp_time)
                    exp_params['CCD3.IMAGETYP'] = 'WAVE,LAMP'
                    exp_params['CCD3.OBJECT'] = 'Hg calib'
                    exp_params['WASA.filter'] = "0"
                    exp_params['WASB.filter'] = "0"
                    #binning option
                    #dither between frames

                    ccd.set_exposure_parameters(params=exp_params)

                    ccd.start_exposure(f'test_arc_{g}_{s}_{f}.fits')
                    time.sleep(exp_time + 30) #readout time

    # turn off the lamps
    lamp.CyberPowerPdu(lamphost).set_outlet_on(outlet, 'off')
    lamp.CyberPowerPdu(lamphost).set_outlet_on(outlet2, 'off')


def wheel_return():
    # returns wheel to empty position
    with telnetlib.Telnet(host, port) as tn:
        tn.write(b'A1\n')
        tn.write(b'G1\n')
        tn.write(b'F1\n')
        time.sleep(15)


if __name__ == '__main__':
    # define the parser
    parser = ArgumentParser(description='Take arc calibration images with DFOSC')
    parser.add_argument('--grism',nargs= '+',help='Grism position(s) to use, 1-8, or multiple grism positions')
    parser.add_argument('--slit', nargs='+' ,help='Slit position(s) to use, 1-8, or multiple slit positions')
    parser.add_argument('--filt', nargs = '+',help='Filter position(s) to use, 1-8, or multiple filter positions')
    args = parser.parse_args()
    take_arc_calib(args.grism, args.slit, args.filt)
    wheel_return()
