import os
import shutil
import errno
import mutagen


MAIN = "/Volumes/media/audiobooks/"
TEMP = '/Volumes/media/temp-audiobooks/'
NEW = '/Volumes/media/temp-audiobooks/new/'
HOLDING = "/Volumes/media/temp-audiobooks/holding-pen/"
FROM_CD = "/Volumes/media/temp-audiobooks/From CD/"
PHONE_BACKUPS = os.path.expanduser(
    '~/Library/Application Support/MobileSync/Backup')
KIDS = "/Volumes/media/sorted_audiobooks/kids_audiobooks"
KIDS_CHAPTERBOOKS = "/Volumes/media/sorted_audiobooks/kids_chapter_audiobooks/"


fail_codes = "🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉"

genre_dict = {
    'audiobook' : "Audiobook",
    'fiction' : "Fiction",

    'science-fiction' : "Science Fiction",
    'sci-fi' : "Science Fiction",
    'fantasy' : "Fantasy",
    'urban-fantasy' : "Urban Fantasy",
    'adventure' : "Adventure",
    'steampunk' : "Steampunk",

    'middle-grade' : "Middle Grades",
    'middle-grades' : "Middle Grades",
    'childrens' : "Children's",
    'children-s' : "Children's",
    'young-adult' : "Young Adult",

    'romance' : "Romance",
    'historical' : "Historical",
    'historical-fiction' : "Historical",
    'historical-romance' : "Historical Romance",
    'romance-historical' : "Historical Romance",
    'classic' : "Classics",

    'mystery' : "Mystery",
    'horror' : "Horror",
    'thriller' : "Thriller",
    'suspense' : "Suspense ",

    'superheroes' : "Superheroes",

    'non-fiction' : "Nonfiction",
    'nonfiction' : "Nonfiction",

    'humor' : "Humorous",
    'humour' : "Humorous",
    'comedy' : "Humorous",

    'graphic-novels' : "Comics",
    'comics' : "Comics",
    'graphic-novel' : "Comics",
    'comics-graphic-novels' : "Comics",
    'graphic-novels-comics' : "Comics",
    'comic-books' : "Comics",
    'comics-and-graphic-novels' : "Comics",
    
    'picture-books' : "Picture Books",
    'picture-book' : "Picture Books",
    'kids-picture-books' : "Picture Books",
    'preschool' : "Picture Books",
    'picturebooks' : "Picture Books",
}
gr_genres = set(genre_dict.keys())
my_genres = {genre_dict[x] for x in gr_genres}


def fail(n):
    # print(fail_codes[n], end='')
    pass

def succeed():
    # print("💎", end='')
    pass

def display_tags(path):
    print(f'Tags for {path}')
    try:
        tags = mutagen.File(path, easy=True)
    except mutagen.mp3.HeaderNotFoundError:
        print('Cannot read tags')
        return
    for key in tags.keys(): 
        print('        •', key.ljust(16), tags[key])
    print()

def preview_tags(dirs):
    for directory in dirs: 
        display_tags(get_mp3_files(directory)[0])

def mkdir_p(path):
    '''Makes directories, ignoring errors if it already exists'''
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

def copy(old, new):
    '''Copies a file from old to new, creating directories where necessary '''
    newpath = os.path.split(new)[0]
    mkdir_p(newpath)
    shutil.copy(old, new)

def merge(to_dir=MAIN, from_dir=NEW, overwrite=False):
    print(f"Merging files from {from_dir} to {to_dir}")
    for root, dirs, files in os.walk(from_dir, followlinks=True):
        for name in files:
            oldpathandname = os.path.join(root, name)
            relpath = os.path.relpath(oldpathandname, start=from_dir)
            newpathandname = os.path.join(to_dir,relpath)
            if overwrite or not os.path.exists(newpathandname):
                os.renames(oldpathandname, newpathandname)
                print(f" - {relpath}")

def organize_by_tag(root):
    for name in os.listdir(root):
        oldpathandname = os.path.join(root, name)
        try:
            tags = mutagen.File(oldpathandname, easy=True)
            authortag = tags['artist'][0]
            booktitletag = tags['album'][0].split(':')[0]
            newpathandname = os.path.join(root, authortag, booktitletag, name )
            os.renames(oldpathandname, newpathandname)
        except:
            pass

def makelist(startdir, limit=None):
    '''Makes a list of directories that only contain files (no directories)'''
    dirlist = []
    for root, dirs, files in os.walk(startdir, followlinks=True):
        if dirs == []:
            dirlist.append(root)
    if limit:
        return dirlist[:limit]
    return dirlist

def get_parent_folders(filelist):
    parent_folders = set()
    for f in filelist:
        parent_folders.add(os.path.dirname(f))

def get_dirs(startdir):
    if isinstance(startdir, str):
        dirs = makelist(startdir)
    else:
        dirs = startdir
    return dirs

def get_mp3_files(directory):
    return [os.path.join(directory, i)
                for i in os.listdir(directory) if i[-4:]=='.mp3']

def get_single_mp3(directory):
    allmp3s = get_mp3_files(directory)
    if allmp3s == []:
        return None
    return allmp3s[0]

