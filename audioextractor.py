import os
import magic
import errno
import shutil
import mutagen
# from mutagen.easyid3 import EasyID3 as ezid3

from tagger import tagfile
from common import copy

MIME_EXT = {
    'application/octet-stream': '.mp3',
    'application/zip': '.zip',
    'audio/mpeg': '.mp3',
    'audio/x-m4a': '.m4a',
    'audio/x-mp4a-latm': '.m4a',
    'audio/x-wav': '.wav',
    'video/3gpp': '.3gp',
    'video/mp4': '.mp4',
    'video/quicktime': '.mov',
}


DESIRED_TYPES = [
    # These are the only ones that I've found audiobooks in
    'application/octet-stream',
    'audio/mpeg',
]

VIDEO_TYPES = [
    'video/3gpp',
    'video/mp4',
    'video/quicktime',
]

PHONE_BACKUPS = os.path.expanduser(
    '~/Library/Application Support/MobileSync/Backup')
# DESTINATION = os.path.expanduser(
#     '~/Desktop/Copied from phone')
DESTINATION = '/Volumes/media/temp-audiobooks/'
NEW = '/Volumes/media/temp-audiobooks/new/'


# This is something I use as a scratch folder.
rubble = '/Users/kate/Desktop/rubble/'





def list_mimetypes(startdir=PHONE_BACKUPS):
    '''Returns a list of the mimetypes of the files in startdir '''
    mimetypes = []
    for root, dirs, files in os.walk(startdir, followlinks=True):
        for name in files:
            filepathandname = os.path.join(root, name)
            mimetype = magic.from_file(filepathandname, mime=True)
            if mimetype not in mimetypes:
                mimetypes.append(mimetype)
    return mimetypes


def sort_files_by_mimetype(startdir, destination=DESTINATION, copy=True):
    """Organize files in directory tree by mimetype"""
    if copy:
        do = copy
    else:
        do = os.renames
    for root, dirs, files in os.walk(startdir, followlinks=True):
        for name in files:
            filepathandname = os.path.join(root, name)
            mimetype = magic.from_file(filepathandname, mime=True)
            newpathandname = os.path.join(destination, mimetype, name)
            do(filepathandname, newpathandname)




def copy_desired_files(startdir=PHONE_BACKUPS, destination=DESTINATION,
                      desired_types=DESIRED_TYPES, move_without_copying=True):
    if move_without_copying:
        do = os.renames
    else:
        do = copy
    for root, dirs, files in os.walk(startdir, followlinks=True):
        for name in files:
            filepathandname = os.path.join(root, name)
            mimetype = magic.from_file(filepathandname, mime=True)
            if mimetype in desired_types:
                ext = MIME_EXT[mimetype]
                try:
                    newname = ezid3(filepathandname)['title'][0] + ext
                except:
                    newname = name + ext

                newpathandname = os.path.join(destination, mimetype, newname)
                do(filepathandname, newpathandname)




def add_mp3_extension(maindir):
    for root, dirs, files in os.walk(maindir):
        for name in files:
            filepathandname = os.path.join(root, name)
            if os.path.splitext(name)[1] == '':
                os.rename(filepathandname, filepathandname + '.mp3')
    
    
    
    
#
# def check_unknown_files(startdir=PHONE_BACKUPS, destination=DESTINATION, copy=True):
#     if copy:
#         do = copy
#     else:
#         do = os.renames
#     for root, dirs, files in os.walk(startdir, followlinks=True):
#         for name in files:
#             filepathandname = os.path.join(root, name)
#             mimetype = magic.from_file(filepathandname, mime=True)
#             if mimetype == 'application/octet-stream':
#                 try:
#                     newname = ezid3(filepathandname)['title'][0] + '.mp3'
#                     newpathandname = os.path.join(destination, mimetype, newname)
#                     do(filepathandname, newpathandname)
#                 except mutagen.id3.ID3NoHeaderError:
#                     pass

def tagfile(path):
    origpath, filename = os.path.split(path)  
    tags = mutagen.File(path, easy=True)
    try:
        title, track = tags['title'][0].split(' - Part ')
    except ValueError:
        try:
            title = tags['album'][0]
            track = tags['tracknumber'][0]
        except KeyError:
            return   # can't figure out title & track from filename or tags
    if 'artist' in tags.keys():
        artist_tag = tags['artist']
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
    tags.save()
    
    newpath = os.path.join(origpath, author, title, filename)
    os.renames(path, newpath)





def get_overdrive_files(startdir=PHONE_BACKUPS, destination=DESTINATION,
                  sorted=True, copy=True, dryrun=False):
    """I don't know"""
    mp3files = []
    if copy:
        do = copy
    else:
        do = os.renames
    for root, dirs, files in os.walk(startdir, followlinks=True):
        for name in files:
            icon = '.'
            filepathandname = os.path.join(root, name)
            tags = mutagen.File(filepathandname, easy=True)
            if tags:
                if 'genre' in tags.keys():                
                    if tags['genre'] in (['Ringtone'],['Other']):
                        break
                try:
                    try:
                        newname = tags['title'][0]    
                        title, track = newname.split(' - Part ')
                    except ValueError:
                        try:
                            title = tags['album'][0]
                            track = tags['tracknumber'][0]
                        except KeyError:
                            # this means it will only work with Overdrive 
                            break                
                    if 'artist' in tags.keys():
                        artist_tag = tags['artist']
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
                    tags.save()
                    if sorted:
                        newpathandname = os.path.join(destination, author, title, newname + '.mp3')
                    else:
                        newpathandname = os.path.join(destination, newname)

                    mp3files.append(newname)
                    if dryrun:
                        break
                    icon = '-'
                    if not os.path.exists(newpathandname) and newname != '.':
                        do(filepathandname, newpathandname)
                        tagfile(newpathandname)
                        icon = '*'
                except KeyError:
                    pass
            print(icon, end='')
        mp3files.sort()
    return mp3files


def get_ringtones(startdir=NEW, destination=DESTINATION, copy=False, dryrun=False):
    mp3files = []
    if copy:
        do = copy
    else:
        do = os.renames
    for root, dirs, files in os.walk(startdir, followlinks=True):
        for name in files:
            icon = '.'
            filepathandname = os.path.join(root, name)
            tags = mutagen.File(filepathandname, easy=True)
            if tags:
                try:
                    if tags['genre'] in (['Ringtone'],['Other']):
                        newname = tags['title'][0] + '.mp3'
                        if dryrun:
                            break
                        newpathandname = os.path.join(destination, 'ringtones', newname)
                        mp3files.append(newname)
                        if not os.path.exists(newpathandname) and newname != '..mp3':
                            do(filepathandname, newpathandname)
                except KeyError:
                    pass
            print('.', end='')
    return mp3files
            


