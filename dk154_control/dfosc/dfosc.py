"""
Python wrapper for low-level TCP-IP communication.

24-11-23
"""


import datetime
import socket
from logging import getLogger


logger = getLogger(__file__.split("/")[-1])


class AscolInputError(Exception):
    pass


class DFOSC:
    """
    DFOSC commands for the MOXA

    These are the commands that are sent directly to the MOXA (figure out the IP & port).
    Includes aperture (slit), filter, and grism wheel commands.
    """

    INTERNAL_HOST = "192.168.132."  # The remote host, internal IP of the MOXA
    EXTERNAL_HOST = "134.171.81."  # The remote host, external IP of the MOXA
    PORT =   # TODO: get port number
    GLOBAL_PASSWORD = ""  # TODO: get password, if there is one

    def __init__(self, internal=True, dry_run=False):
        if internal:
            self.HOST = self.INTERNAL_HOST
        else:
            self.HOST = self.EXTERNAL_HOST

        self.dry_run = dry_run

        self.init_time = datetime.datetime.gmtime()

        logger.info("initialise DFOSC")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.HOST, self.PORT))

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

# Grism Wheel

    def gi(self):
        """
        Grism Initialize position to hall switch and grism_zero offset.
        Only to be used after a power failure/cycle or if the grism has been moved manually.
        """
        command = f"GI"
        (result_code,) = self.get_data(command)  # Unpack single element list.
        return result_code

    def gg(self,x: str):
        """
        Grism Goto position nnnnnn, where nnnnnn is the position number between 0 and 320000
        """
        command = f"GG{x}\n"
        (result_code,) = self.get_data(command)  # Unpack single element list.
        return result_code

    def gm(self,x:str):
        """
        Grism Move relative nnnnnn. '+' or '-' can be entered before nnnnnn
        """

        command = f"GM {x}\n"
        (result_code,) = self.get_data(command)
        return result_code

    def gp(self):
        """
        Grism Position 'nnnnnn'
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
            msg = f"Grism has positions 0-7; provided: {position}"
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

# Repeat the same set of commands for the aperture and filter wheels

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

# Filter Wheel

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
