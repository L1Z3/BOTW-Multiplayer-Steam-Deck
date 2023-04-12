#!/usr/bin/python

import os
import sys

from utils.cemu import get_user_paths
from utils.common import STEAM_DIR, WORKING_DIR
from utils.multiplayer_mod import download_mod_files, generate_graphics_packs, \
    place_graphics_packs, \
    update_graphics_packs, update_user_config
from utils.steam import add_dependencies_to_prefix, add_grids, generate_steam_shortcut, is_valid_steam_installation


def main():
    if not is_valid_steam_installation(STEAM_DIR):
        print("Steam installation not found. Please install Steam before running this script.", file=sys.stderr)
        print(f"(Note, we currently only look for Steam in {STEAM_DIR})", file=sys.stderr)
        exit(1)

    cemu_dir, game_dir, update_dir, dlc_dir = get_user_paths()
    # Generate the working directory
    os.makedirs(WORKING_DIR, exist_ok=True)

    # Download the latest mod files
    download_mod_files()

    # Generate steam shortcut
    prefix_app_id, user_id = generate_steam_shortcut()

    # Add grid data
    add_grids(prefix_app_id, user_id)

    # Add dependencies to prefix
    add_dependencies_to_prefix(prefix_app_id)

    # Generate the graphics packs from the mod files
    bcml_dir = generate_graphics_packs(game_dir, update_dir, dlc_dir)

    # Place the graphics packs in cemu & verify they're in the settings.xml
    place_graphics_packs(cemu_dir, bcml_dir)
    update_graphics_packs(cemu_dir)

    # Point the mod to the correct directories
    update_user_config(cemu_dir, game_dir, update_dir, dlc_dir, prefix_app_id)


if __name__ == "__main__":
    main()
