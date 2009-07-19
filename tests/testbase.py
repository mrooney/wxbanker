#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    testbase.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

import os, sys

# make sure path contains both the test dir and its parent (wxbanker root dir)
# we must insert since if wxbanker is installed on the system this would
# otherwise pull in that package first.

testdir = os.path.dirname(__file__)
rootdir = os.path.dirname(testdir)

sys.path.insert(0, testdir)
sys.path.insert(0, rootdir)

# Import wxbanker here so wx gets initialized first, so wxversion calls work properly.
import wxbanker, controller, unittest
from wx.lib.pubsub import Publisher

class TestCaseWithController(unittest.TestCase):
    def setUp(self):
        Publisher.unsubAll()
        self.ConfigPath = os.path.expanduser("~/.wxBanker")
        self.ConfigPathBackup = self.ConfigPath + ".backup"
        if os.path.exists("test.db"):
            os.remove("test.db")
        if os.path.exists(self.ConfigPath):
            os.rename(self.ConfigPath, self.ConfigPathBackup)

        self.Controller = controller.Controller("test.db")
        self.Model = self.Controller.Model

    def tearDown(self):
        self.Controller.Close()
        if os.path.exists("test.db"):
            os.remove("test.db")
        if os.path.exists(self.ConfigPathBackup):
            os.rename(self.ConfigPathBackup, self.ConfigPath)
        Publisher.unsubAll()
