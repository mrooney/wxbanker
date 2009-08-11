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
from testbase import today, one

class RecurringTest(testbase.TestCaseWithController):
    def createAccount(self):
        model = self.Controller.Model
        return model, model.CreateAccount("A")
        
    def testRecurringTransactionsAreEmpty(self):
        self.assertEqual(self.Controller.Model.GetRecurringTransactions(), [])
        
    def testRecurringDefaults(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", today, bankobjects.RECURRING_DAILY)
        self.assertEqual(rt.RepeatType, bankobjects.RECURRING_DAILY)
        self.assertEqual(rt.RepeatEvery, 1)
        self.assertEqual(rt.RepeatOn, None)
        self.assertEqual(rt.EndDate, None)
        self.assertEqual(rt.LastTransacted, None)
        
    def testRecurringWeeklyDefault(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", today, bankobjects.RECURRING_WEEKLY)
        self.assertEqual(rt.RepeatType, bankobjects.RECURRING_WEEKLY)
        self.assertEqual(rt.RepeatOn, [i==today.weekday() for i in range(7)])
        
    def testCanCreateRecurringTransaction(self):
        model, account = self.createAccount()
        account.AddRecurringTransaction(1, "test", today, repeatType=bankobjects.RECURRING_DAILY)
        
        rts = model.GetRecurringTransactions()
        self.assertEqual(len(rts), 1)
        
    def testRecurringDateDailySimple(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", today, bankobjects.RECURRING_DAILY)
        
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [today])
        
    def testRecurringDateDailyWithEvery(self):
        model, account = self.createAccount()
        start = today - one*7
        rt = account.AddRecurringTransaction(1, "test", start, bankobjects.RECURRING_DAILY, repeatEvery=3)
        
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [start, start+one*3, start+one*6])
        
    def testRecurringDateDailyWithEnd(self):
        model, account = self.createAccount()
        start = today - one*4
        rt = account.AddRecurringTransaction(1, "test", start, bankobjects.RECURRING_DAILY, endDate=today-one*2)
        
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [start, start+one, start+one*2])
        
    def testRecurringDateWeeklySimple(self):
        model, account = self.createAccount()
        start = today - one*14
        rt = account.AddRecurringTransaction(1, "test", start, bankobjects.RECURRING_WEEKLY)
        
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [start, start+one*7, start+one*14])
        

if __name__ == "__main__":
    unittest.main()
