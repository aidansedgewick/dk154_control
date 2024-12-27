from dk154_control.tcs import ascol_constants
from dk154_control.dfosc import load_dfosc_setup


COMMENTS = {
    "object_name": "name of target/observation (used as filename)",
    "remote_dir": "on lin1 note that '/data/' is ALWAYS prepended.",
    "imagetyp": "eg DARK, SCIENCE, FLAT, BIAS, LAMP ?",
    "obsnote": "other short note about the obs (<80 char)",
    "fasu_a": "FASU A wheel. Remember to EMPTY for spectroscopic obs!",
    "fasu_b": "FASU B wheel. Remember to EMPTY for spectroscopic obs!",
    "dfosc_grism": "grism number eg. G15 = grism #15.",
    "dfosc_aperture": "aperture, eg. 'A15' = 1.5'' slit.",
    "dfosc_filter": "Filter wheel currently contains crossdispersion grisms.",
    "n_exp": "how many repeat exposures? Integer",
    "exp_time": "in sec (float, minimum 0.002sec)",
    "n_discard": "how many short (0.005s) discard frames to take, so that CCD is ready",
    "binning": "CURRENTLY HAS NO EFFECT!",
    "imagetyp": "CCD3 requires one of these options.",
    "mod_imagetyp": "Header key 'IMAGETYP' is changed on backup",
}


### ================= DOME ACTIONS FRAME ================ ###

TEL_BUTTONS = {
    "tel_on": ("ON", "TEON 1"),  # Text on button, then command to execute
    "tel_off": ("OFF", "TEON 0"),
    "tel_init": ("INIT", "TEIN"),
    "tel_stop": ("TRACK", "TETR 1"),
    "tel_park": ("PARK", "TEPA"),
}

CASS_BUTTONS = {
    "cass_open": ("OPEN", "FCOP 1"),  # Text on button, then command to execute
    "cass_close": ("CLOSE", "FCOP 0"),
    "cass_stop": ("STOP", "FCST"),
}

MIRROR_BUTTONS = {
    "mirror_open": ("OPEN", "FMOP 1"),  # Text on button, then command to execute
    "mirror_close": ("CLOSE", "FMOP 0"),
    "mirror_stop": ("STOP", "FMST"),
}


DOME_BUTTONS = {
    "dome_init": ("INIT", "DOIN"),  # Text on button, then command to execute
    "dome_park": ("PARK", "DOPA"),
    "dome_stop": ("STOP", "DOST"),
    "dome_auto": ("AUTO", "DOAM"),
}

SLIT_BUTTONS = {
    "slit_open": ("OPEN", "DOSO 1"),  # Text on button, then command to execute
    "slit_close": ("CLOSE", "DOSO 0"),
}

DOME_ACTION_BUTTONS = {
    "Telescope": TEL_BUTTONS,
    "Dome": DOME_BUTTONS,
    "Cass. flap": CASS_BUTTONS,
    "Mirror flap": MIRROR_BUTTONS,
    "Dome slit": SLIT_BUTTONS,
}

### ======================= WHEELS FRAME ======================= ###

WHEEL_LABEL_TEXT = {
    "fasu_a": "FASU A",
    "fasu_b": "FASU B",
    "dfosc_grism": "DFOSC grism",
    "dfosc_aperture": "DFOSC aperture",
    "dfosc_filter": "DFOSC filter",
}

FASU_A_INVERTED = {v: k for k, v in ascol_constants.WARP_CODES.items()}
FASU_B_INVERTED = {v: k for k, v in ascol_constants.WBRP_CODES.items()}
DFOSC_SETUP = load_dfosc_setup()

WHEEL_OPTIONS = {
    "fasu_a": list(FASU_A_INVERTED.keys()),
    "fasu_b": list(FASU_B_INVERTED.keys()),
}
for wheel, positions in DFOSC_SETUP.items():
    key = f"dfosc_{wheel}"
    WHEEL_OPTIONS[key] = list(positions.keys())


def check_wheel_options():
    expected_wheel_options_keys = set(WHEEL_LABEL_TEXT.keys())
    wheel_options_keys = set(WHEEL_OPTIONS.keys())
    if wheel_options_keys != expected_wheel_options_keys:
        raise ValueError(
            f"In control_gui_settings.py:\n"
            f"    Wheel options are: {wheel_options_keys}.\n"
            f"    Expected: {expected_wheel_options_keys}\n"
            f"Check WHEEL_LABEL_TEXT and WHEEL_OPTIONS construction."
        )


### ========================= CCD3 FRAME ========================###

CCD3_LABEL_TEXT = {
    "remote_dir": "Directory",
    "object_name": "Object name",
    "exp_time": "Exposure time (sec)",
    "n_exp": "Num. exposures",
    "shutter": "Shutter",
    "n_discard": "Num. discard",
    "binning": "CCD binning",
    "imagetyp": "Image type",
    "mod_imagetyp": "Mod. image type",
}

# If key is present in OPTIONS, it is shown as a ttk.Combobox (dropdown menu).
# MUST ALSO BE PRESENT IN CCD3_LABEL_TEXT!!
CCD3_OPTIONS = {
    "imagetyp": ["LIGHT", "DARK", "BIAS", "FLAT"],
    "binning": ["1x1"],
    "shutter": ["OPEN", "CLOSED"],
}

CCD3_SHUTTER_CODES = {"OPEN": "0", "CLOSED": "1", "0": "0", "1": "1"}

# only for free-text widgets (ie, not in both CCD_OPTIONS and CCD3_DEFAULT_OPTIONS.
CCD3_DEFAULT_OPTIONS = {
    "n_exp": 1,
    "n_discard": 2,
}


### ======================= STATUS WIDGETS ===================== ###

# keys in these dictionaries should match the attributes in
# AscolStatus, DfoscStatus (and Ccd3Status when it is written)


BLINK_INTERVAL = 0.250  # s

TEL_STATUS_DATA_LABELS = {
    "remote_state": "Remote State [GLRE]",
    "safety_relay_state": "Safety relay [GLSR]",
    "telescope_state": "Telescope state [TERS]",
    "flap_cassegrain_state": "Cass. flap state [FCRS]",
    "flap_mirror_state": "Mirror flap state [FMRS]",
    "shutter_position": "Shutter pos. [SHRP]",
}

POINTING_STATUS_DATA_LABELS = {
    "current_ra": "Curr. R.A. (HHMMSS.SS)",
    "current_dec": "Curr. Dec (DDMMSS.SS)",
    "current_position": "Curr. pos. (E/W)",
}

DOME_STATUS_DATA_LABELS = {
    "dome_state": "Dome state [DORS]",
    "dome_position": "Dome position [DORA]",
    "dome_slit_state": "Dome slit state [DOSS]",
}

FASU_STATUS_DATA_LABELS = {
    "wheel_a_position": "Wheel A pos. [WARP]",
    "wheel_b_position": "Wheel B pos. [WBRP]",
    "wheel_a_state": "Wheel A state [WARS]",
    "wheel_b_state": "Wheel B state [WBRS]",
}

DFOSC_STATUS_DATA_LABELS = {
    "grism_ready": "Grism ready [g]",
    "grism_position": "Grism pos. [gp]",
    "grism_name_guess": "Grism name (?)",
    "aper_ready": "Aper. ready [a]",
    "aper_position": "Aper. pos. [ap]",
    "aper_name_guess": "Aper. name (?)",
    "filter_ready": "Filter ready [a]",
    "filter_position": "Filter pos. [ap]",
    "filter_name_guess": "Filter name (?)",
}

CCD3_STATUS_DATA_LABELS = {
    "ccd3_status_code": "CCD3 status (code)",
    "ccd3_status_label": "CCD3 status",
}

BLINKING_STATUS_LABELS = {
    "flap_cassegrain_state": {"stopped": "red", "opening": "green", "closing": "green"},
    "flap_mirror_state": {"stopped": "red", "opening": "green", "closing": "green"},
    "dome_slit_state": {"stopped": "red", "opening": "green", "closing": "green"},
    "dome_state": {
        "parking": "green",
        "auto +": "green",
        "auto -": "green",
        "manual -": "green",
    },
    "wheel_a_position": {"rotating": "green"},
    "wheel_b_position": {"rotating": "green"},
    "wheel_a_state": {"positioning": "green", "stopped": "red"},
    "wheel_b_state": {"positioning": "green", "stopped": "red"},
    "grism_ready": {"n": "red"},
    "aper_ready": {"n": "red"},
    "filter_ready": {"n": "red"},
}

ASCOL_STATUS_DATA_LABELS = {
    **TEL_STATUS_DATA_LABELS,
    **DOME_STATUS_DATA_LABELS,
    **POINTING_STATUS_DATA_LABELS,
    **FASU_STATUS_DATA_LABELS,
}

STATUS_WIDGET_SUBSETS = {
    "col1": {
        "Telescope": TEL_STATUS_DATA_LABELS,
        "Dome": DOME_STATUS_DATA_LABELS,
        "Pointing": POINTING_STATUS_DATA_LABELS,
    },
    "col2": {
        "FASU wheels": FASU_STATUS_DATA_LABELS,
        "DFOSC_wheels": DFOSC_STATUS_DATA_LABELS,
        "CCD3": CCD3_STATUS_DATA_LABELS,
    },
}
