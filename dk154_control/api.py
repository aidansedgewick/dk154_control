import time
from logging import getLogger

from astropy.coordinates import SkyCoord

from dk154_control.camera.ccd3 import Ccd3
from dk154_control.tcs.ascol import Ascol
from dk154_control.tcs import ascol_constants

logger = getLogger(__file__.split("/")[-1])


class Dk154Api:
    """
    User-friendly interface for common operations with the telescope.
    """

    def __init__(self, external=False, test_mode=False, debug=False):
        logger.info("init Tcs object")

        self.ascol = Ascol(external=external, test_mode=test_mode, debug=debug)
        self.ccd3 = Ccd3(external=external, test_mode=test_mode, debug=debug)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Correctly close connections.
        """

        logger.info("Tcs exit")
        self.ascol.sock.close()
        logger.info("ascol socket closed")

    def telescope_check_status(self):
        """
        Current status of various telescope parameters
        """
        remote_state = self.ascol.glre()
        safety_relay_state = self.ascol.glsr()
        telescope_state = self.ascol.ters()
        dome_state = self.ascol.dors()
        flap_cassegrain_state = self.ascol.fcrs()
        flap_mirror_state = self.ascol.fmrs()
        curr_ra, curr_dec, curr_pos = self.ascol.trrd()
        wheel_a_position = self.ascol.warp()
        wheel_b_position = self.ascol.wbrp()

        status_str = (
            "Telescope status:\n"
            f"    RA/Dec (pos) [TRRD]: {curr_ra}, {curr_dec} ({curr_pos})\n",
            f"    remote/local [GLRE]: {remote_state}\n"
            f"    safety relay [GLSR]: {safety_relay_state}\n"
            f"    tel. state [TERS]  : {telescope_state}\n"
            f"    dome state [DORS]  : {dome_state}\n"
            f"    casseg. flap [FCRS]: {flap_cassegrain_state}\n"
            f"    mirror flap [FMRS] : {flap_mirror_state}\n"
            f"    RA/Dec (pos) [TRRD]: {curr_ra}, {curr_dec} ({curr_pos})\n",
            f"    wheel A pos. [WARP]: {wheel_a_position}\n"
            f"    wheel B pos. [WBRP]: {wheel_b_position}\n",
        )
        logger.info(status_str)
        return

    def meteo_status(self):
        twilight, tw_valid = self.ascol.metw()  # Lux
        # brightness_east, be_valid = self.ascol.mebe()  # kLux
        # brightness_north, bn_valid = self.ascol.mebn()  # kLux
        # brightness_west, bw_valid = self.ascol.mebn()  # kLux
        humidity, hu_valid = self.ascol.mehu()  # percent
        temp, te_valid = self.ascol.mete()  # C
        wind_speed, wi_valid = self.ascol.mews()  # m/s
        precip, pr_valid = self.ascol.mepr()  # y/n
        atm_pressure, ap_valid = self.ascol.meap()  # mbar
        irradience, ir_valid = self.ascol.mepy()  # W/m2

        status_str = (
            "Meteorology status:\n"
            f"    twilight [METW]  : {twilight:.2f} Lux [{tw_valid}]\n"
            f"    humidity [MEHU]  : {humidity:03d} \% [{hu_valid}]\n"
            f"    temperat. [METE] : {temp:.1f} C [{te_valid}]\n"
            f"    wind speed [MEWS]: {wind_speed:.1f} m/s [{wi_valid}]\n"
            f"    precip. [MEPR]   : {precip} [{pr_valid}]\n"
            f"    atm. pres. [MEAP]: {atm_pressure:.2f} mbar [{ap_valid}]\n"
            f"    irradience [MEPY]: {irradience:.2f} W/m2 [{ir_valid}]\n"
        )
        logger.info(status_str)
        return

    def telescope_goto(self, coord: SkyCoord, pos: str):
        """
        Convenience function, which formats `astropy.coordinates.SkyCoord` for Ascol.
        Formatted string is passed to ascol.tsra(), then calls tgra()

        Parameters
        ----------
        coord [astropy.coordinates.SkyCoord]
            The coordinate to point the telecope to.
            This will be formatted as hhmmss.s +ddmmss.s, for ascol.tsra
        pos [str]
            The "0" - "east", "1"=="west"

        """

        ra_hms = coord.ra.hms
        ra_str = f"{int(ra_hms.h):02d}{int(ra_hms.m):02d}{ra_hms.s:.1f}"

        dec_dms = coord.dec.dms
        dec_str = f"{int(dec_dms.d):+02d}{int(dec_dms.m)}{dec_dms.s:.1f}"
        # TODO: check this with positive and negative Dec values. Does ASCOL
        # take signed or unsigned string of float? If unsigned, how does -ve dec work?

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
        tsra_result = self.ascol.tsra(ra_str, dec_str, pos_code)

        self.ascol.tgra()

        time.sleep(1.0)
