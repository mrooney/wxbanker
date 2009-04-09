#    https://launchpad.net/wxbanker
#    newtransactionctrl.py: Copyright 2007, 2008 Mike Rooney <mrooney@ubuntu.com>
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

import wx, datetime
import bankcontrols
from wx.lib.pubsub import Publisher


class NewTransactionCtrl(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.CurrentAccount = None

        self.dateCtrl = dateCtrl = bankcontrols.DateCtrlFactory(self)

        # The Description and Amount controls.
        self.descCtrl = descCtrl = bankcontrols.HintedTextCtrl(self, size=(140, -1), style=wx.TE_PROCESS_ENTER, hint=_("Description"), icon="wxART_page_edit")
        self.amountCtrl = amountCtrl = bankcontrols.HintedTextCtrl(self, size=(90, -1), style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT, hint=_("Amount"), icon="wxART_money_dollar")

        # The add button.
        self.newButton = newButton = wx.BitmapButton(self, bitmap=wx.ArtProvider.GetBitmap('wxART_money_add'))
        newButton.SetToolTipString(_("Enter this transaction"))

        # The transfer check.
        self.transferCheck = transferCheck = wx.CheckBox(self, label=_("Transfer"))
        
        # The recurs check.
        self.recursCheck = recursCheck = wx.CheckBox(self, label=_("Recurring"))
        
        transferSizer = wx.BoxSizer()
        transferSizer.Add(transferCheck, 0, wx.ALIGN_CENTER)
        transferSizer.Add(wx.StaticText(self, label="("), 0, wx.ALIGN_CENTER)
        transferSizer.Add(bankcontrols.HyperlinkText(self, label="?", onClick=self.onTransferTip), 0, wx.ALIGN_CENTER)
        transferSizer.Add(wx.StaticText(self, label=")"), 0, wx.ALIGN_CENTER)

        checkSizer = wx.BoxSizer(wx.VERTICAL)
        checkSizer.Add(transferSizer)
        checkSizer.Add(self.recursCheck)

        # Set up the layout.
        self.mainSizer = mainSizer = wx.BoxSizer()
        mainSizer.Add(wx.StaticBitmap(self, bitmap=wx.ArtProvider.GetBitmap('wxART_date')), 0, wx.ALIGN_CENTER|wx.ALL, 2)
        mainSizer.Add(dateCtrl, 0, wx.ALIGN_CENTER)
        mainSizer.AddSpacer(5)
        mainSizer.Add(descCtrl, 1, wx.ALIGN_CENTER)
        mainSizer.AddSpacer(5)
        mainSizer.Add(amountCtrl, 0, wx.ALIGN_CENTER)
        mainSizer.AddSpacer(5)
        mainSizer.Add(newButton, 0, wx.ALIGN_CENTER)
        mainSizer.AddSpacer(5)
        mainSizer.Add(checkSizer, 0, wx.ALIGN_CENTER)
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
            
        Publisher.subscribe(self.onAccountChanged, "view.account changed")
        
    def onAccountChanged(self, message):
        account = message.data
        self.CurrentAccount = account

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
        # Grab the raw values we will need to parse.
        date = self.dateCtrl.Value
        desc = self.descCtrl.Value
        amount = self.amountCtrl.Value

        # Parse the amount.
        try:
            amount = float(amount)
        except ValueError:
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

        return amount, desc, date

    def getSourceAccount(self, destinationAccount):
        accountDict = {}
        for account in destinationAccount.GetSiblings():
            accountDict[account.Name] = account
            
        # Create a dialog with the other account names to choose from.
        dlg = wx.SingleChoiceDialog(self,
                _('Which account will the money come from?'), _('Other accounts'),
                sorted(accountDict.keys()), wx.CHOICEDLG_STYLE)

        if dlg.ShowModal() == wx.ID_OK:
            accountName = dlg.GetStringSelection()
            return accountDict[accountName]

    def onNewTransaction(self, event):
        # First, ensure an account is selected.
        destAccount = self.CurrentAccount
        if destAccount is None:
            dlg = wx.MessageDialog(self,
                                _("Please select an account and then try again."),
                                _("No account selected"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return
        
        # Grab the transaction values from the control.
        result = self.getValues()
        if result is None:
            # Validation failed, user was informed.
            return

        amount, desc, date = result
        isTransfer = self.transferCheck.Value

        # If a search is active, we have to ask the user what they want to do.
        if self.Parent.searchActive:
            actionStr = {True: _("transfer"), False: _("transaction")}[isTransfer]
            ##TRANSLATORS: Example: ...and make this TRANSACTION in "CHECKING ACCOUNT"?
            msg = _('A search is currently active. Would you like to clear the current search and make this %s in "%s"?') % (actionStr, destAccount.Name)
            dlg = wx.MessageDialog(self, msg, _("Clear search?"), style=wx.YES_NO|wx.ICON_WARNING)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                Publisher().sendMessage("SEARCH.CANCELLED")
            else:
                return

        source = None
        if isTransfer:
            source = self.getSourceAccount(destAccount)
            if source is None:
                return
            
        destAccount.AddTransaction(amount, desc, date, source)
        self.onSuccess()


    def onTransferTip(self, event):
        tipStr = _("If this box is checked when adding a transaction, you will be prompted for the account to use as the source of the transfer.")+"\n\n"+\
                 _("For example, checking this box and entering a transaction of $50 into this account will also subtract $50 from the account that you choose as the source.")
        wx.TipWindow(self, tipStr, maxLength=200)

    def onSuccess(self):
        # Reset the controls.
        self.descCtrl.Value = ''
        self.amountCtrl.Value = ''
