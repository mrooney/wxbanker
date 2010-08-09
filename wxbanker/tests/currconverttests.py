#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    currconverttests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
import unittest
from wxbanker import currencies, currconvert

class CurrConvertTest(unittest.TestCase):
    def setUp(self):
        self.CC = currconvert.CurrencyConverter()

    def testConversionToSameCurrencyIsSame(self):
        amount = 5.23
        self.assertEqual(self.CC.Convert(amount, "EUR", "EUR"), amount)

    def testConversionWithStockValuesIsExpected(self):
        rate = 1.2795
        self.assertEqual(self.CC.Convert(1, "EUR", "USD"), rate)
        self.assertEqual(self.CC.Convert(1, "USD", "EUR"), 1/rate)

    def testInvalidCurrencyIsExpectedException(self):
        self.assertRaises(currconvert.ConversionException, lambda: self.CC.Convert(1, "FOO", "USD"))
        self.assertRaises(currconvert.ConversionException, lambda: self.CC.Convert(1, "USD", "BAR"))

if __name__ == "__main__":
    unittest.main()
