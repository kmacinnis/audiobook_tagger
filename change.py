import mutagen


from goodreads import client
API_KEY = "iaqF5jmbfkRAsudBGVHXLg"
CLIENT_SECRET = "2Af9zFVtOHVAlJcCM9DjymoeOMFKv6ePo1YC3GhxaQg"
gc = client.GoodreadsClient(API_KEY, CLIENT_SECRET)

startdir = "/Volumes/media/audiobooks/"

# import os
# rootdirsfiles = tuple(os.walk(startdir))
# rootdirsfiles
# _[0]
# import random
# random.choice(rootdirsfiles)
# os.path.relpath(startdir,_[0])
# _23
# _[0]
# path = _
# os.path.relpath(startdir,path)
# path
# startdir
# os.path.relpath(path, start=startdir)
# gc.search_books(_)
# os.path.relpath(path, start=startdir).split('/')
# author, title = os.path.relpath(path, start=startdir).split('/')
# gc.search_books(title)
# gc.search_books(title + ' - ' + author)
# gc.search_books(f'{title} - {author}')








def clean(title):
    return title.split(' (')




def update_tags(startdir):
    gc = client.GoodreadsClient(API_KEY, CLIENT_SECRET)
    for root, dirs, files in os.walk(startdir, followlinks=True):
        if dirs == []:
            print(root)
            author, title = os.path.relpath(root, start=startdir).split('/')
            results = gc.search_books(f'{title} - {author}')
            book = results[0]
            year = book.publication_date[2]
            print(f'{book.title}   -   {book.authors[0]}   ({year})')
            print()


for directory in dirs:
    # try:
        print(directory)
        author, title = os.path.relpath(directory, start=startdir).split('/')
        results = gc.search_books(f'{title} - {author}')
        for i, book in enumerate(results[:3], 1):
            print(f'{i}. {book.title} - {book.authors[0]} ({book.publication_date[2]})')
        print()
    
        mp3files = [os.path.join(directory, i) 
                    for i in os.listdir(directory) if i[-4:]=='.mp3']
        tags = mutagen.File(mp3files[0], easy=True)
        for key in tags.keys(): 
            print('        • ',key.ljust(16), tags[key])
        for item in mp3files:
            tags = mutagen.File(item, easy=True)
            if 'date' not in tags.keys():
                tags['date'] = book.publication_date[2]
                
            if '(' in tags['title']:
                newtitle = tags['title'].split(' (')[0]
                tags['title'] = newtitle
        # tags.save()
    # except:
   #      pass
    



        