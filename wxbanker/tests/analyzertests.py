#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    analyzertests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker.analyzers import MonthlyAnalyzer
import unittest, datetime

class AnalyzerTests(testbase.TestCaseWithController):
    def setUp(self):
        testbase.TestCaseWithController.setUp(self)
        a = self.Model.CreateAccount("A")
        for i in xrange(1, 13):
            a.AddTransaction(amount=i, date=datetime.date(2009, i, 15))
            
    def createMonthly(self, *args, **kwargs):
        monthly = MonthlyAnalyzer(*args, **kwargs)
        monthly.Today = datetime.date(2010, 1, 15)
        return monthly
            
    def testMonthlyDateRangeDefault(self):
        monthly = self.createMonthly()
        start, end = monthly.GetDateRange()
        self.assertEqual(start, datetime.date(2009, 1, 1))
        self.assertEqual(end, datetime.date(2009, 12, 31))
        
    def testMonthlyDateRangeOne(self):
        monthly = self.createMonthly(months=1)
        start, end = monthly.GetDateRange()
        self.assertEqual(start, datetime.date(2009, 12, 1))
        self.assertEqual(end, datetime.date(2009, 12, 31))
        
    def testMonthlyAmountsDefault(self):
        monthly = self.createMonthly()
        earnings = monthly.GetEarnings(self.Model.GetTransactions())
        self.assertEqual(
            earnings,
            [('2009.01', 1), ('2009.02', 2), ('2009.03', 3), ('2009.04', 4), ('2009.05', 5), ('2009.06', 6),
             ('2009.07', 7), ('2009.08', 8), ('2009.09', 9), ('2009.10', 10), ('2009.11', 11), ('2009.12', 12)]
        )
    
    def testMonthlyAmountsOne(self):
        monthly = self.createMonthly(months=1)
        earnings = monthly.GetEarnings(self.Model.GetTransactions())
        self.assertEqual(earnings, [("2009.12", 12)])

    def testMonthlyAmountsEmpty(self):
        # With no transactions from a previous month, we should have a zero for all months to show. (LP: #623055)
        self.Model.Accounts[0].Remove()
        monthly = self.createMonthly()
        earnings = monthly.GetEarnings(self.Model.GetTransactions())
        self.assertEqual(
            earnings,
            [('2009.01', 0), ('2009.02', 0), ('2009.03', 0), ('2009.04', 0), ('2009.05', 0), ('2009.06', 0),
             ('2009.07', 0), ('2009.08', 0), ('2009.09', 0), ('2009.10', 0), ('2009.11', 0), ('2009.12', 0)]
        )