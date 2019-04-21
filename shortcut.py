from change import update_tags, update_descriptions
from pull import pull_mp3_files
from images import stretch_all_covers
from common import makelist, NEW, PHONE_BACKUPS
from pathlib import Path

NEW = '/Volumes/media/temp-audiobooks/new/'

def pull_and_update(destination=NEW):
    mp3s = pull_mp3_files(destination=destination)
    stretch_all_covers(destination)
    if mp3s == []:
        print(f"No mp3 files found in {PHONE_BACKUPS}")
        return
    newdirs = set([Path(mp3).parent for mp3 in mp3s])
    failures = update_tags(newdirs)
    if failures == []:
        print("Transfer complete")
    else:
        update_tags(failures, auto=False)
    update_descriptions(newdirs)
    return newdirs

