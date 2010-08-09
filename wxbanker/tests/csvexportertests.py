#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    csvexportertests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker.csvexporter import CsvExporter

class CsvExporterTest(testbase.TestCaseWithController):
    def testExpectedOutput(self):
        model = self.Model
        a = model.CreateAccount("foo")
        a.AddTransaction(1, "Baz", "2010-5-24")
        
        result = CsvExporter.Generate(model)
        
        expected = [
            'Account,Description,Amount,Date',
            'foo,Baz,1.0,2010-05-24'
        ]
        
        self.assertEquals('\r\n'.join(expected)+"\r\n", result)

if __name__ == "__main__":
    unittest.main()
