import time
from argparse import ArgumentParser
from logging import getLogger

from dk154_control.camera.ccd3 import Ccd3
from dk154_control.tcs.ascol import Ascol


logger = getLogger("test_" + __file__.split("/")[-1].split("_")[0])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    args = parser.parse_args()

    test_mode = args.test_mode  # False by default
    debug = args.debug  # False by default

    logger.info("start script")

    with Ascol(test_mode=test_mode, debug=debug) as ascol:

        input("test \033[032;1mbrightness east (MEBE)\033[0m - press enter: ")
        logger.info("test MEBE")
        try:
            brightness, validity = ascol.mebe()
            logger.info(f"brightness east: {brightness} kLux, {validity}")
        except Exception as e:
            print(e)
            logger.error("MEBE failed")
        print("\n\n\n")

        input("test \033[032;1mbrightness north (MEBN)\033[0m - press enter: ")
        logger.info("test MEBN")
        try:
            brightness, validity = ascol.mebn()
            logger.info(f"brightness north: {brightness} kLux, {validity}")
        except Exception as e:
            print(e)
            logger.error("MEBN failed")
        print("\n\n\n")

        input("test \033[032;1mbrightness west (MEBW)\033[0m - press enter: ")
        logger.info("test MEBW")
        try:
            brightness, validity = ascol.mebw()
            logger.info(f"brightness west: {brightness} kLux, {validity}")
        except Exception as e:
            print(e)
            logger.error("MEBW failed")
        print("\n\n\n")

        input("test \033[032;1mmeteo twilight (METW)\033[0m - press enter: ")
        logger.info("test METW")
        try:
            twilight, validity = ascol.metw()
            logger.info(f"twilight: {twilight} Lux, {validity}")
        except Exception as e:
            print(e)
            logger.error("METW failed")
        print("\n\n\n")

        input("test \033[032;1mmeteo humidity (MEHU)\033[0m - press enter: ")
        logger.info("test MEHU")
        try:
            humidity, validity = ascol.mehu()
            logger.info(f"humidity: {humidity}%, {validity}")
        except Exception as e:
            print(e)
            logger.error("MEHU failed")
        print("\n\n\n")

        input("test \033[032;1mtemp (METE)\033[0m - press enter: ")
        logger.info("test METE")
        try:
            temp, validity = ascol.mete()
            logger.info(f"temperature: {temp} degC, {validity}")
        except Exception as e:
            print(e)
            logger.error("METE failed")
        print("\n\n\n")

        input("test \033[032;1mwind speed (MEWS)\033[0m - press enter: ")
        logger.info("test MEWS")
        try:
            wind, validity = ascol.mews()
            logger.info(f"wind speed: {wind} m/s, {validity}")
        except Exception as e:
            print(e)
            logger.error("MEWS failed")
        print("\n\n\n")

        input("test \033[032;1mprecip (MEPR)\033[0m - press enter: ")
        logger.info("test MEPR")
        try:
            precip, validity = ascol.mepr()
            logger.info(f"precipitation: {precip}, {validity}")
        except Exception as e:
            print(e)
            logger.error("MEPR failed")
        print("\n\n\n")

        input("test \033[032;1matm pressure (MEAP)\033[0m - press enter: ")
        logger.info("test MEAP")
        try:
            press, validity = ascol.meap()
            logger.info(f"precipitation: {press} mbar, {validity}")
        except Exception as e:
            print(e)
            logger.error("MEAP failed")
        print("\n\n\n")

        input("test \033[032;1mirradiance (MEPY)\033[0m - press enter: ")
        logger.info("test MEPY")
        try:
            irr, validity = ascol.meap()
            logger.info(f"irradiance: {irr} W/m2, {validity}")
        except Exception as e:
            print(e)
            logger.error("MEPY failed")
        print("\n\n\n")
