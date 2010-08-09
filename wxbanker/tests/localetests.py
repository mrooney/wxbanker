#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    localetests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker import currencies
import unittest, locale

def assertLocale(loc=None):
    result = locale.setlocale(locale.LC_ALL, loc)
    assert result == loc, (loc, result)
    reload(currencies)

class LocaleTests(unittest.TestCase):
    TEST_AMOUNT = 1234.5
    
    def tearDown(self):
        testbase.resetLocale()

    def testDateParsing(self):
        #INCOMPLETE
        assertLocale(testbase.LOCALES[0])

    def testLocaleCurrencyRobustness(self):
        # Test locale.format() thousand separator workaround.
        # Also calculator bug LP: #375308
        # Depends on language-pack-(ru/fr)-base
        for loc in testbase.LOCALES:
            assertLocale(loc)

            # The test is that none of these calls throw an exception including the unicode conversion.
            for curr in currencies.CurrencyList:
                unicode(curr().float2str(1000))

# Automatically generate some tests for locales.
localeDisplays = {}
for loc in testbase.LOCALES:
    assertLocale(loc)
    localeDisplays[loc] = currencies.LocalizedCurrency().float2str(LocaleTests.TEST_AMOUNT)

for loc in testbase.LOCALES:
    assertLocale(loc)
    localecurr = currencies.LocalizedCurrency()
    locales = [
        currencies.UnitedStatesCurrency,
        currencies.RussianCurrency,
        currencies.EuroCurrency,
        ]

    for i, desiredloc in enumerate(testbase.LOCALES):
        desiredcurr = locales[i]()
        def test(self, localecurr=localecurr, desiredcurr=desiredcurr, desiredloc=desiredloc):
            self.assertEqual(localeDisplays[desiredloc], desiredcurr.float2str(LocaleTests.TEST_AMOUNT))
        testName = ("test%sDisplays%sProperly"%(localecurr.GetCurrencyNick(), desiredcurr.GetCurrencyNick())).replace(" ", "")
        setattr(LocaleTests, testName, test)

testbase.resetLocale()

if __name__ == "__main__":
    unittest.main()
