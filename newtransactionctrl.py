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

class TransferPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.accountDict = {}
        self.nullChoice = ["----------"]
        
        self.fromRadio = wx.RadioButton(self, label=_("From"), style=wx.RB_GROUP)
        self.toRadio = wx.RadioButton(self, label=_("To"))
        self.accountSelection = wx.Choice(self, choices=self.nullChoice)
        
        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(wx.StaticText(self, label=_("Transfer:")), flag=wx.ALIGN_CENTER)
        self.Sizer.AddSpacer(3)
        self.Sizer.Add(self.fromRadio, flag=wx.ALIGN_CENTER)
        self.Sizer.Add(self.toRadio, flag=wx.ALIGN_CENTER)
        self.Sizer.AddSpacer(8)
        self.Sizer.Add(wx.StaticText(self, label=_("Account:")), flag=wx.ALIGN_CENTER)
        self.Sizer.Add(self.accountSelection, flag=wx.ALIGN_CENTER)
        
    def GetAccounts(self, currentAccount):
        otherAccount = self.accountDict[self.accountSelection.GetStringSelection()]
        if self.fromRadio.Value:
            source, destination = otherAccount, currentAccount
        else:
            source, destination = currentAccount, otherAccount
            
        return source, destination
    
    def Update(self, selectedAccount):
        if selectedAccount:
            self.accountDict = {}
            for account in selectedAccount.GetSiblings():
                self.accountDict[account.Name] = account
            choices = self.accountDict.keys()
        else:
            choices = self.nullChoice
            
        # Update the choices.
        self.accountSelection.SetItems(choices)
        

class RecurringPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        
        self.repeatsCombo = wx.Choice(self, choices=(_("Weekly"), _("Monthly"), _("Yearly")))
        self.everyText = wx.StaticText(self)
        self.everySpin = wx.SpinCtrl(self, min=1, max=130, initial=1)
        self.everySpin.MinSize = (50, -1)
        self.repeatsOnText = wx.StaticText(self)
        self.startDateCtrl = bankcontrols.DateCtrlFactory(self)
        self.endDateCtrl = bankcontrols.DateCtrlFactory(self)
        
        self.repeatsOnChecksWeekly = []
        self.repeatsOnSizerWeekly = wx.BoxSizer()
        today = datetime.date.today().weekday()
        for i, label in enumerate(_("MTWTFSS")):
            cb = wx.CheckBox(self, label=label)
            cb.SetValue(i==today)
            self.repeatsOnChecksWeekly.append(cb)
            self.repeatsOnSizerWeekly.Add(cb, flag=wx.ALIGN_CENTER)
            
        self.repeatsOnChecksMonthly = []
        self.repeatsOnSizerMonthly = wx.BoxSizer()
        for i in range(12):
            cb = wx.CheckBox(self, label=str(i+1))
            cb.SetValue(True)
            self.repeatsOnChecksMonthly.append(cb)
            self.repeatsOnSizerMonthly.Add(cb, flag=wx.ALIGN_CENTER)
        
        self.topSizer = wx.BoxSizer()
        self.bottomSizer = wx.BoxSizer()
        
        self.topSizer.Add(wx.StaticText(self, label=_("Repeats:")), flag=wx.ALIGN_CENTER)
        self.topSizer.Add(self.repeatsCombo, flag=wx.ALIGN_CENTER)
        self.topSizer.AddSpacer(15)
        self.topSizer.Add(wx.StaticText(self, label=_("Every")), flag=wx.ALIGN_CENTER)
        self.topSizer.AddSpacer(3)
        self.topSizer.Add(self.everySpin, flag=wx.ALIGN_CENTER)
        self.topSizer.AddSpacer(3)
        self.topSizer.Add(self.everyText, flag=wx.ALIGN_CENTER)
        self.topSizer.AddSpacer(15)
        self.topSizer.Add(wx.StaticText(self, label=_("Starts:")), flag=wx.ALIGN_CENTER)
        self.topSizer.Add(self.startDateCtrl, flag=wx.ALIGN_CENTER)
        self.topSizer.AddSpacer(5)
        self.topSizer.Add(wx.StaticText(self, label=_("Ends:")), flag=wx.ALIGN_CENTER)
        self.topSizer.Add(self.endDateCtrl, flag=wx.ALIGN_CENTER)
        
        self.bottomSizer.AddSpacer(10)
        self.bottomSizer.Add(self.repeatsOnText, flag=wx.ALIGN_CENTER)
        self.bottomSizer.Add(self.repeatsOnSizerWeekly, flag=wx.ALIGN_CENTER)
        self.bottomSizer.Add(self.repeatsOnSizerMonthly, flag=wx.ALIGN_CENTER)
        self.bottomSizer.Hide(self.repeatsOnSizerWeekly)
        self.bottomSizer.Hide(self.repeatsOnSizerMonthly)
        
        
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.topSizer)
        self.Sizer.AddSpacer(3)
        self.Sizer.Add(self.bottomSizer)
        
        self.update()
        self.repeatsCombo.Bind(wx.EVT_CHOICE, self.update)
        
    def update(self, event=None):
        self.Freeze()
        self.Sizer.Show(self.bottomSizer)
        self.bottomSizer.Hide(self.repeatsOnSizerWeekly)
        self.bottomSizer.Hide(self.repeatsOnSizerMonthly)
        self.bottomSizer.Hide(self.repeatsOnText)

        repeatType = self.repeatsCombo.Selection
        if repeatType == 0:
            everyText = _("weeks")
            self.repeatsOnText.Label = label=_("Repeats on days:")
            self.bottomSizer.Show(self.repeatsOnText)
            self.bottomSizer.Show(self.repeatsOnSizerWeekly)
        elif repeatType == 1:
            everyText = _("months")
            self.repeatsOnText.Label = label=_("Repeats on months:")
            self.bottomSizer.Show(self.repeatsOnText)
            self.bottomSizer.Show(self.repeatsOnSizerMonthly)
        elif repeatType == 2:
            everyText = _("years")
            self.Sizer.Hide(self.bottomSizer)
            
        self.everyText.Label = everyText
        
        self.Thaw()
        self.Parent.Parent.Layout()

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

        checkSizer = wx.BoxSizer(wx.VERTICAL)
        checkSizer.Add(self.transferCheck)
        checkSizer.Add(self.recursCheck)
        
        self.recurringPanel = RecurringPanel(self)
        self.transferPanel = TransferPanel(self)

        # Set up the layout.
        hSizer = wx.BoxSizer()
        hSizer.Add(wx.StaticBitmap(self, bitmap=wx.ArtProvider.GetBitmap('wxART_date')), 0, wx.ALIGN_CENTER|wx.ALL, 2)
        hSizer.Add(dateCtrl, 0, wx.ALIGN_CENTER)
        hSizer.AddSpacer(5)
        hSizer.Add(descCtrl, 1, wx.ALIGN_CENTER)
        hSizer.AddSpacer(5)
        hSizer.Add(amountCtrl, 0, wx.ALIGN_CENTER)
        hSizer.AddSpacer(5)
        hSizer.Add(newButton, 0, wx.ALIGN_CENTER)
        hSizer.AddSpacer(5)
        hSizer.Add(checkSizer, 0, wx.ALIGN_CENTER)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.recurringPanel, 0, wx.EXPAND|wx.TOP, 5)
        self.Sizer.Add(self.transferPanel, 0, wx.EXPAND|wx.TOP, 5)
        self.Sizer.Add(hSizer, 0, wx.EXPAND)
        self.Sizer.Hide(self.recurringPanel)
        self.Sizer.Hide(self.transferPanel)

        # Initialize necessary bindings.
        self.Bind(wx.EVT_TEXT_ENTER, self.onNewTransaction) # Gives us enter from description/amount.
        self.newButton.Bind(wx.EVT_BUTTON, self.onNewTransaction)
        self.recursCheck.Bind(wx.EVT_CHECKBOX, self.onRecurringCheck)
        self.transferCheck.Bind(wx.EVT_CHECKBOX, self.onTransferCheck)
        
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
            dateTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.onDateEnter)
            
        Publisher.subscribe(self.onAccountChanged, "view.account changed")
        
    def onRecurringCheck(self, event):
        self.toggleVisibilityOf(self.recurringPanel, self.recursCheck.IsChecked())

    def onTransferCheck(self, event):
        self.toggleVisibilityOf(self.transferPanel, self.transferCheck.IsChecked())
        
    def toggleVisibilityOf(self, control, visibility):
        self.Parent.Freeze()
        self.Sizer.Show(control, visibility)
        self.Parent.Layout()
        self.Parent.Thaw()
        
    def onDateEnter(self, event):
        # Force a focus-out/tab to work around LP #311934
        self.dateCtrl.Navigate()
        self.onNewTransaction()
        
    def onAccountChanged(self, message):
        account = message.data
        self.CurrentAccount = account
        self.transferPanel.Update(account)

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
            amount = self.CurrentAccount.ParseAmount(amount)
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

    def onNewTransaction(self, event=None):
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

        sourceAccount = None
        if isTransfer:
            sourceAccount, destAccount = self.transferPanel.GetAccounts(destAccount)
            
        destAccount.AddTransaction(amount, desc, date, sourceAccount)
        self.onSuccess()


    def onTransferTip(self, event):
        tipStr = _("If this box is checked when adding a transaction, you will be prompted for the account to use as the source of the transfer.")+"\n\n"+\
                 _("For example, checking this box and entering a transaction of $50 into this account will also subtract $50 from the account that you choose as the source.")
        wx.TipWindow(self, tipStr, maxLength=200)

    def onSuccess(self):
        # Reset the controls.
        self.descCtrl.Value = ''
        self.amountCtrl.Value = ''
