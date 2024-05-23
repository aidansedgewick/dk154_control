import time
import traceback

from argparse import ArgumentParser
from logging import getLogger

from astropy import units as u
from astropy.coordinates import Angle, SkyCoord

from dk154_control.tcs.ascol import Ascol

logger = getLogger("test_" + __file__.split("/")[-1].split("_")[0])


POSITION_LOOKUP = {"east": "0", "west": "1"}

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    args = parser.parse_args()

    test_mode = args.test_mode  # False by default
    debug = args.debug  # False by default

    with Ascol(test_mode=test_mode, debug=debug) as ascol:
        print("\n\n\n")

        input("\033[32;1mGet current ra, dec, pos\033[0m - press enter: ")
        ra, dec, tel_pos = ascol.trrd()

        # Some formatting to make it a SkyCoord to make it easy to nudge...
        ra_str = f"{dec[:2]} {dec[2:4]} {dec[5:]}"
        dec_str = f"{ra[:3]} {ra[3:5]} {ra[5:]}"
        curr_coord = SkyCoord(ra=ra_str, dec=dec_str, unit=(u.hourangle, u.deg))

        logger.info(f"currently: ra={ra}, dec={dec}, pos={tel_pos}")
        logger.info(f"    = ({curr_coord.ra.deg:.4f}, {curr_coord.dec.deg:.4f})")
        print("\n\n\n")

        input("\033[32;1mNudge the telescope a bit\033[0m - press enter: ")
        dra, ddec = +30.0 * u.arcmin, +30.0 * u.arcmin
        new_coord = curr_coord.spherical_offsets_by(dra, ddec)

        ra_hms = new_coord.ra.hms
        ra_str = f"{int(ra_hms.h):02d}{int(ra_hms.m):02d}{ra_hms.s:.1f}"  # Format...
        dec_dms = new_coord.dec.dms
        dec_str = f"{int(dec_dms.d):+02d}{int(dec_dms.m)}{dec_dms.s:.1f}"
        pos_str = POSITION_LOOKUP[tel_pos]

        logger.info(f"move to: ra={ra_str}, dec={dec_str}, pos={pos_str}")
        logger.info(f"    = ({new_coord.ra.deg:.4f}, {new_coord.dec.deg:.4f})")
        print("\n\n\n")

        input("test \033[32;1mTelescope Set RA/dec (TSRA)\033[0m - press enter: ")
        # USE YOUR OWN!
        # ra_str = "120000.34" # f.example - must be in hhmmss.ss format
        # dec_str = "-301515.12" # in ddmmss.ss fmt.
        try:
            TRSA_result = ascol.tsra(ra_str, dec_str, pos_str)
            logger.info(f"TRSA result: {TRSA_result}")
        except Exception as e:
            print(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.error("TSRA failed!")
        print("\n\n\n")

        input("test \033[32;1mTelescope Go RA/dec (TGRA)\033[0m - press enter: ")
        TGRA_success = False
        try:
            TGRA_result = ascol.tgra()
            logger.info(f"TGRA_result: {TGRA_result}")
            if TGRA_result != "ERR":
                TGRA_success = True
        except Exception as e:
            print(e)
            logger.info("traceback:\n" + traceback.format_exc())
            logger.error("TGRA failed!")

        if TGRA_success:
            for ii in range(30):
                tel_state = ascol.ters()
                logger.info(f"tel state: {tel_state}")
                if tel_state == "sky track":
                    break
                time.sleep(2.0)
