import pandas as pd

import dk154_control

POINT_RES_DIR = dk154_control.root_dir / "config/pointing_restrictions/"
POINT_RES_MAIN_FILEPATH = POINT_RES_DIR / "main.dat"
POINT_RES_REV_FILEPATH = POINT_RES_DIR / "reverse.dat"


def load_pointing_restrictions():

    columns = ["ha", "da"]  # da=dec in main, da=-90-dec in reverse
    point_res_main = pd.read_csv(
        POINT_RES_MAIN_FILEPATH, delim_whitespace=True, names=columns
    )
    point_res_rev = pd.read_csv(
        POINT_RES_REV_FILEPATH, delim_whitespace=True, names=columns
    )
    point_res_main["dec"] = point_res_main["da"]
    point_res_rev["dec"] = abs(point_res_rev["da"] + 90.0) - 90.0

    return point_res_main, point_res_rev


def check_gui_config(config):

    comments = []

    da_config = config.get("dome_action_buttons", None)
    da_labels = config.get("dome_action_labels", {})

    if len(da_labels) == 0:
        comments.append(
            "no labels to format sets of dome_actions_commands!!"
            "provide mapping 'dome_action_labels'"
        )

    if da_config is None:
        comments.append("NO 'dome_action_buttons' in config!!")
    else:
        for subset_key, subset in da_config:
            for key, text_command_pair in subset.items():

                comm = (
                    f"in dome_action_buttons--{subset_key}, "
                    f"{key} should be a LIST: [button_text, ASCOL_CMD]"
                )
                if not isinstance(text_command_pair, list):
                    comm = comm + f"not {type(text_command_pair)}"
                    comments.append(comm)
                else:
                    if len(text_command_pair) != 2:
                        comm = comm + f"not {len(text_command_pair)}"
                        comments.append(comm)

            if subset_key not in da_labels:
                comm = f"{subset_key} not found in dome_actions_button_labels"
                comments.append(comm)

    for subset_key, subset_label in da_labels.items():
        if subset_key not in da_config:
            comm = f"Unknown subset_key {subset_key} in dome_action_labels"
