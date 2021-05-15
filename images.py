import io
import os
from mutagen.id3 import ID3, APIC, PictureType, Encoding
from PIL import ImageFile
from pathlib import Path

from common import get_leaf_dirs, get_mp3_files, NEW, unique_path
from covers import AUDIOBOOKSTORE_SEARCH_URI

mimetype = {
    'JPEG' : 'image/jpeg',
    'PNG' : 'image/png',
}

DOC_NAME = '_image_search_links.html'
COMPILED_DOC_NAME = '_compiled_search_links.html'
PAGE_START = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Image Search Links</title>
</head>
<body>
'''
PAGE_END = '''
</body>
</html> 
'''
GOOGLE_INFO_SEARCH = 'Google: <a href="https://google.com/search?q={0}">{0}</a>\n'
GOOGLE_IMAGE_SEARCH = 'GoogleImages: <a href="https://google.com/search?q={0}&tbm=isch">{0}</a>\n'
AUDIOBOOKSTORE_SEARCH = f'Audiobookstore: <a href="{AUDIOBOOKSTORE_SEARCH_URI}">{{0}}</a>\n'

def sort_search_items(items):

    def key(item):
        if 'audiobook cover' in item:
            return '1' + item
        elif 'author photo' in item:
            return '2' + item
        else:
            return '3' + item

    items.sort(key=key)

def create_image_search_links(search_items, docpath=NEW, docname=DOC_NAME):
    if not search_items:
        return
    path = unique_path(Path(docpath) / docname)
    with open(path, 'w') as search_doc:
        search_doc.write(PAGE_START)
        for item in search_items:
            search_doc.write('\n<p>\n')
            if item.endswith('audiobook cover'):
                true_item = item[:-15]
                search_doc.write(f'<h2>{true_item}</h2>\n')
                search_doc.write(GOOGLE_INFO_SEARCH.format(true_item,))
                search_doc.write('\n<br/>\n')
                search_doc.write(AUDIOBOOKSTORE_SEARCH.format(true_item,))
                search_doc.write('\n<br/>\n')
            search_doc.write(GOOGLE_IMAGE_SEARCH.format(item,))
            search_doc.write('\n</p>\n')
        search_doc.write(PAGE_END)



def stretch_cover_image(mp3file):
    tags = ID3(mp3file)
    #TODO: Decide whether should do anything with mulitple pictures
    for tag in tags.keys():
        if tag[:4] == "APIC":
            apic_tag = tag

            break
    try:
        apic = tags[apic_tag]
    except NameError:
        return
    parser = ImageFile.Parser()
    parser.feed(apic.data)
    im = parser.close()
    width, height = im.size
    if width == height:
        # image is already square
        return
    maxdim = max(width, height)
    square_image = im.resize((maxdim, maxdim))
    with io.BytesIO() as output:
        square_image.save(output, format=im.format)
        data = output.getvalue()
    newapic = APIC(
        encoding=Encoding.UTF8,
        mime=mimetype[im.format],
        type=PictureType.COVER_FRONT,
        desc='Stretched Overdrive Cover',
        data=data,
    )
    tags.delall(apic_tag)
    tags.add(newapic)
    tags.save()

def extract_cover_image(mp3file):

    tags = ID3(mp3file)
    #TODO: Decide whether should do anything with mulitple pictures
    for tag in tags.keys():
        if tag[:4] == "APIC":
            apic_tag = tag

            break
    try:
        apic = tags[apic_tag]
    except NameError:
        return
    tags.delall(apic_tag)
    tags.save()
    parser = ImageFile.Parser()
    parser.feed(apic.data)
    im = parser.close()
    width, height = im.size
    if width == height:
        square_image = im
    else:
        maxdim = max(width, height)
        square_image = im.resize((maxdim, maxdim))
    with io.BytesIO() as output:
        square_image.save(output, format=im.format)
        data = output.getvalue()


def stretch_all_covers(startdir):
    if isinstance(startdir, str):
        dirs = get_leaf_dirs(startdir)
    else:
        dirs = startdir
    for bookdir in dirs:
        mp3files = get_mp3_files(bookdir)
        for mp3file in mp3files:
            stretch_cover_image(os.path.join(bookdir,mp3file))

def stretch_all_covers(startdir):
    if isinstance(startdir, str):
        dirs = get_leaf_dirs(startdir)
    else:
        dirs = startdir
    for bookdir in dirs:
        mp3files = get_mp3_files(bookdir)
        for mp3file in mp3files:
            stretch_cover_image(os.path.join(bookdir, mp3file))
        if len(x for x in bookdir.iterdir() if x.stem.startswith('cover')) > 0:
            return
