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
from wx.lib.pubsub import Publisher

from newtransactionctrl import TransferRow, NewTransactionRow, RecurringRow
from recurringsummaryrow import RecurringSummaryRow
        
class TransactionCtrl(wx.Panel):
    RECURRING_ROW = 0
    SUMMARY_ROW = 1
    TRANSFER_ROW = 2
    TRANSACTION_ROW = 3
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.Sizer = wx.GridBagSizer(1, 1)
        self.Sizer.SetEmptyCellSize((0,0))
        self.Sizer.AddGrowableCol(1, 1)
        
        self.transferRow = TransferRow(self, self.TRANSFER_ROW)
        self.recurringSummaryRow = RecurringSummaryRow(self, self.SUMMARY_ROW)
        self.transactionRow = NewTransactionRow(self, self.TRANSACTION_ROW)
        self.recurringRow = RecurringRow(self, self.RECURRING_ROW)
        
        # Hide everything up to the actual transaction row initially.
        for i in range(self.TRANSACTION_ROW):
            self.ShowRow(i, False)
        
        Publisher.subscribe(self.onTransferToggled, "newtransaction.transfertoggled")
        Publisher.subscribe(self.onRecurringToggled, "newtransaction.recurringtoggled")
        
    def onTransferToggled(self, message):
        transfer = message.data
        self.ShowRow(self.TRANSFER_ROW, transfer)
        
    def onRecurringToggled(self, message):
        recurring = message.data
        for row in (self.SUMMARY_ROW, self.RECURRING_ROW):
            self.ShowRow(row, recurring)
        
    def ShowRow(self, row, show=True):
        self.Freeze()
        for child in self.Sizer.GetChildren():
            if child.Pos[0] == row:
                child.Show(show)
        self.Parent.Layout()
        self.Thaw()
        
        
if __name__ == "__main__":
    app = wx.App()
    f = wx.Frame(None)
    TransactionCtrl(f)
    f.Show()
    app.MainLoop()