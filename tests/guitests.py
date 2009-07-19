#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    guitests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

import testbase, wxbanker, controller, unittest
import os
from wx.lib.pubsub import Publisher

class GUITests(testbase.TestCaseHandlingConfig):
    def setUp(self):
        testbase.TestCaseHandlingConfig.setUp(self)
        self.App = wxbanker.init(":memory:", welcome=False)
        self.Frame = self.App.TopWindow

    def testAutoSaveSetAndSaveDisabled(self):
        self.assertTrue( self.Frame.MenuBar.autoSaveMenuItem.IsChecked() )
        self.assertFalse( self.Frame.MenuBar.saveMenuItem.IsEnabled() )

    def testAppHasController(self):
        self.assertTrue( hasattr(self.App, "Controller") )

    def testCanAddAndRemoveUnicodeAccount(self):
        self.App.Controller.Model.CreateAccount(u"Lópezहिंदी")
        # Make sure the account ctrl has the first (0th) selection.
        self.assertEqual(0, self.Frame.managePanel.accountCtrl.currentIndex)
        self.Frame.managePanel.accountCtrl.onRemoveButton(None)

    def testCanAddTransaction(self):
        model = self.App.Controller.Model
        tctrl = self.Frame.managePanel.transactionPanel.newTransCtrl
        a = model.CreateAccount("testCanAddTransaction")

        self.assertEquals(len(a.Transactions), 0)
        self.assertEquals(a.Balance, 0)

        tctrl.amountCtrl.Value = "12.34"
        tctrl.onNewTransaction()

        self.assertEquals(len(a.Transactions), 1)
        self.assertEquals(a.Balance, 12.34)

if __name__ == "__main__":
    unittest.main()
