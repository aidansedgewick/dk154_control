from pathlib import Path

import json
from termcolor import colored, cprint
from dk154_control.dfosc import dfosc

"""
Script for moving DFOSC wheels to specified positions
Needs to be tested on DFOSC!
This imports the dfosc module from dk154_control, which contains the low level commands for the slit, grism, and filter wheels.
The script then reads the setup from the dfosc_setup.json file and moves the wheels to the specified positions
NOTE: actual wheel positions should be tested, measured, and updated in the dfosc_setup.json file!
other commands can be written in dfosc.py for more complex operations (eg. slit)
"""
slit = dfosc.Slit()
grism = dfosc.Grism()
filter = dfosc.Filter()

# Read dfosc setup - read as this file: the parent (ie, 'dfosc' dir), then the relevant JSON.
dfosc_setup_filepath = Path(__file__).parent / "dfosc_setup.json"
dfosc_wheels = json.load(dfosc_setup_filepath)

grism_pos = dfosc_wheels["grism"]["7"]
slit_pos = dfosc_wheels["slit"]["1.0"]
filt_pos = dfosc_wheels["filter"]["dispb"]

cprint("\n**** Moving to specified DFOSC wheels ****", "red", attrs=["blink"])

# Move to specified positions
slit.goto(slit_pos)
grism.goto(grism_pos)
filter.goto(filt_pos)
