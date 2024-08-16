import time
import traceback
from argparse import ArgumentParser
from logging import getLogger

import dk154_control
from dk154_control.tcs.ascol import Ascol
from dk154_control.dfosc.dfosc import Dfosc
from dk154_control.camera.ccd3 import Ccd3
import yaml

dfosc_setup = yaml.load(open('dk154_control/dfosc/dfosc_setup.yaml'), Loader=yaml.FullLoader)

logger = getLogger("test_" + __file__.split("/")[-1].split("_")[0])

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    parser.add_argument("-s", "--slit", type=str, default='empty', choices=dfosc_setup['slit'].keys())
    parser.add_argument("-m", "--mag", type=float)
    args = parser.parse_args()

    test_mode = args.test_mode
    debug = args.debug

    logger.info("start script")
    mag = args.mag

    with Ascol(test_mode=test_mode, debug=debug) as ascol:
        ascol.log_all_status()

    with Dfosc(test_mode=test_mode, debug=debug) as dfosc:
        input("test \033[032;1mAcquisition Image Script\033[0m - press enter: ")
        logger.info("take acquisition image")

        try:
            grism = dfosc.gp()
            slit = dfosc.aperture_goto(dfosc_setup['slit'][args.slit])
            exp_params = {}

            dfosc.grism_goto(0)
            dfosc.filter_goto(0)

            if slit != 0:
                logger.info(f"Grism and slit in positions - G: {grism} , S: {slit}")
                decision = input("test \033[032;1mMove Grism and Slit to empty Position?\033[0m - [y/n]: ")
                if decision=="y":
                    logger.info("move slit wheel to empty positions")
                    dfosc.ag(0)
                    time.sleep(15)
                    imgtpe = 'OBJECT'

                else:
                    input("test \033[032;1mSlit in position\033[0m - press enter: ")
                    logger.info(f"Slit wheel in position: {slit}")
                    imgtpe = 'OBJECT,SLIT'

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

            exp_params['CCD3.exposure'] = exp_time #TODO: adjust exposure time based on target magnitude
            exp_params['CCD3.IMAGETYP'] = imgtpe
            exp_params['CCD3.OBJECT'] = 'DFOSC target acquisition'
            ccd = Ccd3()
            ccd.set_exposure_parameters(params=exp_params)
            filename = f'test_acquisition_{0:03d}.fits'
            logger.info(f"acquisition image without slit")
            logger.info(f"filename: {filename}") 
            ccd.start_exposure(filename=filename)

        except Exception as e:
            logger.info(e)
            logger.info(traceback.format_exc())
            logger.info("acquisition failed")
        print("\n\n\n")
        time.sleep(exp_params['CCD3.exposure']+30)
