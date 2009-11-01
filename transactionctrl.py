#    https://launchpad.net/wxbanker
#    transactionctrl.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
from newtransactionctrl import TransferRow
        
class TransactionCtrl(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.Sizer = wx.GridBagSizer(1, 1)
        self.Sizer.SetEmptyCellSize((0,0))
        
        TransferRow(self, 0)
        
    def ShowRow(self, row, show=True):
        for child in self.Sizer.GetChildren():
            if child.Pos[0] == row:
                child.Show(show)
        self.Layout()
        
        
if __name__ == "__main__":
    app = wx.App()
    f = wx.Frame(None)
    TransactionCtrl(f)
    f.Show()
    app.MainLoop()