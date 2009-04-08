#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    currencies.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

"""
>>> import localization
>>> usd = UnitedStatesCurrency()
>>> usd.float2str(1)
'$1.00'
>>> usd.float2str(-2.1)
'-$2.10'
>>> usd.float2str(-10.17)
'-$10.17'
>>> usd.float2str(-777)
'-$777.00'
>>> usd.float2str(12345.67)
'$12,345.67'
>>> usd.float2str(12345)
'$12,345.00'
>>> usd.float2str(-12345.67)
'-$12,345.67'
>>> usd.float2str(-12345.6)
'-$12,345.60'
>>> usd.float2str(-123456)
'-$123,456.00'
>>> usd.float2str(1234567890)
'$1,234,567,890.00'
>>> usd.float2str(.01)
'$0.01'
>>> usd.float2str(.01, 8)
'   $0.01'
>>> usd.float2str(2.1-2.2+.1) == u'$0.00' #test to ensure no negative zeroes
True
>>> locale.setlocale(locale.LC_ALL, 'ru_RU.utf8')
'ru_RU.utf8'
>>> LocalizedCurrency().float2str(1) == '1.00 руб'
True
>>> bool(locale.setlocale(locale.LC_ALL, ''))
True
"""

import localization, locale


class BaseCurrency(object):
    def __init__(self):
        self.LOCALECONV = {
            'decimal_point': '.',
            'frac_digits': 2,
            'grouping': [3, 3, 0],
            'int_frac_digits': 2,
            'mon_decimal_point': '.',
            'mon_grouping': [3, 3, 0],
            'mon_thousands_sep': ',',
            'n_cs_precedes': 1,
            'n_sep_by_space': 0,
            'n_sign_posn': 1,
            'negative_sign': '-',
            'p_cs_precedes': 1,
            'p_sep_by_space': 0,
            'p_sign_posn': 1,
            'positive_sign': '',
            'thousands_sep': ','
        }
        
    def GetCurrencyNick(self):
        return self.LOCALECONV["int_curr_symbol"].strip()
    
    def float2str(self, val, just=0, symbol=True, grouping=True, international=False):
        """
        Formats val according to the currency settings in the current locale.
        Taken from Python 2.5.2 source, Lib/locale.py.
        """
        # Don't show negative zeroes!
        if abs(val) < .001:
            val = 0
            
        conv = self.LOCALECONV
    
        # check for illegal values
        digits = conv[international and 'int_frac_digits' or 'frac_digits']
        if digits == 127:
            raise ValueError("Currency formatting is not possible using "
                             "the 'C' locale.")
    
        s = locale.format('%%.%if' % digits, abs(val), grouping, monetary=True)
        # locale.localeconv bug http://bugs.python.org/issue1995 workaround
        if _locale_encoding is not None:
            s = unicode(s, _locale_encoding)
        # '<' and '>' are markers if the sign must be inserted between symbol and value
        s = '<' + s + '>'
    
        if symbol:
            smb = conv[international and 'int_curr_symbol' or 'currency_symbol']
            precedes = conv[val<0 and 'n_cs_precedes' or 'p_cs_precedes']
            separated = conv[val<0 and 'n_sep_by_space' or 'p_sep_by_space']
    
            if precedes:
                s = smb + (separated and ' ' or '') + s
            else:
                s = s + (separated and ' ' or '') + smb
    
        sign_pos = conv[val<0 and 'n_sign_posn' or 'p_sign_posn']
        sign = conv[val<0 and 'negative_sign' or 'positive_sign']
    
        if sign_pos == 0:
            s = '(' + s + ')'
        elif sign_pos == 1:
            s = sign + s
        elif sign_pos == 2:
            s = s + sign
        elif sign_pos == 3:
            s = s.replace('<', sign)
        elif sign_pos == 4:
            s = s.replace('>', sign)
        else:
            # the default if nothing specified;
            # this should be the most fitting sign position
            s = sign + s
    
        return s.replace('<', '').replace('>', '').rjust(just)
    
    def __eq__(self, other):
        return self.LOCALECONV == other.LOCALECONV
    
    CurrencyNick = property(GetCurrencyNick)
    
class UnitedStatesCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['currency_symbol'] = '$'
        self.LOCALECONV['int_curr_symbol'] = 'USD '
    
class EuroCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['mon_decimal_point'] = ','
        self.LOCALECONV['p_sep_by_space'] = 1
        self.LOCALECONV['thousands_sep'] = ' '
        self.LOCALECONV['decimal_point'] = ','
        self.LOCALECONV['int_curr_symbol'] = 'EUR '
        self.LOCALECONV['n_cs_precedes'] = 0
        self.LOCALECONV['mon_thousands_sep'] = ' '
        self.LOCALECONV['currency_symbol'] = u'€' #'\xe2\x82\xac'
        self.LOCALECONV['n_sep_by_space'] = 1
        self.LOCALECONV['p_cs_precedes'] = 0
        
class GreatBritainCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['int_curr_symbol'] = 'GBP '
        self.LOCALECONV['currency_symbol'] = u'£' #'\xc2\xa3'
        
class JapaneseCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['int_frac_digits'] = 0
        self.LOCALECONV['frac_digits'] = 0
        self.LOCALECONV['n_sign_posn'] = 4
        self.LOCALECONV['int_curr_symbol'] = 'JPY '
        self.LOCALECONV['p_sign_posn'] = 4
        self.LOCALECONV['currency_symbol'] = u'￥' #'\xef\xbf\xa5'
        self.LOCALECONV['mon_grouping'] = [3, 0]
        self.LOCALECONV['grouping'] = [3, 0]
        
class RussianCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['p_sep_by_space'] = 1
        self.LOCALECONV['thousands_sep'] = ' ' #u'\xa0'
        self.LOCALECONV['decimal_point'] = ','
        self.LOCALECONV['int_curr_symbol'] = 'RUB '
        self.LOCALECONV['n_cs_precedes'] = 0
        self.LOCALECONV['mon_thousands_sep'] = ' ' #u'\xa0'
        self.LOCALECONV['currency_symbol'] = u'руб' #'\xd1\x80\xd1\x83\xd0\xb1'
        self.LOCALECONV['n_sep_by_space'] = 1
        self.LOCALECONV['p_cs_precedes'] = 0
        
class LocalizedCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV = locale.localeconv()
        
        # workaround for the locale.localeconv() bug
        if _locale_encoding is not None:
            self.LOCALECONV.update((k, unicode(v, _locale_encoding)) for k, v in self.LOCALECONV.iteritems() if type(v) is str)


CurrencyList = [LocalizedCurrency, UnitedStatesCurrency, EuroCurrency, GreatBritainCurrency, JapaneseCurrency, RussianCurrency]

# workaround for a locale.localeconv bug http://bugs.python.org/issue1995 
# test if float2str raises exceptions, apply a workaround if it does
# NOTE: this happens once at import time, a runtime locale change will require
#       a module reload for this workaround to take effect.
# TODO: can float2str just be updated from python 3.0?
try:
    _locale_encoding = None
    for curr in CurrencyList:
        curr().float2str(1000)
except UnicodeDecodeError:
    # save the current locale's encoding for use in float2str
    _locale_encoding = locale.getlocale()[1]
    
def GetCurrencyInt(currency):
    for i, curr in enumerate(CurrencyList):
        if isinstance(currency, curr):
            return i
    return -1

CurrencyStrings = ["%s: %s" % (c().LOCALECONV['int_curr_symbol'].strip(), c().float2str(1)) for c in CurrencyList]
CurrencyStrings[0] += " [Locale]"
