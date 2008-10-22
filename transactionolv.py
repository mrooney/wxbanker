"""
A refactor of TransactionGrid, using ObjectListView.

Can we bind this to the list so inserts and removals and automatically handled?

IMPLEMENTED:
- displaying transactions
- editable amounts/descriptions
- edits pushed to model
TODO (for feature parity):
- editable date
- total based on total of last transaction
- totals automatically updates for transaction changes above them
- display negative amount as Red
- right-click context menu
  - remove
  - calculator options on amounts
- handle new transactions
- min column sizes when there aren't any transactions
EXTRA:
- custom negative option such as Red, (), or Red and ()

"""

import wx
from wx.lib.pubsub import Publisher
from ObjectListView import GroupListView, ColumnDefn
#from model_sqlite import Model
from banker import Bank # only temporary until Transactions can do float2str themselves


class TransactionOLV(GroupListView):
    def __init__(self, parent):
        GroupListView.__init__(self, parent, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        
        self.showGroups = False
        self.evenRowsBackColor = wx.Color(224,238,238)
        self.oddRowsBackColor = wx.WHITE
        self.cellEditMode = GroupListView.CELLEDIT_SINGLECLICK
        self.SetEmptyListMsg("No transactions entered.")
        self.SetColumns([
            ColumnDefn("Date", valueGetter="Date", minimumWidth=100),
            ColumnDefn("Description", valueGetter="Description", isSpaceFilling=True, minimumWidth=80),
            ColumnDefn("Amount", "right", valueGetter="Amount", stringConverter=Bank().float2str, minimumWidth=80),
            ColumnDefn("Total", "right", valueGetter=self.getTotal, stringConverter=Bank().float2str, minimumWidth=80, isEditable=False),
        ])
        
    def getTotal(self, transObj):
        """
        This is a really really bad way to do this, O(N**2) perhaps?
        It is a "for each item: for each item2 before item", in essence.
        """
        i = self.GetIndexOf(transObj)
        if i == 0:
            total = 0
        else:
            previousTotal = self.GetValueAt( self.GetObjectAt(i-1), 3 )
            
            total = previousTotal + transObj.Amount
            
        return total
    
    def setAccount(self, accountName):
        transactions = Bank().getTransactionsFrom(accountName)
        self.SetObjects(transactions)
        self.Parent.Layout() # Necessary for columns to size properly. (GTK)
        
    def ensureVisible(self, index):
        # I wonder if this is needed in OLV? Probably.
        print "ensureVisible STUB: ", index
    

class olvFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        self.Size = (800, 600)
        panel = wx.Panel(self)
        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(panel, 1, wx.EXPAND)
        panel.Sizer = wx.BoxSizer()

        m = Model('bank')
        transactions = m.getTransactionsFrom('HSBC Checking')
        glv = TransactionOLV(panel)
        glv.SetObjects(transactions)

        panel.Sizer.Add(glv, 1, wx.EXPAND)
        Publisher.subscribe(self.onMessage)

    def onMessage(self, message):
        print message.topic, message.data


if __name__ == "__main__":
    app = wx.App(False)
    olvFrame(None).Show()
    app.MainLoop()
