"""
Python wrapper for low-level TCP-IP communication.

Based on ASCOL protocol: from doc v1.1.0 (20-07-2014)

24-11-23
"""

import datetime
import time
import socket
from logging import getLogger


from dk154_control.tcs import ascol_constants

logger = getLogger(__name__.split(".")[-1])


class AscolInputError(Exception):
    pass


class Ascol:
    """
    ASCOL implemented as in the documentation v1.1.0 (20-07-2014)

    For ASCOL commands, any inputs are **always** accepted as strings.
    Some are accepted as integers, strings are better...
    """

    INTERNAL_HOST = "192.168.132.11"  # The remote host, internal IP of the TCS
    EXTERNAL_HOST = "134.171.81.74"  # The remote host, external IP of the TCS
    LOCAL_HOST = "127.0.0.1"
    ASCOL_PORT = (
        2003  # Same port used by the server, ports avail 2001-2009, 2007 is occupied
    )
    LOCAL_PORT = 8888  # Alt-HTTP port -- safe to use?
    GLOBAL_PASSWORD = "1178"

    def __init__(
        self,
        external: bool = False,
        test_mode: bool = False,
        debug: bool = False,
        delay: float = None,
    ):
        logger.info("initialise Ascol")
        self.external = external
        if self.external:
            self.HOST = self.EXTERNAL_HOST
        else:
            self.HOST = self.INTERNAL_HOST
        self.PORT = self.ASCOL_PORT

        self.test_mode = test_mode
        if self.test_mode:
            self.HOST = self.LOCAL_HOST
            self.PORT = self.LOCAL_PORT
            logger.info(f"starting in TEST MODE (use localhost:{self.PORT})")

        self.debug = debug  # TODO: change debug mode so that the LOGGER is changed!

        self.init_time = datetime.datetime.now()
        self.delay = delay

        self.connect_socket()

    def connect_socket(self):
        logger.info("socket connect")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.HOST, self.PORT))
        self.conn_timestamp = time.time()
        time.sleep(1.0)

        self.sock = sock  # Don't name it 'socket' else overload module...

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()
        logger.info("ASCOL connection closed in __exit__")

    def get_data(self, command: str) -> tuple:
        """
        The actual sending/recieving of TCP IP commands.

        Returns a tuple (can be one element long)
        """

        print_command = command
        if "GLLG" in command:
            print_command = "GLLG <passwd>"  # Don't print the actual pwd to logs!

        logger.info(f"send to ASCOL: {print_command}")

        send_command = (command + "\n").encode("utf-8")

        time.sleep(0.1)  # Sensible to wait a little?

        try:
            self.sock.sendall(send_command)  # Send the command to the TCS computer
            if self.debug:
                logger.info("successful sending")
        except OSError as e:
            logger.info("try reconnecting socket...")
            self.connect_socket()
            self.sock.sendall(send_command)
            if self.debug:
                logger.info("successful sending after reconnect")

        data = self.sock.recv(1024)  # Ask for the result, up to 1024 char long.
        data = data.decode("ascii")  # Decode from binary string
        data = data.rstrip()  # Strip some unimportant newlines
        data = tuple(data.split())  # Immutable 'tuple' better than 'list'.

        if self.debug:
            logger.info(
                f"data received from server {self.HOST}:{self.PORT}\n    {data}"
            )

        if self.delay is not None:
            time.sleep(self.delay)

        if len(data) == 1 and data[0] == "ERR":
            command_code = command.split()[0]
            logger.warning(f"Result is ERR. Is {command_code} a 'set' command?")
            logger.warning(f"You might have forgotten to send the password: use gllg()")

        return data

    def wait_for_result(self, func, exp_result, delay=2.0, timeout=180.0):
        """
        Run a command repeatedly (with delay) until the expected result is returned.

        # This function is experimental!

        Parameters
        ----------
        func
            The (ASCOL) function to run many times.
        exp_result
            The expected result (eg. "sky track")
        delay
            sleep time between repeats [float: sec]
        timeout
            give up after this many seconds [float: sec]

        eg.
        >>> res = ascol.wait_for_result(ascol.ters, "sky track") #  Note no () after ters!!
        >>> print(res)
        "sky track"
        """
        t_start = time.time()
        while time.time() - t_start < timeout:
            result = func()
            if result == exp_result:
                break
            time.sleep(delay)
        return result

    def glre(self):
        """
        GLobal read REmote state [Not defined in ASCOL doc]

        Returns human-readable string
        """
        command = f"GLRE"
        result_code, *dummy_values = self.get_data(command)
        return ascol_constants.GLRE_CODES[result_code]

    def glsr(self):
        """
        GLobal read Safety Relay state [Not defined in ASCOL doc]

        Returns human-readable string
        """
        command = f"GLSR"
        result_code, *dummy_values = self.get_data(command)
        return ascol_constants.GLSR_CODES[result_code]

    def gllg(self, password=None):
        """
        GLobal LoGin [ASCOL 2.2]

        Returns 0 (wrong pwd) 1 (correct)
        """
        password = password or self.GLOBAL_PASSWORD

        command = f"GLLG {password}"
        result_code, *dummy_values = self.get_data(command)
        password_result = ascol_constants.GLLG_CODES[result_code]
        return password_result

    def glll(self):
        """
        GLobal read Latitude and Longitude [ASCOL 2.3]

        Returns lat [str: hhmmdd.dd], lon [str: ]
        """
        lat, lon = self.get_data("GLLL")
        return lat, lon

    def glut(self):
        """
        GLobal read UTC [ASCOL 2.4]

        Returns date [int: MJD], time [str: hhmmss.sss]
        """
        mjd, time_str, *dummy_values = self.get_data("GLUT")
        return int(mjd), time_str

    def glsd(self):
        """
        GLobal read SiDereal time [ASCOL 2.5]

        Returns time [str: hhmmss.ss]
        """
        time_str, *dummy_values = self.get_data("GLSD")
        return time_str

    def gldp(self):
        """
        GLobal DePartment [ASCOL 2.6]

        Returns department (human-readable string)
        """
        result_code, *dummy_values = self.get_data("GLDP")
        return ascol_constants.GLDP_CODES.get(
            result_code, f"Unknown dept {result_code}"
        )

    def teon(self, on_off: str):
        """
        Telescope ON/off [ASCOL 2.10]

        Parameters
        ----------
        on_off [1 - on, 0 - off]

        Returns "1" (ok) or ERR
        """

        on_off = str(on_off)
        if on_off not in ["1", "0"]:
            errstr = "teon: use input '1' for on, '0' for off"
            raise AscolInputError(errstr)

        command = f"TEON {on_off}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def test(self):
        """
        TElescope STop [ASCOL 2.11]

        Returns "1" (ok) or ERR
        """
        self.gllg()
        return self.get_data("TEST")

    def tefl(self):
        """
        TElescope FLip [ASCOL 2.13]

        Returns "1" (ok) or ERR
        """
        self.gllg()
        return self.get_data("TEFL")

    def tepa(self):
        """
        Telescope PArk [ASCOL 2.14]

        Returns "1" (ok) or ERR
        """
        self.gllg()  # Set commands require global password
        return self.get_data("TEPA")

    def tein(self):
        """
        TElescope INitialization [ASCOL 2.15]

        Returns "1" (ok) or ERR
        """
        self.gllg()
        return self.get_data("TEIN")

    def tsra(self, ra: str, dec: str, position: str):
        """
        Telescope Set Right Ascension and declination [ASCOL 2.17]

        Parameters
        ----------
        ra [str: hhmmss.s]
        dec [str: ddmmss.s]
        position [str: 0 - east, 1 - west]

        Returns "1" (ok) or ERR
        """
        self.gllg()  # Set commands require global password
        command = f"TSRA {ra} {dec} {position}"

        result_code, *dummy_values = self.get_data(command)
        return result_code

    def tgra(self):
        """
        Telescope Go Right Ascension and declination [ASCOL 2.19]

        Returns 1 (ok) or ERR
        """
        self.gllg()  # Set commands require global password
        result_code, *dummy_values = self.get_data("TGRA")
        return result_code

    def trrd(self):
        """
        Telescope Read Right ascension and Declination [ASCOL 2.41]

        Returns RA [str: hhmmss.s], Dec [str: +ddmmss.s], position [str: east/west].
        """
        ra, dec, position_code, *dummy_values = self.get_data("TRRD")
        return ra, dec, ascol_constants.TRRD_POSITION_CODES[position_code]

    def ters(self):
        """
        TElescope Read State. [ASCOL 2.43]

        Returns human-readable string.
        """
        result_code, *dummy_values = self.get_data("TERS")
        return ascol_constants.TERS_CODES[result_code]

    def dosa(self, dome_pos):
        """
        DOme Set Absolute position [ASCOL 2.44]

        Parameters
        ----------
        dome_pos [ddd.dd: str] (eg. 0.00-359.99)

        Returns "1" (ok)
        """
        if isinstance(dome_pos, float):
            dome_pos = f"{dome_pos:.2f}"
        command = f"DOSA {dome_pos}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def doga(self):
        """
        DOme Go Absolute position [ASCOL 2.45]

        Returns "1" (ok) or ERR
        """
        result_code, *dummy_values = self.get_data("DOGA")
        return result_code

    def doam(self):
        """
        DOme AutoMated [ASCOL 2.46]

        Returns "1" (ok) or ERR
        """
        self.gllg()
        result_code, *dummy_values = self.get_data("DOAM")
        return result_code

    def dopa(self):
        """
        DOme PArk [ASCOL 2.47]

        Returns "1" (ok) or ERR
        """
        self.gllg()
        result_code, *dummy_values = self.get_data("DOPA")
        return result_code

    def doin(self):
        """
        DOme INitialization [ASCOL 2.48]

        Returns "1" (ok) or ERR
        """
        self.gllg()
        result_code, *dummy_values = self.get_data("DOIN")
        return result_code

    def doso(self, open_close):
        """
        DOme Slit Open/close [ASCOL 2.50]

        Parameters
        ----------
        open_close [1 - open, 0 - close]

        Returns "1" (ok) or ERR
        """
        self.gllg()
        command = f"DOSO {open_close}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def dost(self):
        """
        DOme STop

        Returns 1 (ok) or ERR
        """
        self.gllg()
        result_code, *dummy_values = self.get_data("DOST")
        return result_code

    def dors(self):
        """
        DOme Read State [ASCOL 2.56]

        Returns human-readable string
        """
        return_code, *dummy_values = self.get_data("DORS")
        return ascol_constants.DORS_CODES[return_code]

    def fcop(self, open_close: str):
        """
        Flap Cassegrain OPen/close [ASCOL 2.57]

        Parameters
        ----------
        open_close [1 - open, 0 - close]

        Returns 1 (ok) or ERR
        """
        open_close = str(open_close)
        if open_close not in ["1", "0"]:
            msg = "fcop: use input '1' for open, '0' for close"
            raise AscolInputError(msg)

        command = f"FCOP {open_close}"
        return_code, *dummy_values = self.get_data(command)
        return return_code

    def fcrs(self):
        """
        Flap Cassegrain Read State [ASCOL 2.59]

        Returns human-readable string
        """
        result_code, *dummy_values = self.get_data("FCRS")
        return ascol_constants.FCRS_CODES[result_code]

    def fmop(self, open_close: str):
        """
        Flap Mirror OPen/close [ASCOL 2.60]

        Parameters
        ----------
        open_close [1 - open, 0 - close]

        Returns 1 (ok) or ERR
        """
        open_close = str(open_close)
        if open_close not in ["1", "0"]:
            errstr = "fmop: use input '1' for open, '0' for close"
            raise AscolInputError(errstr)

        self.gllg()  # Set commands require global password
        command = f"FMOP {open_close}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def fmrs(self):
        """
        Flap Mirror Read State [ASCOL 2.62]

        Returns human-readable string
        """
        result_code, *dummy_values = self.get_data("FMRS")
        return ascol_constants.FMRS_CODES[result_code]

    def wasp(self, position: str):
        """
        Wheel A Set Position [ASCOL 2.63]

        Parameters
        ----------
        position [str: 0-7]

        Returns 1 (ok) or ERR
        """
        if int(position) not in range(8):  # range(8) incl. 0, excl, 8
            msg = f"Wheel A has positions 0-7; provided: {position}"
            logger.warning(msg)

        self.gllg()  # Set commands require global password
        command = f"WASP {position}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def wagp(self):
        """
        Wheel A Go Position [ASCOL 2.64]

        Returns 1 (ok) or ERR
        """
        self.gllg()  # Set commands require global password
        result_code, *dummy_values = self.get_data("WAGP")
        return result_code

    def warp(self):
        """
        Wheel A Read Position [ASCOL 2.66]

        Returns human-readable string
        """
        result_code, *dummy_values = self.get_data("WARP")
        return ascol_constants.WARP_CODES[result_code]

    def wars(self):
        """
        Wheel A Read State [ASCOL 2.68]

        Returns human-readable string
        """
        result_code, *dummy_values = self.get_data("WARS")
        return ascol_constants.WARS_CODES[result_code]

    def wbsp(self, position):
        """
        Wheel B Set Position [ASCOL 2.69]

        Parameters
        ----------
        position [str: 0-6]

        Returns 1 (ok) or ERR
        """
        if int(position) not in range(7):  # range(7) incl. 0, excl. 7
            msg = f"Wheel B has positions 0-6; provided: {position}"
            logger.warning(msg)

        self.gllg()  # Set commands require global login
        command = f"WBSP {position}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def wbgp(self):
        """
        Wheel B Go Position [ASCOL 2.70]

        Returns 1 (ok) or ERR
        """
        self.gllg()  # Set commands require global login
        result_code, *dummy_values = self.get_data("WBGP")
        return result_code

    def wbrp(self):
        """
        Wheel B Read Position [ASCOL 2.72]

        Returns human-readable string
        """
        result_code, *dummy_values = self.get_data("WBRP")
        return ascol_constants.WBRP_CODES[result_code]

    def wbrs(self):
        """
        Wheel B Read State [ASCOL 2.74]

        Returns human-readable string
        """
        result_code, *dummy_values = self.get_data("WBRS")
        return ascol_constants.WBRS_CODES[result_code]

    def fora(self):
        """
        FOcus Read Absolute position [ASCOL 2.82]

        Returns focus_pos [float: mm]
        """

        focus_pos, *dummy_values = self.get_data("FORA")
        return float(focus_pos)

    def fors(self):
        """
        FOcus Read State [ASCOL 2.87]

        Returns human-readable string
        """
        result_code, *dummy_values = self.get_data("FORS")
        return ascol_constants.FORS_CODES[result_code]

    def shop(self, open_close):
        """
        SHutter OPen/close [ASCOL 2.134]

        Parameters
        ----------
        open_close [1 - open, 0 - close]

        Returns "1" (ok) or ERR
        """
        open_close = str(open_close)
        if open_close not in ["1", "0"]:
            errstr = "shop: use input '1' for open, '0' for close"
            raise AscolInputError(errstr)
        command = f"SHOP {open_close}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def shrp(self):
        """
        SHutter Read Position [ASCOL 2.135]

        Returns human-readable string
        """
        result_code, *dummy_values = self.get_data("SHRP")
        return ascol_constants.SHRP_CODES[result_code]

    def mebe(self):
        """
        MEteo Brightness East [ASCOL 2.136]

        Returns brightness [float: kLux], validity [str]
        """
        command = f"MEBE"
        brightness, validity_code, *dummy_values = self.get_data(command)
        return float(brightness), ascol_constants.MEBE_VALIDITY_CODES[validity_code]

    def mebn(self):
        """
        MEteo Brightness North [ASCOL 2.137]

        Returns brightness [float: kLux], validity [str]
        """
        brightness, validity_code, *dummy_values = self.get_data("MEBN")
        return float(brightness), ascol_constants.MEBN_VALIDITY_CODES[validity_code]

    def mebw(self):
        """
        MEteo Brightness West [ASCOL 2.138]

        Returns brightness [float: kLux], validity [str]
        """
        brightness, validity_code, *dummy_values = self.get_data("MEBW")
        return float(brightness), ascol_constants.MEBW_VALIDITY_CODES[validity_code]

    def metw(self):
        """
        MEteo TWilight [ASCOL 2.139]

        Returns twilight [float: Lux], validity [str]
        """
        brightness, validity_code, *dummy_values = self.get_data("METW")
        return float(brightness), ascol_constants.METW_VALIDITY_CODES[validity_code]

    def mehu(self):
        """
        MEteo HUmidity [ASCOL 2.140]

        Returns Humidity [float: percentage], validity [str]
        """
        humidity, validity_code, *dummy_values = self.get_data("MEHU")
        return float(humidity), ascol_constants.MEHU_VALIDITY_CODES[validity_code]

    def mete(self):
        """
        MEteo TEmperature [ASCOL 2.141]

        Returns temperature [float: celcius], validity [str]
        """
        temperature, validity_code, *dummy_values = self.get_data("METE")
        return float(temperature), ascol_constants.METE_VALIDITY_CODES[validity_code]

    def mews(self):
        """
        MEteo Wind Speed [ASCOL 2.142]

        Returns wind_speed [float: m/s], validity [str]
        """
        wind_speed, validity_code, *dummy_values = self.get_data("MEWS")
        return float(wind_speed), ascol_constants.MEWS_VALIDITY_CODES[validity_code]

    def mepr(self):
        """
        MEteo PRecipitation [ASCOL 2.143]

        Returns precipitiation [str: yes/no], validity [str]
        """
        precip_code, validity_code, *dummy_values = self.get_data("MEPR")
        return (
            ascol_constants.MEPR_CODES[precip_code],
            ascol_constants.MEPR_VALIDITY_CODES[validity_code],
        )

    def meap(self):
        """
        MEteo Atmospheric Pressure [ASCOL 2.144]

        Returns atmospheric_pressure [float: mbar], validity [str]
        """
        pressure, validity_code, *dummy_values = self.get_data("MEAP")
        return float(pressure), ascol_constants.MEPR_VALIDITY_CODES[validity_code]

    def mepy(self):
        """
        MEteo PYrgeometer [ASCOL 2.145]

        Returns irradience [float: W/m2], validity [str]
        """
        irradience, validity_code, *dummy_values = self.get_data("MEPY")
        return float(irradience), ascol_constants.MEPY_VALIDITY_CODES[validity_code]

    def doss(self):
        """
        DOme read Slit State [Not defined in ASCOL document]

        Returns human-readable string
        """
        result_code, *dummy_values = self.get_data("DOSS")
        return ascol_constants.DOSS_CODES[result_code]

    def dola(self):
        """
        DOme read LAmp state [Not defined in ASCOL document]

        Returns human-readable string
        """
        result_code, *dummy_values = self.get_data("DOLA")
        return ascol_constants.DOLA_CODES[result_code]

    def vnos(self):
        """
        Vent NOrth read State [Not defined in ASCOL document]

        Returns human-readable string
        """
        vnos_code, *dummy_values = self.get_data("VNOS")
        return ascol_constants.VNOS_CODES.get(vnos_code, f"Unknown code {vnos_code}")

    def vnes(self):
        """
        Vent NorthEast read State [Not defined in ASCOL document]

        Returns human-readable string
        """
        vnes_code, *dummy_values = self.get_data("VNES")
        return ascol_constants.VNES_CODES.get(vnes_code, f"Unknown code {vnes_code}")

    def veas(self):
        """
        Vent EAst read State [Not defined in ASCOL document]

        Returns human-readable string
        """
        veas_code, *dummy_values = self.get_data("VEAS")
        return ascol_constants.VNOS_CODES.get(veas_code, f"Unknown code {veas_code}")

    def vses(self):
        """
        Vent SouthEast read State [Not defined in ASCOL document]

        Returns human-readable string
        """
        vses_code, *dummy_values = self.get_data("VSES")
        return ascol_constants.VSES_CODES.get(vses_code, f"Unknown code {vses_code}")

    def vsos(self):
        """
        Vent SOuth read State [Not defined in ASCOL document]

        Returns human-readable string
        """
        vsos_code, *dummy_values = self.get_data("VSOS")
        return ascol_constants.VSOS_CODES.get(vsos_code, f"Unknown code {vsos_code}")

    def vsws(self):
        """
        Vent SouthWest read State [Not defined in ASCOL document]

        Returns human-readable string
        """
        vsws_code, *dummy_values = self.get_data("VSWS")
        return ascol_constants.VNOS_CODES.get(vsws_code, f"Unknown code {vsws_code}")

    def vwes(self):
        """
        Vent WEst read State [Not defined in ASCOL document]

        Returns human-readable string
        """
        vwes_code, *dummy_values = self.get_data("VWES")
        return ascol_constants.VWES_CODES.get(vwes_code, f"Unknown code {vwes_code}")

    def vnws(self):
        """
        Vent NorthWest read State [Not defined in ASCOL document]

        Returns human-readable string
        """
        vnws_code, *dummy_values = self.get_data("VNWS")
        return ascol_constants.VNWS_CODES.get(vnws_code, f"Unknown code {vnws_code}")

    def log_all_status(self):
        remote_state = self.glre()
        safety_relay_state = self.glsr()
        telescope_state = self.ters()
        dome_state = self.dors()
        dome_slit_state = self.doss()
        flap_cassegrain_state = self.fcrs()
        flap_mirror_state = self.fmrs()
        curr_ra, curr_dec, curr_pos = self.trrd()
        shutter_pos = self.shrp()
        wheel_a_position = self.warp()
        wheel_b_position = self.wbrp()

        status_str = (
            f"Telescope status:\n"
            f"    remote/local [GLRE]: {remote_state}\n"
            f"    safety relay [GLSR]: {safety_relay_state}\n"
            f"    tel. state [TERS]  : {telescope_state}\n"
            f"    dome state [DORS]  : {dome_state}\n"
            f"    domeslit ste [DOSS]: {dome_slit_state}\n"
            f"    casseg. flap [FCRS]: {flap_cassegrain_state}\n"
            f"    mirror flap [FMRS] : {flap_mirror_state}\n"
            f"    RA/Dec (pos) [TRRD]: {curr_ra}, {curr_dec} ({curr_pos})\n"
            f"    shutter pos [SHRP] : {shutter_pos}\n"
            f"    wheel A pos. [WARP]: {wheel_a_position}\n"
            f"    wheel B pos. [WBRP]: {wheel_b_position}\n"
        )
        logger.info(f"{status_str}")
        return
