import re
import mutagen
from Levenshtein import distance

from change import match, MatchStyle
from common import get_mp3_files, get_single_mp3, get_dirs, get_leaf_dirs


THRESHOLD = 3

def prettify_author_name(name):
    name = str(name)
    patterns = [
        {'pattern' : r'([A-Z]\.)\s([A-Z]\.)',
         'repl' : r'\1\2'},
        {'pattern': r'([A-Z]\.)\s([A-Z]\.)',
         'repl': r'\1\2'},
        {'pattern' : r'(\s{2,})',
         'repl' : ' '},
         {'pattern' : r'([A-Z])([A-Z])\s([A-Z]\.)',
         'repl' : ''}
    ]
    for patt in patterns:
        name = re.sub(patt['pattern'], patt['repl'], name)
    return name

def check_book_authors(bookdirs):
    books = get_dirs(bookdirs)
    many_authors = []
    change_suggested = []
    unmatched = []
    for index, bookdir in enumerate(books):
        try:
            print(f'<{index}> {bookdir}')

            samplefile = get_single_mp3(bookdir)
            tags = mutagen.File(samplefile, easy=True)
            result = match(tags, match_style = MatchStyle.AUTO)
            if result is None:
                print("     • Problem matching book")
                continue
            grbook = result['result']
            num_authors = len(grbook.authors)
            if num_authors == 1:
                old_artist = tags['artist'][0]
                new_artist = prettify_author_name(grbook.authors[0])
            elif num_authors < 4:
                old_artist = tags['artist'][0]
                new_artist = ' & '.join([prettify_author_name(author)
                                                for author in grbook.authors])
            else: # num_authors > 4 TODO: figure out what to do with these
                print("     • Too many authors")
                many_authors.append({'dir': bookdir, 'book' : grbook})
                continue
            new_artist = ' '.join(filter(None, new_artist.split(' ')))

            if old_artist == new_artist:
                print(f"     • No changes needed")
            else:
                print(f"     • Suggest change from {old_artist} to {new_artist}")
                change_suggested.append( {
                    'bookdir' : bookdir,
                    'old_artist' : old_artist,
                    'new_artist' : new_artist
                    }
                )
        except:
            pass

    return {
        'change_suggested' : change_suggested,
        'many_authors' : many_authors,
        'unmatched' :unmatched,
    }

def make_author_change(bookdir, old_artist, new_artist, dryrun=False):
    mp3files = get_mp3_files(bookdir)
    for item in mp3files:
        try:
            tags = mutagen.File(item, easy=True)
        except mutagen.MutagenError:
            print(f"\n ✖ Cannot read mpeg headers in {item} \n\n ")
            continue
        print(f"   - {tags['title'][0]}")

        tags['artist'] = new_artist
        print(f"     • Changed artist from {old_artist} to {new_artist}")
        if not dryrun:
            tags.save()

def make_suggested_changes(changes):
    for suggestion in changes:
        make_author_change(**suggestion)
