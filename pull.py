import os
import mutagen
import sqlite3
from pathlib import Path

from common import ( copy, fail, succeed, unique_path,
                     JUMBLED_JUNK_DIR, NEW, KIDS_CHAPTERBOOKS, KIDS, MAIN )
from database import ( add_info_to_database, add_info_to_db_cursor,
                        item_exists, author_exists, DATABASEFILE )


SLASH_SUBSTITUTE = '-'
COLON_SUBSTITUTE = '\uA789'

def set_tags(path, **kwargs):

    def remove_copyright(text):
        if '&#169;' in text:
            text = text.split('&#169;')[0]
        if '©' in text:
            text = text.split('©')[0]
        return text

    try:
        tags = mutagen.File(path, easy=True)
    except mutagen.MutagenError:
        fail(0)
        return
    if tags == None:
        fail(1)
        return
    if 'title' not in tags.keys():
        fail(2)
        return
    if 'genre' in tags.keys():
        if tags['genre'] in (['Ringtone'],['Other']):
            fail(3)
            return
    titletrack = tags['title'][0]
    if ' - Part' in titletrack:
        title, track = tags['title'][0].split(' - Part ')
    elif ' - Disc' in titletrack:
        title, track = tags['title'][0].split(' - Disc ')
    else:
        try:
            title = tags['album'][0]
            track = tags['tracknumber'][0]
        except KeyError:
            fail(4)
            return   # can't figure out title & track from filename or tags
    if 'artist' in tags.keys() and 'composer' in tags.keys():
        tags['artist'] = remove_copyright(tags['artist'][0])
        tags['composer'] = remove_copyright(tags['composer'][0])
        author = tags['artist'][0]
    elif 'artist' in tags.keys() and 'composer' not in tags.keys():
        artist_tag = remove_copyright(tags['artist'])
        creators = artist_tag[0].split('/')
        author = creators[0]
        narrator = ', '.join(creators[1:])
        tags['artist'] = author
        tags['composer'] = narrator
    else:
        author = 'Unknown Author'

    if 'tracknumber' not in tags.keys():
        tags['tracknumber'] = track.lstrip('0')
    if 'album' not in tags.keys():
        tags['album'] = title
    if ' - ' in tags['album'][0]:
        try:
            album, series = tags['album'][0].split(' - ')
            tags['album'] = album
            tags['version'] = series
        except ValueError: # more than one " - " in album won't unpack
            pass
    if kwargs.get('change_tags', True):
        tags.save()
    return {
        'filename' : titletrack.replace(':',COLON_SUBSTITUTE
                                    ).replace('/',SLASH_SUBSTITUTE) + '.mp3',
        'title' : title,
        'author' : author,
        }


def get_and_tag(path, destination, organize=True, get=copy,
        dryrun=False, check_exists=True, cursor=None, **kwargs):

    origpath, filename = os.path.split(path)
    try:
        info = set_tags(path, **kwargs)
    except mutagen.MutagenError:
        info = None
    if info is None:
        return
    info['oldfile'] = filename
    destination = Path(destination)
    if organize:
        newpathandname = destination / info['author'] / info['title'] / info['filename']
        authorpath = destination /  info['author']
    else:
        newpathandname = destination / info['filename']
    newpathandname = unique_path(newpathandname)
    if os.path.exists(newpathandname):
        fail(5)
        return
    if check_exists:
        if item_exists(info, cursor=cursor):
            fail(6)
            print(f"   file not copied:  {info['filename']}")
            return
        else:
            try:
                authorpath.mkdir(parents=True, exist_ok=True)
            except NameError:
                pass
        if not author_exists(info, cursor=cursor):
            needs_photo = authorpath / '_ needs photo'
            needs_photo.touch()
    if cursor is None:
        add_info_to_database(info)
    else:
        add_info_to_db_cursor(info, cursor)
    if not dryrun:
        get(path, newpathandname)
    succeed()
    return newpathandname


def pull_mp3_files(startdir=JUMBLED_JUNK_DIR, destination=NEW,
              organize=True, move_without_copying=False, dryrun=False,
              check_exists=True, change_tags=True):

    line = f"Pulling mp3 files from {startdir}:"
    print(f"{line}\n{'‾'*len(line)}")
    connection = sqlite3.dbapi2.connect(DATABASEFILE)
    cursor = connection.cursor()
    mp3files = []
    if move_without_copying:
        get = os.renames
    else:
        get = copy
    kwargs = {
        'destination' : destination,
        'dryrun' : dryrun,
        'organize' : organize,
        'check_exists' :check_exists,
        'cursor' : cursor,
        'get' : get,
        'change_tags' : change_tags,
    }
    for root, dirs, files in os.walk(startdir, followlinks=True):
        for name in files:
            filepathandname = os.path.join(root, name)
            newpath = get_and_tag(filepathandname, **kwargs)
            if newpath:
                mp3files.append(newpath)
                print(newpath)
    cursor.close()
    connection.close()
    return mp3files




