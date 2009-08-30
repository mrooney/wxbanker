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
import bankcontrols, helpers
import localization, gettext
from wx.lib.pubsub import Publisher

class RecurringSummaryText(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(wx.BLACK)

        self.contentPanel = wx.Panel(self)
        self.contentPanel.SetBackgroundColour(wx.Color(224,238,238))
        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(self.contentPanel, 1, wx.EXPAND|wx.ALL, 1)

        self.summaryText = wx.StaticText(self.contentPanel)
        self.contentPanel.Sizer = wx.BoxSizer()
        self.contentPanel.Sizer.Add(self.summaryText, 0, wx.ALIGN_CENTER|wx.ALL, 2)

    def SetLabel(self, text):
        self.summaryText.Label = text

class TransferPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.accountDict = {}
        self.nullChoice = ["----------"]

        self.fromtoBox = wx.Choice(self, choices=[_("from"), _("to")])
        self.accountSelection = wx.Choice(self, choices=self.nullChoice)

        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(wx.StaticText(self, label=_("Transfer")), flag=wx.ALIGN_CENTER)
        self.Sizer.AddSpacer(3)
        self.Sizer.Add(self.fromtoBox, flag=wx.ALIGN_CENTER)
        self.Sizer.AddSpacer(8)
        self.Sizer.Add(wx.StaticText(self, label=_("account:")), flag=wx.ALIGN_CENTER)
        self.Sizer.AddSpacer(3)
        self.Sizer.Add(self.accountSelection, flag=wx.ALIGN_CENTER)

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

    def Update(self, selectedAccount):
        if selectedAccount:
            self.accountDict = {}
            for account in selectedAccount.GetSiblings():
                self.accountDict[account.Name] = account
            choices = self.accountDict.keys()
        else:
            choices = self.nullChoice

        # Update the choices, and make sure to sort them!
        self.accountSelection.SetItems(sorted(choices))


class RecurringPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        # The daily option is useful if you have something which happens every 30 days, for example.
        # Some billing cycles work this way, and the date slowly shifts down monthly.
        self.repeatsCombo = wx.Choice(self, choices=(_("Daily"), _("Weekly"), _("Monthly"), _("Yearly")))
        # Set the default to weekly.
        self.repeatsCombo.SetSelection(1)

        self.everyText = wx.StaticText(self)
        self.everySpin = wx.SpinCtrl(self, min=1, max=130, initial=1)
        self.everySpin.MinSize = (50, -1)
        self.repeatsOnText = wx.StaticText(self)
        self.endDateCtrl = bankcontrols.DateCtrlFactory(self)
        self.endsNeverRadio = wx.RadioButton(self, label=_("Never"), style=wx.RB_GROUP)
        self.endsSometimeRadio = wx.RadioButton(self, label=("On:"))

        # Make 'Never' the default.
        self.endsNeverRadio.SetValue(True)
        self.endDateCtrl.Value += wx.DateSpan(days=-1, years=1)

        self.repeatsOnChecksWeekly = []
        self.repeatsOnSizerWeekly = wx.BoxSizer()
        today = datetime.date.today().weekday()
        days = (_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun"))
        for i, label in enumerate(days):
            cb = wx.CheckBox(self, label=label)
            cb.SetValue(i==today)
            self.repeatsOnChecksWeekly.append(cb)
            self.repeatsOnSizerWeekly.Add(cb, 0, wx.ALIGN_CENTER|wx.LEFT, 5)

        # The vertical sizer for when the recurring transaction stops ocurring.
        endsSizer = wx.BoxSizer(wx.VERTICAL)
        endsDateSizer = wx.BoxSizer()
        endsSizer.Add(self.endsNeverRadio)
        endsDateSizer.Add(self.endsSometimeRadio)
        endsDateSizer.Add(self.endDateCtrl)
        endsSizer.Add(endsDateSizer)

        # The control which will summarize the recurring transaction
        self.summaryCtrl = RecurringSummaryText(self)

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
        self.topSizer.Add(wx.StaticText(self, label=_("Ends:")), flag=wx.ALIGN_CENTER)
        self.topSizer.AddSpacer(3)
        self.topSizer.Add(endsSizer)

        #self.bottomSizer.AddSpacer(10)
        self.bottomSizer.Add(self.repeatsOnText, flag=wx.ALIGN_CENTER)
        self.bottomSizer.Add(self.repeatsOnSizerWeekly, flag=wx.ALIGN_CENTER)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.topSizer)
        self.Sizer.AddSpacer(3)
        self.Sizer.Add(self.bottomSizer)
        self.Sizer.AddSpacer(3)
        self.Sizer.Add(self.summaryCtrl, 0, wx.ALIGN_CENTER)

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
        self.Sizer.Hide(self.bottomSizer)

        repeatType, every, repeatsOn, end = self.GetSettings()
        summary = "Summary"
        if repeatType == 0:
            everyText = gettext.ngettext("day", "days",every)
            summary = gettext.ngettext("Daily", "Every %(num)d days", every) % {'num':every} 
        elif repeatType == 1:
            everyText = gettext.ngettext("week", "weeks", every)
            self.repeatsOnText.Label = label=_("Repeats on days:")
            self.Sizer.Show(self.bottomSizer)
            if repeatsOn == [1,1,1,1,1,0,0]:
                summary = _("Weekly on weekdays")
            elif repeatsOn == [0,0,0,0,0,1,1]:
                summary = _("Weekly on weekends")
            elif repeatsOn == [1,1,1,1,1,1,1]:
                summary = _("Daily")
            else:
                pluralDayNames = (_("Mondays"), _("Tuesdays"), _("Wednesdays"), _("Thursdays"), _("Fridays"), _("Saturdays"), _("Sundays"))
                repeatDays = tuple(day for i, day in enumerate(pluralDayNames) if repeatsOn[i])
                if len(repeatDays) == 0:
                    summary = "Never"
                elif len(repeatDays) == 1:
                    summary = _("Weekly on %s") % repeatDays[0]
                else:
                    summary = _("Weekly on %s") % ((", ".join(repeatDays[:-1])) + (_(" and %s") % repeatDays[-1]))
        elif repeatType == 2:
            everyText = gettext.ngettext("month", "months", every)
            summary = gettext.ngettext("Monthly", "Every %(num)d months", every) % {'num':every} 
        elif repeatType == 3:
            everyText = gettext.ngettext("year", "years", every)
            summary = gettext.ngettext("Annually", "Every %(num)d years", every) % {'num':every} 

        # If the recurring ends at some point, add that information to the summary text.
        if end:
            summary += " " + _("until %s") % end.FormatISODate()

        self.everyText.Label = everyText
        self.summaryCtrl.SetLabel(summary)

        self.Thaw()
        self.Parent.Parent.Layout()

class NewTransactionCtrl(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.CurrentAccount = None

        self.dateCtrl = dateCtrl = bankcontrols.DateCtrlFactory(self)
        self.startText = wx.StaticText(self, label=_("Starts:"))

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
        
        # Checkboxes seem to have an overly large horizontal margin that looks bad.
        for check in (self.transferCheck, self.recursCheck):
            x, y = check.BestSize
            check.SetMinSize((x, y-4))

        # Set up the layout.
        hSizer = wx.BoxSizer()
        hSizer.Add(self.startText, flag=wx.ALIGN_CENTER)
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

        self.startText.Hide()
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

    def onRecurringCheck(self, event=None):
        recurring = self.recursCheck.IsChecked()
        self.toggleVisibilityOf(self.recurringPanel, recurring)
        self.startText.Show(recurring)

    def onTransferCheck(self, event=None):
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

            dlg = wx.MessageDialog(self,
                                baseStr + " " + _("Please enter a number such as 12.34 or -20."),
                                _("Invalid Transaction Amount"), wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            return

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
            result = self.transferPanel.GetAccounts(destAccount)
            if result is None:
                dlg = wx.MessageDialog(self,
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
            self.onSuccess()
        else:
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
        self.transferCheck.Value = False
        self.recursCheck.Value = False
        self.onTransferCheck()
        self.onRecurringCheck()
