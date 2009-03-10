#    https://launchpad.net/wxbanker
#    managetab.py: Copyright 2007, 2008 Mike Rooney <michael@wxbanker.org>
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

import wx, wx.grid as gridlib
import datetime
import searchctrl, accountlistctrl, newtransactionctrl
from transactionolv import TransactionOLV as TransactionCtrl
from calculator import CollapsableWidget, SimpleCalculator
from wx.lib.pubsub import Publisher
import localization


class ManagePanel(wx.Panel):
    """
    This panel contains the list of accounts on the left
    and the transaction panel on the right.
    """
    def __init__(self, parent, bankController):
        wx.Panel.__init__(self, parent)

        ## Left side, the account list and calculator
        self.leftPanel = leftPanel = wx.Panel(self)
        leftPanel.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.accountCtrl = accountCtrl = accountlistctrl.AccountListCtrl(leftPanel, bankController)
        calcWidget = CollapsableWidget(leftPanel, SimpleCalculator, "Calculator")

        leftPanel.Sizer.Add(accountCtrl, 0, wx.EXPAND)
        leftPanel.Sizer.AddStretchSpacer(1)
        leftPanel.Sizer.Add(calcWidget, 0, wx.EXPAND)

        # Force the calculator widget (and parent) to take on the desired size.
        for widget in [calcWidget.widget, leftPanel]:
            widget.SetMinSize((accountCtrl.BestSize[0], -1))

        ## Right side, the transaction panel:
        self.transactionPanel = transactionPanel = TransactionPanel(self, bankController)

        mainSizer = wx.BoxSizer()
        self.Sizer = mainSizer
        mainSizer.Add(leftPanel, 0, wx.EXPAND|wx.ALL, 5)
        mainSizer.Add(transactionPanel, 1, wx.EXPAND|wx.ALL, 0)

        #subscribe to messages that interest us
        Publisher().subscribe(self.onChangeAccount, "view.account changed")
        Publisher().subscribe(self.onCalculatorToggled, "CALCULATOR.TOGGLED")

        # Select the first account by default, if there are any.
        # Windows needs a delay, to work around LP #339860
        wx.CallLater(50, accountCtrl.SelectVisibleItem, 0)

        self.Layout()

        # Ensure the calculator is displayed as desired.
        calcWidget.SetExpanded(wx.Config.Get().ReadBool("SHOW_CALC"))

    def onCalculatorToggled(self, message):
        """
        Re-layout ourself so the calcWidget always fits properly at the bottom.
        """
        self.leftPanel.Layout()
        shown = message.data == "HIDE" # backwards, HIDE means it is now shown.
        wx.Config.Get().WriteBool("SHOW_CALC", shown)

    def onChangeAccount(self, message):
        account = message.data
        self.transactionPanel.setAccount(account)

    def getCurrentAccount(self):
        return self.accountCtrl.GetCurrentAccount()

    
class TransactionPanel(wx.Panel):
    def __init__(self, parent, bankController):
        wx.Panel.__init__(self, parent)
        self.searchActive = False
        
        subpanel = wx.Panel(self)
        
        self.searchCtrl = searchCtrl = searchctrl.SearchCtrl(self, bankController)
        self.transactionCtrl = transactionCtrl = TransactionCtrl(subpanel, bankController)
        self.newTransCtrl = newTransCtrl = newtransactionctrl.NewTransactionCtrl(self)
        
        subpanel.Sizer = wx.BoxSizer()
        subpanel.Sizer.Add(transactionCtrl, 1, wx.EXPAND)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(searchCtrl, 0, wx.ALIGN_CENTER_HORIZONTAL)
        mainSizer.Add(subpanel, 1, wx.EXPAND)
        mainSizer.Add(newTransCtrl, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.TOP, 5)

        self.Sizer = mainSizer
        mainSizer.Layout()

        ##self.Bind(wx.EVT_SIZE, self.transactionCtrl.doResize)
        for message in ["account.created", "account.removed", "view.account changed"]:
            Publisher().subscribe(self.onSearchInvalidatingChange, message)

    def setAccount(self, *args, **kwargs):
        self.transactionCtrl.setAccount(*args, **kwargs)

    def onSearchInvalidatingChange(self, event):
        """
        Some event has occurred which trumps any active search, so make the
        required changes to state. These events will handle all other logic.
        """
        self.searchActive = False
        #Publisher().sendMessage("SEARCH.CANCELLED")
