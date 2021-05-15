import mutagen
import xml.etree.ElementTree as etree

from common import (get_mp3_files, get_leaf_dirs, unique_path, 
                        SPLIT, SPLIT_OUTPUT, SPLIT_BACKUP)
from pathlib import Path
import subprocess
import os

MARKER = 'TXXX:OverDrive MediaMarkers'



def time_format(time):
    if isinstance(time, str):
        if time.count(':') == 2:
            hours, minutes, seconds = time.split(':')
            minutes = 60 * int(hours) + int(minutes)
        elif time.count(':') == 1:
            minutes, seconds = time.split(':')
            minutes = int(minutes)
        else:
            raise ValueError('Unable to decipher time format')
        seconds, frames = seconds.split('.')
        seconds = int(seconds)
        frames = int(int(frames) * 0.075)
    
    elif isinstance(time, float):
        seconds = int(time)
        fraction = time - seconds
        minutes = seconds // 60
        seconds %= 60
        frames = int(fraction * 75)
    
    return "%02d:%02d:%02d" % (minutes, seconds, frames) 

def create_xmlfiles(book):
    for mp3 in get_mp3_files(book):
        tags = mutagen.File(mp3)
        try:
            text = tags['TXXX:OverDrive MediaMarkers'].text[0]
        except KeyError:
            continue
        xmlname = book / (mp3.stem + '.xml')
        with open(xmlname, 'w') as xmlfile:
            xmlfile.write(text)

def extract_xmldata(directory=SPLIT):
    dirs = get_leaf_dirs(directory)
    msg = f'Extracting tag to create xml files for files in {directory}'
    print(msg)
    print('‾'*len(msg))
    for book in dirs:
        print(f'  ⦾ {book.name}')
        mp3files = list(get_mp3_files(book))
        mp3files.sort()
        count = 1
        for mp3path in mp3files:
            print(f'    ‣ {mp3path.name}')
            mp3path = Path(mp3path)
            tags = None
            try:
                tags = mutagen.File(mp3path)
            except:
                print(f'Cannot read tags from {mp3path}')
                continue
            try:
                title = tags['TALB'][0]
                artist = tags['TPE1'][0]
                date = tags['TDRC'][0]
            except:
                print(f'Set title/artist/date for {mp3path}')
                print(tags.keys())
                continue
            try:
                markertext = tags[MARKER].text[0]
                markers = etree.fromstring(markertext)
            except KeyError:
                print(f'Cannot create cue file for {mp3path}')
                print(tags.keys())
                continue
            xmlpath = mp3path.parent / (mp3path.stem + '.xml')
            with open(xmlpath, 'w') as xmlfile:
                xmlfile.write(markertext)

def make_cue_sheets(directory=SPLIT, replace_existing=False, pad = 0):
    dirs = get_leaf_dirs(directory)
    msg = f'Extracting tag to create cue sheets for files in {directory}'
    print(msg)
    print('‾'*len(msg))
    for book in dirs:
        print(f'  ⦾ {book.name}')
        mp3files = list(get_mp3_files(book))
        mp3files.sort()
        count = 1 + pad
        first = True
        for mp3path in mp3files:
            cuepath = mp3path.parent / (mp3path.stem + '.cue')
            if cuepath.exists() and not replace_existing:
                print(f'      ⁌ {cuepath} exists, skipping')
                continue
            print(f'    ‣ {mp3path.name}')
            mp3path = Path(mp3path)
            tags = None
            try:
                tags = mutagen.File(mp3path)
            except:
                print(f'Cannot read tags from {mp3path}')
                continue
            title = tags['TALB'][0]
            artist = tags['TPE1'][0]
            try:
                date = tags['TDRC'][0]
            except:
                date = ''
            try:
                markertext = tags[MARKER].text[0]
                markers = etree.fromstring(markertext)
            except KeyError:
                print(f'       ✗ Cannot create cue file for {mp3path}')
                continue
            
            with open(cuepath, 'w') as cuefile:
                cuefile.write(f'PERFORMER "{artist}"\n')
                cuefile.write(f'TITLE "{title}"\n')
                cuefile.write(f'REM DATE "{date}"\n')
                cuefile.write(f'FILE "{mp3path.name}" MP3\n')
                if first:
                    for index in range(pad):
                        cuefile.write(f'  TRACK {index + 1:02} AUDIO\n')
                        cuefile.write(f'    REM TRACK "{index + 1:02}"\n')
                        cuefile.write(f'    TITLE "{title}"\n')
                        cuefile.write( '    INDEX 01 00:00:00\n')
                for m in markers.iter():
                    if m.tag == 'Time':
                        cuefile.write(f'    INDEX 01 {time_format(m.text)}\n')
                    elif m.tag == 'Name':
                        cuefile.write(f'    TITLE "{m.text}"\n')
                    elif m.tag == 'Marker':
                        cuefile.write(f'  TRACK {count:02} AUDIO\n')
                        cuefile.write(f'    REM TRACK "{count:02}"\n')
                        count += 1
                # cuefile.write(f'  TRACK {count:02} AUDIO\n')
                # cuefile.write(f'    INDEX 01 {time_format(tags.info.length)}\n')
                cuefile.write('\n')
            first = False

def create_split_files(directory=SPLIT, replace_existing=False, 
                move_backups=True, backup_dir=SPLIT_BACKUP):
    directory = Path(directory)
    backup_dir = Path(backup_dir)
    dirs = get_leaf_dirs(directory)
    msg = f'Creating split mp3 files in {directory}'
    print(msg)
    print('‾'*len(msg))
    for book in dirs:
        print(f'  ⦾ {book.name}')
        mp3files = list(get_mp3_files(book))
        mp3files.sort()
        for mp3file in mp3files:
            cuefile = mp3file.with_suffix('.cue')
            if not cuefile.exists():
                continue
            args = [ 'mp3splt',
                     '-o',
                     '@b - Track @N2 - @t',
                     '-K',
                     '-a',
                     '-c',
                     cuefile.name,
                     mp3file.name,
                     ]
            subprocess.call(args, cwd=book)
            if move_backups:
                relpath = mp3file.relative_to(directory)
                backup_mp3 = unique_path(backup_dir / relpath)
                backup_cue = backup_mp3.with_suffix('.cue')
                os.renames(mp3file, backup_mp3)
                os.renames(cuefile, backup_cue)
                print(f" - {relpath}")

def remove_markers(directory=None):
    if directory == None:
        print('`directory` was not passed in')
        return
    dirs = get_leaf_dirs(directory)
    for book in dirs:
        print(f'  ⦾ {book.name}')
        mp3files = list(get_mp3_files(book))
        for mp3file in mp3files:
            print(f'    ‣ {mp3file.name}')
            try:
                tags = mutagen.id3.ID3(mp3file)
                tags.delall(MARKER)
                tags.save()
            except:
                print(f'Cannot read tags from {mp3path}')
                continue

def testing():
    directory=SPLIT
    dirs = get_leaf_dirs(directory)
    book = next(dirs)
    mp3files = list(get_mp3_files(book))
    mp3files.sort()
    mp3path = mp3files[0]
    tags = mutagen.File(mp3path)
    
