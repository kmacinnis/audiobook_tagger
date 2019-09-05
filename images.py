import io
import os
from mutagen.id3 import ID3, APIC, PictureType, Encoding
from PIL import ImageFile
from pathlib import Path

from common import makelist, get_mp3_files, NEW, unique_path

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
SEARCH_ITEM = '<p><a href="https://google.com/search?q={0}&tbm=isch">{0}</a></p>\n'

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
    path = unique_path(Path(docpath) / docname)
    with open(path, 'w') as search_doc:
        search_doc.write(PAGE_START)
        for item in search_items:
            search_doc.write(SEARCH_ITEM.format(item,))
        search_doc.write(PAGE_END)

def compile_image_search_links(docpath=NEW, docname=COMPILED_DOC_NAME):
    docpath = Path(docpath)
    image_search_links =[x for x in docpath.iterdir() if x.name.startswith('_image_search_links')]
    textlines = set()
    newpath = unique_path(Path(docpath) / docname)
    with open(newpath, 'w') as compiled_doc:
        for f in image_search_links:
            with open(docpath / f, 'r') as search_link_file:
                newlines = [x for x in list(search_link_file) if x.startswith('<p>')]
                textlines = textlines.union(newlines)
        textlines = list(textlines)
        compiled_doc.write(PAGE_START)
        sort_search_items(textlines)
        compiled_doc.writelines(textlines)
        compiled_doc.write(PAGE_END)

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

def stretch_all_covers(startdir):
    if isinstance(startdir, str):
        dirs = makelist(startdir)
    else:
        dirs = startdir
    for bookdir in dirs:
        mp3files = get_mp3_files(bookdir)
        for mp3file in mp3files:
            stretch_cover_image(os.path.join(bookdir,mp3file))









