Preparing observations
======================

Preparing an observation with the `obs_parser.py` GUI. Some test scripts can be found in /scripts/.
This feature is still preliminary, and needs to be implemented in the future.

* Run 
    ``python3 scripts/102_build_obs_config.py``

Here, you can choose a filename, and select the parameters for the observation (i.e target, FASU, DFOSC, and camera settings).

Certain settings have expected values, and they are listed at the bottomm of the GUI.

Once the parameters are chosen, a .yaml file will be saved in the output directory.
This file can then be read into the ``dk154_control`` framework.

* Then 
    ``python3 scripts/103_run_observations.py``

This script will read in the .yaml file, and parse the configuration to the appropriate ``dk154_control`` classes.