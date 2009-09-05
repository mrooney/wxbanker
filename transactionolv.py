#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    transactionolv.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
"""
A refactor of TransactionGrid, using ObjectListView.

TODO (for feature parity):
- disable sorting on Total column
- flickerless repositioning when changing date
- flickerless RefreshObjects
- flickerless remove transaction
- handle batch events at UI level
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

        self.showGroups = False
        self.evenRowsBackColor = wx.Color(224,238,238)
        self.oddRowsBackColor = wx.WHITE
        self.cellEditMode = GroupListView.CELLEDIT_DOUBLECLICK
        self.SetEmptyListMsg(_("No transactions entered."))

        # Calculate the necessary width for the date column.
        dateStr = str(datetime.date.today())
        dateWidth = self.GetTextExtent(dateStr)[0] + 10

        # Define some constants to use throughout.
        self.COL_DATE = 0
        self.COL_AMOUNT = 2
        self.COL_TOTAL = 3

        self.SetColumns([
            ColumnDefn(_("Date"), valueGetter=self.getDateOf, valueSetter=self.setDateOf, width=dateWidth),
            ColumnDefn(_("Description"), valueGetter="Description", isSpaceFilling=True, editFormatter=self.renderEditDescription),
            ColumnDefn(_("Amount"), "right", valueGetter="Amount", stringConverter=self.renderFloat, editFormatter=self.renderEditFloat),
            ColumnDefn(_("Total"), "right", valueGetter=self.getTotal, stringConverter=self.renderFloat, isEditable=False),
        ])
        # Our custom hack in OLV.py:2017 will render amount floats appropriately as %.2f when editing.

        # By default, sort by the date column, ascending.
        self.SORT_COL = self.COL_DATE
        self.SortBy(self.SORT_COL)
        
        self.Bind(wx.EVT_RIGHT_DOWN, self.onRightDown)

        self.Subscriptions = (
            (self.onSearch, "SEARCH.INITIATED"),
            (self.onSearchCancelled, "SEARCH.CANCELLED"),
            (self.onSearchMoreToggled, "SEARCH.MORETOGGLED"),
            (self.onTransactionAdded, "transaction.created"),
            (self.onTransactionsRemoved, "transactions.removed"),
            (self.onCurrencyChanged, "currency_changed"),
            (self.updateTotals, "ormobject.updated.Transaction.Amount"),
            (self.onTransactionDateUpdated, "ormobject.updated.Transaction.Date"),
        )

        for callback, topic in self.Subscriptions:
            Publisher.subscribe(callback, topic)

    def SetObjects(self, objs, *args, **kwargs):
        """
        Override the default SetObjects to properly refresh the auto-size,
        and clear out any cached Totals as they may not be valid IE when we
        search and have a subset of transactions.
        """
        # Remove any previously cached totals, to fix search totals.
        GroupListView.SetObjects(self, objs, *args, **kwargs)
        self.updateTotals()

        # Force a re-size here, in the case that the vscrollbar-needed state
        # changed by this set account, to size correctly.
        wx.CallLater(50, self._ResizeSpaceFillingColumns)
        
    def onTransactionDateUpdated(self, message):
        transaction = message.data
        self.RefreshObject(transaction)
        self.SortBy(self.SORT_COL)
        self.updateTotals()

    def getDateOf(self, transaction):
        return str(transaction.Date)

    def setDateOf(self, transaction, date):
        transaction.Date = date
        self.Freeze()
        self.SortBy(self.SORT_COL)
        self.Thaw()

    def getTotal(self, transObj):
        if not hasattr(transObj, "_Total"):
            self.updateTotals()
        
        return transObj._Total
    
    def updateTotals(self, message=None):
        first = self.GetObjectAt(0)
        if first is None:
            return
        
        first._Total = first.Amount
        
        b = first
        for i in range(1, len(self.GetObjects())):
            a, b = b, self.GetObjectAt(i)
            b._Total = a._Total + b.Amount

    def renderFloat(self, floatVal):
        return self.CurrentAccount.float2str(floatVal)
    
    def renderEditFloat(self, modelObj):
        return "%.2f" % modelObj.Amount
    
    def renderEditDescription(self, modelObj):
        return modelObj._Description

    def setAccount(self, account, scrollToBottom=True):
        self.CurrentAccount = account

        if account is None:
            transactions = []
        else:
            transactions = account.Transactions

        self.SetObjects(transactions)
        # Unselect everything.
        self.SelectObjects([], deselectOthers=True)
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

    def showContextMenu(self, transactions, col, removeOnly=False):
        menu = wx.Menu()

        if not removeOnly and col in (self.COL_AMOUNT, self.COL_TOTAL):
            # This is an amount cell, allow calculator options.
            if col == self.COL_AMOUNT:
                amount = sum((t.Amount for t in transactions))
            else:
                amount = transactions[-1]._Total
            val = self.BankController.Model.float2str(amount)

            actions = [
                (_("Send %s to calculator") % val, "wxART_calculator_edit"),
                (_("Add %s to calculator") % val, "wxART_calculator_add"),
                (_("Subtract %s from calculator") % val, "wxART_calculator_delete"),
            ]

            for i, (actionStr, artHint) in enumerate(actions):
                item = wx.MenuItem(menu, -1, actionStr)
                item.SetBitmap(wx.ArtProvider.GetBitmap(artHint))
                menu.Bind(wx.EVT_MENU, lambda e, i=i: self.onCalculatorAction(transactions, col, i), source=item)
                menu.AppendItem(item)
            menu.AppendSeparator()

        # Always show the Remove context entry.
        if len(transactions) == 1:
            removeStr = _("Remove this transaction")
            moveStr = _("Move this transaction to account")
        else:
            removeStr = _("Remove these %i transactions") % len(transactions)
            moveStr = _("Move these %i transactions to account") % len(transactions)

        removeItem = wx.MenuItem(menu, -1, removeStr)
        menu.Bind(wx.EVT_MENU, lambda e: self.onRemoveTransactions(transactions), source=removeItem)
        removeItem.SetBitmap(wx.ArtProvider.GetBitmap('wxART_delete'))
        menu.AppendItem(removeItem)

        if not removeOnly:
            # Create the sub-menu of sibling accounts to the move to.
            moveToAccountItem = wx.MenuItem(menu, -1, moveStr)
            accountsMenu = wx.Menu()
            for account in self.CurrentAccount.GetSiblings():
                accountItem = wx.MenuItem(menu, -1, account.GetName())
                accountsMenu.AppendItem(accountItem)
                accountsMenu.Bind(wx.EVT_MENU, lambda e, account=account: self.onMoveTransactions(transactions, account), source=accountItem)
            moveToAccountItem.SetSubMenu(accountsMenu)
            menu.AppendItem(moveToAccountItem)

        # Show the menu and then destroy it afterwards.
        self.PopupMenu(menu)
        menu.Destroy()

    def onCalculatorAction(self, transactions, col, i):
        """
        Given an action to perform on the calculator, and the row and col,
        generate the string of characters necessary to perform that action
        in the calculator, and push them.
        """
        if col == self.COL_AMOUNT:
            amount = sum((t.Amount for t in transactions))
        elif col == self.COL_TOTAL:
            # Use the last total, if multiple are selected.
            amount = transactions[-1]._Total
        else:
            raise Exception("onCalculatorAction should only be called with COL_AMOUNT or COL_TOTAL")

        pushStr = ('C%s', '+%s=', '-%s=')[i] # Send, Add, Subtract commands
        pushStr %= amount

        Publisher.sendMessage("CALCULATOR.PUSH_CHARS", pushStr)

    def onRemoveTransactions(self, transactions):
        """Remove the transactions from the account."""
        self.CurrentAccount.RemoveTransactions(transactions)

    def onMoveTransactions(self, transactions, targetAccount):
        """Move the transactions to the target account."""
        self.CurrentAccount.MoveTransactions(transactions, targetAccount)

    def frozenResize(self):
        self.Parent.Layout()
        self.Parent.Thaw()

    def onTransactionsRemoved(self, message):
        account, transactions = message.data
        if account is self.CurrentAccount:
            # Remove the item from the list.
            self.RemoveObjects(transactions)
            self.updateTotals()
            
    def onTransactionAdded(self, message):
        account, transaction = message.data
        if account is self.CurrentAccount:
            self.AddObject(transaction)
            self.updateTotals()
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

    def __del__(self):
        for callback, topic in self.Subscriptions:
            Publisher.unsubscribe(callback)
