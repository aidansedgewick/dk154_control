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
        input(f"Telescope ON - press enter: ")
        teon_result = ascol.teon("1")
        input(f"Telescope INIT - press enter: ")
        tein_result = ascol.tein()
        input(f"Dome INIT - press enter: ")
        doin_result = ascol.doin()
        input(f"Dome SLIT OPEN - press enter: ")
        doso_result = ascol.doso("1")
        input(f"Cassegran flap OPEN - press enter: ")
        fcop_result = ascol.fcop("1")
        input(f"Mirror flap OPEN - press enter: ")
        fmop_result = ascol.fmop("1")
        input(f"Dome AUTOMATED - press enter: ")
        doam_result = ascol.doam()
