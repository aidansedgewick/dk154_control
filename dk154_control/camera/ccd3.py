import time
from logging import getLogger

import requests
import json

from dk154_control.utils import get_hm_str
from dk154_control.local_backup import backup_and_add_header_keys

logger = getLogger(__name__.split(".")[-1])


CAMERA_READY = 0  # TODO: check this is true!
CAMERA_READING = 2
CAMERA_HAS_IMAGE = 8
DEVICE_ERROR_KILL = 65536
CAMERA_EXPOSING_SHUTTER_OPEN = 67108865

EXPECTED_PARAMETERS = (
    "async",
    "CCD3.exposure",
    "CCD3.IMAGETYP",
    "CCD3.OBJECT",
    "CCD3.SHUTTER",
    "WASA.filter",
    "WASB.filter",
)


def take_discard_frames(
    remote_dir: str, hm_str=None, n_exp=2, discard_exposure=1.0, test_mode=False
):

    hm_str = hm_str or get_hm_str()

    discard_params = {"CCD3.exposure": discard_exposure, "CCD3.SHUTTER": "1"}

    logger.info(f"take {n_exp} discard frames")

    for ii in range(n_exp):

        t_start = time.perf_counter()
        with Ccd3(test_mode=test_mode) as ccd3:
            state = ccd3.get_ccd_state()
            logger.info(f"before set discard params, ccd state {state}")

            logger.info(f"set discard params {discard_params}")
            ccd3.set_exposure_parameters(discard_params)

            discard_filename = f"discard_{hm_str}_{ii:03d}.fits"
            remote_filepath = f"{remote_dir}/{discard_filename}"

            ccd3.start_exposure(remote_filepath)

            ccd3.wait_for_exposure(exp_time=discard_exposure)

            try:
                backup_and_add_header_keys(f"/data/{remote_filepath}")
            except Exception as e:
                logger.error(
                    f"in backup {remote_filepath}:\n    {type(e).__name__} {e}"
                )

    return


class Ccd3:
    EXTERNAL_URL = "http://134.171.81.78:/8889/"
    INTERNAL_URL = "http://192.168.132.52:8889/"
    LOCAL_URL = "http://127.0.0.1:8884/"
    USER = "dk154"
    PASSWORD = "dk154"

    EXPOSURE_SLEEP_BUFFER = 3.0

    def __init__(self, external=False, test_mode=False, debug=False):
        logger.info("initialise Ccd3 ")

        self.exposure_parameters = None

        self.external = external
        if external:
            self.base_url = self.EXTERNAL_URL
        else:
            self.base_url = self.INTERNAL_URL

        self.test_mode = test_mode
        if self.test_mode:
            self.base_url = self.LOCAL_URL

        self.debug = debug  # TODO: change debug mode so that the LOGGER is changed!

        self.auth = requests.auth.HTTPBasicAuth(self.USER, self.PASSWORD)

        self.current_exposure_parameters = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def get_data(self, url, params):

        response = requests.get(url, auth=self.auth, params=params)
        time.sleep(0.5)  # Czech scripts show waiting 0.5s after calling is helpful.

        return response.json()

    def get_ccd_response(self) -> requests.Response:
        get_url = f"{self.base_url}api/get"
        params = {"e": "1", "d": "CCD3"}  # Don't know what "e" or "d" mean.

        response = self.get_data(get_url, params=params)
        if self.debug:
            # TODO: Remove next two lines?
            response_str = json.dumps(response, indent=4)
            logger.info(f"full response:\n{response_str}")
        return response

    def set_exposure_parameters(
        self, params: dict, use_async=True
    ) -> requests.Response:
        """
        Requests 'api/mset'

        Parameters
        ----------
        params [dict]
            dictionary parameters to set.
        """

        mset_url = f"{self.base_url}api/mset"
        if use_async and "async" not in params:
            params["async"] = 0

        # Are we trying to set something unexpected?
        unknown_params = {
            key: val for key, val in params.items() if key not in EXPECTED_PARAMETERS
        }
        if len(unknown_params) > 0:
            logger.warning(f"Unknown exposure parameters:\n {unknown_params}")
        self.current_exposure_parameters = params

        response = self.get_data(mset_url, params=params)
        # state = response["state"]
        # logger.info(f"after set params, state={state}")

        if self.debug:
            # TODO: Remove next two lines?
            response_str = json.dumps(response, indent=4)
            logger.info(f"set_exposure_parameters() full response:\n {response_str}")
        return response

    def start_exposure(self, filename: str) -> requests.Response:
        """
        Requests 'api/expose'

        Parameters
        ----------
        filename [str]
            the name of the file to save.
        """
        logger.info("starting exposure")

        if self.current_exposure_parameters is None:
            msg = (
                "You have not set any exposure parameters since last exposure"
                " - the last exposure parameters will be repeated."
            )
            logger.warning(msg)

        expose_url = f"{self.base_url}api/expose"
        params = {"ccd": "CCD3", "fe": str(filename)}

        response = self.get_data(expose_url, params=params)
        state = response["state"]
        logger.info(f"after start exp: state={state}")

        self.exposure_parameters = None  # so that we warn if parameters are not reset
        return response

    def stop_exposure(self) -> requests.Response:
        """
        Sends api/killscript to CCD3
        """

        stop_url = f"{self.base_url}api/killscript"
        params = {"d": "CCD3"}

        return self.get_data(stop_url, params)

    def get_ccd_state(self) -> int:

        ccd_response = self.get_ccd_response()

        ccd_state = ccd_response["state"]
        if self.debug:
            logger.info(f"CCD3 state: {ccd_state}")

        return ccd_state

    def wait_for_exposure(
        self, exp_time: float = None, read_time=45.0, log_interval=20.0, log_state=True
    ):

        time.sleep(1.0)
        t_start = time.perf_counter()

        if exp_time is None:
            response = self.get_ccd_response()
            exp_time = response["d"]["exposure"][1]
            logger.info("read exposure time as {exp_time}s")
            # 'exposure' is a list [<code>, <exp_time>, 0, 0, <comment>]

        logger.info(f"wait {exp_time:.1f}+{read_time:.1f}sec for exposure")

        wait_time = exp_time + read_time

        dt = time.perf_counter() - t_start
        while dt < wait_time:
            time.sleep(log_interval)
            dt = time.perf_counter() - t_start
            if log_state:
                state = self.get_ccd_state()
                logger.info(f"after {dt:.1f}s, ccd state is {state}")

        logger.info(f"exit after wait {dt:.1f}s")

        return
