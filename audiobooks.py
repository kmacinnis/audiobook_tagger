import os
from pathlib import Path
from collections import defaultdict


class Audiobook:
    
    def __init__(**kwargs):
        kwargs = defaultdict(lambda:None, kwargs)
        self.title = kwargs['title']
        self.author = kwargs['author']
        self.date = kwargs['date']
        self.series_info = kwargs['series_info']
        self.goodreadsid = kwargs['goodreadsid']
        self.narrator = kwargs['narrator']
        self.totaltracks = 0
        self.files = []
        filepath = kwargs['filepath']
        if filepath:
            self.files.append(filepath)
            self.totaltracks = 1
    
    def add_file(filepath):
        self.files.append(filepath)
        self.totaltracks += 1
    
    def __add__(filepath):
        self.add_file(filepath)


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

