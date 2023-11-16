import datetime
import socket
from logging import getLogger


from dk154_control.tcs import ascol_constants

logger = getLogger(__file__.split("/")[-1])

class Ascol:
    INTERNAL_HOST = '192.168.132.11' # The remote host, internal IP of the TCS
    EXTERNAL_HOST = '134.171.81.74' # The remote host, external IP of the TCS
    PORT = 2003 # Same port used by the server, ports avail 2001-2009, 2007 is occupied
    GLOBAL_PASSWORD = "1178"
    
    def __init__(self, internal=True):
        """
        ASCOL implemented as in the documentatin
        """
        
        if internal:
            self.HOST = self.INTERNAL_HOST
        else:
            self.HOST = self.EXTERNAL_HOST

        self.init_time = datetime.datetime.gmtime()
        
        logger.info("initialise Ascol")
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.HOST, self.PORT))
        
        self.sock = sock # Don't name it 'socket' else overload module...
        
      
    def __enter__(self):
          return self
            
    def __exit__(self, exc_type, exc_value, traceback):
        self.sock.close()
        
        
    def get_data(self, command: str):
        """
        The actual sending/recieving of TCP IP commands.
        
        returns a LIST (can be one element long)
        """
        
        print_cmd = command
        if "GLLG" in command:
            print_cmd = "GLLG <pwd>"

        logger.info("send: {print_cmd}")
     
        send_cmd = (command + "\n").encode("utf-8")
        self.sock.sendall(send_cmd) # Send the command to the TCS computer
        
        data = self.sock.recv(1024) # Ask for the result, up to 1024 char long.
        data = data.decode("ascii") # Decode from binary string
        data = data.rstrip() # Strip some unimportant newlines
        data = data.split()
        ###TODO: ADD CONVERT DATA
        print(data)
        
        return data

    def gllg(self, password=None):
        """
        GLobal LoGin
        
        ASCOL 2.2
        
        returns 0 (wrong pwd) 1 (correct)
        """
        password = password or self.GLOBAL_PASSWORD
        
        cmd = f"GLLG {password}"
        result_code, = self.get_data(cmd)
        password_result = GLLG_CODES[result_code]
        return password_result


    def glll(self):
        """
        GLobal read Latitude and Longitude
        
        ASCOL 2.3
        
        returns lat/lon
        """
        lat, lon = self.get_data("GLLL")
        return lat, lon
    
    
    def teon(self):
        """
        
        ASCOL 2.10
        """
        raise NotImplementedError()
    
    def tsra(self, ra, dec, position):
        """
        Telescope Set Right ascension and declination
        
        ASCOL 2.17
        
        Parameters
        ----------
        
        
        ra [hhmmss.s]
        dec [ddmmss.s]
        position [0 – East, 1 – West]
        
        returns 1 (ok) or ERR
        """
        self.gllg() # Set commands require global password
        cmd = f"TSRA {ra} {dec} {position}"
        return self.get_data(cmd)
    
    
    def tgra(self):
        """
        Telescope Go Right ascension and declination
        
        ASCOL 2.19
        
        Returns 1 (ok) or ERR
        """
        self.gllg() # Set commands require global password
        return self.get_data("TGRA")
        
      
    def trrd(self):
        """
        Telescope Read Right ascension and Declination
        
        ASCOL 2.41
        
        Returns RA, Dec and human readable position (east/west).
        """
        ra, dec, position_code = self.get_data("TRRD")
        return float(ra), float(dec), TRRD_POSITION_CODES[position_code]
      
            
    def ters(self):
        """
        TElescope Read State.
        
        ASCOL 2.43
        
        Returns human readable string.
        """
        return_code, dummy_value = self.get_data("TERS")
        return TERS_CODES[return_code]
        
        
    def dors(self):
        """
        DOme Read State
        
        ASCOL 2.56
        
        Returns as human readable string
        """
        return_code, dummy_value = self.get_data("DORS")
        return DORS_CODES[return_code]
    
    
    def fmop(self):
        """
        
        ASCOL 2.60
        """
        raise NotImplementedError()
    
    
    def fmrs(self):
        """
        
        ASCOL 2.62
        """
        raise NotImplementedError()
    
    
    def wasp(self):
        """
        
        ASCOL 2.63
        """
        raise NotImplementedError()
    
    
    def wagp(self):
        """
        
        ASCOL 2.64
        """
        raise NotImplementedError()
    
    
    def warp(self):
        """
        
        ASCOL 2.66
        """
        raise NotImplementedError()
    
    
    def wars(self):
        """
        
        ASCOL 2.68
        """
        raise NotImplementedError()
    
    
    def wbsp(self):
        """
        
        ASCOL 2.69
        """
        raise NotImplementedError()
    
    
    def wbgp(self):
        """
        
        ASCOL 2.70
        """
        raise NotImplementedError()
    
    
    def wbrp(self):
        """
        
        ASCOL 2.72
        """
        raise NotImplementedError()
    
    
    def wbrs(self):
        """
        
        ASCOL 2.74
        """
        raise NotImplementedError()
    
    
    def mebe(self):
        """
        
        ASCOL 2.136
        """
        raise NotImplementedError()
    
    
    def mebn(self):
        """
        
        ASCOL 2.137
        """
        raise NotImplementedError()
    
    
    def mebw(self):
        """
        
        ASCOL 2.138
        """
        raise NotImplementedError()
    
    
    def metw(self):
        """
        
        ASCOL 2.139
        """
        raise NotImplementedError()
    
    
    def mehu(self):
        """
        
        ASCOL 2.140
        """
        raise NotImplementedError()
    
    
    def mete(self):
        """
        
        ASCOL 2.141
        """
        raise NotImplementedError()
    
    
    def mews(self):
        """
        
        ASCOL 2.142
        """
        raise NotImplementedError()
    
    
    def mepr(self):
        """
        
        ASCOL 2.139
        """
        raise NotImplementedError()
    
    
    def meap(self):
        """
        
        ASCOL 2.144
        """
        raise NotImplementedError()
    
    
    def mepy(self):
        """
        
        ASCOL 2.145
        """
        raise NotImplementedError()
    
    

