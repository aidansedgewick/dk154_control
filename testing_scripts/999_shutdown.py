from argparse import ArgumentParser
from logging import getLogger

from dk154_control.tcs.ascol import Ascol

logger = getLogger(__file__.split("/")[-1])  # eg. 999_shutdown


def require_next(ascol: Ascol):
    """
    Require user to confirm the status of the telescope is OK before
    moving onto the next step of shutdown.
    """

    while True:
        ascol.log_all_status()
        print(
            "\033[32;1mif\033[0m status above is sensible:\n    enter 'NEXT' to move to next command.\n"
            "\033[32;1melse\033[0m:\n    wait some time, press enter to re-check tel status: "
        )
        data = input("input \033[32;1m'NEXT'\033[0m or <blank>: ")
        if data == "NEXT":
            logger.info("move to next command.")
            break


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    args = parser.parse_args()

    test_mode = args.test_mode  # False by default
    debug = args.debug  # False by default

    logger.info("start shutdown")

    with Ascol(test_mode=test_mode, debug=debug) as ascol:
        print("\n\n\n")
        # stop everything

        input("\033[32;1mSTOP telesccope (TEST)\033[0m - press enter: ")
        test_result = ascol.test()
        logger.info(f"TEST result: {test_result}")
        print("\n\n\n")

        input("\033[32;1mSTOP dome (DOST)\033[0m - press enter: ")
        dost_result = ascol.dost()
        logger.info(f"DOST result: {dost_result}")
        print("\n\n\n")

        tel_state = ascol.ters()
        dome_state = ascol.dors()
        logger.info(f"tel. state = {tel_state}")
        logger.info(f"dome state = {dome_state}")
        print("\n\n\n")

        input("\033[32;1mCLOSE mirror flap (FMOP)\033[0m- press enter: ")
        mirror_state = ascol.fmrs()
        logger.info(f"mirror flap state: {mirror_state}")
        fmop_result = ascol.fmop("0")
        logger.info(f"FMOP result: {fmop_result}")
        mirror_state = ascol.fmrs()
        logger.info(f"mirror flap state: {mirror_state}")
        require_next(ascol)
        print("\n\n\n")

        input("\033[32;1mCLOSE casssegrain flap (FCOP)\033[0m - press enter: ")
        cass_state = ascol.fcrs()
        logger.info(f"casseg. flap state: {cass_state}")
        fcop_result = ascol.fcop("0")
        logger.info(f"FCOP result: {fcop_result}")
        cass_state = ascol.fcrs()
        logger.info(f"casseg. flap state: {cass_state}")
        dome_state = ascol.dors()
        require_next(ascol)  # User must confirm status is OK before next step.
        print("\n\n\n")

        input("\033[32;1mPARK telescope (TEPA)\033[0m - press enter: ")
        tepa_result = ascol.tepa()
        logger.info(f"TEPA result: {tepa_result}")
        require_next(ascol)
        print("\n\n\n")

        input("\033[32;1mPARK dome (DOPA)\033[0m - press enter: ")
        dopa_result = ascol.dopa()
        logger.info(f"DOPA result: {dopa_result}")
        require_next(ascol)
        print("\n\n\n")

        input("\033[32;1mCLOSE dome slit (DOSO)\033[0m - press enter: ")
        require_next(ascol)
        doso_result = ascol.doso("0")
        logger.info(f"DOSO result: {dopa_result}")
        require_next(ascol)
        print("\n\n\n")

        input("\033[32;1mOFF telescope\033[0m - press enter: ")
        ascol.teon("0")
        ascol.log_all_status()

    logger.info("exit shutdown script")
