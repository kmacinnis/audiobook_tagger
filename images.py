# TODO: Automatically resize images to square.







fd = urllib.urlopen(cover)
# Drop the entire PIL part
covr = MP4Cover(fd.read(), getattr(
            MP4Cover,
            'FORMAT_PNG' if cover.endswith('png') else 'FORMAT_JPEG'
        ))
fd.close() # always a good thing to do

tags['covr'] = [covr] # make sure it's a list
tags.save()


