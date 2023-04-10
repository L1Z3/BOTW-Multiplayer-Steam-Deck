# Code in this file was adapted from SteamRomManager's AppId generation.
# https://github.com/SteamGridDB/steam-rom-manager/blob/dc8500ebe7df467f310b1d36fbc93b44494169be/src/lib/helpers/steam/generate-app-id.ts

import crc32c
import ctypes


def generate_preliminary_id(exe: str, appname: str) -> int:
    key = exe + appname
    top = ctypes.c_uint32(crc32c.crc32c(key.encode("ascii"))).value | 0x80000000
    return (top << 32) | 0x02000000


# Used for Big Picture Grids
def generate_app_id(exe: str, appname: str) -> int:
    return generate_preliminary_id(exe, appname)


# Used for all other Grids
def generate_short_app_id(exe: str, appname: str) -> int:
    return generate_preliminary_id(exe, appname) >> 32


# Used as appid in shortcuts.vdf
def generate_shortcut_id(exe: str, appname: str) -> int:
    return (generate_preliminary_id(exe, appname) >> 32) - 0x100000000


# shortcut AppId to ShortAppId
def shortcut_id_to_short_app_id(shortcut_id: int) -> int:
    return shortcut_id + 0x100000000


# Convert from AppId to ShortAppId
def shorten_app_id(long_id: int) -> int:
    return long_id >> 32


# Convert from ShortAppId to AppId
def lengthen_app_id(short_id: int) -> int:
    return (short_id << 32) | 0x02000000
