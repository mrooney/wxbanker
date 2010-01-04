#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    guitests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

class GUITests(testbase.TestCaseHandlingConfig):
    def setUp(self):
        testbase.TestCaseHandlingConfig.setUp(self)
        if not hasattr(wx, "appInst"):
            wx.appInst = main.init(":memory:", welcome=False)
        self.App = wx.appInst
        self.Frame = self.App.TopWindow
        self.Model = self.Frame.Panel.bankController.Model
        self.OLV = self.Frame.Panel.managePanel.transactionPanel.transactionCtrl
        
    def tearDown(self):
        for account in self.Model.Accounts[:]:
            self.Model.RemoveAccount(account.Name)
        # Clear out any state of the NTC.
        wx.FindWindowByName("NewTransactionCtrl").clear()

    def testAutoSaveSetAndSaveDisabled(self):
        self.assertTrue( self.Frame.MenuBar.autoSaveMenuItem.IsChecked() )
        self.assertFalse( self.Frame.MenuBar.saveMenuItem.IsEnabled() )

    def testAppHasController(self):
        self.assertTrue( hasattr(self.App, "Controller") )

    def testCanAddAndRemoveUnicodeAccount(self):
        self.Model.CreateAccount(u"Lópezहिंदी")
        # Make sure the account ctrl has the first (0th) selection.
        managePanel = self.Frame.Panel.managePanel
        self.assertEqual(0, wx.FindWindowByName("AccountListCtrl").currentIndex)
        # Mock out the account removal dialog in-place to just return "Yes"
        managePanel.accountCtrl.showModal = lambda *args, **kwargs: wx.ID_YES
        # Now remove the account and make sure there is no selection.
        managePanel.accountCtrl.onRemoveButton(None)
        self.assertEqual(None, managePanel.accountCtrl.currentIndex)

    def testCanAddTransaction(self):
        tctrl = wx.FindWindowByName("NewTransactionCtrl")
        a = self.Model.CreateAccount("testCanAddTransaction")

        self.assertEquals(len(a.Transactions), 0)
        self.assertEquals(a.Balance, 0)

        tctrl.amountCtrl.Value = "12.34"
        tctrl.onNewTransaction()

        self.assertEquals(len(a.Transactions), 1)
        self.assertEquals(a.Balance, 12.34)
        
    def testCanAddRecurringTransaction(self):
        model = self.Model
        tctrl = wx.FindWindowByName("NewTransactionCtrl")
        a = model.CreateAccount("testCanAddRecurringTransaction")

        self.assertEquals(len(a.Transactions), 0)
        self.assertEquals(a.Balance, 0)

        tctrl.amountCtrl.Value = "12.34"
        tctrl.recursCheck.Value = True
        
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
        
        tctrl.onNewTransaction()

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
        
        wx.FindWindowByName("AccountListCtrl").SelectItem(None)
        
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
        

if __name__ == "__main__":
    unittest.main()
