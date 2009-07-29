#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    localetests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
import unittest, locale, currencies

def assertLocale(loc):
    assert locale.setlocale(locale.LC_ALL, loc) == loc
    reload(currencies)

class LocaleTests(unittest.TestCase):
    # The list of locales tested and assumed to be installed and available.
    LOCALES = ['en_US.utf8', 'ru_RU.utf8', 'fr_FR.utf8']
    TEST_AMOUNT = 1234.5

    def testDateParsing(self):
        #INCOMPLETE
        assertLocale('en_US.utf8')

    def testLocaleCurrencyRobustness(self):
        # Test locale.format() thousand separator workaround.
        # Also calculator bug LP: #375308
        # Depends on language-pack-(ru/fr)-base
        for loc in self.LOCALES:
            assertLocale(loc)

            # The test is that none of these calls throw an exception including the unicode conversion.
            for curr in currencies.CurrencyList:
                unicode(curr().float2str(1000))

# Automatically generate some tests for locales.
localeDisplays = {}
for loc in LocaleTests.LOCALES:
    assertLocale(loc)
    localeDisplays[loc] = currencies.LocalizedCurrency().float2str(LocaleTests.TEST_AMOUNT)

for loc in LocaleTests.LOCALES:
    assertLocale(loc)
    localecurr = currencies.LocalizedCurrency()
    locales = {
        'en_US.utf8':currencies.UnitedStatesCurrency,
        'ru_RU.utf8':currencies.RussianCurrency,
        'fr_FR.utf8':currencies.EuroCurrency,
        }

    for desiredloc in LocaleTests.LOCALES:
        desiredcurr = locales[desiredloc]()
        def test(self, localecurr=localecurr, desiredcurr=desiredcurr, desiredloc=desiredloc):
            self.assertEqual(localeDisplays[desiredloc], desiredcurr.float2str(LocaleTests.TEST_AMOUNT))
        testName = ("test%sDisplays%sProperly"%(localecurr.GetCurrencyNick(), desiredcurr.GetCurrencyNick())).replace(" ", "")
        setattr(LocaleTests, testName, test)

if __name__ == "__main__":
    unittest.main()
