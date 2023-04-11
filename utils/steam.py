"""
Functions for interacting with Steam.
"""

import os
import shutil
import sys
import time
from typing import Tuple

import vdf

from utils import appids
from utils.common import MOD_DIR, STEAM_DIR, Shortcut


def set_proton_version(prefix_app_id: int):
    config_vdf_path = os.path.join(STEAM_DIR, "config", "config.vdf")
    if not os.path.exists(config_vdf_path):
        print("Steam config file not found! Exiting...", file=sys.stderr)
        exit(1)
    # backup config file
    shutil.copyfile(config_vdf_path, config_vdf_path + f".{int(time.time())}.bak")

    with open(config_vdf_path, "r") as config_file:
        data = vdf.load(config_file)

    data["InstallConfigStore"]["Software"]["Valve"]["Steam"]["CompatToolMapping"][str(prefix_app_id)] = \
        {
            "name": "proton_experimental",
            "config": "",
            "priority": "250"
        }

    with open(config_vdf_path, "w") as config_file:
        vdf.dump(data, config_file)


def generate_steam_shortcut() -> Tuple[int, int]:
    # Get the existing user ids
    user_data_folder = os.path.join(STEAM_DIR, "userdata")
    user_ids = os.listdir(user_data_folder)
    shortcut_name = "Breath of the Wild Multiplayer"

    # TODO get user name from user id
    # Prompt user to pick the user id
    print("User IDs:")
    for i, user_id in enumerate(user_ids):
        print(f"{i + 1}. {user_id}")

    selected_index = int(input("Enter the number of the user ID you want to use: ")) - 1
    user_id = user_ids[selected_index]

    shortcuts_path = os.path.join(STEAM_DIR, f"userdata/{user_id}/config/shortcuts.vdf")
    if not os.path.exists(shortcuts_path):
        with open(shortcuts_path, "wb") as shortcuts_file:
            vdf.binary_dump({"shortcuts": {}}, shortcuts_file)

    with open(shortcuts_path, "rb") as shortcuts_file:
        shortcuts = vdf.binary_load(shortcuts_file)

    # Back up vdf
    shutil.copyfile(shortcuts_path, os.path.join(STEAM_DIR,
                                                 f"userdata/{user_id}/config/shortcuts.vdf.{int(time.time())}.bak"))

    # Check to see if there is an entry with the name "Breath of the Wild Multiplayer Mod"
    shortcut_app_id = None
    for shortcut in shortcuts.get("shortcuts", {}).values():
        if ("appname" in shortcut and shortcut["appname"] == shortcut_name) \
                or ("AppName" in shortcut and shortcut["AppName"] == shortcut_name):
            if "appid" in shortcut:
                shortcut_app_id = shortcut["appid"]
            break

    # If not, generate a shortcut with the name "Breath of the Wild Multiplayer Mod"
    if not shortcut_app_id:
        mod_exe = os.path.join(MOD_DIR, "Breath of the Wild Multiplayer.exe")
        shortcut_app_id = appids.generate_shortcut_id(mod_exe, shortcut_name)
        prefix_app_id = appids.shortcut_id_to_short_app_id(shortcut_app_id)
        icon = os.path.join(STEAM_DIR, f"userdata/{user_id}/config/grid/{prefix_app_id}_icon.png")

        new_shortcut = Shortcut(shortcut_name, mod_exe, MOD_DIR, icon, [])
        next_index = max((int(key) for key in shortcuts.get("shortcuts", {}).keys()), default=0) + 1
        shortcuts["shortcuts"][str(next_index)] = \
            {
                "appid": shortcut_app_id,
                "appname": new_shortcut.name,
                "Exe": new_shortcut.exe,
                "StartDir": new_shortcut.startdir,
                "icon": new_shortcut.icon,
                "LaunchOptions": "",
                "IsHidden": 0,
                "AllowDesktopConfig": 1,
                "AllowOverlay": 1,
                "OpenVR": 0,
                "Devkit": 0,
                "DevkitGameID": "",
                "DevkitOverrideAppID": 0,
                "LastPlayTime": 0,
                "FlatpakAppID": "",
                "tags": {}
            }

        with open(shortcuts_path, "wb") as shortcuts_file:
            vdf.binary_dump(shortcuts, shortcuts_file)

    prefix_app_id = appids.shortcut_id_to_short_app_id(shortcut_app_id)
    long_app_id = appids.lengthen_app_id(prefix_app_id)
    # either way, set the proton version
    set_proton_version(prefix_app_id)

    # TODO maybe add this to log file once we do that
    print(f"Shortcut name: {shortcut_name}")
    print(f"Shortcut app id: {shortcut_app_id}")
    print(f"Prefix app id: {prefix_app_id}")
    print(f"Long app id: {long_app_id}")

    return int(prefix_app_id), int(user_id)


def add_grids(app_id: int, user_id: int):
    try:
        for file in os.listdir("./grids"):
            shutil.copy(f"./grids/{file}",
                        os.path.join(STEAM_DIR, f"userdata/{user_id}/config/grid/{file.replace('BotWM', str(app_id))}"))
    except FileNotFoundError:
        print(f"Could not write to your Steam artwork folder. If you want custom artwork for your shortcut, please "
              f"add the files from {os.path.abspath('./grids/')} manually in the Steam desktop client.")
    except Exception as e:
        print(f"An error has occurred while adding artwork to Steam. Please continue with installation, and add the "
              f"artwork to Steam later if desired.\n"
              f"All artwork can be found in {os.path.abspath('./grids/')}\nError: {e}")
