"""
Python wrapper for low-level TCP-IP communication.

Based on ASCOL protocol.

24-11-23
"""


import datetime
import socket
from logging import getLogger


from dk154_control.tcs import ascol_constants

logger = getLogger(__file__.split("/")[-1])


class AscolInputError(Exception):
    pass


class Ascol:
    """
    ASCOL implemented as in the documentation

    For ASCOL commands, any inputs are **always** accepted as strings.
    Some are accepted as integers, strings are better...
    """

    INTERNAL_HOST = "192.168.132.11"  # The remote host, internal IP of the TCS
    EXTERNAL_HOST = "134.171.81.74"  # The remote host, external IP of the TCS
    PORT = 2003  # Same port used by the server, ports avail 2001-2009, 2007 is occupied
    GLOBAL_PASSWORD = "1178"

    def __init__(self, internal=True, dry_run=False):
        if internal:
            self.HOST = self.INTERNAL_HOST
        else:
            self.HOST = self.EXTERNAL_HOST

        self.dry_run = dry_run

        self.init_time = datetime.datetime.now()

        logger.info("initialise Ascol")
        if not self.dry_run:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.HOST, self.PORT))
        else:
            sock = None

        self.sock = sock  # Don't name it 'socket' else overload module...

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()
        logger.info("ASCOL connection closed in __exit__")

    def get_data(self, command: str):
        """
        The actual sending/recieving of TCP IP commands.

        returns a LIST (can be one element long)
        """

        command_code = command.split()[0]
        print_command = command
        if "GLLG" in command:
            print_command = "GLLG <pwd>"

        if self.dry_run:
            print_command = print_command + " [dry run mode]"

        logger.info(f"send: {print_command}")
        if self.dry_run:
            return

        send_command = (command + "\n").encode("utf-8")
        self.sock.sendall(send_command)  # Send the command to the TCS computer

        data = self.sock.recv(1024)  # Ask for the result, up to 1024 char long.
        data = data.decode("ascii")  # Decode from binary string
        data = data.rstrip()  # Strip some unimportant newlines
        data = data.split()

        if len(data) == 1 and data[0] == "ERR":
            logger.warning(f"Result is ERR. Is {command_code} a 'set' command?")
            logger.warning(
                f"You might have forgotten to send the password: use self.gllg()"
            )

        return data

    def glre(self):
        """
        GLobal read REmote state

        Not defined in ASCOL document

        Returns human-readable string
        """
        command = f"GLRE"
        (result_code,) = self.get_data(command)  # Unpack single element list.
        return ascol_constants.GLRE_CODES[result_code]

    def glsr(self):
        """
        GLobal read REmote state

        Not defined in ASCOL document

        returns human-readable string
        """
        command = f"GLSR"
        (result_code,) = self.get_data(command)  # Unpack single element list.
        return ascol_constants.GLSR_CODES[result_code]

    def gllg(self, password=None):
        """
        GLobal LoGin

        ASCOL 2.2

        returns 0 (wrong pwd) 1 (correct)
        """
        password = password or self.GLOBAL_PASSWORD

        command = f"GLLG {password}"
        (result_code,) = self.get_data(command)
        password_result = ascol_constants.GLLG_CODES[result_code]
        return password_result

    def glll(self):
        """
        GLobal read Latitude and Longitude

        ASCOL 2.3

        returns lat/lon
        """
        lat, lon = self.get_data("GLLL")
        return lat, lon

    def teon(self, on_off: str):
        """
        Telescope ON/off

        ASCOL 2.10

        Parameters
        ----------
        on_off [1 - on, 0 - off]

        Returns 1 (ok) or ERR
        """

        on_off = str(on_off)
        if on_off not in ["1", "0"]:
            errstr = "teon: use input '1' for on, '0' for off"
            raise AscolInputError(errstr)

        command = f"TEON {on_off}"
        (return_code,) = self.get_data(command)
        return return_code

    def tsra(self, ra: str, dec: str, position: str):
        """
        Telescope Set Right ascension and declination

        ASCOL 2.17

        Parameters
        ----------
        ra [hhmmss.s]
        dec [ddmmss.s]
        position [0 - East, 1 - West]

        Returns 1 (ok) or ERR
        """
        self.gllg()  # Set commands require global password
        command = f"TSRA {ra} {dec} {position}"

        (return_code,) = self.get_data(command)
        return return_code

    def tgra(self):
        """
        Telescope Go Right Ascension and declination

        ASCOL 2.19

        Returns 1 (ok) or ERR
        """
        self.gllg()  # Set commands require global password
        return self.get_data("TGRA")

    def trrd(self):
        """
        Telescope Read Right ascension and Declination

        ASCOL 2.41

        Returns RA, Dec and human-readable position (east/west).
        """
        ra, dec, position_code = self.get_data("TRRD")
        return ra, dec, ascol_constants.TRRD_POSITION_CODES[position_code]

    def ters(self):
        """
        TElescope Read State.

        ASCOL 2.43

        Returns human-readable string.
        """
        return_code, dummy_value = self.get_data("TERS")
        return ascol_constants.TERS_CODES[return_code]

    def dors(self):
        """
        DOme Read State

        ASCOL 2.56

        Returns human-readable string
        """
        return_code, dummy_value = self.get_data("DORS")
        return ascol_constants.DORS_CODES[return_code]

    def fcop(self, open_close: str):
        """
        Flap Cassegrain OPen/close

        ASCOL 2.57

        Returns 1 (ok) or ERR
        """
        open_close = str(open_close)
        if open_close not in ["1", "0"]:
            msg = "fcop: use input '1' for open, '0' for close"
            raise AscolInputError(msg)

        command = f"FCOP {open_close}"
        (return_code,) = self.get_data(command)
        return return_code

    def fcrs(self):
        """
        Flap Cassegrain Read State

        ASCOL 2.59

        Returns human-readable string
        """
        command = f"FCRS"
        (return_code,) = self.get_data(command)
        return ascol_constants.FCRS_CODES[return_code]

    def fmop(self, open_close: str):
        """
        Flap Mirror OPen/close

        ASCOL 2.60

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
        (return_code,) = self.get_data(command)
        return return_code

    def fmrs(self):
        """
        Flap Mirror Read State

        ASCOL 2.62

        Returns human-readable string
        """
        command = f"FMRS"
        (return_code,) = self.get_data(command)  # Unpack single element list.
        return ascol_constants.FMRS_CODES[return_code]

    def wasp(self, position: str):
        """
        Wheel A Set Position

        ASCOL 2.63

        Parameters
        ----------
        position [string, 0-7]

        Returns 1 (ok) or ERR
        """
        if int(position) not in range(8):  # range(8) incl. 0, excl, 8
            msg = f"Wheel A has positions 0-7; provided: {position}"
            logger.warning(msg)

        self.gllg()  # Set commands require global password
        command = f"WASP {position}"
        (return_code,) = self.get_data(command)
        return return_code

    def wagp(self):
        """
        Wheel A Go Position

        ASCOL 2.64

        Returns 1 (ok) or ERR
        """
        self.gllg()  # Set commands require global password
        command = f"WAGP"
        (return_code,) = self.get_data(command)
        return return_code

    def warp(self):
        """
        Wheel A Read Position

        ASCOL 2.66

        Returns human-readable string
        """
        command = f"WARP"
        (return_code,) = self.get_data("WARP")
        return ascol_constants.WARP_CODES[return_code]

    def wars(self):
        """
        Wheel A Read State

        ASCOL 2.68

        Returns human-readable string
        """
        command = f"WARS"
        (return_code,) = self.get_data(command)
        return ascol_constants.WARS_CODES[return_code]

    def wbsp(self, position):
        """
        Wheel B Set Position

        ASCOL 2.69

        Parameters
        ----------
        position [string, 0-7]

        Returns 1 (ok) or ERR
        """
        if int(position) not in range(7):  # range(7) incl. 0, excl. 7
            msg = f"Wheel B has positions 0-6; provided: {position}"
            logger.warning(msg)

        self.gllg()  # Set commands require global login
        command = f"WBSP {position}"
        (return_code,) = self.get_data(command)
        return return_code

    def wbgp(self):
        """
        Wheel B Go Position

        ASCOL 2.70

        Returns 1 (ok) or ERR
        """
        self.gllg()  # Set commands require global login
        command = f"WBGP"
        (return_code,) = self.get_data(command)
        return return_code

    def wbrp(self):
        """
        Wheel B Read Position

        ASCOL 2.72

        Returns human-readable string
        """
        command = f"WBRP"
        (return_code,) = self.get_data(command)
        return ascol_constants.WBRP_CODES[return_code]

    def wbrs(self):
        """
        Wheel B Read State

        ASCOL 2.74

        Returns human-readable string
        """
        command = f"WBRS"
        (return_code,) = self.get_data(command)
        return ascol_constants.WBRS_CODES[return_code]

    def shrp(self):
        """
        SHutter Read Position

        ASCOL 2.135

        Returns human-readable string
        """
        command = f"SHRP"
        (return_code,) = self.get_data(command)
        return ascol_constants.SHRP_CODES[return_code]

    def mebe(self):
        """
        MEteo Brightness East

        ASCOL 2.136

        Returns brightness [float, kLux], validity [str]
        """
        command = f"MEBE"
        brightness, validity_code = self.get_data(command)
        return float(brightness), ascol_constants.MEBE_VALIDITY_CODES[validity_code]

    def mebn(self):
        """
        MEteo Brightness North

        ASCOL 2.137

        Returns brightness [float, kLux], validity [str]
        """
        command = f"MEBN"
        brightness, validity_code = self.get_data(command)
        return float(brightness), ascol_constants.MEBN_VALIDITY_CODES[validity_code]

    def mebw(self):
        """
        MEteo Brightness West

        ASCOL 2.138

        Returns brightness [float, kLux], validity [str]
        """
        command = f"MEBW"
        brightness, validity_code = self.get_data(command)
        return float(brightness), ascol_constants.MEBW_VALIDITY_CODES[validity_code]

    def metw(self):
        """
        MEteo TWilight

        ASCOL 2.139

        Returns twilight [float, Lux], validity [str]
        """
        command = f"METW"
        brightness, validity_code = self.get_data(command)
        return float(brightness), ascol_constants.METW_VALIDITY_CODES[validity_code]

    def mehu(self):
        """
        MEteo HUmidity

        ASCOL 2.140

        Returns Humidity [float, percentage], validity [str]
        """
        command = f"MEHU"
        humidity, validity_code = self.get_data(command)
        return float(humidity), ascol_constants.MEHU_VALIDITY_CODES[validity_code]

    def mete(self):
        """
        MEteo TEmperature

        ASCOL 2.141

        Returns temperature [float, celcius], validity [str]
        """
        command = f"METE"
        temperature, validity_code = self.get_data(command)
        return float(temperature), ascol_constants.METE_VALIDITY_CODES[validity_code]

    def mews(self):
        """
        MEteo Wind Speed [ASCOL 2.142]

        Returns wind_speed [float, m/s], validity [str]
        """
        command = f"MEWS"
        wind_speed, validity_code = self.get_data(command)
        return float(wind_speed), ascol_constants.MEWS_VALIDITY_CODES[validity_code]

    def mepr(self):
        """
        MEteo PRecipitation [ASCOL 2.143]

        Returns precipitiatin [float, m/s], validity [str]
        """
        command = f"MEPR"
        precip_code, validity_code = self.get_data(command)
        return (
            ascol_constants.MEPR_CODES[precip_code],
            ascol_constants.MEPR_VALIDITY_CODES[validity_code],
        )

    def meap(self):
        """
        MEteo Atmospheric Pressure

        ASCOL 2.144

        Returns atmospheric_pressure [float, mbar], validity [str]
        """
        command = f"MEAP"
        pressure, validity_code = self.get_data(command)
        return float(pressure), ascol_constants.MEPR_VALIDITY_CODES[validity_code]

    def mepy(self):
        """
        MEteo PYrgeometer

        ASCOL 2.145

        Returns irradience [float, W/m2], validity [str]
        """
        command = f"MEPY"
        irradience, validity_code = self.get_data(command)
        return float(irradience), ascol_constants.MEPY_VALIDITY_CODES[validity_code]

    def vnos(self):
        """
        Vent NOrth read State

        Not defined in ASCOL document

        Returns TODO
        """
        raise NotImplementedError()

    def vnes(self):
        """
        Vent NorthEast read State

        Not defined in ASCOL document

        Returns TODO
        """
        raise NotImplementedError()

    def veas(self):
        """
        Vent EAst read State

        Not defined in ASCOL document

        Returns TODO
        """
        raise NotImplementedError()

    def vses(self):
        """
        Vent SouthEast read State

        Not defined in ASCOL document

        Returns TODO
        """
        raise NotImplementedError()

    def vsos(self):
        """
        Vent SOuth read State

        Not defined in ASCOL document

        Returns TODO
        """
        raise NotImplementedError()

    def vsws(self):
        """
        Vent SouthWest read State

        Not defined in ASCOL document

        Returns TODO
        """
        raise NotImplementedError()

    def vwes(self):
        """
        Vent WEst read State

        Not defined in ASCOL document

        Returns TODO
        """
        raise NotImplementedError()

    def vnws(self):
        """
        Vent NorthWest read State

        Not defined in ASCOL document

        Returns TODO
        """
        raise NotImplementedError()
