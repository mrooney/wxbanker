"""
A script to generate an img2py catalog module, given a directory full of images.

It will also append some code to the end of the module, making it runnable,
displaying a frame of all the available icons in the module, with the mouseover
tooltip being the name of the icon.

Note that this MUST be run with wxPython >= 2.8.8.0, although it will generate
compatible code with at least back to 2.8.7.1 (and probably much farther).
"""
from wx.tools import img2py
import os

base = 'silk'
validExts = ['png',]
testFrame = """
# Added so that the img2py module is runnable, for a sample of all available art.
import wx

class ArtFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Available Icons")
        panel = wx.Panel(self)
        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(panel, 1, wx.EXPAND)

        import wx.lib.art.img2pyartprov as img2pyartprov
        class fakemodule:
            catalog = catalog
            index = index
        wx.ArtProvider.Push(img2pyartprov.Img2PyArtProvider(fakemodule()))

        panel.Sizer = wx.FlexGridSizer(cols=40, vgap=2, hgap=2)
        iconNames = sorted(catalog.keys())
        self.SetIcon(wx.ArtProvider.GetIcon(iconNames[0]))
        for iconName in iconNames:
            bmp = wx.StaticBitmap(panel, bitmap=wx.ArtProvider.GetBitmap('wxART_'+iconName))
            bmp.SetToolTipString(iconName)
            panel.Sizer.Add(bmp)

        self.Layout()
        self.Fit()


def main():
    app = wx.App(False)
    frame = ArtFrame().Show()
    app.MainLoop()


if __name__ == "__main__":
    main()

"""

# Append should initially be False, so the file is overwritten
# and the necessary imports/declarations are made.
append = False
for file in os.listdir(base):
    name, ext = [s.lower() for s in file.split('.')]
    if ext in validExts:
        #print 'img2pying %s' % file
        try:
            img2py.img2py(os.path.join(base, file), '%s.py'%base, append=append, imgName=name, catalog=True, functionCompatible=False)
        except TypeError:
            # Try with the typo that existed in wxPython 2.8.8.0 but fixed since 2.8.8.1.
            img2py.img2py(os.path.join(base, file), '%s.py'%base, append=append, imgName=name, catalog=True, functionCompatibile=False)
        # From now on, we want to append to the original file, not overwrite.
        append = True
    else:
        print 'Ignoring %s' % file

# Fix < 2.8 compatibility by shipping embeddedimage.py.
print "Fixing compatibility with wxPython < 2.8...",
lines = open('%s.py'%base).readlines()
assert lines[3] == "from wx.lib.embeddedimage import PyEmbeddedImage\n", lines[3]
lines[3] = "from embeddedimage import PyEmbeddedImage\n"
print "fixed!"

print "Adding demo frame and making %s module runnable..."%base,
for line in testFrame.splitlines(True):
    lines.append(line)
print "added!"

print "Saving modified %s.py..."%base,
open('%s.py'%base, 'w').writelines(lines)
print "done!"
