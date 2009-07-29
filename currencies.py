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

import localization, locale

def createFromLocale(currencyName):
    """Create a currency from the current locale."""
    new = {}
    local = LocalizedCurrency()
    base = BaseCurrency()
    print "class %sCurrency(BaseCurrency):\n    def __init__(self):\n        BaseCurrency.__init__(self)" % currencyName
    for key, val in local.LOCALECONV.items():
        if not base.LOCALECONV.has_key(key) or base.LOCALECONV[key] != val:
            new[key] = val
            print (" "*8) + "self.LOCALECONV['%s'] = %r" % (key, val)

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

    def float2str(self, val, just=0):
        """Formats float values as currency strings according to the currency settings in self.LOCALECONV"""
        # Don't show negative zeroes!
        if abs(val) < .001:
            val = 0

        # Temporarily override the localeconv dictionary so the locale module acts as the desired locale.
        # Wrap in a try/finally to be extra safe as it needs to be restored no matter what.
        locale._override_localeconv = self.LOCALECONV
        try:
            s = locale.currency(val, grouping=True)
        finally:
            locale._override_localeconv = None

        # locale.localeconv bug http://bugs.python.org/issue1995 workaround.
        if _locale_encoding is not None:
            s = unicode(s, _locale_encoding)

        # Justify as appropriate.
        s = s.rjust(just)

        # Always return unicode!
        if type(s) != unicode:
            s = s.decode("utf-8")
        return s

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
        self.LOCALECONV['decimal_point'] = '.'
        self.LOCALECONV['int_curr_symbol'] = 'RUB '
        self.LOCALECONV['n_cs_precedes'] = 0
        self.LOCALECONV['mon_thousands_sep'] = ' ' #u'\xa0'
        self.LOCALECONV['currency_symbol'] = u'руб' #'\xd1\x80\xd1\x83\xd0\xb1'
        self.LOCALECONV['n_sep_by_space'] = 1
        self.LOCALECONV['p_cs_precedes'] = 0

class UkranianCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['mon_decimal_point'] = u','
        self.LOCALECONV['p_sep_by_space'] = 2
        self.LOCALECONV['thousands_sep'] = ' '#u'\xa0'
        self.LOCALECONV['decimal_point'] = u','
        self.LOCALECONV['int_curr_symbol'] = u'UAH '
        self.LOCALECONV['n_cs_precedes'] = 0
        self.LOCALECONV['mon_thousands_sep'] = ' ' #u'\xa0'
        self.LOCALECONV['currency_symbol'] = u'гр' #u'\u0433\u0440'
        self.LOCALECONV['n_sep_by_space'] = 1
        self.LOCALECONV['p_cs_precedes'] = 0

class MexicanCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['currency_symbol'] = '$'
        self.LOCALECONV['int_curr_symbol'] = 'MXN '

class SwedishCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['mon_decimal_point'] = ','
        self.LOCALECONV['p_sep_by_space'] = 1
        self.LOCALECONV['thousands_sep'] = ' '
        self.LOCALECONV['decimal_point'] = ','
        self.LOCALECONV['int_curr_symbol'] = 'SEK '
        self.LOCALECONV['n_cs_precedes'] = 0
        self.LOCALECONV['mon_thousands_sep'] = ' '
        self.LOCALECONV['currency_symbol'] = 'kr'
        self.LOCALECONV['n_sep_by_space'] = 1
        self.LOCALECONV['p_cs_precedes'] = 0

class LocalizedCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV = locale.localeconv()

        # workaround for the locale.localeconv() bug
        if _locale_encoding is not None:
            self.LOCALECONV.update((k, unicode(v, _locale_encoding)) for k, v in self.LOCALECONV.iteritems() if type(v) is str)


CurrencyList = [LocalizedCurrency, UnitedStatesCurrency, EuroCurrency, GreatBritainCurrency, JapaneseCurrency, RussianCurrency, UkranianCurrency, MexicanCurrency, SwedishCurrency]

# workaround for a locale.localeconv bug http://bugs.python.org/issue1995
# test if float2str raises exceptions, apply a workaround if it does
# NOTE: this happens once at import time, a runtime locale change will require
#       a module reload for this workaround to take effect.
# TODO: can float2str just be updated from python 3.0?
try:
    _locale_encoding = None
    for curr in CurrencyList:
        unicode(curr().float2str(1000))
except UnicodeDecodeError:
    # save the current locale's encoding for use in float2str
    _locale_encoding = locale.getlocale()[1]

def GetCurrencyInt(currency):
    for i, curr in enumerate(CurrencyList):
        if isinstance(currency, curr):
            return i
    return -1

CurrencyStrings = ["%s: %s" % (c().LOCALECONV['int_curr_symbol'].strip(), c().float2str(1)) for c in CurrencyList]
CurrencyStrings[0] += " [%s]" % _("detected")

if __name__ == "__main__":
    import sys
    createFromLocale(sys.argv[1])
