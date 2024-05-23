import time
import traceback
from logging import getLogger
from argparse import ArgumentParser

from dk154_control.tcs.ascol import Ascol

logger = getLogger("test_" + __file__.split("/")[-1].split("_")[0])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    args = parser.parse_args()

    test_mode = args.test_mode  # False by default
    debug = args.debug  # False by default

    with Ascol(test_mode=test_mode, debug=debug) as ascol:
        print("\n\n\n")

        # ========== test Wheel A Read State ========= #
        input("test \033[32;1mWheel A Read State (WARS)\033[0m - press enter: ")
        logger.info("test WARS")
        try:
            wheel_a_status = ascol.wars()
            logger.info(f"wheel a status: {wheel_a_status}")
        except Exception as e:
            logger.info(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.info("WARS failed")
        print("\n\n\n")

        # ========== test Wheel A Read Position ========= #
        input("test \033[32;1mWheel A Read Position (WARP)\033[0m - press enter: ")
        logger.info("test WARP")
        try:
            wheel_a_pos = ascol.warp()
            logger.info(f"wheel a pos: {wheel_a_pos}")
        except Exception as e:
            logger.info(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.info("WARP failed")
        print("\n\n\n")

        input(
            "test \033[32;1mWheel A Set Postion (WASP)\033[0m to '2'  - press enter: "
        )
        logger.info("test WASP")
        try:
            wheel_a_set_result = ascol.wasp("2")  # ""
            logger.info(f"WASP result: {wheel_a_set_result}")
        except Exception as e:
            logger.info(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.info("WASP failed")
        print("\n\n\n")

        input(
            "test \033[32;1mWheel A GO (WAGP)\033[0m and wait for move - press enter: "
        )
        WAGP_success = False
        try:
            WAGP_result = ascol.wagp()  # 1 (ok) or ERR.
            logger.info(f"WAGP result: {WAGP_result}")
            if WAGP_result != "ERR":
                WAGP_success = True
        except Exception as e:
            logger.info(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.info("WAGP failed")

        # ===== Wait for the wheel to move...

        if WAGP_success:
            logger.info("wheel a should be moving!")
            for ii in range(30):
                time.sleep(2.0)
                wheel_a_status = ascol.wars()
                wheel_a_pos = ascol.warp()
                logger.info(f"WHEEL A: pos={wheel_a_pos}, status={wheel_a_status}")
                if wheel_a_status == "stopped":
                    logger.info("WHEEL A move success!")
                    break
        else:
            logger.info("skip waiting for wheel to move... GO failed.")
        print("\n\n\n")

        input("move \033[32;1mwheel A back to empty\033[0m pos '0'- press enter: ")
        logger.info("move wheel A back to empty")
        WAGP_success = False
        try:
            WASP_result = ascol.wasp("0")
            WAGP_result = ascol.wagp()
            if WAGP_result != "ERR":
                WAGP_success = True
        except Exception as e:
            logger.info(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.info("WAGP failed")

        if WAGP_success:
            logger.info("wheel a should be moving!!!")
            for ii in range(30):
                wheel_a_status = ascol.wars()
                wheel_a_pos = ascol.warp()
                logger.info(f"WHEEL A: pos={wheel_a_pos}, status={wheel_a_status}")
                if wheel_a_status == "stopped":
                    logger.info("WHEEL A move success!")
                    break
                time.sleep(2.0)
        else:
            logger.info("skip waiting for wheel to move... GO failed.")
        print("\n\n\n")

        # with Ascol(test_mode=True, debug=True) as ascol:
        input("test \033[32;1mWheel B Read State (WBRS)\033[0m - press enter: ")
        logger.info("test WBRS")
        try:
            wheel_b_status = ascol.wbrs()
            logger.info(f"wheel b status: {wheel_b_status}")
        except Exception as e:
            logger.info(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.info("WBRS failed")
        print("\n\n\n")

        input("test \033[32;1mWheel B Read Position (WBRP)\033[0m - press enter: ")
        logger.info("test WBRP")
        try:
            wheel_b_pos = ascol.wbrp()
            logger.info(f"wheel b pos: {wheel_b_pos}")
        except Exception as e:
            logger.info(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.info("WBRP failed")
        print("\n\n\n")

        input(
            "test \033[32;1mWheel B Set Postion (WBSP)\033[0m to '2'  - press enter: "
        )
        logger.info("test WBSP: set wheel 'b' to position 2")
        try:
            wheel_b_set_result = ascol.wbsp("2")  # ""
            logger.info(f"WBSP result: {wheel_b_set_result}")
        except Exception as e:
            logger.info(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.info("WBSP failed")
        print("\n\n\n")

        input(
            "test \033[32;1mWheel B GO (WAGP)\033[0m and wait for move - press enter: "
        )
        logger.info("test WHEEL B GO")
        WBGP_success = False
        try:
            WBGP_result = ascol.wbgp()  # 1 (ok) or ERR.
            logger.info(f"WBGP result: {WBGP_result}")
            if WBGP_result != "ERR":
                WBGP_success = True
        except Exception as e:
            logger.info(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.info("WBGP failed")

        if WBGP_success:
            logger.info("wheel B should be moving!!!")
            for ii in range(30):
                time.sleep(2.0)
                wheel_b_status = ascol.wbrs()
                wheel_b_pos = ascol.wbrp()
                logger.info(f"WHEEL B: pos={wheel_b_pos}, status={wheel_b_status}")
                if wheel_b_status == "stopped":
                    logger.info("WHEEL B move success!")
                    break
        else:
            logger.info("skip waiting for wheel to move... GO failed.")
        print("\n\n\n")

        input("move \033[32;1mwheel B back to empty\033[0m pos '0'- press enter: ")
        logger.info("move wheel B back to empty")
        WBGP_success = False
        try:
            WBSP_result = ascol.wbsp("0")
            WBGP_result = ascol.wbgp()
            if WBGP_result != "ERR":
                WBGP_success = True
        except Exception as e:
            logger.info(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.info("WBGP failed")

        if WBGP_success:
            logger.info("WHEEL B should be moving!!!")
            for ii in range(30):
                wheel_b_status = ascol.wbrs()
                wheel_b_pos = ascol.wbrp()
                logger.info(f"WHEEL B: pos={wheel_b_pos}, status={wheel_b_status}")
                if wheel_b_status == "stopped":
                    logger.info("WHEEL B move success!")
                    break
                time.sleep(2.0)
        else:
            logger.info("skip waiting for wheel to move... GO failed.")
        print("\n\n\n")
