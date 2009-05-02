#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    currconvert.py: Copyright 2007, 2008 Mike Rooney <mrooney@ubuntu.com>
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

import os, localization
from xml.etree import ElementTree

class ConversionException(Exception): pass

class CurrencyConverter(object):
    """
    >>> import currencies
    >>> c = CurrencyConverter()
    >>> USD = currencies.UnitedStatesCurrency()
    >>> EUR = currencies.EuroCurrency()
    >>> c.Convert(5.23, EUR, EUR) == 5.23
    True
    >>> c.Convert(1, EUR, USD) == 1.2795
    True
    >>> c.Convert(1, USD, EUR) == 1/1.2795
    True
    """
    def __init__(self):
        self.Exchanges = {"EUR": 1.0}
        self.OriginalPath = os.path.join(os.path.dirname(__file__), "exchanges.xml")
        self._loadExchanges()
        
    def _loadExchanges(self):
        tree = ElementTree.fromstring(open(self.OriginalPath).read())
        
        exchanges = tree.getchildren()[-1].getchildren()[0].getchildren()
        for e in exchanges:
            self.Exchanges[e.get("currency")] = float(e.get("rate"))
        
    
    def Convert(self, amount, original, destination):
        """
        Convert an amount from one currency to another. In order to this we
        first convert the original to euros, and then convert that to the
        destination currency, since all rates are based on euros.
        """
        if original == destination:
            return amount
        
        fromStr = original.CurrencyNick
        toStr = destination.CurrencyNick
        
        fromRate = self.Exchanges.get(fromStr)
        toRate = self.Exchanges.get(toStr)
        
        if fromRate is None:
            raise ConversionException(_('No exchange rate for currency "%s"') % fromRate)
        if toRate is None:
            raise ConversionException(_('No exchange rate for currency "%s"') % toRate)
        
        middle = amount * (1.0 / fromRate)
        end = middle * toRate
        
        return end
        
        
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
    