import os
import shutil
from pysteam.shortcuts import write_shortcuts
from xml.etree import ElementTree as ET
import requests
from requests.structures import CaseInsensitiveDict
import zipfile
from pathlib import Path
import uuid
import json
from bcml.install import export, install_mod, refresh_merges
import py7zr

DOWNLOAD_URL = "https://api.github.com/repos/edgarcantuco/BOTW.Release/releases"
WORKING_DIR = os.path.expanduser("~/.local/share/botwminstaller")
MOD_DIR = os.path.join(WORKING_DIR, "BreathOfTheWildMultiplayer")

# TODO don't hard code these, get input from user
GAME_DIR = "~/Applications/modding-botw/rom/00050000101c9400_v0/content"
DLC_DIR = "~/Applications/modding-botw/rom/0005000c101c9400_v80/content/0010"
UPDATE_DIR = "~/Applications/modding-botw/rom/0005000e101c9400_v208/content"

def download_mod_files():
    headers = CaseInsensitiveDict()
    r = requests.get(DOWNLOAD_URL, headers=headers)
    pretty = json.dumps(r.json(), indent=4)
    r_json = r.json()
    if len(r_json) == 0:
        raise Exception("Error downloading mod files")
    latest_release = r_json[0]
    download_link = latest_release["assets"][0]["browser_download_url"]

    r = requests.get(download_link, headers=headers)

    zip_name = os.path.join(WORKING_DIR, uuid.uuid4().hex + ".zip")

    if r.status_code == 200:
        with open(zip_name, 'wb') as file:
            file.write(r.content)

        with zipfile.ZipFile(zip_name, 'r') as zip_ref:
            zip_ref.extractall(MOD_DIR)

        file.close()
        zip_ref.close()

        os.remove(zip_name)
    else:
        raise Exception("Error downloading mod files")


def generate_graphics_packs():
    with open("settings_template.json", "r") as f:
        settings_json = json.load(f)
    settings_json["game_dir"] = os.path.expanduser(GAME_DIR)
    settings_json["dlc_dir"] = os.path.expanduser(DLC_DIR)
    settings_json["update_dir"] = os.path.expanduser(UPDATE_DIR)
    settings_json["store_dir"] = os.path.expanduser("~/.config/bcml")
    settings_json["export_dir"] = os.path.join(WORKING_DIR, "bcml_exports")

    temp_bcml_dir = os.path.expanduser('~/.config/bcml_temp')
    bcml_dir = os.path.expanduser('~/.config/bcml')

    if os.path.exists(temp_bcml_dir):
        shutil.rmtree(temp_bcml_dir)

    if os.path.exists(bcml_dir):
        shutil.move(bcml_dir, temp_bcml_dir)

    os.makedirs(bcml_dir)

    with open(os.path.join(bcml_dir, 'settings.json'), 'w') as f:
        json.dump(settings_json, f, indent=4)

    install_mod(Path(MOD_DIR) / "BNPs" / "BreathoftheWildMultiplayer.bnp")
    refresh_merges()
    install_mod(Path(MOD_DIR) / "BNPs" / "BOTWMultiplayer-Classic.bnp")
    refresh_merges()

    export_path = Path(WORKING_DIR) / "exported-mods.7z"
    export(export_path, True)

    py7zr.unpack_7zarchive(export_path,
                           os.path.join(WORKING_DIR, "BreathOfTheWild_BCML"))
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

    # TODO copy into graphicsPacks and copy patches to separate dir

    # TODO enable the packs with settings.

def main(cemu_path):
    # Generate the working directory
    os.makedirs(WORKING_DIR, exist_ok=True)

    # Download the latest mod files
    download_mod_files()

    # Create a Steam shortcut for 'Breath of the Wild Multiplayer.exe'
    game_path = os.path.join(MOD_DIR, "Breath of the Wild Multiplayer.exe")
    write_shortcuts(game_path, "Breath of the Wild Multiplayer", cemu_path)

    # Get the id for the Steam shortcut
    shortcut_path = os.path.join(cemu_path, "Breath of the Wild Multiplayer.lnk")
    with open(shortcut_path, "r") as f:
        contents = f.read()
        id = contents.split("steamid=")[1].split("&")[0]


    # TODO install protontricks if not installed already?
    # Run protontricks to install dotnetcoredesktop6
    os.system(f"protontricks {id} install dotnetcoredesktop6")

    # Generate the graphics packs from the mod files
    generate_graphics_packs()

    # Place the graphics packs files into the appropriate directories in Cemu
    graphics_packs_dir = os.path.join(cemu_path, "graphicPacks")
    # TODO: add code to place the graphics packs files into the appropriate directories

    # Add the relevant entries to the settings.xml file
    settings_path = os.path.join(cemu_path, "settings.xml")
    tree = ET.parse(settings_path)
    root = tree.getroot()

    graphic_pack_entries = [
        {"filename": "graphicPacks/BreathOfTheWild_BCML/rules.txt"},
        {"filename": "graphicPacks/bcmlPatches/BreathoftheWildMultiplayer/rules.txt"}
    ]

    graphic_pack_element = root.find("GraphicPack")
    for entry in graphic_pack_entries:
        entry_element = ET.SubElement(graphic_pack_element, "Entry", entry)
        graphic_pack_element.append(entry_element)

    tree.write(settings_path)

if __name__ == "__main__":
    cemu_path = "/path/to/cemu"
    main(cemu_path)
