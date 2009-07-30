#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    currencytests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
import currencies, locale

class CurrencyTest(unittest.TestCase):
    def testUSD(self):
        usd = currencies.UnitedStatesCurrency()
        self.assertEqual(usd.float2str(1), '$1.00')
        self.assertEqual(usd.float2str(-2.1), '-$2.10')
        self.assertEqual(usd.float2str(-10.17), '-$10.17')
        self.assertEqual(usd.float2str(-777), '-$777.00')
        self.assertEqual(usd.float2str(12345.67), '$12,345.67')
        self.assertEqual(usd.float2str(12345), '$12,345.00')
        self.assertEqual(usd.float2str(-12345.67), '-$12,345.67')
        self.assertEqual(usd.float2str(-12345.6), '-$12,345.60')
        self.assertEqual(usd.float2str(-123456), '-$123,456.00')
        self.assertEqual(usd.float2str(1234567890), '$1,234,567,890.00')
        self.assertEqual(usd.float2str(.01), '$0.01')
        self.assertEqual(usd.float2str(.01, 8), '   $0.01')

    def testNoNegativeZeroes(self):
        usd = currencies.UnitedStatesCurrency()
        tinyNegative = 2.1-2.2+.1
        self.assertTrue(tinyNegative < 0)
        self.assertEqual(usd.float2str(tinyNegative), u'$0.00')

    def testCurrencyLocalizes(self):
        self.assertEqual(locale.setlocale(locale.LC_ALL, 'ru_RU.utf8'), 'ru_RU.utf8')
        self.assertEqual(currencies.LocalizedCurrency().float2str(1), u'1.00 руб')
        self.assertTrue(bool(locale.setlocale(locale.LC_ALL, '')))

    def testCurrencyDisplay(self):
        # First make sure we know how many currencies there are. If this is wrong, we are
        # testing too much or not enough and need to alter the test.
        self.assertEqual(len(currencies.CurrencyList), 9)

        testAmount = 1234.5
        self.assertEqual(locale.setlocale(locale.LC_ALL, 'en_US.utf8'), 'en_US.utf8')
        self.assertEqual(currencies.LocalizedCurrency().float2str(testAmount), u'$1,234.50')
        self.assertEqual(currencies.UnitedStatesCurrency().float2str(testAmount), u'$1,234.50')
        self.assertEqual(currencies.EuroCurrency().float2str(testAmount), u'1 234,50 €')
        self.assertEqual(currencies.GreatBritainCurrency().float2str(testAmount), u'£1,234.50')
        self.assertEqual(currencies.JapaneseCurrency().float2str(testAmount), u'￥1,234')
        self.assertEqual(currencies.RussianCurrency().float2str(testAmount), u'1 234.50 руб')
        self.assertEqual(currencies.UkranianCurrency().float2str(testAmount), u'1 234,50 гр')
        self.assertEqual(currencies.MexicanCurrency().float2str(testAmount), u'$1,234.50')
        self.assertEqual(currencies.SwedishCurrency().float2str(testAmount), u'1 234,50 kr')


if __name__ == "__main__":
    unittest.main()
