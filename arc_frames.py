import time
from argparse import ArgumentParser
from datetime import datetime, timedelta

from logging import getLogger

from dk154_control import DK154
from dk154_control.camera import Ccd3
from dk154_control.dfosc.dfosc import Dfosc, DfoscStatus, load_dfosc_setup
from dk154_control.lamps import WaveLamps
from dk154_control.local_backup import backup_and_add_header_keys
from dk154_control.utils import get_directory_datestr, get_hm_str
#from dk154_control.tcs import Ascol

logger = getLogger("arc_frames")

def take_arc_frames(grism_name, aper_name, filter_name, n_exp=1, exp_time=10.0):
    
    dfosc_setup = load_dfosc_setup()
    
    aper_pos = dfosc_setup["aperture"][aper_name]
    grism_pos = dfosc_setup["grism"][grism_name]
    filter_pos = dfosc_setup["filter"][filter_name]
    
    wheel_a_pos = "empty"
    wheel_b_pos = "empty"
    
    with DK154() as dk154:
        dk154.move_wheel_a_and_wait("empty")
        dk154.move_wheel_b_and_wait("empty")
        
    with DK154() as dk154:
        dk154.move_dfosc_aperture_and_wait(aper_name)
        dk154.move_dfosc_grism_and_wait(grism_name)
        dk154.move_dfosc_filter_and_wait(filter_name)
        
    dfosc_status = DfoscStatus()
    dfosc_status.log_all_status()
    
    with WaveLamps() as wv:
        wv.all_lamps_on()
    time.sleep(1.0)
    
    date_str = get_directory_datestr()
    hm_str = get_hm_str()
    aper_str = aper_name.replace(".", "p")    
    base_dir = f"/ucph/{date_str}/calib/arc/"
    object_name = f"Hglamp_{grism_name}{aper_name}{filter_name}_{hm_str}"
        
    exp_parameters = {}
    exp_parameters["CCD3.exposure"] = exp_time  # exp_time [sec]
    exp_parameters["CCD3.IMAGETYP"] = "LIGHT"
    exp_parameters["CCD3.OBJECT"] = "CALIB"
    exp_parameters["CCD3.SHUTTER"] = "0"
    
    for ii in range(n_exp):
        remote_filepath = f"{base_dir}/{object_name}_{ii:03d}.fits"
        with Ccd3() as ccd3:
            ccd3.set_exposure_parameters(exp_parameters)
            
            ccd3.start_exposure(remote_filepath)
        
            ccd3.wait_for_exposure(exp_time=exp_time)
                        
        try:
            backup_and_add_header_keys(f"/data/{remote_filepath}", img_type="WAVE,LAMP")
        except Exception as e:
            logger.error(f"in backup {remote_filepath}:\n    {type(e).__name__} {e}")
         
    with WaveLamps() as wv:
        wv.all_lamps_off()
         
def wheel_reset():
    with DK154() as dk154:
        dk154.move_dfosc_aper_wheel_and_wait("empty")
        dk154.move_dfosc_grism_wheel_and_wait("empty")
        dk154.move_dfosc_filter_wheel_and_go("empty0")
        
    ds = DfoscStatus.collect_silent()
    ds.log_all_status()


if __name__ == "__main__":

    dfosc_setup = load_dfosc_setup()
    
    aper_choices = list(dfosc_setup["aperture"].keys())
    grism_choices = list(dfosc_setup["grism"].keys())
    filter_choices = list(dfosc_setup["filter"].keys())
    
    parser = ArgumentParser()
    parser.add_argument("-a", "--aper", choices=aper_choices, required=True)
    parser.add_argument("-f", "--filter", choices=filter_choices, required=True)
    parser.add_argument("-g", "--grism", choices=grism_choices, required=True)
    parser.add_argument("-n", "--n-exp", default=1, type=int)
    parser.add_argument("-t", "--exp-time", default=15.0, type=float)
    
    args = parser.parse_args()
    
    take_arc_frames(args.grism, args.aper, args.filter, n_exp=args.n_exp, exp_time=args.exp_time)
    
    #wheel_reset()
    
    
    
