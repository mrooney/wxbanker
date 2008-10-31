#    https://launchpad.net/wxbanker
#    managetab.py: Copyright 2007, 2008 Mike Rooney <wxbanker@rowk.com>
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

import wx, wx.grid as gridlib
import datetime
from banker import Bank
from bankcontrols import AccountListCtrl, NewTransactionCtrl, SearchCtrl
from calculator import CollapsableWidget, SimpleCalculator
from wx.lib.pubsub import Publisher
import localization


class ManagePanel(wx.Panel):
    """
    This panel contains the list of accounts on the left
    and the transaction panel on the right.
    """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        ## Left side, the account list and calculator
        self.leftPanel = leftPanel = wx.Panel(self)
        leftPanel.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.accountCtrl = accountCtrl = AccountListCtrl(leftPanel)
        calcWidget = CollapsableWidget(leftPanel, SimpleCalculator, "Calculator")

        leftPanel.Sizer.Add(accountCtrl, 0, wx.EXPAND)
        leftPanel.Sizer.AddStretchSpacer(1)
        leftPanel.Sizer.Add(calcWidget, 0, wx.EXPAND)

        # Force the calculator widget (and parent) to take on the desired size.
        for widget in [calcWidget.widget, leftPanel]:
            widget.SetMinSize((accountCtrl.BestSize[0], -1))

        ## Right side, the transaction panel:
        self.transactionPanel = transactionPanel = TransactionPanel(self)

        mainSizer = wx.BoxSizer()
        self.Sizer = mainSizer
        mainSizer.Add(leftPanel, 0, wx.EXPAND|wx.ALL, 5)
        mainSizer.Add(transactionPanel, 1, wx.EXPAND|wx.ALL, 0)

        #subscribe to messages that interest us
        Publisher().subscribe(self.onChangeAccount, "VIEW.ACCOUNT_CHANGED")
        Publisher().subscribe(self.onCalculatorToggled, "CALCULATOR.TOGGLED")

        #select the first item by default, if there are any
        #we use a CallLater to allow everything else to finish creation as well,
        #otherwise it won't get scrolled to the bottom initially as it should.
        accountCtrl.SelectVisibleItem(0)

        self.Layout()

        # Ensure the calculator is displayed as desired.
        calcWidget.SetExpanded(wx.Config.Get().ReadBool("SHOW_CALC"))

        wx.CallLater(50, lambda: transactionPanel.transactionGrid.doResize())
        wx.CallLater(50, lambda: transactionPanel.transactionGrid.ensureVisible(-1)) # GTK

    def onCalculatorToggled(self, message):
        """
        Re-layout ourself so the calcWidget always fits properly at the bottom.
        """
        self.leftPanel.Layout()
        shown = message.data == "HIDE" # backwards, HIDE means it is now shown.
        wx.Config.Get().WriteBool("SHOW_CALC", shown)

    def onChangeAccount(self, message):
        self.transactionPanel.setAccount(message.data)

    def getCurrentAccount(self):
        return self.accountCtrl.GetCurrentAccount()


class TransactionPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.searchActive = False

        self.searchCtrl = searchCtrl = SearchCtrl(self)
        self.transactionGrid = transactionGrid = TransactionGrid(self)
        self.newTransCtrl = newTransCtrl = NewTransactionCtrl(self)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(searchCtrl, 0, wx.ALIGN_CENTER_HORIZONTAL)
        mainSizer.Add(transactionGrid, 1, wx.EXPAND)
        mainSizer.Add(newTransCtrl, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 5)

        self.Sizer = mainSizer
        mainSizer.Layout()

        self.Bind(wx.EVT_SIZE, self.transactionGrid.doResize)
        for message in ['NEW ACCOUNT', 'REMOVED ACCOUNT', 'VIEW.ACCOUNT_CHANGED']:
            Publisher().subscribe(self.onSearchInvalidatingChange, message)
        #self.Bind(wx.EVT_MAXIMIZE, self.doResize) # isn't necessary on GTK, what about Windows?

    def setAccount(self, *args, **kwargs):
        self.transactionGrid.setAccount(*args, **kwargs)

    def onSearchInvalidatingChange(self, event):
        """
        Some event has occurred which trumps any active search, so make the
        required changes to state. These events will handle all other logic.
        """
        self.searchActive = False
        #Publisher().sendMessage("SEARCH.CANCELLED")


class MoneyCellRenderer(gridlib.PyGridCellRenderer):
    def __init__(self):
        gridlib.PyGridCellRenderer.__init__(self)

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        dc.SetBackgroundMode(wx.SOLID)
        dc.SetBrush(wx.Brush(attr.GetBackgroundColour(), wx.SOLID))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangleRect(rect)
        dc.SetBackgroundMode(wx.TRANSPARENT)
        dc.SetFont(attr.GetFont())

        value = grid.GetCellValue(row, col)
        if value < 0:
            dc.SetTextForeground("RED")
        else:
            dc.SetTextForeground("BLACK")

        text = Bank().float2str(value)

        #right-align horizontal, center vertical
        w, h = dc.GetTextExtent(text)
        x = rect.x + (rect.width-w) - 1
        y = rect.y + (rect.height-h)/2

        dc.DrawText(text, x, y)

    def GetBestSize(self, grid, attr, dc, row, col):
        dc.SetFont(attr.GetFont())
        w, h = dc.GetTextExtent(Bank().float2str(grid.GetCellValue(row, col)))
        return wx.Size(w, h)

    def Clone(self):
        return MoneyCellRenderer()


class TransactionGrid(gridlib.Grid):
    def __init__(self, parent):
        gridlib.Grid.__init__(self, parent)
        self.changeFrozen = False

        self.CreateGrid(0, 4)

        self.SetRowLabelSize(1)

        self.SetColLabelValue(0, _("Date"))
        self.SetColLabelValue(1, _("Description"))
        self.SetColLabelValue(2, _("Amount"))
        self.SetColLabelValue(3, _("Total"))

        self.Bind(gridlib.EVT_GRID_CELL_CHANGE, self.onCellChange)
        self.Bind(gridlib.EVT_GRID_LABEL_RIGHT_CLICK, self.onCellRightClick)
        self.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.onCellRightClick)

        Publisher().subscribe(self.onTransactionRemoved, "REMOVED TRANSACTION")
        Publisher().subscribe(self.onTransactionAdded, "NEW TRANSACTION")
        #XXX this causes a segfault on amount changes, that's cute
        #Publisher().subscribe(self.onTransactionUpdated, "UPDATED TRANSACTION")
        Publisher().subscribe(self.onSearch, "SEARCH.INITIATED")
        Publisher().subscribe(self.onSearchCancelled, "SEARCH.CANCELLED")
        Publisher().subscribe(self.onSearchMoreToggled, "SEARCH.MORETOGGLED")

    def GetCellValue(self, row, col):
        """
        When we get the values of amount/total columns,
        we want the float values. So just give us them.
        """
        val = gridlib.Grid.GetCellValue(self, row, col)
        if col in [2,3]: #cols 2 and 3 and amount/total
            val = float(val)

        return val

    def SetCellValue(self, row, col, val):
        """
        When we set the values of amount/total columns,
        it expects a string but our values are floats,
        so just cast it for us.
        """
        if col in [2,3]: #cols 2 and 3 and amount/total
            val = str(val)

        return gridlib.Grid.SetCellValue(self, row, col, val)

    def DeleteRows(self, pos=0, numRows=1, updateLabels=True):
        """
        Override the default DeleteRows, which ignores updateLabels, and
        always updates them. For this application, we don't want that, so
        allow that option.
        """
        if not updateLabels:
            # Shift all the following row labels up the appropriate amount, to
            # compensate for the row[s] that are being deleted, so that the row
            # labels still correspond to the same rows that they did before
            # the DeleteRows call.
            self.BeginBatch() # Freeze any future repaints temporarily.
            for i in range( self.GetNumberRows() - (pos + numRows) ):
                self.SetRowLabelValue(pos+i, self.GetRowLabelValue(pos+i+numRows))
            self.EndBatch() # Unfreeze repaints.
        gridlib.Grid.DeleteRows(self, pos, numRows, updateLabels=True)

    def onSearch(self, message):
        searchString, accountScope, match, caseSens = message.data

        if accountScope == 0: # Search in just current account.
            accountName = self.Parent.Parent.getCurrentAccount()
        else: # Search in all accounts.
            accountName = None

        matches = Bank().searchTransactions(searchString, accountName=accountName, matchIndex=match, matchCase=caseSens)
        self.setTransactions(matches)
        self.Parent.searchActive = True

    def onSearchCancelled(self, message):
        self.setAccount(self.Parent.Parent.getCurrentAccount())
        self.Parent.searchActive = False

    def onSearchMoreToggled(self, message):
        self.Refresh()
        #self.doResize()

    def onTransactionAdded(self, message):
        #ASSUMPTION: the transaction was of the current account
        self.setAccount(self.Parent.Parent.getCurrentAccount())

    def onTransactionUpdated(self, message):
        #ASSUMPTION: the transaction was of the current account
        self.setAccount(self.Parent.Parent.getCurrentAccount(), ensureVisible=None)

    def onCellRightClick(self, event):
        row, col = event.Row, event.Col # col == -1 -> row label right click
        if row < 0: # col labels have row of -1, we don't care about them
            return

        menu = wx.Menu()

        if col in (2,3):
            # This is an amount cell, allow calculator options.
            actions = [
                (_("Send to calculator"), "wxART_calculator_edit"),
                (_("Add to calculator"), "wxART_calculator_add"),
                (_("Subtract from calculator"), "wxART_calculator_delete"),
            ]

            for actionStr, artHint in actions:
                item = wx.MenuItem(menu, -1, actionStr)
                item.SetBitmap(wx.ArtProvider.GetBitmap(artHint))
                menu.Bind(wx.EVT_MENU, lambda e, s=actionStr: self.onCalculatorAction(row, col, s), source=item)
                menu.AppendItem(item)
            menu.AppendSeparator()

        # Always show the Remove context entry.
        ID = int(self.GetRowLabelValue(row))
        removeItem = wx.MenuItem(menu, -1, _("Remove this transaction"))
        menu.Bind(wx.EVT_MENU, lambda e: self.onRemoveTransaction(row, ID), source=removeItem)
        removeItem.SetBitmap(wx.ArtProvider.GetBitmap('wxART_delete'))
        menu.AppendItem(removeItem)

        # Show the menu and then destroy it afterwards.
        self.PopupMenu(menu)
        menu.Destroy()

    def onCalculatorAction(self, row, col, actionStr):
        """
        Given an action to perform on the calculator, and the row and col,
        generate the string of characters necessary to perform that action
        in the calculator, and push them.
        """
        command = actionStr.split(' ')[0].upper()
        amount = self.GetCellValue(row, col)

        pushStr = {'SEND': 'C%s', 'SUBTRACT': '-%s=', 'ADD': '+%s='}[command]
        pushStr %= amount

        Publisher.sendMessage("CALCULATOR.PUSH_CHARS", pushStr)

    def onRemoveTransaction(self, row, ID):
        #remove the transaction from the bank
        Bank().removeTransaction(ID)

    def getRowFromID(self, ID):
        for i in range(self.GetNumberRows()):
            if int(self.GetRowLabelValue(i)) == ID:
                return i

    def onTransactionRemoved(self, message):
        ID = message.data
        row = self.getRowFromID(ID)
        if row is not None: # it may not have been from the current account
            # Delete the row from the grid.
            self.DeleteRows(row, updateLabels=False)
            # Update all the rows starting from where it was.
            self.updateRowsFrom(row)
            # Ensure the first cell visible is still the first cell visible.
            #TODO: ^

    def onCellChange(self, event):
        if not self.changeFrozen:
            uid = int(self.GetRowLabelValue(event.Row))
            value = self.GetCellValue(event.Row, event.Col)

            amount = desc = date = None
            refreshNeeded = False
            if event.Col == 0:
                #make a date
                m, d, y = [int(x) for x in value.split('/')]
                date = datetime.date(y, m, d)
                refreshNeeded = True
            elif event.Col == 1:
                #make a desc
                desc = value
            else:
                #make a float
                amount = value
                #update all the totals after and including this one
                self.updateTotalsFrom(event.Row)

            self.changeFrozen = True
            Bank().updateTransaction(uid, amount, desc, date)
            self.changeFrozen = False

            if refreshNeeded and not self.Parent.searchActive:
                #this is needed because otherwise the Grid will put the new value in,
                #even if event.Skip isn't called, for some reason I don't understand.
                #event.Veto() will cause the OLD value to be put in. so it has to be updated
                #after the event handlers (ie this function) finish.
                wx.CallLater(50, lambda: self.setAccount(self.Parent.Parent.getCurrentAccount(), ensureVisible=None))

    def updateRowsFrom(self, startingRow=0):
        """
        This method will ensure everything from startingRow is correct:
          * the alternating background color of the row cells
          * the total column
        """
        self.BeginBatch() # Freeze any future repaints temporarily.
        for i in range(startingRow, self.GetNumberRows()):
            self.colorizeRow(i)
        self.updateTotalsFrom(startingRow)
        self.EndBatch() # Unfreeze repaints.

    def updateTotalsFrom(self, startingRow=0):
        """
        Instead of pulling all the data from the bank, just
        update the totals ourselves, starting at a given row.
        """
        if startingRow == 0:
            total = 0.0
        else:
            total = self.GetCellValue(startingRow-1, 3)

        self.BeginBatch() # Freeze any future repaints temporarily.

        row = startingRow
        lastRow = self.GetNumberRows()-1
        while row <= lastRow:
            amount = self.GetCellValue(row, 2)
            total += amount
            self.SetCellValue(row, 3, total)
            row += 1

        self.EndBatch() # Unfreeze repaints.

    def colorizeRow(self, rowNum):
        cellAttr = gridlib.GridCellAttr()
        if rowNum%2:
            cellAttr.SetBackgroundColour(wx.Color(224,238,238))
        else:
            cellAttr.SetBackgroundColour(wx.WHITE)
        self.SetRowAttr(rowNum, cellAttr)

    def setAccount(self, accountName, ensureVisible=-1):
        if accountName is None:
            numRows = self.GetNumberRows()
            if numRows:
                self.DeleteRows(0, numRows)
            return

        transactions = Bank().getTransactionsFrom(accountName)
        self.setTransactions(transactions, ensureVisible)

    def setTransactions(self, transactions, ensureVisible=-1):
        self.BeginBatch() # Freeze any future repaints temporarily.

        #first, adjust the number of rows in the grid to fit
        rowsNeeded = len(transactions)
        rowsExisting = self.GetNumberRows()
        if rowsNeeded > rowsExisting:
            self.AppendRows(rowsNeeded-rowsExisting)
        elif rowsExisting > rowsNeeded:
            self.DeleteRows(0, rowsExisting-rowsNeeded)

        #now fill in all the values
        total = 0.0
        for i, transaction in enumerate(transactions):
            uid, amount, desc, date = transaction
            total += amount
            self.SetRowLabelValue(i, str(uid))
            self.SetCellValue(i, 0, date.strftime('%m/%d/%Y'))
            self.SetCellValue(i, 1, desc)
            self.SetCellValue(i, 2, amount)
            self.SetCellEditor(i, 2, gridlib.GridCellFloatEditor(precision=2))
            self.SetCellValue(i, 3, total)
            self.SetReadOnly(i, 3, True) #make the total read-only
            for col in range(2):
                self.SetCellAlignment(i, 2+col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
                self.SetCellRenderer(i, 2+col, MoneyCellRenderer())

            #make every other row a different color
            self.colorizeRow(i)

        self.EndBatch() # Unfreeze repaints.

        #resize
        self.doResize()

        #scroll to the last transaction
        if ensureVisible is not None:
            self.ClearSelection()
            self.ensureVisible(ensureVisible)

    def ensureVisible(self, index):
        """
        Make sure that a cell at a given index is shown.
        Negative indexes are allowed for pythonic purposes.
        """
        rows = self.GetNumberRows()
        if not rows:
            return

        if index < 0:
            #allow pythonic negative indexing: -1 for the last, -2 for 2nd last, etc.
            index = rows + index
        self.MakeCellVisible(index, 0)

    def doResize(self, event=None):
        """
        This method is called to resize the grid when the window is resized.
        Basically, it Autosizes all columns and then gives any remaining space
        to the Description column's width.
        """
        # The column which will be expanded.
        expandCol = 1

        # Freeze everything so no changes are made while we do some magic.
        parent = self.Parent
        parent.Freeze()

        # Autosize the columns and layout so we know how big everything wants to be.
        self.AutoSizeColumns()
        parent.Layout()

        # Calculate the total width of the other columns, including the Row Label.
        otherWidths = self.RowLabelSize
        for i in range(self.GetNumberCols()):
            if i != expandCol:
                otherWidths += self.GetColSize(i)

        # Calculate the width of the description (as wide as we can get).
        descWidth = self.Size[0] - otherWidths

        # If there is a vertical scrollbar, allow for that.
        vsbWidth = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
        if self.HasScrollbar(wx.VERTICAL):
            descWidth -= vsbWidth

        # Finally, set the size of the expandable column.
        self.SetColSize(expandCol, descWidth)

        #self.SetVirtualSize((self.Size[0]-vsbWidth, self.Size[1]))

        self.Refresh()
        parent.Thaw()
        parent.Layout()

        if event:
            event.Skip()
