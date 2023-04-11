"""
Functions for setting up Cemu.
"""

import io
import os
import shutil
import zipfile
from typing import Optional, Tuple
from xml.etree import ElementTree as ET

import requests

from utils.common import CEMU_URL, wait_for_confirmation
from utils.paths import check_path, get_directory, get_path, get_sd_path


def scan_for_cemu() -> Optional[str]:
    confirmation = wait_for_confirmation(f"Do you want to automatically look for a Cemu installation? This will scan "
                                         f"your home directory for Cemu.exe and may take a while. [Y/n]: ")
    if confirmation:
        try:
            print("Press ctrl+C at any time to end the scan.")
            for root, dirs, files in os.walk(os.path.expanduser("~/")):
                for filename in files:
                    if filename == "Cemu.exe":
                        return root
        except KeyboardInterrupt:
            print("Scan aborted.")
    return None


def download_cemu() -> Optional[str]:
    confirmation = wait_for_confirmation(f"Do you want to download Cemu now? [Y/n]: ")
    if confirmation:
        try:
            z = zipfile.ZipFile(io.BytesIO(requests.get(CEMU_URL).content))
            wiiu_dir = os.path.expanduser("~/Emulation/roms/wiiu/")
            os.makedirs(wiiu_dir, exist_ok=True)
            z.extractall(wiiu_dir)
            zipinfo = z.infolist()
            cemu_subdir = os.path.join(wiiu_dir, zipinfo[0].filename)
            for item in os.listdir(cemu_subdir):
                item_path = os.path.join(cemu_subdir, item)
                if os.path.isdir(item_path):
                    shutil.copytree(item_path, os.path.join(wiiu_dir, item))
                else:
                    shutil.copy2(item_path, wiiu_dir)
            shutil.rmtree(cemu_subdir)
            return wiiu_dir
        except ValueError:
            Exception(
                "ERROR: The information inside of the Cemu download was not what was expected! "
                "Please contact the developers of this application!")
        except (requests.RequestException, zipfile.BadZipFile, OSError, IndexError) as e:
            print(
                f"Something went wrong with the download, please download manually or select "
                f"a previous installation in the next step! Error:\n{e}", file=sys.stderr)
    return None


def get_cemu_dir() -> str:
    # Check for EmuDeck dirs
    is_valid, reason, emudeck_cemu_dir = check_path(
        os.path.expanduser("~/Emulation/roms/wiiu"), dir_includes=["Cemu.exe", "settings.xml"])

    if not is_valid:
        sd_path = get_sd_path()
        if sd_path is not None:
            is_valid, reason, emudeck_cemu_dir = check_path(
                f"{sd_path}/Emulation/roms/wiiu", dir_includes=["Cemu.exe", "settings.xml"])
    cemu_dir = None

    if is_valid:
        confirmation = wait_for_confirmation(f"Is this your Cemu directory? \n{emudeck_cemu_dir}\n[Y/n]: ")
        if confirmation:
            cemu_dir = emudeck_cemu_dir
    if cemu_dir is None:
        print("Could not automatically detect a Cemu installation. "
              "You will have the option to scan for Cemu, download Cemu, or manually select a Cemu exe.")
        got_by_scan = scan_for_cemu()
        if got_by_scan:
            cemu_dir = got_by_scan
            print(f"Successfully found Cemu at {cemu_dir}!")
    if cemu_dir is None:
        downloaded = download_cemu()
        if downloaded:
            cemu_dir = downloaded
            print(f"Successfully downloaded Cemu to {cemu_dir}!")
    if cemu_dir is None:
        cemu_dir = get_path("Directory to your Cemu Installation (where Cemu.exe is): ",
                            required_files=["Cemu.exe", "settings.xml"])

    return cemu_dir


def get_user_paths() -> Tuple[str, str, str, str]:
    cemu_dir = get_cemu_dir()

    root = None
    title_list_cache_path = os.path.join(cemu_dir, "title_list_cache.xml")
    if os.path.exists(title_list_cache_path):
        tree = ET.parse(title_list_cache_path)
        root = tree.getroot()

    # Find the paths with a specific titleId
    game_title_id = "00050000101c9400"
    game_sub_folders = {"Layout": ["Horse.sblarc"]}
    installed_game_dir = os.path.join(cemu_dir, "mlc01/usr/title/0005000/101c9400/content")
    game_dir = get_directory(root, installed_game_dir, game_title_id, "content", game_sub_folders, None, "Game")

    # Find the paths for update
    update_title_id = "0005000e101c9400"
    update_sub_folders = {"Actor/Pack": ["ActorObserverByActorTagTag.sbactorpack"]}
    installed_update_dir = os.path.join(cemu_dir, "mlc01/usr/title/0005000e/101c9400/content")
    update_dir = get_directory(root, installed_update_dir, update_title_id, "content", update_sub_folders,
                               None, "Update")

    # Find the paths for dlc
    dlc_title_id = "0005000c101c9400"
    dlc_sub_folders = {"Movie": ["Demo655_0.mp4"]}
    installed_dlc_dir = os.path.join(cemu_dir, "mlc01/usr/title/0005000c/101c9400/content/0010")
    dlc_dir = get_directory(root, installed_dlc_dir, dlc_title_id, "content/0010", dlc_sub_folders, None, "DLC")

    # !!IMPORTANT!! the tests I used to check each directory may not work for everyone. This is based upon my files and
    # my files may be messed up who knows. Double check these with your files to see if the tests work for you too :)
    return cemu_dir, game_dir, update_dir, dlc_dir

