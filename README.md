# dk154_control

Python wrappers for controlling the Danish-1.54m telescope.

### Install

Ideally you should start a new python environment for this project.

eg. `python3 -m virtualenv ctrl_env`
then. `source ctrl_env/bin/activate`
(do the source step every time)

Clone this repository: `git clone https://github.com/aidansedgewick/dk154-control.git`,
then `cd` into `dk154-control`

Now install:

`python3 -m pip install -r requirements.txt -e .`

(The `-e` flag is developer mode so you can continue to edit the source code)

### Interacting with the telescope:

use the `Ascol` class. eg.

```
from dk154_control.tcs.ascol import Ascol

with Ascol() as ascol:
    ra, dec, tel_pos = ascol.trrd() # see Ascol docs for full list of commands.
    print(f"ra={ra}, dec={dec}, tel. pos={tel_pos}")
```


Not all the ASCOL commands are implemented as above. If there's one that's not
implemented that you want to use, you can use eg.
```
result = ascol.get_data("TRRD")
print(result)
```

The `with Ascol() as ascol:` statement is preferred over just `ascol = Ascol()`
as this way, the socket connection to the server is nicely closed on exit 
(even if there is an Error/Exception)


### Interacting with the camera

Use the `Ccd3` class. eg.


```ccd3 = Ccd()```
It's not so important to use Ccd() in a `with` block, as there are no connections 
to close.

Take and exposure:

```
import time
from dk154_control.camera.ccd3 import Ccd3

ccd3 = Ccd3()

ccd_state = ccd3.get_ccd_state()
print(f"CCD state before exposure: {ccd_state}")

exp_time = 10.0 # sec

# Hopefully there will be a nicer way to set parameters in the future...
exp_parameters = {}
exp_parameters["CCD3.exposure"] = exp_time # exp_time [sec]
exp_parameters["CCD3.IMAGETYP"] = "LIGHT" # one of "LIGHT", "DARK", "BIAS", "FLAT"
exp_parameters["CCD3.OBJECT"] = "SN 1572" # What are you observing?
exp_parameters["WASA.filter"] = "empty" 
exp_parameters["WASB.filter"] = "empty"

ccd3.set_exposure_parameters(exp_parameters)

filename = f"test_exposure_001.fits"
ccd3.start_exposure(file_name)

print("wait for exposure to finish...")
time.sleep(exp_time + 5.0) # wait!
# Now check the directory where you expect the file to have been saved.

ccd_state = ccd3.get_ccd_state()
print("CCD state after exposure: {ccd_state}")

```

### Interacting with DFOSC

Use the `Dfosc` class. eg.

```
from dk154_control.dfosc.dfosc import Dfosc
import yaml

dfosc_setup = yaml.load(open('dk154_control/dfosc/dfosc_setup.yaml'), Loader=yaml.FullLoader)

with Dfosc() as dfosc:
    dfosc.grism_goto(dfosc_setup[grism]['empty']) # move grism wheel into 'empty' position
    dfosc.aperture_goto(dfosc_setup[slit]['1.5']) # move aperture wheel to 1.5" slit
    dfosc.filter_goto(dfosc_setup[filter]['empty0']) # move filter wheel to first empty position

    grism_pos = dfosc.gp()
    slit_pos = dfosc.ap()
    filter_pos = dfosc.fp()

    # print step positions of the wheels
    print(f'Grism position: {grism_pos}')
    print(f'Aperture position: {slit_pos}')
    print(f'Filter position: {filter_pos})  
```
#### Calibration Lamps

Use the `WaveLamps` class. eg.

```
from dk154_control.lamps.wave_lamps import WaveLamps

lamps = WaveLamps()
lamps.turn_on_lamps()
time.sleep(30) # let the lamps warm up/turn on completely
lamps.turn_off_lamps()
```

### Running test scripts

There are a handful of test scripts in test scripts.

run eg. `python3 test_scripts/001_test_imports.py`.
You can also run with a debug mode which prints the 'raw' response from ASCOL/CC3.
eg. `python3 test_scripts/002_test_imports.py --debug`.


#### 001_test_import.py

tests that the Ascol() and Ccd() classes import and init properly.

#### 002_test_status_commands.py

tests a number of commands which read the status of the telescope, FASU wheels.

#### 003_test_movement.py

test moving the telescope. Read it's current position, nudge it by a degree and go.
CHECK THE DESTINATION COORD IS SENSIBLE - if not, kill the script and
hard code the destination in the script for now...

#### 004_test_FASU.py
    
test reading state/pos,  and movement of FASU filter wheels.

#### 005_test_CCD3.py

test exposing the camera.

NOTE1: CCD3 also has "WASB.filter"/"WASA.filter" option
Unsure if this is just for storing a string in FITS header of output, or actually
changing the wheel position. Don't know which is the more likely.
This script prints all.

NOTE2: ASCOL has command "open shutter". Is this shutter separate to CCD3 shutter?!
If so - uncomment OPEN SHUTTER and CLOSE SHUTTER lines in this script...

#### 006_test_meteo.py

test meteorology instrument commands.

#### 007_test_convenience.py

TBW

#### 008_test_dfosc_wheels.py

Checks if DFOSC wheels are ready, and returns their current positions

#### 010_test_dfosc_init.py

Initializes all the DFOSC wheels, and waits 40 seconds for a compete rotation to occur. Initializing the wheels should be done after a power outage/reset.

#### 011_test_dfosc_flats.py

Script for taking sky flats. 
Useage: python3 testing_scripts/011_test_dfosc_flats.py -n [nframes] -g [grism] -s [slit] -f [filter]
The script will loop through selected grism, slit, and filter orientations, and take the specified number of frames per position.

#### 012_test_dfosc_arc.py

Script for running through various arc calibration frames. Hg lamps will turn on at the start, and the user specified grisms, slits, and filters will be looped through, then the lamps will turn off. It is recommended to run this script once for many orientations rather than multiple times. For all slit/grism positions (and empty filter position), this will take around 90 minutes to run through. Example: python3 testing_scripts/012_test_dfosc_arc.py -g 3 5 6 7 8 14 15 -s 1.0 1.5 2.0 2.5 3.0 5.0 -f empty0

#### 013_test_dfosc_acquisition.py

Take an acquisition frame with slit in place, without a grism. Take for bright targets 10 < mag < 15 (used to check object alignment in slit). Example: python3 testing_scripts/013_test_dfosc_acquisition.py -s 2.5 -m 13

#### 101_status_loop.py

loop every 'n' seconds, log results from a set of status commands.


#### 998_startup.py
    
*guide only* - unsure exactly what commands are needed to fully initialise telescope.
    
#### 999_shutdown.py
    
*guide only* - unsure exactly what commands are needed to fully/safely shutdown telescope.

#### dfosc_flat_direct.py

Similar to 011_test_dfosc_flats.py expect it connects to dfosc directly (without Dfosc class).

#### dfosc_target_acq.py

Similar to 013_test_dfosc_acquisition.py except it connects directly via telnet. 

#### dfosc_arc_calib.py

Script used to directly connect to dfosc, and the cyberpowerbar. Similar to 012_test_dfosc_arc.py except it bypasses the conventions used by Dfosc, and WaveLamp classes. See comments in script. 

### Mock telescope interactions

There is a separate repo, `dk154_mock` (*still in early dev!*) which can be used 
to test sending commands to mock servers, and recieving responses.

Currently this is only for the Ascol class - but more later.













