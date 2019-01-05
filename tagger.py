import os
import mutagen


DONE = '/Volumes/media/temp-audiobooks/done/'



def movefiles(path):

    def setifempty(tagname, value):
        if tagname not in tags.keys():
            tags[tagname] = value

    origpath, filename = os.path.split(path)  
    tags = mutagen.File(path, easy=True)
    title, track = tags['title'][0].split(' - Part ')
    artist_tag = tags['artist']
    if artist_tag is not None:
        creators = artist_tag[0].split('/')
        author = creators[0]
        narrator = ', '.join(creators[1:])
    
        setifempty('artist', author)
        setifempty('composer', narrator)
    else:
        author = 'Unknown Author'

    setifempty('tracknumber', track.lstrip('0'))
    setifempty('album', title)
    tags.save()
    
    newpath = os.path.join(origpath, author, title, filename)
    os.renames(path, newpath)

def tagfile(path):
    origpath, filename = os.path.split(path)
    try:
        tags = mutagen.File(path, easy=True)
    except mutagen.mp3.HeaderNotFoundError:
        return
    if 'title' not in tags.keys():
        return
    
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
    
    filename = tags['title'][0]
    newpath = os.path.join(origpath, author, title, filename)
    os.renames(path, newpath)
    
    
def tag_all_files(maindir):
    for item in os.listdir(maindir):
        f = os.path.join(maindir,item)
        if f[-4:] == '.mp3':
            print(f)
            tagfile(f)


# def organize_files(maindir):
#     for item in os.listdir(maindir):
#         f = os.path.join(maindir,item)
#         if f[-4:] == '.mp3':
#             print(f)
#             movefiles(f)



def tag_and_copy(path):
    origpath, filename = os.path.split(path)
    try:
        tags = mutagen.File(path, easy=True)
    except mutagen.mp3.HeaderNotFoundError:
        return
    if 'title' not in tags.keys():
        return
    
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
    
    filename = tags['title'][0]
    newpath = os.path.join(origpath, author, title, filename)
    os.renames(path, newpath)



