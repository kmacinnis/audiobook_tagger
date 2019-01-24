# TODO: Automatically resize images to square.



mimetype = {
    'JPEG' : 'image/jpeg',
    'PNG' : 'image/png',
}



# fd = urllib.urlopen(cover)
# # Drop the entire PIL part
# covr = MP4Cover(fd.read(), getattr(
#             MP4Cover,
#             'FORMAT_PNG' if cover.endswith('png') else 'FORMAT_JPEG'
#         ))
# fd.close() # always a good thing to do
#
# tags['covr'] = [covr] # make sure it's a list
# tags.save()


from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error

audio = MP3(mp3file, ID3=ID3)


from PIL import ImageFile


p = ImageFile.Parser()

while 1:
    s = apic.data.read(1024)
    if not s:
        break
    p.feed(s)

im = p.close()

square_image = im.resize((max(im.size),max(im.size)))

import io

with io.BytesIO() as output:
    square_image.save(output, format=im.format)
    data = output.getvalue()



audio.tags.add(
    APIC(
        encoding=3,                 # 3 is for utf-8
        mime=mimetype[im.format],   # image/jpeg or image/png
        type=3,                     # 3 is for the cover image
        desc='Cover',
        data=data
    )
)
audio.save()



from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error, PictureType, Encoding

from PIL import Image
from PIL import ImageFile
import io


# ipython history:

mimetype = {
    'JPEG' : 'image/jpeg',
    'PNG' : 'image/png',
}
mp3file = "/Volumes/media/temp-audiobooks/new/Cecilia Grant/A Gentleman Undone/A Gentleman Undone - Part 02.mp3"
audio = MP3(mp3file, ID3=ID3)
apic = audio.tags['APIC:']
parser = ImageFile.Parser()
parser.feed(apic.data)
im = parser.close()

square_image = im.resize((max(im.size),max(im.size)))
with io.BytesIO() as output:
    square_image.save(output, format=im.format)
    data = output.getvalue()



newapic = APIC(
        encoding=Encoding.UTF8,
        mime=mimetype[im.format],
        type=PictureType.COVER_FRONT,
        desc='Cover',
        data=data
    )
audio.tags.add(newapic)
audio.save()
history

mp3file = "/Volumes/media/temp-audiobooks/new/Cecilia Grant/A Gentleman Undone/A Gentleman Undone - Part 03.mp3"
tags = ID3(mp3file)
apic = tags['APIC:']
parser = ImageFile.Parser()
parser.feed(apic.data)
im = parser.close()
square_image = im.resize((max(im.size),max(im.size)))
with io.BytesIO() as output:
    square_image.save(output, format=im.format)
    data = output.getvalue()
newapic = APIC(
        encoding=Encoding.UTF8,
        mime=mimetype[im.format],
        type=PictureType.COVER_FRONT,
        desc='Cover',
        data=data
    )
tags.delall('APIC:')
tags.add(newapic)
tags.save()












