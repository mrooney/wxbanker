#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    modeltests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
import controller, unittest, bankexceptions
from wx.lib.pubsub import Publisher

class ModelTests(testbase.TestCaseWithController):
    def testRobustTransactionAmountParsing(self):
        model = self.Controller.Model
        a = model.CreateAccount("Test")

        self.assertEquals(a.ParseAmount("3"), 3)
        self.assertEquals(a.ParseAmount(".3"), .3)
        self.assertEquals(a.ParseAmount(".31"), .31)
        self.assertEquals(a.ParseAmount(",3"), .3)
        self.assertEquals(a.ParseAmount(",31"), .31)
        self.assertEquals(a.ParseAmount("1.5"), 1.5)
        self.assertEquals(a.ParseAmount("1,5"), 1.5)
        self.assertEquals(a.ParseAmount("10"), 10)
        self.assertEquals(a.ParseAmount("10."), 10)
        self.assertEquals(a.ParseAmount("10.1"), 10.1)
        self.assertEquals(a.ParseAmount("10.23"), 10.23)
        self.assertEquals(a.ParseAmount("10,"), 10)
        self.assertEquals(a.ParseAmount("10,1"), 10.1)
        self.assertEquals(a.ParseAmount("10,23"), 10.23)
        self.assertEquals(a.ParseAmount("1 000"), 1000)
        self.assertEquals(a.ParseAmount("1 000."), 1000)
        self.assertEquals(a.ParseAmount("1 000,"), 1000)
        self.assertEquals(a.ParseAmount("1,000"), 1000)
        self.assertEquals(a.ParseAmount("1,000."), 1000)
        self.assertEquals(a.ParseAmount("1,000.2"), 1000.2)
        self.assertEquals(a.ParseAmount("1.000.23"), 1000.23)
        self.assertEquals(a.ParseAmount("1 000.23"), 1000.23)
        self.assertEquals(a.ParseAmount("1,000.23"), 1000.23)
        self.assertEquals(a.ParseAmount("1.000,23"), 1000.23)
        self.assertEquals(a.ParseAmount("1 000,23"), 1000.23)
        self.assertEquals(a.ParseAmount("1234567890"), 1234567890)

    def testControllerIsAutoSavingByDefault(self):
        self.assertTrue( self.Controller.AutoSave )

    def testNewAccountIsSameCurrencyAsOthers(self):
        # This test is only valid so long as only one currency is allowed.
        # Otherwise it needs to test a new account gets the right default currency, probably Localized
        import currencies
        model = self.Controller.Model

        account = model.CreateAccount("Hello")
        self.assertEqual(account.Currency, currencies.LocalizedCurrency())

        account.Currency = currencies.EuroCurrency()
        self.assertEqual(account.Currency, currencies.EuroCurrency())

        account2 = model.CreateAccount("Another!")
        self.assertEqual(account2.Currency, currencies.EuroCurrency())

    def testBlankModelsAreEqual(self):
        model1 = self.Controller.Model
        model2 = self.Controller.LoadPath(":memory:")
        self.assertEqual(model1, model2)

    def testLoadingTransactionsPreservesReferences(self):
        a = self.Model.CreateAccount("A")
        t = a.AddTransaction(1, "First")
        self.assertEqual(t.Description, "First")

        # When we do a.Transactions, the list gets loaded with new
        # transaction objects, so let's see if the containership test works.
        self.assertTrue(t in a.Transactions)

        # 't' is the original transaction object created before Transactions
        # was loaded, but it should be in the list due to magic.
        t.Description = "Second"
        self.assertEqual(a.Transactions[0].Description, "Second")

    def testSimpleMove(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        t1 = a.AddTransaction(-1)

        b = model1.CreateAccount("B")

        a.MoveTransaction(t1, b)

        self.assertFalse(t1 in a.Transactions)
        self.assertTrue(t1 in b.Transactions)
        self.assertNotEqual(t1.Parent, a)
        self.assertEqual(t1.Parent, b)

    def testTransactionPropertyBug(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        t1 = a.AddTransaction(-1)
        self.assertEqual(len(a.Transactions), 1)

    def testDirtyExitWarns(self):
        """
        This test is kind of hilarious. We want to make sure we are warned of
        exiting with a dirty model, so we create an account, register a callback
        which will change its name when the dirty warning goes out, then trigger
        a dirty exit and make sure the account name has changed.
        """
        self.Controller.AutoSave = False
        a = self.Model.CreateAccount("Unwarned!")

        # Create and register our callback to test for the warning message.
        def cb(message):
            a.Name = "Warned"
        Publisher.subscribe(cb, "warning.dirty exit")

        # Now send the exiting message, which should cause our callback to fire if everything is well.
        Publisher.sendMessage("exiting")

        self.assertEqual(a.Name, "Warned")

    def testAnnouncedAccountHasParent(self):
        """
        Make sure the account has a Parent when it announces itself. To do this
        we need to test this in a listener.
        """
        parent = []
        def listener(message):
            account = message.data
            parent.append(account.Parent)

        # Subscribe our listener
        Publisher.subscribe(listener, "account.created")
        # Create an account, which should trigger the listener
        baby = self.Model.CreateAccount("Baby")
        # Make sure the listener updated state appropriately
        self.assertTrue(parent)

    def testNewAccountCanGetSiblings(self):
        baby = self.Model.CreateAccount("Baby")
        self.assertEqual(list(baby.GetSiblings()), [])

    def testTransfersAreLinked(self):
        a, b, atrans, btrans = self.createLinkedTransfers()

        self.assertEqual(atrans.Parent, a)
        self.assertEqual(btrans.Parent, b)

        self.assertEqual(atrans.LinkedTransaction, btrans)
        self.assertEqual(btrans.LinkedTransaction, atrans)

        self.assertEqual(a.Transactions, [atrans])
        self.assertEqual(b.Transactions, [btrans])

    def testDeletingTransferDeletesBoth(self):
        a, b, atrans, btrans = self.createLinkedTransfers()
        model = self.Controller.Model

        self.assertEqual(len(model.Accounts), 2)
        self.assertEqual(model.GetTransactions(), [atrans, btrans])
        self.assertEqual(model.Balance, 0)
        self.assertEqual(len(a.Transactions), 1)
        self.assertEqual(len(b.Transactions), 1)

        a.RemoveTransaction(atrans)

        self.assertEqual(len(a.Transactions), 0)
        self.assertEqual(len(b.Transactions), 0)
        self.assertEqual(model.GetTransactions(), [])
        self.assertEqual(model.Balance, 0)

    def testEmptyAccountNameInvalidForNewAccount(self):
        self.assertRaises(bankexceptions.BlankAccountNameException, lambda: self.Controller.Model.CreateAccount(""), )

    def testEmptyAccountNameInvalidForRename(self):
        a = self.Controller.Model.CreateAccount("Test")

        def blankName():
            a.Name = ""

        self.assertRaises(bankexceptions.BlankAccountNameException, blankName)

if __name__ == "__main__":
    unittest.main()
