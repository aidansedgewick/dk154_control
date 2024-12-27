import itertools
import threading
import time
import tkinter as tk
import traceback
from argparse import ArgumentParser
from pathlib import Path
from tkinter import ttk
from typing import Tuple

from logging import getLogger
import yaml

import numpy as np

import pandas as pd

from astropy import units as u
from astropy.coordinates import AltAz, Angle, EarthLocation, SkyCoord
from astropy.time import Time

from astroplan import Observer

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import dk154_control
from dk154_control import DK154, Ascol, Ccd3, Dfosc
from dk154_control.camera import take_multi_exposure, take_discard_frames
from dk154_control.dfosc.dfosc import load_dfosc_setup, DfoscStatus

from dk154_control.gui import control_gui_settings as gui_settings
from dk154_control.gui.gui_utils import load_pointing_restrictions
from dk154_control.tcs import ascol_constants
from dk154_control.tcs.ascol import AscolStatus
from dk154_control.utils import dec_dms_to_deg, ra_hms_to_deg, time_from_mjdstr_hhmmss

from dk154_control.obs_parser.obs_parser import check_constants

logger = getLogger("control_gui")

GRAPHICS_PATH = Path(__file__).parent / "graphics"


def get_warning_popup(text, title="WARNING") -> tk.Toplevel:
    popup = tk.Toplevel()
    popup.title(title)
    window = tk.Frame(master=popup)
    window.rowconfigure(0, minsize=100, pad=5)
    window.columnconfigure(0, minsize=100, pad=5)
    window.grid(row=0, column=0, padx=10, pady=10)

    label = tk.Label(master=window, text=text)
    label.grid(row=0, column=0)

    close_button = tk.Button(master=window, text="OK", command=popup.destroy, width=10)
    close_button.grid(row=1, column=0, sticky="nsew")
    return popup


class ControlGui:

    def __init__(self, test_mode=False, status_update_interval=2.0):
        self.root = tk.Tk()
        self.root.title("DK154 controller")
        self.set_icon()

        self.test_mode = test_mode
        self.status_update_interval = status_update_interval

        check_constants()

        self.window = tk.Frame(master=self.root, name="main")
        self.window.grid(row=0, column=0, sticky="nsew")

        self.window.rowconfigure(0, minsize=500, pad=5)
        self.window.columnconfigure(0, minsize=500, pad=5)

        self.location = EarthLocation.of_site("lasilla")  # TODO read from tel?

        self.coord_widget_lookup = {}
        self.wheel_widget_lookup = {}
        self.ccd3_widget_lookup = {}
        self.status_widget_lookup = {}
        self.status_last_updated_widget = None
        self.dome_action_widget_lookup = {}
        self.dome_action_commands = {}

        self.status_loop_var = tk.IntVar()
        self.main_rev_var = tk.StringVar()
        self.main_rev_var.set("0")

        # keeping track of the statis of all of the stuff.
        self.ascol_status = None
        self.dfosc_status = None
        self.ccd3_status = None
        self.status_data = {}

        # track if we can send new "wheels GO" command.
        self.wheels_moving = False

        # track if we have asked to stop exposures.
        self.stop_exposure_event = threading.Event()
        self.exposure_in_progress = False

        # pointing graphic
        self.latest_pointing = (None, None)
        self.latest_proposal = (None, None)

        self.init_header()
        self.init_body()
        self.init_footer()

        self.pointing_graphic_update_time = time.perf_counter()
        self.update_pointing_graphic()

        self.start_status_loop()
        self.update_all_status_widgets()

    def set_icon(self):
        mw_icon_path = GRAPHICS_PATH / "mw_white.png"
        # icon: Milky way icons created by Victoruler - Flaticon
        if mw_icon_path.exists():
            try:
                photo = tk.PhotoImage(file=mw_icon_path)
                self.root.wm_iconphoto(False, photo)
                self.root.iconbitmap(mw_icon_path)
            except Exception as e:
                logger.error(f"setting icon: {type(e).__name__}: {e}")

    def set_popup_location_and_show(self, popup: tk.Toplevel):
        self.root.update_idletasks()  # so that popup has size correctly set...

        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_w = self.root.winfo_width()
        root_h = self.root.winfo_height()

        win_w = popup.winfo_width()
        win_h = popup.winfo_height()

        # center the popup in the window...
        win_x = root_x + (root_w // 2 - win_w // 2)
        win_y = root_y + (root_h // 2 - win_h // 2)

        popup.attributes("-topmost", "true")
        popup.geometry(f"{win_w}x{win_h}+{win_x}+{win_y}")
        popup.mainloop()
        return

    def init_header(self):
        ### HEAD

        self.head_frame = tk.Frame(master=self.window, name="head")
        self.head_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        title_frame = tk.Frame(master=self.head_frame, name="title")
        title_frame.grid(row=0, column=0, sticky="nsew")
        self.head_frame.rowconfigure(0, weight=1)
        self.head_frame.columnconfigure(0, weight=1)

        title_label = tk.Label(master=title_frame, text="DK154 observations", font=24)
        title_label.grid(row=0, column=0, sticky="new")
        title_frame.rowconfigure(0, weight=1)
        title_frame.columnconfigure(0, weight=1)

        self.head_main = tk.Frame(master=self.head_frame, name="head_main")
        self.head_main.grid(row=1, column=0, sticky="nsew")
        self.head_frame.rowconfigure(1, weight=1)
        self.head_frame.columnconfigure(0, weight=1)

        self.init_status_frame()
        self.init_pointing_graphic_frame()
        # self.init_action_frame()

    def init_body(self):

        self.body_frame = tk.Frame(master=self.window, relief=tk.SUNKEN)
        self.body_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # self.init_parameters_frame()
        self.init_dome_actions_frame()
        self.init_coords_frame()
        self.init_wheels_frame()
        self.init_ccd3_frame()

    def init_footer(self):

        self.footer_frame = tk.Frame(master=self.window)
        self.footer_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        self.init_footer_comment()

    def init_status_frame(self):
        self.status_frame = tk.Frame(master=self.head_main, name="status")
        self.status_frame.grid(row=0, column=0, sticky="nsw", padx=5, pady=5)
        self.head_main.rowconfigure(0, weight=1)
        self.head_main.columnconfigure(0, weight=1)

        status_title = tk.Label(master=self.status_frame, text="Observatory status")
        status_title.grid(row=0, column=0)

        status_button_frame = tk.Frame(master=self.status_frame, name="status_buttons")
        status_button_frame.grid(row=1, column=0)

        status_loop_checkbox = tk.Checkbutton(
            master=status_button_frame,
            variable=self.status_loop_var,
            state=tk.ACTIVE,
            text="Loop updates?",
        )
        status_loop_checkbox.select()
        status_loop_checkbox.grid(row=0, column=0)
        update_status_button = tk.Button(
            master=status_button_frame, text="UPDATE", command=self.update_status_info
        )
        update_status_button.grid(row=0, column=1)

        time_frame = tk.Frame(master=self.status_frame)
        time_frame.grid(row=2, column=0, sticky="new")

        time_label = tk.Label(master=time_frame, text="Last updated: ")
        time_label.grid(row=0, column=0, sticky="nse")
        time_data = tk.Label(master=time_frame, text="<unavail>")
        time_data.grid(row=0, column=1, sticky="nsw")
        self.status_last_updated_widget = time_data

        status_main_frame = tk.Frame(master=self.status_frame)
        status_main_frame.grid(row=3, column=0)
        status_title.rowconfigure(1, minsize=500)
        status_title.columnconfigure(0, minsize=500)

        for jj, (col_name, column_subsets) in enumerate(
            gui_settings.STATUS_WIDGET_SUBSETS.items()
        ):

            status_frame_column = tk.Frame(
                master=status_main_frame, name=f"status_column_{jj}"
            )
            status_frame_column.grid(row=0, column=jj, sticky="new")

            for ii, (subset_header, key_subset) in enumerate(column_subsets.items()):
                frame_name = subset_header.replace(" ", "_").lower()
                status_subset_frame = tk.Frame(
                    master=status_frame_column,
                    relief=tk.SUNKEN,
                    borderwidth=3,
                    # name=frame_name,
                )
                status_subset_frame.grid(row=ii, column=0, padx=5, pady=5)

                status_data_header = tk.Label(
                    master=status_subset_frame, text=subset_header
                )
                status_data_header.grid(row=0, column=0, sticky="nsew")

                status_data_frame = tk.Frame(
                    master=status_subset_frame, name=f"{frame_name}_data"
                )
                status_data_frame.grid(row=1, column=0, sticky="new", padx=2, pady=2)
                status_subset_frame.columnconfigure(0, minsize=300)

                for jj, (key, label) in enumerate(key_subset.items()):
                    static_label = tk.Label(master=status_data_frame, text=f"{label}:")

                    static_label.grid(row=jj, column=0, sticky="nse", padx=1, pady=2)

                    widget_label = tk.Label(
                        master=status_data_frame, text="<to-enter>", borderwidth=1
                    )
                    widget_label.grid(row=jj, column=1, sticky="nsw")
                    self.status_widget_lookup[key] = widget_label

    def init_pointing_graphic_frame(self):
        self.pointing_graphic_frame = tk.Frame(master=self.head_main)
        self.pointing_graphic_frame.grid(row=0, column=1)

        try:
            point_res_main, point_res_reverse = load_pointing_restrictions()
        except FileNotFoundError as e:
            print(e)
            point_res_main = None
            point_res_reverse = None
            tr = traceback.format_exc()
            popup = get_warning_popup(tr)
        self.point_res_main = point_res_main
        self.point_res_reverse = point_res_reverse

        self.fig = plt.Figure()
        self.pointing_ax = self.fig.add_axes([0.12, 0.1, 0.78, 0.8])
        self.twin_ax = self.pointing_ax.twinx()

        self.fig.set_facecolor("none")
        self.pointing_ax.set_facecolor("none")

        self.plot_pointing_restrictions()

        self.pointing_canvas = FigureCanvasTkAgg(
            self.fig, master=self.pointing_graphic_frame
        )
        graphic = self.pointing_canvas.get_tk_widget()
        graphic.grid(row=0, column=0)

    def plot_pointing_restrictions(self):
        if self.point_res_main is not None:
            xdat = self.point_res_main["ha"][:-1]
            ydat = self.point_res_main["da"][:-1]
            self.pointing_ax.plot(xdat, ydat, color="k")
        if self.point_res_reverse is not None:
            xdat = self.point_res_reverse["ha"][:-1]
            ydat = self.point_res_reverse["da"][:-1]
            self.pointing_ax.plot(xdat, ydat, color="k")

        yticks = -90 + np.arange(-5, 6, 1) * 30.0
        self.pointing_ax.set_yticks(yticks.astype(int))

        mod_yticks = np.array([y if y > -90.0 else -180.0 - y for y in yticks])
        self.twin_ax.set_yticks(yticks)
        self.twin_ax.set_yticklabels(mod_yticks.astype(int))
        self.twin_ax.set_ylim(self.pointing_ax.get_ylim())

        rev_kwargs = dict(ha="center", va="top", rotation=90.0)
        self.pointing_ax.text(250.0, -100, "<-- REVERSE", **rev_kwargs)

        main_kwargs = dict(ha="center", va="bottom", rotation=90.0)
        self.pointing_ax.text(250.0, -80, "MAIN -->", **main_kwargs)

        self.pointing_ax.axhline(-90.0, ls="--", color="k")
        self.pointing_ax.set_xlabel("Hour angle [deg]")

        self.pointing_ax.set_ylabel("D.A. [deg]")
        self.twin_ax.set_ylabel("Declination main/reverse [deg]")

    def update_pointing_graphic(self):
        dt = time.perf_counter() - self.pointing_graphic_update_time

        # if dt < 5.0:
        #    continue

        self.window.after(2500, self._perform_graphic_update)

    def get_current_time(self):
        if self.ascol_status is None:
            return None

        mjd_str = self.ascol_status.__dict__.get("mjd", None)
        time_str = self.ascol_status.__dict__.get("time_str", None)

        if mjd_str and time_str:
            obstime = time_from_mjdstr_hhmmss(mjd_str, time_str)
            return obstime
        return None

    def get_current_pointing(self) -> Tuple[SkyCoord, str]:

        curr_ra = self.status_data.get("current_ra", None)
        curr_dec = self.status_data.get("current_dec", None)
        curr_tel_pos = self.status_data.get("current_position", None)

        print(curr_ra, curr_dec, curr_tel_pos)

        if curr_ra and curr_dec and (curr_tel_pos is not None):
            curr_coord = SkyCoord(
                ra=ra_hms_to_deg(curr_ra) * u.deg, dec=dec_dms_to_deg(curr_dec) * u.deg
            )
            return curr_coord, curr_tel_pos
        else:
            return None, None

    def get_current_proposal(self) -> Tuple[SkyCoord, str]:

        prop_ra = self.coord_widget_lookup["ra_entry"].get()
        prop_dec = self.coord_widget_lookup["dec_entry"].get()
        prop_tel_pos = self.main_rev_var.get()
        if prop_ra and prop_dec:
            proposed_coord = SkyCoord(
                ra=ra_hms_to_deg(prop_ra) * u.deg, dec=dec_dms_to_deg(prop_dec) * u.deg
            )
            return proposed_coord, prop_tel_pos
        else:
            return None, prop_tel_pos

    def _perform_graphic_update(self):

        # if dt > 5.0:
        #
        #    return

        t_grid = Time.now() + np.linspace(0, 180, 100) * u.min

        obstime = self.get_current_time()

        self.pointing_ax.clear()

        if obstime:
            time_label = obstime.strftime("%y-%m-%d %H:%M:%S")
            txt = f"last updated: {time_label}"
            transform = self.pointing_ax.transAxes
            self.pointing_ax.text(
                0.5, 1.05, txt, transform=transform, ha="center", va="bottom"
            )

            observer = Observer(self.location)

            pointing = self.get_current_pointing()
            try:
                proposal = self.get_current_proposal()
            except:
                proposal = (None, None)

            if proposal[0] is not None:
                ha = observer.target_hour_angle(obstime, proposal[0]).deg

                dec = proposal[0].dec.deg
                if proposal[1] == "1":
                    dec = -90 + dec
                self.pointing_ax.scatter(ha, dec, color="black", marker="x")

            if pointing[0] is not None:
                ha = observer.target_hour_angle(obstime, pointing[0]).deg
                dec = pointing[0].dec.deg
                if pointing[1] == "1":
                    dec = -90 + dec
                self.pointing_ax.scatter(ha, dec, color="green", s=10)

        yticks = self.pointing_ax.get_yticks()
        # print(yticks)

        labels = [int(y) if y > -90 else int(-(y + 180)) for y in yticks]

        # self.fig.text(0.9, 0.3, "<- REVERSE", rotation=90.0)
        # self.fig.text(0.9, 0.7, "MAIN ->", rotation=90.0)

        self.plot_pointing_restrictions()

        self.pointing_canvas.draw()

        self.window.after(1000, self.update_pointing_graphic)

    def init_dome_actions_frame(self):

        self.dome_frame = tk.Frame(
            master=self.body_frame, name="dome", relief=tk.SUNKEN, borderwidth=3
        )
        self.dome_frame.grid(row=0, column=0, sticky="new", padx=5, pady=5)

        dome_actions_title = tk.Label(master=self.dome_frame, text="Dome actions")
        dome_actions_title.grid(row=0, column=0)

        enable_frame = tk.Frame(master=self.dome_frame, name="dome_enable")
        enable_frame.grid(row=1, column=0)
        self.enable_dome_var = tk.IntVar()
        self.enable_dome_button = tk.Checkbutton(
            master=enable_frame,
            variable=self.enable_dome_var,
            text="Enable dome actions",
            command=self.enable_dome_actions_command,
        )
        self.enable_dome_button.grid(row=0, column=0, pady=5, sticky="w")

        self.dome_actions_frame = tk.Frame(master=self.dome_frame, name="dome_buttons")
        self.dome_actions_frame.grid(row=2, column=0)

        for ii, (label, button_set) in enumerate(
            gui_settings.DOME_ACTION_BUTTONS.items()
        ):
            label = tk.Label(master=self.dome_actions_frame, text=f"{label}:")
            label.grid(row=ii, column=0, sticky="nse", padx=2)

            for jj, (widget_name, button_data) in enumerate(button_set.items()):
                button_text, cmd = button_data  # unpack 2-tuple
                self.dome_action_commands[widget_name] = button_data

                button = tk.Button(
                    master=self.dome_actions_frame,
                    text=button_text,
                    command=lambda cmd=cmd: self.execute_ascol_action(cmd),
                    state=tk.DISABLED,
                    width=5,
                    name=widget_name,
                )
                button.grid(row=ii, column=jj + 1)
                self.dome_action_widget_lookup[widget_name] = button

    def enable_dome_actions_command(self):
        if self.enable_dome_var.get():
            for name, dome_widget in self.dome_action_widget_lookup.items():
                logger.debug(f"enable {name}")
                dome_widget.configure(state=tk.NORMAL)
        else:
            self.disable_dome_actions_command()

    def disable_dome_actions_command(self):
        for name, dome_widget in self.dome_action_widget_lookup.items():
            logger.debug(f"disable {name}")
            dome_widget.configure(state=tk.DISABLED)

    def execute_ascol_action(self, cmd):

        cmd_str = cmd.replace(" ", ":")
        thread = threading.Thread(
            target=lambda cmd=cmd: self._exc_ascol_action(cmd),
            name=f"thread-{cmd_str}",
            daemon=True,
        )
        thread.start()

    def _exc_ascol_action(self, cmd):

        with Ascol(test_mode=self.test_mode) as ascol:
            ascol.gllg()
            ascol.get_data(cmd)

    def init_coords_frame(self):
        self.coords_frame = tk.Frame(
            master=self.body_frame, relief=tk.SUNKEN, borderwidth=3
        )
        self.coords_frame.grid(row=0, column=1, sticky="new", padx=5, pady=5)

        coords_header = tk.Label(master=self.coords_frame, text="Pointing")
        coords_header.grid(row=0, column=0, sticky="new")

        coords_data_frame = tk.Frame(master=self.coords_frame, name="coords_data")
        coords_data_frame.grid(row=1, column=0, sticky="new", padx=5, pady=5)

        propose_frame = tk.Frame(master=coords_data_frame, name="propose_coord_frame")
        propose_frame.grid(row=0, column=0)

        ra_label = tk.Label(master=propose_frame, text="R.A. (alpha)")
        ra_label.grid(row=0, column=0)
        ra_entry = tk.Entry(master=propose_frame, width=12)
        ra_entry.grid(row=0, column=1)

        dec_label = tk.Label(master=propose_frame, text="Dec (delta)")
        dec_label.grid(row=0, column=2)
        dec_entry = tk.Entry(master=propose_frame, width=12)
        dec_entry.grid(row=0, column=3)

        self.coord_widget_lookup["ra_entry"] = ra_entry
        self.coord_widget_lookup["dec_entry"] = dec_entry

        radio_frame = tk.Frame(master=propose_frame)
        radio_frame.grid(row=1, column=0, columnspan=4, sticky="nsew")
        propose_frame.rowconfigure(1, weight=1)
        main_opt = tk.Radiobutton(
            master=radio_frame,
            text="MAIN",
            variable=self.main_rev_var,
            value="0",
        )
        main_opt.grid(row=0, column=0)
        rev_opt = tk.Radiobutton(
            master=radio_frame,
            text="REVERSE",
            variable=self.main_rev_var,
            value="1",
        )
        rev_opt.grid(row=0, column=1)

        coords_actions_frame = tk.Frame(master=self.coords_frame, name="wheel_actions")
        coords_actions_frame.grid(row=2, column=0)
        coords_setup_label = tk.Label(master=coords_actions_frame, text="Coords")
        coords_setup_label.grid(row=0, column=0)

        self.wheel_setup_button = tk.Button(
            master=coords_actions_frame,
            text="SLEW",
            command=self.slew_telescope,
        )
        self.wheel_setup_button.grid(row=0, column=1)

    def slew_telescope(self):
        ra_coord = self.coord_widget_lookup["ra_entry"].get()
        dec_coord = self.coord_widget_lookup["dec_entry"].get()
        tel_pos = self.main_rev_var.get()

        if ra_coord == "" or dec_coord == "":
            msg = f"Must provide both RA and Dec in order to slew!"
            popup = get_warning_popup(msg)
            self.set_popup_location_and_show(popup)
            return

        thread = threading.Thread(
            target=self._excecute_slew, args=(ra_coord, dec_coord, tel_pos)
        )
        thread.start()

    def _excecute_slew(self, ra, dec, pos):
        print("in _exc_slew")
        with Ascol(test_mode=self.test_mode) as ascol:
            ascol.gllg()
            ascol.tsra(ra, dec, pos)
            time.sleep(0.5)
            ascol.tgra()

    def init_wheels_frame(self):

        self.wheels_frame = tk.Frame(
            master=self.body_frame, relief=tk.SUNKEN, borderwidth=3, name="wheels"
        )
        self.wheels_frame.grid(row=0, column=2, sticky="new", padx=5, pady=5)

        wheel_header = tk.Label(master=self.wheels_frame, text="DFOSC/FASU wheels")
        wheel_header.grid(row=0, column=0, sticky="nsw")

        wheel_data_frame = tk.Frame(master=self.wheels_frame, name="wheels_data")
        wheel_data_frame.grid(row=1, column=0)

        gui_settings.check_wheel_options()

        for ii, (wheel_key, wheel_text) in enumerate(
            gui_settings.WHEEL_LABEL_TEXT.items()
        ):
            wheel_label = tk.Label(master=wheel_data_frame, text=wheel_text)
            wheel_label.grid(row=ii, column=0, sticky="nse")

            wheel_options = gui_settings.WHEEL_OPTIONS[wheel_key]
            wheel_combobox = ttk.Combobox(
                master=wheel_data_frame,
                state="readonly",
                values=wheel_options,
                name=wheel_key,
                width=10,
            )
            wheel_combobox.current(0)
            wheel_combobox.bind("<1>", lambda e: self.update_hint(event=e))
            wheel_combobox.grid(row=ii, column=1, pady=5, padx=5)

            self.wheel_widget_lookup[wheel_key] = wheel_combobox

        wheel_actions_frame = tk.Frame(master=self.wheels_frame, name="wheel_actions")
        wheel_actions_frame.grid(row=2, column=0)
        wheel_setup_label = tk.Label(master=wheel_actions_frame, text="Wheel setup")
        wheel_setup_label.grid(row=0, column=0)

        self.wheel_setup_button = tk.Button(
            master=wheel_actions_frame, text="GO", command=self.move_to_wheel_setup
        )
        self.wheel_setup_button.grid(row=0, column=1)

    def move_to_wheel_setup(self):

        if self.wheels_moving:
            popup = get_warning_popup("Wheels already moving! Wait for finish...")
            self.set_popup_location_and_show(popup)
            return

        move_wheels_thread = threading.Thread(
            target=self._move_to_wheel_setup_thread, daemon=True
        )
        move_wheels_thread.name = "move_wheels_thread"
        move_wheels_thread.start()

    def _move_to_wheel_setup_thread(self):
        fasu_a_target = self.wheel_widget_lookup["fasu_a"].get()
        fasu_b_target = self.wheel_widget_lookup["fasu_b"].get()

        dfosc_grism_target = self.wheel_widget_lookup["dfosc_grism"].get()
        dfosc_filter_target = self.wheel_widget_lookup["dfosc_filter"].get()
        dfosc_aper_target = self.wheel_widget_lookup["dfosc_aperture"].get()

        self.wheels_moving = True
        with DK154(test_mode=self.test_mode) as dk154:
            dk154.move_wheel_a_and_wait(fasu_a_target)
        time.sleep(0.5)

        with DK154(test_mode=self.test_mode) as dk154:
            dk154.move_wheel_b_and_wait(fasu_b_target)
        time.sleep(0.5)

        with DK154(test_mode=self.test_mode) as dk154:
            dk154.move_dfosc_grism_and_wait(dfosc_grism_target)
            dk154.move_dfosc_aperture_and_wait(dfosc_aper_target)
            dk154.move_dfosc_filter_and_wait(dfosc_filter_target)
        self.wheels_moving = False

    def init_ccd3_frame(self):

        self.ccd3_frame = tk.Frame(
            master=self.body_frame, relief=tk.SUNKEN, borderwidth=3, name="ccd3"
        )
        self.ccd3_frame.grid(row=0, column=3, stick="new", padx=5, pady=5)

        ccd3_header = tk.Label(master=self.ccd3_frame, text="CCD3 Camera")
        ccd3_header.grid(row=0, column=0, sticky="nsw")

        ccd3_data_frame = tk.Frame(master=self.ccd3_frame, name="wheels_data")
        ccd3_data_frame.grid(row=1, column=0)

        for ii, (ccd3_entry_key, ccd3_entry_label) in enumerate(
            gui_settings.CCD3_LABEL_TEXT.items()
        ):
            key_label = tk.Label(master=ccd3_data_frame, text=ccd3_entry_label)
            key_label.grid(row=ii, column=0, sticky="nse")

            options = gui_settings.CCD3_OPTIONS.get(ccd3_entry_key, None)
            if options is None:
                widget = tk.Entry(master=ccd3_data_frame, width=10, name=ccd3_entry_key)
                default = gui_settings.CCD3_DEFAULT_OPTIONS.get(ccd3_entry_key, None)
                if default is not None:
                    widget.insert(tk.END, default)

            else:
                widget = ttk.Combobox(
                    master=ccd3_data_frame,
                    state="readonly",
                    values=options,
                    name=ccd3_entry_key,
                    width=10,
                )
                widget.current(0)

            self.ccd3_widget_lookup[ccd3_entry_key] = widget
            widget.bind("<1>", lambda e: self.update_hint(event=e))
            widget.grid(row=ii, column=1, pady=5, padx=5, sticky="nsw")

        ccd3_actions_frame = tk.Frame(master=self.ccd3_frame, name="ccd3_actions")
        ccd3_actions_frame.grid(row=2, column=0)
        exposure_label = tk.Label(master=ccd3_actions_frame, text="Exposure")
        exposure_label.grid(row=0, column=0)

        self.start_exposure_button = tk.Button(
            master=ccd3_actions_frame,
            text="START",
            command=self.start_exposure,
        )
        self.start_exposure_button.grid(row=0, column=1)

        self.stop_exposure_button = tk.Button(
            master=ccd3_actions_frame,
            text="STOP",
            command=self.stop_exposure,
        )
        self.stop_exposure_button.grid(row=0, column=2)

    def start_exposure(self):

        if self.exposure_in_progress:
            popup = get_warning_popup("Exposure in progress!")
            self.set_popup_location_and_show(popup)

        invalid_entry_comments = []
        exp_time = self.ccd3_widget_lookup["exp_time"].get()
        try:
            exp_time = float(exp_time)
        except ValueError as e:
            msg = f"Exposure time: can't interpret '{exp_time}' as a float!\n    {e}"
            invalid_entry_comments.append(msg)
        n_exp = self.ccd3_widget_lookup["n_exp"].get()

        try:
            n_exp = int(n_exp)
        except ValueError as e:
            msg = f"Num. exposures: can't interpret '{n_exp}' as a int!\n    {e}"
            invalid_entry_comments.append(msg)

        n_discard = self.ccd3_widget_lookup["n_discard"].get() or 0
        try:
            n_discard = int(n_discard)
        except:
            msg = f"Num. discard: can't interpret '{n_discard}' as a int!\n    {e}"
            invalid_entry_comments.append(msg)

        if len(invalid_entry_comments) > 0:
            warning_text = "\n".join(invalid_entry_comments)
            popup = get_warning_popup(warning_text, title="Invalid CCD3 entries!")

            self.set_popup_location_and_show(popup)
            return

        shutter_key = self.ccd3_widget_lookup["shutter"].get().upper()
        shutter = gui_settings.CCD3_SHUTTER_CODES.get(shutter_key, None)
        if shutter is None:
            msg = f"Unknown shutter code {shutter_key} - how has this happened?!"
            popup = get_warning_popup(msg)
            self.set_popup_location_and_show(popup)
            return

        remote_dir = self.ccd3_widget_lookup["remote_dir"].get()
        object_name = self.ccd3_widget_lookup["object_name"].get()
        args = (remote_dir, exp_time, n_exp, object_name)

        kwargs = dict(
            shutter=shutter,
            imagetyp=self.ccd3_widget_lookup["imagetyp"].get(),
            mod_imagetyp=self.ccd3_widget_lookup["mod_imagetyp"].get(),
        )

        exposure_thread = threading.Thread(
            target=self._exposure_process, daemon=True, args=args, kwargs=kwargs
        )
        exposure_thread.name = "exposure_thread"
        exposure_thread.start()

    def _exposure_process(
        self,
        remote_dir,
        exp_time,
        n_exp,
        object_name,
        n_discard=2,
        shutter="0",
        imagetyp="LIGHT",
        mod_imagetyp=None,
    ):
        self.exposure_in_progress = True
        self.stop_exposure_event.clear()

        take_discard_frames(
            remote_dir,
            n_exp=n_discard,
            test_mode=self.test_mode,
            exit_event=self.stop_exposure_event,
        )
        take_multi_exposure(
            remote_dir,
            exp_time,
            n_exp,
            object_name,
            shutter=shutter,
            imagetyp=imagetyp,
            mod_imagetyp=mod_imagetyp,
            test_mode=self.test_mode,
            exit_event=self.stop_exposure_event,
        )

        self.exposure_in_progress = False

    def stop_exposure(self):
        stop_exposure_thread = threading.Thread(target=self._stop_exposure, daemon=True)
        stop_exposure_thread.name = "stop_exposure_thread"
        stop_exposure_thread.start()  # haha

    def _stop_exposure(self):
        self.stop_exposure_event.set()

        with Ccd3(test_mode=self.test_mode) as ccd3:
            ccd3.stop_exposure()

        time.sleep(2.0)
        self.exposure_in_progress = False

    def init_footer_comment(self):

        self.footer_comment_frame = tk.Frame(master=self.footer_frame, name="footer")
        self.footer_comment_frame.grid(row=0, column=0, sticky="nsew")

        self.footer_comment_label = tk.Label(master=self.footer_comment_frame, text="")
        self.footer_comment_label.grid(row=0, column=0)

    def update_all_status_widgets(self):

        t_start = time.perf_counter()

        if self.ascol_status is not None:
            mjd_str = self.ascol_status.__dict__.get("mjd", None)
            time_str = self.ascol_status.__dict__.get("time_str", None)
            if mjd_str and time_str:
                update_time = time_from_mjdstr_hhmmss(mjd_str, time_str)
                update_label = update_time.strftime("%y-%m-%d %H:%M:%S")
                self.status_last_updated_widget.configure(text=update_label)

        for key, widget in self.status_widget_lookup.items():
            self._update_status_widget(key)
        interval = int(0.250 * 1000)  # must be integer for argument.
        self.root.after(interval, self.update_all_status_widgets)

    def _update_status_widget(self, key):
        widget = self.status_widget_lookup[key]

        status = self.status_data.get(key, f"<unavail>")

        labels_to_blink = gui_settings.BLINKING_STATUS_LABELS.get(key, {})
        is_blinking = status in labels_to_blink
        blinking_color = labels_to_blink.get(status, None) or "black"

        if is_blinking:
            curr_fg = widget.cget("fg")
            if curr_fg == blinking_color:
                fg = widget.cget("bg")  # ie. switch it OFF for the next interval.
            else:
                fg = blinking_color  # set it to the visible colour.
            text = status.upper()
        else:
            fg = "black"
            text = status
        font = "TkDefaultFont"

        widget.configure(text=text, fg=fg, font=font)
        # self.root.after(BLINK_INTERVAL, lambda key=key: self._update_status_widget(key))

    def start_status_loop(self):
        thread_status_loop = threading.Thread(
            target=self.loop_status_update, name="thread_status_loop", daemon=True
        )
        thread_status_loop.start()

    def loop_status_update(self):
        while True:
            if self.status_loop_var.get():
                self.update_status_info()
            time.sleep(self.status_update_interval)

    def update_status_info(self):
        logger.debug("retrieve status")

        try:
            self.ascol_status = AscolStatus.collect_silent(test_mode=self.test_mode)
        except ConnectionResetError as e:
            self.ascol_status = None
            logger.error(f"in AscolStatus: ConnectionResetError: {e}")
        try:
            self.dfosc_status = DfoscStatus.collect_silent(test_mode=self.test_mode)
            # self.dfosc_status.log_all_status()
        except ConnectionResetError as e:
            logger.error(f"in DfoscStatus: ConnectionResetError: {e}")
            self.dfosc_status = None

        if self.ascol_status is not None:
            for key in gui_settings.ASCOL_STATUS_DATA_LABELS.keys():
                status = self.ascol_status.__dict__.get(key, f"<unavail>")
                self.status_data[key] = status

        if self.dfosc_status is not None:
            for key in gui_settings.DFOSC_STATUS_DATA_LABELS.keys():
                status = self.dfosc_status.__dict__.get(key, f"<unavail>")
                self.status_data[key] = status

    def update_hint(self, event):
        key = str(event.widget).split(".")[-1]
        comment = gui_settings.COMMENTS.get(key, "")
        print(f"hint for {key} is '{comment}'")

        self.update_footer_label(text=comment)

    def update_footer_label(self, text):
        self.footer_comment_label.configure(text=text)

    def excecute_ascol_action(self, command):
        with Ascol(test_mode=self.test_mode) as ascol:
            ascol.get_data(command)

    @classmethod
    def main(cls, test_mode=False):
        gui = cls(test_mode=test_mode)

        thid = threading.get_ident()
        gui.root.mainloop()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-t", "--test-mode", action="store_true", default=False)
    args = parser.parse_args()

    ControlGui.main(test_mode=args.test_mode)
