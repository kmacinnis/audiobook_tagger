import os
from mutagen.id3 import ID3, TIT2, COMM, TALB, TCOM, TPE1
from common import organize_by_tag
import re


def tag_audible_books(root):
    for i, name in enumerate(os.listdir(root)):
        if name[-4:] != '.mp3':
            continue
        print(f"\n<{i}> Attempting to tag {name}...")
        audiobook = ID3(os.path.join(root, name))
        try:
            album = audiobook['TXXX:short_title'].text[0]
        except KeyError:
            try:
                album = audiobook['TXXX:parent_short_title'].text[0]
            except:
                album = audiobook['TIT2'].text[0]
        album_match = re.match(r"(?P<title>.*)( Part \d+)", album)
        if album_match:
            album = album_match.group('title')
        audiobook.add(TALB(encoding=3, text=album))
        print(f" - {album}")
        artist = audiobook['TXXX:author'].text[0]
        audiobook.add(TPE1(encoding=3, text=artist))
        print(f" - {artist}")
        try:
            composer = audiobook['TXXX:narrator'].text[0]
            audiobook.add(TCOM(encoding=3, text=composer))
            print(f" - {composer}")
        except KeyError:
            pass
        try:
            audiobook.add(COMM(encoding=3, text=audiobook['TXXX:description'].text[0]))
        except KeyError:
            pass
        audiobook.save()
        print(f"{name} tagged successfully.")


def tag_and_organize_audible_books(root):
    tag_audible_books(root)
    organize_by_tag(root)








