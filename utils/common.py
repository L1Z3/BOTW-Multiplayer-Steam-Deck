import collections
import os

Shortcut = collections.namedtuple("Shortcut", ["name", "exe", "startdir", "icon", "tags"])

DOWNLOAD_URL = "https://api.github.com/repos/edgarcantuco/BOTW.Release/releases"
WORKING_DIR = os.path.expanduser("~/.local/share/botwminstaller")
MOD_DIR = os.path.join(WORKING_DIR, "BreathOfTheWildMultiplayer")
STEAM_DIR = os.path.expanduser("~/.steam/steam")

CEMU_URL = "https://cemu.info/releases/cemu_1.27.1.zip"  # where to download the Cemu zip from


def wait_for_confirmation(prompt: str) -> bool:
    while (confirmation := str(input(prompt)).lower()) not in ["y", "n"]:
        pass
    return True if confirmation == "y" else False
