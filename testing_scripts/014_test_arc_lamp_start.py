import dk154_control.dfosc.dfosc as df
from argparse import ArgumentParser
from logging import getLogger
import time
from dk154_control.camera.ccd3 import Ccd3
from dk154_control.tcs.ascol import Ascol

# from dk154_control.lamps.wave_lamps import WaveLamps
import yaml

dfosc_setup = yaml.load(
    open("dk154_control/dfosc/dfosc_setup.yaml"), Loader=yaml.FullLoader
)

logger = getLogger("test_" + __file__.split("/")[-1].split("_")[0])


def take_arc_calib(grism, slit, filt, test_mode=False):

    with Ascol(test_mode=test_mode) as ascol:
        ascol.wasp("empty")
        ascol.wagp()
        time.sleep(1.0)
        ascol.wait_for_result(ascol.wars, "locked")

        ascol.wbsp("empty")
        ascol.wbgp()
        time.sleep(1.0)
        ascol.wait_for_result(ascol.wbrs, "locked")

        ascol.log_all_status()

    with df.Dfosc(test_mode=test_mode) as dfosc:
        dfosc.grism_goto(dfosc_setup["grism"][grism])
        dfosc.aperture_goto(dfosc_setup["slit"][slit])
        dfosc.filter_goto(dfosc_setup["filter"][filt])

        # TODO: check if the exposure times are valid for 1.0" slit

        if grism == "3" or grism == "7" or grism == "14" or grism == "15":
            exp_time = 10
        elif grism == "5":
            exp_time = 40
        elif grism == "6":
            exp_time = 20
        elif grism == "8":
            exp_time = 150
        else:
            exp_time = 10

        dfosc.log_all_status()

    # with WaveLamps(test_mode=test_mode) as lamps:
    #    lamps.all_lamps_on()

    exp_params = {}
    exp_params["CCD3.exposure"] = str(exp_time)
    exp_params["CCD3.IMAGETYP"] = "WAVE,LAMP"
    exp_params["CCD3.OBJECT"] = "Hg calib"

    for i in range(8):  # first 6 mintues of lamp warmup
        with Ascol(test_mode=test_mode) as ascol:
            ascol.shop("1")
        with Ccd3(test_mode=test_mode) as ccd:
            # 'with' statement not really necessary for Ccd3()...
            ccd.set_exposure_parameters(exp_params)
            time.sleep(1.0)
            fname = f"test_arc_g{grism}_s{slit}_f{filt}_{i:03d}.fits"
            logger.info(f"start expname {fname}")
            ccd.start_exposure(fname)
        time.sleep(exp_time + 30)  # readout time

    # with WaveLamps(test_mode=test_mode) as lamps:
    #    lamps.all_lamps_off()


def wheel_return():
    with df.Dfosc() as dfosc:
        dfosc.aperture_goto(dfosc_setup["slit"]["empty"])
        dfosc.grism_goto(dfosc_setup["grism"]["empty"])
        dfosc.filter_goto(dfosc_setup["filter"]["empty0"])


if __name__ == "__main__":
    # define the parser
    parser = ArgumentParser(
        description="Take arc calibration images with DFOSC, preferred setup is with grism 15, slit 1.5, and no filter"
    )
    parser.add_argument(
        "-g", "--grism", nargs="+", type=str, choices=dfosc_setup["grism"].keys()
    )
    parser.add_argument(
        "-s", "--slit", nargs="+", type=str, choices=dfosc_setup["slit"].keys()
    )
    parser.add_argument(
        "-f", "--filt", nargs="+", type=str, choices=dfosc_setup["filter"].keys()
    )
    args = parser.parse_args()
    take_arc_calib(args.grism, args.slit, args.filt)
    wheel_return()
