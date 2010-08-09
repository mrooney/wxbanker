#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    modelequalitytests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker.bankobjects.transaction import Transaction
import unittest

class ModelEqualityTest(testbase.TestCaseWithController):
    def testBlankModelsAreEqual(self):
        model1 = self.Controller.Model
        model2 = self.Controller.LoadPath(":memory:")
        self.assertEqual(model1, model2)
        
    def testAccountsWithDifferentNamesArentEqual(self):
        model1 = self.Controller.Model
        model2 = self.Controller.LoadPath(":memory:")
        
        model1.CreateAccount("A")
        self.assertNotEqual(model1, model2)
        model2.CreateAccount("B")
        self.assertNotEqual(model1, model2)
        
    def testAccountWithRecurringTransactionsIsNotEqualToAccountWithout(self):
        # make sure a model with rts is not equal to one without
        model1 = self.Controller.Model
        model2 = self.Controller.LoadPath(":memory:")
        
        a = model1.CreateAccount("A")
        b = model2.CreateAccount("A")
        self.assertEqual(model1, model2)
        
        a.AddRecurringTransaction(0, "", None, 0)
        
        self.assertNotEqual(model1, model2)
        return model1, model2, a, b
    
    def assertChangingAttributeTogglesEquality(self, obj, attr, val, model1, model2):
        self.assertEqual(model1, model2)
        oldVal = getattr(obj, attr)
        setattr(obj, attr, val)
        self.assertNotEqual(model1, model2)
        setattr(obj, attr, oldVal)
        self.assertEqual(model1, model2)
    
    def testDifferentRecurringTransactionsArentEqual(self):
        model1, model2, a, b = self.testAccountWithRecurringTransactionsIsNotEqualToAccountWithout()
        self.assertNotEqual(model1, model2)

        rt = b.AddRecurringTransaction(0, "", None, 0)
        self.assertEqual(model1, model2)
        
        self.assertChangingAttributeTogglesEquality(rt, "Amount", 5, model1, model2)
        self.assertChangingAttributeTogglesEquality(rt, "RepeatType", 5, model1, model2)
        self.assertChangingAttributeTogglesEquality(rt, "RepeatEvery", "2", model1, model2)
        self.assertChangingAttributeTogglesEquality(rt, "RepeatOn", [1,3], model1, model2)
        self.assertChangingAttributeTogglesEquality(rt, "EndDate", testbase.yesterday, model1, model2)
        self.assertChangingAttributeTogglesEquality(rt, "Source", a, model1, model2)
        self.assertChangingAttributeTogglesEquality(rt, "LastTransacted", testbase.yesterday, model1, model2)
        
    def testModelTagEquality(self):
        model1 = self.Controller.Model
        model2 = self.Controller.LoadPath(":memory:")
        
        self.assertEqual(model1, model2)
        model2._Tags = {"foo": 1}
        self.assertNotEqual(model1, model2)
        
    def testTransactionTagEquality(self):
        t1 = Transaction(None, None, 1, "", None)
        t2 = Transaction(None, None, 1, "", None)
        
        self.assertEqual(t1, t2)
        
        t2._Tags = set("foo")
        
        self.assertNotEqual(t1, t2)

if __name__ == "__main__":
    unittest.main()
