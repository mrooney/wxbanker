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

import unittest, locale, currencies as c

class LocaleTests(unittest.TestCase):
    def testCurrencyDisplay(self):
        self.assertEquals(locale.setlocale(locale.LC_ALL, 'en_US.utf8'), 'en_US.utf8')
        self.assertEquals(c.LocalizedCurrency().float2str(1), u'$1.00')
        self.assertEquals(c.UnitedStatesCurrency().float2str(1), u'$1.00')
        self.assertEquals(c.EuroCurrency().float2str(1), u'1.00 €')
        self.assertEquals(c.GreatBritainCurrency().float2str(1), u'£1.00')
        self.assertEquals(c.JapaneseCurrency().float2str(1), u'￥1')
        self.assertEquals(c.RussianCurrency().float2str(1), u'1.00 руб')
        
    def testDateParsing(self):
        #INCOMPLETE
        self.assertEquals(locale.setlocale(locale.LC_ALL, 'en_US.utf8'), 'en_US.utf8')
    
    def testLocaleFormatWorkaround(self):
        ''' test locale.format() thousand separator workaround '''
        self.assertEquals(locale.setlocale(locale.LC_ALL, 'ru_RU.utf8'), 'ru_RU.utf8')
        reload(c)
        
        # The test is that none of these calls throw an exception.
        for curr in c.CurrencyList:
            curr().float2str(1000)
