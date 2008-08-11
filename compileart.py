from wx.tools import img2py
import os

base = 'silk'
validExts = ['png',]

# Append should initially be False, so the file is overwritten
# and the necessary imports/declarations are made.
append = False
for file in os.listdir(base):
    name, ext = [s.lower() for s in file.split('.')]
    if ext in validExts:
        #print 'img2pying %s' % file
        img2py.img2py(os.path.join(base, file), 'silk.py', append=append, imgName=name, catalog=True, functionCompatibile=False)
        # From now on, we want to append to the original file, not overwrite.
        append = True
    else:
        print 'Ignoring %s' % file

# Fix < 2.8 compatibility by shipping embeddedimage.py.
print "Fixing compatibility with wxPython < 2.8...",
lines = open('silk.py').readlines()
assert lines[3] == "from wx.lib.embeddedimage import PyEmbeddedImage\n", lines[3]
lines[3] = "from embeddedimage import PyEmbeddedImage\n"
open('silk.py', 'w').writelines(lines)
print "fixed!"
