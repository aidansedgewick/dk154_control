from logging import getLogger

from dk154_control.api import Dk154Api

logger = getLogger("test_004")

if __name__ == "__main__":
    with Dk154Api(test_mode=True) as api:
        api.telescope_check_status()
