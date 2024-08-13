Usage
=====

There are four main controllers, ``Ascol``, ``Dfosc``, ``Ccd3``, and ``WaveLamps``.

DK154: convenient API
........................

Many common telscope operations are implemented in the ``DK154`` class.

For instance, moving to a given RA and Dec, defined by an ``astropy`` SkyCoord.

.. code-block::
    
    from astropy.coordinates import SkyCoord
    from dk154_control import DK154

    coord = SkyCoord(ra=60.0, dec=-30.0, unit="deg")
    tel_pos = "0" # east or west position
    
    with DK154() as dk154:
        result = dk154.move_telescope_and_wait(coord, tel_pos)
        #  


It is preferred to use the ``with`` syntax over directly 

ASCOL
.....

The ``Ascol`` class controls the telescope, dome, FASU wheels, and meteo tools.

Many of the ASCOL commands are implemented as methods in the ``Ascol`` class.
For instance, the Telescope Read RA and Dec (TRRD):

.. code-block:: python

    with Ascol() as ascol:
        ra, dec, telescope_pos = ascol.trrd()

Each method is implemented as the four 


DFOSC
.....

The Danish Faint Object Spectrograph and Camera.

CCD3 (Camera)
.............

Lamps
.....



