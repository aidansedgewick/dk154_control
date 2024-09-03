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

The Danish Faint Object Spectrograph and Camera (DFOSC), is comprised of three wheels, a filter wheel, grism wheel, and a slit wheel.
These wheels are controlled by the ``Dfosc`` class. 
The current slits, grisms, and filters in place are stored in the dfosc_setup.yaml file, and should be updated when changed. 
By loading in the .yaml, it is possible to select grisms, filters, and slits by name, rather than by number.
A typical command for moving the grism wheel, then reading the position of the wheel is:

.. code-block:: python

    grisms = yaml.load(open('dk154_control/dfosc/dfosc_setup.yaml'), Loader=yaml.FullLoader)['grism']

        with Dfosc() as dfosc:
            dfosc.gg(grisms['15'])
            time.sleep(10)
            dfosc.gp()

Here, grism #15 is selected, and after some time the position of the grism wheel is read.


CCD3 (Camera)
.............

The CCD3 camera is controlled by the ``Ccd3`` class. 
Only some of the known parameters are implemented, and a full list of possibilities should be documented in the future.
First, set the parameters of the camera using the `set_exposure_parameters` function, then with ``Ascol`` open the shutter, and with ``Ccd3``, `start_exposure``:

.. code-block:: python

    ccd3 = Ccd3()

    exp_params = {}
	exp_params['CCD3.exposure'] = str(exp_time)
	exp_params['CCD3.IMAGETYP'] = str(exp_type)
	exp_params['CCD3.OBJECT'] = str(obj_name)
	exp_params['WASA.filter'] = "0"
	exp_params['WASB.filter'] = "0"
    
    ccd3.set_exposure_parameters(params=exp_params)

    with Ascol() as ascol:
        ascol.shop('0')
        ccd3.start_exposure()

From here the files are currently saved on the lin1 machine outside the current date folder.

Note: these files are temporary and need to be transferred the target machine/destination as soon as possible. 

Lamps
.....

THe mercury calibration lamps are controlled by the ``WaveLamps`` class. 
The function `all_lamps_on` powers on outlets 5 & 6, and `all_lamps_off` turns them off.
These still need to be tested/changed on the .55 machine (see dfosc_arc_calib.py for the current implementation).

.. code-block:: python

    with WaveLamps() as lamps:
        lamps.all_lamps_on()
        lamps.all_lamps_off()

Note: Currently the calibration lamps are unplugged. A power outage may have caused the IP of the cyberpower bar to revert to a default IP.
It is better to leave lamps on longer, than constantly turning them on and off.
