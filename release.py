#! C:\Python34\python.exe

# Imports
import argparse
import sys
import json
import subprocess
import os
import dotenv
import fileinput
import re
import shutil
import psutil
import time
from PIL import Image, ImageFont, ImageDraw

# Configuration
repository_owner = 'Zamiell'
repository_name = 'isaac-racing-client'
mod_dir = 'C:\\Users\\james\\Documents\\My Games\\Binding of Isaac Afterbirth+ Mods\\racing+_dev'
title_screen_path = os.path.join(mod_dir, 'resources\\gfx\\ui\\main menu')
repository_dir = os.path.join('D:\\Repositories\\', repository_name)
os.chdir(repository_dir)

# Subroutines
def error(message, exception = None):
    if exception == None:
        print(message)
    else:
        print(message, exception)
    sys.exit(1)

# Get command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-gh', '--github', help="upload to GitHub in addition to building locally", action='store_true')
parser.add_argument('-l', '--logo', help="only udate the logo", action='store_true')
parser.add_argument('-s', '--skipmod', help="skip all mod related stuff", action='store_true')
parser.add_argument('-m', '--mod', help="only do mod related stuff", action='store_true')
args = parser.parse_args()

# Get the version
with open('package.json') as package_JSON:
    data = json.load(package_JSON)
number_version = data['version']
version = 'v' + data['version']

if args.skipmod == False:
    # Fill the "save.dat" file with all default values
    save_dat_defaults = os.path.join(mod_dir, 'save-defaults.dat')
    for i in range(1, 4): # This will go from 1 to 3
        save_dat = os.path.join(mod_dir, 'save ' + str(i) + '.dat')
        shutil.copyfile(save_dat_defaults, save_dat)

    # Draw the version number on the title menu graphic
    large_font = ImageFont.truetype(os.path.join('assets', 'fonts', 'Jelly Crazies.ttf'), 9)
    small_font = ImageFont.truetype(os.path.join('assets', 'fonts', 'Jelly Crazies.ttf'), 6)
    URL_font = ImageFont.truetype(os.path.join('assets', 'fonts', 'Vera.ttf'), 11)
    title_img = Image.open(os.path.join(title_screen_path, 'titlemenu-orig.png'))
    title_draw = ImageDraw.Draw(title_img)
    w, h = title_draw.textsize(version, font=large_font)
    color = (67, 93, 145)
    title_draw.text((420 - w / 2, 236), 'V', color, font=small_font)
    title_draw.text((430 - w / 2, 230), number_version, color, font=large_font)

    # Draw the URL on the title menu graphic
    URL = 'isaacracing.net'
    w, h = title_draw.textsize(URL, font=URL_font)
    title_draw.text((420 - w / 2, 250), URL, color, font=URL_font)

    title_img.save(os.path.join(title_screen_path, 'titlemenu.png'))
    print('Title screen image updated.')

    # We are done if all we need to do is update the title screen
    if args.logo:
        sys.exit()

    # Check to see if we had the Basement/Cellar STBs in testing mode
    rooms_dir = os.path.join(mod_dir, 'resources', 'rooms')
    for file_name in os.listdir(rooms_dir):
        if file_name.endswith('2.stb'):
            match = re.search(r'(.+)2\.stb$', file_name)
            new_file_name = match.group(1) + '.stb'
            os.rename(os.path.join(rooms_dir, file_name), os.path.join(rooms_dir, new_file_name))

    # Copy the mod
    mod_dir2 = 'mod'
    if os.path.exists(mod_dir2):
        try:
            shutil.rmtree(mod_dir2)
            time.sleep(1) # This is necessary or else we get "ACCESS DENIED" errors for some reason
        except Exception as e:
            error('Failed to remove the "' + mod_dir2 + '" directory:', e)
    try:
        shutil.copytree(mod_dir, mod_dir2)
    except Exception as e:
        error('Failed to copy the "' + mod_dir + '" directory:', e)
    print('Copied the mod.')

if args.github:
    # Open the mod updater tool from Nicalis
    path_to_uploader = 'C:\\Program Files (x86)\\Steam\\steamapps\\common\\The Binding of Isaac Rebirth\\tools\\ModUploader\\ModUploader.exe'
    subprocess.Popen([path_to_uploader]) # Popen will run it in the background

    # Commit to the client repository
    return_code = subprocess.call(['git', 'add', '-A'])
    if return_code != 0:
        error('Failed to git add.')
    return_code = subprocess.call(['git', 'commit', '-m', version])
    if return_code != 0:
        error('Failed to git commit.')
    return_code = subprocess.call(['git', 'push'])
    if return_code != 0:
        error('Failed to git push.')

# Close the program if it is running
# (having it open can cause corrupted ASAR archives)
for process in psutil.process_iter():
    if process.name() == 'electron.exe':
        process.kill()

# Build/package
print('Building:', repository_name, version)
if args.github:
    dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    run_command = 'dist2'
else:
    run_command = 'dist'
return_code = subprocess.call(['npm', 'run', run_command, '--python="C:/Python27/python.exe"'], shell=True)
if return_code != 0:
    error('Failed to build.')

# Done
print('Released version', number_version, 'successfully.')
