import os
import magic
import errno
import shutil
import mutagen
from collections import defaultdict

from tagger import tagfile
from common import copy, PHONE_BACKUPS, NEW

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
    "application/epub+zip" : '.epub',
    'text/xml' : '.xml',
    'text/vcard': '.vcard',
     'text/x-python': '.py',
     'text/html': '.html',
     'text/x-asm': '.asm',
     'text/plain': '.txt',
     'image/png': '.png',
     'image/x-ms-bmp': '.bmp',
     'image/x-tga': '.tga',
     'image/jpeg': '.jpeg',
     'image/tiff': '.tiff',
     'image/gif': '.gif',
     'image/x-icon': '.ico',
     'video/quicktime': '.mov',
     'video/3gpp': '.3gp',
     'video/mp4': '.mp4',
     'inode/x-empty': '',
     'application/x-tplink-bin': '.bin',
     'application/vnd.ms-opentype': '.otf',
     'application/x-wine-extension-ini': '.ini',
     'application/octet-stream': '.a',
     'application/json': '.json',
     'application/x-dosexec': '.exec',
     'application/epub+zip': '.epub',
     'application/vnd.lotus-1-2-3': '.123',
     'application/x-gzip': '.gzip',
     'application/zip': '.zip',
     'application/x-sqlite3': '.db',
     'application/pdf': '.pdf',
     'audio/x-mp4a-latm': '.m4a',
     'audio/x-wav': '.wav',
     'audio/amr': '.amr',
     'audio/x-m4a': '.m4a',
     'audio/mpeg': '.mp3'
}
MIME_EXT = defaultdict(lambda: "", MIME_EXT) 

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

EBOOK_TYPES = [
    'application/epub+zip',
    'application/zip',
    ''
]

MIME_DEST = '/Volumes/mangomedia/temp-audiobooks/by_mime/'


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

def pull_by_mimetype(startdir=PHONE_BACKUPS, destination=MIME_DEST, 
                                                move_without_copying=False):
    """Organize files in directory tree by mimetype"""
    if move_without_copying:
        do = os.renames
    else:
        do = copy
    for root, dirs, files in os.walk(startdir, followlinks=True):
        for name in files:
            filepathandname = os.path.join(root, name)
            mimetype = magic.from_file(filepathandname, mime=True)
            newpathandname = os.path.join(destination, mimetype, name)
            ext = MIME_EXT[mimetype]
            do(filepathandname, newpathandname)

def copy_desired_files(startdir=PHONE_BACKUPS, destination=MIME_EXT,
                      desired_types=DESIRED_TYPES, move_without_copying=False):
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

def add_extensions(maindir=MIME_DEST):
    for root, dirs, files in os.walk(maindir):
        relpath = os.path.relpath(root, start=maindir)
        mimetype = relpath.strip('/')
        print(repr(mimetype))
        try:
            ext = MIME_EXT[mimetype]
            print(ext)
        except:
            continue
        for name in files:
            filepathandname = os.path.join(root, name)
            if os.path.splitext(name)[1] == '':
                os.rename(filepathandname, filepathandname + ext)


def get_ringtones(startdir=NEW, destination=MIME_DEST, copy=False, dryrun=False):
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
            


