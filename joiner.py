import os
import subprocess
from pathlib import Path
from common import get_leaf_dirs


# %pwd

def join_split_bits(bookdir):
    maxnum = len(list(bookdir.iterdir())) + 1
    for n in range(maxnum):
        check_file = bookdir/f"Chapter {n}a.mp3"
        if not check_file.exists():
            print(f"- Not needed for Chapter {n}")
            continue
        filename = f"zzChapter {n}.txt"
        with open(bookdir/filename, 'w') as f:
            contents = f"file 'Chapter {n}a.mp3'\nfile 'Chapter {n}b.mp3'\n"
            f.write(contents)
        print(f"⦾ Created concat file for Chapter {n}")
    
        mp3name = f'Chapter {n}.mp3'
        first_mp3 = f'Chapter {n}a.mp3'
        ffmpeg_args = [ 'ffmpeg', '-f', 'concat', 
                        '-safe', '0', 
                        '-i', filename, 
                        '-i', first_mp3, 
                        '-map_metadata', '1',
                        '-c', 'copy', mp3name]
        # print(' '.join(ffmpeg_args))
        subprocess.run(ffmpeg_args, cwd=bookdir)
        print()
        print(f"Joined files for Chapter {n}")
        
        os.rename(bookdir/f"Chapter {n}a.mp3", bookdir/f"zzChapter {n}a.mp3")    
        os.rename(bookdir/f"Chapter {n}b.mp3", bookdir/f"zzChapter {n}b.mp3")

def join_all_split_bits(directory):
    for bookdir in get_leaf_dirs(directory):
        join_split_bits(bookdir)
