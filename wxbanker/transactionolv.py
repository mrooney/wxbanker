#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    transactionolv.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

import threading
import wx, datetime
from wx.lib.pubsub import Publisher
from wxbanker.ObjectListView import GroupListView, ColumnDefn, CellEditorRegistry
from wxbanker import bankcontrols, tagtransactiondialog

from wxbanker.currencies import GetCurrencyInt

class TransactionOLV(GroupListView):
    EMPTY_MSG_NORMAL = _("No transactions entered.")
    EMPTY_MSG_SEARCH = _("No matching transactions.")
    
    def __init__(self, parent, bankController):
        GroupListView.__init__(self, parent, style=wx.LC_REPORT|wx.SUNKEN_BORDER, name="TransactionOLV")
        self.LastSearch = None
        self.CurrentAccount = None
        self.BankController = bankController
        self.GlobalCurrency = self.BankController.Model.Store.getGlobalCurrency()

        self.showGroups = False
        #WXTODO: figure out these (and the text color, or is that already?) from theme (LP: ???)
        self.evenRowsBackColor = wx.Color(224,238,238)
        self.oddRowsBackColor = wx.WHITE

        self.cellEditMode = GroupListView.CELLEDIT_DOUBLECLICK
        self.SetEmptyListMsg(self.EMPTY_MSG_NORMAL)

        # Calculate the necessary width for the date column.
        dateStr = str(datetime.date.today())
        dateWidth = self.GetTextExtent(dateStr)[0] + 10

        # Define some constants to use throughout.
        self.COL_DATE = 0
        self.COL_DESCRIPTION = 1
        self.COL_AMOUNT = 2
        self.COL_TOTAL = 3

        # If you change these column names, update sizeAmounts()!
        self.SetColumns([
            ColumnDefn(_("Date"), valueGetter=self.getDateAndIDOf, valueSetter=self.setDateOf, stringConverter=self.renderDateIDTuple, editFormatter=self.renderEditDate, width=dateWidth),
            ColumnDefn(_("Description"), valueGetter="Description", isSpaceFilling=True, editFormatter=self.renderEditDescription),
            ColumnDefn(_("Amount"), "right", valueGetter=self.getAmount, valueSetter=self.setAmount, stringConverter=self.renderFloat, editFormatter=self.renderEditFloat),
            ColumnDefn(_("Balance"), "right", valueGetter=self.getTotal, stringConverter=self.renderFloat, isEditable=False),
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
            (self.onShowCurrencyNickToggled, "controller.show_currency_nick_toggled"),
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
        
    def IsSearchActive(self):
        return self.GrandParent.searchActive
    
    def SetSearchActive(self, value):
        self.GrandParent.searchActive = value
        
    def onTransactionDateUpdated(self, message):
        transaction = message.data
        self.RefreshObject(transaction)
        self.SortBy(self.SORT_COL)
        self.updateTotals()

    def getDateAndIDOf(self, transaction):
        # A date and ID two-tuple is used to allow for correct sorting
        # by date (bug #653697)
        return (transaction.Date, transaction.ID)

    def setDateOf(self, transaction, date):
        transaction.Date = date
        self.Freeze()
        self.SortBy(self.SORT_COL)
        self.Thaw()
        
    def setAmount(self, transaction, amount):
        transaction.Amount = amount
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
        
        if not self.CurrentAccount:
            #This means we are in 'All accounts' so we need to convert each total
            # to the global currency
            balance_currency = self.GlobalCurrency
        else:
            #we are just viewing a single account
            # balance currency = accounts currency
            balance_currency = GetCurrencyInt(self.CurrentAccount.GetCurrency())
        
        first._Total = first.GetAmount(balance_currency)
        
        b = first
        for i in range(1, len(self.GetObjects())):
            a, b = b, self.GetObjectAt(i)
            b._Total = a._Total + b.GetAmount(balance_currency)
    
    def renderDateIDTuple(self, pair):
        return str(pair[0])
  
    def getAmount(self, obj):
        #Return the whole transaction/float since we need to use its
        #renderAmount method to support multiple currencies.
        return obj  
        
    def renderFloat(self, value):
        if isinstance(value, float):
            #this is a 'balance' column, its ok to use the bank model's float2str
            # as long as we'r not in an account.
            if self.CurrentAccount:
                return self.CurrentAccount.float2str(value)
            else:
                return self.BankController.Model.float2str(value)
        else:
            #this is a trnasaction, so it belogns to the 'Amount' column, render
            # it with its appropieate currency
            return value.RenderAmount()
    
    def renderEditDate(self, transaction):
        return str(transaction.Date)
    
    def renderEditFloat(self, modelObj):
        return "%.2f" % modelObj.Amount
    
    def renderEditDescription(self, modelObj):
        return modelObj._Description

    def _sizeAmounts(self):
        """Set the width of the Amount and Total columns based on the approximated widest value."""
        transactions = self.GetObjects()
        # If there aren't any transactions, there's nothing to do.
        if len(transactions) == 0:
            return

        for i, attr in enumerate(("Amount", "_Total")):
            # Sort by amount, then compare the highest and lowest, to take into account a negative sign.
            sortedtrans = list(sorted(transactions, cmp=lambda a,b: cmp(getattr(a, attr), getattr(b, attr))))
            high, low = sortedtrans[0], sortedtrans[-1]
            # Get the (translated) displayed column name to calculate width.
            header = _({"_Total": "Balance"}.get(attr, attr))
            # Take the max of the two as well as the column header width, as we need to at least display that.
            widestWidth = max([self.GetTextExtent(header)[0]] + [self.GetTextExtent(self.renderFloat(getattr(t, attr)))[0] for t in (high, low)])
            wx.CallAfter(self.SetColumnFixedWidth, *(self.COL_AMOUNT+i, widestWidth + 10))

    def sizeAmounts(self):
        threading.Thread(target=self._sizeAmounts).start()

    def setAccount(self, account, scrollToBottom=True):
        self.CurrentAccount = account

        if account is None:
            # None represents the "All accounts" option, so we want all transactions.
            transactions = self.BankController.Model.GetTransactions()
        else:
            transactions = account.Transactions

        self.SetObjects(transactions)
        # Update the width of the amount/total columns.
        self.sizeAmounts()
        # Unselect everything.
        self.SelectObjects([], deselectOthers=True)
        if scrollToBottom:
            self.ensureVisible(-1)
            
        if self.IsSearchActive():
            self.doSearch(self.LastSearch)

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
        # This seems unlikely but let's defend against it.
        if not transactions:
            return
        
        menu = wx.Menu()
        
        # removeOnly means only show the remove entry, such as from the CSV import frame.
        if not removeOnly:
            # If the right-click was on the total column, use the total, otherwise the amount.
            if col == self.COL_TOTAL:
                # Use the last total if multiple are selected.
                amount = transactions[-1]._Total
            else:
                amount = sum((t.Amount for t in transactions))
                
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
            tagStr = _("No tags yet")
        else:
            removeStr = _("Remove these %i transactions") % len(transactions)
            moveStr = _("Move these %i transactions to account") % len(transactions)
            tagStr = _("No common tags yet")
            
        addTagStr = _("Add a tag")

        removeItem = wx.MenuItem(menu, -1, removeStr)
        menu.Bind(wx.EVT_MENU, lambda e: self.onRemoveTransactions(transactions), source=removeItem)
        removeItem.SetBitmap(wx.ArtProvider.GetBitmap('wxART_delete'))
        menu.AppendItem(removeItem)

        if not removeOnly:
            # Create the sub-menu of sibling accounts to the move to.
            moveToAccountItem = wx.MenuItem(menu, -1, moveStr)
            accountsMenu = wx.Menu()
            if self.CurrentAccount is None:
                siblings = []
            else:
                siblings = self.CurrentAccount.GetSiblings()
            for account in siblings:
                accountItem = wx.MenuItem(menu, -1, account.GetName())
                accountsMenu.AppendItem(accountItem)
                accountsMenu.Bind(wx.EVT_MENU, lambda e, account=account: self.onMoveTransactions(transactions, account), source=accountItem)
            moveToAccountItem.SetSubMenu(accountsMenu)
            moveMenuItem = menu.AppendItem(moveToAccountItem)
            
            # The tag menu.
            tagsItem = wx.MenuItem(menu, -1, _("Tags"))
            tagsMenu = wx.Menu()

            ## The initial tags are the ones in the first transaction. If there are more, intersect across them.
            commonTags = set(transactions[0].Tags)
            for transaction in transactions[1:]:
                commonTags = commonTags.intersection(transaction.Tags)
                
            ## If we have any common tags, add them to the menu, otherwise the no tags item.
            if commonTags:
                for tag in commonTags:
                    tagItem = wx.MenuItem(tagsMenu, -1, tag.Name)
                    tagItemMenu = wx.Menu()
                    searchItem = tagItemMenu.Append(-1, _("Search for this tag"))
                    removeItem = tagItemMenu.Append(-1, _("Remove this tag"))
                    tagItem.SetSubMenu(tagItemMenu)
                    tagsMenu.AppendItem(tagItem)
                    
                    tagItemMenu.Bind(wx.EVT_MENU, lambda e, tag=tag: self.onTagSearch(tag), source=searchItem)
                    tagItemMenu.Bind(wx.EVT_MENU, lambda e, tag=tag: self.onTagRemoval(tag, transactions), source=removeItem)
            else:
                noTagsItem = tagsMenu.Append(-1, tagStr)
                menu.Enable(noTagsItem.Id, False)
            tagsMenu.AppendSeparator()
            addItem = tagsMenu.Append(-1, addTagStr)
            tagsItem.SetSubMenu(tagsMenu)
            tagsMenu.Bind(wx.EVT_MENU, lambda e: self.onTagTransactions(transactions), source=addItem)
            
            ## Append it at the bottom after a separator.
            menu.AppendSeparator()
            menu.AppendItem(tagsItem)
            
            # If there are no siblings, disable the item, but leave it there for consistency.
            if not siblings:
                menu.Enable(moveMenuItem.Id, False)

        # Show the menu and then destroy it afterwards.
        self.PopupMenu(menu)
        menu.Destroy()

    def onCalculatorAction(self, transactions, col, i):
        """
        Given an action to perform on the calculator, and the row and col,
        generate the string of characters necessary to perform that action
        in the calculator, and push them.
        """
        if col == self.COL_TOTAL:
            # Use the last total if multiple are selected.
            amount = transactions[-1]._Total
        else:
            amount = sum((t.Amount for t in transactions))

        pushStr = ('C%s', '+%s=', '-%s=')[i] # Send, Add, Subtract commands
        pushStr %= amount

        Publisher.sendMessage("CALCULATOR.PUSH_CHARS", pushStr)

    def onRemoveTransactions(self, transactions):
        """Remove the transactions from the account."""
        if self.CurrentAccount:
            self.CurrentAccount.RemoveTransactions(transactions)
        # We won't have a CurrentAccount when viewing all accounts (LP: #620924)
        else:
            for transaction in transactions:
                transaction.Parent.RemoveTransaction(transaction)

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
            self.sizeAmounts()
            
    def onTransactionAdded(self, message):
        account, transaction = message.data
        if account is self.CurrentAccount:
            self.AddObject(transaction)
            self.updateTotals()
            self.Reveal(transaction)
            self.sizeAmounts()

    def onTagSearch(self, tag):
        Publisher.sendMessage("SEARCH.EXTERNAL", str(tag))
        
    def onTagRemoval(self, tag, transactions):
        for transaction in transactions:
            transaction.RemoveTag(tag)
        # The removal won't appear unless we refresh the affected transactions.
        self.RefreshObjects(transactions)
        
    def onTagTransactions(self, transactions):
        dlg = tagtransactiondialog.TagTransactionsDialog(self, transactions)
        dlg.ShowModal()
        # Unconditionally refresh, since hitting enter in the tag field requires a refresh but doesn't provide a useful result.
        self.RefreshObjects(transactions)
        
    def onSearch(self, message):
        self.SetEmptyListMsg(self.EMPTY_MSG_SEARCH)
        self.LastSearch = message.data
        self.doSearch(self.LastSearch)
        
    def doSearch(self, searchData):
        searchString, match = searchData
        account = self.CurrentAccount
        matches = self.BankController.Model.Search(searchString, account=account, matchIndex=match)
        self.SetObjects(matches)
        self.SetSearchActive(True)

    def onSearchCancelled(self, message):
        # Ignore cancels on an inactive search to avoid silly refreshes.
        if self.IsSearchActive():
            self.SetSearchActive(False)
            self.setAccount(self.CurrentAccount)
        self.SetEmptyListMsg(self.EMPTY_MSG_NORMAL)

    def onSearchMoreToggled(self, message):
        # Perhaps necessary to not glitch overlap on Windows?
        self.Refresh()

    def onCurrencyChanged(self, message):
        self.GlobalCurrency = message.data
        # Refresh all the transaction objects, re-rendering the amounts.
        self.RefreshObjects()
        # The current likely changed the widths of the amount/total column.
        self.sizeAmounts()
        # Now we need to adjust the description width so we don't have a horizontal scrollbar.
        self.AutoSizeColumns()
        
    def onShowCurrencyNickToggled(self, message):
        # Refresh all the transaction objects, re-rendering the amounts.
        self.RefreshObjects()
        # The current likely changed the widths of the amount/total column.
        self.sizeAmounts()
        # Now we need to adjust the description width so we don't have a horizontal scrollbar.
        self.AutoSizeColumns()
        
    def __del__(self):
        for callback, topic in self.Subscriptions:
            Publisher.unsubscribe(callback)
