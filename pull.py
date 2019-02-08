from common import copy, fail, succeed, PHONE_BACKUPS, NEW, get_parent_folders
import os
import mutagen



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
        'filename' : tags['title'][0] + '.mp3',
        'title' : title,
        'author' : author,
        }


def get_and_tag(path, destination, organize=True, get=copy, dryrun=False):
    origpath, filename = os.path.split(path)

    info = set_tags(path)
    if info is None:
        return
    if organize:
        newpathandname = os.path.join(destination, info['author'], 
                                            info['title'], info['filename'] )
    else:
        newpathandname = os.path.join(destination, info['filename'])
    if os.path.exists(newpathandname):
        fail(5)
        return
    if not dryrun:
        get(path, newpathandname)
    succeed()
    return newpathandname


def pull_mp3_files(startdir=PHONE_BACKUPS, destination=NEW,
              organize=True, move_without_copying=False, dryrun=False):

    line = f"Pulling mp3 files from {startdir}:"
    print(f"{line}\n{'‾'*len(line)}")
    kwargs = {
        'destination' : destination,
        'dryrun' : dryrun,
        'organize' : organize,
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
    return mp3files




        