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

### Mock telescope interactions

There is a separate repo, `dk154_mock` (*still in early dev!*) which can be used 
to test sending commands to mock servers, and recieving responses.

Currently this is only for the Ascol class - but more later.













