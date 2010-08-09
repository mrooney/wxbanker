#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    compileart.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
#
#    This file is part of wxBanker.
#
#    wxBanker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    wxBanker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with wxBanker.  If not, see <http://www.gnu.org/licenses/>.
#

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

header = """#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    silk.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
#
#    This file is part of wxBanker.
#
#    wxBanker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    wxBanker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with wxBanker.  If not, see <http://www.gnu.org/licenses/>.
#
"""

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
lines[3] = "from wxbanker.art.embeddedimage import PyEmbeddedImage\n"
print "fixed!"

print "Adding demo frame and making %s module runnable..."%base,
for line in testFrame.splitlines(True):
    lines.append(line)
print "added!"

print "Prepending header (shebang and license)...",
headerLines = header.splitlines()
lines = headerLines + lines
print "prepended!"

print "Saving modified %s.py..."%base,
open('%s.py'%base, 'w').writelines(lines)
print "done!"
