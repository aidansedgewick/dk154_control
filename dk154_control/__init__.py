import datetime
import logging
import sys
from pathlib import Path

import dk154_control.tcs

root_dir = Path(__file__).parent.parent

test = "hello world!"


###====== setup logger =======###

log_dir = root_dir / "logs"
log_dir.mkdir(exist_ok=True)
time_now = datetime.datetime.now()
log_name = time_now.strftime("%y%m%d_%H%M%S.log")

log_file = log_dir / log_name

logging.basicConfig(
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
    ],
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    datefmt="%y-%m-%d %H:%M:%S",
)
    
