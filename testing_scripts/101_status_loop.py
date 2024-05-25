import time
from argparse import ArgumentParser

from dk154_control.tcs.ascol import Ascol


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    parser.add_argument("-s", "--sleep-time", default=2.0, type=float)
    args = parser.parse_args()

    test_mode = args.test_mode  # False by default
    debug = args.debug  # False by default

    with Ascol(test_mode=test_mode, debug=debug) as ascol:
        while True:
            ascol.log_all_status()
            time.sleep(2.0)
