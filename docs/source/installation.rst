Installation
============

Clone the repo
..............

* Clone this repository
   http clone is easiest:
   ``git clone https://github.com/aidansedgewick/dk154-control.git``

Set up a new virtual env
........................

If you have already done this, skip ahead...

* Start a new virtual env:
   ``python3 -m virtualenv env_control``
   This uses the ``virtualenv`` package

* Load the environment (do this every time):
   ``source env_control/bin/activate``

.. note::
   You may need to first install ``virtualenv``, use ``python -m pip install virtualenv``

.. warning::
   You might prefer another package manager (eg. conda). ``dk154_control`` has not been tested
   with anything other than ``pip``/``virtualenv``.

Install
.......

* Move to the directory
   ``cd dk154_control``

* Install the requirements
   ``python3 -m pip install -r requirements.txt``

   Installs ``numpy``, ``astropy``, ``pyyaml`` and some other useful tools.

* Install the actual package
   ``python3 -m pip install -e .``

   The ``-e`` (developer mode) flag allows you to modify the code.
   Additionally, it installs it 'in place' (not in eg. env_control/lib/python3.8/site-packages).

Requirements
............

* `Python <https://www.python.org/>_`

* `numpy <https://pypi.org/project/numpy/>_`

* `astropy <https://astropy.org/>_`

* `pyyaml <https://https://pypi.org/project/PyYAML/>_`

* `pysnmp <https://pysnmp.com/>_`