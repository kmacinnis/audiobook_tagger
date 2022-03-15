import mutagen
from mutagen.id3 import ID3, COMM, Encoding
# from bs4 import BeautifulSoup
from pathlib import Path
from enum import Enum, auto

from pull import set_tags
from common import get_mp3_files, gr_genres, genre_dict, get_dirs, get_leaf_dirs, get_single_mp3
from Levenshtein import distance
import os
import re
import requests

from googleapiclient.discovery import build
from keys import GOOGLE_API_KEY

google_books_service = build('books','v1',developerKey=GOOGLE_API_KEY)
 
SCORE_THRESHOLD = 5
MAX_RESULTS = 10


class BookInfo:
    def __init__(self, info=None, **kwargs):
        # print(info.keys())
        # print(info)
        if info is None and 'gb_id' in kwargs.keys():
            #TODO: get the book info from the google books id
            pass
        self.title = info.get('title',' ██████████ MISSING TITLE ██████████ ')
        # TODO: make multiple authors nicer
        authors = info.get('authors', [])
        self.author = ' & '.join(reversed(authors))
        self.pubdate = info.get('publishedDate', '')
        self.gb_id = info.get('gb_id', '')
        self.gb_link = info.get('infoLink','')
        self.language = info.get('language','')
        self.description = info.get('description','')
        
    def __str__(self):
        return f'{self.title} by {self.author} ({self.pubdate})'
        
    def __repr__(self):
        return f'<BookInfo: gb_id={self.gb_id}>'
        
    def scrape_extra_data():
        page = requests.get(self.gb_link)
        soup = BeautifulSoup(page.content, 'lxml')
        soup.select('')
        # Damn, it looks like the info I need is loaded by js.
        # Look into using selenium if you decide original pub date
        # and genres are important to you?


class MatchStyle(Enum):
    ''' Ways of handling matching.
    "Good match" here is defined as matches that have a score
    (see function `match`) lower than `SCORE_THRESHOLD`
    '''
    # `AUTO` - skip items that don't have a good match
    AUTO = auto()

    # `SEMIAUTO` - ask user to match items that don't have a good match
    SEMIAUTO = auto()

    # `MANUAL` - ask user to match each item
    MANUAL = auto()


def clean(title):
    '''Removes parentheticals and subtitles to make searching easier'''
    if '(' in title:
        return title.split(' (')[0]
    if ':' in title:
        return title.split(':')[0]
    if ':' in title:
        return title.split(':')[0]
    # For Audible books that are part of a series 'BookName-SeriesName, Book #'
    pattern = r'(.*)-(.*), Book \d'
    result = re.search(pattern,title)
    if result:
        return result.groups()[0]
    return title

def match(tags, match_style = MatchStyle.MANUAL, search_terms = None):
    authortag = tags['artist'][0]
    booktitletag = clean(tags['album'][0])
    if search_terms is None:
        search_terms = f'intitle:{booktitletag} inauthor:{authortag}'
    gb = build('books','v1',developerKey=GOOGLE_API_KEY)
    print(f'   Searching google books for: “{search_terms}”')
    try:
        results = gb.volumes().list(  q=search_terms, 
                                    maxResults=MAX_RESULTS,).execute()
        gb.close()
    except Exception as err:
        print("   Trouble getting results from google books.")
        print(err)
        return
    try:
        results = results['items']
    except KeyError:
        results = []
    score_chart = []
    for i, result in enumerate(results):
        info = result['volumeInfo']
        info['gb_id'] = result['id']
        #TODO: Add description to info dict
         
        try:
            authors = info.get('authors', [])
            author_score = min(
                    [distance(authortag, author) for author in authors] + [99]
                )
            title_score = distance(booktitletag, info['title'])
            score = author_score + title_score
            #TODO: Adjust score so complete dates get a better score
        except mutagen.MutagenError:
            score = 999
        book = BookInfo(info)
        score_chart.append({'score': score, 'book': book})
    score_chart.sort(key=lambda k: k['score'])
    if match_style == MatchStyle.AUTO:
        return score_chart[0]
    elif match_style == MatchStyle.SEMIAUTO:
        try:
            if score_chart[0]['score'] < SCORE_THRESHOLD:
                return score_chart[0]
        except IndexError:
            pass
    for i, item in enumerate(score_chart, 1):
        print(f"    {i}. {item['book']}       ⟪score: {item['score']}⟫ ")
    
    if not score_chart:
        print(f"    * No results from google books for “{search_terms}” *")
    
    print('\n')
    print('    N. Move author to narrator and redo search')
    print('    T. Redo search using only the title')
    print('    C. Change search terms and search again')
    print('    S. Skip this audiobook')
    print('\n')
    
    

    response = 'True'
    while response:
        response = input("   Select from above: ")
        if response in ('S','s'):
            # Skip this audiobook by returning no match
            return
        elif response in ('T', 't'):
            new_terms = f'intitle:{booktitletag}'
            return match(tags, search_terms=new_terms, match_style=match_style)
        elif response in ('C','c'):
            new_terms = input('Enter new search terms:')
            return match(tags, search_terms=new_terms, match_style=match_style)
        elif response in ('n', 'N'):
            tags['composer'] = tags["artist"][0]
            tags['artist'] = '██████████ MISSING AUTHOR ██████████'
            tags.save()
            new_terms = f'intitle:{booktitletag}'
            return match(tags, search_terms=new_terms, match_style=match_style)
        else:
            try:
                num = int(response) - 1
                chosen = score_chart[num]
                chosen['score'] = -1
                return chosen
            except:
                response = 'True'
                print('Response not recognized. Try again.')


def update_tags(items, match_style=MatchStyle.SEMIAUTO, dryrun=False):
    '''Takes a set of organized directories containing one audiobook each and
    updates mp3 tags: date tag with publication date from google books,
    track number to contain totaltracks, and fixes language.
    
    TODO: Find decent source for: 
                    ✓ any publication date
                    ⎚ *original* publication date, 
                    ⎚ series info,
                    ⎚ genres
    TODO: Figure out how to fix authors?

    '''

    items = [ {'folder' : d, 'book' : None} for d in get_dirs(items)]

    failures = []
    successes = []
    for index, item in enumerate(items):
        directory = item['folder']
        book = item['book']
        print(f'<{index}> {directory}')
        mp3files = get_mp3_files(directory)
        if mp3files == []:
            continue
        mp3files.sort()
        tags = mutagen.File(mp3files[0], easy=True)
        result = match(tags, match_style=match_style)
        if result is None  and  match_style == MatchStyle.AUTO:
            print("************* Problem matching book.")
            print("************* No results from google books for")
            print(f"****************** title = {tags['album'][0]}")
            print(f"****************** author = {tags['artist'][0]}")
            print()
            failures.append(directory)
            continue
        elif result is None or (result['score'] > SCORE_THRESHOLD
                                and match_style == MatchStyle.AUTO):
            print("************* Problem matching book.")
            print(f"************* Best match is {result} ")
            print()
            failures.append(directory)
            continue
        # Otherwise, successful match:
        book = result['book']
        print(f'   Matched to {book}' )
        totaltracks = len(mp3files)
        pubdate = ''.join(book.pubdate.split('-'))
        
        
        newauthor = ''
        oldauthor = tags["artist"][0]
        author_distance = distance(book.author, tags['artist'][0])

        if author_distance > 0:
            space = ' '*(len(f'<{index}>   '))
            print()
            print(f'{space} Discrepancy in authors identified. Select one:')
            print(f'{space} 1. {book.author}')
            print(f'{space} 2. {tags["artist"][0]}')
            print(f'{space} 3. Type in other option')
            print(f'{space} 4. Make no changes')
            print()
            response = input(f'{space} Select from above: ')
            print()
            while True:
                if response == '1':
                    newauthor = book.author
                    oldauthor = tags["artist"][0]
                    break
                elif response == '2':
                    # newauthor = tags["artist"][0]
                    book.author = tags["artist"][0]
                    newauthor = False
                    break
                elif response == '3':
                    newauthor = input(f'{space} Enter new author: ')
                    book.author = newauthor
                    oldauthor = tags["artist"][0]
                    break
                elif response == '4':
                    newauthor = False
                    break
                else:
                    response = input(f'{space} Select valid option from above: ')

        for item in mp3files:
            try:
                tags = mutagen.File(item, easy=True)
            except mutagen.MutagenError:
                print(f"\n ✖ Cannot read mpeg headers in {item} \n\n ")
                continue
            try:
                temp_title = tags['title'][0]
            except KeyError:
                temp_title = ' ██████████ MISSING TITLE ██████████ '
            print(f"   - {temp_title}")
            if newauthor:
                tags['artist'] = newauthor
                print(f"     • Changed author from {oldauthor} to {newauthor}")
                
            try:
                origdate = tags['date'][0]
            except KeyError:
                origdate = None
            if pubdate and (origdate != pubdate):
                tags['date'] = pubdate
                print(f"     • Changed date from {origdate} to {pubdate}")
            tracktag = tags['tracknumber'][0]
            if '/' not in tracktag:
                if int(tracktag) > totaltracks:
                    print('\n\n','█'*100)
                    msg = 'PROBLEM: Track number is higher than number of total tracks'
                    print('█',msg.center(98),'█')
                    print('█'*100,'\n\n')
                
                newtracktag = f'{tracktag}/{totaltracks}'
                tags['tracknumber'] = newtracktag
                print(f"     • Changed track number from {tracktag} to {newtracktag}")
            if 'language' in tags.keys() and tags['language'] == ['XXX']:
                tags['language'] = book.language
                print(f"     • Changed language from 'XXX' to 'English'")
            
            if not dryrun:
                tags.save()
        successes.append({'directory' : directory, 'book' : book})
        print()
    return {'failures' : failures, 'successes' : successes}

def match_goodreads_version(gc, tags, match_style = MatchStyle.SEMIAUTO):
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
    for i, result in enumerate(results[:15]):
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


def update_tags_goodreads_version(items, match_style=MatchStyle.SEMIAUTO, dryrun=False):
    '''Updates date tag with original publication date from goodreads,
    updates track number to contain totaltracks,

    If book is not passed in, will match the author and title via goodreads search.
    '''
    try:
        items[0]['book']
    except:
        items = [ {'directory' : d, 'book' : None} for d in get_dirs(items)]


    gc = goodreads_client
    failures = []
    successes = []
    for index, item in enumerate(items):
        directory = item['directory']
        book = item['book']
        print(f'<{index}> {directory}')
        mp3files = get_mp3_files(directory)
        if mp3files == []:
            continue
        tags = mutagen.File(mp3files[0], easy=True)
        if book is None:
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
            pubdate = f'{year}{month:0>2}01'
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
                if int(tracktag) > totaltracks:
                    print('\n\n','█'*100)
                    msg = 'PROBLEM: Track number is higher than number of total tracks'
                    print('█',msg.center(98),'█')
                    print('█'*100,'\n\n')
                
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
    dirs = get_leaf_dirs(place)
    for index, directory in enumerate(dirs):
        print(f'<{index}> {directory}')
        mp3files = [os.path.join(directory, i)
                    for i in os.listdir(directory) if i[-4:]=='.mp3']
        tags = mutagen.File(mp3files[0], easy=True)
        if 'version' in tags:
            print(tags['version'])
        print('--')

def tag_test(tags):
    if 'date' not in tags.keys():
        return True

def which_books_need_tagging(check_dirs, tag_test=tag_test):
    need_tagging = []
    dirs = get_leaf_dirs(check_dirs)
    for bookdir in dirs:
        try:
            mp3files = get_mp3_files(bookdir)
            tags = mutagen.File(mp3files[0], easy=True)
            if tag_test(tags):
                need_tagging.append(bookdir)
        except IndexError:
            pass
    return need_tagging

def identify_spoken(dirs):
    books = get_leaf_dirs(dirs)
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

def update_descriptions_from_goodreads(items, match_style=MatchStyle.SEMIAUTO, book=None, dryrun=False):
    '''Updates comments tag with book description from goodreads,
    '''
    try:
        items[0]['book']
    except:
        items = [ {'directory' : d, 'book' : None} for d in get_dirs(items)]
    gc = goodreads_client
    failures = []
    successes = []
    for index, item in enumerate(items):
        directory = item['directory']
        book = item['book']
        print(f'<{index}> {directory}')
        mp3files = [os.path.join(directory, i)
                    for i in os.listdir(directory) if i[-4:]=='.mp3']
        if mp3files == []:
            continue
        tags = mutagen.File(mp3files[0], easy=True)
        if book is None:
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


