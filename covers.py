import requests
import urllib
import mutagen
from PIL import ImageFile
from bs4 import BeautifulSoup
from pathlib import Path
from common import DESKTOP, MAIN, unique_path, get_dirs, get_mp3_files

AUDIOBOOKSTORE_SEARCH_URI = "https://audiobookstore.com/search.aspx?Keyword=%s"
AUDIBLE_SEARCH_URI = "https://www.audible.com/search?keywords=%s"

def has_separate_cover(bookdir):
    covers = [x for x in bookdir.iterdir() if x.stem.startswith('cover')]
    return len(covers) > 0

def clear_embedded_image(bookdir):
    for mp3file in get_mp3_files(bookdir):
        apic_tag = None
        try:
            mp3 = mutagen.File(mp3file)
        except mutagen.MutagenError:
            return
        for tag in mp3.tags.keys():
            if tag[:4] == "APIC":
                apic_tag = tag
                break
        if apic_tag:
            mp3.tags.delall(apic_tag)
            mp3.save()

def extract_embedded_image(bookdir):
    try:
        mp3file = get_mp3_files(bookdir)[0]
    except IndexError:
        return
    try:
        mp3 = mutagen.File(mp3file)
    except mutagen.MutagenError:
        return
    for tag in mp3.tags.keys():
        if tag[:4] == "APIC":
            apic_tag = tag
            break
    try:
        apic = mp3.tags[apic_tag]
    except NameError:
        return
    parser = ImageFile.Parser()
    parser.feed(apic.data)
    im = parser.close()
    width, height = im.size
    if width != height:
        orig_format = im.format
        maxdim = max(width, height)
        im = im.resize((maxdim, maxdim))
        im.format = orig_format
    image_path = unique_path(bookdir / f'cover.{im.format.lower()}')
    with open(image_path, 'wb') as output:
        im.save(output, format=im.format)
    clear_embedded_image(bookdir)

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
            clear_embedded_image(directory)
        else:
            failures.append(' '.join((authortag, booktitletag)))
            extract_embedded_image(directory)
    return {'failures' : failures, 'successes' : successes}


def extract_all_covers(startdir=MAIN):
    startdir = Path(startdir)
    for authordir in startdir.iterdir():
        print(f'  ◈ {authordir.name}')
        try:
            for bookdir in authordir.iterdir():
                if bookdir.is_file():
                    continue
                print(f'    • {bookdir.name}')
                if has_separate_cover(bookdir):
                    print(f'       clearing embedded images')
                    clear_embedded_image(bookdir)
                else:
                    extract_embedded_image(bookdir)
                    print(f'       extracting embedded images')
        except NotADirectoryError:
            continue

