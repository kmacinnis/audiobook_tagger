import os
import shutil
import errno
import mutagen



fail_codes = "🅰🅱🅲🅳🅴🅵🅶🅷🅸🅹🅺🅻🅼🅽🅾🅿🆀🆁🆂🆃🆄🆅🆆🆇🆈🆉"

def fail(n):
    # print(fail_codes[n], end='')
    pass

def succeed():
    # print("💎", end='')
    pass

def display_tags(path):
    print(f'Tags for {path}')
    try:
        tags = mutagen.File(path, easy=True)
    except mutagen.mp3.HeaderNotFoundError:
        print('Cannot read tags')
        return
    for key in tags.keys(): 
        print('        •', key.ljust(16), tags[key])
    print()

def preview_tags(dirs):
    for directory in dirs: 
        display_tags(get_mp3_files(directory)[0])

def mkdir_p(path):
    '''Makes directories, ignoring errors if it already exists'''
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

def copy(old, new):
    '''Copies a file from old to new, creating directories where necessary '''
    newpath = os.path.split(new)[0]
    mkdir_p(newpath)
    shutil.copy(old, new)

def merge(old, new):
    for root, dirs, files in os.walk(old, followlinks=True):
        for name in files:
            oldpathandname = os.path.join(root, name)
            relpath = os.path.relpath(oldpathandname, start=old)
            newpathandname = os.path.join(new,relpath)
            os.renames(oldpathandname, newpathandname)

def makelist(startdir):
    dirlist = []
    for root, dirs, files in os.walk(startdir, followlinks=True):
        if dirs == []:
            dirlist.append(root)
    return dirlist

def get_mp3_files(directory):
    return [os.path.join(directory, i)
                         for i in os.listdir(directory) if i[-4:]=='.mp3']

