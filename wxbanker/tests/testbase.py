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

import os, sys, datetime, locale, unittest
from wxbanker import main, currencies

# Make sure path contains both the test dir and its parent (wxbanker root dir).
here = os.path.dirname(__file__)
testdir = here
rootdir = os.path.dirname(testdir)
# We must insert since if wxbanker is installed on the system this would otherwise pull in that package first.
sys.path.insert(0, testdir)
sys.path.insert(0, rootdir)

# Set up some convenience dates.
today = datetime.date.today()
yesterday = today - datetime.timedelta(days=1)
tomorrow = today + datetime.timedelta(days=1)
one = datetime.timedelta(1)

# The list of locales tested and assumed to be installed and available.
if sys.platform == "win32":
    LOCALES = ['English_United States.1252', 'Russian_Russia.1251', 'French_France.1252']
else:
    LOCALES = ['en_US.utf8', 'ru_RU.utf8', 'fr_FR.utf8']

# Import wxbanker here so wx gets initialized first, so wxversion calls work properly.
import wxbanker
from wxbanker import controller, fileservice
from wx.lib.pubsub import Publisher

def fixturefile(name):
    return fileservice.getSharedFilePath("fixtures", name)

def resetLocale():
    assert bool(locale.setlocale(locale.LC_ALL, ""))
    reload(currencies)

class TestCaseHandlingConfig(unittest.TestCase):
    """
    Handle not stomping over the config file.
    """
    def setUp(self):
        self.ConfigPath = fileservice.getConfigFilePath(controller.Controller.CONFIG_NAME)
        self.ConfigPathBackup = self.ConfigPath + ".backup"
        if os.path.exists(self.ConfigPath):
            os.rename(self.ConfigPath, self.ConfigPathBackup)
            
    def tearDown(self):
        # The backup won't exist if there wasn't an original config to back-up.
        if os.path.exists(self.ConfigPathBackup):
            os.rename(self.ConfigPathBackup, self.ConfigPath)

class TestCaseWithController(TestCaseHandlingConfig):
    """
    This is an abstract test case which handles setting up a database
    (by default in memory) with a controller and model.
    """
    def setUp(self, path=":memory:"):
        TestCaseHandlingConfig.setUp(self)
        Publisher.unsubAll()
        self.Controller = controller.Controller(path)
        self.Model = self.Controller.Model
        
    def tearDown(self):
        self.Controller.Close()
        Publisher.unsubAll()
        TestCaseHandlingConfig.tearDown(self)
        
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
