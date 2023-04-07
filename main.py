import os
import shutil
from steampy.shortcuts import create_shortcut
from xml.etree import ElementTree as ET

def main(cemu_path):
    # Generate the working directory
    working_dir = os.path.expanduser("~/.local/share/botwminstaller")
    os.makedirs(working_dir, exist_ok=True)

    # Download the latest mod files
    # TODO: add code to download mod files

    # Create a Steam shortcut for 'Breath of the Wild Multiplayer.exe'
    game_path = os.path.join(working_dir, "Breath of the Wild Multiplayer.exe")
    create_shortcut(game_path, "Breath of the Wild Multiplayer", cemu_path)

    # Get the id for the Steam shortcut
    shortcut_path = os.path.join(cemu_path, "Breath of the Wild Multiplayer.lnk")
    with open(shortcut_path, "r") as f:
        contents = f.read()
        id = contents.split("steamid=")[1].split("&")[0]

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
