#    https://launchpad.net/wxbanker
#    accountlistctrl.py: Copyright 2007, 2008 Mike Rooney <mrooney@ubuntu.com>
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
import bankcontrols, bankexceptions
from wx.lib.pubsub import Publisher
import accountconfigdialog


class AccountListCtrl(wx.Panel):
    """
    This control manages a clickable list of accounts,
    displaying their totals to the right of them
    as well as the grand total as the last entry.

    Accounts can be added, removed, and renamed.
    """
    ID_TIMER = wx.NewId()
    
    def __init__(self, parent, bankController, autoPopulate=True):
        wx.Panel.__init__(self, parent)
        self.Model = bankController.Model
        
        # Initialize some attributes to their default values.
        self.editCtrl = self.hiddenIndex = None
        self.currentIndex = None
        self.boxLabel = _("Accounts") + " (%i)"
        self.hyperLinks, self.totalTexts, self.accountObjects = [], [], []

        # Create the staticboxsizer which is the home for everything.
        # This *MUST* be created first to ensure proper z-ordering (as per docs).
        self.staticBox = wx.StaticBox(self, label=self.boxLabel%0)
        
        # Create a single panel to be the "child" of the static box sizer,
        # to work around a wxPython regression that prevents tooltips. lp: xxxxxx
        self.childPanel = wx.Panel(self)
        self.childSizer = childSizer = wx.BoxSizer(wx.VERTICAL)

        ## Create and set up the buttons.
        # The ADD account button.
        BMP = self.addBMP = wx.ArtProvider.GetBitmap('wxART_add')
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
        #configureButton.Hide()
        
        # Layout the buttons.
        buttonSizer = wx.BoxSizer()
        buttonSizer.Add(addButton)
        buttonSizer.Add(removeButton)
        buttonSizer.Add(editButton)
        buttonSizer.Add(configureButton)

        # Set up the "Total" sizer.
        self.totalText = wx.StaticText(self.childPanel, label="$0.00")
        self.totalTexts.append(self.totalText)
        miniSizer = wx.BoxSizer()
        miniSizer.Add(wx.StaticText(self.childPanel, label=_("Total")+":"))
        miniSizer.AddStretchSpacer(1)
        miniSizer.Add(self.totalText)

        # The hide zero-balance accounts option.
        self.hideBox = hideBox = wx.CheckBox(self.childPanel, label=_("Hide zero-balance accounts"))
        hideBox.SetToolTipString(_("When enabled, accounts with a balance of $0.00 will be hidden from the list"))

        #self.staticBoxSizer = SmoothStaticBoxSizer(self.staticBox, wx.VERTICAL)
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
        configureButton.Bind(wx.EVT_BUTTON, self.onConfigureButton)
        hideBox.Bind(wx.EVT_CHECKBOX, self.onHideCheck)
        # Set up the link binding.
        self.Bind(wx.EVT_HYPERLINK, self.onAccountClick)

        # Subscribe to messages we are concerned about.
        Publisher().subscribe(self.onAccountBalanceChanged, "account.balance changed")
        Publisher().subscribe(self.onAccountRemoved, "account.removed")
        Publisher().subscribe(self.onAccountAdded, "account.created")
        Publisher().subscribe(self.onAccountRenamed, "account.renamed")
        Publisher().subscribe(self.onCurrencyChanged, "currency_changed")

        # Populate ourselves initially unless explicitly told not to.
        if autoPopulate:
            for account in self.Model.Accounts:
                self._PutAccount(account)

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
        
        # Set up the timer, which will flash the add account bitmap if there aren't any accounts.
        self.Timer = wx.Timer(self, self.ID_TIMER)
        self.FlashState = 0
        wx.EVT_TIMER(self, self.ID_TIMER, self.onFlashTimer)
        if not self.GetCount():
            self.startFlashTimer()
            
    def onFlashTimer(self, event):
        if self.FlashState:
            self.addButton.SetBitmapLabel(self.addBMP)
        else:
            self.addButton.SetBitmapLabel(wx.EmptyBitmapRGBA(16,16))
        
        # Now toggle the flash state.
        self.FlashState = not self.FlashState
        
    def stopFlashTimer(self):
        self.Timer.Stop()
        self.addButton.SetBitmapLabel(self.addBMP)
        
    def startFlashTimer(self):
        self.Timer.Start(1250)
        
    def onCurrencyChanged(self, message):
        # Update all the accounts.
        for account, textCtrl in zip(self.accountObjects, self.totalTexts):
            textCtrl.Label = account.float2str(account.Balance)
        # Update the total text.
        self.updateGrandTotal()
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
            account = self.accountObjects[index]
        else:
            account = None

        self.currentIndex = index
        # Update the remove/edit buttons.
        self.removeButton.Enabled = index is not None
        self.editButton.Enabled = index is not None
        self.configureButton.Enabled = index is not None

        # Tell the parent we changed.
        Publisher().sendMessage("view.account changed", account)

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

    def HighlightItem(self, index):
        #print "Highlighting", self.hyperLinks[index].Label[:-1]
        self.hyperLinks[index].SetNormalColour(wx.BLACK)

    def UnhighlightItem(self, index):
        #print "Unhighlighting", self.hyperLinks[index].Label[:-1]
        self.hyperLinks[index].SetNormalColour(wx.BLUE)

    def GetCount(self):
        return len(self.accountObjects)

    def GetCurrentAccount(self):
        if self.currentIndex is not None:
            return self.accountObjects[self.currentIndex]
        else: # Not necessary, but explicit is clearer here.
            return None

    def onAccountRemoved(self, message):
        """
        Called when an account is removed from the model.
        """
        account = message.data
        index = self.accountObjects.index(account)
        self._RemoveItem(index)
        
        # Start flashing the add button if there are no accounts.
        if not self.GetCount():
            self.startFlashTimer()

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
        link = bankcontrols.HyperlinkText(self.childPanel, label=account.Name+":", url=str(index))
        totalText = wx.StaticText(self.childPanel, label=account.float2str(balance))
        self.accountObjects.insert(index, account)
        self.hyperLinks.insert(index, link)
        self.totalTexts.insert(index, totalText)

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
        self.updateGrandTotal()

        # Update the static label.
        self.staticBox.Label = self.boxLabel % self.GetCount()

        self.Layout()
        self.Parent.Layout()

    def _RemoveItem(self, index, fixSel=True):
        linkCtrl = self.hyperLinks[index]
        removedAccount = linkCtrl.Label[:-1]

        self.accountObjects.pop(index)
        del self.hyperLinks[index]
        del self.totalTexts[index]

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
        self.updateGrandTotal()

        # Update the static label.
        self.staticBox.Label = self.boxLabel % self.GetCount()

        self.Layout()
        self.Parent.Layout()

    def onAccountBalanceChanged(self, message):
        """
        Update all the total strings.
        """
        account = message.data
        # Figure out the position of the account in our list.
        index = self.accountObjects.index(account)
        if index < 0:
            raise Exception("Unable to locate Account in list")
        
        # Update the total for the changed account.
        self.totalTexts[index].Label = account.float2str(account.Balance)
        # Update the grand total.
        self.updateGrandTotal()

        # Handle a zero-balance account going to non-zero or vice-versa.
        self.onHideCheck()

        self.Layout()
        self.Parent.Layout()
        
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

    def onAccountAdded(self, message):
        """
        Called when a new account is created in the model.
        """
        account = message.data
        self.onHideEditCtrl() #ASSUMPTION!
        self._PutAccount(account, select=True)
        
        # Stop flashing the add button if it was, since there is now an account.
        self.stopFlashTimer()
        
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
            pos = self.GetCount()+1
            self.editCtrl.Bind(wx.EVT_TEXT_ENTER, self.onAddAccount)
        else:
            self.editCtrl.Value = self.accountObjects[pos].Name
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
            account = self.accountObjects[self.currentIndex]
            warningMsg = _("This will permanently remove the account '%s' and all its transactions. Continue?")
            dlg = wx.MessageDialog(self, warningMsg%account.Name, _("Warning"), style=wx.YES_NO|wx.ICON_EXCLAMATION)
            if dlg.ShowModal() == wx.ID_YES:
                # Remove the account from the model.
                account.Remove()
                
    def onConfigureButton(self, event):
        dlg = accountconfigdialog.AccountConfigDialog(self, self.GetCurrentAccount())
        dlg.ShowModal()

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
            #wx.MessageDialog(self, 'An account by that name already exists', 'Error :[', wx.OK | wx.ICON_ERROR).ShowModal()
            wx.TipWindow(self, _("Sorry, an account by that name already exists."))#, maxLength=200)

    def onAccountRenamed(self, message):
        """
        Called when an account has been renamed in the model.

        TODO: don't assume it was the current account that was renamed.
        """
        oldName, account = message.data
        # Hide the edit control.
        self.onHideEditCtrl(restore=False) #ASSUMPTION!
        # Just renaming won't put it in the right alpha position, so remove it
        # and add it again, letting _PutAccount handle the ordering.
        self.UnhighlightItem(self.currentIndex)
        self._RemoveItem(self.currentIndex, fixSel=False)
        self.currentIndex = self._PutAccount(account)
        # Hightlight but don't select, account is already displayed elsewhere.
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
        for i, account in enumerate(self.accountObjects):
            # Show it, in the case of calls from updateTotals where a
            # zero-balance became a non-zero. otherwise it won't come up.
            # +1 offset is to take into account the buttons at the top.
            self.childSizer.Show(i+1)
            if checked:
                if abs(account.Balance) < .001:
                    self.childSizer.Hide(i+1)

        self.Parent.Layout()

        # We hid the current selection, so select the first available.
        if checked and not self.IsVisible(self.currentIndex):
            self.SelectVisibleItem(0)

        wx.Config.Get().WriteBool("HIDE_ZERO_BALANCE_ACCOUNTS", checked)
