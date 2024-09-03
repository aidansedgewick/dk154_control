# Basic script for taking an image with dfosc for a given slit, grism and filter wheels are in empty position
# Usage: python3 dfosc_target_acq.py --slit 1 2 3 4 5 6 7 8 --mag 10
# Start with position 8 as it is a 5.0" slit
# Postion 7 is a pinhole, and not usefuly for this test
# use --slit 8 6 5 4 3 2 for testing.
# adjust the exposure time based on the magnitude of the target

import telnetlib
import time
from argparse import ArgumentParser
from logging import getLogger
from dk154_control.camera.ccd3 import Ccd3
from dk154_control.tcs.ascol import Ascol

host = "192.168.132.58" 
port = 4001

def take_acquisition(slit,mag):
    # take user inputs and loop them through all configurations
    #slit = slit.split(',')
    with telnetlib.Telnet(host, port) as tn:

        for s in slit:

        # connect to dfosc and move to the correct positions

            tn.write(f'A{s}\n'.encode())
            print(tn.read_until(b'\n').decode('utf-8'))
            time.sleep(15)


            tn.write(b'a\n')
            aper = tn.read_until(b'\n').decode('utf-8')
            tn.write(b'AP\n')
            print('Current Aperture step position: ' + tn.read_until(b'\n').decode('utf-8'))

            # wait for wheels to return 'y'
            if aper == 'y':
                print('All wheels are in position')
            else: 
                print('Wheels are not in position, waiting 10 seconds')
                time.sleep(10)

        # take the image
        with Ascol() as ascol:
            ccd3 = Ccd3()
            
            if mag < 10:
                exp_time = 10
            elif 10 <= mag < 12:
                exp_time = 20
            elif 12 <= mag < 13:
                exp_time = 30
            elif 13 <= mag < 14:
                exp_time = 50
            else:
                exp_time = 90

            # set the exposure parameters
            exp_params = {}
            exp_params['CCD3.exposure'] = str(exp_time)
            exp_params['CCD3.IMAGETYP'] = 'Target Acquisition'
            exp_params['CCD3.OBJECT'] = 'OBJECT'
            exp_params['WASA.filter'] = "0"
            exp_params['WASB.filter'] = "0"
            
            ccd3.set_exposure_parameters(params=exp_params)

            ascol.shop('0')
            ccd3.start_exposure(f'test_acq_{s}.fits')
            time.sleep(exp_time + 30) #readout time

def wheel_return():
    # returns wheel to empty position
    with telnetlib.Telnet(host, port) as tn:
        tn.write(b'A1\n')
        tn.write(b'G1\n')
        tn.write(b'F1\n')
            

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--slit", nargs="+",type=str, help="Slit position, 1-8")
    parser.add_argument("--mag", type=str, help="Magnitude of the target")
    args = parser.parse_args()

    take_acquisition(args.slit,args.mag)
    wheel_return()