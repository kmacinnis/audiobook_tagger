import os
from change import update_tags, update_descriptions
from pull import pull_mp3_files
from images import stretch_all_covers, create_image_search_links
from covers import update_covers
from common import makelist, NEW, PHONE_BACKUPS
from pathlib import Path


# NEW = '/Volumes/mangomedia/temp-audiobooks/new/'






def pull_and_update(destination=NEW):
    mp3s = pull_mp3_files(destination=destination)
    # stretch_all_covers(destination)
    if mp3s == []:
        print(f"No mp3 files found in {PHONE_BACKUPS}")
        return
    newdirs = set([Path(mp3).parent for mp3 in mp3s])
    tagged = update_tags(newdirs)
    update_descriptions(tagged['successes'])
    cover_results = update_covers(newdirs)
    needed_covers = ['{} audiobook cover'.format(x)
                                for x in cover_results['failures']]
    author_dirs = set([Path(book).parent for book in newdirs])
    needed_authors = ['{} author photo'.format(d.name)
                        for d in author_dirs if (d/'_ needs photo').exists()]
    needed_authors.sort()
    needed_covers.sort()
    create_image_search_links(needed_covers + needed_authors)
    return newdirs

