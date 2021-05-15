from change import *
from common import *
from covers import *
from audible import *
from pull import *
from images import *
from organize import *
from splitter import *


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
    books = get_leaf_dirs(newdir)
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

def set_initial_tags(dirs):
    for bookdir in dirs:
        mp3files = [os.path.join(bookdir, i)
                    for i in os.listdir(bookdir) if i[-4:]=='.mp3']
        for mp3file in mp3files:
            set_tags(os.path.join(bookdir,mp3file))

def find_dateless(dirs=MAIN):
    dateless = []
    books = get_leaf_dirs(MAIN)
    for book in books:
        try:
          mp3 = get_single_mp3(book)
          tags = mutagen.File(mp3)
          if 'TDRC' not in tags.keys():
            dateless.append(book)
        except TypeError as e:
            print(e)
            print(book)
            print(mp3)
    return dateless


def find_shortdates(dirs=MAIN):
    bad_dates = []
    books = get_leaf_dirs(MAIN)
    for book in books:
        try:
          mp3 = get_single_mp3(book)
          tags = mutagen.File(mp3, easy=True)
          date = tags['date'][0]
          if len(date) < 8:
              bad_dates.append({'dir':book, 'date':date})
        except TypeError as e:
            print(e)
            print(book)
            print(mp3)
    return bad_dates

def fix_shortdates(dirs=MAIN):
    dateless = []
    books = get_leaf_dirs(MAIN)
    for book in books:
        try:
            mp3s = get_mp3_files(book)
            for mp3 in mp3s:
                tags = mutagen.File(mp3, easy=True)
                try:
                    date = tags['date'][0]
                except KeyError:
                    dateless.append(mp3)
                    continue
                if len(date) == 6:
                    tags['date'] = date + '01'
                    tags.save()
                elif len(date) == 4:
                    tags['date'] = date + '0101'
                    tags.save()
        except:
            print(mp3)

def fix_dateless(dirs=MAIN,dateless=None):
    nomatch = []
    nodate =[]
    if dateless is None:
        dateless = find_dateless(dirs=dirs)
    for d in dateless:
        mp3 = get_mp3_files(d)[0]
        tags = mutagen.File(mp3, easy=True)
        try:
            result = match(goodreads_client,tags)
            book = result['result']
        except:
            nomatch.append(d)
            continue
        pubdate = get_pubdate(book)
        if pubdate and pubdate != (None,None,None):
            tags['date'] = pubdate
            tags.save()
        else:
            nodate.append(d)
    return {'no date': nodate,
            'no match': nomatch}


def get_pubdate(book):
    try:
        year = book.work['original_publication_year']['#text']
    except KeyError:
        year = None
    try:
        month = book.work['original_publication_month']['#text']
    except KeyError:
        month = None
    try:
        day = book.work['original_publication_day']['#text']
    except KeyError:
        day = None
    if year and month and day:
        pubdate = f'{year}{month:0>2}{day:0>2}'
    elif year and month:
        pubdate = f'{year}{month:0>2}01'
    else:
        pubdate = year
    if pubdate is None:
        month, day, year = book.publication_date
        try:
            pubdate = f'{year}{month:0>2}{day:0>2}'
        except:
            return 
    return pubdate
