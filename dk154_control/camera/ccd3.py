import time
from logging import getLogger

import requests
import json

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
    "WASA.filter",
    "WASB.filter",
)


class Ccd3:
    EXTERNAL_URL = "http://134.171.81.78:/8889/"
    INTERNAL_URL = "http://192.168.132.52:8889/"
    LOCAL_URL = "http://127.0.0.1:8889/"
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

        self.debug = debug

        self.auth = requests.auth.HTTPBasicAuth(self.USER, self.PASSWORD)

        self.current_exposure_parameters = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def get_data(self, url, params):

        response = requests.get(url, auth=self.auth, params=params)
        return response.json()

    def get_ccd_response(self) -> requests.Response:
        get_url = f"{self.base_url}api/get"
        params = {"e": "1", "d": "CCD3"}  # Don't know what "e" or "d" mean.
        return self.get_data(get_url, params=params)

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

        result = self.get_data(mset_url, params=params)

        if self.debug:
            # TODO: Remove next two lines?
            result_str = json.dumps(result, indent=4)
            print(f"set_exposure_parameters() full response:\n {result_str}")
        return response

    def start_exposure(self, filename: str) -> requests.Response:
        """
        Requests 'api/expose'

        Parameters
        ----------
        filename [str]
            the name of the file to save.
        """

        if self.current_exposure_parameters is None:
            msg = "You have not set any exposure parameters since last exposure."
            logger.warning(msg)

        expose_url = f"{self.base_url}api/expose"
        params = {"ccd": "CCD3", "fe": str(filename)}

        response = self.get_data(expose_url, params=params)

        self.exposure_parameters = None
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

        result = ccd_response.json()
        ccd_state = result["state"]
        logger.info(f"CCD3 state: {ccd_state}")

        return ccd_state

    # def take_exposure(self, params: dict, filename: str) -> int:
    #     """
    #     Convenience method:
    #         sets parameters, starts exposure, waits for exposure to finish.
    #         returns an in

    #     Parameters
    #     ----------
    #     params [dict]
    #         the parameters to set for the exposure.

    #     """

    #     ccd_state = self.get_ccd_state()
    #     # TODO: some check on CCD state

    #     exptime = params.get("CCD3.exposure", None)
    #     if exptime is None:
    #         raise ValueError(
    #             "you should provide exp_time as 'CCD3.exposure' in params"
    #         )

    #     self.set_exposure_parameters(params)

    #     t_start = time.perf_counter()
    #     self.start_exposure(filename)

    #     sleep_time = float(exptime) + self.EXPOSURE_SLEEP_BUFFER
    #     # logger.info(f"sleep for {sleep_time:.2f}s during exposure")
    #     # time.sleep(sleep_time)

    #     logger.info("TEST: report status every few seconds...")
    #     while time.perf_counter() - t_start < sleep_time:
    #         self.get_ccd_state()
    #         time.sleep(3.0)

    #     ccd_state = self.get_ccd_state()
    #     return ccd_state

    # def take_flat(self, filter, exptime, filename):
