import collections
import os
import subprocess

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


def terminate_program(process_name: str):
    # Wait for the user to press enter to proceed
    try:
        subprocess.run(["killall", "-w", process_name], check=True, timeout=15, capture_output=True, text=True)
        print(f"Successfully closed '{process_name}'.")
    except subprocess.CalledProcessError as e:
        if "no process found" in e.stderr.lower():
            print(f"{process_name} was already closed.")
        else:
            input(
                f"This program does not have the correct permissions to close {process_name}.\n"
                f"Please close {process_name} manually, then press enter to continue:")
    except subprocess.TimeoutExpired:
        input(
            f"It took too long to close {process_name}!\n"
            f"Please close {process_name} manually, then press enter to continue:")
