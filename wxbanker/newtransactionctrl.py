#    https://launchpad.net/wxbanker
#    newtransactionctrl.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

from wxbanker import bankcontrols, bankobjects, helpers, localization
import gettext

class TransferRow(bankcontrols.GBRow):
    def __init__(self, parent, row):
        bankcontrols.GBRow.__init__(self, parent, row)
        self.accountDict = {}
        self.nullChoice = ["----------"]

        self.fromtoBox = wx.Choice(parent, choices=[_("from"), _("to")])
        self.accountSelection = wx.Choice(parent, choices=[])
        
        hSizer = wx.BoxSizer()
        hSizer.Add(wx.StaticText(parent, label=_("Transfer")), flag=wx.ALIGN_CENTER_VERTICAL)
        hSizer.AddSpacer(3)
        hSizer.Add(self.fromtoBox, flag=wx.ALIGN_CENTER_VERTICAL)

        self.AddNext(hSizer)
        self.AddNext(self.accountSelection)
        
        Publisher.subscribe(self.onAccountChanged, "view.account changed")
        
    def GetSelectedAccount(self):
        stringSel = self.accountSelection.GetStringSelection()
        if stringSel == "":
            return None

        return self.accountDict[stringSel]

    def GetAccounts(self, currentAccount):
        otherAccount = self.GetSelectedAccount()
        
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
            
    def FromRecurring(self, rt):
        self.fromtoBox.Disable()
        self.Update(rt.Parent)
        if rt.Source:
            self.accountSelection.SetStringSelection(rt.Source.Name)
            
    def ToRecurring(self, rt):
        if self.Parent.IsTransfer():
            rt.Source = self.GetSelectedAccount()
        else:
            rt.Source = None


class RecurringRow(bankcontrols.GBRow):
    def __init__(self, parent, row):
        bankcontrols.GBRow.__init__(self, parent, row, name="RecurringPanel")

        # The daily option is useful if you have something which happens every 30 days, for example.
        # Some billing cycles work this way, and the date slowly shifts down monthly.
        self.repeatsCombo = wx.Choice(parent, choices=(_("Daily"), _("Weekly"), _("Monthly"), _("Yearly")))
        # Set the default to weekly.
        self.repeatsCombo.SetSelection(1)

        self.everyText = wx.StaticText(parent)
        self.everySpin = wx.SpinCtrl(parent, min=1, max=130, initial=1)
        self.everySpin.MinSize = (50, -1)
        bankcontrols.fixMinWidth(self.everyText, (_(x) for x in ("days", "weeks", "months", "years")))
        self.endDateCtrl = bankcontrols.DateCtrlFactory(parent)
        self.endsNeverRadio = wx.RadioButton(parent, label=_("Never"), style=wx.RB_GROUP)
        self.endsSometimeRadio = wx.RadioButton(parent, label=("On:"), name="EndsSometimeRadio")

        # Make 'Never' the default.
        self.endsNeverRadio.SetValue(True)
        self.ResetEndDate()

        # The vertical sizer for when the recurring transaction stops ocurring.
        endsSizer = wx.BoxSizer(wx.VERTICAL)
        endsSizer.Add(self.endsNeverRadio)
        endsDateSizer = wx.BoxSizer()
        endsDateSizer.Add(self.endsSometimeRadio)
        endsDateSizer.Add(self.endDateCtrl)
        endsSizer.Add(endsDateSizer)

        # Create the sizer for the "Every" column and "End".
        # This all is best as one item which spans the last two cols, otherwise the
        # description column will be forced to be too wide in a small width window.
        everySizer = wx.BoxSizer()
        everySizer.Add(self.repeatsCombo, flag=wx.ALIGN_CENTER)
        everySizer.AddSpacer(10)
        everySizer.Add(wx.StaticText(parent, label=_("every")), flag=wx.ALIGN_CENTER)
        everySizer.AddSpacer(3)
        everySizer.Add(self.everySpin, flag=wx.ALIGN_CENTER)
        everySizer.AddSpacer(3)
        everySizer.Add(self.everyText, flag=wx.ALIGN_CENTER)
        everySizer.Add(wx.StaticText(parent, label=_("Ends:")), flag=wx.ALIGN_CENTER)
        everySizer.AddSpacer(3)
        everySizer.Add(endsSizer)
        
        # Add all the columns
        self.AddNext(wx.StaticText(parent, label=_("Repeats:")))
        self.AddNext(everySizer, span=(1,2))
        
        self.everySpin.Bind(wx.EVT_SPINCTRL, self.Update)
        self.repeatsCombo.Bind(wx.EVT_CHOICE, self.Update) # Don't generically bind to the parent, the transfer is a choice too.
        parent.Bind(wx.EVT_CHECKBOX, self.Update)
        parent.Bind(wx.EVT_RADIOBUTTON, self.Update)
        
    def ResetEndDate(self):
        self.endDateCtrl.Value = wx.DateTime.Today() + wx.DateSpan(days=-1, years=1)

    def GetSettings(self):
        repeatType = self.repeatsCombo.GetSelection()
        repeatEvery = self.everySpin.GetValue()

        if self.endsNeverRadio.GetValue():
            end = None
        else:
            end = helpers.wxdate2pydate(self.endDateCtrl.GetValue())
        

        return repeatType, repeatEvery, end

    def Update(self, event=None):
        self.Freeze()
        self.Parent.ShowWeekly(False)

        repeatType, every, end = self.GetSettings()
        if repeatType == 0:
            everyText = gettext.ngettext("day", "days",every)
        elif repeatType == 1:
            everyText = gettext.ngettext("week", "weeks", every)
            self.Parent.ShowWeekly(True)
        elif repeatType == 2:
            everyText = gettext.ngettext("month", "months", every)
        elif repeatType == 3:
            everyText = gettext.ngettext("year", "years", every)

        self.ToRecurring()
        self.everyText.Label = everyText
        
        self.Parent.UpdateSummary()

        self.Thaw()
        self.Parent.Parent.Layout()
        
    def FromRecurring(self, rt):
        """Given a RecurringTransaction, make our settings mirror it."""
        self.repeatsCombo.SetSelection(rt.RepeatType)
        self.everySpin.SetValue(rt.RepeatEvery)
        
        end = rt.EndDate
        if end:
            self.endsSometimeRadio.SetValue(True)
            self.endDateCtrl.SetValue(helpers.pydate2wxdate(end))
        else:
            self.ResetEndDate()
            self.endsNeverRadio.SetValue(True)
            
        self.Update()
    
    def ToRecurring(self):
        """Given a RecurringTransaction, make it equivalent to the settings here."""
        repeatType, repeatEvery, repeatsOn, end = self.Parent.GetSettings()
        self.Parent.recurringObj.Update(repeatType, repeatEvery, repeatsOn, end)
        

class WeeklyRecurringRow(bankcontrols.GBRow):
    def __init__(self, parent, row):
        bankcontrols.GBRow.__init__(self, parent, row)
        
        self.repeatsOnChecksWeekly = []
        self.repeatsOnSizerWeekly = wx.BoxSizer()
        today = datetime.date.today().weekday()
        days = (_("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat"), _("Sun"))
        for i, label in enumerate(days):
            cb = wx.CheckBox(parent, label=label)
            cb.SetValue(i==today)
            self.repeatsOnChecksWeekly.append(cb)
            self.repeatsOnSizerWeekly.Add(cb, 0, wx.ALIGN_CENTER|wx.LEFT, 5)
            
        self.AddNext(wx.StaticText(parent, label=_("Repeats on days:")))
        self.AddNext(self.repeatsOnSizerWeekly, span=(1,2))
        
    def GetSettings(self):
        repeatsOn = [int(check.Value) for check in self.repeatsOnChecksWeekly]
        return repeatsOn
    
    def SetCheck(self, i, value):
        self.repeatsOnChecksWeekly[i].Value = value
    
    def FromRecurring(self, rt):
        if rt.IsWeekly():
            for i, value in enumerate(rt.RepeatOn):
                self.SetCheck(i, value)


class NewTransactionRow(bankcontrols.GBRow):
    def __init__(self, parent, row, editing=None):
        bankcontrols.GBRow.__init__(self, parent, row, name="NewTransactionCtrl")
        self.CurrentAccount = editing
        self.isInitialAccountSet = False

        self.dateCtrl = bankcontrols.DateCtrlFactory(parent)
        self.startText = wx.StaticText(parent, label=_("Starts:"))

        # The Description and Amount controls.
        handler = self.dateCtrl.customKeyHandler
        self.descCtrl = bankcontrols.HintedTextCtrl(parent, size=(140, -1), style=wx.TE_PROCESS_ENTER, hint=_("Description"), icon="wxART_page_edit", handler=handler)
        self.amountCtrl = bankcontrols.HintedTextCtrl(parent, size=(90, -1), style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT, hint=_("Amount"), icon="wxART_money_dollar", handler=handler)
        
        # The add button.
        self.newButton = bankcontrols.FlashableButton(parent, bitmap=wx.ArtProvider.GetBitmap('wxART_money_add'))
        self.newButton.SetToolTipString(_("Enter this transaction"))

        checkSizer = wx.BoxSizer(wx.VERTICAL)
        
        # The transfer check.
        self.transferCheck = wx.CheckBox(parent, label=_("Transfer"))
        checkSizer.Add(self.transferCheck, 0, wx.RIGHT, 6)
        
        # The recurs check.
        self.recursCheck = wx.CheckBox(parent, label=_("Recurring"))
        checkSizer.Add(self.recursCheck, 0, wx.RIGHT, 6)
    
        # If we are editing, it is inherently a recurring transaction.
        if editing:
            self.recursCheck.Hide()

        # Checkboxes seem to have an overly large horizontal margin that looks bad.
        for check in (self.transferCheck, self.recursCheck):
            x, y = check.BestSize
            check.SetMinSize((x, y-4))

        # Set up the layout.
        dateSizer = wx.BoxSizer()
        dateSizer.Add(self.startText, flag=wx.ALIGN_CENTER)
        dateSizer.Add(wx.StaticBitmap(parent, bitmap=wx.ArtProvider.GetBitmap('wxART_date')), 0, wx.ALIGN_CENTER|wx.RIGHT, 2)
        dateSizer.Add(self.dateCtrl, flag=wx.ALIGN_CENTER|wx.EXPAND)
        self.startText.Hide()
        
        hSizer = wx.BoxSizer()
        hSizer.Add(self.amountCtrl, 0, wx.ALIGN_CENTER)
        hSizer.AddSpacer(5)
        hSizer.Add(self.newButton, 0, wx.ALIGN_CENTER)
        hSizer.AddSpacer(5)
        hSizer.Add(checkSizer, 0, wx.ALIGN_CENTER)
        
        descSizer = wx.BoxSizer()
        descSizer.Add(self.descCtrl, 1, flag=wx.ALIGN_CENTER)
        
        self.AddNext(dateSizer)
        self.AddNext(descSizer, flag=wx.EXPAND)
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
            pass
        else:
            # Bind to DateCtrl Enter (LP: 252454).
            dateTextCtrl.WindowStyleFlag |= wx.TE_PROCESS_ENTER
            dateTextCtrl.Bind(wx.EVT_TEXT_ENTER, self.onDateEnter)
            
        Publisher.subscribe(self.onAccountChanged, "view.account changed")
        wx.CallLater(50, self.initialFocus)

    def onRecurringCheck(self, event=None):
        Publisher.sendMessage("newtransaction.%i.recurringtoggled"%id(self), self.recursCheck.IsChecked())
        ##self.startText.Show(recurring) #WXTODO: perhaps remove startText?

    def onTransferCheck(self, event=None):
        Publisher.sendMessage("newtransaction.%i.transfertoggled"%id(self), self.transferCheck.IsChecked())

    def onDateEnter(self, event):
        # Force a focus-out/tab to work around LP #311934.
        self.dateCtrl.Navigate()
        self.onNewTransaction()

    def onAccountChanged(self, message):
        account = message.data
        self.CurrentAccount = account

        # Flash the add transaction button if there are no transactions in this account.
        # We could see if there are siblings, but they might not have transactions either.
        if account and not account.Transactions:
            self.newButton.StartFlashing()
            # For a new account, set the description to "Initial balance" as a suggestion/hint (LP: #520285)
            self.descCtrl.UpdateValue(_("Initial balance"))
        else:
            self.newButton.StopFlashing()
            
        # Reset the focus assuming an account was selected; otherwise the new focus can't be acted on.
        if self.isInitialAccountSet:
            # Also, don't focus if the transaction tab isn't being viewed, otherwise it snaps us back from viewing graphs.
            if account and self.Parent.IsShownOnScreen():
                self.defaultFocus()
        else:
            self.isInitialAccountSet = True

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

        # If a search is active, we have to ask the user what they want to do.
        if self.Parent.Parent.searchActive:
            msg = _("A search is currently active.") + " " + _('Would you like to clear the current search and make this transaction in "%s"?') % (destAccount.Name)
            dlg = wx.MessageDialog(self.Parent, msg, _("Clear search?"), style=wx.YES_NO|wx.ICON_WARNING)
            result = dlg.ShowModal()
            if result == wx.ID_YES:
                Publisher.sendMessage("SEARCH.CANCELLED")
            else:
                return

        sourceAccount = None
        # If the transfer box is checked, this is a transfer!
        if self.transferCheck.Value:
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
            settings = self.Parent.GetSettings()
            args = [amount, desc, date] + list(settings) + [sourceAccount]
            destAccount.AddRecurringTransaction(*args)
        else:
            destAccount.AddTransaction(amount, desc, date, sourceAccount)
            
        # A transaction was added, we can stop flashing if we were.
        self.newButton.StopFlashing()
        
        # Reset the controls and focus to their default values.
        self.clear()
        
    def FromRecurring(self, rt):
        self.descCtrl.Value = rt.Description
        self.amountCtrl.Value = "%.2f" % rt.Amount
        self.dateCtrl.Value = helpers.pydate2wxdate(rt.Date)
        self.transferCheck.Value = bool(rt.Source)
        
    def ToRecurring(self, rt):
        result = self.getValues()
        if result:
            amount, desc, date = result
            rt.Amount, rt.Description, rt.Date = amount, desc, date

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
        self.defaultFocus()
        
    def initialFocus(self):
        """Set the focus to what it should be when initially starting the application."""
        self.dateCtrl.SetFocus()
        
    def defaultFocus(self):
        # Give focus to the description ctrl so the user can enter another transaction.
        # By default a focus will select the field, but that's annoying in this case, so restore the state.
        preSelection = self.descCtrl.GetSelection()
        self.descCtrl.SetFocus()
        self.descCtrl.SetSelection(*preSelection)
