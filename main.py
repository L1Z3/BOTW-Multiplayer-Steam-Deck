import os
import shutil
from steampy.shortcuts import create_shortcut
from xml.etree import ElementTree as ET
import requests
from requests.structures import CaseInsensitiveDict
import zipfile
import uuid
import os
import json

DOWNLOAD_URL = "https://api.github.com/repos/edgarcantuco/BOTW.Release/releases"
WORKING_DIR = os.path.expanduser("~/.local/share/botwminstaller")
MOD_DIR = os.path.join(WORKING_DIR, "BreathOfTheWildMultiplayer")

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

def main(cemu_path):
    # Generate the working directory
    os.makedirs(WORKING_DIR, exist_ok=True)

    # Download the latest mod files
    download_mod_files()

    # Create a Steam shortcut for 'Breath of the Wild Multiplayer.exe'
    game_path = os.path.join(MOD_DIR, "Breath of the Wild Multiplayer.exe")
    create_shortcut(game_path, "Breath of the Wild Multiplayer", cemu_path)

    # Get the id for the Steam shortcut
    shortcut_path = os.path.join(cemu_path, "Breath of the Wild Multiplayer.lnk")
    with open(shortcut_path, "r") as f:
        contents = f.read()
        id = contents.split("steamid=")[1].split("&")[0]


    # TODO install protontricks if not installed already?
    # Run protontricks to install dotnetcoredesktop6
    os.system(f"protontricks {id} install dotnetcoredesktop6")

    # Generate the graphics packs from the mod files
    # TODO: add code to generate the graphics packs from the mod files

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
