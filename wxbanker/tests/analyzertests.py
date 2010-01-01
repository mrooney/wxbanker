#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    analyzertests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
        model = self.Controller.Model
        a = model.CreateAccount("A")
        for i in xrange(1, 13):
            a.AddTransaction(amount=i, date=datetime.date(2009, i, 15))
            
    def testMonthlyDateRangeDefault(self):
        monthly = MonthlyAnalyzer()
        monthly.Today = datetime.date(2010, 1, 15)
        start, end = monthly.GetDateRange()
        self.assertEqual(start, datetime.date(2008, 12, 31))
        self.assertEqual(end, datetime.date(2009, 12, 31))
        
    def testMonthlyDateRangeOne(self):
        monthly = MonthlyAnalyzer(months=1)
        monthly.Today = datetime.date(2010, 1, 15)
        start, end = monthly.GetDateRange()
        self.assertEqual(start, datetime.date(2009, 11, 30))
        self.assertEqual(end, datetime.date(2009, 12, 31))
        
    def testMonthlyAmountsDefault(self):
        monthly = MonthlyAnalyzer()
        earnings = monthly.GetEarnings(self.Controller.Model.GetTransactions())
        self.assertEqual(earnings, range(1,13))
    
    def testMonthlyAmountsOne(self):
        monthly = MonthlyAnalyzer(months=1)
        earnings = monthly.GetEarnings(self.Controller.Model.GetTransactions())
        self.assertEqual(earnings, [12])
