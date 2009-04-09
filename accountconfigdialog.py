#    https://launchpad.net/wxbanker
#    accountconfigdialog.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

class AccountConfigDialog(wx.Dialog):
    def __init__(self, parent, account):
        wx.Dialog.__init__(self, parent, title=account.Name)
        
        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(wx.StaticText(self, -1, "Hello."))
        
    def createMintConfigPanel(self):
        panel = wx.Panel(self)
        
        
        
    