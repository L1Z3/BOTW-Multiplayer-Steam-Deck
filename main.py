import collections
import json
import os
import py7zr
import requests
import shutil
import uuid
import vdf
import zipfile

from _crc_algorithms import Crc
from bcml.install import export, install_mod, refresh_merges
from pathlib import Path
from requests.structures import CaseInsensitiveDict
from xml.etree import ElementTree as ET


DOWNLOAD_URL = "https://api.github.com/repos/edgarcantuco/BOTW.Release/releases"
WORKING_DIR = os.path.expanduser("~/.local/share/botwminstaller")
MOD_DIR = os.path.join(WORKING_DIR, "BreathOfTheWildMultiplayer")

#make function so it can be called within while statement
# string path : the filepath as given by the user
# list pathContains : the requiredPhrases list
# list dirIncludes : the requiredFiles list
# dict subFolderIncludes : the requiredSubFiles dictionary
def checkPath(path : str, **kwargs):

  #if the filepath does not end in the courtesy slash
  if path[:-1] != "/" and path[:-1] != "\\":

    #append the slash
    path += '/'

  #set defaults
  containsTrue = True
  valid = True
  reason = None

  #if there are required substrings
  if 'pathContains' in kwargs:

    #try for AssertionError
    try:

        #assert that pathContains is a list
        assert isinstance(kwargs['pathContains'], list)

    #if assertion is wrong
    except AssertionError:

        #tell the user the programmer messed up
        print(f"A check is misconfigured, please contact the developers of this application!\nLocation of Error: pathContains check. kwargs={kwargs}")

    #for each wanted phrase in the path
    for phrase in kwargs['pathContains']:

        #if the phrase is not present in the given path
        if phrase not in path:

            #set containsTrue to False so future checks are skipped
            containsTrue = False

            #set reason for failure
            reason = f"Filepath does not contain neccessary phrases\nPhrases needed to occur in path: {kwargs['pathContains']}"
      
            #tell the while loop to continue
            valid = False

            #end the for loop as a problem has occurred
            break

  #if the last check passed and there are required files
  if containsTrue and 'dirIncludes' in kwargs:

    #try for AssertionError
    try:

        #assert that dirIncludes is a list
        assert isinstance(kwargs['dirIncludes'], list)

    #if assertion is wrong
    except AssertionError:

        #tell the user the programmer messed up
        print(f"A check is misconfigured, please contact the developers of this application!\nLocation of Error: dirIncludes check. kwargs={kwargs}")

    #try statement to catch any directory issues
    try:

        #collect all the files in the path
        files = os.listdir(path)

        #for each file that is required
        for file in kwargs['dirIncludes']:

          #if the file is not present in the directory
          if file not in files:

            #set reason for failure
            reason = f"Directory does not include neccessary files!\nFiles needed: {kwargs['dirIncludes']}\nFiles present: {files}"

            #tell the while loop to continue
            valid = False

            #end the for loop as a problem has occurred
            break

    #if an exception occurs
    except Exception as e:

      #set the reason for failure to the exception
      reason = e

      #tell the while loop to continue
      valid = False

  if valid == True and 'subFolderIncludes' in kwargs:

    #try for AssertionError
    try:

        #assert that subFolderIncludes is a dictionary
        assert isinstance(kwargs['subFolderIncludes'], dict)

    #if assertion is wrong
    except AssertionError:

        #tell the user the programmer messed up
        print(f"A check is misconfigured, please contact the developers of this application!\nLocation of Error: subFolderIncludes check. kwargs={kwargs}")

    #for each subfolder and collection of required files
    for subFolder in kwargs['subFolderIncludes'].keys():

        
        #try statement to catch any directory issues
        try:

            #get list of each file in the subFolder
            files = os.listdir(path+subFolder)

            #for eacg file required
            for file in kwargs['subFolderIncludes'][subFolder]:

                #if the file is not present in the directory
                if file not in files:

                    #set reason for failure
                    reason = f"Sub-directory does not include neccessary files!\nFiles needed: {kwargs['subFolderIncludes'][subFolder]}\nFiles present: {files}"

                    #tell the while loop to continue
                    valid = False

                    #end the for loop as a problem has occurred
                    break

            if valid == False:
                break

        #if an exception occurs
        except Exception as e:

            #set the reason for failure to the exception
            reason = e

            #tell the while loop to continue
            valid = False

        #for each file
  #return the validity of the path, the reason for failure (returns as none if all is well), and the path tested
  return (valid,reason,path)

#make function to get a specific path
# string inputMessage : the text shown to ask the user for the path
# list requiredPhrases : substrings that are required to be in the filepath
# list requiredFiles : files that are required to be in the directory
# dict requiredSubFiles : files that are required to be in a sub-directory
#   format as follows : {'subdirectory':['file.txt','file2.json'],'subdirectory2/subsubdirectory':['coolfile.txt']} IMPORTANT: USE LISTS EVEN IF IT IS ONLY ONE FILE, DO NOT ADD A PRESLASH TO THE SUBDIRECTORY
def getPath(inputMessage : str, **kwargs):

  #try for AssertionError
  try:

    #assert that all arguments are the correct type and if kwarg does not exist set a default
    assert isinstance(inputMessage, str)

    if 'requiredPhrases' in kwargs:
        assert isinstance(kwargs['requiredPhrases'], list)
        reqPhrases = kwargs['requiredPhrases']
    else:
        reqPhrases = []

    if 'requiredFiles' in kwargs:
        assert isinstance(kwargs['requiredFiles'], list)
        reqFiles = kwargs['requiredFiles']
    else:
        reqFiles = []

    if 'requiredSubFiles' in kwargs:
        assert isinstance(kwargs['requiredSubFiles'], dict)
        reqSubFiles = kwargs['requiredSubFiles']
    else:
        reqSubFiles = {}

  #if an assertion is wrong
  except AssertionError:

    #tell the user the programmer messed up
    print(f"This ask is misconfigured, please contact the developers of this application!\nLocation of Error: getPath kwargs + message check. kwargs={kwargs}")

    #end the function
    return


  #while an inputted path does not meet the requirements needed
  while (Path:=checkPath(str(input(inputMessage)),pathContains=reqPhrases,dirIncludes=reqFiles,subFolderIncludes=reqSubFiles))[0] == False:

    #tell the user the reason for failure
    print(f"Invalid Path: {Path[1]}")

  #return the valid path
  return Path[2]

#make function so that the sd card path can be found
def get_sd_path():
    if os.path.exists("/dev/mmcblk0p1"):
        return os.popen("findmnt -n --raw --evaluate --output=target -S /dev/mmcblk0p1").read().strip()
    return None

#check for EmuDeck dirs
emudeck_CEMU_DIR = checkPath("Z:/home/deck/Emulation/roms/wiiu", dirIncludes=['Cemu.exe','settings.xml'])

if emudeck_CEMU_DIR[0] == False:
    emudeck_CEMU_DIR = checkPath(f"{get_sd_path()}/Emulation/roms/wiiu", dirIncludes=['Cemu.exe','settings.xml'])

#get the Cemu directory
if emudeck_CEMU_DIR[0] == False:
    CEMU_DIR = getPath("Directory to your Cemu Installation (where Cemu.exe is): ", requiredFiles=['Cemu.exe','settings.xml'])
else:
    while confirmation:=input(f"Is this your Cemu directory? [Y/n]\n{emudeck_CEMU_DIR[2]}\n: ") not in ['Y','y','N','n']:
        pass
    
    if confirmation in ['Y','y']:
        CEMU_DIR = emudeck_CEMU_DIR[2]
    else:
        CEMU_DIR = getPath("Directory to your Cemu Installation (where Cemu.exe is): ", requiredFiles=['Cemu.exe','settings.xml'])
    

if CEMU_DIR[:-1] != '/' and CEMU_DIR[:-1] != '\\':
    CEMU_DIR += '/'

gameInXML = False
updateInXML = False
dlcInXML = False

try:
    # Load the XML file
    tree = ET.parse(CEMU_DIR+'title_list_cache.xml')
    root = tree.getroot()

    # Find the paths with a specific titleId

    #game
    title_id = '00050000101c9400'
    for title in root.findall(f".//title[@titleId='{title_id}']"):
        if (xml_GAME_DIR:=title.find('path').text)[0] == True:
            GAME_DIR = xml_GAME_DIR[2]
            while confirmation:=input(f"Is this your BotW Game directory? [Y/n]\n{GAME_DIR[2]}\n: ") not in ['Y','y','N','n']:
                pass

            if confirmation in ['Y','y']:
                gameInXML = True
            

    #update
    title_id = '0005000e101c9400'
    for title in root.findall(f".//title[@titleId='{title_id}']"):
        if (xml_UPDATE_DIR:=title.find('path').text)[0] == True:
            UPDATE_DIR = xml_UPDATE_DIR
            while confirmation:=input(f"Is this your BotW Update directory? [Y/n]\n{UPDATE_DIR[2]}\n: ") not in ['Y','y','N','n']:
                pass

            if confirmation in ['Y','y']:
                updateInXML = True

    #dlc
    title_id = '0005000c101c9400'
    for title in root.findall(f".//title[@titleId='{title_id}']"):
        if (xml_DLC_DIR:=title.find('path').text)[0] == True:
            DLC_DIR = xml_DLC_DIR
            while confirmation:=input(f"Is this your BotW DLC directory? [Y/n]\n{GAME_DIR[2]}\n: ") not in ['Y','y','N','n']:
                pass

            if confirmation in ['Y','y']:
                dlcInXML = True
        
except:
    print("No title_list_cache.xml found (this is perfectly fine)...")

#get the game directory if not in xml
if gameInXML == False:
    emudeck_GAME_DIR = checkPath("Z:/home/deck/Emulation/roms/wii/mlc01/usr/title/0005000/101c9400", subFolderIncludes={'content/Layout':['Horse.sblarc']})
    if emudeck_GAME_DIR[0] == False:
        GAME_DIR = getPath("Directory of the Breath of the Wild Game Dump (where the /content folder is): ", requiredSubFiles={'content/Layout':['Horse.sblarc']})
    else:
        while confirmation:=input(f"Is this your BotW Game directory? [Y/n]\n{emudeck_GAME_DIR[2]}\n: ") not in ['Y','y','N','n']:
            pass

        if confirmation in ['Y','y']:
            GAME_DIR = emudeck_GAME_DIR[2]
        else:
            GAME_DIR = getPath("Directory of the Breath of the Wild Game Dump (where the /content folder is): ", requiredSubFiles={'content/Layout':['Horse.sblarc']})

#get the update directory if not in xml
if updateInXML == False:
    emudeck_UPDATE_DIR = checkPath("Z:/home/deck/Emulation/roms/wii/mlc01/usr/title/0005000e/101c9400", pathContains=['usr','title'],subFolderIncludes={'content/Actor/Pack':['ActorObserverByActorTagTag.sbactorpack']})
    if emudeck_UPDATE_DIR[0] == False:
        UPDATE_DIR = getPath("Directory of Breath of the Wild Update (where the /content folder is): ", requiredPhrases=['usr','title'],requiredSubFiles={'content/Actor/Pack':['ActorObserverByActorTagTag.sbactorpack']})
    else:
        while confirmation:=input(f"Is this your BotW Update directory? [Y/n]\n{emudeck_GAME_DIR[2]}\n: ") not in ['Y','y','N','n']:
            pass

        if confirmation in ['Y','y']:
            UPDATE_DIR = emudeck_UPDATE_DIR[2]
        else:
            UPDATE_DIR = getPath("Directory of Breath of the Wild Update (where the /content folder is): ", requiredPhrases=['usr','title'],requiredSubFiles={'content/Actor/Pack':['ActorObserverByActorTagTag.sbactorpack']})

#get the dlc directory if not in xml
if dlcInXML == False:
    emudeck_DLC_DIR = checkPath("Z:/home/deck/Emulation/roms/wii/mlc01/usr/title/0005000c/101c9400", pathContains=['usr','title'],subFolderIncludes={'content/0010/Movie':['Demo655_0.mp4']})
    if emudeck_DLC_DIR[0] == False:
        DLC_DIR = getPath("Directory of Breath of the Wild DLC (where the /content folder is): ", requiredPhrases=['usr','title'],requiredSubFiles={'content/0010/Movie':['Demo655_0.mp4']})
    else:
        while confirmation:=input(f"Is this your BotW DLC directory? [Y/n]\n{emudeck_GAME_DIR[2]}\n: ") not in ['Y','y','N','n']:
            pass

        if confirmation in ['Y','y']:
            DLC_DIR = emudeck_DLC_DIR[2]
        else:
            DLC_DIR = getPath("Directory of Breath of the Wild DLC (where the /content folder is): ", requiredPhrases=['usr','title'],requiredSubFiles={'content/0010/Movie':['Demo655_0.mp4']})

#!!!IMPORTANT!!! the tests I used to check each directory may not work for everyone. This is based upon my files and my files may be messed up who knows. Double check these with your files to see if the tests work for you too :)

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
    settings_json["game_dir"] = GAME_DIR
    settings_json["dlc_dir"] = DLC_DIR
    settings_json["update_dir"] = UPDATE_DIR
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

Shortcut = collections.namedtuple('Shortcut', ['name', 'exe', 'startdir', 'icon', 'tags'])


def shortcut_app_id(shortcut):
    """
    Generates the app id for a given shortcut. Steam uses app ids as a unique
    identifier for games, but since shortcuts dont have a canonical serverside
    representation they need to be generated on the fly. The important part
    about this function is that it will generate the same app id as Steam does
    for a given shortcut
    """
    algorithm = Crc(width = 32, poly = 0x04C11DB7, reflect_in = True, xor_in = 0xffffffff, reflect_out = True, xor_out = 0xffffffff)
    crc_input = ''.join([shortcut.exe,shortcut.name])
    high_32 = algorithm.bit_by_bit(crc_input) | 0x80000000
    full_64 = (high_32 << 32) | 0x02000000
    return str(full_64)

def generate_steam_shortcut():
    # Get the existing user ids
    userDataFolder = os.path.expanduser(STEAM_DIR + "/userdata/")
    userIds = os.listdir(userDataFolder)

    # Prompt user to pick the user id
    print("User IDs:")
    for i, user_id in enumerate(userIds):
        print(f"{i + 1}. {user_id}")

    selected_index = int(input("Enter the number of the user ID you want to use: ")) - 1
    user_id = userIds[selected_index]

    shortcuts_path = os.path.expanduser(STEAM_DIR + f"/userdata/{user_id}/config/shortcuts.vdf")
    if not os.path.exists(shortcuts_path):
        with open(shortcuts_path, "wb") as f:
            vdf.binary_dump({"shortcuts": {}}, f)

    with open(shortcuts_path, "rb") as f:
        shortcuts = vdf.binary_load(f)

    # Check to see if there is an entry with the name "Breath of the Wild Multiplayer Mod"
    app_id = None
    for shortcut in shortcuts.get("shortcuts", {}).values():
        if shortcut["AppName"] == "Breath of the Wild Multiplayer Mod":
            app_id = shortcut_app_id(Shortcut(shortcut["AppName"], shortcut["exe"], shortcut["StartDir"], "", []))
            break

    # If not, generate a shortcut with the name "Breath of the Wild Multiplayer Mod"
    if not app_id:
        mod_exe = os.path.join(MOD_DIR, "Breath of the Wild Multiplayer.exe")
        new_shortcut = Shortcut("Breath of the Wild Multiplayer Mod", mod_exe, MOD_DIR, "", [])

        app_id = shortcut_app_id(new_shortcut)
        next_app_id = max((int(key) for key in shortcuts.get("shortcuts", {}).keys()), default=0) + 1
        shortcuts["shortcuts"][str(next_app_id)] = {
            "AppName": new_shortcut.name,
            "exe": new_shortcut.exe,
            "StartDir": new_shortcut.startdir,
            "icon": new_shortcut.icon,
            "tags": {str(i): tag for i, tag in enumerate(new_shortcut.tags)}
        }

        with open(shortcuts_path, "wb") as f:
            vdf.binary_dump(shortcuts, f)

    return int(app_id)

def main(cemu_path):
    # Generate the working directory
    os.makedirs(WORKING_DIR, exist_ok=True)

    # Download the latest mod files
    download_mod_files()

    # Generate the shortcut for steam
    generate_steam_shortcut()

    # TODO install protontricks if not installed already?
    # Run protontricks to install dotnetcoredesktop6
    #os.system(f"protontricks {id} install dotnetcoredesktop6")

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
        existing_entry = None
        for elem in graphic_pack_element.findall("Entry"):
            if elem.attrib["filename"] == entry["filename"]:
                existing_entry = elem
                break

        if not existing_entry:
            entry_element = ET.SubElement(graphic_pack_element, "Entry", entry)
            graphic_pack_element.append(entry_element)

    tree.write(settings_path)

if __name__ == "__main__":
    cemu_path = CEMU_DIR
    main(cemu_path)

