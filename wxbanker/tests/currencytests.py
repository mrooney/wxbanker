#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    currencytests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
import unittest, locale
from wxbanker import currencies

class CurrencyTest(unittest.TestCase):
    def tearDown(self):
        testbase.resetLocale()
        
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
        russianLocale = testbase.LOCALES[1]
        self.assertEqual(locale.setlocale(locale.LC_ALL, russianLocale), russianLocale)
        self.assertEqual(currencies.LocalizedCurrency().float2str(1), u'1.00 руб')

    def testCurrencyDisplay(self):
        # First make sure we know how many currencies there are. If this is wrong, we are
        # testing too much or not enough and need to alter the test.
        self.assertEqual(len(currencies.CurrencyList), 19)

        americanLocale = testbase.LOCALES[0]
        self.assertEqual(locale.setlocale(locale.LC_ALL, americanLocale), americanLocale)
        
        testAmount = 1234.5
        self.assertEqual(currencies.LocalizedCurrency().float2str(testAmount), u'$1,234.50')
        self.assertEqual(currencies.UnitedStatesCurrency().float2str(testAmount), u'$1,234.50')
        self.assertEqual(currencies.EuroCurrency().float2str(testAmount), u'1 234,50 €')
        self.assertEqual(currencies.GreatBritainCurrency().float2str(testAmount), u'£1,234.50')
        self.assertEqual(currencies.JapaneseCurrency().float2str(testAmount), u'￥1,234')
        self.assertEqual(currencies.RussianCurrency().float2str(testAmount), u'1 234.50 руб')
        self.assertEqual(currencies.UkranianCurrency().float2str(testAmount), u'1 234,50 гр')
        self.assertEqual(currencies.MexicanCurrency().float2str(testAmount), u'$1,234.50')
        self.assertEqual(currencies.SwedishCurrency().float2str(testAmount), u'1 234,50 kr')
        self.assertEqual(currencies.SaudiCurrency().float2str(testAmount), u'1234.50 ريال')
        self.assertEqual(currencies.NorwegianCurrency().float2str(testAmount), u'kr1 234,50')
        self.assertEqual(currencies.ThaiCurrency().float2str(testAmount), u'฿ 1,234.50')
        self.assertEqual(currencies.VietnameseCurrency().float2str(testAmount), u'1.234₫')
        self.assertEqual(currencies.IndianCurrency().float2str(testAmount), u'₨ 1,234.50')
        self.assertEqual(currencies.RomanianCurrency().float2str(testAmount), u'Lei 1.234,50')
        self.assertEqual(currencies.ArabEmiratesCurrency().float2str(testAmount), u'د.إ. 1,234.500')
        self.assertEqual(currencies.LithuanianCurrency().float2str(testAmount), u'1.234,50 Lt')
        self.assertEqual(currencies.SerbianCurrency().float2str(testAmount), u'1.234,50 дин')
        self.assertEqual(currencies.HungarianCurrency().float2str(testAmount), u'1.234,50 Ft')


if __name__ == "__main__":
    unittest.main()
