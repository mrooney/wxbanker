#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    summarytests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

import testbase, bankobjects
import unittest, datetime
from plotalgo import get

def makeTransaction(date, amount):
    """A tiny wrapper to make tests below shorter."""
    return bankobjects.Transaction(None, None, amount, "", date)

T = makeTransaction
today = datetime.date.today()
one = datetime.timedelta(1)


class SummaryTests(unittest.TestCase):
    def testGetTenPointsWithNoTransactions(self):
        result = get([], 10)
        self.assertEqual(result[0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.assertEqual(result[1], datetime.date.today())
        # Make sure it is close to zero but not zero.
        self.assertNotEqual(result[2], 0)
        self.assertAlmostEqual(result[2], 0)

    def testGetPointsWithOneTransaction(self):
        result = get([T("2008/1/6", 1)], 3)
        self.assertEqual(result[0], [1.0, 1.0, 1.0])

        result = get([T(today, 1)], 2)
        self.assertEqual(result[0], [1.0, 1.0])
        self.assertEqual(result[1], today)
        self.assertNotEqual(result[2], 0)

    def testGetOnePointWithTwoTransactionsYesterdayAndToday(self):
        result = get([T(today-one, 1), T(today, 2)], 1)
        self.assertEqual(result[0], [3.0])
        self.assertEqual(result[1], today - one)
        self.assertEqual(result[2], 1.0)

    def testGetPointsWithTwoSequentialDays(self):
        self.assertEqual(get([T(today-one, 1), T(today, 2)], 4)[0], [1.0, 1.0, 1.0, 3.0])
        self.assertEqual(get([T(today, 1), T(today+one, 2)], 2)[0], [1.0, 3.0])
        self.assertEqual(get([T(today, 1), T(today+one, 2)], 3)[0], [1.0, 1.0, 3.0])

    def testGetPointsWithNonSequentialDays(self):
        self.assertEqual(get([T(today-one*9, 1), T(today, 2)], 10)[0], [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 3.0])
        self.assertEqual(get([T(today, 1), T(today+one*2, 2), T(today+one*9, 3)], 10)[0], [1.0, 1.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 6.0])



if __name__ == "__main__":
    unittest.main()