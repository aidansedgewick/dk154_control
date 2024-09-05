import time
import yaml
from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from typing import List

from astropy.coordinates import SkyCoord

from dk154_control import DK154

from dk154_control.tcs.ascol import Ascol
from dk154_control.tcs import ascol_constants
from dk154_control.dfosc.dfosc import Dfosc, load_dfosc_setup
from dk154_control.obs_parser import ObservationParser

logger = getLogger("103_observe")


dfosc_setup = load_dfosc_setup()


def move_telescope_and_wait(ra_str, dec_str, test_mode=False):
    with Ascol(test_mode=test_mode) as ascol:

        curr_ra, curr_dec, curr_pos = ascol.trrd()

        ascol.tsra(ra_str, dec_str, curr_pos)
        ascol.tgra()

        tel_state = ascol.ters()
        while tel_state not in ["ready", "sky track"]:
            time.sleep(5.0)
            tel_state = ascol.ters()


def do_observation(config: dict, test_mode=False):

    if isinstance(config, Path):
        # if it's a path, not a dictionary.
        with open(config) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

    # Read config parameters
    target_name = config["name"]
    target_ra = config["ra"]
    target_dec = config["dec"]

    fasu_a = config["fasu_a"]
    fasu_b = config["fasu_b"]

    dfosc_grism = config["grism"]
    dfosc_slit = config["slit"]
    dfosc_filter = config["filter"]

    n_exp = config["n_exp"]
    exptime = config["exptime"]

    target_coord = SkyCoord(ra=target_ra, dec=target_dec, unit="deg")

    dk154 = DK154(test_mode=test_mode)
    dk154.move_telescope_and_wait(target_coord, 0)
    dk154.move_wheel_a_and_wait(fasu_a)
    dk154.move_wheel_b_and_wait(fasu_b)

    dk154.move_dfosc_grism_and_wait(dfosc_grism)
    dk154.move_dfosc_slit_and_wait(dfosc_slit)
    dk154.move_dfosc_filter_and_wait(dfosc_filter)

    # "target_name" converted to filename eg. "M31" -> "M31_001.fits", "M31_002.fits"
    dk154.take_multi_science_exposure(exptime, target_name, n_exp)

    return


def observe_grid(config_filelist: List[Path]):
    for config_file in config_filelist:
        do_observation(config_file)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("-t", "--test-mode", default=False, action="store_true")

    args = parser.parse_args()

    if Path(args.config).is_dir():
        config_filelist = args.config.glob("*.y*ml")  # catch .yaml AND .yml
        logger.info(f"found {len(config_filelist)} observation configs.")

        observe_grid(config_filelist)
    else:

        with open(args.config) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
        do_observation(config, test_mode=args.test_mode)
