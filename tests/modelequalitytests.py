#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    modelequalitytests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

import testbase
import unittest

class ModelEqualityTest(testbase.TestCaseWithController):
    def testBlankModelsAreEqual(self):
        model1 = self.Controller.Model
        model2 = self.Controller.LoadPath(":memory:")
        self.assertEqual(model1, model2)
        
    def testAccountWithRecurringTransactionsIsNotEqualToAccountWithout(self):
        # make sure a model with rts is not equal to one without
        model1 = self.Controller.Model
        model2 = self.Controller.LoadPath(":memory:")
        
        a = model1.CreateAccount("A")
        b = model2.CreateAccount("A")
        self.assertEqual(model1, model2)
        
        a.AddRecurringTransaction(0, "", None, 0, 0, 0, 0)
        
        self.assertNotEqual(model1, model2)

if __name__ == "__main__":
    unittest.main()
