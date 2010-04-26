#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    minttests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker.mint.api import Mint, MintConnection

class MintTests(testbase.TestCase):
    def testAccountsAvailableAfterParsingIndex(self):
        conn = MintConnection()
        index = open(testbase.fixturefile("mint_index.html")).read()
        expectedAccounts = {
            '1218040': ('PayPal PayPal Balance' , -4277.24),
            '1218022': ('Wells Fargo Dojo Checking', 19497.25)
        }

        conn._CachedSummary = index
        self.assertEqual(index, conn.GetSummary())
        self.assertEqual(Mint.GetAccounts(), expectedAccounts)
