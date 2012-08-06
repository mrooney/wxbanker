#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    currencies.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
#
# Usage: LC_ALL=vi_VN.utf8 python -c "from wxbanker.currencies import createFromLocale as c;c('Vietnamese')"

import locale
from wxbanker import localization

def createFromLocale(currencyName):
    """Create a currency class from the current locale."""
    new = {}
    local = LocalizedCurrency()
    base = BaseCurrency()
    currency_class_name = "%sCurrency" % currencyName
    currency_class = "class %s(BaseCurrency):\n    def __init__(self):\n        BaseCurrency.__init__(self)" % currency_class_name
    print currency_class
    for key, val in local.LOCALECONV.items():
        if not base.LOCALECONV.has_key(key) or base.LOCALECONV[key] != val:
            new[key] = val
            if isinstance(val, basestring) and not isinstance(val, unicode):
                val = "u'%s'" % val.decode("utf-8")
            print (" "*8) + "self.LOCALECONV['%s'] = %s" % (key, val)

    base.LOCALECONV = local.LOCALECONV
    testAmount = base.float2str(1234.5)
    currency_assertion = "self.assertEqual(currencies.%sCurrency().float2str(testAmount), u'%s')" % (currencyName, testAmount)
    print currency_assertion
    print "\nThanks for the request, I've added this! How does it look? Examples: \"%s\" and \"%s\"" % (base.float2str(1234.56), base.float2str(-5))

    currencies = open(__file__).read()
    marker = "# " + "__CURRENCY_CLASS__"
    currencies = currencies.replace(marker, currency_class+"\n\n"+marker)
    marker = "# " + "__CURRENCY_CLASS_NAME__"
    currencies = currencies.replace(marker, currency_class_name+"\n    "+marker)
    open(__file__, "w").write(currencies)
    #currencytests = open(

class BaseCurrency(object):
    """
    This object represents the base of a currency, seeded with Western values.
    Subclasses need only change dictionary keys which are different.
    """
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
        ##locale._override_localeconv = self.LOCALECONV # Use this when python2.5 support is dropped.
        localeConvBackup = locale.localeconv
        locale.localeconv = lambda: self.LOCALECONV
        try:
            s = locale.currency(val, grouping=True)
        finally:
            ##locale._override_localeconv = None
            locale.localeconv = localeConvBackup

        if not isinstance(s, unicode):
            s = unicode(s, locale.getlocale()[1])

        # Justify as appropriate.
        s = s.rjust(just)

        return s

    def __eq__(self, other):
        return self.LOCALECONV == other.LOCALECONV

    CurrencyNick = property(GetCurrencyNick)

class UnitedStatesCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['currency_symbol'] = u'$'
        self.LOCALECONV['int_curr_symbol'] = u'USD '

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
        self.LOCALECONV['thousands_sep'] = u' '
        self.LOCALECONV['decimal_point'] = u','
        self.LOCALECONV['int_curr_symbol'] = u'RUB '
        self.LOCALECONV['n_cs_precedes'] = 0
        self.LOCALECONV['mon_thousands_sep'] = u' '
        self.LOCALECONV['currency_symbol'] = u'руб'
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
        self.LOCALECONV['currency_symbol'] = u'$'
        self.LOCALECONV['int_curr_symbol'] = u'MXN '

class SwedishCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['mon_decimal_point'] = u','
        self.LOCALECONV['p_sep_by_space'] = 1
        self.LOCALECONV['thousands_sep'] = u' '
        self.LOCALECONV['decimal_point'] = u','
        self.LOCALECONV['int_curr_symbol'] = u'SEK '
        self.LOCALECONV['n_cs_precedes'] = 0
        self.LOCALECONV['mon_thousands_sep'] = u' '
        self.LOCALECONV['currency_symbol'] = u'kr'
        self.LOCALECONV['n_sep_by_space'] = 1
        self.LOCALECONV['p_cs_precedes'] = 0

class SaudiCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['p_sep_by_space'] = 1
        self.LOCALECONV['thousands_sep'] = u''
        self.LOCALECONV['int_curr_symbol'] = u'SAR '
        self.LOCALECONV['n_cs_precedes'] = 0
        self.LOCALECONV['mon_thousands_sep'] = u''
        self.LOCALECONV['currency_symbol'] = u'ريال'
        self.LOCALECONV['n_sep_by_space'] = 1
        self.LOCALECONV['mon_grouping'] = []
        self.LOCALECONV['p_cs_precedes'] = 0
        self.LOCALECONV['grouping'] = []

class NorwegianCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['mon_decimal_point'] = u','
        self.LOCALECONV['thousands_sep'] = u' '
        self.LOCALECONV['n_sign_posn'] = 4
        self.LOCALECONV['decimal_point'] = u','
        self.LOCALECONV['int_curr_symbol'] = u'NOK '
        self.LOCALECONV['p_sign_posn'] = 4
        self.LOCALECONV['mon_thousands_sep'] = u' '
        self.LOCALECONV['currency_symbol'] = u'kr'

class ThaiCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['p_sep_by_space'] = 2
        self.LOCALECONV['n_sign_posn'] = 4
        self.LOCALECONV['int_curr_symbol'] = u'THB '
        self.LOCALECONV['p_sign_posn'] = 4
        self.LOCALECONV['currency_symbol'] = u'฿'
        self.LOCALECONV['n_sep_by_space'] = 2
        self.LOCALECONV['mon_grouping'] = [3, 0]
        self.LOCALECONV['grouping'] = [3, 0]

class VietnameseCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['mon_decimal_point'] = u','
        self.LOCALECONV['int_frac_digits'] = 0
        self.LOCALECONV['frac_digits'] = 0
        self.LOCALECONV['thousands_sep'] = u'.'
        self.LOCALECONV['decimal_point'] = u','
        self.LOCALECONV['int_curr_symbol'] = u'VND '
        self.LOCALECONV['mon_thousands_sep'] = u'.'
        self.LOCALECONV['currency_symbol'] = u'₫'
        self.LOCALECONV['p_cs_precedes'] = 0

class IndianCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['p_sep_by_space'] = 1
        self.LOCALECONV['int_curr_symbol'] = u'INR '
        self.LOCALECONV['currency_symbol'] = u'₨'
        self.LOCALECONV['n_sep_by_space'] = 1
        self.LOCALECONV['mon_grouping'] = [3, 2, 0]
        self.LOCALECONV['grouping'] = [3, 2, 0]

class RomanianCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['mon_decimal_point'] = u','
        self.LOCALECONV['p_sep_by_space'] = 1
        self.LOCALECONV['thousands_sep'] = u'.'
        self.LOCALECONV['decimal_point'] = u','
        self.LOCALECONV['int_curr_symbol'] = u'RON '
        self.LOCALECONV['mon_thousands_sep'] = u'.'
        self.LOCALECONV['currency_symbol'] = u'Lei'
        self.LOCALECONV['n_sep_by_space'] = 1
        
class ArabEmiratesCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['int_frac_digits'] = 3
        self.LOCALECONV['p_sep_by_space'] = 1
        self.LOCALECONV['frac_digits'] = 3
        self.LOCALECONV['n_sign_posn'] = 2
        self.LOCALECONV['int_curr_symbol'] = u'AED '
        self.LOCALECONV['currency_symbol'] = u'د.إ.'
        self.LOCALECONV['n_sep_by_space'] = 1
        self.LOCALECONV['mon_grouping'] = [3, 0]
        self.LOCALECONV['grouping'] = [3, 0]

class LithuanianCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['mon_decimal_point'] = u','
        self.LOCALECONV['p_sep_by_space'] = 1
        self.LOCALECONV['thousands_sep'] = u'.'
        self.LOCALECONV['decimal_point'] = u','
        self.LOCALECONV['int_curr_symbol'] = u'LTL '
        self.LOCALECONV['n_cs_precedes'] = 0
        self.LOCALECONV['mon_thousands_sep'] = u'.'
        self.LOCALECONV['currency_symbol'] = u'Lt'
        self.LOCALECONV['n_sep_by_space'] = 1
        self.LOCALECONV['p_cs_precedes'] = 0
        
class SerbianCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['mon_decimal_point'] = u','
        self.LOCALECONV['p_sep_by_space'] = 1
        self.LOCALECONV['thousands_sep'] = u''
        self.LOCALECONV['decimal_point'] = u','
        self.LOCALECONV['int_curr_symbol'] = u'RSD '
        self.LOCALECONV['n_cs_precedes'] = 0
        self.LOCALECONV['mon_thousands_sep'] = u'.'
        self.LOCALECONV['currency_symbol'] = u'дин'
        self.LOCALECONV['n_sep_by_space'] = 1
        self.LOCALECONV['p_cs_precedes'] = 0
        self.LOCALECONV['grouping'] = []
        
class HungarianCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV['mon_decimal_point'] = u','
        self.LOCALECONV['p_sep_by_space'] = 1
        self.LOCALECONV['thousands_sep'] = u'.'
        self.LOCALECONV['decimal_point'] = u','
        self.LOCALECONV['int_curr_symbol'] = u'HUF '
        self.LOCALECONV['n_cs_precedes'] = 0
        self.LOCALECONV['mon_thousands_sep'] = u'.'
        self.LOCALECONV['currency_symbol'] = u'Ft'
        self.LOCALECONV['n_sep_by_space'] = 1
        self.LOCALECONV['p_cs_precedes'] = 0

# __CURRENCY_CLASS__

class LocalizedCurrency(BaseCurrency):
    def __init__(self):
        BaseCurrency.__init__(self)
        self.LOCALECONV = locale.localeconv()

def GetCurrencyInt(currency):
    for i, curr in enumerate(CurrencyList):
        if isinstance(currency, curr):
            return i
    return -1

CurrencyList = [
    LocalizedCurrency,
    UnitedStatesCurrency,
    EuroCurrency,
    GreatBritainCurrency,
    JapaneseCurrency,
    RussianCurrency,
    UkranianCurrency,
    MexicanCurrency,
    SwedishCurrency,
    SaudiCurrency,
    NorwegianCurrency,
    ThaiCurrency,
    VietnameseCurrency,
    IndianCurrency,
    RomanianCurrency,
    ArabEmiratesCurrency,
    LithuanianCurrency,
    SerbianCurrency,
    HungarianCurrency,
    # __CURRENCY_CLASS_NAME__
]
CurrencyStrings = ["%s: %s" % (c().LOCALECONV['int_curr_symbol'].strip(), c().float2str(1)) for c in CurrencyList]
CurrencyStrings[0] += " (%s)" % _("detected")

if __name__ == "__main__":
    import sys
    createFromLocale(sys.argv[1])
