"""
Python wrapper for low-level TCP-IP communication.

24-11-23

Controls for the aperture/slits, filter, and grism wheels for DFOSC.
Basic commands defined, and some additional start-up read-state commands for the various wheels.

NOTE: These are not yet tested on ALFOSC, so it is not guaranteed that they work.

TODO would it be easier to just have a library of grism, filter, and slit configurations at the beginning of this file?
"""

import time
import socket
from logging import getLogger

logger = getLogger(__file__.split("/")[-1])

"""
DFOSC commands for the MOXA
These are the commands that are sent directly to the MOXA (figure out the IP & port).
Includes aperture (slit), filter, and grism wheel commands.
"""
# TODO - get the IP and port number for the MOXA


class Grism:

    INTERNAL_HOST = ""
    EXTERNAL_HOST = ""
    MOXA_PORT = 4001  # TODO: get port number
    LOCAL_HOST = "127.0.0.1"
    LOCAL_PORT = 8883

    def __init__(self, external=False, test_mode=False):

        logger.info("initialise DFOSC grism wheel")
        if external:
            self.HOST = self.EXTERNAL_HOST
        else:
            self.HOST = self.INTERNAL_HOST
        self.port = self.MOXA_PORT

        self.test_mode = test_mode
        if self.test_mode:
            self.HOST = self.LOCAL_HOST
            self.PORT = self.LOCAL_PORT
            logger.info(f"start Grism in TEST MODE (use localhost:{self.PORT})")

        self.init_time = time.time()

        # self.connect_socket()

    def connect_socket(self):
        self.info("Grism socket connect")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.HOST, self.PORT))
        self.conn_timestamp()
        self.sock = sock  # Don't name it 'socket' else overload module...

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()
        logger.info("DFOSC Grism connection closed in __exit__")

    def get_data(self, command: str):
        """
        The actual sending/recieving of TCP IP commands.
        returns a LIST (can be one element long)
        Similar to ASCOL????
        """
        command_code = command.split()[0]
        print_command = command
        logger.info(f"send: {print_command}")

        send_command = (command + "\n").encode("utf-8")
        # TODO there may be a timeout issue here, so would need a try block to reconnect
        self.sock.sendall(send_command)  # Send the command to the TCS computer

        data = self.sock.recv(1024)  # Ask for the result, up to 1024 char long.
        data = data.decode("ascii")  # Decode from binary string
        data = data.rstrip()  # Strip some unimportant newlines
        data = data.split()

        if len(data) == 1 and data[0] == "ERR":
            logger.warning(f"Result is ERR. Is {command_code} a 'set' command?")

        return data

    def gi(self):
        """
        Grism Initialize position to hall switch and grism_zero offset.
        Only to be used after a power failure/cycle or if the grism has been moved manually.
        """
        command = f"GI"
        (result_code,) = self.get_data(command)  # Unpack single element list.
        return result_code

    def gg(self, x: str):
        """
        Grism Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        command = f"GG{x}\n"
        (result_code,) = self.get_data(command)  # Unpack single element list.
        return result_code

    def gm(self, x: str):
        """
        Grism Move relative nnnnnn. '+' or '-' can be entered before nnnnnn
        """

        command = f"GM {x}\n"
        (result_code,) = self.get_data(command)
        return result_code

    def gp(self):
        """
        Grism Position, returns the current position value 'nnnnnn'
        """
        command = f"GP"
        (result_code,) = self.get_data(command)
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
        (result_code,) = self.get_data(command)
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
        (return_code,) = self.getdata(command)
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

    def g_init(self):
        """
        Grism wheel initialize
        """
        self.gi()
        time.sleep(5)
        wheel_rdy = self.g()
        while wheel_rdy != "y":
            logger.warning("Grism Wheel Not Ready")
            time.sleep(2)
            self.g()

        return logger.info(f"Current Grism Position: {self.gp()}")

    def goto(self, position: str):
        """
        Grism Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        wheel_ready = self.g()
        if wheel_ready == "y":
            logger.info("Grism Wheel Moving to Position")
            self.gg(position)
        else:
            logger.warning("Grism Wheel Not Ready")

        return print(f"Current Grism Position: {self.gp()}")


class Slit:

    INTERNAL_HOST = ""
    EXTERNAL_HOST = ""
    MOXA_PORT = 4001  # TODO: get port number
    LOCAL_HOST = "127.0.0.1"
    LOCAL_PORT = 8884

    def __init__(self, external=False, test_mode=False):

        logger.info("initialise DFOSC grism wheel")
        if external:
            self.HOST = self.EXTERNAL_HOST
        else:
            self.HOST = self.INTERNAL_HOST
        self.port = self.MOXA_PORT

        self.test_mode = test_mode
        if self.test_mode:
            self.HOST = self.LOCAL_HOST
            self.PORT = self.LOCAL_PORT
            logger.info(f"start Slit in TEST MODE (use localhost:{self.PORT})")

        # self.connect_socket()

    def connect_socket(self):
        self.info("Grism socket connect")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.HOST, self.PORT))
        self.conn_timestamp = time.time()
        self.sock = sock  # Don't name it 'socket' else overload module...

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()
        logger.info("DFOSC connection closed in __exit__")

    def get_data(self, command: str):
        """
        The actual sending/recieving of TCP IP commands.
        returns a LIST (can be one element long)
        Similar to ASCOL????
        """
        command_code = command.split()[0]
        print_command = command

        logger.info(f"send: {print_command}")

        send_command = (command + "\n").encode("utf-8")
        self.sock.sendall(send_command)  # Send the command to the TCS computer
        data = self.sock.recv(1024)  # Ask for the result, up to 1024 char long.
        data = data.decode("ascii")  # Decode from binary string
        data = data.rstrip()  # Strip some unimportant newlines
        data = data.split()

        if len(data) == 1 and data[0] == "ERR":
            logger.warning(f"Result is ERR. Is {command_code} a 'set' command?")

        return data

    def ai(self):
        """
        Aperture Initialize position to hall switch and aperture_zero offset
        """
        command = f"AI"
        (result_code,) = self.get_data(command)
        return result_code

    def ag(self, position: str):
        """
        Aperture Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        command = f"AG{position}"
        (result_code,) = self.get_data(command)
        return result_code

    def am(self, position: str):
        """
        Aperture Move relative nnnnnn. '+' or '-' can be entered before nnnnnn
        """
        command = f"AM{position}"
        (result_code,) = self.get_data(command)
        return result_code

    def ap(self):
        """
        Aperture Position 'nnnnnn'
        """
        command = f"AP"
        (result_code,) = self.get_data(command)
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
        (result_code,) = self.get_data(command)
        return result_code

    def aq(self):
        """
        Aperture Quit current operation. Must be called quickly after command is sent.
        """
        command = f"AQ"
        (result_code,) = self.get_data(command)
        return result_code

    def a(self):
        """
        Check driver ready. Returns 'y' if ready, 'n' if not ready.
        """
        command = f"a"
        (result_code,) = self.get_data(command)
        return result_code

    def ax(self):
        """
        Aperture Goto hall initial position. Ressets aperture_zero to 0
        """
        command = f"AX"
        (result_code,) = self.get_data(command)
        return result_code

    def aidfoc(self):
        """
        Set zero position to current position. Records the aperture_zero value in eeprom.
        """
        command = f"Aidfoc"
        (result_code,) = self.get_data(command)
        return result_code

    def a_init(self):
        """
        Aperture initialize
        """
        self.ai()

        time.sleep(5)
        wheel_rdy = self.a()
        while wheel_rdy != "y":
            logger.warning("Aperture Wheel Not Ready")
            time.sleep(2)
            self.a()

        return print(f"Current Aperture Position: {self.ap()}")

    def goto(self, position: str):
        """
        Aperture Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        self.a()
        if self.a() == "y":
            logger.info("Aperture Wheel Moving to Position")
            self.ag(position)
        else:
            logger.warning("Aperture Wheel Not Ready")

        return print(f"Current Aperture Position: {self.ap()}")


class Filter:

    INTERNAL_HOST = ""
    EXTERNAL_HOST = ""
    MOXA_PORT = 4001  # TODO: get port number
    LOCAL_HOST = "127.0.0.1"
    LOCAL_PORT = 8885

    def __init__(self, external=False, test_mode=False):

        logger.info("initialise DFOSC filter wheel")
        if external:
            self.HOST = self.EXTERNAL_HOST
        else:
            self.HOST = self.INTERNAL_HOST
        self.port = self.MOXA_PORT

        self.test_mode = test_mode
        if self.test_mode:
            self.HOST = self.LOCAL_HOST
            self.PORT = self.LOCAL_PORT
            logger.info(f"start Filter in TEST MODE (use localhost:{self.PORT})")

        # self.connect_socket()

    def connect_host(self):
        self.info("Filter socket connect")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.HOST, self.PORT))
        self.conn_timestamp = time.time()
        self.sock = sock  # Don't name it 'socket' else overload module...

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()
        logger.info("Filter connection closed in __exit__")

    def get_data(self, command: str):
        """
        The actual sending/recieving of TCP IP commands.
        returns a LIST (can be one element long)
        """
        command_code = command.split()[0]
        print_command = command

        logger.info(f"send: {print_command}")

        send_command = (command + "\n").encode("utf-8")
        self.sock.sendall(send_command)  # Send the command to the TCS computer
        data = self.sock.recv(1024)  # Ask for the result, up to 1024 char long.
        data = data.decode("ascii")  # Decode from binary string
        data = data.rstrip()  # Strip some unimportant newlines
        data = data.split()

        if len(data) == 1 and data[0] == "ERR":
            logger.warning(f"Result is ERR. Is {command_code} a 'set' command?")

        return data

    def fi(self):
        """
        Filter Initialize position to hall switch and filter_zero offset
        """
        command = f"FI"
        (result_code,) = self.get_data(command)
        return result_code

    def fg(self, position: str):
        """
        Filter Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        command = f"FG{position}"
        (result_code,) = self.get_data(command)
        return result_code

    def fm(self, position: str):
        """
        Filter Move relative nnnnnn. '+' or '-' can be entered before nnnnnn
        """
        command = f"FM{position}"
        (result_code,) = self.get_data(command)
        return result_code

    def fp(self):
        """
        Filter Position 'nnnnnn'
        """
        command = f"FP"
        (result_code,) = self.get_data(command)
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
        (result_code,) = self.get_data(command)
        return result_code

    def fq(self):
        """
        Filter Quit current operation. Must be called quickly after command is sent.
        """
        command = f"FQ"
        (result_code,) = self.get_data(command)
        return result_code

    def f(self):
        """
        Check driver ready. Returns 'y' if ready, 'n' if not ready.
        """
        command = f"f"
        (result_code,) = self.get_data(command)
        return result_code

    def fx(self):
        """
        Filter Goto hall initial position. Ressets aperture_zero to 0
        """
        command = f"FX"
        (result_code,) = self.get_data(command)
        return result_code

    def fidfoc(self):
        """
        Set zero position to current position. Records the aperture_zero value in eeprom.
        """
        command = f"Fidfoc"
        (result_code,) = self.get_data(command)
        return result_code

    def f_init(self):
        """
        Filter wheel initialize
        """
        self.fi()

        time.sleep(5)

        self.f()

        while self.f() != "y":
            logger.warning("Filter Wheel Not Ready")
            time.sleep(2)
            self.f()

        return print(f"Current Filter Position: {self.fp()}")

    def goto(self, position: str):
        """
        Filter Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        self.f()

        if self.f() == "y":
            logger.info("Filter Wheel Moving to Position")
            self.fg(position)
        else:
            logger.warning("Filter Wheel Not Ready")

        return print(f"Current Filter Position: {self.fp()}")
