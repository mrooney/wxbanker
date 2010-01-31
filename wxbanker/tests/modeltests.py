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

from wxbanker.tests import testbase
import os, datetime, unittest
from wxbanker import controller, bankexceptions, currencies
from wx.lib.pubsub import Publisher

from wxbanker.tests.testbase import today, yesterday, tomorrow

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
        
    def testFreshAccount(self):
        a = self.Model.CreateAccount("Fresh")
        self.assertEqual(a.Balance, 0)
        self.assertEqual(a.Transactions, [])
        self.assertEqual(a.Name, "Fresh")
        
    def testCannotRemoveNonexistentAccount(self):
        self.assertRaisesWithMsg(self.Model.RemoveAccount, ["Foo"], bankexceptions.InvalidAccountException, "Invalid account 'Foo' specified.")
            
    def testCannotCreateAccountWithSameName(self):
        a = self.Model.CreateAccount("A")
        self.assertRaisesWithMsg(self.Model.CreateAccount, ["A"], bankexceptions.AccountAlreadyExistsException, "Account 'A' already exists.")

    def testControllerIsAutoSavingByDefault(self):
        self.assertTrue( self.Controller.AutoSave )

    def testNewAccountIsSameCurrencyAsOthers(self):
        # This test is only valid so long as only one currency is allowed.
        # Otherwise it needs to test a new account gets the right default currency, probably Localized
        model = self.Controller.Model

        account = model.CreateAccount("Hello")
        self.assertEqual(account.Currency, currencies.LocalizedCurrency())

        account.Currency = currencies.EuroCurrency()
        self.assertEqual(account.Currency, currencies.EuroCurrency())

        account2 = model.CreateAccount("Another!")
        self.assertEqual(account2.Currency, currencies.EuroCurrency())

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

    def testSiblingsSingleAccount(self):
        baby = self.Model.CreateAccount("Baby")
        self.assertEqual(baby.GetSiblings(), [])
        
    def testSiblingsTwoAccounts(self):
        a = self.Model.CreateAccount("A")
        b = self.Model.CreateAccount("B")
        
        self.assertEqual(a.GetSiblings(), [b])
        self.assertEqual(b.GetSiblings(), [a])

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
        
    def testGetDateRangeWhenEmpty(self):
        self.assertEqual(self.Controller.Model.GetDateRange(), (datetime.date.today(), datetime.date.today()))
        
    def testGetDateRangeWithTransactions(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        a.AddTransaction(1, date=yesterday)
        a.AddTransaction(1, date=tomorrow)
        
        self.assertEqual(model.GetDateRange(), (yesterday, tomorrow))
        
    def testGetDateRangeSorts(self):
        # Make sure that the transactions don't need to be in order for GetDateRange to work.
        model = self.Controller.Model
        a = model.CreateAccount("A")
        a.AddTransaction(1, date=today)
        a.AddTransaction(1, date=yesterday)
        
        self.assertEqual(model.GetDateRange(), (yesterday, today))
        
    def testAccountRename(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        self.assertEqual(a.Name, "A")
        a.Name = "B"
        self.assertEqual(a.Name, "B")
        self.assertRaisesWithMsg(model.RemoveAccount, ["A"], bankexceptions.InvalidAccountException, "Invalid account 'A' specified.")
        
    def testTransactionDescriptionChange(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        t = a.AddTransaction(1, "test")
        self.assertEqual(t.Description, "test")
        t.Description = "new"
        self.assertEqual(t.Description, "new")
        
    def testBalanceIsUpdatedOnTransactionAdded(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        self.assertEqual(a.Balance, 0)
        a.AddTransaction(1)
        self.assertEqual(a.Balance, 1)
        
    def testBalanceIsUpdatedOnTransactionRemoved(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        self.assertEqual(a.Balance, 0)
        t = a.AddTransaction(1)
        self.assertEqual(a.Balance, 1)
        a.RemoveTransaction(t)
        self.assertEqual(a.Balance, 0)
        
    def testBalanceIsUpdatedOnTransactionAmountModified(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        self.assertEqual(a.Balance, 0)
        t = a.AddTransaction(1)
        self.assertEqual(a.Balance, 1)
        t.Amount = 2
        self.assertEqual(a.Balance, 2)
        
    def testModelBalance(self):
        model = self.Controller.Model
        self.assertEqual(model.Balance, 0)
        
        a = model.CreateAccount("A")
        a.AddTransaction(1)
        self.assertEqual(model.Balance, 1)
        
        b = model.CreateAccount("B")
        b.AddTransaction(2)
        self.assertEqual(model.Balance, 3)
        
    def testRemovingTransactionsReturnsSources(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        b = model.CreateAccount("B")

        t = a.AddTransaction(1)
        result = a.RemoveTransaction(t)
        self.assertEqual(result, [None])
        
        ta, tb = a.AddTransaction(1, source=b)
        result = a.RemoveTransaction(ta)
        self.assertEqual(result, [b], result[0].Name)
        
    def testCanMoveTransfer(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        b = model.CreateAccount("B")
        
        atrans, btrans = a.AddTransaction(1, source=b)
        self.assertEqual(len(model.GetTransactions()), 2)
        self.assertEqual(model.Balance, 0)
        self.assertEqual(atrans.Description, "Transfer from B")
        self.assertEqual(btrans.Description, "Transfer to A")
        
        c = model.CreateAccount("C")
        a.MoveTransaction(atrans, c)
        
        self.assertEqual(a.Transactions, [])
        self.assertEqual(len(b.Transactions), 1)
        self.assertEqual(len(c.Transactions), 1)
        
        btrans = b.Transactions[0]
        ctrans = c.Transactions[0]
        self.assertEqual(btrans.LinkedTransaction, ctrans)
        self.assertEqual(ctrans.LinkedTransaction, btrans)
        self.assertEqual(btrans.Description, "Transfer to C")
        self.assertEqual(ctrans.Description, "Transfer from B")
        
    def testTransferDescriptionWithoutDescription(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        b = model.CreateAccount("B")
        
        at, bt = a.AddTransaction(1, source=b)
        self.assertEqual(at._Description, "")
        self.assertEqual(bt._Description, "")
        self.assertEqual(at.Description, "Transfer from B")
        self.assertEqual(bt.Description, "Transfer to A")
        
    def testTransferDescriptionWithDescription(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        b = model.CreateAccount("B")
        
        at, bt = a.AddTransaction(1, description="hello world", source=b)
        self.assertEqual(at._Description, "hello world")
        self.assertEqual(bt._Description, "hello world")
        self.assertEqual(at.Description, "Transfer from B (hello world)")
        self.assertEqual(bt.Description, "Transfer to A (hello world)")
        
    def testTransferMoveDescriptionWithDescription(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        b = model.CreateAccount("B")
        c = model.CreateAccount("C")
        
        at, bt = a.AddTransaction(1, description="hello world", source=b)
        a.MoveTransaction(at, c)
        
        bt, ct = b.Transactions[0], c.Transactions[0]
        
        self.assertEqual(ct._Description, "hello world")
        self.assertEqual(bt._Description, "hello world")
        self.assertEqual(ct.Description, "Transfer from B (hello world)")
        self.assertEqual(bt.Description, "Transfer to C (hello world)")
        
    def testUnicodeTransactionDescription(self):
        unicodeString = u'￥'
        unicodeString2 = u'￥2'
        model = self.Controller.Model
        a = model.CreateAccount("A")
        
        t = a.AddTransaction(1, description=unicodeString)
        self.assertEqual(t.Description, unicodeString)
        
        t.Description = unicodeString2
        self.assertEqual(t.Description, unicodeString2)
        
    def testUnicodeSearch(self):
        unicodeString = u'￥'
        model = self.Controller.Model
        a = model.CreateAccount("A")
        
        self.assertEqual(model.Search(unicodeString), [])
        t = a.AddTransaction(1, description=unicodeString)
        self.assertEqual(model.Search(unicodeString), [t])
        
    def testAccountsAreSorted(self):
        model = self.Controller.Model
        b = model.CreateAccount("B")
        self.assertEqual(model.Accounts, [b])
        
        a = model.CreateAccount("A")
        self.assertEqual(model.Accounts, [a, b])
        
        a.Name = "Z"
        self.assertEqual(model.Accounts, [b, a])
        
    def testDefaultLastAccountIsNone(self):
        model = self.Controller.Model
        self.assertEqual(model.LastAccountId, None)
        
    def testLastAccountIsUpdated(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        self.assertEqual(model.LastAccountId, None)
        Publisher.sendMessage("view.account changed", a)
        self.assertEqual(model.LastAccountId, a.ID)
        
    def testTransactionDateMassaging(self):
        model = self.Controller.Model
        t = model.CreateAccount("A").AddTransaction(1)
        self.assertEqual(t.Date, today)
        t.Date = "2001/01/01"
        self.assertEqual(t.Date, datetime.date(2001, 1, 1))
        t.Date = "2008-01-06"
        self.assertEqual(t.Date, datetime.date(2008, 1, 6))
        t.Date = "08-01-06"
        self.assertEqual(t.Date, datetime.date(2008, 1, 6))
        t.Date = "86-01-06"
        self.assertEqual(t.Date, datetime.date(1986, 1, 6))
        t.Date = "11-01-06"
        self.assertEqual(t.Date, datetime.date(2011, 1, 6))
        t.Date = "0-1-6"
        self.assertEqual(t.Date, datetime.date(2000, 1, 6))
        t.Date = "0/1/6"
        self.assertEqual(t.Date, datetime.date(2000, 1, 6))
        t.Date = datetime.date(2008, 1, 6)
        self.assertEqual(t.Date, datetime.date(2008, 1, 6))
        t.Date = None
        self.assertEqual(t.Date, datetime.date.today())
        
    def testDeletingAccountDoesNotSiblingLinkedTransfers(self):
        """If you close (delete) an account, it is still true that the transfers occurred."""
        a, b, atrans, btrans = self.createLinkedTransfers()
        model = self.Controller.Model
        
        self.assertTrue(atrans in a.Transactions)
        self.assertTrue(btrans in b.Transactions)
        self.assertEqual(atrans.LinkedTransaction, btrans)
        self.assertEqual(btrans.LinkedTransaction, atrans)
        
        model.RemoveAccount(b.Name)
        
        self.assertTrue(atrans in a.Transactions)
        self.assertEqual(atrans.LinkedTransaction, None)
        
        
if __name__ == "__main__":
    unittest.main()
