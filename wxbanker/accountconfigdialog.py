#    https://launchpad.net/wxbanker
#    accountconfigdialog.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
from wx.lib.pubsub import Publisher
from wxbanker.transactionctrl import TransactionCtrl
from wxbanker.currencies import CurrencyStrings, GetCurrencyInt

from wxbanker.mint.api import Mint
try:
    from wxbanker.mint.keyring import Keyring
except ImportError:
    Keyring = None


class MintConfigPanel(wx.Panel):
    ID_UPDATE = wx.NewId()
    
    def  __init__(self, parent, account):
        wx.Panel.__init__(self, parent)
        self.Account = account
        self.NoneAccount = _("None")
        self.headerText = wx.StaticText(self, -1, _("Mint.com credentials:"))

        self.usernameBox = wx.TextCtrl(self)
        self.passwordBox = wx.TextCtrl(self, style=wx.TE_PASSWORD)
            
        self.saveAuthCheck = wx.CheckBox(self, label=_("Save credentials in keyring"))
        
        self.accountText = wx.StaticText(self, -1, _("Corresponding Mint account for %(name)s:") % {"name": account.Name})
        self.mintCombo = wx.Choice(self, choices=[self.NoneAccount])
        self.mintUpdateButton = wx.Button(self, label=_("Update"), id=self.ID_UPDATE)

        gridSizer = wx.GridSizer(2, 2, 3, 3)
        gridSizer.Add(wx.StaticText(self, label=_("Username:")), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        gridSizer.Add(self.usernameBox, flag=wx.ALIGN_LEFT|wx.LEFT, border=6)
        gridSizer.Add(wx.StaticText(self, label=_("Password:")), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        gridSizer.Add(self.passwordBox, flag=wx.ALIGN_LEFT|wx.LEFT, border=6)
        
        mintAccountSizer = wx.BoxSizer()
        mintAccountSizer.Add(self.mintCombo, 0, wx.LEFT, 6)
        mintAccountSizer.Add(self.mintUpdateButton, wx.LEFT, 6)

        saveButton = wx.Button(self, label=_("Save"), id=wx.ID_SAVE)
        closeButton = wx.Button(self, label=_("Cancel"), id=wx.ID_CLOSE)
        buttonSizer = wx.BoxSizer()
        buttonSizer.Add(saveButton)
        buttonSizer.AddSpacer(12)
        buttonSizer.Add(closeButton)
        buttonSizer.AddSpacer(6)
        
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.AddSpacer(6)
        self.Sizer.Add(self.headerText, 0, wx.LEFT, 6)
        self.Sizer.AddSpacer(12)
        self.Sizer.Add(gridSizer, 0, wx.EXPAND|wx.LEFT, 6)
        self.Sizer.AddSpacer(12)
        self.Sizer.Add(self.saveAuthCheck, 0, wx.LEFT, 12)
        self.Sizer.AddSpacer(24)
        self.Sizer.Add(self.accountText, 0, wx.LEFT, 6)
        self.Sizer.AddSpacer(6)
        self.Sizer.Add(mintAccountSizer)
        self.Sizer.AddStretchSpacer(1)
        self.Sizer.Add(buttonSizer, flag=wx.ALIGN_RIGHT)
        self.Sizer.AddSpacer(6)
        
        # If we have a keyring, enable the checkbox, and populate any existing data.
        if Keyring:
            self.saveAuthCheck.Enable(True)
            keyring = Keyring()
            if keyring.has_credentials():
                self.saveAuthCheck.Value = True
                user, passwd = keyring.get_credentials()
                self.usernameBox.Value = user
                self.passwordBox.Value = passwd

        # Properly populate the list of accounts if we are already logged in.
        if Mint().IsLoggedIn():
            self.updateMintAccounts()
            
        self.mintUpdateButton.Bind(wx.EVT_BUTTON, self.onUpdateButton)
        self.Bind(wx.EVT_BUTTON, self.onButton)
        
    def onUpdateButton(self, event):
        self.updateMintAccounts()
        
    def updateMintAccounts(self):
        # Reset the choices.
        self.mintCombo.SetItems([self.NoneAccount])
        
        # Login (potentially using the cache) and populate accounts.
        self.mintLogin()
        accounts = Mint.GetAccounts()
        accountMintId = self.Account.GetMintId()
        # Init i in the case that there aren't accounts as we use it below.
        i = 0
        matched = False
        for i, (mintId, item) in enumerate(sorted(Mint.GetAccounts().items(), cmp=lambda a,b: cmp(a[1]['name'], b[1]['name']))):
            option = "%s - %s" % (item['name'], self.Account.float2str(item['balance']))
            self.mintCombo.Append(option, mintId)
            # If this is the currently configured account, select it.
            if mintId == accountMintId:
                # It is offset by one as NoneAccount is first.
                self.mintCombo.Selection = i+1
                matched = True
        
        # If the account has an ID configured but it wasn't matched, show/select it so a save is not lossy.
        if not matched and accountMintId:
            self.mintCombo.Append(str(accountMintId), accountMintId)
            self.mintCombo.Selection = i+1
        # If there are accounts but none is currently set, choose the first actual one.
        elif accounts and not self.Account.IsMintEnabled():
            self.mintCombo.Selection = 1
            
        self.Layout()
        
    def onButton(self, event):
        """If the save button was clicked save, and close the dialog in any case (Close/Cancel/Save)."""
        assert event.Id in (wx.ID_CLOSE, wx.ID_SAVE)
        
        if event.Id == wx.ID_SAVE:
            self.mintLogin()
            sel = self.mintCombo.Selection
            if sel != -1:
                mintId = self.mintCombo.GetClientData(sel)
                self.Account.MintId = mintId
            
        self.GrandParent.Destroy()
        
    def mintLogin(self):
        username, passwd = [ctrl.Value for ctrl in (self.usernameBox, self.passwordBox)]
        if self.saveAuthCheck.IsChecked():
            Keyring().set_credentials(username, passwd)
            Mint.LoginFromKeyring()
        else:
            Mint.Login(username, passwd)
        
 
class RecurringConfigPanel(wx.Panel):
    def __init__(self, parent, account):
        self.Account = account
        wx.Panel.__init__(self, parent)
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.AddSpacer(6)
        
        self.staticBox = wx.StaticBox(self, label=_("Transaction details"))
        self.staticBoxSizer = wx.StaticBoxSizer(self.staticBox, wx.VERTICAL)
        
        self.transactionCtrl = TransactionCtrl(self, editing=account)
        self.staticBoxSizer.Add(self.transactionCtrl)
        
        self.transactions = self.Account.GetRecurringTransactions()
        
        self.buttonSizer = wx.BoxSizer()
        self.Sizer.AddSpacer(6)
        # Something can be inserted here so the double spacers makes some sense.
        self.Sizer.AddSpacer(12)
        self.Sizer.Add(self.staticBoxSizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 6)
        self.Sizer.AddStretchSpacer(1)
        self.Sizer.Add(self.buttonSizer, flag=wx.ALIGN_RIGHT|wx.EXPAND)
        self.Sizer.AddSpacer(6)
        
        if not self.transactions:
            self.setupNoRecurringTransactions()
        else:
            self.setupRecurringTransactions()
            
        self.buttonSizer.AddSpacer(6)
        
        self.Bind(wx.EVT_BUTTON, self.onButton)
        
    def GetCurrentRecurringTransaction(self):
        return self.transactions[self.transactionChoice.GetSelection()]
        
    def onButton(self, event):
        """If the save button was clicked save, and close the dialog in any case (Close/Cancel/Save)."""
        assert event.Id in (wx.ID_CLOSE, wx.ID_SAVE, wx.ID_DELETE)
        
        if event.Id == wx.ID_SAVE:
            self.transactionCtrl.ToRecurring()
            originalTransaction = self.transactions[self.transactionChoice.Selection]
            modifiedTransaction = self.transactionCtrl.recurringObj
            originalTransaction.UpdateFrom(modifiedTransaction)
            # Let everyone know about this, someone might want to check if there are new pending transactions.
            Publisher.sendMessage("recurringtransaction.updated")
        elif event.Id == wx.ID_DELETE:
            recurring = self.GetCurrentRecurringTransaction()
            warningMsg = _("This will permanently remove this recurring transaction. Continue?")
            dlg = wx.MessageDialog(self, warningMsg, _("Warning"), style=wx.YES_NO|wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                recurring.Parent.RemoveRecurringTransaction(recurring)
        
        self.GrandParent.Destroy()
            
    def setupNoRecurringTransactions(self):
        self.staticBox.Hide()
        self.transactionCtrl.Hide()
        self.Sizer.Insert(1, wx.StaticText(self, label=_("This account currently has no recurring transactions.")), flag=wx.ALIGN_CENTER)
        
        closeButton = wx.Button(self, label=_("Close"), id=wx.ID_CLOSE)
        self.buttonSizer.AddStretchSpacer(1)
        self.buttonSizer.Add(closeButton)
        
    def setupRecurringTransactions(self):
        strings = [rt.GetDescriptionString() for rt in self.transactions]
        self.transactionChoice = wx.Choice(self, choices=strings)
        
        self.Sizer.Insert(1, self.transactionChoice, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=6)
        self.transactionCtrl.FromRecurring(self.transactions[0])
        
        deleteButton = wx.Button(self, label=_("Delete"), id=wx.ID_DELETE)
        saveButton = wx.Button(self, label=_("Save"), id=wx.ID_SAVE)
        closeButton = wx.Button(self, label=_("Cancel"), id=wx.ID_CLOSE)
        self.buttonSizer.AddSpacer(6)
        self.buttonSizer.Add(deleteButton)
        self.buttonSizer.AddStretchSpacer(1)
        self.buttonSizer.Add(saveButton)
        self.buttonSizer.AddSpacer(12)
        self.buttonSizer.Add(closeButton)
        
        self.transactionChoice.Bind(wx.EVT_CHOICE, self.onTransactionChoice)
        
    def onTransactionChoice(self, event):
        transaction = self.GetCurrentRecurringTransaction()
        self.transactionCtrl.FromRecurring(transaction)
        
class CurrencyConfigPanel(wx.Panel):
    def __init__(self, parent, account):
        self.Account = account
        wx.Panel.__init__(self, parent)
        self.headerText = wx.StaticText(self, -1, _("Account currency: "))
        
        saveButton = wx.Button(self, label=_("Save"), id=wx.ID_SAVE)
        closeButton = wx.Button(self, label=_("Cancel"), id=wx.ID_CLOSE)
        
        buttonSizer = wx.BoxSizer()
        buttonSizer.Add(saveButton)
        buttonSizer.AddSpacer(12)
        buttonSizer.Add(closeButton)
        buttonSizer.AddSpacer(6)
        
        #base currency = global currency
        currencies = ["Base currency"] + CurrencyStrings
        self.currencyCombo = wx.Choice(self, choices=currencies)
        # we have to add 1 to the current indext because we added the "base currency" entry
        self.currencyCombo.SetSelection(GetCurrencyInt(self.Account.GetCurrency())+1)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.AddSpacer(6)
        self.Sizer.Add(self.headerText, 0, wx.LEFT, 6)
        self.Sizer.AddSpacer(6)
        self.Sizer.Add(self.currencyCombo, 0, wx.LEFT, 6)
        self.Sizer.AddStretchSpacer(1)
        self.Sizer.Add(buttonSizer, flag=wx.ALIGN_RIGHT)
        self.Sizer.AddSpacer(6)
        self.Bind(wx.EVT_BUTTON, self.onButton)
        
    def onButton(self, event):
        """If the save button was clicked save, and close the dialog in any case (Close/Cancel/Save)."""
        assert event.Id in (wx.ID_CLOSE, wx.ID_SAVE)
        
        if event.Id == wx.ID_SAVE:
            #we have to substract 1 from combo_box selection because we added the "base currency" entry
            selectedCurrency = self.currencyCombo.GetSelection() - 1
            Publisher.sendMessage("user.account_currency_changed", (self.Account, selectedCurrency))
            
        self.GrandParent.Destroy()
        
class AccountConfigDialog(wx.Dialog):
    def __init__(self, parent, account, tab="default"):
        wx.Dialog.__init__(self, parent, title=account.Name, size=(600, 400))
        self.Sizer = wx.BoxSizer()
        self.notebook = wx.aui.AuiNotebook(self, style=wx.aui.AUI_NB_TOP)
        self.Sizer.Add(self.notebook, 1, wx.EXPAND)
        
        self.recurringPanel = RecurringConfigPanel(self.notebook, account)
        self.mintPanel = MintConfigPanel(self.notebook, account)
        self.currencyPanel = CurrencyConfigPanel(self.notebook, account)
        self.notebook.AddPage(self.recurringPanel, _("Recurring Transactions"))
        self.notebook.AddPage(self.mintPanel, _("Mint.com Integration"))
        self.notebook.AddPage(self.currencyPanel, _("Currency Settings"))
        
        if tab == "mint":
            # Setting the selection synchronously gets changed back somewhere in the event queue.
            wx.CallLater(50, self.notebook.SetSelection, 1)
