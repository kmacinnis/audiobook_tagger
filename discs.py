import os
from pathlib import Path
from collections import defaultdict
from audiobooks import Audiobook



def make_audiobooks(startdir):
    ''' Takes a directory (eventually tiered, but now flat)
    and 
    '''
    
    books = []
    for item in Path(startdir).iterdir():
        if item.suffix not in AUDIOFILE_EXTENSIONS:
            continue
        filename = item.stem
        try:
            title, track = filename.split(' - Disc ')
        except ValueError:
            title = filename
            track = None
        match = [book for book in books if book.title == title]
        if match:
            match[0].add_file(item)
        else:
            books.append(Audiobook(title=title, filepath=item))
    return books

    
        