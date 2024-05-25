import time
import pandas as pd
from termcolor import colored, cprint
from dk154_control.dfosc import dfosc
from dk154_control.tcs.ascol import Ascol

"""
initialize DFOSC wheels (only at startup/power cycle) 
returns current wheel positions and telescope state
imports Ascol, and dfosc modules from dk154_control
"""

cprint(
    "\n**** Initializing DFOSC wheels, and Reading Telescope State ****",
    "red",
    attrs=["blink"],
)
time.sleep(2)

tcs = Ascol()

slit = dfosc.Slit()
grism = dfosc.Grism()
filter = dfosc.Filter()

slit.a_init()
grism.g_init()
filter.f_init()

tcs.ters()
