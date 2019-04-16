import sqlite3
import mutagen
import os

from pathlib import Path
from common import makelist, get_mp3_files


APP_SUPPORT = Path('~/Library/Application Support/AudiobookHandler').expanduser()
DATABASEFILE = APP_SUPPORT / 'overdrive.db'


def create_database():
    if DATABASEFILE.exists():
        return
    connection = sqlite3.connect(DATABASEFILE)
    cursor = connection.cursor() 
    print('Creating Table...')
    cursor.execute('CREATE TABLE audiobookfiles (id INTEGER PRIMARY KEY, author VARCHAR(50), title VARCHAR(50), oldfilename VARCHAR(80), newfilename VARCHAR(80) )')
    connection.commit()
    cursor.close()
    connection.close()
    print('Table created')

def add_info_to_database(info):
    connection = sqlite3.dbapi2.connect(DATABASEFILE)
    cursor = connection.cursor() 
    insertinto = 'INSERT INTO audiobookfiles (author, title, oldfilename, newfilename) '
    author = info['author']#.replace("'","’") 
    title = info['title']#.replace("'","’") 
    old = info['oldfile']
    new = info['filename']#.replace("'","’")
    insertvalues = f"VALUES ('{author}', '{title}', '{old}', '{new}')"  
    values = (author, title, old, new)
    try:
        cursor.execute('INSERT INTO audiobookfiles (author, title, oldfilename, newfilename) VALUES (?,?,?,?)', values)
    except sqlite3.OperationalError as e:
        print(e)
        print(insertinto + insertvalues)
    connection.commit()
    cursor.close()
    connection.close()

def item_exists(info):
    connection = sqlite3.dbapi2.connect(DATABASEFILE)
    cursor = connection.cursor() 
    author = info['author']#.replace("'","’") 
    title = info['title']#.replace("'","’") 
    old = info['oldfile']
    new = info['filename']#.replace("'","’")
    values = (author, title, old, new)
    try:
        cursor.execute('SELECT COUNT(*) FROM audiobookfiles WHERE newfilename = ? AND author = ?', (new, author))
        results = cursor.fetchone()[0]
    except sqlite3.OperationalError as e:
        print(e)
        print(info)
    connection.commit()
    cursor.close()
    connection.close()
    return (results > 0)


def fill_database(directories):

    def file_info(path):
        origpath, filename = os.path.split(path)
        tags = mutagen.File(path, easy=True)
        return {
            'filename' : filename,
            'oldfile' : 'unknown',
            'title' : tags['album'][0],
            'author' : tags['artist'][0],
            }

    connection = sqlite3.dbapi2.connect(DATABASEFILE)
    cursor = connection.cursor()
    for directory in directories:
        books = makelist(directory)
        for book in books:
            print(book)
            for mp3file in get_mp3_files(book):
                info = file_info(mp3file)
                author = info['author'].replace("'","’") 
                title = info['title'].replace("'","’") 
                old = info['oldfile']
                new = info['filename'].replace("'","’")
                values = (author, title, old, new)
                try:
                    cursor.execute('INSERT INTO audiobookfiles (author, title, oldfilename, newfilename) VALUES (?,?,?,?)', values)
                except sqlite3.OperationalError as e:
                    print(e)
                    print(values)
    connection.commit()
    cursor.close()
    connection.close()
