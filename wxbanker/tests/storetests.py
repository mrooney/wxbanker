#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    storetests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

class StoreTests(testbase.TestCaseWithController):
    def testRemovingAccountRemovesTransactions(self):
        model = self.Model
        
        def howmany(query):
            return len(model.Store.dbconn.cursor().execute(query).fetchall())
        
        self.assertEqual(howmany("SELECT * FROM accounts"), 0)
        self.assertEqual(howmany("SELECT * FROM transactions"), 0)
        
        foo = model.CreateAccount("Foo")
        foo.AddTransaction(1)
        
        self.assertEqual(howmany("SELECT * FROM accounts"), 1)
        self.assertEqual(howmany("SELECT * FROM transactions"), 1)
        
        model.RemoveAccount(foo.Name)
        
        self.assertEqual(howmany("SELECT * FROM accounts"), 0)
        self.assertEqual(howmany("SELECT * FROM transactions"), 0)
        
        