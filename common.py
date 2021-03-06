import os
import shutil
import errno
import mutagen
import urllib
from pathlib import Path

from private import BASE_WORKING_PATH, BASE_STORAGE_PATH, JUMBLED_JUNK_DIR

MAIN = BASE_STORAGE_PATH / '/Volumes/mangomedia/MediaSections/AudioSections/audiobooks/'
TEMP = BASE_WORKING_PATH / 'temp'
NEW = BASE_WORKING_PATH / 'new/'
HOLDING = BASE_WORKING_PATH / "holding-pen/"
FROM_CD = BASE_WORKING_PATH / "From CD/"
SPLIT = BASE_WORKING_PATH / 'split/'
SPLIT_OUTPUT = BASE_WORKING_PATH / 'split_output/'
SPLIT_BACKUP = BASE_WORKING_PATH / 'split_backup/'



DESKTOP = Path('~/Desktop/').expanduser()
KIDS = BASE_STORAGE_PATH / "kids_audiobooks"
KIDS_CHAPTERBOOKS = BASE_STORAGE_PATH / 'kids_chapter_audiobooks'

AUDIOFILE_EXTENSIONS = ('.mp3', '.ogg')


fail_codes = "π°π±π²π³π΄π΅πΆπ·πΈπΉπΊπ»πΌπ½πΎπΏππππππππππ"

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


def is_audiofile(item):
    item = Path(item)
    return item.suffix in AUDIOFILE_EXTENSIONS

def fail(n):
    # print(fail_codes[n], end='')
    pass

def succeed():
    # print("π", end='')
    pass

def display_tags(path):
    print(f'Tags for {path}')
    try:
        tags = mutagen.File(path, easy=True)
    except mutagen.mp3.HeaderNotFoundError:
        print('Cannot read tags')
        return
    for key in tags.keys():
        print('        β’', key.ljust(16), tags[key])
    print()

def preview_tags(dirs):
    for directory in dirs:
        display_tags(get_mp3_files(directory)[0])

def copy(old, new):
    '''Copies a file from old to new, creating directories where necessary '''
    newpath = os.path.split(new)[0]
    os.makedirs(newpath, exist_ok=True)
    shutil.copy(old, new)


def makelist(startdir, limit=None):
    '''Makes a list of directories that only contain files (no directories)'''
    dirlist = []
    for root, dirs, files in os.walk(startdir, followlinks=True):
        if dirs == []:
            dirlist.append(Path(root))
    if limit:
        return dirlist[:limit]
    return dirlist

def get_leaf_dirs(topdir):
    return ( Path(root)
             for root, dirs, files
             in os.walk(topdir, followlinks=True)
             if dirs == []
             )


def get_dirs(dirs):
    try:
        main_dir = Path(dirs)
    except TypeError:
        pass
    else:
        dirs = get_leaf_dirs(main_dir)
    return dirs

def get_mp3_files(directory):
    directory = Path(directory)
    return [directory / i for i in directory.iterdir() if i.suffix=='.mp3']

def get_audio_files(directory):
    return (item for item in Path(directory).iterdir() if is_audiofile(item))

def get_single_mp3(directory):
    allmp3s = get_mp3_files(directory)
    if allmp3s == []:
        return None
    return allmp3s[0]

def flatten(source_dir, new_dir=None, overwrite=False):
    if new_dir is None:
        new_dir = Path(source_dir)
    print(f"Move files nested in {source_dir} to be flatly in {new_dir}")
    for root, dirs, files in os.walk(source_dir, followlinks=False):
        for name in files:
            if name == ".DS_Store":
                continue
            oldpathandname = Path(root) / name
            newpathandname = Path(new_dir) / name
            if not overwrite:
                newpathandname = unique_path(newpathandname)
            print(f" - {name}")
            os.renames(oldpathandname, newpathandname)

def delete_unwanted_files(directory):
    trashextensionlist = [  '.rar' , '.srr' , '.sfv' , '.nzb' , '.tbn' ,
                            '.nfo' , '.md5' ,
                            '.txt' , '.url' , '.par2' , '.par', '.srs'
                            '.0', '.1' , '.2' , '.3' , '.4' ,
                            '.5' , '.6' , '.7' , '.8' , '.9' ]

    for root, dirs, files in os.walk(directory):
        for name in files:
            filepathandname = Path(root) / name
            if filepathandname.suffix in trashextensionlist:
                os.remove(filepathandname)

def delete_all_files(directory):
    for root, dirs, files in os.walk(directory):
        for name in files:
            os.remove(Path(root) / name)

def unique_path(filepath):
    counter = 0
    if not filepath.is_absolute():
        raise TypeError('filepath must be absolute path.')
    path = filepath
    origext = filepath.suffix
    origname = filepath.name.rstrip(origext)
    name_pattern = '{origname} ({counter}){origext}'
    while True:
        if not path.exists():
            return path
        counter += 1
        formatter = {'origname':origname, 'counter':counter, 'origext':origext}
        name = name_pattern.format(**formatter)
        path = filepath.with_name(name)


def safe_string(text):
    text = text.replace('&','')
    return urllib.parse.quote_plus(text)



