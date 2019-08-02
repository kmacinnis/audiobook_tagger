import requests
import urllib
import mutagen
from bs4 import BeautifulSoup
from pathlib import Path
from common import DESKTOP, unique_path, get_dirs, get_mp3_files

AUDIOBOOKSTORE_SEARCH_URI = "https://audiobookstore.com/search.aspx?Keyword=%s"
AUDIBLE_SEARCH_URI = "https://www.audible.com/search?keywords=%s"                                           


def get_audiobookstore_cover_image(author, title, directory=None):
    if directory is None:
        save_location = DESKTOP / f"{author} - {title}"
    else:
        save_location = Path(directory) / 'cover'
    search_string = urllib.parse.quote(f"{author} - {title}")
    try:
        page = requests.get(AUDIOBOOKSTORE_SEARCH_URI % search_string)
        soup = BeautifulSoup(page.content, 'html.parser')
        soup.select('img#imageAudiobookCoverArt')
        cover_uri = soup.select('img#imageAudiobookCoverArt')[0]['src']
        ext = Path(cover_uri).suffix
        save_location = unique_path(save_location.with_suffix(ext))
        urllib.request.urlretrieve(cover_uri, filename=save_location) 
    except Exception as err:
        print(f"Unable to download cover at audiobookstore for {author} - {title}.")
        print(err)
        print()
        return False
    else:
        print(f'Got cover for {author} - {title} at {save_location}\n')
        return True

def update_covers(dirs, dryrun=False):
    '''Downloads a cover for each audiobook from audiobookstore.com
    '''
    dirs = get_dirs(dirs)   
    failures = []
    successes = []
    for index, directory in enumerate(dirs):
        print(f'<{index}> {directory}')
        mp3files = get_mp3_files(directory)
        if mp3files == []:
            continue
        tags = mutagen.File(mp3files[0], easy=True)
        authortag = tags['artist'][0]
        booktitletag = tags['album'][0]
        if get_audiobookstore_cover_image(authortag, booktitletag, directory):
            successes.append(directory)
        else:
            failures.append(' '.join((authortag, booktitletag)))
    return {'failures' : failures, 'successes' : successes}
    
        