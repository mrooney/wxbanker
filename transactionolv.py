"""
A refactor of TransactionGrid, using ObjectListView.

Can we bind this to the list so inserts and removals and automatically handled?

IMPLEMENTED:
- displaying transactions
- editable amounts/descriptions
- edits pushed to model
- total based on total of last transaction
- handle new transactions
- min column sizes when there aren't any transactions
- default sort by date
- display negative amount as Red
- right-click context menu
  - remove
  - calculator options on amounts
- amount editing as %.2f (instead of 2.16999999 etc)
- searching
- editable date
- changing date moves transaction appropriately
- handle currency changes
TODO (for feature parity):
- done? totals automatically updates for transaction changes above them
- disable sorting on Total column
- flickerless repositioning when changing date
- flickerless RefreshObjects
- flickerless remove transaction
NEW THINGS:
- sorting by columns
- empty account message
- fixed:
 - slow resizing
 - unnecessary scrollbars sometimes
"""

import wx, datetime
from wx.lib.pubsub import Publisher
from ObjectListView import GroupListView, ColumnDefn, CellEditorRegistry
import bankcontrols


class TransactionOLV(GroupListView):
    def __init__(self, parent, bankController):
        GroupListView.__init__(self, parent, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.CurrentAccount = None
        self.BankController = bankController
        self.SORT_COL = 1
        
        self.showGroups = False
        self.evenRowsBackColor = wx.Color(224,238,238)
        self.oddRowsBackColor = wx.WHITE
        self.rowFormatter = self.rowFormatter2
        self.cellEditMode = GroupListView.CELLEDIT_DOUBLECLICK
        self.SetEmptyListMsg("No transactions entered.")
        
        # Calculate the necessary width for the date column.
        dateStr = str(datetime.date.today())
        dateWidth = self.GetTextExtent(dateStr)[0] + 10
        
        # Make a bogus first column, since the 1st column isn't editable in CELLEDIT_SINGLECLICK mode.
        bogusColumn = ColumnDefn("", fixedWidth=0)
        bogusColumn.isInternal = True
        
        self.SetColumns([
            bogusColumn,
            ColumnDefn(_("Date"), valueGetter=self.getDateOf, valueSetter=self.setDateOf, width=dateWidth),
            ColumnDefn(_("Description"), valueGetter="Description", isSpaceFilling=True),
            ColumnDefn(_("Amount"), "right", valueGetter="Amount", stringConverter=self.renderFloat),
            ColumnDefn(_("Total"), "right", valueGetter=self.getTotal, stringConverter=self.renderFloat, isEditable=False),
        ])
        # Our custom hack in OLV.py line 2017 will render floats appropriately as %.2f
        
        # By default, sort by the date column, ascending.
        self.SortBy(self.SORT_COL)
        
        self.Bind(wx.EVT_RIGHT_DOWN, self.onRightDown)
        
        Publisher.subscribe(self.onSearch, "SEARCH.INITIATED")
        Publisher.subscribe(self.onSearchCancelled, "SEARCH.CANCELLED")
        Publisher.subscribe(self.onSearchMoreToggled, "SEARCH.MORETOGGLED")
        Publisher.subscribe(self.onTransactionAdded, "transaction.created")
        Publisher.subscribe(self.onTransactionRemoved, "transaction.removed")
        Publisher.subscribe(self.onCurrencyChanged, "currency_changed")
        
    def SetObjects(self, objs, *args, **kwargs):
        """
        Override the default SetObjects to properly refresh the auto-size,
        and clear out any cached Totals as they may not be valid IE when we
        search and have a subset of transactions.
        """
        # Remove any previously cached totals, to fix search totals.
        for obj in objs:
            obj._Total = None
            
        GroupListView.SetObjects(self, objs, *args, **kwargs)
        
    def getDateOf(self, transaction):
        return str(transaction.Date)
    
    def setDateOf(self, transaction, date):
        transaction.Date = date
        self.Freeze()
        self.SortBy(self.SORT_COL)
        self.Thaw()
        
    def getTotal(self, transObj):
        """
        A somewhat hackish implementation, but an improvement!
        """
        i = self.GetIndexOf(transObj)
        if i == 0:
            total = transObj.Amount
        else:
            previousObj = self.GetObjectAt(i-1)
            
            try:
                previousTotal = previousObj._Total
                if previousTotal is None:
                    raise AttributeError
            except AttributeError:
                previousTotal = self.getTotal(previousObj)
            
            total = previousTotal + transObj.Amount
                
        transObj._Total = total
        return total
    
    def rowFormatter2(self, listItem, transaction):
        if transaction.Amount < 0:
            listItem.SetTextColour(wx.RED)
    
    def renderFloat(self, floatVal):
        return self.CurrentAccount.float2str(floatVal)
    
    def setAccount(self, account, scrollToBottom=True):
        self.CurrentAccount = account
        
        if account is None:
            transactions = []
        else:
            transactions = account.Transactions
        
        self.SetObjects(transactions)
        
        if scrollToBottom:
            self.ensureVisible(-1)
        
    def ensureVisible(self, index):
        length = self.GetItemCount()
        # If there are no items, ensure a no-op (LP: #338697)
        if length:
            if index < 0:
                index = length + index
            self.EnsureCellVisible(index, 0)
        
    def onRightDown(self, event):
        itemID, flag, col = self.HitTestSubItem(event.Position)

        # Don't do anything for right-clicks not on items.
        if itemID != -1:
            if not self.GetItemState(itemID, wx.LIST_STATE_SELECTED):
                self._SelectAndFocus(itemID)
            transactions = self.GetSelectedObjects()
            self.showContextMenu(transactions, col)
    
    def showContextMenu(self, transactions, col):
        menu = wx.Menu()

        if col in (3,4):
            # This is an amount cell, allow calculator options.
            if col == 3:
                amount = sum((t.Amount for t in transactions))
            else:
                amount = transactions[-1]._Total
            val = self.BankController.Model.float2str(amount)
            
            actions = [
                (_("Send %s to calculator") % val, "wxART_calculator_edit"),
                (_("Add %s to calculator") % val, "wxART_calculator_add"),
                (_("Subtract %s from calculator") % val, "wxART_calculator_delete"),
            ]

            for actionStr, artHint in actions:
                item = wx.MenuItem(menu, -1, actionStr)
                item.SetBitmap(wx.ArtProvider.GetBitmap(artHint))
                menu.Bind(wx.EVT_MENU, lambda e, s=actionStr: self.onCalculatorAction(transactions, col, s), source=item)
                menu.AppendItem(item)
            menu.AppendSeparator()

        # Always show the Remove context entry.
        if len(transactions) == 1:
            removeStr = _("Remove this transaction")
        else:
            removeStr = _("Remove these %i transactions") % len(transactions)
            
        removeItem = wx.MenuItem(menu, -1, removeStr)
        menu.Bind(wx.EVT_MENU, lambda e: self.onRemoveTransactions(transactions), source=removeItem)
        removeItem.SetBitmap(wx.ArtProvider.GetBitmap('wxART_delete'))
        menu.AppendItem(removeItem)

        # Show the menu and then destroy it afterwards.
        self.PopupMenu(menu)
        menu.Destroy()

    def onCalculatorAction(self, transactions, col, actionStr):
        """
        Given an action to perform on the calculator, and the row and col,
        generate the string of characters necessary to perform that action
        in the calculator, and push them.
        """
        command = actionStr.split(' ')[0].upper()
        
        if col == 3:
            amount = sum((t.Amount for t in transactions))
        elif col == 4:
            # Use the last total, if multiple are selected.
            amount = transactions[-1]._Total
        else:
            raise Exception("onCalculatorAction should only be called with col 3 or 4.")

        pushStr = {'SEND': 'C%s', 'SUBTRACT': '-%s=', 'ADD': '+%s='}[command]
        pushStr %= amount

        Publisher.sendMessage("CALCULATOR.PUSH_CHARS", pushStr)

    def onRemoveTransactions(self, transactions):
        """Remove the transaction from the account."""
        #TODO: each call in the loop is going to force a freeze, resize, and thaw. Ideally batch this.
        for transaction in transactions:
            self.CurrentAccount.RemoveTransaction(transaction)
        
    def frozenResize(self):
        self.Parent.Layout()
        self.Parent.Thaw()
        
    def onTransactionRemoved(self, message):
        account, transaction = message.data
        if account is self.CurrentAccount:
            # Remove the item from the list.
            self.RemoveObject(transaction)
    
    def onTransactionAdded(self, message):
        account, transaction = message.data
        if account is self.CurrentAccount:
            self.AddObject(transaction)
            #TODO: Perhaps get the actual position and scroll to that, it may not be last.
            self.ensureVisible(-1)
        
    def onSearch(self, message):
        searchString, accountScope, match, caseSens = message.data

        if accountScope == 0: # Search in just current account.
            account = self.CurrentAccount
        else: # Search in all accounts.
            account = None

        matches = self.BankController.Model.Search(searchString, account=account, matchIndex=match, matchCase=caseSens)
        self.SetObjects(matches)
        self.Parent.Parent.searchActive = True

    def onSearchCancelled(self, message):
        # Ignore cancels on an inactive search to avoid silly refreshes.
        if self.Parent.Parent.searchActive:
            self.setAccount(self.CurrentAccount)
            self.Parent.Parent.searchActive = False

    def onSearchMoreToggled(self, message):
        # Perhaps necessary to not glitch overlap on Windows?
        self.Refresh()
        
    def onCurrencyChanged(self, message):
        self.RefreshObjects()


if __name__ == "__main__":
    app = wx.App(False)
    olvFrame(None).Show()
    app.MainLoop()
