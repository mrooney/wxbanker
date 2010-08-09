#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    csvimportertests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
import unittest, datetime
from wxbanker.csvimporter import CsvImporter, CsvImporterProfileManager

class CsvImporterTest(unittest.TestCase):
    def setUp(self):
        self.importer = CsvImporter()
        
    def getTransactions(self, csvtype):
        path = testbase.fixturefile("%s.csv"%csvtype)
        profile = CsvImporterProfileManager().getProfile(csvtype)
        container = CsvImporter().getTransactionsFromFile(path, profile)
        return container.Transactions

    def testParseAmountWithSpaceAsThousandsSep(self):
        # Regression test for LP: #370571
        decimalSeparator = ','
        self.assertEquals(self.importer.parseAmount('-1 000,00', decimalSeparator), -1000.0)
        self.assertEquals(self.importer.parseAmount('$ -1 000,00 ', decimalSeparator), -1000.0)
        
    def testCanImportMintData(self):
        transactions = self.getTransactions("mint")
        transactions.sort()
        self.assertEqual(len(transactions), 3)
        self.assertAlmostEqual(sum(t.Amount for t in transactions), 29.46)
        self.assertEqual(transactions[-1].Date, datetime.date(2009, 7, 21))
        self.assertEqual(transactions[-1].Description, "Teavana San Mateo")
        
    def testCanImportSparkasseData(self):
        transactions = self.getTransactions("Sparkasse")
        self.assertEqual(len(transactions), 5)
        
        tran = transactions[1]
        self.assertEqual(tran.Date, datetime.date(2009, 7, 17))
        self.assertEqual(tran.Description, "PHONE CORP, ### , LASTSCHRIFT")
        self.assertEqual(tran.Amount, -31.24)
       
    def testCanImportComdirectData(self):
        transactions = self.getTransactions("comdirect")
        self.assertEqual(len(transactions), 5)
        
        tran = transactions[2]
        self.assertEqual(tran.Date, datetime.date(2010, 3, 8))
        self.assertEqual(tran.Description, "Auftraggeber: XYZ SAGT DANKE Buchungstext: XYZ SAGT DANKE EC 123456789 06.03 14.53 CE0 Ref. ABCDFER213456789/1480  (Lastschrift Einzug)")
        self.assertEqual(tran.Amount, -32.27)   
        

if __name__ == "__main__":
    unittest.main()
