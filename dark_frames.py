import time
from argparse import ArgumentParser
from logging import getLogger

from dk154_control import DK154
from dk154_control.tcs import Ascol
from dk154_control.local_backup import backup_and_add_header_keys
from dk154_control.camera import Ccd3, take_discard_frames
from dk154_control.utils import get_directory_datestr, get_hm_str

logger = getLogger("dark_frames")

def take_dark(exp_time=1800.0, n_exp=1, read_time=60.0, discard=2):

    with DK154() as dk154:
        dk154.move_wheel_a_and_wait("empty")
        dk154.move_wheel_b_and_wait("empty")
    
    with Ascol() as ascol:
        ascol.shop("0")
        time.sleep(1.0)
        shutter_pos = ascol.shrp()
        logger.info(f"shutter_pos = {shutter_pos}")
    
    date_str = get_directory_datestr()
    hm_str = get_hm_str()
    remote_dir = f"/ucph/{date_str}/calib/"
        
    wait_time = exp_time + read_time
    
    
    ### ========= take some short 'discard' frames, to 'reset' CCD =========###
    take_discard_frames(remote_dir, n_exp=discard)
    
    ###================== Now start the actual dark frames ====================###
    
    params = {}
    params["CCD3.exposure"] = exp_time
    params["CCD3.IMAGETYP"] = "DARK"
    params["CCD3.OBJECT"] = "CALIB"
    params["CCD3.SHUTTER"] = "1" # in CCD3 'speak' open=0, closed=1: REVERSE of ASCOL!
    
    logger.info(f"take {n_exp} exposures of {exp_time}sec")
    
    for ii in range(n_exp):    
        
        filename = f"dark_{hm_str}_{ii:03d}.fits"
        remote_filepath = f"{remote_dir}/{filename}"
    
        with Ccd3() as ccd3:              
            logger.info("start dark exposure {ii+1} / {n_exp}")
        
            state = ccd3.get_ccd_state()
            logger.info(f"before set params, CCD3 state is {state}")
        
            ccd3.set_exposure_parameters(params)
                   
            ccd3.start_exposure(remote_filepath)
            
            ccd3.wait_for_exposure(exp_time=exp_time)
            
            try:
                backup_and_add_header_keys(f"/data/{remote_filepath}")
            except Exception as e:
                logger.error(f"in backup {remote_filepath}:\n    {type(e).__name__} {e}")
                

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--n-exp", default=5, type=int)
    parser.add_argument("--exp-time", default=1800.0, type=float)
    args = parser.parse_args()
    
    take_dark(exp_time=args.exp_time, n_exp=args.n_exp)
        
    
    
    
    
    
    

