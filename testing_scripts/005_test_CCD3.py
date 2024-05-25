import time
from argparse import ArgumentParser
from logging import getLogger

from dk154_control.camera.ccd3 import Ccd3
from dk154_control.tcs.ascol import Ascol


logger = getLogger("test_" + __file__.split("/")[-1].split("_")[0])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    args = parser.parse_args()

    test_mode = args.test_mode  # False by default
    debug = args.debug  # False by default

    logger.info("start script")

    with Ascol(test_mode=test_mode, debug=debug) as ascol:
        ccd3 = Ccd3(test_mode=test_mode, debug=debug)  # Ccd3 doesn't need 'with'.

        input(f"test \033[32;1mread CCD state\033[0m - press enter: ")
        ccd_state = ccd3.get_ccd_state()
        logger.info(f"CCD state before exposure: {ccd_state}")
        print("\n\n\n")

        # # DOES THE SHUTTER NEED OPENING?!
        # input("test \033[32;1mopen shutter\033[0m - press enter:")
        # shop_result = ascol.shop("1")
        # logger.info(f"SHOP result: {shop_result}")
        # shutter_state = ascol.shrp()
        # logger.info(f"shutter pos: {shutter_state}")
        # print("\n\n\n")

        input(f"test \033[32;1mset_exposeure_parameters\033[0m - press enter: ")
        exp_time = 1.0  # sec

        # Hopefully there will be a nicer way to set parameters in the future...
        exp_parameters = {}
        exp_parameters["CCD3.exposure"] = exp_time  # exp_time [sec]
        exp_parameters["CCD3.IMAGETYP"] = "LIGHT"
        exp_parameters["CCD3.OBJECT"] = "test_obs"  # What are you observing?
        exp_parameters["WASA.filter"] = "0"
        exp_parameters["WASB.filter"] = "2"  # Filter position is 'B' ?

        ccd3.set_exposure_parameters(params=exp_parameters)

        ccd_state = ccd3.get_ccd_state()
        logger.info(f"ccd state after set parameters: {ccd_state}")
        print("\n\n\n")

        N_exp = 5

        for ii in range(N_exp):
            if ii > 0:
                msg = f"again \033[32;1mset exposure params\033[0m - press enter: "
                input(msg)
                ccd3.set_exposure_parameters(exp_parameters)

            input(
                f"test \033[32;1mstart exposure exp no. {ii}/{N_exp}\033[0m - press enter: "
            )
            filename = f"test_exp_{ii:03d}.fits"  # eg. test_exp_000, test_exp_001, etc.
            logger.info(f"file name {filename}")
            ccd3.start_exposure(filename)

            logger.info(f"wait {exp_time} + 5 sec for exposure/read to finish")
            time.sleep(exp_time + 5.0)  # wait!
            # Now check the directory where you expect the file to have been saved.
            logger.info(f"Now check lin1::/data/<date>/{filename} ?")

            ccd_state = ccd3.get_ccd_state()
            logger.info(f"CCD state after exposure: {ccd_state}")
            print("\n\n\n")

        # # DOES THE SHUTTER NEED CLOSING?
        input("test \033[32;1mclose shutter\033[0m - press enter: ")
        shop_result = ascol.shop("0")
        logger.info(f"SHOP result: {shop_result}")
        shutter_state = ascol.shrp()
        logger.info(f"shutter pos: {shutter_state}")
