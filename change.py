import mutagen
# from mutagen.id3 import TDRC
from pull import set_tags
from common import get_mp3_files
from Levenshtein import distance
import os

from goodreads import client
API_KEY = "iaqF5jmbfkRAsudBGVHXLg"
CLIENT_SECRET = "2Af9zFVtOHVAlJcCM9DjymoeOMFKv6ePo1YC3GhxaQg"
gc = client.GoodreadsClient(API_KEY, CLIENT_SECRET)

startdir = "/Volumes/media/audiobooks/"


def clean(title):
    return title.split(' (')[0]

def score_match(grbook, tags):
    author_score = distance(tags['artist'][0], str(grbook.authors[0]))
    title_score = distance(clean(tags['album'][0]), clean(grbook.title))
    return (author_score, title_score)

def show_matches(dirs):
    gc = client.GoodreadsClient(API_KEY, CLIENT_SECRET)
    for directory in dirs:
        print(directory)
        author, title = os.path.relpath(directory, start=startdir).split('/')
        results = gc.search_books(f'{title} - {author}')
        mp3files = [os.path.join(directory, i) 
                    for i in os.listdir(directory) if i[-4:]=='.mp3']
        tags = mutagen.File(mp3files[0], easy=True)
        score_chart = []
        for i, result in enumerate(results[:5]):
            score = score_match(result,tags)
            score_chart.append({'score': sum(score), 'result': result})
            print(f'{i}.',result, score)
        score_chart.sort(key=lambda k: k['score'])
        book = score_chart[0]['result']
        print(book)


def find_best_match(gc, tags):
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
    return score_chart[0]

def user_chooses_match(gc, tags):
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


def update_date_tags(dirs, auto=True, dryrun=False):
    if auto:
        match = find_best_match
    else:
        match = user_chooses_match
    gc = client.GoodreadsClient(API_KEY, CLIENT_SECRET)
    failures = []
    for index, directory in enumerate(dirs):
        print(f'<{index}> {directory}')
        mp3files = [os.path.join(directory, i) 
                    for i in os.listdir(directory) if i[-4:]=='.mp3']
        tags = mutagen.File(mp3files[0], easy=True)
        result = match(gc, tags)
        if result is None:
            print("************* Problem matching book.")
            print("************* No results from goodreads")
            print()
            failures.append(directory)
            continue
        elif result['score'] > 5:
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
        for item in mp3files:
            tags = mutagen.File(item, easy=True)
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
            if not dryrun:
                tags.save()
        print()
    return failures

directory = '/Volumes/media/temp-audiobooks/xnew/Mansfield Park x'
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

def set_initial_tags(dirs):
    for bookdir in dirs:
        mp3files = [os.path.join(bookdir, i) 
                    for i in os.listdir(bookdir) if i[-4:]=='.mp3']
        for mp3file in mp3files:
            set_tags(os.path.join(bookdir,mp3file))
        
def fix_discworld_books(dirs):
    for bookdir in dirs:
        for mp3file in get_mp3_files(bookdir):
            tags = mutagen.File(mp3file, easy=True)
            origalbum = tags['album'][0]
            tags['album'] = origalbum[5:]
            tags.save()




