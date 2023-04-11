"""
Functions for downloading/installing the BOTWM mod.
"""

import json
import os
import shutil
import sys
import time
import uuid
import zipfile
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

import py7zr
import requests
from bcml.install import export, install_mod, refresh_merges
from packaging import version
from requests.structures import CaseInsensitiveDict

from utils.common import DOWNLOAD_URL, MOD_DIR, WORKING_DIR, wait_for_confirmation


def get_mod_version() -> Optional[version.Version]:
    version_path = os.path.join(MOD_DIR, "Version.txt")
    if not os.path.exists(version_path):
        return None
    with open(version_path, "r") as version_file:
        version_str = version_file.read()
        return version.parse(version_str)


def download_mod_files():
    cur_version = get_mod_version()
    if cur_version is not None:
        confirmation = wait_for_confirmation(f"BOTWM mod version {cur_version} already downloaded. "
                                             f"Would you like to check for updates? [Y/n]: ")
        if not confirmation:
            return
    headers = CaseInsensitiveDict()
    r = requests.get(DOWNLOAD_URL, headers=headers)

    r_json = r.json()
    # if the response doesn't look right, throw an error
    if len(r_json) == 0 or ("message" in r_json and "rate limit" in r_json["message"]):
        print("Error checking for mod file updates!", file=sys.stderr)
        if "message" in r_json and "rate limit" in r_json["message"]:
            print("(GitHub returned an API rate limit error.)", file=sys.stderr)
        if cur_version is None:
            print("No version of BOTWM mod downloaded! Exiting installer...", file=sys.stderr)
            exit(1)
        print(f"Continuing with current version ({cur_version})...", file=sys.stderr)
        time.sleep(0.5)
        return

    latest_release = r_json[0]
    latest_version = version.parse(latest_release["tag_name"])
    if cur_version is not None and cur_version == latest_version:
        print(f"Latest version BOTWM mod ({latest_version}) already downloaded")
        return
    if cur_version is not None and cur_version > latest_version:
        print(f"Current version of BOTWM mod ({cur_version}) is newer than latest version ({latest_version})")
        return
    print(f"Downloading BOTWM mod version {latest_version}")
    download_link = latest_release["assets"][0]["browser_download_url"]

    r = requests.get(download_link, headers=headers)

    zip_name = os.path.join(WORKING_DIR, uuid.uuid4().hex + ".zip")

    if r.status_code == 200:
        with open(zip_name, "wb") as zip_file:
            zip_file.write(r.content)

        with zipfile.ZipFile(zip_name, "r") as zip_ref:
            zip_ref.extractall(MOD_DIR)

        zip_file.close()
        zip_ref.close()

        os.remove(zip_name)

        # update version data
        with open(os.path.join(MOD_DIR, "Version.txt"), "w") as version_file:
            version_file.write(str(latest_version))
    else:
        print("Error downloading mod files!", file=sys.stderr)
        if cur_version is None:
            print("No version of BOTWM mod downloaded! Exiting installer...", file=sys.stderr)
            exit(1)
        print(f"Continuing with current version ({cur_version})...", file=sys.stderr)
        time.sleep(0.5)
        return


def generate_graphics_packs(game_dir: str, update_dir: str, dlc_dir: str):
    with open("settings_template.json", "r") as template_file:
        settings_json = json.load(template_file)
    settings_json["game_dir"] = game_dir
    settings_json["dlc_dir"] = dlc_dir
    settings_json["update_dir"] = update_dir
    settings_json["store_dir"] = os.path.expanduser("~/.config/bcml")
    settings_json["export_dir"] = os.path.join(WORKING_DIR, "bcml_exports")

    temp_bcml_dir = os.path.expanduser(f"~/.config/bcml_temp_{int(time.time())}")
    bcml_dir = os.path.expanduser("~/.config/bcml")

    if os.path.exists(temp_bcml_dir):
        shutil.rmtree(temp_bcml_dir)

    if os.path.exists(bcml_dir):
        shutil.move(bcml_dir, temp_bcml_dir)

    os.makedirs(bcml_dir)

    with open(os.path.join(bcml_dir, "settings.json"), "w") as settings_file:
        json.dump(settings_json, settings_file, indent=4)

    install_mod(Path(MOD_DIR) / "BNPs" / "BreathoftheWildMultiplayer.bnp")
    refresh_merges()
    install_mod(Path(MOD_DIR) / "BNPs" / "BOTWMultiplayer-Classic.bnp")
    refresh_merges()

    export_path = Path(WORKING_DIR) / "exported-mods.7z"
    export(export_path, True)
    graphics_pack = os.path.join(WORKING_DIR, "BreathOfTheWild_BCML")
    py7zr.unpack_7zarchive(export_path, graphics_pack)
    rules = Path(WORKING_DIR) / "BreathOfTheWild_BCML" / "rules.txt"
    rules.write_text(
        "[Definition]\n"
        "titleIds = 00050000101C9300,00050000101C9400,00050000101C9500\n"
        "name = BCML\n"
        "path = The Legend of Zelda: Breath of the Wild/Mods/BCML\n"
        "description = Complete pack of mods merged using BCML\n"
        "version = 7\n"
        "default = true\n"
        "fsPriority = 9999",
        encoding="utf-8",
    )

    shutil.rmtree(bcml_dir)

    shutil.move(temp_bcml_dir, bcml_dir)

    return graphics_pack


def place_graphics_packs(cemu_path: str, bcml_path: str):
    destination = os.path.join(cemu_path, "graphicPacks/BreathOfTheWild_BCML")
    if os.path.exists(destination):
        shutil.rmtree(destination)
    shutil.copytree(bcml_path, destination)
    patches = os.path.join(bcml_path, "patches")
    patches_destination = os.path.join(cemu_path, "graphicPacks", "bcmlPatches", "BreathoftheWildMultiplayer")
    if os.path.exists(patches_destination):
        shutil.rmtree(patches_destination)
    shutil.copytree(patches, patches_destination)


def update_graphics_packs(cemu_path: str):
    # Add the relevant entries to the settings.xml file
    settings_path = os.path.join(cemu_path, "settings.xml")
    tree = ET.parse(settings_path)
    root = tree.getroot()

    graphic_pack_entries = [
        {"filename": "graphicPacks/BreathOfTheWild_BCML/rules.txt"},
        {"filename": "graphicPacks/bcmlPatches/BreathoftheWildMultiplayer/rules.txt"},
        {"filename": "graphicPacks/downloadedGraphicPacks/BreathOfTheWild/Mods/ExtendedMemory/rules.txt"},
        {"filename": "graphicPacks/downloadedGraphicPacks/BreathOfTheWild/Mods/FPS++/rules.txt"},
    ]

    graphic_pack_element = root.find("GraphicPack")
    for entry in graphic_pack_entries:
        if not any(e.attrib["filename"] == entry["filename"] for e in graphic_pack_element):
            entry_element = ET.Element("Entry", entry)
            graphic_pack_element.append(entry_element)
    tree.write(settings_path)
