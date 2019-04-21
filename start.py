from change import *
from common import *
from audible import *
from pull import *
from images import *
from organize import *


def remove_copyright(text):
    if '&#169;' in text:
        text = text.split('&#169;')[0].rstrip(" ,/")
    if '©' in text:
        text = text.split('©')[0].rstrip(" ,/")
    if '(c)' in text:
        text = text.split('(c)')[0].rstrip(" ,/")
    return text

def remove_all_copyright_symbols(dirs):
    for directory in dirs:
        allmp3s = get_mp3_files(directory)
        for mp3file in allmp3s:
            tags = mutagen.File(mp3file, easy=True)
            changed = False
            if 'artist' in tags.keys():
                tags['artist'] = remove_copyright(tags['artist'][0])
                changed = True
            if 'composer' in tags.keys():
                tags['composer'] = remove_copyright(tags['composer'][0])
                changed = True
            if changed:
                tags.save()
                print(f"- Updated {directory}")

def check_if_books_exists(olddir=MAIN, newdir=NEW):
    books = makelist(newdir)
    duplicates = []
    for book in books[:]:
        relpath = os.path.relpath(book, start=newdir)
        checkpath = os.path.join(olddir, relpath)
        print(relpath)
        if os.path.exists(checkpath):
            print("  - duplicate")
            books.remove(book)
            duplicates.append(relpath)
        else:
            print("  - new")
    return {'books': books, 'duplicates': duplicates}

def remove_after_parens(dirs):
    for directory in dirs:
        allmp3s = get_mp3_files(directory)
        for mp3file in allmp3s:
            tags = mutagen.File(mp3file, easy=True)
            changed = False
            title = tags['album'][0]
            if '(' in title:
                tags['album'] = title.split('(')[0]
                tags.save()
        print(f"- Updated {directory}")

