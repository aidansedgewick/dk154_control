from argparse import ArgumentParser
from logging import getLogger

import numpy as np

import pandas as pd


import matplotlib as mpl
import matplotlib.pyplot as plt

import astropy.units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_sun
from astropy.time import Time

from astroplan import Observer

import dk154_control

logger = getLogger("suggest_flat_field")

mpl.use("Qt5Agg")

POINT_RES_DIR = dk154_control.root_dir / "config/pointing_restrictions/"
POINT_RES_MAIN_FILEPATH = POINT_RES_DIR / "main.dat"
POINT_RES_REV_FILEPATH = POINT_RES_DIR / "reverse.dat"


def plot_pointing_restrictions():
    pass

def load_pointing_restrictions():

    columns = ["ha", "da"] # da=dec in main, da=-90-dec in reverse
    point_res_main = pd.read_csv(
        POINT_RES_MAIN_FILEPATH, delim_whitespace=True, names=columns
    )
    point_res_rev = pd.read_csv(
        POINT_RES_REV_FILEPATH, delim_whitespace=True, names=columns
    )
    point_res_main["dec"] = point_res_main["da"]
    point_res_rev["dec"] = abs(point_res_rev["da"] + 90.) - 90.0
    
    return point_res_main, point_res_rev

def suggest_flat_field(
    t_ref: Time = None, 
    observing_site="lasilla", 
):
    
    t_ref = t_ref or Time.now()
    
    location = EarthLocation.of_site(observing_site)
    observer = Observer(location)
    
    if t_ref is None:
        print(t_ref.iso)
        sunset_time = observer.sun_set_time(t_ref)
        t_ref = sunset_time #+ 120 * u.min
        
    sun_coord = get_sun(t_ref)
    sun_altaz = observer.altaz(t_ref, target=sun_coord)
    
    flat_field_az = (sun_altaz.az + 180. * u.deg) # % 360 * u.deg
    flat_field_alt = 60 * u.deg
    
    flat_field_altaz = SkyCoord(
        alt=flat_field_alt, az=flat_field_az, obstime=t_ref, location=location, frame="altaz"
    )
    
    print(flat_field_altaz.az.deg)
    
    
    flat_field_coord = flat_field_altaz.icrs
    
    print("COORD RA:", flat_field_coord.ra.hms)
    print("COORD DEC:", flat_field_coord.dec.dms)
       
    t_grid = t_ref + np.arange(0.0, 60.0, 1.0) * u.min
    
    point_res_main, point_res_rev = load_pointing_restrictions()
    
    fig, ax = plt.subplots()
    ax.plot(point_res_main["ha"], point_res_main["da"])
    ax.plot(point_res_rev["ha"], point_res_rev["da"])
    # plt.show()
    
    
    
    fig, ax = plt.subplots()
    ax.plot(point_res_main["ha"], point_res_main["dec"])
    ax.plot(point_res_rev["ha"], point_res_rev["dec"])
    ax.scatter(flat_field_altaz.az.deg, flat_field_coord.dec)
    plt.show()
    
suggest_flat_field()
















