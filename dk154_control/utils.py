import logging

import os

import numpy as np

from astropy.coordinates import Angle


class SilenceLoggers:

    def __enter__(self):
        logging.disable(logging.CRITICAL)

    def __exit__(self, exit_type, exit_value, exit_traceback):
        logging.disable(logging.NOTSET)


def dec_dms_to_deg(dms):
    """
    Convert (signed) DMS 'float' into decimal degrees.

    eg -102312.43 == -10d23m12.43s -> -10.38678611
    """

    if isinstance(dms, float) or isinstance(dms, int):
        dms_str = f"{dms:+f}"
    else:
        dms_str = dms

    d_str = dms_str[:3]
    m_str = dms_str[3:5]
    s_str = dms_str[5:]

    new_str = f"{d_str}d{m_str}m{s_str}s"

    angle = Angle(new_str)
    return angle.deg


def ra_hms_to_deg(hms):
    """
    Convert (unsigned) HMS 'float' into decimal degrees.

    """

    if isinstance(hms, float) or isinstance(hms, int):
        hms_str = f"{hms:f}"
    else:
        hms_str = hms

    h_str = hms_str[:2]
    m_str = hms_str[2:4]
    s_str = hms_str[4:]

    new_str = f"{h_str}h{m_str}m{s_str}s"

    angle = Angle(new_str)
    return angle.deg
