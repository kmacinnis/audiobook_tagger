import os
import subprocess
from pathlib import Path


for n in range(17): 
    print(f'ffmpeg -f concat -safe 0 -i ch{n}.txt -c copy ch{n}.mp3') 

%pwd
bookdir = Path(_)
maxnum = len(list(bookdir.iterdir())) + 1

for n in range(maxnum):
    check_file = bookdir/f"Chapter {n}a.mp3"
    if not check_file.exists():
        print(f"- Not needed for Chapter {n}")
        continue
    filename = f"Chapter{n}.txt"
    with open(bookdir/filename, 'w') as f:
        contents = f"file 'Chapter {n}a.mp3'\nfile 'Chapter {n}b.mp3'\n"
        f.write(contents)
    print(f"⦾ Created concat file for Chapter {n}")
    
    mp3name = f'Chapter {n}.mp3'
    first_mp3 = f'Chapter {n}a.mp3'
    ffmpeg_args = [ 'ffmpeg', '-f', 'concat', '-safe', '0', '-i', filename, 
                    '-i', first_mp3, '-map_metadata', '1',
                    '-c', 'copy', mp3name]
    # print(' '.join(ffmpeg_args))
    subprocess.call(ffmpeg_args)
    print()
    print(f"Joined files for Chapter {n}")
        
    os.rename(f"Chapter {n}a.mp3",f"zzChapter {n}a.mp3")    
    os.rename(f"Chapter {n}b.mp3",f"zzChapter {n}b.mp3")


