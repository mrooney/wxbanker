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
import unittest, locale, currencies as c

class LocaleTests(unittest.TestCase):
    def testDateParsing(self):
        #INCOMPLETE
        self.assertEquals(locale.setlocale(locale.LC_ALL, 'en_US.utf8'), 'en_US.utf8')

    def testLocaleCurrencyRobustness(self):
        # Test locale.format() thousand separator workaround.
        # Also calculator bug LP: #375308
        # Depends on language-pack-(ru/fr)-base
        for loc in ['en_US.utf8', 'ru_RU.utf8', 'fr_FR.utf8']:
            self.assertEquals(locale.setlocale(locale.LC_ALL, loc), loc)
            reload(c)

            # The test is that none of these calls throw an exception.
            # (including the unicode conversion)
            for curr in c.CurrencyList:
                unicode(curr().float2str(1000))

    def testCommaDecimalSeparater(self):
        loc = "fr_FR.utf8"
        self.assertEqual(locale.setlocale(locale.LC_ALL, loc), loc)
        self.assertEqual(c.CurrencyList[0]().float2str(1), "1,00 €")

if __name__ == "__main__":
    unittest.main()
