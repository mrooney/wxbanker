#    https://launchpad.net/wxbanker
#    accountlistctrl.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker import bankcontrols, bankexceptions, accountconfigdialog, localization
from wx.lib.pubsub import Publisher


class AccountListCtrl(wx.Panel):
    """
    This control manages a clickable list of accounts,
    displaying their totals to the right of them,
    as well as the grand total as the last entry.

    Accounts can be added, removed, and renamed.
    """

    def __init__(self, parent, bankController, autoPopulate=True):
        wx.Panel.__init__(self, parent, name="AccountListCtrl")
        self.bankController = bankController
        self.Model = bankController.Model

        # Initialize some attributes to their default values.
        self.editCtrl = self.hiddenIndex = None
        self.currentIndex = None
        self.radioButtons, self.totalTexts, self.accountObjects, self.mintStatuses = [], [], [], []

        # Create the staticboxsizer which is the home for everything.
        # This *MUST* be created first to ensure proper z-ordering (as per docs).
        self.staticBox = wx.StaticBox(self, label=_("Accounts"))

        # Create a single panel to be the "child" of the static box sizer,
        # to work around a wxPython regression that prevents tooltips. lp: xxxxxx
        self.childPanel = wx.Panel(self)
        self.childSizer = childSizer = wx.BoxSizer(wx.VERTICAL)

        ## Create and set up the buttons.
        # The ADD account button.
        BMP = self.addBMP = wx.ArtProvider.GetBitmap('wxART_add')
        self.addButton = addButton = bankcontrols.FlashableButton(self.childPanel, bitmap=BMP)
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

        # Layout the buttons.
        buttonSizer = wx.BoxSizer()
        buttonSizer.Add(addButton)
        buttonSizer.AddSpacer(6)
        buttonSizer.Add(editButton)
        buttonSizer.AddSpacer(6)
        buttonSizer.Add(configureButton)
        buttonSizer.AddSpacer(6)
        buttonSizer.Add(removeButton)

        # Set up the "Total" sizer.
        self.totalText = wx.StaticText(self.childPanel, label=self.Model.float2str(0))
        self.totalTexts.append(self.totalText)
        miniSizer = wx.BoxSizer()
        self.allAccountsRadio = wx.RadioButton(self.childPanel, label=_("All accounts"))
        miniSizer.Add(self.allAccountsRadio, 1, wx.ALIGN_CENTER)
        miniSizer.Add(self.totalText, 0, wx.ALIGN_CENTER|wx.LEFT, 10)
        miniSizer.AddSpacer(3)

        #self.staticBoxSizer = SmoothStaticBoxSizer(self.staticBox, wx.VERTICAL)
        self.staticBoxSizer = wx.StaticBoxSizer(self.staticBox, wx.VERTICAL)
        #self.staticBoxSizer.SetSmooth(False)
        childSizer.Add(buttonSizer, 0, wx.BOTTOM, 9)
        # Add just a tiny bit of padding between the accounts and the total item.
        childSizer.AddSpacer(3)
        childSizer.Add(miniSizer, 0, wx.EXPAND)
        self.childPanel.Sizer = childSizer
        self.staticBoxSizer.Add(self.childPanel, 1, wx.EXPAND)

        # Set up the button bindings.
        addButton.Bind(wx.EVT_BUTTON, self.onAddButton)
        removeButton.Bind(wx.EVT_BUTTON, self.onRemoveButton)
        editButton.Bind(wx.EVT_BUTTON, self.onRenameButton)
        configureButton.Bind(wx.EVT_BUTTON, self.onConfigureButton)
        # Set up the link binding.
        self.Bind(wx.EVT_RADIOBUTTON, self.onAccountClick)

        # Subscribe to messages we are concerned about.
        Publisher.subscribe(self.onAccountBalanceChanged, "ormobject.updated.Account.Balance")
        Publisher.subscribe(self.onAccountRenamed, "ormobject.updated.Account.Name")
        Publisher.subscribe(self.onAccountMintIdChanged, "ormobject.updated.Account.MintId")
        Publisher.subscribe(self.onAccountRemoved, "account.removed")
        Publisher.subscribe(self.onAccountAdded, "account.created")
        Publisher.subscribe(self.onCurrencyChanged, "currency_changed")
        Publisher.subscribe(self.onShowZeroToggled, "controller.showzero_toggled")
        Publisher.subscribe(self.onAccountChanged, "user.account changed")
        Publisher.subscribe(self.onSelectNextAccount, "user.next account")
        Publisher.subscribe(self.onSelectPreviousAccount, "user.previous account")
        Publisher.subscribe(self.onToggleMintIntegration, "user.mint.toggled")
        Publisher.subscribe(self.onMintDataUpdated, "mint.updated")

        # Populate ourselves initially unless explicitly told not to.
        if autoPopulate:
            for account in self.Model.Accounts:
                self._PutAccount(account)

        self.Sizer = self.staticBoxSizer
        # Set the minimum size to the amount it needs to display the edit box.
        self.Freeze()
        self.showEditCtrl(focus=False)
        minWidth = max((self.staticBoxSizer.CalcMin()[0], 250))
        self.onHideEditCtrl()
        self.Thaw()
        self.staticBoxSizer.SetMinSize((minWidth, -1))
        
        # Initially load the visibility of zero-balance accounts!
        # Don't refresh the selection or we'll send an account changed message which will overwrite the LastAccountId before it gets used!
        self.refreshVisibility(refreshSelection=False)

        self.staticBoxSizer.Layout()
        #self.staticBoxSizer.SetSmooth(True)

        if not self.GetCount():
            self.addButton.StartFlashing()
            
    def onAccountMintIdChanged(self, message):
        self._UpdateMintStatuses()
        
    def _UpdateMintStatuses(self):
        for account, mintCtrl in zip(self.accountObjects, self.mintStatuses):
            bitmapName = "transparent"
            tooltip = _("Not synchronized with Mint.com")
            if account.IsMintEnabled():
                tooltip = account.GetSyncString()
                if account.IsInSync():
                    bitmapName = "accept"
                else:
                    bitmapName = "exclamation"
            mintCtrl.SetBitmap(wx.ArtProvider.GetBitmap("wxART_%s" % bitmapName))
            mintCtrl.SetToolTipString(tooltip)

    def onCurrencyChanged(self, message):
        # Update all the accounts.
        for account, textCtrl in zip(self.accountObjects, self.totalTexts):
            textCtrl.Label = account.float2str(account.Balance)
        # Update the total text.
        self.updateGrandTotal()
        self.Parent.Layout()
        
    def onToggleMintIntegration(self, message):
        enabled = message.data
        if enabled:
            self.ConfigureCurrentAccount(tab="mint")
            # Refresh everything in the case of a cancel which won't trigger an update event.
            self.onMintDataUpdated()
        else:
            self.ShowMintStatus(False)
           
    def onMintDataUpdated(self, message=None):
        self.ShowMintStatus(True)
        self._UpdateMintStatuses()
        # A zero-balance account could be out of/ in sync, potentially toggling its visibility.
        self.refreshVisibility()
        
    def ShowMintStatus(self, show):
        for index, mintStatus in enumerate(self.mintStatuses):
            if self.IsVisible(index):
                mintStatus.Show(show)
        self.Layout()
        
    def MintStatusIsShown(self):
        return self.Model.MintEnabled

    def IsVisible(self, index):
        """Return whether or not the account at the given index is visible."""
        if index is None:
            return False

        if index < 0 or index >= self.GetCount():
            raise IndexError, "No element at index %i"%index

        # Offset by 1 because the first child is actually the button sizer.
        return self.childSizer.GetItem(index+1).IsShown()

    def SelectItem(self, index):
        """Given an index (zero-based), select the appropriate account."""
        if index is None:
            account = None
            self.allAccountsRadio.Value = True
        else:
            account = self.accountObjects[index]
            # Set the value in case it wasn't a click that triggered this.
            self.radioButtons[index].Value = True

        self.currentIndex = index
        # Update the remove/edit buttons.
        self.removeButton.Enabled = index is not None
        self.editButton.Enabled = index is not None
        self.configureButton.Enabled = index is not None

        # Inform everyone that we've changed. This is different from the 'user.account changed' event,
        # as account changes are also triggered by account removals and additions.
        Publisher.sendMessage("view.account changed", account)
        return account
        
    def SelectItemById(self, theId):
        # If there is no recently selected account, select the first visible if one exists.
        if theId is None:
            self.SelectVisibleItem(0)
        else:
            for i, account in enumerate(self.accountObjects):
                if account.ID == theId:
                    self.SelectItem(i)
                    break
            else:
                # This seems rather unlikely, but let's handle it gracefully.
                self.SelectVisibleItem(0)
                
    def SelectItemByAccount(self, account):
        if account:
            return self.SelectItemById(account.ID)
        else:
            return self.SelectItem(None)

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
            
    def SelectPreviousAccount(self):
        if self.currentIndex is not None:
            i = self.currentIndex - 1
        else:
            i = len(self.accountObjects) - 1
            
        while i >= 0:
            if self.IsVisible(i):
                return self.SelectItem(i)
            i -= 1
        return self.accountObjects[0]
    
    def SelectNextAccount(self):
        if self.currentIndex is not None:
            i = self.currentIndex + 1
        else:
            i = len(self.accountObjects)
            
        while i < len(self.accountObjects):
            if self.IsVisible(i):
                return self.SelectItem(i)
            i += 1
            
        # We reached the end. If "All" isn't already selected, do it.
        if self.GetCurrentAccount() is not None:
            self.SelectItem(None)

    def GetCount(self):
        return len(self.accountObjects)
    
    def GetVisibleCount(self):
        return len([i for i in range(self.GetCount()) if self.IsVisible(i)])

    def GetCurrentAccount(self):
        if self.currentIndex is not None:
            return self.accountObjects[self.currentIndex]
        else: # Not necessary, but explicit is clearer here.
            return None

    def ConfigureCurrentAccount(self, tab="default"):
        dlg = accountconfigdialog.AccountConfigDialog(self, self.GetCurrentAccount(), tab)
        dlg.ShowModal()

    def onAccountRemoved(self, message):
        """
        Called when an account is removed from the model.
        """
        account = message.data
        index = self.accountObjects.index(account)
        self._RemoveItem(index)

        # Start flashing the add button if there are no accounts.
        if not self.GetCount():
            self.addButton.StartFlashing()

    def _PutAccount(self, account, select=False):
        index = 0
        for currAccount in self.accountObjects:
            if account.Name < currAccount.Name:
                break
            index += 1

        self._InsertItem(index, account)

        if select:
            self.SelectItem(index)
        return index

    def _InsertItem(self, index, account):
        """
        Insert an item (by account) into the given position.

        This assumes the account already exists in the database.
        """
        balance = account.Balance

        # Create the controls.
        link = wx.RadioButton(self.childPanel, label=account.Name)
        link.AccountIndex = index
        totalText = wx.StaticText(self.childPanel, label=account.float2str(balance))
        mintStatus = wx.StaticBitmap(self.childPanel)
        mintStatus.Show(self.Model.MintEnabled)
        
        self.accountObjects.insert(index, account)
        self.radioButtons.insert(index, link)
        self.totalTexts.insert(index, totalText)
        self.mintStatuses.insert(index, mintStatus)

        # Put them in an hsizer.
        miniSizer = wx.BoxSizer()
        miniSizer.Add(link, 1, wx.ALIGN_CENTER)
        miniSizer.Add(totalText, 0, wx.ALIGN_CENTER|wx.LEFT, 10)
        miniSizer.Add(mintStatus, 0, wx.ALIGN_CENTER|wx.LEFT, 3)
        miniSizer.AddSpacer(3)

        # Insert the hsizer into the correct position in the list.
        self.childSizer.Insert(index+1, miniSizer, 0, wx.EXPAND|wx.BOTTOM, 3)

        # Renumber the links after this.
        for linkCtrl in self.radioButtons[index+1:]:
            linkCtrl.AccountIndex = linkCtrl.AccountIndex+1
        if self.currentIndex >= index:
            self.currentIndex += 1

        # Update the total text, as sometimes the account already exists.
        self.updateGrandTotal()

        self.Layout()
        self.Parent.Layout()

    def _RemoveItem(self, index, fixSel=True):
        linkCtrl = self.radioButtons[index]

        self.accountObjects.pop(index)
        del self.radioButtons[index]
        del self.totalTexts[index]
        del self.mintStatuses[index]

        # Renumber the links after this.
        for linkCtrl in self.radioButtons[index:]:
            linkCtrl.AccountIndex = linkCtrl.AccountIndex-1

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
        self.updateGrandTotal()

        self.Layout()
        self.Parent.Layout()

    def onAccountBalanceChanged(self, message):
        """
        Update all the total strings.
        """
        account = message.data
        # Figure out the position of the account in our list.
        index = self.accountObjects.index(account) # Raises ValueError if not found.

        # Update the total for the changed account.
        self.totalTexts[index].Label = account.float2str(account.Balance)
        # Update the grand total.
        self.updateGrandTotal()

        # Handle a zero-balance account going to non-zero or vice-versa.
        self.refreshVisibility()
        
        # Refresh sync status
        self._UpdateMintStatuses()

    def updateGrandTotal(self):
        self.totalText.Label = self.Model.float2str( self.Model.Balance )

    def onAddButton(self, event):
        self.showEditCtrl()
        self.addButton.Enabled = False

    def onAddAccount(self, event):
        # Grab the account name and add it.
        accountName = self.editCtrl.Value
        try:
            self.Model.CreateAccount(accountName)
        except bankexceptions.AccountAlreadyExistsException:
            wx.TipWindow(self, _("Sorry, an account by that name already exists."))#, maxLength=200)
        except bankexceptions.BlankAccountNameException:
            wx.TipWindow(self, _("Account names cannot be blank."))

    def onAccountAdded(self, message):
        """
        Called when a new account is created in the model.
        """
        account = message.data
        self.onHideEditCtrl()
        self._PutAccount(account, select=True)

        # Stop flashing the add button if it was, since there is now an account.
        self.addButton.StopFlashing()
        
    def onAccountChanged(self, message):
        account = message.data
        self.SelectItemByAccount(account)

    def onEditCtrlKey(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.onHideEditCtrl()
        else:
            event.Skip()

    def showEditCtrl(self, pos=-1, focus=True):
        if self.editCtrl:
            self.editCtrl.Value = ''
            self.editCtrl.Show()
        else:
            self.editCtrl = wx.TextCtrl(self.childPanel, style=wx.TE_PROCESS_ENTER)
            self.editCtrl.Bind(wx.EVT_KILL_FOCUS, self.onHideEditCtrl)
            self.editCtrl.Bind(wx.EVT_KEY_DOWN, self.onEditCtrlKey)

        if pos == -1:
            pos = 1
            self.editCtrl.Value = _("Account name")
            self.editCtrl.Bind(wx.EVT_TEXT_ENTER, self.onAddAccount)
        else:
            self.editCtrl.Value = self.accountObjects[pos].Name
            pos += 1
            self.childSizer.Hide(pos)
            self.hiddenIndex = pos
            self.editCtrl.Bind(wx.EVT_TEXT_ENTER, self.onRenameAccount)
            
        # Select the text inside so it can be typed over.
        self.editCtrl.SetSelection(-1, -1)

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

    def showModal(self, message, title, style):
        return wx.MessageDialog(self, message, title, style=style).ShowModal()

    def onRemoveButton(self, event):
        if self.currentIndex is not None:
            account = self.accountObjects[self.currentIndex]
            warningMsg = _("This will permanently remove the account '%s' and all its transactions. Continue?")
            result = self.showModal(warningMsg%account.Name, _("Warning"), style=wx.YES_NO|wx.ICON_EXCLAMATION)
            if result == wx.ID_YES:
                # Remove the account from the model.
                account.Remove()

    def onConfigureButton(self, event=None):
        self.ConfigureCurrentAccount()

    def onRenameButton(self, event):
        if self.currentIndex is not None:
            self.showEditCtrl(self.currentIndex)

    def onRenameAccount(self, event):
        account = self.accountObjects[self.currentIndex]
        oldName = account.Name
        newName = self.editCtrl.Value

        if oldName == newName:
            # If there was no change, don't do anything.
            self.onHideEditCtrl()
            return

        try:
            account.Name = newName
        except bankexceptions.AccountAlreadyExistsException:
            wx.TipWindow(self, _("Sorry, an account by that name already exists."))#, maxLength=200)
        except bankexceptions.BlankAccountNameException:
            wx.TipWindow(self, _("Account names cannot be blank."))

    def onAccountRenamed(self, message):
        """Called when an account has been renamed in the model."""
        account = message.data
        # Hide the edit control.
        self.onHideEditCtrl(restore=False)
        # Just renaming won't put it in the right alpha position, so remove it
        # and add it again, letting _PutAccount handle the ordering.
        self._RemoveItem(self.currentIndex, fixSel=False)
        self.currentIndex = self._PutAccount(account)
        self.radioButtons[self.currentIndex].Value = True

    def onAccountClick(self, event):
        """
        This method is called when the current account has been changed by clicking on an account name.
        """
        radio = event.EventObject
        if radio is self.allAccountsRadio:
            account = None
        else:
            account = self.accountObjects[radio.AccountIndex]
        Publisher.sendMessage("user.account changed", account)
        
    def onShowZeroToggled(self, message):
        self.refreshVisibility()
        
    def onSelectNextAccount(self, message):
        self.SelectNextAccount()
        
    def onSelectPreviousAccount(self, message):
        self.SelectPreviousAccount()

    def refreshVisibility(self, refreshSelection=True):
        """
        This method is called when the user checks/unchecks the option to hide zero-balance accounts.
        """
        showZero = self.bankController.ShowZeroBalanceAccounts
        showMint = self.MintStatusIsShown()
        
        for i, account in enumerate(self.accountObjects):
            # Show it, in the case of calls from updateTotals where a
            # zero-balance became a non-zero. otherwise it won't come up.
            # +1 offset is to take into account the buttons at the top.
            self.childSizer.Show(i+1)
            if not showZero:
                # If the account is out of sync, always show it so as not to hide discrepencies.
                if abs(account.Balance) < .001 and not account.IsOutOfSync():
                    self.childSizer.Hide(i+1)

        # Restore the Mint status.
        self.ShowMintStatus(showMint)
        # If we hid the current selection, select the first available.
        if refreshSelection and not showZero and not self.IsVisible(self.currentIndex):
            self.SelectVisibleItem(0)
                
        self.Parent.Layout()
