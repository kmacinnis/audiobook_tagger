import os
import shutil
import mutagen
from enum import Enum, auto
from pathlib import Path

from common import MAIN, NEW, KIDS_CHAPTERBOOKS


class OrgType(Enum):
    BOOK_ONLY = auto()
    AUTHOR_BOOK = auto()

def organize_by_tag(root, orgtype=OrgType.AUTHOR_BOOK):
    root = Path(root)
    for name in os.listdir(root):
        oldpathandname = root / name
        try:
            tags = mutagen.File(oldpathandname, easy=True)
        except:
            continue
        try:
            authortag = tags['artist'][0]
        except TypeError:
            authortag = None
        try:
            booktitletag = tags['album'][0].split(':')[0]
        except TypeError:
            booktitletag = None
        if orgtype == OrgType.AUTHOR_BOOK:
            if authortag is None or booktitletag is None:
                print(f"File `{name}` does not have tags for orginizing")
                continue
            relpath =  Path(authortag) / booktitletag / name
        elif orgtype == OrgType.BOOK_ONLY:
            if booktitletag is None:
                print(f"File `{name}` does not have tags for orginizing")
                continue
            relpath = Path(booktitletag) / name
        else:
            relpath = ''
            print("** orgtype not recognized **")
        newpathandname = root / relpath
        os.renames(oldpathandname, newpathandname)

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

def get_parent_folders(filelist):
    parent_folders = set()
    for f in filelist:
        parent_folders.add(os.path.dirname(f))

def move_to_final_destination(dirs=None, booklist=None):
    if booklist is None:                 
        if dirs is None:
            dirs = NEW
        books = makelist(dirs)
    else:
        books = booklist
    for b in books:
        book = Path(b)
        title = book.name
        author = book.parent.name
        samplefile = get_single_mp3(book)
        try:
            tags = mutagen.File(samplefile, easy=True)
        except TypeError:
            print(f"- No genre tags found in {b}")
            continue
        genres = tags['genre']
        if 'Middle Grades' in genres or "Children's" in genres:
            final_dir = KIDS_CHAPTERBOOKS
        else:
            final_dir = MAIN
        new_dir = Path(final_dir) / author / title
        if os.path.exists(new_dir):
            print(f"- {title} already exists in {final_dir}")
            continue
        shutil.move(book, new_dir)
        print(f"* {title} moved to {final_dir}")
    
def pull_contents_from_folder(directory, prefix_with_folder=False):
    print("«Pulling all files into parent folder»")
    if prefix_with_folder:
        for root, dirs, files in os.walk(directory):
            for name in files:
                filepathandname = Path(root) / name
                newpathandname = Path(root + ' -- ' + name)
                os.renames(filepathandname, newpathandname)
                try:
                    os.rmdir(root)
                except:
                    pass
    else:
        for root, dirs, files in os.walk(directory):
            for name in files:
                print(name)
                filepathandname = Path(root) / name
                newpathandname = Path(root).parent / name
                os.renames(filepathandname, newpathandname)
                print("*", newpathandname)


def delete_unwanted_files(directory):
    trashextensionlist = [  '.rar' , '.srr' , '.sfv' , '.nzb' , '.tbn' ,
                            '.nfo' , '.jpg' , '.gif' , '.png' , '.md5' , 
                            '.txt' , '.url' , '.par2' , '.par', '.srs'
                            '.0', '.1' , '.2' , '.3' , '.4' , '.5' , '.6' , '.7' , '.8' , '.9' ]
    
    for root, dirs, files in os.walk(directory):
        for name in files:
            filepathandname = Path(root) / name
            if filepathandname.suffix in trashextensionlist:
                os.remove(filepathandname)


