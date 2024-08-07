import datetime
import logging
import sys
from pathlib import Path
from logging import handlers


root_dir = Path(__file__).parent.parent


###====== setup logger =======###

time_init = datetime.datetime.now()

log_dir = root_dir / "logs"
log_dir.mkdir(exist_ok=True)
time_str = time_init.strftime("%y%m%d_%H%M%S")
log_file = log_dir / f"dk154_{time_str}.log"
log_file = log_dir / f"dk154.log"

stream_handler = logging.StreamHandler(sys.stdout)
# file_handler = logging.FileHandler(log_file)
file_handler = handlers.TimedRotatingFileHandler(log_file, when="midnight")

logging.basicConfig(
    handlers=[stream_handler, file_handler],
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    datefmt="%y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("__init__")

from dk154_control.api import DK154
from dk154_control.tcs.ascol import Ascol
from dk154_control.dfosc.dfosc import Dfosc
from dk154_control.camera.ccd3 import Ccd3
from dk154_control.lamps.wave_lamps import WaveLamps
