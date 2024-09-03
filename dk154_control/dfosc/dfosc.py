"""
Python wrapper for low-level TCP-IP communication.

24-11-23

Controls for the aperture/slits, filter, and grism wheels for DFOSC.
Basic commands defined, and some additional start-up read-state commands for the various wheels.

NOTE: These are not yet tested on ALFOSC, so it is not guaranteed that they work.

TODO would it be easier to just have a library of grism, filter, and slit configurations at the beginning of this file?
"""

import time

# import socket
import telnetlib
import yaml
from logging import getLogger
from pathlib import Path

logger = getLogger(__name__.split(".")[-1])

"""
DFOSC commands for the MOXA
These are the commands that are sent directly to the MOXA (figure out the IP & port).
Includes aperture (slit), filter, and grism wheel commands.
"""
# TODO - get the IP and port number for the MOXA


def load_dfosc_setup(setup_path=None):
    setup_path = setup_path or Path(__file__).parent / "dfosc_setup.yaml"
    with open(setup_path, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def guess_wheel_pos(current_pos, wheel_setup):
    if len(wheel_setup) == 0:
        return "???", None
    likely_key, likely_val = min(
        wheel_setup.items(), key=lambda x: (abs(current_pos - x[1]) % 320000)
    )
    return likely_key, likely_val


class DfoscError(Exception):
    pass


class Dfosc:
    """
    Start a connection to the DFOSC MOXA to send commands to DFOSC.

    Args:
        external (bool): Not in use...
        test_mode (bool): For testing with mock servers in `dk154_mock` package

    """

    INTERNAL_HOST = "192.168.132.58"
    EXTERNAL_HOST = ""
    MOXA_PORT = 4001  # TODO: get port number
    LOCAL_HOST = "127.0.0.1"
    LOCAL_PORT = 8883  # Matches with MockDfoscServer

    def __init__(self, test_mode=False, debug=False, external=False):

        logger.info("initialise DFOSC grism wheel")
        if external:
            self.HOST = self.EXTERNAL_HOST
        else:
            self.HOST = self.INTERNAL_HOST
        self.PORT = self.MOXA_PORT

        self.test_mode = test_mode
        if self.test_mode:
            self.HOST = self.LOCAL_HOST
            self.PORT = self.LOCAL_PORT
            logger.info(f"starting in TEST MODE (use localhost:{self.PORT})")

        self.debug = debug

        self.init_time = time.time()

        try:
            self.dfosc_setup = load_dfosc_setup()
        except Exception as e:
            self.dfosc_setup = {"grism": {}, "slit": {}, "filter": {}}

        self.connect_telnet()

    def connect_telnet(self):
        logger.info("Dfosc telnet connect")
        self.tn = telnetlib.Telnet(self.HOST, self.PORT)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.tn.close()
        logger.info("DFOSC telnet closed in __exit__")

    def get_data(self, command: str):
        """
        The actual sending/recieving of commands with telnet.
        returns a LIST (can be one element long)

        NB:
        ===
        `telnetlib` module is deprecated with python 3.11.
        May be preferable to upgrade to SOCKET in future ?
        """
        command_code = command.split()[0]
        print_command = command
        logger.info(f"send: {print_command}")

        send_command = (command + "\n").encode()

        try:
            logger.info(f"try sending {send_command}...")
            print(self.tn)
            self.tn.write(send_command)
        except IOError as e:
            logger.info("try to reconnect telnet...")
            self.connect_telnet()
            self.tn.write(send_command)
            if self.debug:
                logger.info("successful send after reconnect.")

        TERMINATE_BYTES = "\n".encode("utf-8")  # telnet should return chars until THIS.
        data = self.tn.read_until(TERMINATE_BYTES)
        data = data.decode("utf-8")
        data = data.rstrip()
        data = data.split()

        logger.info(f"receive {data}")

        if len(data) == 1 and data[0] == "ERR":
            logger.warning(f"Result is ERR. Is {command_code} a 'set' command?")

        return tuple(data)

    def gi(self):
        """
        Grism Initialize position to hall switch and grism_zero offset.
        Only to be used after a power failure/cycle or if the grism has been moved manually.
        """
        command = f"GI"
        result_code, *dummy_values = self.get_data("GI")
        return result_code

    def gg(self, x: str):
        """
        Grism Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        command = f"GG{x}\n"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def gm(self, x: str):
        """
        Grism Move relative nnnnnn. '+' or '-' can be entered before nnnnnn
        """
        command = f"GM {x}\n"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def gp(self):
        """
        Grism Position, returns the current position value 'nnnnnn'
        """
        command = f"GP"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def gn(self, pos: str):
        """
        Goto one of the 8 positions (n*40000 steps), corresponds to centered aperture plate opening
        n is a number 1-8 or 0-7
        """
        if int(pos) not in range(8):  # range(8) incl. 0, excl, 8
            msg = f"Grism has positions 0-7; provided: {pos}"
            logger.warning(msg)

        command = f"G{pos}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def gq(self):
        """
        Grism Quit current operation. Must be called quickly after command is sent.
        """
        command = f"GQ"

        (return_code,) = self.get_data(command)
        return return_code

    def g(self):
        """
        Check driver ready. Returns 'y' if ready, 'n' if not ready.
        """
        command = f"g"
        return_code, *dummy_values = self.get_data(command)
        print(dummy_values)
        return return_code

    def gx(self):
        """
        Grism Goto hall initial position. Ressets aperture_zero to 0
        """
        (return_code,) = self.get_data("GX")
        return return_code

    def gidfoc(self):
        """
        Set zero position to current position. Records the aperture_zero value in eeprom.
        """
        (return_code,) = self.get_data("Gidfoc")
        return return_code

    def grism_init(self):
        """
        Grism wheel initialize
        """
        self.gi()
        time.sleep(5.0)
        wheel_ready = self.g()
        while wheel_ready != "y":
            logger.warning("grism wheel not ready")
            time.sleep(2.0)
            wheel_ready = self.g()
        return

    def grism_wait(self, func, N_tries=24, sleep_time=5.0):
        for ii in range(N_tries):
            grism_ready = func() #self.g()
            if grism_ready == "y":
                return
            time.sleep(sleep_time)
        raise DfoscError(f"DFOSC grism wheel not ready after {N_tries}")

    def grism_goto(self, position: str, ):
        """
        Grism Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        self.grism_wait()
        logger.info(f"filter ready: move to {position}")
        result = self.gg(position)
        self.grism_wait()
        return

    def ai(self):
        """
        Aperture Initialize position to hall switch and aperture_zero offset
        """
        command = f"AI"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def ag(self, position: str):
        """
        Aperture Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        command = f"AG{position}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def am(self, position: str):
        """
        Aperture Move relative nnnnnn. '+' or '-' can be entered before nnnnnn
        """
        command = f"AM{position}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def ap(self):
        """
        Aperture Position 'nnnnnn'
        """
        command = f"AP"
        result_code, *dummy_values = self.get_data(command)
        print(result_code, dummy_values)
        return result_code

    def an(self, position: str):
        """
        Aperture Goto one of the 8 positions (n*40000 steps), corresponds to centered aperture plate opening
        n is a number 1-8 or 0-7
        """
        if int(position) not in range(8):
            msg = f"Aperture has positions 0-7; provided: {position}"
            logger.warning(msg)

        command = f"A{position}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def aq(self):
        """
        Aperture Quit current operation. Must be called quickly after command is sent.
        """
        command = f"AQ"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def a(self):
        """
        Check driver ready. Returns 'y' if ready, 'n' if not ready.
        """
        command = f"a"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def ax(self):
        """
        Aperture Goto hall initial position. Ressets aperture_zero to 0
        """
        command = f"AX"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def aidfoc(self):
        """
        Set zero position to current position. Records the aperture_zero value in eeprom.
        """
        command = f"Aidfoc"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def aperture_init(self):
        """
        Aperture initialize
        """
        self.ai()

        time.sleep(5.0)
        wheel_rdy = self.a()
        while wheel_rdy != "y":
            logger.warning("aperture wheel not ready")
            time.sleep(2.0)
            self.a()
        return

    def aperture_goto(self, position: str, N_tries=30, sleep_time=5.0):
        """
        Aperture Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        for ii in range(N_tries):
            aperture_ready = self.a()
            if aperture_ready == "y":
                logger.info(f"filter ready: move to {position}")
                result = self.ag(position)
                return result
            time.sleep(sleep_time)
        raise DfoscError(f"DFOSC aperture wheel not ready after {N_tries}")

    def fi(self):
        """
        Filter Initialize position to hall switch and filter_zero offset
        """
        command = f"FI"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def fg(self, position: str):
        """
        Filter Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        command = f"FG{position}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def fm(self, position: str):
        """
        Filter Move relative nnnnnn. '+' or '-' can be entered before nnnnnn
        """
        command = f"FM{position}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def fp(self):
        """
        Filter Position 'nnnnnn'
        """
        command = f"FP"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def fn(self, position: str):
        """
        Filter Goto one of the 8 positions (n*40000 steps), corresponds to centered aperture plate opening
        n is a number 1-8 or 0-7
        """
        if int(position) not in range(8):
            msg = f"Filter has positions 0-7; provided: {position}"
            logger.warning(msg)

        command = f"F{position}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def fq(self):
        """
        Filter Quit current operation. Must be called quickly after command is sent.
        """
        command = f"FQ"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def f(self):
        """
        Check driver ready. Returns 'y' if ready, 'n' if not ready.
        """
        command = f"f"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def fx(self):
        """
        Filter Goto hall initial position. Ressets aperture_zero to 0
        """
        command = f"FX"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def fidfoc(self):
        """
        Set zero position to current position. Records the aperture_zero value in eeprom.
        """
        command = f"Fidfoc"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def filter_init(self):
        """
        Filter wheel initialize
        """
        self.fi()
        time.sleep(5.0)
        while self.f() != "y":
            logger.warning("Filter Wheel Not Ready")
            time.sleep(2.0)
        return

    def filter_goto(self, position: str, N_tries=30, sleep_time=5.0):
        """
        Filter Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """

        for ii in range(N_tries):
            filter_ready = self.f()
            if filter_ready == "y":
                logger.info(f"filter ready: move to {position}")
                result = self.fg(position)
                return result
            time.sleep(sleep_time)
        raise DfoscError(f"DFOSC filter wheel not ready after {N_tries}")

    def log_all_status(self):
        grism_ready = self.g()
        grism_pos = self.gp()
        aper_ready = self.a()
        aper_pos = self.ap()
        filter_ready = self.f()
        filter_pos = self.fp()

        try:
            grism_guess, grism_value = guess_wheel_pos(
                grism_pos, self.dfosc_setup["grism"]
            )
            aper_guess, aper_value = guess_wheel_pos(
                grism_pos, self.dfosc_setup["slit"]
            )
            filter_guess, filter_value = guess_wheel_pos(
                grism_pos, self.dfosc_setup["filter"]
            )
        except Exception as e:
            grism_guess, aper_guess, filter_pos = "?", "?", "?"

        status_str = (
            f"DFOSC status:\n"
            f"    grism wheel ready? {grism_ready}\n"
            f"    aper wheel ready? {aper_ready}\n"
            f"    filter wheel ready? {filter_ready}\n"
            f"    grism pos: {grism_pos} (likely '{grism_guess}')\n"
            f"    aper pos: {aper_pos} (likely '{aper_guess}')\n"
            f"    filter pos: {filter_pos} (likely '{filter_guess}')\n"
        )

        logger.info(status_str)
