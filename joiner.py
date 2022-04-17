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


def reencode(directory):
    dirs = get_leaf_dirs(directory)
    mp3s_with_errors = []
    for bookdir in dirs:
        for chapter in bookdir.iterdir():
            if chapter.suffix != '.mp3':
                continue
            name = chapter.name
            newchapter = f'zz {name}'
            ffmpeg_args = ['ffmpeg',
                             '-i', name,
                             '-codec:a', 'libmp3lame',
                             '-b:a', '64k', 
                             newchapter]
            subprocess.run(ffmpeg_args, cwd=bookdir)
            reencodeprocess = subprocess.run(args, cwd=book)
            if reencodeprocess.returncode != 0:
                mp3s_with_errors.append(mp3file)
    if mp3s_with_errors:
        print('✖✖✖ The following files had errors when attempting to reencode! ✖✖✖')
        for errfile in mp3s_with_errors:
            print('    ✖ {errfile.relative_to(bookdir.parent.parent)}')
        return mp3s_with_errors
    else:
        print('\n\nAll files reencoded with no errors!')
    

for bookdir in authordir.iterdir():
    reencode(bookdir)

