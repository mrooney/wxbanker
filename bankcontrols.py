#    https://launchpad.net/wxbanker
#    bankcontrols.py: Copyright 2007, 2008 Mike Rooney <michael@wxbanker.org>
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

import datetime
import wx
from wx.lib.pubsub import Publisher

from banker import AccountAlreadyExistsException, Bank
from smoothsizer import SmoothStaticBoxSizer
import localization


class HyperlinkText(wx.HyperlinkCtrl):
    def __init__(self, parent, id=-1, label='', url='', style=wx.NO_BORDER | wx.HL_ALIGN_CENTRE, onClick=None, *args, **kwargs):
        # By default, disable the right-click "Copy URL" menu.
        wx.HyperlinkCtrl.__init__(self, parent, id, label, url, style=style, *args, **kwargs)

        # Don't show a different color for previously clicked items.
        self.VisitedColour = wx.BLUE

        # Bind to the optional callable.
        if callable:
            self.Bind(wx.EVT_HYPERLINK, onClick)

    def SetVisited(self, visited):
        print visited


class SearchCtrl(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.searchCtrl = wx.SearchCtrl(self, value="", size=(200, -1), style=wx.TE_PROCESS_ENTER)
        self.searchCtrl.SetCancelBitmap(wx.ArtProvider.GetBitmap('wxART_cancel'))
        self.searchCtrl.ShowCancelButton(True)
        self.searchCtrl.ShowSearchButton(False)
        self.searchCtrl.DescriptiveText = _("Search transactions")

        self.searchInChoices = [_("Current Account"), _("All Accounts")]
        self.searchInBox = CompactableComboBox(self, value=self.searchInChoices[0], choices=self.searchInChoices, style=wx.CB_READONLY)

        # The More/Less button.
        self.moreButton = MultiStateButton(self, baseLabel="%s "+_("Options"), labelDict={True: _("More"), False: _("Less")}, state=True)

        self.matchChoices = [_("Amount"), _("Description"), _("Date")]
        self.matchBox = CompactableComboBox(self, value=self.matchChoices[1], choices=self.matchChoices, style=wx.CB_READONLY)

        self.caseCheck = wx.CheckBox(self, label=_("Case Sensitive"))
        self.caseCheck.SetToolTipString(_("Whether or not to match based on capitalization"))

        topSizer = wx.BoxSizer()
        #self.Sizer.Add(wx.StaticText(self, label="Search: "))
        topSizer.Add(self.searchCtrl, 0, wx.ALIGN_CENTER_VERTICAL)
        topSizer.AddSpacer(10)
        topSizer.Add(wx.StaticText(self, label=_("In: ")), 0, wx.ALIGN_CENTER_VERTICAL)
        topSizer.Add(self.searchInBox, 0, wx.ALIGN_CENTER_VERTICAL)
        topSizer.AddSpacer(10)
        topSizer.Add(self.moreButton, 0, wx.ALIGN_CENTER_VERTICAL)

        self.moreSizer = moreSizer = wx.BoxSizer()
        moreSizer.Add(wx.StaticText(self, label=_("Match: ")), 0, wx.ALIGN_CENTER_VERTICAL)
        moreSizer.Add(self.matchBox, 0, wx.ALIGN_CENTER_VERTICAL)
        moreSizer.AddSpacer(5)
        moreSizer.Add(self.caseCheck, 0, wx.ALIGN_CENTER_VERTICAL)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(topSizer, 0, wx.ALIGN_CENTER)
        self.Sizer.Add(moreSizer, 0, wx.ALIGN_CENTER)
        self.searchInBox.Compact()
        self.matchBox.Compact()
        self.Layout()

        #self.matchBox.Bind(wx.EVT_COMBOBOX, self.onMatchCombo)
        self.searchCtrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.onCancel)
        #self.searchCtrl.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.onSearch)
        self.searchCtrl.Bind(wx.EVT_TEXT_ENTER, self.onSearch)
        self.moreButton.Bind(wx.EVT_BUTTON, self.onToggleMore)

        # Initially hide the extra search options.
        self.onToggleMore()

    def onSearch(self, event):
        # TODO: sort by [Amount, Description, Date]
        # TODO: order [Ascending, Descending]
        #X TODO: case sensitivity checkbox
        #X TODO: checkboxes for defining what to search in (currently just desc)
        # TODO: enable search button in ctrl and appropriate event handling
        #X TODO: properly handle the state of everything during a search!
        searchString = event.String # For a date, should be YYYY-MM-DD.
        accountScope = self.searchInChoices.index(self.searchInBox.Value)
        matchType = self.matchChoices.index(self.matchBox.Value)
        caseSens = self.caseCheck.Value

        searchInfo = (searchString, accountScope, matchType, caseSens)
        Publisher().sendMessage("SEARCH.INITIATED", searchInfo)

    def onCancel(self, event):
        self.searchCtrl.Value = ""
        Publisher().sendMessage("SEARCH.CANCELLED")
        #event.Skip()

    def onToggleMore(self, event=None):
        # Show or hide the advanced search options.
        showLess = self.Sizer.IsShown(self.moreSizer)
        self.Sizer.Show(self.moreSizer, not showLess)

        # Update appropriate strings.
        self.moreButton.State = showLess
        tipActionStr = {True: _("Show"), False: _("Hide")}[showLess]
        self.moreButton.SetToolTipString(_("%s advanced search options") % tipActionStr)

        # Give or take the appropriate amount of space.
        self.Parent.Layout()
        Publisher().sendMessage("SEARCH.MORETOGGLED")


class AccountListCtrl(wx.Panel):
    """
    This control manages a clickable list of accounts,
    displaying their totals to the right of them
    as well as the grand total as the last entry.

    Accounts can be added, removed, and renamed.
    """

    def __init__(self, parent, autoPopulate = True):
        wx.Panel.__init__(self, parent)
        # Initialize some attributes to their default values.
        self.editCtrl = self.hiddenIndex = None
        self.currentIndex = None
        self.boxLabel = _("Accounts") + " (%i)"
        self.hyperLinks, self.totalTexts, self.totalVals = [], [], []

        # Create the staticboxsizer which is the home for everything.
        # This *MUST* be created first to ensure proper z-ordering (as per docs).
        self.staticBox = wx.StaticBox(self, label=self.boxLabel%0)
        
        # Create a single panel to be the "child" of the static box sizer,
        # to work around a wxPython regression that prevents tooltips. lp: xxxxxx
        self.childPanel = wx.Panel(self)
        self.childSizer = childSizer = wx.BoxSizer(wx.VERTICAL)

        ## Create and set up the buttons.
        # The EDIT account button.
        BMP = wx.ArtProvider.GetBitmap('wxART_add')
        self.addButton = addButton = wx.BitmapButton(self.childPanel, bitmap=BMP)
        addButton.SetToolTipString(_("Add a new account"))
        # The REMOVE account button.
        BMP = wx.ArtProvider.GetBitmap('wxART_delete')
        self.removeButton = removeButton = wx.BitmapButton(self.childPanel, bitmap=BMP)
        removeButton.SetToolTipString(_("Remove the selected account"))
        removeButton.Enabled = False
        # The EDIT account button.
        BMP = wx.ArtProvider.GetBitmap('wxART_textfield_rename')
        self.editButton = editButton = wx.BitmapButton(self.childPanel, bitmap=BMP)
        editButton.SetToolTipString(_("Rename the selected account"))
        editButton.Enabled = False
        # The CONFIGURE account button.
        BMP = wx.ArtProvider.GetBitmap('wxART_cog')
        self.configureButton = configureButton = wx.BitmapButton(self.childPanel, bitmap=BMP)
        configureButton.SetToolTipString(_("Configure the selected account"))
        configureButton.Enabled = False
        configureButton.Hide()
        
        # Layout the buttons.
        buttonSizer = wx.BoxSizer()
        buttonSizer.Add(addButton)
        buttonSizer.Add(removeButton)
        buttonSizer.Add(editButton)
        buttonSizer.Add(configureButton)

        # Set up the "Total" sizer.
        self.totalText = wx.StaticText(self.childPanel, label="$0.00")
        self.totalTexts.append(self.totalText)
        self.totalVals.append(0)
        miniSizer = wx.BoxSizer()
        miniSizer.Add(wx.StaticText(self.childPanel, label=_("Total")+":"))
        miniSizer.AddStretchSpacer(1)
        miniSizer.Add(self.totalText)

        # The hide zero-balance accounts option.
        self.hideBox = hideBox = wx.CheckBox(self.childPanel, label=_("Hide zero-balance accounts"))
        hideBox.SetToolTipString(_("When enabled, accounts with a balance of $0.00 will be hidden from the list"))

        self.staticBoxSizer = wx.StaticBoxSizer(self.staticBox, wx.VERTICAL)
        #self.staticBoxSizer.SetSmooth(False)
        childSizer.Add(buttonSizer, 0, wx.BOTTOM, 5)#, 0, wx.ALIGN_RIGHT)
        childSizer.Add(miniSizer, 0, wx.EXPAND)
        childSizer.Add(hideBox, 0, wx.TOP, 10)
        self.childPanel.Sizer = childSizer
        self.staticBoxSizer.Add(self.childPanel, 1, wx.EXPAND)

        # Set up the button bindings.
        addButton.Bind(wx.EVT_BUTTON, self.onAddButton)
        removeButton.Bind(wx.EVT_BUTTON, self.onRemoveButton)
        editButton.Bind(wx.EVT_BUTTON, self.onRenameButton)
        hideBox.Bind(wx.EVT_CHECKBOX, self.onHideCheck)
        # Set up the link binding.
        self.Bind(wx.EVT_HYPERLINK, self.onAccountClick)

        # Subscribe to messages we are concerned about.
        Publisher().subscribe(self.updateTotals, "NEW TRANSACTION")
        Publisher().subscribe(self.updateTotals, "UPDATED TRANSACTION")
        Publisher().subscribe(self.updateTotals, "REMOVED TRANSACTION")
        Publisher().subscribe(self.onAccountRemoved, "REMOVED ACCOUNT")
        Publisher().subscribe(self.onAccountAdded, "NEW ACCOUNT")
        Publisher().subscribe(self.onAccountRenamed, "RENAMED ACCOUNT")
        Publisher().subscribe(self.onCurrencyChanged, "model.currency_changed")

        # Populate ourselves initially unless explicitly told not to.
        if autoPopulate:
            for accountName in Bank().getAccountNames():
                self._PutAccount(accountName)

        self.Sizer = self.staticBoxSizer
        # Set the minimum size to the amount it needs to display the edit box.
        self.Freeze()
        self.showEditCtrl(focus=False)
        minWidth = self.staticBoxSizer.CalcMin()[0]
        self.onHideEditCtrl()
        self.Thaw()
        self.staticBoxSizer.SetMinSize((minWidth, -1))

        # Update the checkbox at the end, so everything else is initialized.
        hideBox.Value = wx.Config.Get().ReadBool("HIDE_ZERO_BALANCE_ACCOUNTS")
        # Setting the value doesn't trigger an event, so force an update.
        self.onHideCheck()

        self.staticBoxSizer.Layout()
        #self.staticBoxSizer.SetSmooth(True)
        
    def onCurrencyChanged(self, message):
        for i, textCtrl in enumerate(self.totalTexts):
            balance = self.totalVals[i]
            textCtrl.Label = Bank().float2str(balance)
        self.Parent.Layout()

    def IsVisible(self, index):
        """
        Return whether or not the account at the given
        index is visible.
        """
        if index is None:
            return False

        if index < 0 or index >= self.GetCount():
            raise IndexError, "No element at index %i"%index

        # Offset by 1 because the first child is actually the button sizer.
        return self.childSizer.GetItem(index+1).IsShown()

    def SelectItem(self, index):
        """
        Given an index (zero-based), select the
        appropriate account.
        """
        # Return the old ctrl to an "unselected" state.
        if self.currentIndex is not None:
            self.UnhighlightItem(self.currentIndex)

        if index is not None:
            # Set this as "selected".
            linkCtrl = self.hyperLinks[index]
            linkCtrl.Visited = False
            self.HighlightItem(index)
            account = linkCtrl.Label[:-1]
        else:
            account = None

        self.currentIndex = index
        # Update the remove/edit buttons.
        self.removeButton.Enabled = index is not None
        self.editButton.Enabled = index is not None
        self.configureButton.Enabled = index is not None

        # Tell the parent we changed.
        Publisher().sendMessage("VIEW.ACCOUNT_CHANGED", account)

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
        else: # If we didn't break (or return).
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
        else: # Not necessary, but explicit is clearer here.
            return None

    def onAccountRemoved(self, message):
        """
        Called when an account is removed from the model.
        """
        accountName = message.data
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
        balance = Bank().getBalanceOf(accountName)
        self.totalVals[-1] += balance

        # Create the controls.
        link = HyperlinkText(self.childPanel, label=accountName+":", url=str(index))
        totalText = wx.StaticText(self.childPanel, label=Bank().float2str(balance))
        self.hyperLinks.insert(index, link)
        self.totalTexts.insert(index, totalText)
        self.totalVals.insert(index, balance)

        # Put them in an hsizer.
        miniSizer = wx.BoxSizer()
        miniSizer.Add(link)
        miniSizer.AddStretchSpacer(1)
        miniSizer.Add(totalText, 0, wx.LEFT, 10)

        # Insert the hsizer into the correct position in the list.
        self.childSizer.Insert(index+1, miniSizer, 0, wx.EXPAND|wx.BOTTOM, 3)

        # Renumber the links after this.
        for linkCtrl in self.hyperLinks[index+1:]:
            linkCtrl.URL = str( int(linkCtrl.URL)+1 )
        if self.currentIndex >= index:
            self.currentIndex += 1

        # Update the total text, as sometimes the account already exists.
        self.totalText.Label = Bank().float2str(self.totalVals[-1])

        # Update the static label.
        self.staticBox.Label = self.boxLabel % self.GetCount()

        self.Layout()
        self.Parent.Layout()

    def _RemoveItem(self, index, fixSel=True):
        linkCtrl = self.hyperLinks[index]
        removedAccount = linkCtrl.Label[:-1]

        # Subtract the balance from the total.
        self.totalVals[-1] -= self.totalVals[index]

        del self.hyperLinks[index]
        del self.totalTexts[index]
        del self.totalVals[index]

        # Renumber the links after this.
        for linkCtrl in self.hyperLinks[index:]:
            linkCtrl.URL = str( int(linkCtrl.URL)-1 )

        # Actually remove (sort of) the account sizer.
        self.childSizer.Hide(index+1)
        self.childSizer.Detach(index+1)

        # Handle selection logic.
        if fixSel:
            if self.currentIndex >= self.GetCount():
                # Select the first one, if there is at least one.
                if self.GetCount() > 0:
                    self.currentIndex = 0
                # Otherwise, select None, as there are no accounts.
                else:
                    self.currentIndex = None
            self.SelectVisibleItem(self.currentIndex)

        # Update the total text (subtract what was removed).
        self.totalText.Label = Bank().float2str(self.totalVals[-1])

        # Update the static label.
        self.staticBox.Label = self.boxLabel % self.GetCount()

        self.Layout()
        self.Parent.Layout()

    def updateTotals(self, message=None):
        """
        Update all the total strings.
        """
        total = 0.0
        self.totalVals = []
        for linkCtrl, text in zip(self.hyperLinks, self.totalTexts):
            accountName = linkCtrl.Label[:-1]
            balance = Bank().getBalanceOf(accountName)
            text.Label = Bank().float2str(balance)
            self.totalVals.append(balance)
            total += balance
        self.totalTexts[-1].Label = Bank().float2str(total)
        self.totalVals.append(total)

        # Handle a zero-balance account going to non-zero or vice-versa.
        self.onHideCheck()

        self.Layout()
        self.Parent.Layout()

    def onAddButton(self, event):
        self.showEditCtrl()
        self.addButton.Enabled = False

    def onAddAccount(self, event):
        # Grab the account name and add it.
        accountName = self.editCtrl.Value
        try:
            Bank().createAccount(accountName)
        except AccountAlreadyExistsException:
            wx.TipWindow(self, _("Sorry, an account by that name already exists."))#, maxLength=200)

    def onAccountAdded(self, message):
        """
        Called when a new account is created in the model.
        """
        accountName = message.data
        self.onHideEditCtrl() #ASSUMPTION!
        self._PutAccount(accountName)
        self.SelectItemByName(accountName)

    def showEditCtrl(self, pos=-1, focus=True):
        if self.editCtrl:
            self.editCtrl.Value = ''
            self.editCtrl.Show()
        else:
            self.editCtrl = wx.TextCtrl(self.childPanel, style=wx.TE_PROCESS_ENTER)
            self.editCtrl.Bind(wx.EVT_KILL_FOCUS, self.onHideEditCtrl)

        if pos == -1:
            pos = self.GetCount()+1
            self.editCtrl.Bind(wx.EVT_TEXT_ENTER, self.onAddAccount)
        else:
            self.editCtrl.Value = self.GetAccounts()[pos]
            self.editCtrl.SetSelection(-1, -1)
            pos += 1
            self.childSizer.Hide(pos)
            self.hiddenIndex = pos
            self.editCtrl.Bind(wx.EVT_TEXT_ENTER, self.onRenameAccount)

        self.childSizer.Insert(pos, self.editCtrl, 0, wx.EXPAND)#, smooth=True)
        self.Parent.Layout()

        if focus:
            self.editCtrl.SetFocus()

    def onHideEditCtrl(self, event=None, restore=True):
        # Hide and remove the control and re-layout.
        self.childSizer.Hide(self.editCtrl)#, smooth=True)
        self.childSizer.Detach(self.editCtrl)

        # If it was a rename, we have to re-show the linkctrl.
        if restore and self.hiddenIndex is not None:
            self.childSizer.Show(self.hiddenIndex)
            self.hiddenIndex = None

        self.Parent.Layout()

        # Re-enable the add button.
        self.addButton.Enabled = True

    def onRemoveButton(self, event):
        if self.currentIndex is not None:
            linkCtrl = self.hyperLinks[self.currentIndex]
            warningMsg = _("This will permanently remove the account '%s' and all its transactions. Continue?")
            dlg = wx.MessageDialog(self, warningMsg%linkCtrl.Label[:-1], _("Warning"), style=wx.YES_NO|wx.ICON_EXCLAMATION)
            if dlg.ShowModal() == wx.ID_YES:
                # Remove the account from the model.
                accountName = linkCtrl.Label[:-1]
                Bank().removeAccount(accountName)

    def onRenameButton(self, event):
        if self.currentIndex is not None:
            self.showEditCtrl(self.currentIndex)

    def onRenameAccount(self, event):
        oldName = self.GetAccounts()[self.currentIndex]
        newName = self.editCtrl.Value

        if oldName == newName:
            # If there was no change, don't do anything.
            self.onHideEditCtrl()
            return

        try:
            Bank().renameAccount(oldName, newName)
        except AccountAlreadyExistsException:
            #wx.MessageDialog(self, 'An account by that name already exists', 'Error :[', wx.OK | wx.ICON_ERROR).ShowModal()
            wx.TipWindow(self, _("Sorry, an account by that name already exists."))#, maxLength=200)

    def onAccountRenamed(self, message):
        """
        Called when an account has been renamed in the model.

        TODO: don't assume it was the current account that was renamed.
        """
        oldName, newName = message.data
        # Hide the edit control.
        self.onHideEditCtrl(restore=False) #ASSUMPTION!
        # Just renaming won't put it in the right alpha position, so remove it
        # and add it again, letting _PutAccount handle the ordering.
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
        for i, amountCtrl in enumerate(self.totalTexts[:-1]):
            # Show it, in the case of calls from updateTotals where a
            # zero-balance became a non-zero. otherwise it won't come up.
            # +1 offset is to take into account the buttons at the top.
            self.childSizer.Show(i+1)
            if checked:
                if abs(self.totalVals[i]) < .001:
                    self.childSizer.Hide(i+1)

        self.Parent.Layout()

        # We hid the current selection, so select the first available.
        if checked and not self.IsVisible(self.currentIndex):
            self.SelectVisibleItem(0)

        wx.Config.Get().WriteBool("HIDE_ZERO_BALANCE_ACCOUNTS", checked)


class NewTransactionCtrl(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # The date control. We want the Generic control, which is a composite control
        # and allows us to bind to its enter, but on Windows with wxPython < 2.8.8.0,
        # it won't be available.
        try:
            DatePickerClass = wx.GenericDatePickerCtrl
        except AttributeError:
            DatePickerClass = wx.DatePickerCtrl
        self.dateCtrl = dateCtrl = DatePickerClass(self, style=wx.DP_DROPDOWN|wx.DP_SHOWCENTURY)
        dateCtrl.SetToolTipString(_("Date"))

        # The Description and Amount controls.
        self.descCtrl = descCtrl = HintedTextCtrl(self, size=(140, -1), style=wx.TE_PROCESS_ENTER, hint=_("Description"), icon="wxART_page_edit")
        self.amountCtrl = amountCtrl = HintedTextCtrl(self, size=(90, -1), style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT, hint=_("Amount"), icon="wxART_money_dollar")

        # The add button.
        self.newButton = newButton = wx.BitmapButton(self, bitmap=wx.ArtProvider.GetBitmap('wxART_money_add'))
        newButton.SetToolTipString(_("Enter this transaction"))

        # The transfer check,
        self.transferCheck = transferCheck = wx.CheckBox(self, label=_("Transfer"))

        # Set up the layout.
        #dateCtrl.SetMaxSize((200, 20))
        self.mainSizer = mainSizer = wx.BoxSizer()
        mainSizer.Add(wx.StaticText(self, label=_("Transact")+": "), 0, wx.ALIGN_CENTER)
        mainSizer.AddSpacer(8)
        mainSizer.Add(wx.StaticBitmap(self, bitmap=wx.ArtProvider.GetBitmap('wxART_date')), 0, wx.ALIGN_CENTER|wx.ALL, 2)
        mainSizer.Add(dateCtrl, 0, wx.ALIGN_CENTER)
        mainSizer.AddSpacer(10)
        mainSizer.Add(descCtrl, 0, wx.ALIGN_CENTER)
        mainSizer.AddSpacer(10)
        mainSizer.Add(amountCtrl, 0, wx.ALIGN_CENTER)
        mainSizer.AddSpacer(10)
        mainSizer.Add(newButton, 0, wx.ALIGN_CENTER)
        mainSizer.AddSpacer(10)
        mainSizer.Add(transferCheck, 0, wx.ALIGN_CENTER)
        mainSizer.Add(wx.StaticText(self, label="("), 0, wx.ALIGN_CENTER)
        mainSizer.Add(HyperlinkText(self, label="?", onClick=self.onTransferTip), 0, wx.ALIGN_CENTER)
        mainSizer.Add(wx.StaticText(self, label=")"), 0, wx.ALIGN_CENTER)
        self.Sizer = mainSizer

        # Now layout the control.
        mainSizer.Layout()

        # Initialize necessary bindings.
        self.Bind(wx.EVT_TEXT_ENTER, self.onNewTransaction) # Gives us enter from description/amount.
        self.newButton.Bind(wx.EVT_BUTTON, self.onNewTransaction)
        
        try:
            amountCtrl.Children[0].Bind(wx.EVT_CHAR, self.onAmountChar)
        except IndexError:
            # On OSX for example, a SearchCtrl is native and has no Children.
            pass
        
        try:
            dateTextCtrl = self.dateCtrl.Children[0].Children[0]
        except IndexError:
            # This will fail on MSW + wxPython < 2.8.8.0, nothing we can do.
            print _("Warning: Unable to bind to DateCtrl's ENTER. Upgrade to wxPython >= 2.8.8.1 to fix this.")
        else:
            # Bind to DateCtrl Enter (LP: 252454).
            dateTextCtrl.WindowStyleFlag |= wx.TE_PROCESS_ENTER
            dateTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.onNewTransaction)

    def onAmountChar(self, event):
        wx.CallAfter(self.updateAddIcon)
        event.Skip()

    def updateAddIcon(self, removeFirst=True):
        amountText = self.amountCtrl.Value
        if amountText and amountText[0] == '-':
            BMP = wx.ArtProvider.GetBitmap('wxART_money_delete')
        else:
            BMP = wx.ArtProvider.GetBitmap('wxART_money_add')

        self.newButton.SetBitmapLabel(BMP)

    def getValues(self):
        # First, ensure an account is selected.
        account = self.Parent.Parent.getCurrentAccount()
        if account is None:
            dlg = wx.MessageDialog(self,
                                _("Please select an account and then try again."),
                                _("No account selected"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return

        # Grab the raw values we will need to parse.
        date = self.dateCtrl.Value
        desc = self.descCtrl.Value
        amount = self.amountCtrl.Value

        # Parse the amount.
        try:
            amount = float(amount)
        except:
            if amount == "":
                baseStr = _("No amount entered in the 'Amount' field.")
            else:
                baseStr = _("'%s' is not a valid amount.") % amount

            dlg = wx.MessageDialog(self,
                                baseStr + " " + _("Please enter a number such as 12.34 or -20."),
                                _("Invalid Transaction Amount"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return

        # Parse the date. This is already validated so we are pretty safe.
        date = datetime.date(date.Year, date.Month+1, date.Day)

        return account, amount, desc, date

    def getSourceAccount(self, destination):
        otherAccounts = Bank().getAccountNames()
        otherAccounts.remove(destination)

        # Create a dialog with the other account names to choose from.
        dlg = wx.SingleChoiceDialog(self,
                _('Which account will the money come from?'), _('Other accounts'),
                otherAccounts, wx.CHOICEDLG_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            return dlg.GetStringSelection()

    def onNewTransaction(self, event):
        result = self.getValues()
        if result is None:
            return

        account, amount, desc, date = result
        isTransfer = self.transferCheck.Value

        # If a search is active, we have to ask the user what they want to do.
        if self.Parent.searchActive:
            actionStr = {True: _("transfer"), False: _("transaction")}[isTransfer]
            ##TRANSLATORS: Example: ...and make this TRANSACTION in "CHECKING ACCOUNT"?
            msg = _('A search is currently active. Would you like to clear the current search and make this %s in "%s"?') % (actionStr, account)
            dlg = wx.MessageDialog(self, msg, _("Clear search?"), style=wx.YES_NO|wx.ICON_WARNING)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                Publisher().sendMessage("SEARCH.CANCELLED")
            else:
                return

        if isTransfer:
            destination = account
            source = self.getSourceAccount(destination)
            if source is not None:
                Bank().makeTransfer(source, destination, amount, desc, date)
                self.onSuccess()
        else:
            Bank().makeTransaction(account, amount, desc, date)
            self.onSuccess()

    def onTransferTip(self, event):
        tipStr = _("If this box is checked when adding a transaction, you will be prompted for the account to use as the source of the transfer.")+"\n\n"+\
                 _("For example, checking this box and entering a transaction of $50 into this account will also subtract $50 from the account that you choose as the source.")
        wx.TipWindow(self, tipStr, maxLength=200)

    def onSuccess(self):
        # Reset the controls.
        self.descCtrl.Value = ''
        self.amountCtrl.Value = ''


class CompactableComboBox(wx.ComboBox):
    def Compact(self):
        # Calculates and sets the minimum width of the ComboBox.
        # Width is based on the width of the longest string.
        # From the ideas of Mike Rooney, Cody Precord, Robin Dunn and Raffaello.
        comboStrings = self.Strings
        if len(comboStrings) == 0:
            self.SetMinSize(wx.DefaultSize)
        else:
            height = self.Size[1]
            maxTextWidth = max([self.Parent.GetTextExtent(s.strip())[0] for s in comboStrings])
            self.SetMinSize((maxTextWidth + height + 8, height))


class MultiStateButton(wx.Button):
    def __init__(self, parent, id=-1, baseLabel="%s", labelDict=None, state=None, style=0):
        wx.Button.__init__(self, parent, id=id, style=style)
        self.BaseLabel = baseLabel
        self._State = state

        if labelDict is None:
            labelDict = {None: ""}
        self.LabelDict = labelDict
        self.State = state

    def GetLabelDict(self):
        return self._LabelDict

    def SetLabelDict(self, ldict):
        self._LabelDict = ldict

        # Calculate the width of the button.
        self.Freeze()
        minWidth, minHeight = self.MinSize
        for modifier in ldict.values():
            self.Label = self.BaseLabel % modifier
            cWidth = self.BestSize[0]
            minWidth = max((minWidth, cWidth))
        self.MinSize = minWidth, minHeight
        # Restore the original State (and Label)
        self.State = self._State
        self.Thaw()

    def GetState(self):
        return self._State

    def SetState(self, state):
        self._State = state
        self.Label = self.BaseLabel % self.LabelDict[state]

    LabelDict = property(GetLabelDict, SetLabelDict)
    State = property(GetState, SetState)


class HintedTextCtrl(wx.SearchCtrl):
    def __init__(self, *args, **kwargs):
        conf = {"hint": "", "icon": None}
        for kw in conf.keys():
            if kw in kwargs:
                conf[kw] = kwargs[kw]
                del kwargs[kw]

        wx.SearchCtrl.__init__(self, *args, **kwargs)
        self.ShowCancelButton(False)

        if conf['icon'] is None:
            self.ShowSearchButton(False)
        else:
            self.SetSearchBitmap(wx.ArtProvider.GetBitmap(conf['icon']))
            self.ShowSearchButton(True)

        self.SetToolTipString(conf['hint'])
        self.SetDescriptiveText(conf['hint'])

        try:
            self.Children[0].Bind(wx.EVT_CHAR, self.onChar)
        except IndexError:
            # On OSX for example, a SearchCtrl is native and has no Children.
            pass

    def onChar(self, event):
        if event.KeyCode == wx.WXK_TAB:
            if event.ShiftDown():
                self.Navigate(wx.NavigationKeyEvent.IsBackward)
            else:
                self.Navigate()
        else:
            event.Skip()