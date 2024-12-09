import os
import yaml
from pathlib import Path
from logging import getLogger

from paramiko import SSHClient, AutoAddPolicy
from paramiko.config import SSH_PORT
from scp import SCPClient

from astropy.io import fits


import dk154_control
from dk154_control.dfosc import Dfosc, DfoscStatus
from dk154_control.lamps import WaveLamps

logger = getLogger(__file__.split("/")[-1].split("_")[0])

REQUIRED_REMOTE_CONFIG_KEYS = ("remote_host", "remote_username", "remote_password")


def local_backup(
    remote_filepath,
    local_filepath,
    remote_host,
    remote_username,
    remote_password,
    remote_port=None,
):

    remote_port = remote_port or SSH_PORT

    logger.info(
        f"start copy:\n    {remote_host}:{remote_filepath}\n    to: local {local_filepath}"
    )
    try:
        ssh_client = SSHClient()
        ssh_client.load_system_host_keys()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(
            remote_host,
            username=remote_username,
            password=remote_password,
            port=remote_port,
        )

        with SCPClient(ssh_client.get_transport()) as scp_client:
            scp_client.get(remote_filepath, local_filepath)
    except Exception as e:
        raise Exception(
            e
        )  # still want exception to be raised - might rely on it outside...
    finally:
        # Make sure that
        if ssh_client:
            ssh_client.close()
            logger.info("close ssh_client conn")


def check_remote_config(remote_config: dict):
    missing_keys = [k for k in REQUIRED_REMOTE_CONFIG_KEYS if k not in remote_config]
    if len(missing_keys) > 0:
        logger.warn(f"In remote_config: missing keys {missing_keys}")


def backup_and_add_header_keys(
    remote_filepath,
    local_filepath=None,
    local_raw_dir=None,
    remote_config=None,
    remote_base_dir="/data/ucph/",
    local_base_dir="/home/dk154/data/",
    img_type=None,
    **header_keys,
):
    """
    TODO: improve deciding where to save data.

    Parameters
    ----------
    remote_filename : str, pathlib.Path
        what is the (full) name of the filename on the remote machine?
        ie. "
    remote_config : dict
        dict containing 'remote_host', 'remote_username', 'remote_password',
        optionally 'remote_port'
        eg. {'remote_host': '192.168.132.1', 'remote_username': 'me', 'remote_password': 'pass'}

    """

    if remote_config is None:
        if dk154_control.default_config_path.exists():
            with open(dk154_control.default_config_path) as f:
                full_config = yaml.load(f, Loader=yaml.FullLoader)
            remote_config = full_config.get("remote_config", None)
        else:
            msg = (
                f"Default config not found at \033[33;1m{dk154_control.default_config_path}\033[0m. "
                f"Either add this config (containing 'remote_config' with keys "
                f"{REQUIRED_REMOTE_CONFIG_KEYS}, or provide remote_config=<dict>)"
            )
            raise FileNotFoundError(msg)
    if remote_config is None:
        msg = (
            f"Either add 'remote_config;' with keys {REQUIRED_REMOTE_CONFIG_KEYS} "
            f"into \033[33;1m{dk154_control.default_config_path}\033[0m, "
            f"or provide kwarg remote_config=<dict>"
        )
        raise ValueError(msg)

    check_remote_config(remote_config)

    remote_filepath = Path(remote_filepath)
    local_base_dir = Path(local_base_dir)
    remote_base_dir = Path(remote_base_dir)

    if local_filepath is None:
        # Decide where to save the file. We want to save it in a similar
        # directory structure that's on remote (eg. lin1), but under a different
        # 'top-level' eg. copy from [lin1] "/data/ucph/20241124/bias/bias_001.fits"
        # to [.55] "/home/dk154/data/20241124/bias/bias_001.fits",

        if local_raw_dir is None:
            local_raw_dir = local_base_dir / "raw"
        else:
            local_raw_dir = Path(local_raw_dir)

        # convert fx. [lin1] "/data/ucph/20241124/bias/bias_001.fits"
        #  -> "20241124/biasl/bias_001.fits" -- ie. keep only the useful bit.
        try:
            local_name = remote_filepath.relative_to(remote_base_dir)
        except Exception as e:
            logger.info(f"In extract filepath: {type(e).__name__} {e}")
            local_name = remote_filepath

        local_raw_filepath = local_raw_dir / local_name

        local_raw_filepath.parent.mkdir(exist_ok=True, parents=True)
        local_backup(remote_filepath, local_raw_filepath, **remote_config)

        mod_fname = f"{local_raw_filepath.stem}_mh{local_raw_filepath.suffix}"
        local_mod_dir = local_base_dir / local_name.parent
        local_mod_dir.mkdir(exist_ok=True, parents=True)
        local_mod_filepath = local_mod_dir / mod_fname

    else:
        raise NotImplementedError("can't give local_filepath yet")

    dfosc_status = DfoscStatus()

    try:
        with WaveLamps() as wv:
            wavelamp_status = wv.get_all_lamps_state()
    except Exception as e:
        wavelamp_status = {}

    with fits.open(local_raw_filepath) as f:

        f[0].header["GAIN"] = (0.164, "e/ADU, measured in lab (2016)")

        aper_name_comment = "DFOSC aperture name, eg. A15 = 1.5'' slit."
        aper_pos_comment = "DFOSC aperture position (exact wheel pos.)"
        grism_name_comment = "DFOSC grism name, eg. G15 = grism #15"
        grism_pos_comment = "DFOSC grism position (exact wheel pos.)"
        filter_name_comment = "DFOSC filter name eg. G11 = grism #11 (cross-disperser)"
        filter_pos_comment = "DFOSC filter position (exact wheel pos.)"
        f[0].header["DFAPRNM"] = (dfosc_status.aper_name_guess, aper_name_comment)
        f[0].header["DFAPRPOS"] = (dfosc_status.aper_position, aper_pos_comment)
        f[0].header["DFGRINM"] = (dfosc_status.grism_name_guess, grism_name_comment)
        f[0].header["DFGRIPOS"] = (dfosc_status.grism_position, grism_pos_comment)
        f[0].header["DFFLTNM"] = (dfosc_status.filter_name_guess, filter_name_comment)
        f[0].header["DFFLTPOS"] = (dfosc_status.filter_position, filter_pos_comment)

        for outlet_number, lamp_status in wavelamp_status.items():
            header_key = f"WVLAMP{outlet_number:1d}"
            comment = f"Hg lamp state (PDU outlet={outlet_number} 1=on 2=off)"
            f[0].header[header_key] = (lamp_status, comment)

        if img_type is not None:
            curr_type = f[0].header["IMAGETYP"]
            comment = f"Updated from {curr_type} during copy"
            f[0].header["IMAGETYP"] = (img_type.upper(), comment)

        for k, v in header_keys.items():
            f[0].header[k] = v

        f.writeto(local_mod_filepath)
