import time
from argparse import ArgumentParser
from logging import getLogger

from dk154_control import DK154
from dk154_control.camera import Ccd3
from dk154_control.dfosc.dfosc import Dfosc, load_dfosc_setup
from dk154_control.local_backup import backup_and_add_header_keys
from dk154_control.utils import get_directory_datestr, get_hm_str

logger = getLogger("dfosc_flat_frames")

def take_flat_frames(
    grism_name, aper_name, filter_name, exp_time=30.0, n_exp=5, discard=2, read_time=60.0
):
       
    date_str = get_directory_datestr()
    hm_str = get_hm_str()
    aper_str = aper_name.replace(".", "p")
    
    with DK154() as dk154:
        dk154.move_wheel_a_and_wait("empty")
        dk154.move_wheel_b_and_wait("empty")
        
        dk154.move_dfosc_grism_and_wait(grism_name)
        dk154.move_dfosc_aperture_and_wait(aper_name)
        dk154.move_dfosc_filter_and_wait(filter_name)
        
    remote_dir = f"/ucph/{date_str}/calib" # "/data" is always prepended.
    
    
    ### ========= take some short 'discard' frames, to 'reset' CCD =========###
    #take_discard_frames(remote_dir, hm_str=hm_str, n_exp=discard)
    
    
    ### ==================== take the actual flat frames ===================###
    
    params = {}
    params["CCD3.exposure"] = exp_time
    params["CCD3.IMAGETYP"] = "FLAT" # this will be updated in backup...
    params["CCD3.OBJECT"] = "CALIB"
    
    for ii in range(n_exp):
    
        filename = f"flat_{grism_name}{aper_str}{filter_name}_{hm_str}_{ii:03d}.fits"
        remote_filepath = f"{remote_dir}/{filename}"
        
        with Ccd3() as ccd3:
            logger.info(f"start exposure {ii+1} / {n_exp}")
        
            state = ccd3.get_ccd_state()
            logger.info(f"before set parameters, ccd state {state}")
            
            logger.info(f"set params {params}")
            ccd3.set_exposure_parameters(params)
            
            ccd3.start_exposure(remote_filepath)
            
            ccd3.wait_for_exposure(exp_time=exp_time)
            
            try:
                backup_and_add_header_keys(f"/data/{remote_filepath}", img_type="FLAT,SKY")
            except Exception as e:
                logger.error(f"in backup {remote_filepath}:\n    {type(e).__name__} {e}")
    
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
    parser.add_argument("-a", "--aperture", choices=aper_choices, required=True)
    parser.add_argument("-f", "--filter", choices=filter_choices, required=True)
    parser.add_argument("-g", "--grism", choices=grism_choices, required=True)
    parser.add_argument("-n", "--n-exp", default=1, type=int)
    parser.add_argument("-t", "--exp-time", default=None, type=float)
    
    args = parser.parse_args()
    
    take_flat_frames(
        args.grism, args.aperture, args.filter, n_exp=args.n_exp, exp_time=args.exp_time
    )
    
    #wheel_reset()
    
    
    
    
    
    
    
    
    
