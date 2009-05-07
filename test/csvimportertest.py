#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    csvimportertest.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
#    along with wxBanker.  If not, see <http://www.gnu.org/licenses/>.%

import unittest, sys
sys.path.append('../')

from csvimporter import CsvImporter

class CsvImporterTest(unittest.TestCase):
    def setUp(self):
        self.importer = CsvImporter()
    
    def testParseAmountWithSpaceAsThousandsSep(self):
        ''' regression test for lp bug #370571 '''
        decimalSeparator = ','
        self.assertEquals(self.importer.parseAmount('-1 000,00', decimalSeparator), -1000.0)
        self.assertEquals(self.importer.parseAmount('$ -1 000,00 ', decimalSeparator), -1000.0)

if __name__ == '__main__':
    unittest.main()
