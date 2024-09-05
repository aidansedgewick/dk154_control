import sys
from argparse import ArgumentParser
from logging import getLogger

import dk154_control
from dk154_control.tcs.ascol import Ascol
from dk154_control.camera.ccd3 import Ccd3
from dk154_control.dfosc.dfosc import Dfosc
from dk154_control.lamps.wave_lamps import WaveLamps

logger = getLogger("test_" + __file__.split("/")[-1].split("_")[0])

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    parser.add_argument("-i", "--import-only", action="store_true", default=False)
    args = parser.parse_args()

    test_mode = args.test_mode
    debug = args.debug

    logger.info("start/import ok")
    if args.import_only:
        logger.info("exit now: test import only")
        sys.exit()

    with Ascol(test_mode=test_mode, debug=debug) as ascol:
        logger.info("Ascol() init in `with` block ok")

    ccd3 = Ccd3()
    logger.info("Ccd3() init ok")

    # write 'dfosc_filter=' as 'filter' is a python builtin.
    with Dfosc(test_mode=test_mode, debug=debug) as dfosc:
        logger.info("Dfosc() init ok")

    with WaveLamps() as wvlamps:
        logger.info("WaveLamps() init ok")
