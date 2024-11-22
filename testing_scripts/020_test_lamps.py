from argparse import ArgumentParser
from logging import getLogger

import dk154_control
from dk154_control.lamps.wave_lamps import WaveLamps

# Call the logger test_NNN where NNN is the number of the script.
logger = getLogger("test_" + __file__.split("/")[-1].split("_")[0])

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    args = parser.parse_args()

    logger.info("script start")

    with WaveLamps(test_mode=args.test_mode) as wv:

        input("test \033[032;1moutlet=5 on\033[0m - press enter: ")
        try:
            wv.set_outlet_on(5)
        except Exception as e:
            print(e)
            logger.info("outlet 5 on failed")
        print("\n\n\n")

        input("test \033[032;1moutlet 5 off\033[0m - press enter: ")
        try:
            wv.set_outlet_off(5)
        except Exception as e:
            print(e)
            logger.info("outlet 5 off failed")
        print("\n\n\n")

        input("test \033[032;1moutlet=6 on\033[0m - press enter: ")
        try:
            wv.set_outlet_on(6)
        except Exception as e:
            print(e)
            logger.info("outlet 5 on failed")
        print("\n\n\n")

        input("test \033[032;1moutlet=6 off\033[0m - press enter: ")
        try:
            wv.set_outlet_off(6)
        except Exception as e:
            print(e)
            logger.info("outlet 5 off failed")
        print("\n\n\n")

        input(
            f"test \033[032;1mall lamps on [outlets={wv.outlets}]\033[0m - press enter: "
        )
        try:
            wv.all_lamps_on()
        except Exception as e:
            print(e)
            logger.info("all_lamps_on failed")
        print("\n\n\n")

        input("test \033[032;1mall lamps off\033[0m - press enter: ")
        try:
            wv.all_lamps_off()
        except Exception as e:
            print(e)
            logger.info("all_lamps_off failed")
        print("\n\n\n")
