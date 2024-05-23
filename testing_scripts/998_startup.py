from argparse import ArgumentParser

from dk154_control.tcs.ascol import Ascol


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    args = parser.parse_args()

    test_mode = args.test_mode  # False by default
    debug = args.debug  # False by default

    with Ascol(test_mode=test_mode, debug=debug) as ascol:
        teon_result = ascol.teon("1")
        tein_result = ascol.tein()
        doin_result = ascol.doin()
        doso_result = ascol.doso("1")
        fmop_result = ascol.fmop("1")
        fcop_result = ascol.fcop("1")
        doam_result = ascol.doam()
