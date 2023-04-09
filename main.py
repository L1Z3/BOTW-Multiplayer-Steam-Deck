#!/usr/bin/python

import json
import os
import py7zr
import requests
import shutil
import uuid
import zipfile

from bcml.install import export, install_mod, refresh_merges
from pathlib import Path
from requests.structures import CaseInsensitiveDict
from typing import Optional, Tuple, Dict, List
from xml.etree import ElementTree as ET

DOWNLOAD_URL = "https://api.github.com/repos/edgarcantuco/BOTW.Release/releases"
WORKING_DIR = os.path.expanduser("~/.local/share/botwminstaller")
MOD_DIR = os.path.join(WORKING_DIR, "BreathOfTheWildMultiplayer")


def normalize_path(path: str) -> str:
    """
    Converts a Windows path to a Unix path
    :param path: path to convert
    :return: path in Unix format
    """
    if len(path) < 2 or not path[0].isalpha() or path[1] != ':':
        return path

    # Replace backslashes with forward slashes
    unix_path = path.replace('\\', '/')

    # Remove drive letter
    _, rest_of_path = unix_path.split(':', 1)
    return rest_of_path


def check_path(path: str, **kwargs) -> Tuple[bool, Optional[str], str]:
    """
    Check if the given file path meets specified requirements.
    The function can be called within a while statement.
    :param path: The file path as given by the user.
    :param kwargs:
        - path_contains (list): The list of required phrases in the file path.
        - dir_includes (list): The list of required files in the directory.
        - sub_folder_includes (dict): The dictionary of required subfiles in subfolders.
    :return: Tuple (valid, reason, normalized_path) where valid is a boolean indicating
             if the path is valid, reason is a string with the reason for failure (None if valid),
             and normalized_path is the input path with a trailing slash added if necessary.
    """

    def normalize_path(p):
        return p if p.endswith(('/', '\\')) else p + '/'

    path_contains: list = kwargs.get('path_contains')
    dir_includes: list = kwargs.get('dir_includes')
    sub_folder_includes: dict = kwargs.get('sub_folder_includes')
    path = os.path.expanduser(normalize_path(path))

    if path_contains is not None:
        for phrase in path_contains:
            if phrase not in path:
                reason = f"Filepath does not contain necessary phrases\nPhrases needed: {path_contains}"
                return False, reason, path

    if dir_includes is not None:
        try:
            files = os.listdir(path)
            for file in dir_includes:
                if file not in files:
                    reason = f"Directory missing necessary files!\nFiles needed: {dir_includes}\nFiles present: {files}"
                    return False, reason, path
        except Exception as e:
            return False, str(e), path

    if sub_folder_includes is not None:
        for subFolder, required_files in sub_folder_includes.items():
            try:
                files = os.listdir(path + subFolder)
                for file in required_files:
                    if file not in files:
                        reason = f"Sub-directory missing necessary files!\nFiles needed: {required_files}\nFiles present: {files}"
                        return False, reason, path
            except Exception as e:
                return False, str(e), path

    return True, None, path


def get_path(input_message: str, **kwargs) -> Optional[str]:
    """
    Prompt the user to input a file path and validate it based on specified requirements.

    :param input_message: The text shown to ask the user for the path.
    :param kwargs:
        - required_phrases (list): A list of substrings that are required to be in the file path.
        - required_files (list): A list of files that are required to be in the directory.
        - required_sub_files (dict): A dictionary of files that are required to be in a subdirectory.
          Format: {'subdirectory': ['file.txt', 'file2.json'], 'subdirectory2/subsubdirectory': ['coolfile.txt']}
          IMPORTANT: USE LISTS EVEN IF IT IS ONLY ONE FILE, DO NOT ADD A PRESLASH TO THE SUBDIRECTORY.
    :return: The valid file path entered by the user or None if invalid.
    """
    required_phrases: list = kwargs.get('required_phrases', [])
    required_files: list = kwargs.get('required_files', [])
    required_sub_files: dict = kwargs.get('required_sub_files', {})

    while True:
        user_input = input(input_message)
        is_valid, reason, normalized_path = check_path(
            user_input,
            path_contains=required_phrases,
            dir_includes=required_files,
            sub_folder_includes=required_sub_files
        )
        if is_valid:
            return normalized_path
        else:
            print(f"Invalid Path: {reason}")


def get_sd_path():
    """
    Get the path to the SD card
    """
    if os.path.exists("/dev/mmcblk0p1"):
        return os.popen("findmnt -n --raw --evaluate --output=target -S /dev/mmcblk0p1").read().strip()
    return None


def wait_for_confirmation(prompt: str) -> str:
    while (confirmation := str(input(prompt)).lower()) not in ['y', 'n']:
        pass
    return confirmation


def get_directory(xml_root: Optional[ET.Element],
                  installed_dir: str,
                  title_id: str,
                  base_dir: str,
                  sub_folders: Dict[str, List[str]],
                  path_contains: Optional[List[str]],
                  prompt_type: str) -> str:
    """
    Get the directory for the specified type (game, update, or DLC) of Breath of the Wild.
    The function checks the XML file, the default installed directory, and prompts the user if needed.

    :param xml_root: The root element of the parsed XML file (None if XML file does not exist).
    :param installed_dir: The default path of the installed directory to check.
    :param title_id: The title ID to search for in the XML file.
    :param base_dir: The base directory name expected in the path.
    :param sub_folders: A dictionary of required sub-folders and their files to validate the directory.
    :param path_contains: A list of substrings that are required to be in the file path (optional).
    :param prompt_type: The type of directory being searched for (e.g., "Game", "Update", "DLC").

    :return: The valid file path entered by the user or found in the XML or default directory.
    """
    if xml_root is not None:
        for title in xml_root.findall(f".//title[@titleId='{title_id}']"):
            xml_dir = normalize_path(title.find('path').text)
            if not xml_dir.strip('/').strip('\\').endswith(base_dir):
                xml_dir = os.path.join(xml_dir, base_dir)
            is_valid, reason, xml_dir = check_path(xml_dir, path_contains=path_contains,
                                                   sub_folder_includes=sub_folders)
            if is_valid:
                confirmation = wait_for_confirmation(f"Is this your BOTW {prompt_type} dir?\n{xml_dir}\n[Y/n]: ")
                if confirmation == 'y':
                    return xml_dir

    is_valid, reason, installed_dir = check_path(installed_dir, path_contains=path_contains,
                                                 sub_folder_includes=sub_folders)
    if is_valid:
        confirmation = wait_for_confirmation(f"Is this your BOTW {prompt_type} dir?\n{installed_dir}\n[Y/n]: ")
        if confirmation == 'y':
            return installed_dir
    if base_dir == "0010":
        base_dir = "content/0010"

    return get_path(f"Directory of the Breath of the Wild {prompt_type} Dump (the /{base_dir} folder): ",
                    required_phrases=path_contains, required_sub_files=sub_folders)


def get_user_paths() -> Tuple[str, str, str, str]:
    # Check for EmuDeck dirs
    is_valid, reason, emudeck_cemu_dir = check_path(
        "Z:/home/deck/Emulation/roms/wiiu", dir_includes=['Cemu.exe', 'settings.xml'])

    if not is_valid:
        is_valid, reason, emudeck_cemu_dir = check_path(
            f"{get_sd_path()}/Emulation/roms/wiiu", dir_includes=['Cemu.exe', 'settings.xml'])

    # Get the Cemu directory
    if is_valid:
        confirmation = wait_for_confirmation(f"Is this your Cemu directory? [Y/n]\n{emudeck_cemu_dir}\n: ")

        cemu_dir = emudeck_cemu_dir if confirmation == 'y' \
            else get_path("Directory to your Cemu Installation (where Cemu.exe is): ",
                          required_files=['Cemu.exe', 'settings.xml'])
    else:
        cemu_dir = get_path(
            "Directory to your Cemu Installation (where Cemu.exe is): ",
            required_files=['Cemu.exe', 'settings.xml'])

    if cemu_dir[-1] not in r'\/':
        cemu_dir += '/'

    root = None
    title_list_cache_path = os.path.join(cemu_dir, 'title_list_cache.xml')
    if os.path.exists(title_list_cache_path):
        tree = ET.parse(title_list_cache_path)
        root = tree.getroot()

    # Find the paths with a specific titleId
    game_title_id = '00050000101c9400'
    game_sub_folders = {'Layout': ['Horse.sblarc']}
    installed_game_dir = os.path.join(cemu_dir, "mlc01/usr/title/0005000/101c9400/content")
    game_dir = get_directory(root, installed_game_dir, game_title_id, 'content', game_sub_folders, None, "Game")

    # Find the paths for update
    update_title_id = '0005000e101c9400'
    update_sub_folders = {'Actor/Pack': ['ActorObserverByActorTagTag.sbactorpack']}
    installed_update_dir = os.path.join(cemu_dir, "mlc01/usr/title/0005000e/101c9400/content")
    update_dir = get_directory(root, installed_update_dir, update_title_id, 'content', update_sub_folders,
                               None, "Update")

    # Find the paths for dlc
    dlc_title_id = '0005000c101c9400'
    dlc_sub_folders = {'Movie': ['Demo655_0.mp4']}
    installed_dlc_dir = os.path.join(cemu_dir, "mlc01/usr/title/0005000c/101c9400/content/0010")
    dlc_dir = get_directory(root, installed_dlc_dir, dlc_title_id, 'content/0010', dlc_sub_folders, None, "DLC")

    # !!!IMPORTANT!!! the tests I used to check each directory may not work for everyone. This is based upon my files and
    # my files may be messed up who knows. Double check these with your files to see if the tests work for you too :)
    return cemu_dir, game_dir, update_dir, dlc_dir


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


def generate_graphics_packs(game_dir: str, update_dir: str, dlc_dir: str):
    with open("settings_template.json", "r") as f:
        settings_json = json.load(f)
    settings_json["game_dir"] = game_dir
    settings_json["dlc_dir"] = dlc_dir
    settings_json["update_dir"] = update_dir
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


def main():
    cemu_dir, game_dir, update_dir, dlc_dir = get_user_paths()
    # Generate the working directory
    os.makedirs(WORKING_DIR, exist_ok=True)

    # Download the latest mod files
    download_mod_files()

    # Generate the graphics packs from the mod files
    generate_graphics_packs(game_dir, update_dir, dlc_dir)

if __name__ == "__main__":
    main()
