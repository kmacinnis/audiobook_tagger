from common import ( copy, fail, succeed, 
                     PHONE_BACKUPS, NEW, KIDS_CHAPTERBOOKS, KIDS, MAIN )
from organize import get_parent_folders
from database import ( add_info_to_database, add_info_to_db_cursor, 
                        item_exists, author_exists, DATABASEFILE )
import os
from pathlib import Path
import sqlite3
import mutagen


SLASH_SUBSTITUTE = '-'


def set_tags(path):
    
    def remove_copyright(text):
        if '&#169;' in text:
            text = text.split('&#169;')[0]
        if '©' in text:
            text = text.split('©')[0]
        return text
        
    try:
        tags = mutagen.File(path, easy=True)
    except mutagen.mp3.HeaderNotFoundError:
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
    try:
        title, track = tags['title'][0].split(' - Part ')
        title = title.replace('/',SLASH_SUBSTITUTE)
    except ValueError:
        try:
            title = tags['album'][0]
            track = tags['tracknumber'][0]
        except KeyError:
            fail(4)
            return   # can't figure out title & track from filename or tags
    if 'artist' in tags.keys() and 'composer' in tags.keys():
        author = remove_copyright(tags['artist'][0])
        tags['artist'] = author
        tags['composer'] = remove_copyright(tags['composer'][0])
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
        album, series = tags['album'][0].split(' - ')
        tags['album'] = album
        tags['version'] = series
    tags.save()
    return {
        'filename' : tags['title'][0].replace('/',SLASH_SUBSTITUTE) + '.mp3',
        'title' : title,
        'author' : author,
        }


def get_and_tag(path, destination, organize=True, get=copy, 
        dryrun=False, check_exists=True, cursor=None):

    origpath, filename = os.path.split(path)
    info = set_tags(path)
    if info is None:
        return
    info['oldfile'] = filename
    destination = Path(destination)
    if organize:
        newpathandname = destination / info['author'] / info['title'] / info['filename']
        authorpath = destination /  info['author']
    else:
        newpathandname = destination / info['filename']
    if os.path.exists(newpathandname):
        fail(5)
        return
    if check_exists:
        if item_exists(info, cursor=cursor):
            fail(6)            
            print(f"   file not copied:  {info['filename']}")
            return
        if not author_exists(info, cursor=cursor):
            needs_photo = authorpath / '_ needs photo'
            needs_photo.parent.mkdir()
            needs_photo.touch()
    if cursor is None:
        add_info_to_database(info)
    else:
        add_info_to_db_cursor(info, cursor)
    if not dryrun:
        get(path, newpathandname)
    succeed()
    return newpathandname


def pull_mp3_files(startdir=PHONE_BACKUPS, destination=NEW,
              organize=True, move_without_copying=False, dryrun=False,
              check_exists=True):

    line = f"Pulling mp3 files from {startdir}:"
    print(f"{line}\n{'‾'*len(line)}")
    connection = sqlite3.dbapi2.connect(DATABASEFILE)
    cursor = connection.cursor() 
    kwargs = {
        'destination' : destination,
        'dryrun' : dryrun,
        'organize' : organize,
        'check_exists' :check_exists,
        'cursor' : cursor,
    }
    mp3files = []
    if move_without_copying:
        get = os.renames
    else:
        get = copy
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




        