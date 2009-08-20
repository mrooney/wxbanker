#    https://launchpad.net/wxbanker
#    wxbanker.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

class MessagePanel(wx.Panel):
    def __init__(self, parent, message):
        wx.Panel.__init__(self, parent)
        self.Freeze()
        self.BackgroundColour = wx.BLACK
        self.Panel = panel = wx.Panel(self)
        panel.BackgroundColour = (0, 200, 100)
        
        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(panel, 1, wx.EXPAND|wx.ALL, 1)
        
        closeButton = wx.Button(panel, label=_("Dismiss"))
        
        self.Panel.Sizer = psizer = wx.BoxSizer()
        psizer.Add(wx.StaticText(panel, label=message), 0, wx.ALIGN_CENTER)
        psizer.AddStretchSpacer(1)
        psizer.Add(closeButton, 0, wx.ALIGN_CENTER)
        
        self.Thaw()
        closeButton.Bind(wx.EVT_BUTTON, self.OnDismiss)
        
        self.BestWidth, self.BestHeight = self.BestSize
        self.CurrentHeight = 0
        self.SetInitialSize((self.BestWidth, self.CurrentHeight))
        self.ExpandPanel()
        
    def ExpandPanel(self):
        self.CurrentHeight += 6
        if self.CurrentHeight >= self.BestHeight:
            self.CurrentHeight = self.BestHeight
        else:
            wx.CallLater(50, self.ExpandPanel)
            
        self.SetInitialSize((self.BestWidth, self.CurrentHeight))
        self.Parent.Layout()
        
    def OnDismiss(self, event):
        # We can't Layout after a Destroy, so Hide, Layout, then Destroy.
        self.Hide()
        self.Parent.Layout()
        self.Destroy()
        