"""
Python wrapper for low-level TCP-IP communication.

24-11-23

Controls for the aperture/slits, filter, and grism wheels for DFOSC.
Basic commands defined, and some additional start-up read-state commands for the various wheels.
"""

import traceback

import time

import socket
import telnetlib
import yaml
from logging import getLogger
from pathlib import Path

import numpy as np

from dk154_control.utils import SilenceLoggers

logger = getLogger(__name__.split(".")[-1])

"""
DFOSC commands for the MOXA
These are the commands that are sent directly to the MOXA (figure out the IP & port).
Includes aperture (slit), filter, and grism wheel commands.
"""


def load_dfosc_setup(setup_path=None):
    setup_path = setup_path or Path(__file__).parent / "dfosc_setup.yaml"
    with open(setup_path, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def guess_wheel_element_name(current_pos, wheel_setup: dict, wheel_max=320000):

    try:
        int(current_pos)
    except:
        return "ERR"

    # Hopefully the position exactly matches
    inv_setup = {int(v): str(k) for k, v in wheel_setup.items()}
    name = inv_setup.get(current_pos, None)
    if name is not None:
        logger.info(f"exact match '{name}' for {current_pos}")
        return name

    # If not, get the closest defined position to the current position...
    logger.info(f"no exact match for {current_pos} - find closest.")

    wheel_positions = []
    wheel_elem_names = []
    for elem_name, wheel_pos in wheel_setup.items():
        wheel_positions.append(int(wheel_pos))
        wheel_elem_names.append(elem_name)

    # Take care of 'wrap around' - eg. if positions are [0, ..., 240, 300], then
    # have list [0,...240, 300, 360] so that 359 'rounds to' 360, not 300.
    wheel_positions.append(wheel_positions[0] + wheel_max)
    wheel_elem_names.append(wheel_elem_names[0])

    idx = np.argmin(abs(np.array(wheel_positions) - current_pos))
    # diff_list = [abs(x-current_pos) for x in wheel_positions]
    # idx = min(range(len(diff_list)), key=lambda x: diff_list[x])
    name = wheel_elem_names[idx]
    closest_pos = wheel_setup[name]
    logger.info(f"closest match '{name}' at postion {closest_pos}")

    return f"{name} [at {closest_pos}]"


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
    EXTERNAL_HOST = ""  # No external host currently
    MOXA_PORT = 4001
    LOCAL_HOST = "127.0.0.1"
    LOCAL_PORT = 8885  # Matches with MockDfoscServer

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
            self.dfosc_setup = {"grism": {}, "aper": {}, "filter": {}}

        self.tn = None
        self.sock = None
        self.connect_telnet()
        # self.connect_socket()

    def connect_telnet(self):
        logger.info("Dfosc telnet connect")
        self.tn = telnetlib.Telnet(self.HOST, self.PORT)

    def connect_socket(self):
        logger.info("socket connect")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.HOST, self.PORT))
        self.conn_timestamp = time.time()
        time.sleep(1.0)

        self.sock = sock  # Don't call it 'socket', else overload module...

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.tn is not None:
            self.tn.close()
            logger.info("DFOSC telnet closed in __exit__")
        if self.sock is not None:
            self.sock.close()
            logger.info("DFOSC socket conn. closed in __exit__")

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
        # logger.info(f"send: {print_command}")

        send_command = (command + "\n").encode()

        try:
            logger.info(f"try sending {send_command}...")
            self.tn.write(send_command)
            # self.sock.sendall(send_command)
        except IOError as e:
            logger.info("try to reconnect...")
            self.connect_telnet()
            self.tn.write(send_command)
            # self.connect_socket()
            # self.sock.sendall(send_command)
            if self.debug:
                logger.debug("successful send after reconnect.")

        TERMINATE_BYTES = "\n".encode("utf-8")  # telnet should return chars until THIS.
        data = self.tn.read_until(TERMINATE_BYTES)
        # data = self.sock.recv(1024)  # returns bytes
        data = data.decode("utf-8")
        data = data.rstrip()
        data = data.split()

        logger.info(f"receive + decode {data}")

        if len(data) == 1 and data[0] == "ERR":
            logger.warning(f"Result is ERR. Is {command_code} a 'set' command?")

        return tuple(data)

    def gi(self):
        """
        Grism Initialize position to hall switch and grism_zero offset.
        Only to be used after a power failure/cycle or if the grism has been moved manually.
        """
        command = f"GI"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def gg(self, x: str):
        """
        Grism Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        command = f"GG{x}"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def gm(self, x: str):
        """
        Grism Move relative nnnnnn. '+' or '-' can be entered before nnnnnn
        """
        command = f"GM{x}"
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
        n is a number 1-8
        """
        if int(pos) not in range(8):  # range(8) incl. 0, excl, 8
            msg = f"Grism has positions 1-8; provided: {pos}"
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
        return return_code

    def gx(self):
        """
        Grism Goto hall initial position. Ressets aperture_zero to 0

        SHOULD NEVER NEED TO USE THIS
        """
        (return_code,) = self.get_data("GX")
        return return_code

    def gidfoc(self):
        """
        Set zero position to current position. Records the aperture_zero value in eeprom.

        SHOULD NEVER NEED TO USE THIS
        """
        (return_code,) = self.get_data("Gidfoc")
        return return_code

    def grism_init(self):
        """
        Grism wheel initialize
        """
        self.gi()
        self.grism_wait()
        return

    def grism_wait(self, N_tries=24, sleep_time=5.0):
        """
        Wait for grism wheel to be ready
        """
        for ii in range(N_tries):
            grism_ready = self.g()
            if grism_ready == "gy":
                logger.info("grism wheel ready")
                return
            time.sleep(sleep_time)
        raise DfoscError(f"DFOSC grism wheel not ready after {N_tries}")

    def grism_goto(self, position: str):
        """
        Grism Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        self.grism_wait()
        result = self.gg(position)
        self.grism_wait()
        return result

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
        return result_code

    def an(self, position: str):
        """
        Aperture Goto one of the 8 positions (n*40000 steps), corresponds to centered aperture plate opening
        n is a number 1-8
        """
        if int(position) not in range(8):
            msg = f"Aperture has positions 1-8; provided: {position}"
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
        Check driver ready. Returns 'ay' if ready, 'n' if not ready.
        """
        command = f"a"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def ax(self):
        """
        Aperture Goto hall initial position. Ressets aperture_zero to 0

        SHOULD NEVER NEED TO USE THIS
        """
        command = f"AX"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def aidfoc(self):
        """
        Set zero position to current position. Records the aperture_zero value in eeprom.

        SHOULD NEVER NEED TO USE THIS
        """
        command = f"Aidfoc"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def aperture_init(self):
        """
        Aperture initialize
        """
        self.ai()
        self.aperture_wait()
        return

    def aperture_wait(self, N_tries=24, sleep_time=5.0):
        """
        Wait for aperture wheel to be ready
        """
        for ii in range(N_tries):
            aperture_ready = self.a()
            if aperture_ready == "ay":
                logger.info("aperture wheel ready")
                return
            time.sleep(sleep_time)
        raise DfoscError(f"DFOSC aperture wheel not ready after {N_tries}")

    def aperture_goto(self, position: str):
        """
        Aperture Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        self.aperture_wait()
        result = self.ag(position)
        self.aperture_wait()
        return result

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
        n is a number 1-8
        """
        if int(position) not in range(8):
            msg = f"Filter has positions 1-8; provided: {position}"
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
        Check driver ready. Returns 'fy' if ready, 'n' if not ready.
        """
        command = f"f"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def fx(self):
        """
        Filter Goto hall initial position. Ressets aperture_zero to 0

        SHOULD NEVER NEED TO USE THIS
        """
        command = f"FX"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def fidfoc(self):
        """
        Set zero position to current position. Records the aperture_zero value in eeprom.

        SHOULD NEVER NEED TO USE THIS
        """
        command = f"Fidfoc"
        result_code, *dummy_values = self.get_data(command)
        return result_code

    def filter_init(self):
        """
        Filter wheel initialize
        """
        self.fi()
        self.filter_wait()
        return

    def filter_wait(self, N_tries=24, sleep_time=5.0):
        """
        Wait for filter wheel to be ready
        """
        for ii in range(N_tries):
            filter_ready = self.f()
            if filter_ready == "fy":
                logger.info("filter wheel ready")
                return
            time.sleep(sleep_time)
        raise DfoscError(f"DFOSC filter wheel not ready after {N_tries}")

    def filter_goto(self, position: str):
        """
        Filter Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        self.filter_wait()
        result = self.fg(position)
        self.filter_wait()
        return result

    # def log_all_status(self):
    #     grism_ready = self.g()
    #     grism_pos = self.gp()
    #     aper_ready = self.a()
    #     aper_pos = self.ap()
    #     filter_ready = self.f()
    #     filter_pos = self.fp()

    #     try:
    #         grism_guess, grism_value = guess_wheel_pos(
    #             grism_pos, self.dfosc_setup["grism"]
    #         )
    #         aper_guess, aper_value = guess_wheel_pos(
    #             grism_pos, self.dfosc_setup["aperture"]
    #         )
    #         filter_guess, filter_value = guess_wheel_pos(
    #             grism_pos, self.dfosc_setup["filter"]
    #         )
    #     except Exception as e:
    #         print(e)
    #         grism_guess, aper_guess, filter_guess = "?ERR", "?ERR", "?ERR"

    #     status_str = (
    #         f"DFOSC status:\n"
    #         f"    grism wheel ready? {grism_ready}\n"
    #         f"    aper wheel ready? {aper_ready}\n"
    #         f"    filter wheel ready? {filter_ready}\n"
    #         f"    grism pos: {grism_pos} (likely '{grism_guess}')\n"
    #         f"    aper pos: {aper_pos} (likely '{aper_guess}')\n"
    #         f"    filter pos: {filter_pos}   (likely '{filter_guess}')\n"
    #     )

    #     logger.info(status_str)


class DfoscStatus:

    @classmethod
    def collect_silent(cls, test_mode=False):
        with SilenceLoggers():
            status = cls(test_mode=test_mode)
        return status

    def __init__(self, test_mode=False):

        try:
            self.dfosc_setup = load_dfosc_setup()
        except Exception as e:
            self.dfosc_setup = {"grism": {}, "aperture": {}, "filter": {}}

        try:
            self.gather_status(test_mode=test_mode)
        except Exception as e:
            logger.info(f"when gathering DFOSC status:\n    {type(e).__name__}: {e}")
            self.grism_ready = "???"
            self.grism_position = "???"
            self.aper_ready = "???"
            self.aper_position = "???"
            self.filter_ready = "???"
            self.filter_position = "???"

        try:
            gpos = int(self.grism_position[2:])  # "GP40000" -> 0 [integer]
            grism_guess = guess_wheel_element_name(gpos, self.dfosc_setup["grism"])
        except Exception as e:
            grism_guess = "ERR"

        try:
            apos = int(self.aper_position[2:])
            aper_guess = guess_wheel_element_name(apos, self.dfosc_setup["aperture"])
        except Exception as e:
            aper_guess = "ERR"

        try:
            fpos = int(self.filter_position[2:])
            filter_guess = guess_wheel_element_name(fpos, self.dfosc_setup["filter"])
        except Exception as e:
            filter_guess = "ERR"

        self.grism_name_guess = grism_guess
        self.aper_name_guess = aper_guess
        self.filter_name_guess = filter_guess

    def gather_status(self, test_mode=False):

        self.grism_position = "GP--N/A--"  #
        self.aper_position = "AP--N/A--"
        self.filter_position = "FP--N/A--"
        with Dfosc(test_mode=test_mode) as dfosc:
            self.grism_ready = dfosc.g()
            if self.grism_ready == "gy":
                self.grism_position = dfosc.gp()  # returns eg. "GP40000"
            self.aper_ready = dfosc.a()
            if self.aper_ready == "ay":
                self.aper_position = dfosc.ap()
            self.filter_ready = dfosc.f()
            if self.filter_ready == "fy":
                self.filter_position = dfosc.fp()

    def log_all_status(self):
        status_str = (
            f"DFOSC status:\n"
            f"    grism wheel ready? {self.grism_ready}\n"
            f"    aper wheel ready? {self.aper_ready}\n"
            f"    filter wheel ready? {self.filter_ready}\n"
            f"    grism pos: {self.grism_position} ('{self.grism_name_guess}')\n"
            f"    aper pos: {self.aper_position} ('{self.aper_name_guess}')\n"
            f"    filter pos: {self.filter_position} ('{self.filter_name_guess}')\n"
        )
        logger.info(status_str)
