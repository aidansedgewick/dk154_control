import time
import traceback
from argparse import ArgumentParser
from logging import getLogger


import dk154_control
from dk154_control.tcs.ascol import Ascol
from dk154_control.dfosc.dfosc import Dfosc

logger = getLogger("test_" + __file__.split("/")[-1].split("_")[0])

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    args = parser.parse_args()

    test_mode = args.test_mode
    debug = args.debug

    logger.info("start script")

    with Ascol(test_mode=test_mode, debug=debug) as ascol:
        ascol.log_all_status()

    with Dfosc(test_mode=test_mode, debug=debug) as dfosc:
        input("test \033[032;1mgrism wheel ready (G)\033[0m - press enter: ")
        logger.info("test G (grism wheel ready)")
        try:
            ready = dfosc.g()
            logger.info(f"DFOSC grism ready: {ready}")
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            logger.error("G failed")
        print("\n\n\n")

        input("test \033[032;1maperture wheel ready (A)\033[0m - press enter: ")
        logger.info("test A (aperture wheel ready)")
        try:
            ready = dfosc.a()
            logger.info(f"DFOSC aperture ready: {ready}")
        except Exception as e:
            print(e)
            logger.error("A failed")
        print("\n\n\n")

        input("test \033[032;1mfilter wheel ready (F)\033[0m - press enter: ")
        logger.info("test F (filter wheel ready)")
        try:
            ready = dfosc.f()
            logger.info(f"DFOSC filter ready: {ready}")
        except Exception as e:
            print(e)
            logger.error("F failed")
        print("\n\n\n")

        input("test \033[032;1mgrism wheel pos (GP)\033[0m - press enter: ")
        logger.info("test GP (read grism position)")
        try:
            pos = dfosc.gp()
            logger.info(f"DFOSC grism pos: {pos}")
        except Exception as e:
            print(e)
            logger.error("GP failed")
        print("\n\n\n")

        input("test \033[032;1maperture wheel pos (AP)\033[0m - press enter: ")
        logger.info("test AP (read aperture position)")
        try:
            pos = dfosc.ap()
            logger.info(f"DFOSC aperture pos: {pos}")
        except Exception as e:
            print(e)
            logger.error("AP failed")
        print("\n\n\n")

        input("test \033[032;1mfilter wheel pos (FP)\033[0m - press enter: ")
        logger.info("test FP (read filter position)")
        try:
            pos = dfosc.fp()
            logger.info(f"DFOSC filter pos: {pos}")
        except Exception as e:
            print(e)
            logger.error("FP failed")
        print("\n\n\n")
