import traceback
from logging import getLogger

from dk154_control.tcs.ascol import Ascol

logger = getLogger("test_" + __file__.split("/")[-1].split("_")[0])

if __name__ == "__main__":

    with Ascol(test_mode=True) as ascol:

        logger.info("test GLUT")
        input("press enter: ")
        try:
            mjd, time_str = ascol.glut()
            logger.info(f"MJD/time: {mjd} & {time_str}")
        except Exception as e:
            print(e)
            logger.error("GLRE failed")
        print("=================\n\n")

        logger.info("test GLSD")
        input("press enter: ")
        try:
            time_str = ascol.glsd()
            logger.info(f"sideral time {time_str}")
        except Exception as e:
            print(e)
            logger.error("GLRE failed")
        print("=================\n\n")
