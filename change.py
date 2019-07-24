import mutagen
from mutagen.id3 import ID3, COMM, Encoding
from pathlib import Path
from enum import Enum, auto 

from pull import set_tags
from common import get_mp3_files, gr_genres, genre_dict, get_dirs, makelist
from Levenshtein import distance
import os

from goodreads import client
API_KEY = "iaqF5jmbfkRAsudBGVHXLg"
CLIENT_SECRET = "2Af9zFVtOHVAlJcCM9DjymoeOMFKv6ePo1YC3GhxaQg"
goodreads_client = client.GoodreadsClient(API_KEY, CLIENT_SECRET)

SCORE_THRESHOLD = 5
startdir = "/Volumes/mangomedia/audiobooks/"


class MatchStyle(Enum):
    ''' Ways of handling matching. 
    "Good match" here is defined as matches that have a score
    (see function `score_match`) lower than `SCORE_THRESHOLD`
    '''
    # `AUTO` - skip items that don't have a good match
    AUTO = auto() 
    
    # `SEMIAUTO` - ask user to match items that don't have a good match
    SEMIAUTO = auto()
    
    # `MANUAL` - ask user to match each item
    MANUAL = auto()


def clean(title):
    return title.split(' (')[0]

def score_match(grbook, tags):
    author_score = distance(tags['artist'][0], str(grbook.authors[0]))
    title_score = distance(clean(tags['album'][0]), clean(grbook.title))
    return author_score + title_score

def match(gc, tags, match_style = MatchStyle.SEMIAUTO):
    authortag = tags['artist'][0]
    booktitletag = tags['album'][0]
    search_query = f'{booktitletag} - {authortag}'
    print(f'   Searching goodreads for: {search_query}')
    try:
        results = gc.search_books(search_query)
    except:
        print("   Trouble getting results from goodreads.")
        return
    score_chart = []
    for i, result in enumerate(results[:5]):
        author_score = distance(authortag, str(result.authors[0]))
        title_score = distance(clean(booktitletag), clean(result.title))
        score = author_score + title_score
        score_chart.append({'score': score, 'result': result})
    score_chart.sort(key=lambda k: k['score'])
    if match_style == MatchStyle.AUTO:
        return score_chart[0]
    elif match_style == MatchStyle.SEMIAUTO:
        if score_chart[0]['score'] < SCORE_THRESHOLD:
            return score_chart[0]
    for i, item in enumerate(score_chart, 1):
        book = item['result']
        score = item['score']
        print(f"    {i}. {book.title} - {book.authors[0]}   (score: {score}) ")
    
    n = input("   Enter line number (or non-number to skip): ")
    try:
        num = int(n) - 1
    except:
        return None
    result = score_chart[num]
    result['score'] = -1
    return result


def update_tags(dirs, match_style=MatchStyle.SEMIAUTO, dryrun=False):
    '''Updates date tag with original publication date from goodreads,
    updates track number to contain totaltracks,
    
    Optional arg `auto` will skip books that don't match under SCORE_THRESHOLD
    '''
    dirs = get_dirs(dirs)   
    gc = goodreads_client
    failures = []
    successes = []
    for index, directory in enumerate(dirs):
        print(f'<{index}> {directory}')
        mp3files = get_mp3_files(directory)
        if mp3files == []:
            continue
        tags = mutagen.File(mp3files[0], easy=True)
        result = match(gc, tags)
        if result is None:
            print("************* Problem matching book.")
            print("************* No results from goodreads")
            print()
            failures.append(directory)
            continue
        elif result['score'] > SCORE_THRESHOLD:
            print("************* Problem matching book.")
            print(f"************* Best match is {result} ")
            print()
            failures.append(directory)
            continue
        else:
            book = result['result']
            print(f'   Matched to {book}' )
        totaltracks = len(mp3files)
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
            pubdate = f'{year}{month:0>2}'
        else:
            pubdate = year
        if book.series_works:
            try:
                series_dict = book.series_works['series_work'][0]
            except:
                series_dict = book.series_works['series_work']
        else:
            series_dict = None
        try:
            shelves = {shelf.name for shelf in book.popular_shelves[:10]}
        except:
            shelves = set()
        shelves.add('audiobook')
        genres = {genre_dict[i] for i in shelves.intersection(gr_genres)}
        genres = list(genres)
        for item in mp3files:
            try:
                tags = mutagen.File(item, easy=True)
            except mutagen.MutagenError:
                print(f"\n ✖ Cannot read mpeg headers in {item} \n\n ")
                continue
            print(f"   - {tags['title'][0]}")
            try:
                origdate = tags['date'][0]
            except KeyError:
                origdate = None
            if pubdate and (origdate != pubdate):
                tags['date'] = pubdate
                print(f"     • Changed date from {origdate} to {pubdate}")
            tracktag = tags['tracknumber'][0]
            if '/' not in tracktag:
                newtracktag = f'{tracktag}/{totaltracks}'
                tags['tracknumber'] = newtracktag
                print(f"     • Changed track number from {tracktag} to {newtracktag}")
            if 'language' in tags.keys() and tags['language'] == ['XXX']:
                tags['language'] = 'English'
                print(f"     • Changed language from 'XXX' to 'English'")
            if series_dict:
                try:
                    orig_version = tags['version'][0]
                except KeyError:
                    orig_version = None
                series_title = series_dict['series']['title']
                item_num = series_dict['user_position']
                series_info = f"{series_title} Series, Book {item_num}"
                if series_info != orig_version:
                    tags['version'] = series_info
                    print(f"     • Changed series from {orig_version} to {series_info}")
            try:
                orig_genres = tags['genre']
            except KeyError:
                orig_genres = []
            if set(genres) != set(orig_genres):
                tags['genre'] = genres
                print(f"     • Changed genre from {orig_genres} to {genres}")
            if not dryrun:
                tags.save()
            successes.append({'directory' : directory, 'book' : book})
        print()
    return {'failures' : failures, 'successes' : successes}


def prefix_title(directory):
    mp3files = [os.path.join(directory, i) 
                for i in os.listdir(directory) if i[-4:]=='.mp3']
    booktitle = 'Mansfield Park'
    for item in mp3files:
        tags = mutagen.File(item, easy=True)
        titletag = tags['title'][0]
        newtitle = f'{booktitle} - Part {titletag}'
        tags['title'] = newtitle
        tags.save()
        print(newtitle)

def check_versions(place):
    dirs = makelist(place)
    for index, directory in enumerate(dirs):
        print(f'<{index}> {directory}')
        mp3files = [os.path.join(directory, i) 
                    for i in os.listdir(directory) if i[-4:]=='.mp3']
        tags = mutagen.File(mp3files[0], easy=True)
        if 'version' in tags:
            print(tags['version'])
        print('--') 

def tag_test(tags):
    try:
        return '/' in tags['artist'][0]
    except:
        return False

def which_books_need_tagging(dirs, tag_test=tag_test):
    need_tagging = []
    for bookdir in dirs:
        try:
            mp3files = [os.path.join(bookdir, i) 
                        for i in os.listdir(bookdir) if i[-4:]=='.mp3']
            tags = mutagen.File(mp3files[0], easy=True)
            if tag_test(tags):
                need_tagging.append(bookdir)
        except IndexError:
            pass
    return need_tagging

def identify_spoken(dirs):
    books = makelist(dirs)
    positives = []
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
        try:
            genres = tags['genre']
        except KeyError:
            genres = []
            positives.append(book)
        if 'Spoken & Audio' in genres:
            positives.append(book)
    return positives

def update_individual_book(directory, book_id, dryrun=False):
    '''Update audiobook tags using the goodreads book id.
    You should only need this if the book has trouble matching automatically'''
    gc = goodreads_client
    book = gc.book(book_id)
    print(book)
    mp3files = [os.path.join(directory, i) 
                for i in os.listdir(directory) if i[-4:]=='.mp3']
    if mp3files == []:
        print("Directory does not include mp3 files")
        return
    totaltracks = len(mp3files)
    try:
        year = book.work['original_publication_year']['#text']
    except KeyError:
        year = None
    try:
        month = book.work['original_publication_month']['#text']
    except KeyError:
        month = None
    day = '01'
    try:
        day = book.work['original_publication_day']['#text']
    except KeyError:
        day = "01"
    if year and month:
        pubdate = f'{year}{month:0>2}{day:0>2}'
    else:
        pubdate = year
    if book.series_works:
        try:
            series_dict = book.series_works['series_work'][0]
        except:
            series_dict = book.series_works['series_work']
    else:
        series_dict = None
    try:
        shelves = {shelf.name for shelf in book.popular_shelves[:10]}
    except:
        shelves = set()
    shelves.add('audiobook')
    genres = {genre_dict[i] for i in shelves.intersection(gr_genres)}
    genres = list(genres)
    for item in mp3files:
        try:
            tags = mutagen.File(item, easy=True)
        except mutagen.MutagenError:
            print(f"\n ✖ Cannot read mpeg headers in {item} \n\n ")
            continue
        print(f"   - {tags['title'][0]}")
        try:
            origdate = tags['date'][0]
        except KeyError:
            origdate = None
        if pubdate and (origdate != pubdate):
            tags['date'] = pubdate
            print(f"     • Changed date from {origdate} to {pubdate}")
        tracktag = tags['tracknumber'][0]
        if '/' not in tracktag:
            newtracktag = f'{tracktag}/{totaltracks}'
            tags['tracknumber'] = newtracktag
            print(f"     • Changed track number from {tracktag} to {newtracktag}")
        if 'language' in tags.keys() and tags['language'] == ['XXX']:
            tags['language'] = 'English'
            print(f"     • Changed language from 'XXX' to 'English'")
        if series_dict:
            try:
                orig_version = tags['version'][0]
            except KeyError:
                orig_version = None
            series_title = series_dict['series']['title']
            item_num = series_dict['user_position']
            series_info = f"{series_title} Series, Book {item_num}"
            if series_info != orig_version:
                tags['version'] = series_info
                print(f"     • Changed series from {orig_version} to {series_info}")
        try:
            orig_genres = tags['genre']
        except KeyError:
            orig_genres = []
        if set(genres) != set(orig_genres):
            tags['genre'] = genres
            print(f"     • Changed genre from {orig_genres} to {genres}")
        if not dryrun:
            tags.save()

def update_descriptions(start, match_style=MatchStyle.SEMIAUTO, dryrun=False):
    '''Updates comments tag with book description from goodreads,
    '''
    dirs = get_dirs(start)
    gc = goodreads_client
    failures = []
    for index, directory in enumerate(dirs):
        print(f'<{index}> {directory}')
        mp3files = [os.path.join(directory, i) 
                    for i in os.listdir(directory) if i[-4:]=='.mp3']
        if mp3files == []:
            continue
        tags = mutagen.File(mp3files[0], easy=True)
        result = match(gc, tags)
        if result is None:
            print("************* Problem matching book.")
            print("************* No results from goodreads")
            print()
            failures.append(directory)
            continue
        elif result['score'] > SCORE_THRESHOLD:
            print("************* Problem matching book.")
            print(f"************* Best match is {result} ")
            print()
            failures.append(directory)
            continue
        else:
            book = result['result']
            print(f'   Matched to {book}' )
            text = book.description
            print(f'   {text}')
            if not text:
                continue
            for mp3file in mp3files:
                tags = ID3(mp3file)
                print(f"   - {tags['TIT2'].text[0]}")
                
                tags.delall("COMM")
                tags["COMM::eng"] = COMM(
                    encoding=Encoding.UTF8,
                    lang='eng',
                    text=text,
                )
                tags.save()

