import platform
import pathlib
import re
import subprocess
import sys
from typing import Literal
import webbrowser

DOWNLOAD_TYPES = ['yt-dlp', 'khinsider', None]
YOUTUBE_HOSTNAMES = ['www.youtube.com', 'youtube.com', 'youtu.be', 'music.youtube.com']
KHINSIDER_HOSTNAMES = ['downloads.khinsider.com']
DL_COMMANDS: dict[str, list[str]] = {}
MUSIC_FILE_EXTENSIONS = ['.mp3', '.m4a', '.flac', '.opus', '.ogg', '.webm', '.aac']
EXCLUDED_DIRECTORIES = ['__pycache__', '.git']
PATH_SEPARATOR = '\\' if platform.system == "Windows" else '/'
KHINSIDER_INSTALL = pathlib.Path()
OUTPUT_DIRECTORY = pathlib.Path()

'''
"Usually, I would use double quotes for strings
However, due to me using double quotes to indicate
song names, I will use single quotes"    - Past Me
'''
def main():
    if (len(sys.argv) not in [3, 5]) and sys.argv[1] != '-f':
        print('USE: python mass_download.py -f [FILENAME]')
        return 1

    if len(sys.argv) == 5 and sys.argv[3] != '-o':
        print('USE: python mass_download.py -f [FILENAME] -o [OUTPUT DIRECTORY]')

    filename = sys.argv[2]
    global DL_COMMANDS
    global KHINSIDER_INSTALL
    global OUTPUT_DIRECTORY
    global EXCLUDED_DIRECTORIES
    OUTPUT_DIRECTORY = sys.argv[4] if len(sys.argv) == 5 else '~/Music'
    OUTPUT_DIRECTORY = pathlib.Path(OUTPUT_DIRECTORY).expanduser().resolve()
    KHINSIDER_INSTALL = locate_khinsider()
    EXCLUDED_DIRECTORIES.append(KHINSIDER_INSTALL.parent.name)
    DL_COMMANDS = load_commands()

    if not OUTPUT_DIRECTORY.exists():
        OUTPUT_DIRECTORY.mkdir(parents=True)

    buffer = read_song_list(filename)
    if buffer == []:
        print(f'{filename} does not exist!')
        return 1

    song_list = parse(buffer)
    for category, songs in song_list.items():
        for song in songs:
            playlist = category.lower() in ['albums', 'album', 'khinsider-downloads']
            dl_platform = download(song, category, playlist)
            if dl_platform == None:
                continue
            if playlist and dl_platform != None:
                categories = list(song_list)
                sort_album(categories, category, song)
            elif not playlist and dl_platform != None:
                sort_song(category, song)
    
    categories = list(song_list)
    unpack_albums(categories)

    return 0

def locate_khinsider():
    cwd = pathlib.Path('').cwd()
    for file in cwd.glob(f'**/khinsider.py'):
        return cwd / file


    return ""

def download(song_info: tuple[str], category: str, list: bool):
    url = song_info[1]
    success = 0
    
    platform = determine_platform(url)
    if platform == 'youtube':
        success = yt_download(song_info, list)
    elif platform == 'khinsider':
        success = khinsider_download(song_info)
    elif platform == None:
        webbrowser.open(url, 2)

    return None if success == 1 else platform

def unpack_albums(categories: list[str]):
    directories_to_unpack = []

    for category in categories:
        if category.lower() in ['root', 'khinsider-downloads', 'album', 'albums']:
            directories_to_unpack.append(category)
    
    for dir in directories_to_unpack:
        p = pathlib.Path(OUTPUT_DIRECTORY / dir)
        for d in p.glob(pattern='./*'):
            if not d.is_dir():
                continue
            destination = pathlib.Path(OUTPUT_DIRECTORY / d.name)
            if not destination.exists():
                destination.mkdir(parents=True, exist_ok=True)
            unpack(d, destination)
            d.rmdir()

        if p.exists():
            p.rmdir()

    return

def unpack(root: pathlib.Path, new_path: pathlib.Path):
    for f in root.glob(pattern='./*'):
        f.rename(new_path / f"{f.name}{f.suffix}")

    return

def sort_song(category: str, song: tuple[str, str]):
    name = song[0]
    cwd = pathlib.Path().cwd()
    downloaded_file = [
        f for f in cwd.glob(pattern='./*') 
        if f.is_file() and 
        f.suffix in MUSIC_FILE_EXTENSIONS
    ]

    downloaded_file = downloaded_file[0]
    destination = (OUTPUT_DIRECTORY / category)
    if not destination.exists():
        destination.mkdir(parents=True)
    
    ext = downloaded_file.suffix
    downloaded_file.rename(destination / f'{name}{ext}')

    return

def sort_album(categories: list[str], category: str, song: tuple[str, str]):
    name = song[0]
    cwd = pathlib.Path().cwd()

    # To ignore khinsider installs
    if KHINSIDER_INSTALL.parent != pathlib.Path().cwd():
        categories.extend(EXCLUDED_DIRECTORIES)

    downloaded_albums: list[pathlib.Path] = [
        f for f in cwd.glob(pattern='./*') 
        if f.is_dir() and 
        f.name not in categories
    ]
    
    downloaded_album: list[pathlib.Path] = [
        f for f in cwd.glob(pattern='./*') 
        if f.is_file() and 
        f.suffix in MUSIC_FILE_EXTENSIONS
    ]


    destination = OUTPUT_DIRECTORY / category / name

    if not destination.exists():
        try:
            destination.mkdir(parents=True, exist_ok=True)
        except NotADirectoryError:
            sanitised_dir_name = re.sub(r'[<>:"/\\|?*]', '-', destination.name)
            destination = destination.parent / sanitised_dir_name
            destination.mkdir(parents=True, exist_ok=True)

    for item in downloaded_album:
            item.rename(destination / f'{item.name}{item.suffix}')

    if downloaded_album == []:
        downloaded_albums: pathlib.Path = downloaded_albums[0]
        for f in downloaded_albums.glob("./*"):
            f.rename(destination / f'{f.name}{f.suffix}')
        downloaded_albums.rmdir()

    return

def determine_platform(url: str) -> Literal['youtube', 'khinsider', None]:
    hostname = url.split(sep='/')[2]

    platform = None
    if hostname in YOUTUBE_HOSTNAMES:
        platform = 'youtube'
    elif hostname in KHINSIDER_HOSTNAMES:
        platform = 'khinsider'
    
    return platform

def load_commands():
    try:
        f = open('download.conf')
    except FileNotFoundError:
        return
    finally:
        f.close()

    with open('download.conf') as dl_conf:
        DL_COMMANDS = [
            row.strip() for row in dl_conf if row.strip() != ''
        ]

    DL_COMMANDS = {
        DL_COMMANDS[0]: [DL_COMMANDS[1], DL_COMMANDS[2]],
        DL_COMMANDS[3]: [DL_COMMANDS[4]],
    }

    return DL_COMMANDS

def yt_download(song_info: tuple[str], list: bool = False):
    name, url = song_info
    command = DL_COMMANDS.get('[yt-dlp]')[int(list)] or 'yt-dlp'
    command = command.split()[1:]
    command.extend(['--no-config', '--quiet' , url])
    command.insert(0, 'yt-dlp')


    print(f'Running: {' '.join(command)}')
    command = [arg.strip('"\'') for arg in command]
    complete: subprocess.CompletedProcess = subprocess.run(command)
    if complete.returncode not in [0, 127]:
        print(f'Could not download {name}!')
        return 1
    elif complete.returncode == 0:
        print(f'{name} downloaded')
    elif complete.returncode == 127:
        print("Could not find yt-dlp installation!")
        return 1

    return 0

def khinsider_download(song_info: tuple[str]) -> pathlib.Path:
    name, url = song_info
    command: str = DL_COMMANDS.get('[khinsider]')[0] or "python khinsider.py"
    command = command.split()[2:]
    command.extend([url])
    command.insert(0, str(KHINSIDER_INSTALL))
    command.insert(0, sys.executable)

    print(f'Running: {' '.join(command)}')
    complete: subprocess.CompletedProcess = subprocess.run(command)

    for arg in command:
        arg.removeprefix('"')
        arg.removesuffix('"')

    if complete.returncode == 1:
        print(f'Could not download {name}!')
        return 1
    elif complete.returncode == 0:
        print(f'{name} downloaded')
    elif complete.returncode == 127:
        print("Could not find khinsider.py!")
        return 1


    return 0

def read_song_list(filename: str):
    out = []
    try:
        f = open(filename, mode='r')
    except FileNotFoundError:
        return out
    finally:
        f.close()
    
    with open(filename, mode='r', encoding="utf-8") as song_list:
        out = [row.strip() for row in song_list]

    return out

def parse(buffer: str):
    song_list: dict[str, list[tuple[str, str]]] = {}
    current_category = 'root'
    song_list['root'] = []

    for row in buffer:
        if row == '':
            current_category = 'root'
            continue
        if row[0] == '#':
            current_category = row[1:].strip()
            if current_category.lower() == 'khinsider':
                current_category = 'khinsider-downloads'
            if current_category.lower() in ['', 'root']:
                current_category = 'root'
            song_list[current_category] = song_list.get(current_category) or []
            continue
        
        row = row.split('|')
        if not row[0].strip().isnumeric():
            continue

        info = row[1:]
        info = '|'.join(info).strip()   # In case name or url has a '|' character
        name, url = tuple(info.split(sep='"')[1:])
        info = (name.strip(), url.strip())
        song_list[current_category].append(info)

    return song_list

if __name__ == '__main__':
    main()