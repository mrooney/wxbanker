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

# Make sure path contains both the test dir and its parent (wxbanker root dir).
testdir = os.path.dirname(__file__)
rootdir = os.path.dirname(testdir)
# We must insert since if wxbanker is installed on the system this would otherwise pull in that package first.
sys.path.insert(0, testdir)
sys.path.insert(0, rootdir)

# Import wxbanker here so wx gets initialized first, so wxversion calls work properly.
import wxbanker, controller, unittest
from wx.lib.pubsub import Publisher

class TestCaseWithController(unittest.TestCase):
    """
    This is an abstract test case which handles setting up a database
    (by default in memory) with a controller and model. It also
    makes sure not to stomp over an existing config file.
    """
    UNSUBSCRIBE = True
    def setUp(self, path=":memory:", unsubscribe=True):
        if self.UNSUBSCRIBE:
            Publisher.unsubAll()
        
        self.ConfigPath = os.path.expanduser("~/.wxBanker")
        self.ConfigPathBackup = self.ConfigPath + ".backup"
        if os.path.exists(self.ConfigPath):
            os.rename(self.ConfigPath, self.ConfigPathBackup)
            
        if self.UNSUBSCRIBE:
            self.Controller = controller.Controller(path)
            self.Model = self.Controller.Model
        
    def tearDown(self):
        if self.UNSUBSCRIBE:
            self.Controller.Close()
        os.rename(self.ConfigPathBackup, self.ConfigPath)
        if self.UNSUBSCRIBE: Publisher.unsubAll()
        
    def createLinkedTransfers(self):
        a = self.Model.CreateAccount("A")
        b = self.Model.CreateAccount("B")
        atrans, btrans = a.AddTransaction(1, "test", None, source=b)
        return a, b, atrans, btrans

class TestCaseWithControllerOnDisk(TestCaseWithController):
    """
    An extension of TestCaseWithController which puts the db
    on disk and handles clean up of it.
    """
    DBFILE = "test.db"
    
    def removeTestDbIfExists(self):
        if os.path.exists(self.DBFILE):
            os.remove(self.DBFILE)
    
    def setUp(self):
        self.removeTestDbIfExists()
        TestCaseWithController.setUp(self, path=self.DBFILE)

    def tearDown(self):
        TestCaseWithController.tearDown(self)
        self.removeTestDbIfExists()
