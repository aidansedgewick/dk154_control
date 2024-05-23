import time
import traceback
from argparse import ArgumentParser
from logging import getLogger


import dk154_control
from dk154_control.tcs.ascol import Ascol

logger = getLogger("test_" + __file__.split("/")[-1].split("_")[0])

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    args = parser.parse_args()

    test_mode = args.test_mode
    debug = args.debug

    with Ascol(test_mode=test_mode, debug=debug) as ascol:

        input("test \033[032;1mremote state (GLRE)\033[0m - press enter: ")
        logger.info("test GLRE")
        try:
            remote_state = ascol.glre()
            logger.info(f"remote state: {remote_state}")
        except Exception as e:
            print(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.error("GLRE failed")
        print("\n\n\n")

        input("test \033[032;1msafety relay (GLSR)\033[0m - press enter: ")
        logger.info("test GLSR")
        try:
            safety_relay_state = ascol.glsr()
            logger.info(f"safety relay: {safety_relay_state}")
        except Exception as e:
            print(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.error("GLSR failed")
        print("\n\n\n")

        input("test \033[032;1mtelescope state (TERS)\033[0m - press enter: ")
        logger.info("test TERS")
        try:
            telescope_state = ascol.ters()
            logger.info(f"telescope state: {telescope_state}")
        except Exception as e:
            print(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.error("TERS failed")
        print("\n\n\n")

        input("test \033[032;1mdome state (DORS)\033[0m - press enter: ")
        logger.info("test DORS")
        try:
            dome_state = ascol.dors()
            logger.info(f"dome state: {dome_state}")
        except Exception as e:
            print(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.error("DORS failed")
        print("\n\n\n")

        input("test \033[032;1mcasseg. flap state (FCRS)\033[0m - press enter: ")
        logger.info("test FCRS")
        try:
            fcrs_state = ascol.fcrs()
            logger.info(f"Cass. flap state: {fcrs_state}")
        except Exception as e:
            print(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.error("FCRS failed")
        print("\n\n\n")

        input("test \033[032;1mmirror flap state (FMRS)\033[0m - press enter: ")
        logger.info("test FMRS")
        try:
            fmrs_state = ascol.fmrs()
            logger.info(f"Mirror flap state: {fmrs_state}")
        except Exception as e:
            print(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.error("FMRS failed")
        print("\n\n\n")

        input("test \033[032;1mread tel RA/Dec/Pos (TRRD)\033[0m - press enter: ")
        logger.info("test TRRD")
        try:
            ra, dec, pos = ascol.trrd()
            logger.info(f"ra, dec, pos: {ra}, {dec}, {pos}")
        except Exception as e:
            print(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.error("FMRS failed")
        print("\n\n\n")

        input("test convenience \033[032;1mlog all status\033[0m - press enter: ")
        logger.info("test 'log_all_status'")
        try:
            ascol.log_all_status()
        except Exception as e:
            print(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.info("log_all_status() failed.")
