"""
Functions for interacting with Steam.
"""

import os
import io
import shutil
import subprocess
import sys
import time
from typing import Tuple

import vdf

from utils import appids
from utils.common import MOD_DIR, STEAM_DIR, Shortcut, terminate_program, wait_for_file


def is_valid_steam_installation(directory: str) -> bool:
    """
    Check for the presence of specific directories
    that indicate a valid Steam installation on Linux.
    :param directory: directory to check
    :return: boolean indicating if the directory is a valid Steam installation
    """
    dirs_to_check = [
        'steamapps',
        'userdata',
    ]

    for dir_name in dirs_to_check:
        if not os.path.isdir(os.path.join(directory, dir_name)):
            return False

    # If all checks passed, the directory is a valid Steam installation.
    return True


def install_protontricks() -> str:
    """
    Installs Protontricks from Flathub if it is not already installed. Returns the command used to run Protontricks.
    :return: Command needed to run Protontricks, e.g. "flatpak run com.github.Matoking.protontricks"
    """
    flatpak_name = "com.github.Matoking.protontricks"

    # Check if Protontricks is already installed outside of Flatpak
    try:
        subprocess.run(["which", "protontricks"], check=True, capture_output=True)
        print("Protontricks is already installed.")
        return "protontricks"
    except subprocess.CalledProcessError:
        pass  # Protontricks not found outside of Flatpak, continue checking Flatpak

    # Check if flatpak is installed
    try:
        subprocess.run(["flatpak", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Protontricks is not installed on the system. Please either install flatpak (https://flatpak.org/setup/),"
              "or install protontricks from your package manager, then run this installer again.",
              file=sys.stderr)
        exit(1)

    # Check if Protontricks is already installed
    try:
        installed_apps_output = subprocess.run(["flatpak", "list"], capture_output=True, text=True, check=True)
        if flatpak_name in installed_apps_output.stdout:
            print("Protontricks is already installed.")
            return f"flatpak run {flatpak_name}"
    except subprocess.CalledProcessError as e:
        print(f"Failed to list installed Flatpak apps. Error: {e}", file=sys.stderr)
        print(f"Please install Protontricks manually (from flatpak or your package manager), "
              "then run this installer again.", file=sys.stderr)
        exit(1)

    # Install Protontricks from Flathub
    try:
        subprocess.run(["flatpak", "install", "-y", f"{flatpak_name}"], check=True)
        print("Protontricks has been successfully installed.")
        return f"flatpak run {flatpak_name}"
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Protontricks. Error: {e}", file=sys.stderr)
        print(f"Please install Protontricks manually (from flatpak or your package manager), "
              "then run this installer again.", file=sys.stderr)
        exit(1)


def run_steam_game(prefix_app_id: int):
    subprocess.run(["xdg-open", f"steam://rungameid/{appids.lengthen_app_id(prefix_app_id)}"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def add_dependencies_to_prefix(prefix_app_id: int):
    """
    Adds the dependencies for the Breath of the Wild multiplayer mod to the Steam prefix.
    :param prefix_app_id: The Steam app ID of the prefix to add the dependencies to.
    """
    protontricks_cmd = install_protontricks()
    dotnet_32_path = os.path.join(STEAM_DIR, f"steamapps/compatdata/{prefix_app_id}/pfx/drive_c/"
                                             f"Program Files (x86)/dotnet/dotnet.exe")
    dotnet_64_path = os.path.join(STEAM_DIR, f"steamapps/compatdata/{prefix_app_id}/pfx/drive_c/"
                                             f"Program Files/dotnet/dotnet.exe")

    prefix_version_file = os.path.join(STEAM_DIR, f"steamapps/compatdata/{prefix_app_id}/version")
    if not os.path.exists(prefix_version_file):
        print("Proton prefix for the mod does not exist. Launching the mod once to create it... \n"
              "(if you see a popup saying that .NET must be installed, simply close it! This installer "
              "will take care of it.)")
        # launch the game once to create the prefix
        try:
            run_steam_game(prefix_app_id)
        except subprocess.CalledProcessError as e:
            print(f"Failed to launch the BOTWM shortcut. Error: {e}", file=sys.stderr)
            print(
                f"Please manually open Steam, and open the \"Breath of the Wild Multiplayer\" shortcut once to generate"
                f"necessary files. Once it has closed/you have closed the shortcut, please press enter.",
                file=sys.stderr)
            print("Press enter to continue...", file=sys.stderr, end="")
            input()

        # wait for the prefix to be created
        if not wait_for_file(os.path.join(STEAM_DIR, f"steamapps/compatdata/{prefix_app_id}/version"), 20):
            print("Failed to create the Proton prefix for the mod.", file=sys.stderr)
            print(f"Please manually open Steam, and open the \"Breath of the Wild Multiplayer\" shortcut once to "
                  f"generate necessary files. Once it has closed/you have closed the shortcut, please press enter.",
                  file=sys.stderr)
            print("Press enter to continue...", file=sys.stderr, end="")
            input()
            if not os.path.exists(prefix_version_file):
                print("Prefix still not created! Please contact the installer authors for help.", file=sys.stderr)
                exit(1)
        time.sleep(4)  # Wait a bit longer to make sure the prefix is fully created
        terminate_program("Breath of the Wild Multiplayer.exe")
        print("Proton prefix for the mod created! Installing dependencies...")
    else:
        # proton prefix already exists. let's see if we need dotnetdesktop6
        try:
            # Use capture_output=True to capture stdout
            result = subprocess.run(
                protontricks_cmd.split() + [str(prefix_app_id), "list-installed"],
                check=True,
                capture_output=True,
                text=True
            )
            # Check if "dotnetdesktop6" is present in the output
            if "dotnetdesktop6" in result.stdout and os.path.exists(dotnet_32_path) and os.path.exists(dotnet_64_path):
                print("Required dependencies already installed!")
                return
        except subprocess.CalledProcessError as e:
            # Failed to check, let's just assume it's not installed
            pass

        print("Proton prefix for the mod already exists. Installing dependencies...")

    # install dependencies
    try:
        subprocess.run(protontricks_cmd.split() + [str(prefix_app_id), "-q", "dotnetdesktop6"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies. Error: {e}", file=sys.stderr)
        print(f"Please install the dependencies manually by opening up Protontricks,"
              f"selecting \"Breath of the Wild Multiplayer\", then installing dotnetdesktop6.", file=sys.stderr)
        print(f"Once you have done this, please press enter.", file=sys.stderr, end="")
        input()

    expected_files = [dotnet_32_path, dotnet_64_path]
    for file in expected_files:
        if not os.path.exists(file):
            print(f"Failed to install dependencies! File {file} not found.", file=sys.stderr)
            print(f"This should not happen! Please contact the installer authors.", file=sys.stderr)
            exit(1)

    print("Dependencies installed successfully!")


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
    input(
        f"Steam will be closed for the following steps.\nIf this is okay, press enter to continue:")

    terminate_program("steam", "Steam")

    # Get the existing user ids
    user_data_folder = os.path.join(STEAM_DIR, "userdata")
    user_ids = os.listdir(user_data_folder)
    shortcut_name = "Breath of the Wild Multiplayer"
    user_names = {}

    # get user name from user id
    for id in user_ids:
        localconfig_vdf_path = os.path.join(STEAM_DIR, f"userdata/{id}/config", "localconfig.vdf")

    with io.open(localconfig_vdf_path, "r", encoding="utf-8") as config_file:
        id_data = str(vdf.load(config_file))
        id_data = id_data[id_data.index("friends"):id_data.index("Offline")] #just in case

    

    for uid in user_ids:
        if uid not in user_names.keys():
            user_id_location = id_data.index(uid)+len(uid)+13
            user_names[id] = id_data[user_id_location:id_data.index(',',user_id_location)-1] #feel free to change to use the vdf module if wanted

    # Prompt user to pick the user id
    print("User IDs:")
    selected_index = None
    while selected_index not in range(len(user_ids)):
        for i, user_id in enumerate(user_ids):
            print(f"{i + 1}. {user_id} : {user_names[user_id]}")

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
        mod_exe = f"\"{os.path.join(MOD_DIR, 'Breath of the Wild Multiplayer.exe')}\""
        shortcut_app_id = appids.generate_shortcut_id(mod_exe, shortcut_name)
        prefix_app_id = appids.shortcut_id_to_short_app_id(shortcut_app_id)
        icon = os.path.join(STEAM_DIR, f"userdata/{user_id}/config/grid/{prefix_app_id}_icon.png")

        new_shortcut = Shortcut(shortcut_name, mod_exe, f"\"{MOD_DIR}\"", icon, [])
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
    grid_dir = os.path.join(STEAM_DIR, f"userdata/{user_id}/config/grid")
    if not os.path.exists(grid_dir):
        os.makedirs(grid_dir)
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
