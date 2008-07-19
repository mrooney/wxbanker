#    https://launchpad.net/wxbanker
#    bankcontrols.py: Copyright 2007, 2008 Mike Rooney <wxbanker@rowk.com>
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
import datetime

import pubsub
from banker import str2float, float2str, AccountAlreadyExistsException
from smoothsizer import SmoothStaticBoxSizer

class HyperlinkText(wx.HyperlinkCtrl):
    def __init__(self, parent, id=-1, label='', url='', style=wx.NO_BORDER | wx.HL_ALIGN_CENTRE, onClick=None, *args, **kwargs):
        #by default, disable the right-click "Copy URL" menu
        wx.HyperlinkCtrl.__init__(self, parent, id, label, url, style=style, *args, **kwargs)

        #don't show a different color for previously clicked items
        self.VisitedColour = wx.BLUE

        #bind to the optional callable
        if callable:
            self.Bind(wx.EVT_HYPERLINK, onClick)

    def SetVisited(self, visited):
        print visited


class AccountListCtrl(wx.Panel):
    """
    This control manages a clickable list of accounts,
    displaying their totals to the right of them
    as well as the grand total as the last entry.

    Accounts can be added, removed, and renamed.
    """

    def __init__(self, parent, frame, autoPopulate = True):
        wx.Panel.__init__(self, parent)
        self.parent, self.frame = parent, frame
        #initialize some attributes to their default values
        self.editCtrl = self.hiddenIndex = None
        self.currentIndex = None
        self.boxLabel = "Accounts (%i)"
        self.hyperLinks, self.totalTexts = [], []

        #create the staticboxsizer which is the home for everything
        #this MUST be created first to ensure proper z-ordering (as per docs)
        self.staticBox = wx.StaticBox(self, label=self.boxLabel%0)

        ##create and set up the buttons
        #the ADD account button
        BMP = wx.Bitmap('art/add.bmp')
        BMP.SetMask(wx.Mask(BMP, wx.WHITE))
        self.addButton = addButton = wx.BitmapButton(self, bitmap=BMP)
        addButton.SetToolTipString("Add a new account")
        #the REMOVE account button
        BMP = wx.Bitmap('art/remove.bmp')
        BMP.SetMask(wx.Mask(BMP, wx.WHITE))
        self.removeButton = removeButton = wx.BitmapButton(self, bitmap=BMP)
        removeButton.SetToolTipString("Remove the selected account")
        removeButton.Enabled = False
        #the EDIT account button
        BMP = wx.Bitmap('art/edit.bmp')
        BMP.SetMask(wx.Mask(BMP, wx.WHITE))
        self.editButton = editButton = wx.BitmapButton(self, bitmap=BMP)
        editButton.SetToolTipString("Edit the name of the selected account")
        editButton.Enabled = False

        #layout the buttons
        buttonSizer = wx.BoxSizer()
        buttonSizer.Add(addButton)
        buttonSizer.Add(removeButton)
        buttonSizer.Add(editButton)

        #set up the "Total" sizer
        self.totalText = wx.StaticText(self, label="$0.00")
        self.totalTexts.append(self.totalText)
        miniSizer = wx.BoxSizer()
        miniSizer.Add(wx.StaticText(self, label="Total:"))
        miniSizer.AddStretchSpacer(1)
        miniSizer.Add(self.totalText)

        #the hide zero balance accounts option
        self.hideBox = hideBox = wx.CheckBox(self, label="Hide zero-balance accounts")

        #self.staticBoxSizer = SmoothStaticBoxSizer(self.staticBox, wx.VERTICAL)
        self.staticBoxSizer = wx.StaticBoxSizer(self.staticBox, wx.VERTICAL)
        #self.staticBoxSizer.SetSmooth(False)
        self.staticBoxSizer.Add(buttonSizer, 0, wx.BOTTOM, 5)#, 0, wx.ALIGN_RIGHT)
        self.staticBoxSizer.Add(miniSizer, 0, wx.EXPAND)
        self.staticBoxSizer.Add(hideBox, 0, wx.TOP, 10)

        #set up the button bindings
        addButton.Bind(wx.EVT_BUTTON, self.onAddButton)
        removeButton.Bind(wx.EVT_BUTTON, self.onRemoveButton)
        editButton.Bind(wx.EVT_BUTTON, self.onRenameButton)
        hideBox.Bind(wx.EVT_CHECKBOX, self.onHideCheck)
        #set up the link binding
        self.Bind(wx.EVT_HYPERLINK, self.onAccountClick)

        #subscribe to messages we are concerned about
        pubsub.Publisher().subscribe(self.updateTotals, "NEW TRANSACTION")
        pubsub.Publisher().subscribe(self.updateTotals, "UPDATED TRANSACTION")
        pubsub.Publisher().subscribe(self.updateTotals, "REMOVED TRANSACTION")
        pubsub.Publisher().subscribe(self.onAccountRemoved, "REMOVED ACCOUNT")
        pubsub.Publisher().subscribe(self.onAccountAdded, "NEW ACCOUNT")
        pubsub.Publisher().subscribe(self.onAccountRenamed, "RENAMED ACCOUNT")

        #populate ourselves initially unless explicitly told not to
        if autoPopulate:
            for accountName in frame.bank.getAccountNames():
                self._PutAccount(accountName)

        self.Sizer = self.staticBoxSizer
        #set the minimum size to the amount it needs to display the edit box
        self.Freeze()
        self.showEditCtrl(focus=False)
        minWidth = self.staticBoxSizer.CalcMin()[0]
        self.onHideEditCtrl()
        self.Thaw()
        self.staticBoxSizer.SetMinSize((minWidth, -1))

        #update the checkbox at the end, so everything else is initialized
        hideBox.Value = wx.Config.Get().ReadBool("HIDE_ZERO_BALANCE_ACCOUNTS")
        self.onHideCheck() #setting the value doesn't trigger an event

        #self.Sizer = self.staticBoxSizer
        self.staticBoxSizer.Layout()
        #self.staticBoxSizer.SetSmooth(True)

    def IsVisible(self, index):
        """
        Return whether or not the account at the given
        index is visible.
        """
        if index is None:
            return False

        if index < 0 or index >= self.GetCount():
            raise IndexError, "No element at index %i"%index

        # offset by 1 because the first child is actually the button sizer
        return self.staticBoxSizer.GetItem(index+1).IsShown()

    def SelectItem(self, index):
        """
        Given an index (zero-based), select the
        appropriate account.
        """
        #return the old ctrl to an "unselected" state
        if self.currentIndex is not None:
            self.UnhighlightItem(self.currentIndex)

        if index is not None:
            #set this as "selected"
            linkCtrl = self.hyperLinks[index]
            linkCtrl.Visited = False
            self.HighlightItem(index)
            account = linkCtrl.Label[:-1]
        else:
            account = None

        self.currentIndex = index
        #update the remove/edit buttons
        self.removeButton.Enabled = index is not None
        self.editButton.Enabled = index is not None

        #tell the parent we changed
        pubsub.Publisher().sendMessage("VIEW.ACCOUNT_CHANGED", account)

    def SelectVisibleItem(self, index):
        """
        Given an index (zero-based), select the
        visible account at that index.
        """
        visibleItems = -1
        for i in range(self.GetCount()):
            if self.IsVisible(i):
                visibleItems += 1

                if index == visibleItems:
                    self.SelectItem(i)
                    return
        else: # if we didn't break (or return)
            self.SelectItem(None)

    def SelectItemByName(self, name):
        for i, label in enumerate(self.GetAccounts()):
            if label == name:
                self.SelectItem(i)

    def HighlightItem(self, index):
        #print "Highlighting", self.hyperLinks[index].Label[:-1]
        self.hyperLinks[index].SetNormalColour(wx.BLACK)

    def UnhighlightItem(self, index):
        #print "Unhighlighting", self.hyperLinks[index].Label[:-1]
        self.hyperLinks[index].SetNormalColour(wx.BLUE)

    def GetCount(self):
        return len(self.hyperLinks)

    def GetAccounts(self):
        return [link.Label[:-1] for link in self.hyperLinks]

    def GetCurrentAccount(self):
        if self.currentIndex is not None:
            return self.GetAccounts()[self.currentIndex]
        else: #not necessary but this is explicit
            return None

    def onAccountRemoved(self, topic, accountName):
        """
        Called when an account is removed from the model.
        """
        index = self.GetAccounts().index(accountName)
        self._RemoveItem(index)

    def _PutAccount(self, accountName):
        index = 0
        for label in self.GetAccounts():
            if accountName < label:
                break
            index += 1

        self._InsertItem(index, accountName)
        return index

    def _InsertItem(self, index, item):
        """
        Insert an item (by account name) into the given position.

        This assumes the account already exists in the database.
        """
        accountName = item
        balance = self.frame.bank.getBalanceOf(accountName)

        #create the controls
        link = HyperlinkText(self, label=accountName+":", url=str(index))
        totalText = wx.StaticText(self, label=float2str(balance))
        self.hyperLinks.insert(index, link)
        self.totalTexts.insert(index, totalText)

        #put them in an hsizer
        miniSizer = wx.BoxSizer()
        miniSizer.Add(link)
        miniSizer.AddStretchSpacer(1)
        miniSizer.Add(totalText, 0, wx.LEFT, 10)

        #and insert the hsizer into the correct position in the list
        self.staticBoxSizer.Insert(index+1, miniSizer, 0, wx.EXPAND|wx.BOTTOM, 3)

        #renumber the links after this
        for linkCtrl in self.hyperLinks[index+1:]:
            linkCtrl.URL = str( int(linkCtrl.URL)+1 )
        if self.currentIndex >= index:
            self.currentIndex += 1

        #update the total text, as sometimes the account already exists
        total = str2float(self.totalText.Label)
        self.totalText.Label = float2str(total + balance)

        #update the static label
        self.staticBox.Label = self.boxLabel % self.GetCount()

        self.Layout()
        self.parent.Layout()

    def _RemoveItem(self, index, fixSel=True):
        linkCtrl = self.hyperLinks[index]
        removedAccount = linkCtrl.Label[:-1]

        balance = str2float(self.totalTexts[index].Label)

        del self.hyperLinks[index]
        del self.totalTexts[index]

        #renumber the links after this
        for linkCtrl in self.hyperLinks[index:]:
            linkCtrl.URL = str( int(linkCtrl.URL)-1 )

        #actually remove (sort of) the account sizer
        self.Sizer.Hide(index+1)
        self.Sizer.Detach(index+1)

        #handle selection logic
        if fixSel:
            if self.currentIndex >= self.GetCount():
                # select the first one, if there is at least one
                if self.GetCount() > 0:
                    self.currentIndex = 0
                # otherwise, select None, as there are no accounts
                else:
                    self.currentIndex = None
            self.SelectVisibleItem(self.currentIndex)

        #update the total text (subtract what was removed)
        total = str2float(self.totalText.Label)
        self.totalText.Label = float2str(total - balance)

        #update the static label
        self.staticBox.Label = self.boxLabel % self.GetCount()

        self.Layout()
        self.parent.Layout()

    def updateTotals(self, message=None, data=None):
        """
        Update all the total strings.
        """
        total = 0.0
        for linkCtrl, text in zip(self.hyperLinks, self.totalTexts):
            accountName = linkCtrl.Label[:-1]
            balance = self.frame.bank.getBalanceOf(accountName)
            text.Label = float2str(balance)
            total += balance
        self.totalTexts[-1].Label = float2str(total)

        self.onHideCheck() #if a zero-balance account went to non-zero or vice-versa

        self.Layout()
        self.parent.Layout()

    def onAddButton(self, event):
        self.showEditCtrl()
        self.addButton.Enabled = False

    def onAddAccount(self, event):
        #grab the account name and add it
        accountName = self.editCtrl.Value
        try:
            self.frame.bank.createAccount(accountName)
        except AccountAlreadyExistsException:
            wx.TipWindow(self, "Sorry, an account by that name already exists.")#, maxLength=200)

    def onAccountAdded(self, topic, accountName):
        """
        Called when a new account is created in the model.
        """
        self.onHideEditCtrl() #ASSUMPTION!
        self._PutAccount(accountName)
        self.SelectItemByName(accountName)

    def showEditCtrl(self, pos=-1, focus=True):
        if self.editCtrl:
            self.editCtrl.Value = ''
            self.editCtrl.Show()
        else:
            self.editCtrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
            self.editCtrl.Bind(wx.EVT_KILL_FOCUS, self.onHideEditCtrl)

        if pos == -1:
            pos = self.GetCount()+1
            self.editCtrl.Bind(wx.EVT_TEXT_ENTER, self.onAddAccount)
        else:
            self.editCtrl.Value = self.GetAccounts()[pos]
            self.editCtrl.SetSelection(-1, -1)
            pos += 1
            self.Sizer.Hide(pos)
            self.hiddenIndex = pos
            self.editCtrl.Bind(wx.EVT_TEXT_ENTER, self.onRenameAccount)

        self.Sizer.Insert(pos, self.editCtrl, 0, wx.EXPAND)#, smooth=True)
        self.parent.Layout()

        if focus:
            self.editCtrl.SetFocus()

    def onHideEditCtrl(self, event=None, restore=True):
        #hide and remove the control and re-layout
        self.staticBoxSizer.Hide(self.editCtrl)#, smooth=True)
        self.staticBoxSizer.Detach(self.editCtrl)

        #if it was a rename, we have to re-show the linkctrl
        if restore and self.hiddenIndex is not None:
            self.Sizer.Show(self.hiddenIndex)
            self.hiddenIndex = None

        self.parent.Layout()

        #re-enable the add button
        self.addButton.Enabled = True

    def onRemoveButton(self, event):
        if self.currentIndex is not None:
            linkCtrl = self.hyperLinks[self.currentIndex]
            warningMsg = "This will permanently remove the account '%s' and all its transactions. Continue?"
            dlg = wx.MessageDialog(self, warningMsg%linkCtrl.Label[:-1], "Warning", style=wx.YES_NO|wx.ICON_EXCLAMATION)
            if dlg.ShowModal() == wx.ID_YES:
                #remove it from the bank
                accountName = linkCtrl.Label[:-1]
                self.frame.bank.removeAccount(accountName)

    def onRenameButton(self, event):
        if self.currentIndex is not None:
            self.showEditCtrl(self.currentIndex)

    def onRenameAccount(self, event):
        oldName = self.GetAccounts()[self.currentIndex]
        newName = self.editCtrl.Value

        if oldName == newName:
            #if there was no change, don't do anything
            self.onHideEditCtrl()
            return

        try:
            self.frame.bank.renameAccount(oldName, newName)
        except AccountAlreadyExistsException:
            #wx.MessageDialog(self, 'An account by that name already exists', 'Error :[', wx.OK | wx.ICON_ERROR).ShowModal()
            wx.TipWindow(self, "Sorry, an account by that name already exists.")#, maxLength=200)

    def onAccountRenamed(self, topic, (oldName, newName)):
        """
        Called when an account has been renamed in the model.
        """
        #hide the edit control
        self.onHideEditCtrl(restore=False) #ASSUMPTION!
        #just renaming won't put it in the right alpha position
        self.UnhighlightItem(self.currentIndex)
        self._RemoveItem(self.currentIndex, fixSel=False)
        self.currentIndex = self._PutAccount(newName)
        self.HighlightItem(self.currentIndex)

    def onAccountClick(self, event):
        """
        This method is called when the current account has
        been changed by clicking on an account name.
        """
        self.SelectItem(int(event.URL))

    def onHideCheck(self, event=None):
        """
        This method is called when the user checks/unchecks
        the option to hide zero-balance accounts.
        """
        checked = self.hideBox.IsChecked()
        for i, amountCtrl in enumerate(self.totalTexts):
            # show it, in the case of calls from updateTotals where a zero-balance
            # became a non-zero. otherwise it won't come up.
            # +1 offset is to take into account the buttons at the top.
            self.staticBoxSizer.Show(i+1)
            if checked:
                if str2float(amountCtrl.Label) == 0:
                    self.staticBoxSizer.Hide(i+1)

        self.parent.Layout()

        #we hid the current selection, so select the first available
        if checked and not self.IsVisible(self.currentIndex):
            self.SelectVisibleItem(0)

        wx.Config.Get().WriteBool("HIDE_ZERO_BALANCE_ACCOUNTS", checked)


class NewTransactionCtrl(wx.Panel):
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.frame = frame

        #the add button
        BMP = wx.Bitmap('art/add.bmp')
        BMP.SetMask(wx.Mask(BMP, wx.WHITE))
        self.newButton = newButton = wx.BitmapButton(self, bitmap=BMP)
        newButton.SetToolTipString("Enter this transaction")
        #the date, description, and total
        self.dateCtrl = dateCtrl = wx.DatePickerCtrl(self, style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY)
        dateCtrl.SetMinSize(dateCtrl.GetBestSize())
        self.descCtrl = descCtrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.amountCtrl = amountCtrl = wx.TextCtrl(self, size=(70, -1), style=wx.TE_PROCESS_ENTER)
        #the transfer option
        self.transferCheck = transferCheck = wx.CheckBox(self, label="Transfer")

        #set up the layout
        self.mainSizer = mainSizer = wx.BoxSizer()
        mainSizer.Add(wx.StaticText(self, label="New transaction: "), 0, wx.ALIGN_CENTER_VERTICAL)
        mainSizer.Add(dateCtrl, 0, wx.ALIGN_CENTER_VERTICAL)
        mainSizer.Add(wx.StaticText(self, label="Description:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
        mainSizer.Add(descCtrl)
        mainSizer.Add(wx.StaticText(self, label="Amount:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
        mainSizer.Add(amountCtrl)
        mainSizer.Add(newButton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        mainSizer.Add(transferCheck, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
        mainSizer.Add(wx.StaticText(self, label="("), 0, wx.ALIGN_CENTER_VERTICAL)
        mainSizer.Add(HyperlinkText(self, label="?", onClick=self.onTransferTip), 0, wx.ALIGN_CENTER_VERTICAL)
        mainSizer.Add(wx.StaticText(self, label=")"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.Sizer = mainSizer
        mainSizer.Layout()
        #mainSizer.SetMinSize(mainSizer.Size)

        #initialize some bindings
        self.Bind(wx.EVT_BUTTON, self.onNewTransaction, source=newButton)
        self.Bind(wx.EVT_TEXT_ENTER, self.onNewTransaction)

    def getValues(self):
        #first ensure an account is selected
        account = self.parent.parent.getCurrentAccount()
        if account is None:
            dlg = wx.MessageDialog(self,
                                "Please select an account and then try again.",
                                "No account selected", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return

        #now grab the values we will need
        date = self.dateCtrl.Value
        desc = self.descCtrl.Value
        amount = self.amountCtrl.Value

        #parse the amount
        try:
            amount = float(amount)
        except:
            dlg = wx.MessageDialog(self,
                                "Invalid amount. Please enter an amount such as 12.34",
                                "Error parsing amount", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return

        #parse the date. this is already validated so we are pretty safe
        date = datetime.date(date.Year, date.Month+1, date.Day)

        return account, amount, desc, date

    def getSourceAccount(self, destination):
        otherAccounts = self.frame.bank.getAccountNames()
        otherAccounts.remove(destination)

        #create a dialog with the other account names to choose from
        dlg = wx.SingleChoiceDialog(self,
                'Which account will the money come from?', 'Other accounts',
                otherAccounts, wx.CHOICEDLG_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            return dlg.GetStringSelection()

    def onNewTransaction(self, event):
        result = self.getValues()
        if result is None:
            return

        account, amount, desc, date = result

        isTransfer = self.transferCheck.Value
        if isTransfer:
            destination = account
            source = self.getSourceAccount(destination)
            if source is not None:
                self.frame.bank.makeTransfer(source, destination, amount, desc, date)
                self.onSuccess()
        else:
            self.frame.bank.makeTransaction(account, amount, desc, date)
            self.onSuccess()

    def onTransferTip(self, event):
        tipStr = "If this box is checked when adding a transaction, you will be prompted for the account to use as the source of the transfer.\n\n"+\
                 "For example, checking this box and entering a transaction of $50 into this account will also subtract $50 from the account that you choose as the source."
        wx.TipWindow(self, tipStr, maxLength=200)

    def onSuccess(self):
        #reset the controls
        self.descCtrl.Value = ''
        self.amountCtrl.Value = ''
