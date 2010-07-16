#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    dbupgradetests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker.controller import Controller
import unittest, shutil, os, tempfile, datetime

class DBUpgradeTest(testbase.TestCaseHandlingConfig):
    def setUp(self):
        testbase.TestCaseHandlingConfig.setUp(self)
        self.tmpFile = None
        
    def tearDown(self):
        if self.tmpFile:
            os.remove(self.tmpFile)

    def getController(self, ver):
        origpath = testbase.fixturefile("bank-%s.db"%ver)
        self.tmpFile = tempfile.mkstemp()[1]
        shutil.copyfile(origpath, self.tmpFile)
        return Controller(path=self.tmpFile)
        
    def doBaseTest(self, ver):
        c = self.getController(ver)
        model = c.Model
        accounts = model.Accounts
        self.assertEqual([a.Name for a in accounts], ["Another", "My Checking"])
        self.assertEqual(accounts[1].Balance, 25)
        self.assertEqual(accounts[0].Balance, -123.45)
        
        # Make sure it is persisted!
        model2 = model.Store.GetModel(useCached=False)
        accounts = model2.Accounts
        self.assertEqual([a.Name for a in accounts], ["Another", "My Checking"])
        self.assertEqual(accounts[1].Balance, 25)
        self.assertEqual(accounts[0].Balance, -123.45)
        
        return c
        
    def testUpgradeFrom04(self):
        c = self.doBaseTest("0.4")
        
    def testUpgradeFrom04Broken(self):
        # A 0.4 -> 0.6 upgrade left dbs in a broken state, let's handle it.
        c = self.doBaseTest("0.4-broken")
        
    def testUpgradeFrom05(self):
        c = self.doBaseTest("0.5")
        
    def testUpgradeFrom06Broken(self):
        # Test we can upgrade/run if LP #514183 has already occurred.
        c = self.getController("0.6-broken")
        transactions = c.Model.Accounts[0].Transactions
        self.assertEqual(len(transactions), 1)
        
        t = transactions[0]
        self.assertEqual(t.Date, datetime.date(2010, 1, 30))
        self.assertEqual(t.Amount, -1.1)
        self.assertEqual(t.Description, "a")
        self.assertEqual(t.LinkedTransaction, None)

    def testCanDeleteAccountWithOldTransfer(self):
        model = self.getController("0.7-605591").Model
        a = model.Accounts[1]
        model.RemoveAccount(a.Name)
        
        model2 = model.Store.GetModel(useCached=False)
        self.assertEqual(model, model2)
        
    def testUpgradeFromPre08GetsTags(self):
        # Import a db with pre-tag tags in the description, make sure they are real tags.
        self.markTestIncomplete("TODO")
        
def main():
    unittest.main()

