import dk154_control.dfosc.dfosc as df
from argparse import ArgumentParser
from logging import getLogger
import time
from dk154_control.camera.ccd3 import Ccd3
from dk154_control.tcs.ascol import Ascol
from dk154_control.lamps.wave_lamps import WaveLamps
import yaml

dfosc_setup = yaml.load(open('dk154_control/dfosc/dfosc_setup.yaml'), Loader=yaml.FullLoader)

logger = getLogger("test_" + __file__.split("/")[-1].split("_")[0])

def take_arc_calib(grism,slit,filt):
    with WaveLamps() as lamps:
        lamps.turn_on_lamps()
        time.sleep(30) # wait for lamps to warm up  

    for g in grism:
        for s in slit:
            for f in filt:
                with df.Dfosc() as dfosc:
                    dfosc.grism_goto(dfosc_setup['grism'][g])
                    dfosc.aperture_goto(dfosc_setup['slit'][s])
                    dfosc.filter_goto(dfosc_setup['filter'][f])
                    # TODO: see if the exposure times are valid for 1.0" slit
                    if g == '3' or g=='7' or g== '14' or g== '15':
                        exp_time = 10
                    elif g == '5':
                        exp_time = 40
                    elif g == '6':
                        exp_time = 20
                    elif g == '8':
                        exp_time = 150

                    exp_params = {}
                    exp_params['CCD3.exposure'] = str(exp_time)
                    exp_params['CCD3.IMAGETYP'] = 'WAVE,LAMP'
                    exp_params['CCD3.OBJECT'] = 'Hg calib'
                    ccd=Ccd3()
                    ccd.set_exposure_parameters(params=exp_params)
                    with Ascol() as ascol:
                        ascol.shop('0')
                        ccd.start_exposure(f'test_arc_g{g}_s{s}_f{f}.fits')
                    time.sleep(exp_time + 30) #readout time
        
        lamps.turn_off_lamps()

def wheel_return():
    with df.Dfosc() as dfosc:
        dfosc.aperture_goto(dfosc_setup['slit']['empty'])   
        dfosc.grism_goto(dfosc_setup['grism']['empty'])
        dfosc.filter_goto(dfosc_setup['filter']['empty']) 

if __name__ == '__main__':
    # define the parser
    parser = ArgumentParser(description='Take arc calibration images with DFOSC')
    parser.add_argument('-g','--grism',nargs= '+',type=str,choices=dfosc_setup['grism'].keys())
    parser.add_argument('-s','--slit', nargs='+' ,type=str,choices=dfosc_setup['slit'].keys())
    parser.add_argument('-f','--filt', nargs = '+',type=str,choices=dfosc_setup['filter'].keys())
    args = parser.parse_args()
    take_arc_calib(args.grism, args.slit, args.filt)
    wheel_return()

