import mutagen
import xml.etree.ElementTree as etree

from common import get_mp3_files, get_leaf_dirs, SPLIT, SPLIT_OUTPUT
from pathlib import Path





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
                markertext = tags['TXXX:OverDrive MediaMarkers'].text[0]
                markers = etree.fromstring(markertext)
            except KeyError:
                print(f'Cannot create cue file for {mp3path}')
                print(tags.keys())
                continue
            xmlpath = mp3path.parent / (mp3path.stem + '.xml')
            with open(xmlpath, 'w') as xmlfile:
                xmlfile.write(markertext)
                
            




def make_cue_sheets(directory=SPLIT, replace_existing=False):
    dirs = get_leaf_dirs(directory)
    msg = f'Extracting tag to create cue sheets for files in {directory}'
    print(msg)
    print('‾'*len(msg))
    for book in dirs:
        print(f'  ⦾ {book.name}')
        mp3files = list(get_mp3_files(book))
        mp3files.sort()
        count = 1
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
            try:
                title = tags['TALB'][0]
                artist = tags['TPE1'][0]
                date = tags['TDRC'][0]
            except:
                print(f'Set title/artist/date for {mp3path}')
                continue
            try:
                markertext = tags['TXXX:OverDrive MediaMarkers'].text[0]
                markers = etree.fromstring(markertext)
            except KeyError:
                print(f'Cannot create cue file for {mp3path}')
                print(tags.keys())
                continue
            
            with open(cuepath, 'w') as cuefile:
                cuefile.write(f'PERFORMER "{artist}"\n')
                cuefile.write(f'TITLE "{title}"\n')
                cuefile.write(f'REM DATE "{date}"\n')
                cuefile.write(f'FILE "{mp3path.name}" MP3\n')
                for m in markers.iter():
                    if m.tag == 'Time':
                        cuefile.write(f'    INDEX 01 {time_format(m.text)}\n')
                    elif m.tag == 'Name':
                        cuefile.write(f'    TITLE "{m.text}"\n')
                    elif m.tag == 'Marker':
                        cuefile.write(f'  TRACK {count:02} AUDIO\n')
                        cuefile.write(f'    REM TRACK "{count:02}"\n')
                        count += 1
                cuefile.write(f'  TRACK {count:02} AUDIO\n')
                cuefile.write(f'    INDEX 01 {time_format(tags.info.length)}\n')
                cuefile.write('\n')
            

def testing():
    directory=SPLIT
    dirs = get_leaf_dirs(directory)
    book = next(dirs)
    mp3files = list(get_mp3_files(book))
    mp3files.sort()
    mp3path = mp3files[0]
    tags = mutagen.File(mp3path)
    
