#    https://launchpad.net/wxbanker
#    newtransactionctrl.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
from wx.lib.pubsub import Publisher

import bankcontrols, bankobjects, helpers
import localization, gettext
from bankobjects.recurringtransaction import RecurringTransaction

class TransferRow(bankcontrols.GBRow):
    def __init__(self, parent, row):
        bankcontrols.GBRow.__init__(self, parent, row)
        self.accountDict = {}
        self.nullChoice = ["----------"]

        self.fromtoBox = wx.Choice(parent, choices=[_("from"), _("to")])
        self.accountSelection = wx.Choice(parent, choices=[])

        self.AddNext(wx.StaticText(parent, label=_("Transfer")))
        self.AddNext(self.fromtoBox)
        self.AddNext(self.accountSelection, span=wx.GBSpan(1,2))
        
        Publisher.subscribe(self.onAccountChanged, "view.account changed")

    def GetAccounts(self, currentAccount):
        stringSel = self.accountSelection.GetStringSelection()
        if stringSel == "":
            return None

        otherAccount = self.accountDict[stringSel]
        if self.fromtoBox.Selection == 0:
            source, destination = otherAccount, currentAccount
        else:
            source, destination = currentAccount, otherAccount

        return source, destination
    
    def onAccountChanged(self, message):
        account = message.data
        self.Update(account)

    def Update(self, selectedAccount):
        if selectedAccount:
            self.accountDict = {}
            for account in selectedAccount.GetSiblings():
                self.accountDict[account.Name] = account
            choices = self.accountDict.keys()
        else:
            choices = self.nullChoice

        # Update the choices, and make sure to sort them!
        choices.sort()
        self.accountSelection.SetItems(choices)
        # If there are choices, select the first one by default.
        if choices:
            self.accountSelection.SetSelection(0)


class RecurringRow(bankcontrols.GBRow):
    def __init__(self, parent, row):
        bankcontrols.GBRow.__init__(self, parent, row, name="RecurringPanel")

        # The daily option is useful if you have something which happens every 30 days, for example.
        # Some billing cycles work this way, and the date slowly shifts down monthly.
        self.repeatsCombo = wx.Choice(parent, choices=(_("Daily"), _("Weekly"), _("Monthly"), _("Yearly")))
        # Set the default to weekly.
        self.repeatsCombo.SetSelection(1)
        # Create the recurring object we will use internally.
        self.recurringObj = RecurringTransaction(None, None, 0, "", datetime.date.today(), RecurringTransaction.DAILY)

        self.everyText = wx.StaticText(parent)
        self.everySpin = wx.SpinCtrl(parent, min=1, max=130, initial=1)
        self.everySpin.MinSize = (50, -1)
        ##self.repeatsOnText = wx.StaticText(parent) #TODO: put it new row
        bankcontrols.fixMinWidth(self.everyText, (_(x) for x in ("days", "weeks", "months", "years")))
        self.endDateCtrl = bankcontrols.DateCtrlFactory(parent)
        self.endsNeverRadio = wx.RadioButton(parent, label=_("Never"), style=wx.RB_GROUP)
        self.endsSometimeRadio = wx.RadioButton(parent, label=("On:"), name="EndsSometimeRadio")

        # Make 'Never' the default.
        self.endsNeverRadio.SetValue(True)
        self.endDateCtrl.Value += wx.DateSpan(days=-1, years=1)

        self.repeatsOnChecksWeekly = []
        self.repeatsOnSizerWeekly = wx.BoxSizer()
        today = datetime.date.today().weekday()
        days = (_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun"))
        for i, label in enumerate(days):
            cb = wx.CheckBox(parent, label=label)
            cb.SetValue(i==today)
            self.repeatsOnChecksWeekly.append(cb)
            self.repeatsOnSizerWeekly.Add(cb, 0, wx.ALIGN_CENTER|wx.LEFT, 5)
            cb.Hide() ##TODO: these need to be in a new row

        # The vertical sizer for when the recurring transaction stops ocurring.
        endsSizer = wx.BoxSizer(wx.VERTICAL)
        endsSizer.Add(self.endsNeverRadio)
        endsDateSizer = wx.BoxSizer()
        endsDateSizer.Add(self.endsSometimeRadio)
        endsDateSizer.Add(self.endDateCtrl)
        endsSizer.Add(endsDateSizer)

        # Create the sizer for the "Every" column
        everySizer = wx.BoxSizer()
        everySizer.Add(wx.StaticText(parent, label=_("Every")), flag=wx.ALIGN_CENTER)
        everySizer.AddSpacer(3)
        everySizer.Add(self.everySpin, flag=wx.ALIGN_CENTER)
        everySizer.AddSpacer(3)
        everySizer.Add(self.everyText, flag=wx.ALIGN_CENTER)
        
        # Create the sizer for the "Ends" column
        endsHSizer = wx.BoxSizer()
        endsHSizer.Add(wx.StaticText(parent, label=_("Ends:")), flag=wx.ALIGN_CENTER)
        endsHSizer.AddSpacer(3)
        endsHSizer.Add(endsSizer)
        
        # Add all the columns
        self.AddNext(wx.StaticText(parent, label=_("Repeats:")))
        self.AddNext(self.repeatsCombo)
        self.AddNext(everySizer)
        self.AddNext(endsHSizer)
        
        self.Update()
        #self.repeatsCombo.Bind(wx.EVT_CHOICE, self.Update)
        self.everySpin.Bind(wx.EVT_SPINCTRL, self.Update)
        self.Bind(wx.EVT_CHOICE, self.Update)
        self.Bind(wx.EVT_CHECKBOX, self.Update)
        self.Bind(wx.EVT_RADIOBUTTON, self.Update)

    def GetSettings(self):
        repeatType = self.repeatsCombo.GetSelection()
        repeatEvery = self.everySpin.GetValue()

        if self.endsNeverRadio.GetValue():
            end = None
        else:
            end = helpers.wxdate2pydate(self.endDateCtrl.GetValue())

        repeatsOn = None
        if repeatType == 1: # Weekly
            repeatsOn = [int(check.Value) for check in self.repeatsOnChecksWeekly]

        return (repeatType, repeatEvery, repeatsOn, end)

    def Update(self, event=None):
        self.Freeze()
        ##self.Sizer.Hide(self.bottomSizer)

        repeatType, every, repeatsOn, end = self.GetSettings()
        if repeatType == 0:
            everyText = gettext.ngettext("day", "days",every)
        elif repeatType == 1:
            everyText = gettext.ngettext("week", "weeks", every)
            ##self.repeatsOnText.Label = label =_("Repeats on days:")
            ##self.Sizer.Show(self.bottomSizer)
        elif repeatType == 2:
            everyText = gettext.ngettext("month", "months", every)
        elif repeatType == 3:
            everyText = gettext.ngettext("year", "years", every)

        self.ToRecurring(self.recurringObj)
        summary = self.recurringObj.GetRecurrance()
            
        self.everyText.Label = everyText
        ##self.summaryCtrl.SetLabel(summary)

        self.Thaw()
        self.Parent.Parent.Layout()
        
    def FromRecurring(self, recurringObj):
        """Given a RecurringTransaction, make our settings mirror it."""
        pass
    
    def ToRecurring(self, recurringObj):
        """Given a RecurringTransaction, make it equivalent to the settings here."""
        repeatType, repeatEvery, repeatsOn, end = self.GetSettings()
        recurringObj.Update(repeatType, repeatEvery, repeatsOn, end)

class NewTransactionRow(bankcontrols.GBRow):
    def __init__(self, parent, row):
        bankcontrols.GBRow.__init__(self, parent, row, name="NewTransactionCtrl")
        self.CurrentAccount = None

        self.dateCtrl = bankcontrols.DateCtrlFactory(parent)
        self.startText = wx.StaticText(parent, label=_("Starts:"))

        # The Description and Amount controls.
        self.descCtrl = bankcontrols.HintedTextCtrl(parent, size=(140, -1), style=wx.TE_PROCESS_ENTER, hint=_("Description"), icon="wxART_page_edit")
        self.amountCtrl = bankcontrols.HintedTextCtrl(parent, size=(90, -1), style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT, hint=_("Amount"), icon="wxART_money_dollar")

        # The add button.
        self.newButton = wx.BitmapButton(parent, bitmap=wx.ArtProvider.GetBitmap('wxART_money_add'))
        self.newButton.SetToolTipString(_("Enter this transaction"))

        # The transfer check.
        self.transferCheck = wx.CheckBox(parent, label=_("Transfer"))

        # The recurs check.
        self.recursCheck = wx.CheckBox(parent, label=_("Recurring"))

        checkSizer = wx.BoxSizer(wx.VERTICAL)
        checkSizer.Add(self.transferCheck)
        checkSizer.Add(self.recursCheck)

        # Checkboxes seem to have an overly large horizontal margin that looks bad.
        for check in (self.transferCheck, self.recursCheck):
            x, y = check.BestSize
            check.SetMinSize((x, y-4))

        # Set up the layout.
        dateSizer = wx.BoxSizer()
        dateSizer.Add(self.startText, flag=wx.ALIGN_CENTER)
        dateSizer.Add(wx.StaticBitmap(parent, bitmap=wx.ArtProvider.GetBitmap('wxART_date')), 0, wx.ALIGN_CENTER|wx.ALL, 2)
        dateSizer.Add(self.dateCtrl, flag=wx.ALIGN_CENTER)
        self.startText.Hide()
        
        hSizer = wx.BoxSizer()
        hSizer.Add(self.amountCtrl, 0, wx.ALIGN_CENTER)
        hSizer.AddSpacer(5)
        hSizer.Add(self.newButton, 0, wx.ALIGN_CENTER)
        hSizer.AddSpacer(5)
        hSizer.Add(checkSizer, 0, wx.ALIGN_CENTER)
        
        self.AddNext(dateSizer)
        self.AddNext(self.descCtrl, flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, span=wx.GBSpan(1,2))
        self.descCtrl.SetMaxSize((-1, self.descCtrl.BestSize[1]))
        self.AddNext(hSizer)
        
        # Initialize necessary bindings.
        parent.Bind(wx.EVT_TEXT_ENTER, self.onNewTransaction) # Gives us enter from description/amount.
        self.newButton.Bind(wx.EVT_BUTTON, self.onNewTransaction)
        self.recursCheck.Bind(wx.EVT_CHECKBOX, self.onRecurringCheck)
        self.transferCheck.Bind(wx.EVT_CHECKBOX, self.onTransferCheck)

        try:
            self.amountCtrl.Children[0].Bind(wx.EVT_CHAR, self.onAmountChar)
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

    def onRecurringCheck(self, event=None):
        Publisher.sendMessage("newtransaction.recurringtoggled", self.recursCheck.IsChecked())
        ##self.startText.Show(recurring) #TODO: perhaps remove startText?

    def onTransferCheck(self, event=None):
        Publisher.sendMessage("newtransaction.transfertoggled", self.transferCheck.IsChecked())

    def onDateEnter(self, event):
        # Force a focus-out/tab to work around LP #311934
        self.dateCtrl.Navigate()
        self.onNewTransaction()

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
        date = helpers.wxdate2pydate(self.dateCtrl.Value)
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

            dlg = wx.MessageDialog(self.Parent,
                                baseStr + " " + _("Please enter a number such as 12.34 or -20."),
                                _("Invalid Transaction Amount"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return

        return amount, desc, date

    def onNewTransaction(self, event=None):
        # First, ensure an account is selected.
        destAccount = self.CurrentAccount
        if destAccount is None:
            dlg = wx.MessageDialog(self.Parent,
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
        if self.Parent.Parent.searchActive:
            msg = _("A search is currently active.") + " " + _('Would you like to clear the current search and make this transaction in "%s"?') % (destAccount.Name)
            dlg = wx.MessageDialog(self.Parent, msg, _("Clear search?"), style=wx.YES_NO|wx.ICON_WARNING)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                Publisher().sendMessage("SEARCH.CANCELLED")
            else:
                return

        sourceAccount = None
        if isTransfer:
            result = self.Parent.transferRow.GetAccounts(destAccount)
            if result is None:
                dlg = wx.MessageDialog(self.Parent,
                                       _("This transaction is marked as a transfer. Please select the transfer account."),
                                       _("No account selected"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                return
            sourceAccount, destAccount = result

        # Now let's see if this is a recurring transaction
        if self.recursCheck.GetValue():
            settings = self.recurringPanel.GetSettings()
            args = [amount, desc, date] + list(settings) + [sourceAccount]
            destAccount.AddRecurringTransaction(*args)
        else:
            destAccount.AddTransaction(amount, desc, date, sourceAccount)
        self.clear()


    def onTransferTip(self, event):
        tipStr = _("If this box is checked when adding a transaction, you will be prompted for the account to use as the source of the transfer.")+"\n\n"+\
                 _("For example, checking this box and entering a transaction of $50 into this account will also subtract $50 from the account that you choose as the source.")
        wx.TipWindow(self, tipStr, maxLength=200)

    def clear(self):
        # Reset the controls.
        self.descCtrl.Value = ''
        self.amountCtrl.Value = ''
        self.transferCheck.Value = False
        self.recursCheck.Value = False
        self.onTransferCheck()
        self.onRecurringCheck()
