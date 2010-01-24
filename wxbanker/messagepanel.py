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
        self.LinesPanel = wx.Panel(self)
        self.LinesPanel.Sizer = wx.BoxSizer(wx.VERTICAL)
        #self.Panel.BackgroundColour = self.LinesPanel.BackgroundColour = (0, 200, 100)
        
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(panel, 1, wx.EXPAND|wx.ALL, 1)
        self.Sizer.Add(self.LinesPanel, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 1)
        self.LinesPanel.Hide()
    
        self.Panel.Sizer = psizer = wx.BoxSizer()
        self.MessageText = wx.StaticText(panel, label=message)
        psizer.Add(self.MessageText, 0, wx.ALIGN_CENTER|wx.LEFT, 3)
        psizer.AddStretchSpacer(1)
        
        # Note at what position the buttons start, we'll use this in SizeMessage.
        self.BUTTON_START = len(psizer.Children)
        
        # Add the "Dismiss" button to get rid of the message.
        self.PushButton(_("Dismiss"), self.OnDismiss)
        
        self.BestWidth, self.BestHeight = self.Panel.BestSize
        self.CurrentHeight = 0
        self.Panel.SetInitialSize((self.BestWidth, self.CurrentHeight))
        
        # We are done moving stuff around, so thaw.
        self.Thaw()
        
        self.ExpandPanel()
        
    def SizeMessage(self):
        """Make sure the message text gets clipped appropriately."""
        # Figure out how wide it should be.
        availableSize = self.Parent.Size[0] - 5 # Allow a bit of pading.
        buttons = list(self.Panel.Sizer.Children)[2:]
        for button in buttons:
            availableSize -= button.Size[0]
            
        # Figure out the correct height.
        height = self.GetTextExtent(self.MessageText.Label[:5])[1]
        
        self.MessageText.SetInitialSize((availableSize, height))
        
    def ExpandPanel(self):
        self.CurrentHeight += 5
        if self.CurrentHeight >= self.BestHeight:
            self.CurrentHeight = self.BestHeight
        else:
            wx.CallLater(50, self.ExpandPanel)
            
        self.Panel.SetInitialSize((self.BestWidth, self.CurrentHeight))
        self.Parent.Layout()
    
    def AddLines(self, lines):
        sizer = self.LinesPanel.Sizer
        for line in lines:
            sizer.Add(wx.StaticText(self.LinesPanel, label=line), 0, wx.LEFT, 10)
    
    def ToggleLines(self, lines):
        self.LinesPanel.Show(not self.LinesPanel.IsShown())
        self.Parent.Layout()
        
    def PushButton(self, label, callback):
        """Create and prepend a button with label `label` which will call `callback` on a click."""
        button = wx.Button(self.Panel, label=label)
        button.Bind(wx.EVT_BUTTON, callback)
        
        self.Panel.Sizer.Insert(self.BUTTON_START, button, 0, wx.ALIGN_CENTER)
        self.SizeMessage()
        self.Layout()
        
    def Dismiss(self):
        # We can't Layout after a Destroy, so Hide, Layout, then Destroy.
        self.Hide()
        self.Parent.Layout()
        self.Destroy()

    def OnDismiss(self, event):
        self.Dismiss()
        
