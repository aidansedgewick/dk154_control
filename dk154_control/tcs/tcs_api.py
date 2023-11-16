from logging import getLogger

from astropy.coordinates import SkyCoord

from dk154_control.tcs.ascol import Ascol

logger = getLogger(__file__.split("/")[-1])

class Tcs:
    """
    User-friendly interface for controlling the telescope
    """
    
    
    
    def __init__(self):
        logger.info("init Tcs object")
        
        self.ascol = Ascol()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        logger.info("Tcs exit")
        self.ascol.sock.close()
        logger.info("ascol socket closed")
        
    def telescope_goto(self, coord: SkyCoord):
        pass
