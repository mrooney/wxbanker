#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    recurringtests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
import unittest, datetime

from bankobjects.recurringtransaction import RecurringTransaction
from testbase import today, yesterday, tomorrow, one

class RecurringTest(testbase.TestCaseWithController):
    def createAccount(self):
        model = self.Controller.Model
        return model, model.CreateAccount("A")

    def testRecurringTransactionsAreInitiallyEmpty(self):
        self.assertEqual(self.Controller.Model.GetRecurringTransactions(), [])
    
    def testGetChildren(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY, endDate=today)
        
        # Initially empty.
        self.assertLength(rt.GetChildren(), 0)
        
        # Make a transaction that shouldn't be a child.
        t = account.AddTransaction(1)
        self.assertLength(rt.GetChildren(), 0)
        
        rt.PerformTransactions()
        self.assertLength(rt.GetChildren(), 1)
        
    def testCanDeleteRecurringTransaction(self):
        model, account = self.createAccount()
        
        rt = account.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY, endDate=today)
        self.assertEqual(account.RecurringTransactions, [rt])
        
        rt.PerformTransactions()        
        self.assertEqual(len(account.Transactions), 1)
        self.assertEqual(account.Transactions[0].RecurringParent, rt)
        
        # Now remove it and make sure it is gone.
        account.RemoveRecurringTransaction(rt)
        self.assertEqual(account.RecurringTransactions, [])
        # The performed transaction should still exist but have no RecurringParent.
        self.assertEqual(len(account.Transactions), 1)
        self.assertEqual(account.Transactions[0].RecurringParent, None)
        
    def testRecurringDefaults(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY)
        self.assertEqual(rt.RepeatType, RecurringTransaction.DAILY)
        self.assertEqual(rt.RepeatEvery, 1)
        self.assertEqual(rt.RepeatOn, None)
        self.assertEqual(rt.EndDate, None)
        self.assertEqual(rt.LastTransacted, None)
        
    def testRecurringWeeklyDefault(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", today, RecurringTransaction.WEEKLY)
        self.assertEqual(rt.RepeatType, RecurringTransaction.WEEKLY)
        self.assertEqual(rt.RepeatOn, [i==today.weekday() for i in range(7)])
        
    def testCanCreateRecurringTransaction(self):
        model, account = self.createAccount()
        account.AddRecurringTransaction(1, "test", today, repeatType=RecurringTransaction.DAILY)
        
        rts = model.GetRecurringTransactions()
        self.assertEqual(len(rts), 1)
        
    def testRecurringDateDailySimple(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY)
        
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [today])
        
    def testRecurringDateDailyWithEvery(self):
        model, account = self.createAccount()
        start = today - one*7
        rt = account.AddRecurringTransaction(1, "test", start, RecurringTransaction.DAILY, repeatEvery=3)
        
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [start, start+one*3, start+one*6])
        
    def testRecurringDateDailyWithEnd(self):
        model, account = self.createAccount()
        start = today - one*4
        rt = account.AddRecurringTransaction(1, "test", start, RecurringTransaction.DAILY, endDate=today-one*2)
        
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [start, start+one, start+one*2])
        
    def testRecurringDateWeeklySimple(self):
        model, account = self.createAccount()
        start = today - one*14
        rt = account.AddRecurringTransaction(1, "test", start, RecurringTransaction.WEEKLY)
        
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [start, start+one*7, start+one*14])
        
    def testRecurringDateWeeklyEveryOtherWeekendDay(self):
        model, account = self.createAccount()
        start = datetime.date(2009, 1, 1)
        rt = account.AddRecurringTransaction(1, "test", start, RecurringTransaction.WEEKLY, repeatEvery=2, repeatOn=[0,0,0,0,0,1,1], endDate=datetime.date(2009, 1, 31))
        
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [datetime.date(2009, 1, 3), datetime.date(2009, 1, 4), datetime.date(2009, 1, 17), datetime.date(2009, 1, 18), datetime.date(2009, 1, 31)])
        
    def testRecurringDateMonthly(self):
        model, account = self.createAccount()
        start = datetime.date(2009, 1, 1)
        rt = account.AddRecurringTransaction(1, "test", start, RecurringTransaction.MONTLY, endDate=datetime.date(2009, 3, 15))
        
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [start, datetime.date(2009, 2, 1), datetime.date(2009, 3, 1)])
        
    def testRecurringDateMonthlyShortMonths(self):
        # Months should clamp their dates if the day number is too high.
        model, account = self.createAccount()
        start = datetime.date(2009, 1, 31)
        rt = account.AddRecurringTransaction(1, "test", start, RecurringTransaction.MONTLY, endDate=datetime.date(2009, 5, 1))
        
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [start, datetime.date(2009, 2, 28), datetime.date(2009, 3, 31), datetime.date(2009, 4, 30)])
        
    def testRecurringDateMonthlyQuarterly(self):
        model, account = self.createAccount()
        start = datetime.date(2009, 1, 1)
        rt = account.AddRecurringTransaction(1, "test", start, RecurringTransaction.MONTLY, repeatEvery=3, endDate=datetime.date(2009, 12, 31))
        
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [start, datetime.date(2009, 4, 1), datetime.date(2009, 7, 1), datetime.date(2009, 10, 1)])

    def testRecurringDateYearly(self):
        model, account = self.createAccount()
        start = datetime.date(2005, 1, 6)
        rt = account.AddRecurringTransaction(1, "birthday!", start, RecurringTransaction.YEARLY, repeatEvery=2, endDate=datetime.date(2009, 12, 31))

        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [start, datetime.date(2007, 1, 6), datetime.date(2009, 1, 6)])

    def testRecurringDateYearlyLeapYear(self):
        # If a transaction is entered on a leap day, it should only occur on future leap days.
        model, account = self.createAccount()
        start = datetime.date(2004, 2, 29)
        rt = account.AddRecurringTransaction(1, "leap day wee", start, RecurringTransaction.YEARLY, endDate=datetime.date(2009, 12, 31))

        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [start, datetime.date(2008, 2, 29)])
        
    def testUpdatesLastTransacted(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY)
        
        self.assertEqual(rt.LastTransacted, None)
        rt.PerformTransactions()
        self.assertEqual(rt.LastTransacted, today)
        
    def testCanPerformTransactions(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", yesterday, RecurringTransaction.DAILY)
        
        self.assertEqual(account.Transactions, [])
        
        rt.PerformTransactions()
        
        transactions = model.GetTransactions()
        self.assertEqual(len(transactions), 2)
        
        t = transactions[0]
        self.assertEqual(t.Amount, 1)
        self.assertEqual(t.Description, "test")
        self.assertEqual(t.Date, yesterday)
        
        t = transactions[1]
        self.assertEqual(t.Amount, 1)
        self.assertEqual(t.Description, "test")
        self.assertEqual(t.Date, today)
        
    def testRecurringTransfer(self):
        model, account = self.createAccount()
        account2 = model.CreateAccount("B")
        rt = account.AddRecurringTransaction(5, "test", today, RecurringTransaction.DAILY, source=account2)
        
        self.assertEqual(model.GetTransactions(), [])
        rt.PerformTransactions()
        
        transactions = model.GetTransactions()
        self.assertEqual(len(transactions), 2)
        
        self.assertEqual(account.Transactions[0].Amount, 5)
        self.assertEqual(account2.Transactions[0].Amount, -5)
        
    def testDoesntMakeTransactionsAfterLastUpdated(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY)
        self.assertEqual(len(account.Transactions), 0)
        rt.PerformTransactions()
        self.assertEqual(len(account.Transactions), 1)
        rt.PerformTransactions()
        self.assertEqual(len(account.Transactions), 1)
        
    def testUntransactedEndsTodayAtLatest(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", yesterday, RecurringTransaction.DAILY, endDate=tomorrow)
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [yesterday, today])
        
    def testStartCooperatesWithLastTransactedMonthly(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", datetime.date(2009, 1, 15), RecurringTransaction.MONTLY, endDate=datetime.date(2009, 2, 28))
        dates = rt.GetUntransactedDates()
        self.assertEqual(len(dates), 2)
        # Now let's say we performed it on 2/1, there shouldn't be a transaction for 2/2 because it thinks the start is LastTransacted + 1.
        rt.LastTransacted = datetime.date(2009, 2, 1)
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [datetime.date(2009, 2, 15)])
        
    def testStartCooperatesWithLastTransactedYearly(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", datetime.date(2008, 1, 15), RecurringTransaction.YEARLY, endDate=datetime.date(2009, 2, 28))
        dates = rt.GetUntransactedDates()
        self.assertEqual(len(dates), 2)
        # Now let's say we performed it on 2/1, there shouldn't be a transaction for 1/2 because it thinks the start is LastTransacted + 1.
        rt.LastTransacted = datetime.date(2009, 1, 1)
        dates = rt.GetUntransactedDates()
        self.assertEqual(dates, [datetime.date(2009, 1, 15)])

    def testGettingUntransactedInFuture(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", tomorrow, RecurringTransaction.DAILY, endDate=tomorrow)
        self.assertEqual(rt.GetUntransactedDates(), [])
        self.assertEqual(rt.GetNext(), tomorrow)
        
    def testRecurringTransactionLinkIsNoneOnNormalTransaction(self):
        model, account = self.createAccount()
        t = account.AddTransaction(1)
        self.assertEqual(t.RecurringParent, None)
        
    def testRecurringTransactionLinkIsCorrectOnRecurringTransaction(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY, endDate=today)
        rt.PerformTransactions()
        
        ts = account.Transactions
        self.assertEqual(len(ts), 1)
        self.assertEqual(ts[0].RecurringParent, rt)
        
    def testRecurringSummaryDaily(self):
        model, account = self.createAccount()
        
        rt = account.AddRecurringTransaction(1, "test", today, RecurringTransaction.DAILY)
        self.assertEqual(rt.GetRecurrance(), "Daily")
        
        rt.EndDate = today
        self.assertEqual(rt.GetRecurrance(), "Daily until %s" % today)
        
    def testRecurringSummaryWeekly(self):
        model, account = self.createAccount()
        
        rt = account.AddRecurringTransaction(1, "test", datetime.date(2009, 1, 6), RecurringTransaction.WEEKLY)
        self.assertEqual(rt.GetRecurrance(), "Weekly on Tuesdays")
        
        rt.RepeatOn = [0,0,0,0,0,0,0]
        self.assertEqual(rt.GetRecurrance(), "Never")
        
        rt.RepeatOn = [1,1,1,1,1,1,1]
        self.assertEqual(rt.GetRecurrance(), "Daily")
        
        rt.RepeatOn = [1,1,1,1,1,0,0]
        self.assertEqual(rt.GetRecurrance(), "Weekly on weekdays")
        
        rt.RepeatOn = [0,0,0,0,0,1,1]
        self.assertEqual(rt.GetRecurrance(), "Weekly on weekends")
        
        rt.RepeatOn = [1,0,1,0,0,0,0]
        self.assertEqual(rt.GetRecurrance(), "Weekly on Mondays and Wednesdays")
        
        rt.RepeatOn = [1,0,1,0,0,1,0]
        self.assertEqual(rt.GetRecurrance(), "Weekly on Mondays, Wednesdays and Saturdays")
        
        rt.EndDate = today
        self.assertEqual(rt.GetRecurrance(), "Weekly on Mondays, Wednesdays and Saturdays until %s" % today)
        
        rt.RepeatEvery = 2
        self.assertEqual(rt.GetRecurrance(), "Every 2 weeks on Mondays, Wednesdays and Saturdays until %s" % today)
        
    def testRecurringSummaryMonthly(self):
        model, account = self.createAccount()
        
        rt = account.AddRecurringTransaction(1, "test", today, RecurringTransaction.MONTLY)
        self.assertEqual(rt.GetRecurrance(), "Monthly")
        
        rt.RepeatEvery = 3
        self.assertEqual(rt.GetRecurrance(), "Every 3 months")
        
        rt.EndDate = today
        self.assertEqual(rt.GetRecurrance(), "Every 3 months until %s" % today)
        
    def testRecurringSummaryYearly(self):
        model, account = self.createAccount()
        
        rt = account.AddRecurringTransaction(1, "test", today, RecurringTransaction.YEARLY)
        self.assertEqual(rt.GetRecurrance(), "Annually")
        
        rt.EndDate = today
        self.assertEqual(rt.GetRecurrance(), "Annually until %s" % today)
        
        rt.RepeatEvery = 10
        self.assertEqual(rt.GetRecurrance(), "Every 10 years until %s" % today)
        
    def testGetDueString(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "Example Description", yesterday, RecurringTransaction.DAILY)
        self.assertEqual(rt.GetDueString(), "Example Description, $1.00: %s, %s" % (yesterday, today))
        
    def testGetDescriptionString(self):
        model, account = self.createAccount()
        rt = account.AddRecurringTransaction(1, "Example Description", yesterday, RecurringTransaction.DAILY)
        self.assertEqual(rt.GetDescriptionString(), "Example Description, $1.00: Daily")
        
    def testUpdateFrom(self):
        model, account = self.createAccount()
        account2 = model.CreateAccount("Giggles")
        rt = account.AddRecurringTransaction(1, "Example Description", yesterday, RecurringTransaction.DAILY)
        rt2 = account.AddRecurringTransaction(2, "Other Description", today, RecurringTransaction.WEEKLY, repeatEvery=2, repeatOn=(1,1,0,0,0,0,0), endDate=tomorrow, source=account2)

        rt.LastTransacted = yesterday
        rt2.LastTransacted = today
        
        rt.UpdateFrom(rt2)

        # Make sure everything is updated.
        self.assertEqual(rt.Amount, 2)
        self.assertEqual(rt.Description, "Other Description")
        self.assertEqual(rt.Date, today)
        self.assertEqual(rt.RepeatType, RecurringTransaction.WEEKLY)
        self.assertEqual(rt.RepeatEvery, 2)
        self.assertEqual(rt.RepeatOn, (1,1,0,0,0,0,0))
        self.assertEqual(rt.EndDate, tomorrow)
        self.assertEqual(rt.Source, account2)
        # Except LastTransacted should NOT be updated, that should stay the same as it was.
        self.assertEqual(rt.LastTransacted, yesterday)
        

if __name__ == "__main__":
    unittest.main()
