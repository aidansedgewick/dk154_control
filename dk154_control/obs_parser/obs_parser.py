import itertools
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Tuple

from logging import getLogger
import yaml

from astropy.coordinates import SkyCoord, Angle

from dk154_control.dfosc.dfosc import load_dfosc_setup
from dk154_control.tcs import ascol_constants

logger = getLogger("obs_config_parser")

TARGET_KEYS = ("name", "ra", "dec", "type", "obsnote")
FASU_KEYS = ("fasu_a", "fasu_b")
DFOSC_KEYS = ("grism", "slit", "filter")
EXPOSURE_KEYS = ("n_exp", "exptime", "binning")

ALL_KEYS = TARGET_KEYS + FASU_KEYS + DFOSC_KEYS + EXPOSURE_KEYS

KEY_SETS = {
    "TARGET": TARGET_KEYS,
    "FASU": FASU_KEYS,
    "DFOSC": DFOSC_KEYS,
    "EXPOSURE (CCD3)": EXPOSURE_KEYS,
}

COMMENTS = {
    "name": "name of target/observation (used as filename)",
    "type": "eg DARK, SCIENCE, FLAT, BIAS, LAMP ?",
    "obsnote": "other short note about the obs (<80 char)",
    "fasu_a": "filter name (eg. 'V') - NOT filter pos (eg. 1)",
    "n_exp": "how many repeat exposures?",
    "exptime": "in sec",
}

ARRAY_KEYS = ("fasu_a", "fasu_b", "grism", "slit", "filter", "binning")


KW_EMPTY = "empty"
N_CHAR = 20

FASU_A_INVERTED = {v: k for k, v in ascol_constants.WARP_CODES.items()}
FASU_B_INVERTED = {v: k for k, v in ascol_constants.WBRP_CODES.items()}

DFOSC_SETUP = load_dfosc_setup()

try:
    DFOSC_SETUP = load_dfosc_setup()
except Exception as e:
    print("error in DFOSC setup!")
    DFOSC_SETUP = {}

EXPECTED_VALUES = {
    "fasu_a": list(FASU_A_INVERTED.keys()),
    "fasu_b": list(FASU_B_INVERTED.keys()),
    "type": ["DARK", "SCIENCE", "FLAT", "BIAS", "LAMP", "FLAT,WAVE", "FLAT,SKY"],
    "binning": ["1x1 ONLY!"],
}

for wheel, positions in DFOSC_SETUP.items():
    EXPECTED_VALUES[wheel] = list(positions.keys())

GUI_DESCRIPTION = (
    "Enter values for each parameter.\n"
    "Provide a filename, and output directory. Missing directories will be created. File suffixes will be changed to '.yaml'"
    "Check the config for some errors with 'Check config'. Note that this will NOT prevent you from writing any malformed configs.\n"
    "Use 'array mode' to create a parameter grid of configurations.\n"
    ""
)


def format_ra_dec(ra, dec) -> Tuple[str, str]:
    alpha = Angle(ra, unit="deg")
    delta = Angle(dec, unit="deg")

    a_hms = alpha.hms
    d_dms = delta.dms

    a_str = f"{a_hms.h:02d}{a_hms.m:02d}{a_hms.s:.02.2f}"
    d_str = f"{d_dms.d:+02d}{d_dms.m:02d}{d_dms.s:.02.2f}"

    return a_str, d_str


def check_constants():
    unexpected_comments_keys = [k for k in COMMENTS.keys() if k not in ALL_KEYS]
    if unexpected_comments_keys:
        msg = f"UNEXPECTED KEYS in 'COMMENTS' constant:\n    {unexpected_comments_keys}"
        logger.warning(msg)
    unexpected_array_keys = [k for k in ARRAY_KEYS if k not in ALL_KEYS]
    if unexpected_array_keys:
        msg = f"UNEXPECTED KEYS in 'ARRAY' constant:\n    {unexpected_array_keys}"
        logger.warning(msg)

    unexpected_expvals_keys = [k for k in EXPECTED_VALUES if k not in ALL_KEYS]
    if unexpected_array_keys:
        msg = f"UNEXPECTED KEYS in 'EXPECTED_VALUES' constant:\n    {unexpected_expvals_keys}"
        logger.warning(msg)

    pass


MW_ICO_PATH = Path(__file__).parent / "mw_white.png"


def get_default_config():
    config = {k: KW_EMPTY for k in ["fasu_a", "fasu_b", "grism", "slit", "filter"]}
    config["n_exp"] = 1
    config["binning"] = "1x1"
    return config


def product_dict(config: dict):
    """
    Cartesian product of dict.

    ALL VALUES MUST BE ITERABLE (ie, at least 1-element list).

    eg.
    >>> d = {"a": [100], "b": [1,2], "c": [10, 20]}
    >>> print(product_dict(d))
    """
    for key, val in config.items():
        if not isinstance(val, list):
            logger.warning(f"{key} will fail - {val} needs to be iterable.")
    return [c for c in product_kwargs(**config)]


def product_kwargs(**kwargs):
    """Cartesian product of kwargs"""
    keys = kwargs.keys()
    for combination in itertools.product(*kwargs.values()):
        yield {k: v for k, v in zip(keys, combination)}


def check_ra_dec(ra, dec, format="decimal"):
    warning_messages = []
    if not ra or not dec:
        msg = f"ra or dec is empty!"
        # logger.warning(msg)
        warning_messages.append(msg)
    else:
        try:
            ra = float(ra)
            if ra < 0.0 or ra > 360.0:
                msg = f"ra={ra} outside range 0.0 < ra < 360.0"
                # logger.warning(msg)
                warning_messages.append(msg)
        except ValueError as e:
            msg = f"couldn't convert ra={ra} to float!"
            logger.warning(msg)
            warning_messages.append(msg)
        try:
            dec = float(dec)
            if abs(dec) > 90:
                msg = f"dec={dec} outside range -90.0 < dec < 90.0"
                # logger.warning(msg)
                warning_messages.append(msg)
        except ValueError as e:
            msg = f"couldn't convert dec={dec} to float!"
            # logger.warning(msg)
            warning_messages.append(msg)

    return warning_messages


def check_observation_config(observation_config):

    warning_messages = []

    unexpected_keys = set(observation_config.keys()) - set(ALL_KEYS)
    if unexpected_keys:
        msg = f"\033[36;1mUNEXPECTED KEYS:\033[0m\n {unexpected_keys}"
        # logger.warning(msg)
        warning_messages.append(msg)
    missing_keys = set(ALL_KEYS) - set(observation_config.keys())
    if missing_keys:
        msg = f"\033[36;1mMISSING KEYS:\033[0m\n {missing_keys}"
        # logger.warning(msg)
        warning_messages.append(msg)

    ra = observation_config.get("ra", None)
    dec = observation_config.get("dec", None)
    ra_dec_messages = check_ra_dec(ra, dec)
    warning_messages.extend(ra_dec_messages)

    fasu_a = observation_config.get("fasu_a", None)
    fasu_b = observation_config.get("fasu_b", None)
    dfosc_grism = observation_config.get("grism", None)
    dfosc_slit = observation_config.get("slit", None)
    dfosc_filter = observation_config.get("filter", None)

    using_fasu = fasu_a != KW_EMPTY or fasu_b != KW_EMPTY
    fasu_empty = fasu_a == KW_EMPTY and fasu_b == KW_EMPTY
    using_dfosc = (
        dfosc_grism != KW_EMPTY or dfosc_slit != KW_EMPTY or dfosc_filter != KW_EMPTY
    )
    dfosc_empty = (
        dfosc_grism == KW_EMPTY and dfosc_slit == KW_EMPTY and dfosc_filter == KW_EMPTY
    )

    if not fasu_a or not fasu_b:
        msg = (
            "Specify empty FASU wheels explicitly:\n"
            "    'fasu_a: empty', 'fasu_b: empty'"
        )
        # logger.warning(msg)
        warning_messages.append(msg)

    for wheel in ["fasu_a", "fasu_b", "grism", "slit", "filter"]:
        wheel_val = observation_config.get(wheel)
        exp_vals = EXPECTED_VALUES.get(wheel, None)
        if exp_vals is not None:
            if wheel_val not in exp_vals:
                msg = (
                    f"Unknown value {wheel.upper()}={wheel_val}:\n expected {exp_vals}"
                )
                # logger.warning(msg)
                warning_messages.append(msg)

    if fasu_a != KW_EMPTY and fasu_b != KW_EMPTY:
        msg = f"unexpected combination of FASU A='{fasu_a}' and FASU B='{fasu_b}'"
        # logger.warning(msg)
        warning_messages.append(msg)

    if dfosc_grism is None or dfosc_filter is None or dfosc_slit is None:
        msg = (
            "specify empty DFOSC wheels explicitly:\n"
            "    'grism: empty', 'slit: empty', 'filter: empty'"
        )
        # logger.warning(msg)
        warning_messages.append(msg)

    if using_fasu and using_dfosc:
        msg = "Unexpected combination of FASU and DFOSC settings"
        # logger.warning(msg)
        warning_messages.append(msg)

    if fasu_empty and dfosc_empty:
        msg = "All FASU and DFOSC wheels are empty!"
        # logger.warning(msg)
        warning_messages.append(msg)

    return warning_messages


class ObservationParser:

    def __init__(self):
        check_constants()

    @classmethod
    def check_config_file(cls, filepath):
        with open(filepath, "r") as f:
            observation_config = yaml.load(f, loader=yaml.FullLoader)
        return cls.check_config(observation_config)

    @classmethod
    def check_config(cls, observation_config):
        return check_observation_config(observation_config)

    @classmethod
    def check_array_config(cls, array_config):
        warning_messages = []
        config_list = cls.process_array_config(array_config)
        for config in config_list:
            msgs = cls.check_config(config)
            new_msgs = [m for m in msgs if m not in warning_messages]
            warning_messages.extend(new_msgs)
        return warning_messages

    @staticmethod
    def write_formatted_config(obs_config: dict, filepath: Path):
        lines = []

        # Loop over each GROUP of keywords...
        for set_name, key_set in KEY_SETS.items():
            lines.append(f"# {set_name}\n")

            # format each key within the group.
            for key in key_set:
                val = obs_config.get(key, "")
                line = f"{key}: {val}"
                comm = COMMENTS.get(key, None)
                if comm is not None:
                    blank = " " * (N_CHAR - len(line))
                    line = line + blank + f"# {comm}"
                lines.append(line + "\n")
            lines.append("\n")

        with open(filepath, "w+") as f:
            f.writelines(lines)

    @classmethod
    def write_blank_observation_config(cls, filepath: Path):
        config = get_default_config()
        return cls.write_formatted_config(config, filepath)

    # @classmethod
    # def process_array_config_from_file(cls, filepath: Path):
    #     with open(filepath, "r") as f:
    #         array_config = yaml.load(f, loader=yaml.FullLoader)
    #     return cls.process_array_config(array_config)

    # @classmethod
    # def process_array_config(cls, array_config: dict):
    #     for config in product_dict(array_config):
    #         cls.write_formatted_config(config)

    @classmethod
    def process_array_config(cls, config: dict):
        processed_config = {}
        for key, val in config.items():
            if not isinstance(val, list):
                val = [val]
            processed_config[key] = val
        return product_dict(processed_config)

    @classmethod
    def write_array_config(cls, array_config: dict, filepath: Path, idx_start=0):
        filepath = Path(filepath)
        suffix = filepath.suffix
        config_list = cls.process_array_config(array_config)

        for ii, config in enumerate(config_list, idx_start):
            filename_ii = f"{filepath.stem}_{ii:03d}"
            filepath_ii = (filepath.parent / filename_ii).with_suffix(suffix)
            cls.write_formatted_config(config, filepath_ii)

    @classmethod
    def write_blank_array_config(cls):
        pass


class ConfigBuilderGui:
    def __init__(self):
        self.main_window = tk.Tk()
        self.main_window.title("Prep DK154 observations")

        check_constants()

        try:
            img = tk.PhotoImage(file=MW_ICO_PATH)
            self.main_window.wm_iconphoto(False, img)
        except Exception as e:
            pass

        self.window = self.main_window

        # window = tk_tix.ScrolledWindow(master=main_window)
        # window.pack()

        self.window.rowconfigure(0, minsize=200)
        self.window.columnconfigure(0, weight=1, minsize=200)

        self.entry_widget_lookup = {}
        self.array_status_var_lookup = {}
        self.array_status_box_lookup = {}

        self.initialise_header()
        self.initialise_body()
        self.initialise_footer()

    def initialise_header(self):
        ### HEAD

        head_frame = tk.Frame(master=self.window)
        head_frame.grid(row=0, column=0, sticky="nsew")

        title_frame = tk.Frame(master=head_frame, name="frame_head")
        title_frame.grid(row=0, column=0, sticky="nsew")

        title_text = "Prepare YAML files for DK154 observations."
        title_label = tk.Label(master=title_frame, text=title_text)
        title_label.grid(row=0, column=0, sticky="nw", padx=5, pady=5)
        title_descr = tk.Message(master=title_frame, text=GUI_DESCRIPTION)
        title_descr.grid(row=1, column=0, sticky="nsew")

        output_frame = tk.Label(master=head_frame)
        output_frame.grid(row=1, column=0, sticky="nsew")

        output_frame.columnconfigure(index=0, minsize=20)

        output_loc_frame = tk.Frame(master=output_frame)
        output_loc_frame.grid(row=0, column=0, padx=5, pady=5)
        output_loc_frame.rowconfigure(index=[0, 1, 2], minsize=30)

        outdir_label = tk.Label(master=output_loc_frame, text="Output dir: ")
        outdir_label.grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.outdir_entry = tk.Entry(master=output_loc_frame, width=40)
        self.outdir_entry.grid(row=0, column=1)
        self.outdir_entry.insert(0, str(Path.cwd()))
        filename_label = tk.Label(master=output_loc_frame, text="Filename: ")
        filename_label.grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.filename_entry = tk.Entry(master=output_loc_frame, width=25)
        self.filename_entry.grid(row=1, column=1, sticky="w")

        output_button_frame = tk.Frame(master=output_frame)
        output_button_frame.grid(row=0, column=1, padx=20)
        output_button_frame.rowconfigure(index=[0, 1, 2], minsize=30)

        self.array_mode_var = tk.IntVar()
        self.array_mode_button = tk.Checkbutton(
            master=output_button_frame,
            variable=self.array_mode_var,
            text="Array mode",
            command=self.set_array_mode_command,
        )
        self.array_mode_button.grid(row=0, column=0, pady=5, sticky="w")

        output_check_button = tk.Button(
            master=output_button_frame,
            text="Check config",
            relief=tk.RAISED,
            width=10,
            command=self.check_config_command,
        )
        output_check_button.grid(row=1, column=0)

        output_write_button = tk.Button(
            master=output_button_frame,
            text="Write config",
            relief=tk.RAISED,
            width=10,
            command=self.write_config_command,
        )
        output_write_button.grid(row=2, column=0)

    def initialise_body(self):
        ### BODY

        body_frame = tk.Frame(master=self.window, name="frame_body")
        body_frame.grid(row=1, column=0)

        default_config = get_default_config()

        for ii, (key_set, keys) in enumerate(KEY_SETS.items()):
            keyset_frame = tk.Frame(
                master=body_frame,
                relief=tk.SUNKEN,
                borderwidth=3,
                padx=10,
                pady=10,
                name=f"frame_{key_set}",
            )
            keyset_frame.grid(row=ii, column=0, sticky="nsew")

            keyset_header_frame = tk.Frame(
                master=keyset_frame, name=f"frame_{key_set}_head"
            )
            keyset_header_frame.grid(row=0, column=0, sticky="ew")

            keyset_label = tk.Label(master=keyset_header_frame, text=key_set)
            keyset_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")

            keyset_entry_frame = tk.Frame(
                master=keyset_frame, name=f"frame_{key_set}_body"
            )
            keyset_entry_frame.grid(row=1, column=0)

            keyset_entry_frame.columnconfigure(index=0, minsize=80, weight=1)
            keyset_entry_frame.columnconfigure(index=1, minsize=80, weight=1)
            keyset_entry_frame.columnconfigure(index=2, minsize=80, weight=2)

            for jj, key in enumerate(keys, 1):
                key_label = tk.Label(master=keyset_entry_frame, text=f"{key}: ")
                key_label.grid(row=jj, column=0, sticky="e")
                key_entry = tk.Entry(master=keyset_entry_frame, width=20, name=key)
                key_entry.bind(
                    "<1>", lambda e: self.update_expected_values_label(event=e)
                )

                key_entry.grid(row=jj, column=1, sticky="w")

                default_value = default_config.get(key)
                if default_value is not None:
                    key_entry.insert(0, default_value)

                self.entry_widget_lookup[key] = key_entry

                if key in ARRAY_KEYS:
                    key_status_var = tk.IntVar()
                    key_status_box = tk.Checkbutton(
                        master=keyset_entry_frame, variable=key_status_var
                    )
                    key_status_box.configure(state=tk.DISABLED)
                    key_status_box.grid(row=jj, column=2)
                else:
                    key_status_box = None
                    key_status_var = tk.IntVar(value=0)

                self.array_status_box_lookup[key] = key_status_box
                self.array_status_var_lookup[key] = key_status_var

                comm = COMMENTS.get(key, None)
                if comm is not None:
                    key_comm = tk.Label(master=keyset_entry_frame, text=comm)
                    key_comm.grid(row=jj, column=3, sticky="w", padx=5)

    ### FOOT

    def initialise_footer(self):
        foot_frame = tk.Frame(master=self.window)
        foot_frame.grid(row=2, column=0, sticky="ew")

        foot_frame.rowconfigure(index=0, minsize=80)

        footnotes_frame = tk.Frame(master=foot_frame, name="frame_foot")
        footnotes_frame.grid(row=0, column=0, sticky="ew")

        self.footnotes_label = tk.Label(master=footnotes_frame, text="")
        self.footnotes_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

    def gather_config_from_entry_widgets(self):

        config_mapping = {}
        for key, entry_widget in self.entry_widget_lookup.items():
            if self.array_mode_var.get():
                if self.array_status_var_lookup[key].get():
                    values = [v.strip() for v in entry_widget.get().split("-")]
                else:
                    values = [str(entry_widget.get()).strip()]
                config_mapping[key] = values
            else:
                config_mapping[key] = str(entry_widget.get()).strip()
        return config_mapping

    def check_config_command(self):
        config = self.gather_config_from_entry_widgets()

        if self.array_mode_var.get():
            warning_messages = ObservationParser.check_array_config(config)
        else:
            warning_messages = ObservationParser.check_config(config)

        if warning_messages:
            warning_box = tk.Toplevel()
            warning_box.title("CONFIG WARNINGS")

            warning_frame = tk.Frame(master=warning_box)
            # warning_frame.rowconfigure(index=0, minsize=100)
            warning_frame.columnconfigure(index=0, minsize=200)
            warning_frame.grid(row=0, column=0, sticky="ew")
            for ii, msg in enumerate(warning_messages):
                msg_label = tk.Label(master=warning_frame, text=msg)
                msg_label.grid(row=ii, column=0, sticky="w")
            self.footnotes_label.configure(text="Warnings on config check!")
            self.footnotes_label.after(3000, self.empty_footnote_label)
            warning_box.mainloop()
        else:
            self.update_footnote_label(text="No warnings on config check...")
            self.footnotes_label.after(3000, self.empty_footnote_label)

    def empty_footnote_label(self):
        self.footnotes_label.configure(text="")

    def update_footnote_label(self, text):
        self.footnotes_label.configure(text=text)

    def update_expected_values_label(self, event):
        """
        TODO: see if it's possible to update to 'command' over 'bind'...
        """
        key = str(event.widget).split(".")[-1]
        expected_values = EXPECTED_VALUES.get(key, None)
        if expected_values is not None:
            text = "Expected values: " + ", ".join(expected_values)
        else:
            text = ""
        self.update_footnote_label(text=text)
        pass

    def write_config_command(self):

        outdir = Path(self.outdir_entry.get())
        outdir.mkdir(parents=True, exist_ok=True)

        filename = self.filename_entry.get()
        if not filename:
            warning_box = tk.Toplevel(height=100, width=150)
            warning_box.title("CONFIG WARNINGS")

            warning_frame = tk.Frame(warning_box)
            warning_frame.grid(row=0, column=0, sticky="ew")
            warning_frame.rowconfigure(index=0, minsize=100)
            warning_frame.columnconfigure(index=0, minsize=200)

            msg_label = tk.Label(master=warning_frame, text="No filename!")
            msg_label.grid(row=0, column=0)
            warning_box.mainloop()
            return

        filepath = outdir / filename
        if filepath.suffix not in (".yml", ".yaml"):
            filepath = filepath.with_suffix(".yaml")

        config = self.gather_config_from_entry_widgets()

        if self.array_mode_var.get():
            ObservationParser.write_array_config(config, filepath)
        else:
            ObservationParser.write_formatted_config(config, filepath)
        self.update_footnote_label(text="Config written!")
        self.footnotes_label.after(3000, self.empty_footnote_label)

    def set_array_mode_command(self):
        if self.array_mode_var.get():
            for key, checkbox in self.array_status_box_lookup.items():
                if checkbox is not None:
                    checkbox.configure(state=tk.NORMAL)
            msg = "array mode uses DASH separated list:\n eg. fasu_b: U - V - B"
            self.update_footnote_label(text=msg)
        else:
            for key, checkbox in self.array_status_box_lookup.items():
                if checkbox is not None:
                    checkbox.configure(state=tk.DISABLED)
            self.empty_footnote_label()

    @classmethod
    def main(cls):
        obs_window = cls()
        obs_window.window.mainloop()
