import mutagen
from Levenshtein import distance

from change import goodreads_client as gc
from change import match, MatchStyle
from common import get_mp3_files, get_single_mp3, get_dirs, makelist


THRESHOLD = 3


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
            result = match(gc, tags, match_style = MatchStyle.AUTO)
            if result is None:
                print("     • Problem matching book")
                continue
            grbook = result['result']
            num_authors = len(grbook.authors)
            author_distance = distance(tags['artist'][0], str(grbook.authors[0]))
            if num_authors == 1:
                old_artist = tags['artist'][0]
                new_artist = str(grbook.authors[0])
            elif num_authors < 4: 
                old_artist = tags['artist'][0]
                new_artist = ' & '.join([str(author) for author in grbook.authors])
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

