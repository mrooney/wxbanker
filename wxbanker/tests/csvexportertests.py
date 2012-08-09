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
import unittest, datetime, os, tempfile
from wxbanker.csvexporter import CsvExporter


class CsvExporterTest(testbase.TestCaseWithController):
    def assertTransactionExports(self, description):
        model = self.Model
        a = model.CreateAccount("foo")
        a.AddTransaction(1, description, "2010-5-24")
        
        handle, path = tempfile.mkstemp()
        try:
            CsvExporter.Export(model, path)
            result = open(path).read().decode("utf8")
        finally:
            os.remove(path)
        
        expected = [
            u'Account,Description,Amount,Date',
            u'foo,%s,1.0,2010-05-24' % (description),
        ]
        expected = u'\r\n'.join(expected)+u"\r\n"
        self.assertEquals(expected, result)

    def testExpectedOutput(self):
        self.assertTransactionExports("Bar")

    def testExpectedOutputWithUnicode(self):
        self.assertTransactionExports(u'\u0143')


if __name__ == "__main__":
    unittest.main()
