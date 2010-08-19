#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    brandedframe.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

import wx
import os

def getIcon():
    appIcon = wx.ArtProvider.GetIcon('wxART_coins')
    # Use a higher resolution icon if available (LP: #617645)
    hiResIconPath = '/usr/share/icons/hicolor/48x48/apps/wxbanker.png'
    if os.path.exists(hiResIconPath):
        appIcon = wx.Icon(hiResIconPath, wx.BITMAP_TYPE_PNG)
    return appIcon

class BrandedFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        appIcon = getIcon()
        self.SetIcon(appIcon)
