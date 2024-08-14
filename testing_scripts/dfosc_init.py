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
        input("test \033[032;1mInitialize grism wheel (G)\033[0m - press enter: ")
        logger.info("test G (grism wheel ready)")
        try:
            ready = dfosc.gi()
            logger.info(f"DFOSC grism ready: {ready}")
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            logger.error("G init failed")
        print("\n\n\n")

        input("test \033[032;1mInitialize aperture wheel (A)\033[0m - press enter: ")
        logger.info("test A (aperture wheel ready)")
        try:
            ready = dfosc.ai()
            logger.info(f"DFOSC aperture wheel initialized: {ready}")
        except Exception as e:
            print(e)
            logger.error("A init failed")
        print("\n\n\n")

        input("test \033[032;1mInitialize filter wheel (F)\033[0m - press enter: ")
        logger.info("test F (filter wheel ready)")
        try:
            ready = dfosc.fi()
            logger.info(f"DFOSC filter wheel initialized: {ready}")
        except Exception as e:
            print(e)
            logger.error("F init failed")
        print("\n\n\n")
        time.sleep(40)
        print("Wating 40 seconds for wheels to initialize")

"""
        print("Current Grism position:", dfosc.gp() )
        print("Current Aperture position:", dfosc.ap() )
        print("Current Filter position:", dfosc.fp() )
"""
