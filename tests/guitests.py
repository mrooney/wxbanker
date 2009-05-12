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

import testbase, os
import controller, unittest, wxbanker
from wx.lib.pubsub import Publisher

class GUITests(unittest.TestCase):
    def setUp(self):
        self.ConfigPath = os.path.expanduser("~/.wxBanker")
        self.ConfigPathBackup = self.ConfigPath + ".backup"
        if os.path.exists("test.db"):
            os.remove("test.db")
        if os.path.exists(self.ConfigPath):
            os.rename(self.ConfigPath, self.ConfigPathBackup)
        
        self.App = wxbanker.init("test.db", welcome=False)
        self.Frame = self.App.TopWindow
        
    def testAutoSaveSetAndSaveDisabled(self):
        self.assertTrue( self.Frame.MenuBar.autoSaveMenuItem.IsChecked() )
        self.assertFalse( self.Frame.MenuBar.saveMenuItem.IsEnabled() )
        
    def testAppHasController(self):
        self.assertTrue( hasattr(self.App, "Controller") )
        
    def testCanAddAndRemoveUnicodeAccount(self):
        self.App.Controller.Model.CreateAccount(u"Lópezहिंदी")
        self.Frame.managePanel.accountCtrl.onRemoveButton(None)
    
    def tearDown(self):
        if os.path.exists("test.db"):
            os.remove("test.db")
        if os.path.exists(self.ConfigPathBackup):
            os.rename(self.ConfigPathBackup, self.ConfigPath)
            
if __name__ == "__main__":
    unittest.main()
