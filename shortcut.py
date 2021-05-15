import os
from change import update_tags
from pull import pull_mp3_files
from images import stretch_all_covers, create_image_search_links
from covers import update_covers
from common import get_leaf_dirs, NEW, MAIN, PHONE_BACKUPS
from organize import clear_notes, clear_playlists, merge, rename_bookdirs
from authors import check_book_authors

from pathlib import Path
from enum import Enum, auto



class CoverOption(Enum):
    ALWAYS = auto()
    NEVER = auto()
    ONLY_NEEDED = auto()


def pull_and_update(startdir=PHONE_BACKUPS,
                    destination=NEW,
                    check_exists=True, move_without_copying=False):
    mp3s = pull_mp3_files(startdir=startdir,
                          destination=destination,
                          move_without_copying=move_without_copying,
                          check_exists=check_exists)
    # stretch_all_covers(destination)
    if mp3s == []:
        print(f"No new mp3 files found in {startdir}")
        return
    newdirs = set([Path(mp3).parent for mp3 in mp3s])
    tagged = update_tags(newdirs)
    # update_descriptions(tagged['successes'])
    
    # print('Checking for series names:')
    # for item in tagged['successes']:
    #     newpath = rename_bookdirs(**item)
    #     print(item)
    #     if newpath is not None:
    #         print(f" * Renaming directory to {newpath}")
    #         item['directory'] = newpath
    #         print(item)
    corrected_dirs = [x['directory'] for x in tagged['successes']]
    cover_results = update_covers(corrected_dirs)
    needed_covers = ['{} audiobook cover'.format(x)
                                for x in cover_results['failures']]
    author_dirs = set([Path(book).parent for book in corrected_dirs])
    needed_authors = ['{} author photo'.format(d.name)
                        for d in author_dirs if (d/'_ needs photo').exists()]
    needed_authors.sort()
    needed_covers.sort()
    create_image_search_links(needed_covers + needed_authors)
    return tagged


def clean_up(from_dir=NEW, to_dir=MAIN):
    clear_notes(from_dir)
    clear_playlists(from_dir)
    merge(from_dir=from_dir, to_dir=to_dir)
    
def update_new(new=NEW, get_images=CoverOption.ONLY_NEEDED):
    try:
        new = Path(new)
        newdirs = set(get_leaf_dirs(new))
    except TypeError:
        pass
    
    tagged = update_tags(newdirs)
    # update_descriptions(tagged['successes'])
    # for item in tagged['successes']:
    #     newpath = rename_bookdirs(**item)
    #     if newpath is not None:
    #         item['directory'] = newpath
    if get_images == CoverOption.NEVER:
        dirs_that_need_covers = []
    elif get_images == CoverOption.ALWAYS:
        dirs_that_need_covers = [x['directory'] for x in tagged['successes']]
    elif get_images == CoverOption.ONLY_NEEDED:
        tagged_dirs = [x['directory'] for x in tagged['successes']]
        dirs_that_need_covers = [bookdir for bookdir in tagged_dirs 
                if not any((x.stem == 'cover' for x in bookdir.iterdir()))] 
    cover_results = update_covers(dirs_that_need_covers)
    needed_covers = ['{} audiobook cover'.format(x)
                                for x in cover_results['failures']]
    author_dirs = set([Path(book).parent for book in newdirs])
    needed_authors = ['{} author photo'.format(d.name)
                        for d in author_dirs if (d/'_ needs photo').exists()]
    needed_authors.sort()
    needed_covers.sort()
    create_image_search_links(needed_covers + needed_authors)
    return tagged


def just_get_images(new=NEW, get_images=CoverOption.ONLY_NEEDED):
    dirs = set(get_leaf_dirs(new))
    if get_images == CoverOption.NEVER:
        dirs_that_need_covers = []
    elif get_images == CoverOption.ALWAYS:
        dirs_that_need_covers = dirs
    elif get_images == CoverOption.ONLY_NEEDED:
        dirs_that_need_covers = [bookdir for bookdir in dirs 
                if not any((x.stem == 'cover' for x in bookdir.iterdir()))] 
    cover_results = update_covers(dirs_that_need_covers)
    needed_covers = ['{} audiobook cover'.format(x)
                                for x in cover_results['failures']]
    author_dirs = set([Path(book).parent for book in dirs])
    needed_authors = ['{} author photo'.format(d.name) for d in author_dirs 
             if (d/'_ needs photo').exists() and not (d/'artist.jpg').exists()]
    needed_authors.sort()
    needed_covers.sort()
    create_image_search_links(needed_covers + needed_authors)
    