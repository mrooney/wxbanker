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

import wx, datetime
from wx.lib.pubsub import Publisher

from newtransactionctrl import TransferRow, NewTransactionRow, RecurringRow, WeeklyRecurringRow
from recurringsummaryrow import RecurringSummaryRow
from bankobjects.recurringtransaction import RecurringTransaction
        
class TransactionCtrl(wx.Panel):
    RECURRING_ROW = 0
    SUMMARY_ROW = 1
    WEEKLY_ROW = 2
    TRANSFER_ROW = 3
    TRANSACTION_ROW = 4
    
    def __init__(self, parent, editing=False):
        wx.Panel.__init__(self, parent)
        # Create the recurring object we will use internally.
        self.recurringObj = RecurringTransaction(None, None, 0, "", datetime.date.today(), RecurringTransaction.DAILY)
        
        self.Sizer = wx.GridBagSizer(3, 3)
        self.Sizer.SetEmptyCellSize((0,0))
        self.Sizer.AddGrowableCol(1, 1)
        
        self.recurringRow = RecurringRow(self, self.RECURRING_ROW)
        self.recurringSummaryRow = RecurringSummaryRow(self, self.SUMMARY_ROW)
        self.weeklyRecurringRow = WeeklyRecurringRow(self, self.WEEKLY_ROW)
        self.transferRow = TransferRow(self, self.TRANSFER_ROW)
        self.transactionRow = NewTransactionRow(self, self.TRANSACTION_ROW, editing)
        
        # RecurringRow needs an update once both it and the other controls exist.
        self.recurringRow.Update()
        
        # Hide everything up to the actual transaction row initially.
        if not editing:
            for i in range(self.TRANSACTION_ROW):
                self.ShowRow(i, False)
        
        ctrlId = id(self.transactionRow)
        Publisher.subscribe(self.onTransferToggled, "newtransaction.%i.transfertoggled"%ctrlId)
        Publisher.subscribe(self.onRecurringToggled, "newtransaction.%i.recurringtoggled"%ctrlId)
        
    def onTransferToggled(self, message):
        transfer = message.data
        self.ShowRow(self.TRANSFER_ROW, transfer)
        
    def onRecurringToggled(self, message):
        recurring = message.data
        for row in (self.SUMMARY_ROW, self.RECURRING_ROW, self.WEEKLY_ROW):
            self.ShowRow(row, recurring)
        
    def ShowRow(self, row, show=True):
        self.Freeze()
        for child in self.Sizer.GetChildren():
            if child.Pos[0] == row:
                child.Show(show)
        self.Parent.Layout()
        self.Thaw()
        
    def ShowWeekly(self, show=True):
        self.ShowRow(self.WEEKLY_ROW, show)
        
    def UpdateSummary(self):
        self.recurringSummaryRow.UpdateSummary(self.recurringObj)
        
    def GetSettings(self):
        repeatType, repeatEvery, end = self.recurringRow.GetSettings()
        repeatsOn = None
        if repeatType == RecurringTransaction.WEEKLY:
            repeatsOn = self.weeklyRecurringRow.GetSettings()
            
        return repeatType, repeatEvery, repeatsOn, end
    
    def FromRecurring(self, rt):
        self.recurringObj = rt
        
        self.ShowRow(self.TRANSFER_ROW, bool(rt.Source))
        self.ShowRow(self.WEEKLY_ROW, rt.IsWeekly())

        self.recurringSummaryRow.UpdateSummary(rt)
        self.weeklyRecurringRow.FromRecurring(rt)
        self.transferRow.FromRecurring(rt)
        self.transactionRow.FromRecurring(rt)
        
        
if __name__ == "__main__":
    app = wx.App()
    f = wx.Frame(None)
    TransactionCtrl(f)
    f.Show()
    app.MainLoop()