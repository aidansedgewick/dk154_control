import time
from argparse import ArgumentParser
from logging import getLogger

from dk154_control.local_backup import backup_and_add_header_keys
from dk154_control.camera import Ccd3, take_discard_frames
from dk154_control.utils import get_directory_datestr, get_hm_str

logger = getLogger("bias_frames")

def take_40_bias_frames():
    take_bias(n_exp=40)
    
def take_20_bias_frames():
    take_bias(n_exp=20)
    
def take_bias(n_exp=1, read_time=25, discard=2):
    
    date_str = get_directory_datestr()
    hm_str = get_hm_str()
        
    remote_dir = f"/ucph/{date_str}/calib/"
    
    ### ========= take some short 'discard' frames, to 'reset' CCD =========###
    take_discard_frames(remote_dir, hm_str=hm_str, n_exp=discard)
    
    
    ###================== Now start the actual bias frames ====================###
        
    bias_exp_time = 0.005
    
    params = {}
    params["CCD3.exposure"] = bias_exp_time
    params["CCD3.IMAGETYP"] = "BIAS"
    params["CCD3.OBJECT"] = "CALIB"
    
    logger.info(f"take {n_exp} bias frames")
    
    for ii in range(n_exp):
    
        filename = f"bias_{hm_str}_{ii:03d}.fits"
        remote_filepath = f"{remote_dir}/{filename}"
    
        with Ccd3() as ccd3:
            logger.info(f"start bias {ii+1} / {n_exp}")
        
            state = ccd3.get_ccd_state()
            logger.info(f"before set params, CCD3 state is {state}")
        
            ccd3.set_exposure_parameters(params)
            
            ccd3.start_exposure(remote_filepath)
            
            ccd3.wait_for_exposure(exp_time=bias_exp_time)
                
            try:
                backup_and_add_header_keys(f"/data/{remote_filepath}")
            except Exception as e:
                logger.error(f"in backup {remote_filepath}:\n    {type(e).__name__} {e}")
                

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--long", default=False, action="store_true")
    parser.add_argument("--short", default=False, action="store_true")
    parser.add_argument("--n-exp", default=0, type=int)
    args = parser.parse_args()
    
    if args.long + args.short + args.n_exp == 0:
        raise ValueError("Give EXACTLY ONE of --long (n=40), --short (n=20), or --n-exp [int]")
    
    if args.n_exp == 0:
        if args.long + args.short != 1:
            raise ValueError("provide ONLY ONE of --long/--short")
        
        if args.long:
            take_40_bias_frames()
        
        if args.short:
            take_20_bias_frames()
    
    else:
        if args.short or args.long:
            raise ValueError("Can't provide --long/--short AND --n-exp!")
    
    
    
    
    
    

