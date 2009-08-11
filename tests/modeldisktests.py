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

import testbase, os
import controller, unittest
from wx.lib.pubsub import Publisher

from testbase import today

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
        model2 = model1.Store.GetModel(useCached=False)
        self.assertEqual(model1, model2)
        
    def testLinkedTransferIsStored(self):
        a, b, atrans, btrans = self.createLinkedTransfers()
        model1 = self.Controller.Model

        model2 = model1.Store.GetModel(useCached=False)
        self.assertTrue(model1 == model2)
        
    def testRecurringTransactionIsStored(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        a.AddRecurringTransaction(1, "test", today, repeatType=1)
        
        model2 = model1.Store.GetModel(useCached=False)
        self.assertEqual(model1, model2)
        
        repeatOn = model2.GetRecurringTransactions()[0].RepeatOn
        self.assertEqual(len(repeatOn), 7)
        self.assertEqual(sum(repeatOn), 1)
    
if __name__ == "__main__":
    unittest.main()