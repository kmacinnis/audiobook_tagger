import mutagen
from Levenshtein import distance

from change import gc
from change import match
from common import get_mp3_files, get_single_mp3, get_dirs, makelist


THRESHOLD = 3








def fix_book_authors(bookdir, dryrun=False):
    samplefile = get_single_mp3(bookdir)
    tags = mutagen.File(samplefile, easy=True)
    result = match(gc, tags)
    if result is None:
        print("************* Problem matching book *************")
        print()
        return
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
        print("  Too many authors")
        return
    
    if old_artist == new_artist:
        print(f"  No changes needed")
        return
    
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


def check_all_authors(startdir, dryrun=False):
    books = get_dirs(startdir)
    for index, book in enumerate(books):
        print(f'<{index}> {book}')
        fix_book_authors(book, dryrun=dryrun)
        