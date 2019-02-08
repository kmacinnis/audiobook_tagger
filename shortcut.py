from change import update_tags
from pull import pull_mp3_files
from images import stretch_all_covers
from common import makelist, NEW, PHONE_BACKUPS

NEW = '/Volumes/media/temp-audiobooks/new/'
PHONE_BACKUPS

def pull_and_update(destination=NEW):
    mp3s = pull_mp3_files(destination=destination)
    stretch_all_covers(destination)
    if mp3s == []:
        print(f"No mp3 files found in {PHONE_BACKUPS}")
        return
    failures = update_tags(makelist(destination))
    if failures == []:
        print("Transfer complete")
    else:
        update_tags(failures, auto=False)
