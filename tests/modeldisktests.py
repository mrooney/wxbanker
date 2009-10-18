#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    modeldisktests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

import os, unittest
from wx.lib.pubsub import Publisher

import testbase, controller, bankobjects
from bankobjects.recurringtransaction import RecurringTransaction
from testbase import today, tomorrow

class ModelDiskTests(testbase.TestCaseWithControllerOnDisk):
    """
    These are tests which require an actual database on disk.
    Thankfully using PRAGMA synchronous=off makes these still very quick.
    """
    def testAutoSaveDisabledSimple(self):
        self.Controller.AutoSave = False
        self.assertFalse( self.Controller.AutoSave )

        model1 = self.Controller.Model
        a1 = model1.CreateAccount("Checking Account")

        model2 = self.Controller.LoadPath("test.db")

        self.assertNotEqual(model1, model2)
        
    def testAutoSaveDisabledComplex(self):
        model1 = self.Controller.Model
        a1 = model1.CreateAccount("Checking Account")
        t1 = a1.AddTransaction(-10, "Description 1")

        model2 = self.Controller.LoadPath("test.db")
        self.assertEqual(model1, model2)
        self.Controller.Close(model2)

        self.Controller.AutoSave = False
        t2 = a1.AddTransaction(-10, "Description 3")
        model3 = self.Controller.LoadPath("test.db")
        self.assertFalse(model1 is model3)
        self.assertNotEqual(model1, model3)
        self.Controller.Close(model3)

        model1.Save()
        model4 = self.Controller.LoadPath("test.db")
        self.assertEqual(model1, model4)
        self.Controller.Close(model4)

        t1.Description = "Description 2"
        model5 = self.Controller.LoadPath("test.db")
        self.assertNotEqual(model1, model5)

        model1.Save()
        model6 = self.Controller.LoadPath("test.db")
        self.assertEqual(model1, model6)

    def testEnablingAutoSaveSaves(self):
        self.Controller.AutoSave = False
        self.Model.CreateAccount("A")

        # The model has unsaved changes, a new one should be different.
        model2 = self.Controller.LoadPath("test.db")
        self.assertNotEqual(self.Model, model2)
        self.Controller.Close(model2)

        # Setting AutoSave to true should trigger a save.
        self.Controller.AutoSave = True

        # Now a newly loaded should be equal.
        model3 = self.Controller.LoadPath("test.db")
        self.assertEqual(self.Model, model3)
        self.Controller.Close(model3)
        
    def testSaveEventSaves(self):
        self.Controller.AutoSave = False
        model1 = self.Controller.Model

        # Create an account, don't save.
        self.assertEqual(len(model1.Accounts), 0)
        model1.CreateAccount("Hello!")
        self.assertEqual(len(model1.Accounts), 1)

        # Make sure that account doesn't exist on a new model
        model2 = self.Controller.LoadPath("test.db")
        self.assertEqual(len(model2.Accounts), 0)
        self.assertNotEqual(model1, model2)

        # Save
        Publisher.sendMessage("user.saved")

        # Make sure it DOES exist after saving.
        model3 = self.Controller.LoadPath("test.db")
        self.assertEqual(len(model3.Accounts), 1)
        self.assertEqual(model1, model3)
        self.assertNotEqual(model2, model3)
        
    def testModelIsNotCached(self):
        # If this test fails, test*IsStored tests will pass but are no longer testing for regressions!
        model1 = self.Controller.Model
        model2 = model1.Store.GetModel(useCached=False)
        self.assertFalse(model1 is model2)

    def testRenameIsStored(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        a.Name = "B"
        model2 = model1.Store.GetModel(useCached=False)
        self.assertEqual(model2.Accounts[0].Name, "B")
        self.assertEqual(model1, model2)

    def testBalanceIsStored(self):
        model1 = self.Controller.Model
        a1 = model1.CreateAccount("A")
        self.assertEqual(a1.Balance, 0)

        a1.AddTransaction(1)
        self.assertEqual(a1.Balance, 1)
        model2 = model1.Store.GetModel(useCached=False)
        a2 = model2.Accounts[0]
        self.assertEqual(model1, model2)
        self.assertEqual(a1.Balance, a2.Balance)

    def testTransactionChangeIsStored(self):
        model1 = self.Controller.Model
        a1 = model1.CreateAccount("A")

        t1 = a1.AddTransaction(-1.25)

        t1.Description = "new"
        t1.Amount = -1.50
        t1.Date = tomorrow
        
        model2 = model1.Store.GetModel(useCached=False)
        t2 = model2.GetTransactions()[0]
        self.assertEqual(t2.Description, "new")
        self.assertEqual(model1, model2)
        
    def testLinkedTransferIsStored(self):
        a, b, atrans, btrans = self.createLinkedTransfers()
        model1 = self.Controller.Model

        model2 = model1.Store.GetModel(useCached=False)
        
        a2, b2 = model2.Accounts
        self.assertEqual(a2.Name, "A")
        self.assertEqual(b2.Name, "B")
        bt = b2.Transactions[0]
        self.assertEqual(bt.Parent, b)
        self.assertEqual(bt.Parent, b2)
        link = bt.LinkedTransaction
        self.assertEqual(link.Parent, a)
        self.assertEqual(link.Parent, a2)
        self.assertTrue(bt in b2.Transactions)
        self.assertTrue(b2.Transactions[0] is bt)
        self.assertTrue(link in a2.Transactions)
        
    def testRecurringTransactionIsStored(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        a.AddRecurringTransaction(1, "test", today, repeatType=1)
        
        model2 = model1.Store.GetModel(useCached=False)
        self.assertEqual(model1, model2)
        
        repeatOn = model2.GetRecurringTransactions()[0].RepeatOn
        self.assertEqual(len(repeatOn), 7)
        self.assertEqual(sum(repeatOn), 1)
        
    def testRecurringRepeatTypeIsStoredOnUpdate(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        rt = a.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY)
        self.assertEqual(rt.RepeatType, 0)
        rt.RepeatType = 2

        model2 = model1.Store.GetModel(useCached=False)
        rt2 = model2.GetRecurringTransactions()[0]
        self.assertEqual(rt2.RepeatType, 2)
        self.assertEqual(model1, model2)
        
    def testRecurringRepeatEveryIsStoredOnUpdate(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        rt = a.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY)
        self.assertEqual(rt.RepeatEvery, 1)
        rt.RepeatEvery = 2

        model2 = model1.Store.GetModel(useCached=False)
        self.assertEqual(model2.GetRecurringTransactions()[0].RepeatEvery, 2)
        self.assertEqual(model1, model2)
        
    def testRecurringRepeatOnIsStoredOnUpdate(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        rt = a.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY)
        self.assertEqual(rt.RepeatOn, None)
        rt.RepeatOn = [5,6]

        model2 = model1.Store.GetModel(useCached=False)
        self.assertEqual(model2.GetRecurringTransactions()[0].RepeatOn, [5,6])
        self.assertEqual(model1, model2)
        
    def testRecurringEndDateIsStoredOnUpdate(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        rt = a.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY)
        self.assertEqual(rt.EndDate, None)
        rt.EndDate = today

        model2 = model1.Store.GetModel(useCached=False)
        self.assertEqual(model2.GetRecurringTransactions()[0].EndDate, today)
        self.assertEqual(model1, model2)
        
    def testRecurringInheritedPropsAreStoredOnUpdate(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        rt = a.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY)
        self.assertEqual(rt.Amount, 1)
        self.assertEqual(rt.Date, today)
        self.assertEqual(rt.Description, "test")
        
        rt.Amount = 2
        rt.Date = tomorrow
        rt.Description = "new"

        model2 = model1.Store.GetModel(useCached=False)
        t = model2.GetRecurringTransactions()[0]
        self.assertEqual(t.Amount, 2)
        self.assertEqual(t.Date, tomorrow)
        self.assertEqual(t.Description, "new")
        self.assertEqual(model1, model2)
        
    def testRecurringLastUpdatesIsStoredOnUpdate(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        
        rt = a.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY)
        
        self.assertEqual(rt.LastTransacted, None)
        rt.PerformTransactions()
        self.assertEqual(rt.LastTransacted, today)
        
        model2 = model1.Store.GetModel(useCached=False)
        self.assertEqual(model2.GetRecurringTransactions()[0].LastTransacted, today)
        self.assertEqual(model1, model2)
        
    def testRecurringSourceIsStoredOnUpdate(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        b = model1.CreateAccount("B")
        
        rt = a.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY)
        self.assertEqual(rt.Source, None)
        rt.Source = b
        self.assertEqual(rt.Source, b)
        
        model2 = model1.Store.GetModel(useCached=False)
        self.assertEqual(model2.GetRecurringTransactions()[0].Source, b)
        self.assertEqual(model1, model2)
        
    def testTransactionParentIsRestored(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        t = a.AddTransaction(1)
        self.assertEqual(t.Parent, a)
        
        model2 = model1.Store.GetModel(useCached=False)
        t2 = model2.GetTransactions()[0]
        self.assertEqual(t2.Parent, a)
        
    def testLinkedTransferObjectIsInParent(self):
        a, b, atrans, btrans = self.createLinkedTransfers()
        # First make sure the state of these is as expected before we load fresh.
        link = atrans.LinkedTransaction
        self.assertTrue(link is btrans)
        
        self.assertEqual(a._Transactions, None)
        self.assertEqual(b._Transactions, None)
        
        bts = b.Transactions
        self.assertEqual(len(bts), 1)
        self.assertTrue(btrans is bts[0])
        self.assertTrue(bts[0] is link)
        
        # Now load from disk and see how we are doing.
        model2 = self.Model.Store.GetModel(useCached=False)
        a, b = model2.Accounts
        self.assertEqual((a.Name, b.Name), ("A", "B"))
        
        self.assertEqual(a._Transactions, None)
        self.assertEqual(b._Transactions, None)
        
        link = a.Transactions[0].LinkedTransaction
        self.assertTrue(link in b.Transactions)
        # Here is the real trick. These instances should be the same or it isn't QUITE the real link.
        self.assertTrue(link is b.Transactions[0])
        
    def testTransferDescriptionSetsCorrectly(self):
        a, b, atrans, btrans = self.createLinkedTransfers()
        
        self.assertEqual(atrans.Description, "Transfer from B (test)")
        self.assertEqual(atrans._Description, "test")
        
        atrans.Description = "cats"
        
        self.assertEqual(atrans.Description, "Transfer from B (cats)")
        self.assertEqual(atrans._Description, "cats")
        
        model2 = self.Model.Store.GetModel(useCached=False)
        a, b = model2.Accounts
        self.assertEqual((a.Name, b.Name), ("A", "B"))

        atrans2 = a.Transactions[0]
        self.assertEqual(atrans2.Description, "Transfer from B (cats)")
        self.assertEqual(atrans2._Description, "cats")
        
    def testTransactionRecurringParentIsStored(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        rt = a.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY, endDate=today)
        rt.PerformTransactions()
        
        model2 = model1.Store.GetModel(useCached=False)
        t2 = model2.GetTransactions()[0]
        rt2 = model2.GetRecurringTransactions()[0]
        self.assertEqual(t2.RecurringParent, rt)
        self.assertTrue(t2.RecurringParent is rt2)


    
if __name__ == "__main__":
    unittest.main()