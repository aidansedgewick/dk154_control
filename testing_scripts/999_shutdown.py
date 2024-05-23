from argparse import ArgumentParser
from logging import getLogger

from dk154_control.tcs.ascol import Ascol

logger = getLogger()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    args = parser.parse_args()

    test_mode = args.test_mode  # False by default
    debug = args.debug  # False by default

    with Ascol(test_mode=test_mode, debug=debug) as ascol:
        # stop everything
        test_result = ascol.test()
        dost_result = ascol.dost()

        tel_state = ascol.ters()
        logger.info(f"tel. state = {tel_state}")

        dome_state = ascol.dors()
        logger.info(f"dome state = {dome_state}")

        cass_state = ascol.fcrs()
        logger.info(f"casseg. mirror state")
