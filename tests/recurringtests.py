#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    recurringtests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

import bankobjects
from testbase import today

class RecurringTest(testbase.TestCaseWithController):
    def testRecurringTransactionsAreEmpty(self):
        self.assertEqual(self.Controller.Model.GetRecurringTransactions(), [])
        
    def testCanCreateRecurringTransaction(self):
        model = self.Controller.Model
        a = model.CreateAccount("A")
        rType, rEvery, rOn, rEnd = 0,0,0,0
        a.AddRecurringTransaction(1, "test", today, rType, rEvery, rOn, rEnd)
        
        rts = model.GetRecurringTransactions()
        self.assertEqual(len(rts), 1)

if __name__ == "__main__":
    unittest.main()
