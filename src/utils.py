from difflib import diff_bytes
from Classes.PathManager import PathManager
from timeit import default_timer as timer
from Classes.Metadata import Metadata
from Classes.Download import Download
from Classes.Packet import Packet
from datetime import datetime
from subprocess import *
from extension import *
import requests
import tempfile
import difflib
import random
import glob
import json
import sys
import os

manager = PathManager()
parent_dir = manager.get_parent_directory()
current_dir = manager.get_current_directory()

def send_req_all() -> dict:
        REQA = 'https://electric-package-manager.herokuapp.com/packages/darwin'
        time = 0.0
        response = requests.get(REQA, timeout=15)
        res = json.loads(response.text.strip())
        time = response.elapsed.total_seconds()
        return res, time

def install_package(download: Download):
    attach_dmg = f'sudo hdiutil attach -nobrowse -noverify {download.path}'
    try:
        check_call(attach_dmg, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    except (FileNotFoundError, OSError) as err:
        print(err)

    
    volumes = os.listdir('/Volumes')
    
    matches = difflib.get_close_matches(download.name, volumes)

    if matches[0]:
        is_pkg = False
        if 'Macintosh' not in matches[0]:
            os.chdir(f'/Volumes/{matches[0]}')
            filename = None
            for file in glob.glob("*.app"):
                filename = file

            if not filename:
                for file in glob.glob("*.pkg"):
                    filename = file
                    is_pkg = True
                    break
            
            if filename:
                if not is_pkg:
                    run = f'sudo mv -f "{filename}" /Applications'
                else:
                    run = f'sudo installer -pkg "{filename}" -target /Applications'
                
                try:
                    check_call(run, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=True)
                except (FileNotFoundError, OSError, CalledProcessError) as err:
                    pass
    
    os.chdir('/')
    detach_dmg = f'sudo hdiutil detach "/Volumes/{matches[0]}"'
    try:
        proc = Popen(detach_dmg, stdout=PIPE, stderr=PIPE, stdin=PIPE, shell=True)
    except (FileNotFoundError, OSError) as err:
        print(err)

def download(packet: Packet) -> Download:
    path = f'{tempfile.gettempdir()}/Setup{packet.darwin_type}'

    while os.path.isfile(path):
        path = f'{tempfile.gettempdir()}/Setup{random.randint(200, 100000)}{packet.darwin_type}'

    with open(path, "wb") as f:
        response = requests.get(packet.darwin, stream=True)
        total_length = response.headers.get('content-length')

        if total_length is None:
            f.write(response.content)
        else:
            dl = 0
            full_length = int(total_length)

            for data in response.iter_content(chunk_size=7096):
                dl += len(data)
                f.write(data)

                complete = int(20 * dl / full_length)
                fill_c, unfill_c = '#' * complete, ' ' * (20 - complete)
                sys.stdout.write(
                    f"\r[{fill_c}{unfill_c}] ⚡ {round(dl / full_length * 100, 1)} % ⚡ {round(dl / 1000000, 1)} / {round(full_length / 1000000, 1)} MB")
                sys.stdout.flush()

    return Download(packet.darwin, packet.darwin_type, packet.json_name, packet.display_name, path)

def setup_supercache():
    res, time = send_req_all()
    res = json.loads(res)
    with open(Rf'{parent_dir}supercache.json', 'w+') as file:
        del res['_id']
        file.write(json.dumps(res, indent=4))

    return res, time

def update_supercache(res):
    filepath = Rf'{parent_dir}supercache.json'
    file = open(filepath, 'w+')
    file.write(json.dumps(res, indent=4))
    file.close()
    logpath = Rf'{parent_dir}superlog.txt'
    logfile = open(logpath, 'w+')
    now = datetime.now()
    logfile.write(str(now))
    logfile.close()

def check_supercache_valid():
    filepath = Rf'{parent_dir}superlog.txt'
    if os.path.isfile(filepath):
        with open(filepath, 'r') as f:
            contents = f.read()
        date = datetime.strptime(contents, '%Y-%m-%d %H:%M:%S.%f')
        if (datetime.now() - date).days < 1:
            return True
    return False

def handle_cached_request():
    filepath = Rf'{parent_dir}supercache.json'
    if os.path.isfile(filepath):
        file = open(filepath)
        start = timer()
        res = json.load(file)
        file.close()
        end = timer()
        if res:
            return res, (end - start)
        else:
            res, time = setup_supercache()
            return res, time
    else:
        res, time = setup_supercache()
        return res, time

def generate_metadata(no_progress, silent, verbose, debug, no_color, yes, logfile, virus_check, reduce):
    return Metadata(no_progress, no_color, yes, silent, verbose, debug, logfile, virus_check, reduce)

def handle_exit(status: str, setup_name: str, metadata: Metadata):

    if status == 'Downloaded' or status == 'Installing' or status == 'Installed':
        # exe_name = setup_name.split('\\')[-1]
        # os.kill(int(get_pid(exe_name)), SIGTERM)

        write('SafetyHarness Successfully Created Clean Exit Gateway',
              'green', metadata)
        write('\nRapidExit Using Gateway From SafetyHarness Successfully Exited With Code 0',
              'light_blue', metadata)
        os._exit(0)

    if status == 'Got Download Path':
        write('\nRapidExit Successfully Exited With Code 0', 'green', metadata)
        os._exit(0)

    else:
        write('\nRapidExit Successfully Exited With Code 0', 'green', metadata)
        os._exit(0)

def get_correct_package_names(res: str) -> list:
    package_names = []
    for package in res:
        package_names.append(package)
    return package_names

def find_existing_installation(package_name: str, json_name: str):
    run('sudo pwd', stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    applications = os.listdir('/Applications')
    matches = difflib.get_close_matches(package_name, applications)
    try:
        matches[0]
        return True
    except IndexError:
        secondary_matches = difflib.get_close_matches(json_name, applications)
        try:
            secondary_matches[0]
            return True
        except IndexError:
            return False
