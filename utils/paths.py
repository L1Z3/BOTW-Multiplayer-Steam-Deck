"""
Path utilities.
"""

import os
from typing import Tuple, Optional, Dict, List
from xml.etree import ElementTree as ET

from utils.common import wait_for_confirmation


def normalize_path(path: str) -> str:
    """
    Converts a Windows path to a Unix path
    :param path: path to convert
    :return: path in Unix format
    """
    if len(path) < 2 or not path[0].isalpha() or path[1] != ":":
        return path

    # Replace backslashes with forward slashes
    unix_path = path.replace("\\", "/")

    # Remove drive letter
    _, rest_of_path = unix_path.split(":", 1)
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

    path_contains: list = kwargs.get("path_contains")
    dir_includes: list = kwargs.get("dir_includes")
    sub_folder_includes: dict = kwargs.get("sub_folder_includes")
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
        except OSError as e:
            return False, str(e), path

    if sub_folder_includes is not None:
        for sub_folder, required_files in sub_folder_includes.items():
            try:
                files = os.listdir(os.path.join(path, sub_folder))
                for file in required_files:
                    if file not in files:
                        reason = f"Sub-directory missing necessary files!\nFiles needed: {required_files}\n" \
                                 f"Files present: {files}"
                        return False, reason, path
            except OSError as e:
                return False, str(e), path

    return True, None, path


def get_path(input_message: str, **kwargs) -> str:
    """
    Prompt the user to input a file path and validate it based on specified requirements.
    :param input_message: The text shown to ask the user for the path.
    :param kwargs:
        - required_phrases (list): A list of substrings that are required to be in the file path.
        - required_files (list): A list of files that are required to be in the directory.
        - required_sub_files (dict): A dictionary of files that are required to be in a subdirectory.
          Format: {"subdirectory": ["file.txt", "file2.json"], "subdirectory2/subsubdirectory": ["coolfile.txt"]}
          IMPORTANT: USE LISTS EVEN IF IT IS ONLY ONE FILE, DO NOT ADD A PRESLASH TO THE SUBDIRECTORY.
    :return: The valid file path entered by the user or None if invalid.
    """
    required_phrases: list = kwargs.get("required_phrases", [])
    required_files: list = kwargs.get("required_files", [])
    required_sub_files: dict = kwargs.get("required_sub_files", {})

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


def get_sd_path() -> Optional[str]:
    """
    Get the path to the SD card
    """
    if os.path.exists("/dev/mmcblk0p1"):
        return os.popen("findmnt -n --raw --evaluate --output=target -S /dev/mmcblk0p1").read().strip()
    return None


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
            xml_dir = normalize_path(title.find("path").text)
            if not xml_dir.strip("/").strip("\\").endswith(base_dir):
                xml_dir = os.path.join(xml_dir, base_dir)
            is_valid, reason, xml_dir = check_path(xml_dir, path_contains=path_contains,
                                                   sub_folder_includes=sub_folders)
            if is_valid:
                confirmation = wait_for_confirmation(f"Is this your BOTW {prompt_type} dir?\n{xml_dir}\n[Y/n]: ")
                if confirmation:
                    return xml_dir

    is_valid, reason, installed_dir = check_path(installed_dir, path_contains=path_contains,
                                                 sub_folder_includes=sub_folders)
    if is_valid:
        confirmation = wait_for_confirmation(f"Is this your BOTW {prompt_type} dir?\n{installed_dir}\n[Y/n]: ")
        if confirmation:
            return installed_dir

    return get_path(f"Directory of the Breath of the Wild {prompt_type} Dump (the /{base_dir} folder): ",
                    required_phrases=path_contains, required_sub_files=sub_folders)

