#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    guitests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

from wxbanker.tests import testbase
from wxbanker import main, controller
import os, wx, unittest
from wx.lib.pubsub import Publisher

class GUITests(testbase.TestCaseHandlingConfigBase):
    def setUp(self):
        testbase.TestCaseHandlingConfigBase.setUp(self)
        if not hasattr(wx, "appInst"):
            wx.appInst = main.init(":memory:", welcome=False)
            
        self.App = wx.appInst
        self.Frame = self.App.TopWindow
        self.Model = self.Frame.Panel.bankController.Model
        self.OLV = wx.FindWindowByName("TransactionOLV")
        self.AccountListCtrl = wx.FindWindowByName("AccountListCtrl")
        self.NewTransactionCtrl = wx.FindWindowByName("NewTransactionCtrl")
        
    def tearDown(self):
        for account in self.Model.Accounts[:]:
            self.Model.RemoveAccount(account.Name)
        # Clear out any state of the NTC.
        self.NewTransactionCtrl.clear()
        testbase.TestCaseHandlingConfigBase.tearDown(self)
        
    def assertCurrentAccount(self, account):
        alc = self.AccountListCtrl.GetCurrentAccount()
        self.assertEqual(alc, account, alc and alc.Name)
        if account is None:
            expectedTransactions = self.Model.GetTransactions()
        else:
            expectedTransactions = account.Transactions
        self.assertEqual(self.OLV.GetObjects(), expectedTransactions)
        self.assertEqual(self.NewTransactionCtrl.CurrentAccount, account)

    def testAutoSaveSetAndSaveDisabled(self):
        self.assertTrue( self.Frame.MenuBar.autoSaveMenuItem.IsChecked() )
        self.assertFalse( self.Frame.MenuBar.saveMenuItem.IsEnabled() )
        
    def testShowZeroEnabled(self):
        self.assertTrue( self.Frame.MenuBar.showZeroMenuItem.IsChecked() )
        
    def testControlFocus(self):
        # This test is only half-useful, because we're testing the methods directly and not
        # that they happen when expected via events; for some reason that doesn't work.
        newCtrl = self.NewTransactionCtrl
        newCtrl.initialFocus()
        self.assertEqual(wx.Window.FindFocus(), newCtrl.dateCtrl)
        newCtrl.defaultFocus()
        self.assertEqual(wx.Window.FindFocus(), newCtrl.descCtrl)
        
    def testKeyboardAccountShortcuts(self):
        model = self.Model
        accountList = self.AccountListCtrl
        
        a = model.CreateAccount("A")
        a.AddTransaction(1)
        b = model.CreateAccount("B")
        b.AddTransaction(2)
        c = model.CreateAccount("C")
        c.AddTransaction(3)
        
        self.assertCurrentAccount(c)
        
        Publisher.sendMessage("user.previous account")
        self.assertCurrentAccount(b)
        
        Publisher.sendMessage("user.previous account")
        self.assertCurrentAccount(a)
        
        Publisher.sendMessage("user.previous account")
        self.assertCurrentAccount(a)
        
        Publisher.sendMessage("user.next account")
        self.assertCurrentAccount(b)
        
        Publisher.sendMessage("user.next account")
        self.assertCurrentAccount(c)
        
        Publisher.sendMessage("user.account changed", None)
        self.assertCurrentAccount(None)
        
        Publisher.sendMessage("user.next account")
        self.assertCurrentAccount(None)
        
        Publisher.sendMessage("user.previous account")
        self.assertCurrentAccount(c)
        
        # Bring "B" to zero, and test that it gets skipped over when not viewing zero balances.
        b.AddTransaction(-2)
        Publisher.sendMessage("user.showzero_toggled", False)

        try:
            Publisher.sendMessage("user.previous account")
            self.assertCurrentAccount(a)
            
            Publisher.sendMessage("user.next account")
            self.assertCurrentAccount(c)
        finally:
            Publisher.sendMessage("user.showzero_toggled", True)
        
    def testToggleShowZero(self):
        # Create two accounts, make sure they are visible.
        a = self.Model.CreateAccount("A")
        b = self.Model.CreateAccount("B")
        b.AddTransaction(1)
        self.assertEqual(self.AccountListCtrl.GetVisibleCount(), 2)
        
        # Disable showing zero balance accounts, make sure the menu item is unchecked and one account is hidden.
        Publisher.sendMessage("user.showzero_toggled", False)
        self.assertFalse( self.Frame.MenuBar.showZeroMenuItem.IsChecked() )
        self.assertEqual(self.AccountListCtrl.GetVisibleCount(), 1)
        
        # Make sure that a balance going to / coming from zero results in a visibility toggle.
        b.AddTransaction(-1)
        self.assertEqual(self.AccountListCtrl.GetVisibleCount(), 0)
        
    def testAppHasController(self):
        self.assertTrue( hasattr(self.App, "Controller") )

    def testCanAddAndRemoveUnicodeAccount(self):
        self.Model.CreateAccount(u"Lópezहिंदी")
        # Make sure the account ctrl has the first (0th) selection.
        mainPanel = self.Frame.Panel.mainPanel
        self.assertEqual(0, self.AccountListCtrl.currentIndex)
        # Mock out the account removal dialog in-place to just return "Yes"
        mainPanel.accountCtrl.showModal = lambda *args, **kwargs: wx.ID_YES
        # Now remove the account and make sure there is no selection.
        mainPanel.accountCtrl.onRemoveButton(None)
        self.assertCurrentAccount(None)
        
    def testInitialBalanceHint(self):
        # Test LP: 520285
        self.assertEqual(self.NewTransactionCtrl.descCtrl.Value, "")
        a = self.Model.CreateAccount("testInitialBalanceHint")
        self.assertEqual(self.NewTransactionCtrl.descCtrl.Value, "Initial balance")

    def testCanAddTransaction(self):
        a = self.Model.CreateAccount("testCanAddTransaction")

        self.assertEquals(len(a.Transactions), 0)
        self.assertEquals(a.Balance, 0)

        self.NewTransactionCtrl.amountCtrl.Value = "12.34"
        self.NewTransactionCtrl.onNewTransaction()

        self.assertEquals(len(a.Transactions), 1)
        self.assertEquals(a.Balance, 12.34)
        
    def testCanAddRecurringTransaction(self):
        model = self.Model
        a = model.CreateAccount("testCanAddRecurringTransaction")

        self.assertEquals(len(a.Transactions), 0)
        self.assertEquals(a.Balance, 0)

        self.NewTransactionCtrl.amountCtrl.Value = "12.34"
        self.NewTransactionCtrl.recursCheck.Value = True
        
        # Test the default of this field, and that it doesn't end.
        summaryText = wx.FindWindowByName("RecurringSummaryText")
        self.assertTrue(summaryText.Label.startswith("Weekly on "))
        self.assertFalse("until" in summaryText.Label)
        
        # Now set an end date and make sure that gets displayed.
        rb = wx.FindWindowByName("EndsSometimeRadio")
        rb.Value = True
        # Setting the value programmatically doesn't trigger an event, so do so.
        wx.FindWindowByName("RecurringPanel").Update()
        self.assertTrue("until" in summaryText.Label)
        
        self.NewTransactionCtrl.onNewTransaction()

        self.assertEquals(len(a.Transactions), 0)
        self.assertEquals(a.Balance, 0)
        self.assertEquals(len(a.RecurringTransactions), 1)
        
    def testCanCheckRecurringTransactions(self):
        self.assertEqual(self.Frame.Panel.CheckRecurringTransactions(), 0)
        a = self.Model.CreateAccount("A")
        rt = a.AddRecurringTransaction(1, "fun", testbase.today, 0)
        self.assertEqual(self.Frame.Panel.CheckRecurringTransactions(), 1)
        
    def testAccountNoneIsAllAccounts(self):
        a = self.Model.CreateAccount("A")
        b = self.Model.CreateAccount("B")
        ta = a.AddTransaction(1)
        tb = b.AddTransaction(2)
        
        # B was added most recently and as such should be selected.
        self.assertEqual(self.OLV.GetObjects(), [tb])
        
        self.AccountListCtrl.SelectItem(None)
        
        # Selecting None should show all transactions.
        self.assertEqual(self.OLV.GetObjects(), [ta, tb])
        
    def testOLVTotals(self):
        """Test the OLV total column works as expected."""
        def totals():
            totals = []
            for i in range(len(self.OLV.GetObjects())):
                totals.append(self.OLV.GetValueAt(self.OLV.GetObjectAt(i), 3))
            return totals
        
        self.assertEqual(len(self.OLV.GetObjects()), 0)
        
        a = self.Model.CreateAccount("B")
        
        # Super basic test, one transaction.
        t1 = a.AddTransaction(1)
        self.assertEqual(totals(), [1])
        
        # Now add one at the end
        t3 = a.AddTransaction(.5, date=testbase.tomorrow)
        self.assertEqual(totals(), [1, 1.5])
        
        # Add one first.
        t2 = a.AddTransaction(2, date=testbase.yesterday)
        self.assertEqual(totals(), [2, 3, 3.5])
        
        # Remove one not at the end.
        a.RemoveTransaction(t2)
        self.assertEqual(t1, self.OLV.GetObjectAt(0))
        self.assertEqual(totals(), [1, 1.5])
        
        # Now change an existing amount.
        t1.Amount = 1.75
        self.assertEqual(totals(), [1.75, 2.25])
        
        # Now change an existing date which should cause a re-order.
        t3.Date = testbase.yesterday
        self.assertEqual(totals(), [0.5, 2.25])
        
    def testSearch(self):
        a = self.Model.CreateAccount("A")
        b = self.Model.CreateAccount("B")
        
        t1 = a.AddTransaction(1, "Cat")
        t2 = a.AddTransaction(1, "Dog")
        t3 = b.AddTransaction(1, "Pig")
        t4 = b.AddTransaction(1, "Dog")
        
        # Ensure b is selected
        self.assertEqual(self.OLV.GetObjects(), [t3, t4])
        
        # Search for dog, make sure b's matching transaction is shown.
        Publisher.sendMessage("SEARCH.INITIATED", ("Dog", 1))
        self.assertEqual(self.OLV.GetObjects(), [t4])
        
        # Change to a, make sure we see a's match.
        Publisher.sendMessage("user.account changed", a)
        self.assertEqual(self.OLV.GetObjects(), [t2])
        
        # Switch to all accounts, make sure we see both matches.
        Publisher.sendMessage("user.account changed", None)
        self.assertEqual(self.OLV.GetObjects(), [t2, t4])


if __name__ == "__main__":
    unittest.main()
