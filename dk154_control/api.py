import time
from logging import getLogger

from astropy.coordinates import SkyCoord
from astropy.time import Time

from dk154_control.camera.ccd3 import Ccd3
from dk154_control.tcs.ascol import Ascol
from dk154_control.tcs import ascol_constants
from dk154_control.dfosc.dfosc import Dfosc, load_dfosc_setup

logger = getLogger("DK154")

dfosc_setup = load_dfosc_setup()

FASU_A_POS_LOOKUP = {v: k for k, v in ascol_constants.WARP_CODES.items()}
FASU_B_POS_LOOKUP = {v: k for k, v in ascol_constants.WBRP_CODES.items()}

DFOSC_GRISM_LOOKUP = dfosc_setup["grism"]
DFOSC_SLIT_LOOKUP = dfosc_setup["slit"]
DFOSC_FILTER_LOOKUP = dfosc_setup["filter"]


class DK154:
    """
    User-friendly interface for common operations with the telescope.

    Args:
        test_mode (bool, default=False): for use with ``dk154_mock`` tools.

    It is preferred to use DK154 in a ``with`` block, as some connections to servers
    (ASCOL, DFOSC MOXA) are closed nicely on exit.

    Examples:
        Move the telecope, move the A and B wheels.

        >>> from dk154_control import DK154
        >>> from astropy.coordinates import SkyCoord
        >>>
        >>> m83 = SkyCoord(ra=204.2538, dec=-29.86576, unit="deg")
        >>> tel_pos = "0"  # "0" = "east", "1" = "west".
        >>> with DK154() as dk154:
        ...     wheel_a_state = dk154.move_wheel_a_and_wait("empty")
        ...     wheel_b_state = dk154.move_wheel_b_and_wait("V")
        ...     tel_state = dk154.move_telescope_and_wait(m83, 0)



    """

    def __init__(self, test_mode=False):
        self.test_mode = test_mode

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Correctly close connections.
        """

    def log_all_status(self):
        with Ascol(test_mode=self.test_mode) as ascol:
            ascol.log_all_status()
        with Dfosc(test_mode=self.test_mode) as dfosc:
            dfosc.log_all_status()

    def list_all_wheel_positions(self):
        """
        Print all possible wheel positions.
        """

        wheel_states = (
            "ALL WHEEL STATES\n----------------"
            + "\nFASU A:\n    "
            + " ".join(f"'{k}'" for k in FASU_A_POS_LOOKUP.keys())
            + "\nFASU B:\n    "
            + " ".join(f"'{k}'" for k in FASU_B_POS_LOOKUP.keys())
            + "\nDFOSC grism:\n    "
            + " ".join(f"'{k}'" for k in DFOSC_GRISM_LOOKUP.keys())
            + "\nDFOSC slit/aperture:\n    "
            + " ".join(f"'{k}'" for k in DFOSC_SLIT_LOOKUP.keys())
            + "\nDFOSC filter:\n    "
            + " ".join(f"'{k}'" for k in DFOSC_FILTER_LOOKUP.keys())
        )
        print(wheel_states)

    def move_telescope_and_wait(
        self,
        coord: SkyCoord,
        pos: str,
        wait_for_state=("ready", "sky track"),
        timeout=600.0,
    ):
        """
        Convenience function, which formats an ``astropy.coordinates.SkyCoord``
        coordinate
        Formatted string is passed to ascol.tsra(), then repeatedly call tgra()
        Wait for the telescope state to be 'ready' or 'sky track'

        Args:
            coord (astropy.coordinates.SkyCoord): The coordinate to move the telecope to.
                This will be formatted as required by the ASCOL server.
            pos (str): The telescope position "0" - "east", "1"=="west"
            wait_for_state (str or tuple of str, default=("ready", "skytrack"))
                Wait for ``ascol.ters`` (TElescope Read State) to be one of these state(s).
            timeout (float, default=600.0): The amount of time to wait for the
                telescope state to match `wait_for_state` [sec].
                Raises WaitForResultTimeoutError if the state does not match before timeout.

        Returns:
            result (str): The result of the ascol.ters command after it matches
                the ``wait_for_state`` commmand.

        Example:
            Move to (ra,dec) = (45.0, -30.0)

            >>> from dk154_control import DK154
            >>> from astropy.coordinates import SkyCoord
            >>> new_target = SkyCoord(ra=45.0, dec=-30.0, unit="deg")
            >>> with DK154() as dk154:
            ...     result = dk154.move_telescope_and_wait()
            >>> print(result)
            sky track

        """

        ra_hms = coord.ra.hms
        dec_dms = coord.dec.dms
        ra_str = f"{int(ra_hms.h):02d}{int(ra_hms.m):02d}{ra_hms.s:05.2f}"
        dec_str = f"{int(dec_dms.d):+02d}{int(dec_dms.m):02d}{dec_dms.s:05.2f}"
        # need '05' in arcsec str because float ".xx" counts as 3 characters!

        if isinstance(pos, int):
            pos = str(pos)  # TSRA It accepts a string
        pos_code_lookup = {"0": "0", "1": "1", "east": "0", "west": "1"}
        # see ascol_constants.TRRD_POSITION_CODES
        pos_code = pos_code_lookup.get(str(pos).lower(), None)

        if pos_code is None:
            logger.error(f"unknown position for TRRD: {pos}")
            logger.error("Choose '0' (east) or '1' (west)")
            logger.error(f"will not move to {ra_str}, {dec_str}")

        logger.info(f"set ra/dec to {ra_str} {dec_str} {pos_code}")

        with Ascol(test_mode=self.test_mode) as ascol:
            tsra_result = ascol.tsra(ra_str, dec_str, pos_code)
            tgra_result = ascol.tgra()
            time.sleep(1.0)
            res = ascol.wait_for_result(
                ascol.ters, expected_result=wait_for_state, delay=5.0, timeout=timeout
            )

        return res

    def move_wheel_a_and_wait(self, wheel_a_filter: str, wait_for_state="stopped"):
        """
        Move FASU A wheel to provided filter, and wait until FASU A state is 'stopped'

        Args:
            wheel_a_filter (str):
                the NAME of the filter eg. 'Stromgr v', 'OIII', 'empty',
                NOT ascol pos (eg '01', '02', '03'). Raises KeyError if unknown
                filter (as defined in ``ascol.ascol_constants.WARP_CODES``)
            wait_for_state ()str or tuple of str, default="stopped"):
                Wait for ``ascol.wars`` (Wheel A Read State) to be one of these state(s).

        Returns:
            res (str):
                The result of ``ascol.wars`` when it matches one of ``wait_for_state``.

        """

        wheel_a_pos = FASU_A_POS_LOOKUP.get(wheel_a_filter, None)

        if wheel_a_pos is None:
            msg = (
                f"unknown FASU A filter '{wheel_a_filter}'\n"
                f"    known: {FASU_A_POS_LOOKUP.keys()}"
            )
            raise KeyError(msg)

        with Ascol(test_mode=self.test_mode) as ascol:
            wheel_a_curr = ascol.warp()
            wheel_a_state = ascol.wars()
            if wheel_a_pos == wheel_a_curr:
                logger.info(f"FASU A already at {wheel_a_filter}")
                return

            wasp_result = ascol.wasp(wheel_a_pos)
            wagp_result = ascol.wagp()

            res = ascol.wait_for_result(ascol.wars, expected_result=wait_for_state)
        return res

    def move_wheel_b_and_wait(self, wheel_b_filter: str, wait_for_state="stopped"):
        """
        Move FASU B wheel to provided filter, and wait until FASU A state is 'stopped'

        Args:
            wheel_b_filter:
                the NAME of the filter eg. 'U', 'B', 'V', 'R', 'I', 'empty',
                NOT ascol pos (eg '01', '02', '03')
                Raises KeyError if unknown filter (as defined in ``ascol.ascol_constants.WBRP_CODES``)
            wait_for_state (str or tuple of str, default: "stopped"):
                Wait for ``ascol.wbrs`` (Wheel B Read State) to be one of these state(s).

        Returns:
            res:
                The result of ``ascol.wbrs`` when it matches one of ``wait_for_state``.

        """

        wheel_b_pos = FASU_B_POS_LOOKUP.get(wheel_b_filter, None)

        if wheel_b_pos is None:
            msg = (
                f"unknown FASU B filter '{wheel_b_filter}'\n"
                f"    known: {FASU_B_POS_LOOKUP.keys()}"
            )
            raise KeyError(msg)

        with Ascol(test_mode=self.test_mode) as ascol:
            wheel_b_curr = ascol.wbrp()
            wheel_b_state = ascol.wbrs()
            if wheel_b_pos == wheel_b_curr:
                logger.info(f"FASU B already at {wheel_b_filter}")
                return

            wasp_result = ascol.wbsp(wheel_b_pos)
            wagp_result = ascol.wbgp()

            ascol.wait_for_result(ascol.wbrs, expected_result=wait_for_state)
        return

    def move_dfosc_grism_and_wait(
        self,
        dfosc_grism: str,
    ):
        """
        Move DFOSC grism wheel to the requested grism.
        Wait for

        Args:
            dfosc_grism : str
                The grism number (eg. '2')



        """

        if not isinstance(dfosc_grism, str):
            msg = f"please provide dfosc_grism {dfosc_grism} as 'str', not '{type(dfosc_grism)}."
            logger.warning(msg)
            dfosc_grism = str(dfosc_grism)

        dfosc_g_pos = DFOSC_GRISM_LOOKUP.get(dfosc_grism, None)

        if dfosc_g_pos is None:
            msg = (
                f"unknown DFOSC GRISM '{dfosc_grism}'\n"
                f"    known: {DFOSC_GRISM_LOOKUP.keys()}"
            )
            raise KeyError(msg)

        with Dfosc(test_mode=self.test_mode) as dfosc:
            dfosc.grism_goto(dfosc_g_pos)
        return

    def move_dfosc_slit_and_wait(self, dfosc_slit: str, wait_for_state="y"):
        dfosc_s_pos = DFOSC_SLIT_LOOKUP.get(dfosc_slit, None)

        if dfosc_s_pos is None:
            msg = (
                f"unknown DFOSC SLIT '{dfosc_slit}'\n"
                f"    known: {DFOSC_SLIT_LOOKUP.keys()}"
            )
            raise KeyError(msg)

        with Dfosc(test_mode=self.test_mode) as dfosc:
            dfosc.aperture_goto(dfosc_s_pos)
        return

    def move_dfosc_filter_and_wait(self, dfosc_filter: str, wait_for_state="y"):
        dfosc_f_pos = DFOSC_FILTER_LOOKUP.get(dfosc_filter, None)

        if dfosc_f_pos is None:
            msg = (
                f"unknown DFOSC FILTER '{dfosc_filter}'\n"
                f"    known: {DFOSC_FILTER_LOOKUP.keys()}"
            )
            raise KeyError(msg)

        with Dfosc(test_mode=self.test_mode) as dfosc:
            dfosc.filter_goto(dfosc_f_pos)
        return

    def take_science_frame(
        self,
        exposure_time: float,
        filename: str,
        object_name: str,
        read_wait=30.0,
    ):
        """
        Take a single science frame.
        First, Ascol.shop("1") [SHutter OPen/close] is called to ensure shutter is open.
        Then,

        Args:
            exposure_time (float):
                The exposure time for CCD3, in seconds.
            filename (str):
                The filename to store the resulting output.
                The file is likely stored in lin1:/data/YYYYMMDD/<filename>
            object_name (str):
                Stored in the FITS header under OBJECT
            read_wait (float):
                The amount of extra time to wait (after exposure_time sec),
                before return.

        """
        exp_params = {}
        exp_params["CCD3.exposure"] = str(exposure_time)
        exp_params["CCD3.IMAGETYP"] = "SCIENCE"
        exp_params["CCD3.OBJECT"] = object_name

        # TODO: switch lamps off

        with Ascol(test_mode=self.test_mode) as ascol:
            FASU_A = ascol.warp()
            FASU_B = ascol.wbrp()
            shop_result = ascol.shop("1")
            shutter_pos = ascol.shrp()
            logger.info(f"shutter is {shutter_pos}")

        exp_params["WASA.filter"] = FASU_A
        exp_params["WASB.filter"] = FASU_B

        with Ccd3(test_mode=self.test_mode) as ccd3:
            ccd3.set_exposure_parameters(exp_params)
            ccd3.start_exposure(str(filename))

            if not self.test_mode:
                logger.info(f"wait {exposure_time}+1 sec for exposure")
                time.sleep(exposure_time + 1.0)
                ccd_status = ccd3.get_ccd_state()
                logger.info("CCD state: ccd_status")
                logger.info(f"wait {read_wait} sec for read")
                time.sleep(read_wait)
            else:
                logger.info("skip exp/read wait in test mode...")

    def take_science_multi_frames(
        self, exposure_time: float, object_name: str, n_exp: int, read_wait=30.0
    ):
        """
        Repeatedly call take_science_frame().
        (take_science_frame() ensures shutter open, and records FASU A and B position in fits.)
        Filenames will be named sequentially using object_name.

        eg. for n_exp=3, object_name="M101", files are
        "M101_001.fits", "M101_002.fits", "M101_003.fits"

        Example:
            >>> exptime = 30.0
            >>> n_exp = 3
            >>> object_name = "M83"
            >>> with DK154() as dk154:
            ...     dk154.take_science_multi_frame(exptime, object_name, n_exp)


        Args:
            exposure_time:


        """

        for ii in range(1, n_exp + 1):
            filename = f"{object_name}_{ii:03d}.fits"
            self.take_science_exposure(
                exposure_time, filename, object_name, read_wait=read_wait
            )

    def take_dark_frames(
        self, exposure_time: float, n_exp: int, dark_name=None, read_wait=30.0
    ):
        """
        Take dark frames.
        First calls Ascol.shop("0") to ensure shutter is closed.

        files are named "<dark_name>_001.fits", "<dark_name>_002.fits",
        and are likely stored in lin1:/data/YYMMDD/

        Args:
            exposure_time (float):
                sec
            n_exp:
                Number of dark frames to take.
            dark_name (str, optional):
                If not provided, defaults to "dark_<date>UT", <date>=yymmdd_HHMMSS
                (<date> is set at time of function call, so is fixed for all n_exp frames)



        """

        if dark_name is None:
            t_now = Time.now()
            t_str = t_now.strftime("%y%m%d_%H%M%S")
            logger.info(f"dark_name defaults to {t_str}")

        exp_params = {}
        exp_params["CCD3.exposure"] = str(exposure_time)
        exp_params["CCD3.IMAGETYP"] = "DARK"
        exp_params["CCD3.OBJECT"] = "DARK"

        with Ascol(test_mode=self.test_mode) as ascol:
            ascol.shop("0")
            shutter_pos = ascol.shrp()
            logger.info(f"shutter is {shutter_pos}")

        with Ccd3(test_mode=self.test_mode) as ccd3:
            for ii in range(1, n_exp + 1):
                filename = f"{dark_name}_{ii:03d}.fits"
                ccd3.set_exposure_parameters(exp_params)

                ccd3.start_exposure(str(filename))

                if not self.test_mode:
                    logger.info(f"wait {exposure_time}+1 sec for exposure")
                    time.sleep(exposure_time + 1.0)
                    ccd_status = ccd3.get_ccd_state()
                    logger.info("CCD state: ccd_status")
                    logger.info(f"wait {read_wait} sec for read")
                    time.sleep(read_wait)
                else:
                    logger.info("skip exp/read wait in test mode...")

        raise NotImplementedError

    def switch_lamps_on(self):
        raise NotImplementedError
