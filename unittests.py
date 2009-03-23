#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    currencies.py: Copyright 2007-2009 Mike Rooney <michael@wxbanker.org>
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
#    along with wxBanker.  If not, see <http://www.gnu.org/licenses/>.%

import unittest, os, shutil, locale, wx
from wx.lib.pubsub import Publisher
import controller, wxbanker, bankobjects, currencies as c

class LocaleTests(unittest.TestCase):
    def testCurrencyDisplay(self):
        self.assertEquals(locale.setlocale(locale.LC_ALL, 'en_US.utf8'), 'en_US.utf8')
        self.assertEquals(c.LocalizedCurrency().float2str(1), u'$1.00')
        self.assertEquals(c.UnitedStatesCurrency().float2str(1), u'$1.00')
        self.assertEquals(c.EuroCurrency().float2str(1), u'1.00 €')
        self.assertEquals(c.GreatBritainCurrency().float2str(1), u'£1.00')
        self.assertEquals(c.JapaneseCurrency().float2str(1), u'￥1')
        self.assertEquals(c.RussianCurrency().float2str(1), u'1.00 руб')
        
    def testDateParsing(self):
        self.assertEquals(locale.setlocale(locale.LC_ALL, 'en_US.utf8'), 'en_US.utf8')
        
    
    def testLocaleFormatWorkaround(self):
        ''' test locale.format() thousand separator workaround '''
        self.assertEquals(locale.setlocale(locale.LC_ALL, 'ru_RU.utf8'), 'ru_RU.utf8')
        reload(c)
        
        # must not throw an exception
        for curr in c.CurrencyList:
            curr().float2str(1000)
    
class ModelTests(unittest.TestCase):
    def setUp(self):
        Publisher.unsubAll()
        self.ConfigPath = os.path.expanduser("~/.wxBanker")
        self.ConfigPathBackup = self.ConfigPath + ".backup"
        if os.path.exists("test.db"):
            os.remove("test.db")
        if os.path.exists(self.ConfigPath):
            os.rename(self.ConfigPath, self.ConfigPathBackup)
            
        self.Controller = controller.Controller("test.db")
        
    def testControllerIsAutoSavingByDefault(self):
        self.assertTrue( self.Controller.AutoSave )
    
    def testNewAccountIsSameCurrencyAsOthers(self):
        # This test is only valid so long as only one currency is allowed.
        # Otherwise it needs to test a new account gets the right default currency, probably Localized
        import currencies
        model = self.Controller.Model
        
        account = model.CreateAccount("Hello")
        self.assertEqual(account.Currency, currencies.LocalizedCurrency())
        
        account.Currency = currencies.EuroCurrency()
        self.assertEqual(account.Currency, currencies.EuroCurrency())
        
        account2 = model.CreateAccount("Another!")
        self.assertEqual(account2.Currency, currencies.EuroCurrency())
        
    def testBlankModelsAreEqual(self):
        model1 = self.Controller.Model
        model2 = self.Controller.LoadPath("test.db")
        self.assertEqual(model1, model2)
        
    #def testModifiedModelsAreEqual(self):
    #    pass
    
    def testAutoSaveDisabledSimple(self):
        self.Controller.AutoSave = False
        self.assertFalse( self.Controller.AutoSave )
        
        model1 = self.Controller.Model
        a1 = model1.CreateAccount("Checking Account")
        
        model2 = self.Controller.LoadPath("test.db")

        self.assertNotEqual(model1, model2)
        
    def testAutoSaveDisabledComplex(self):
        model1 = self.Controller.Model
        a1 = model1.CreateAccount("Checking Account")
        t1 = a1.AddTransaction(-10, "Description 1")
        
        model2 = self.Controller.LoadPath("test.db")
        self.assertEqual(model1, model2)
        self.Controller.Close(model2)
        
        shutil.copy("test.db", "test2.db")
        self.Controller.AutoSave = False
        #t1.Description = "Description 2"
        t2 = a1.AddTransaction(-10, "Description 1")
        
        model3 = self.Controller.LoadPath("test2.db")
        self.assertFalse(model1 is model3)
        self.assertNotEqual(model1, model3)
        
    def testSimpleMove(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        t1 = a.AddTransaction(-1)
        
        b = model1.CreateAccount("B")
        
        a.MoveTransaction(t1, b)
        
        self.assertFalse(t1 in a.Transactions)
        self.assertTrue(t1 in b.Transactions)
        self.assertNotEqual(t1.Parent, a)
        self.assertEqual(t1.Parent, b)
        
    def testTransactionPropertyBug(self):
        model1 = self.Controller.Model
        a = model1.CreateAccount("A")
        t1 = a.AddTransaction(-1)
        self.assertEqual(len(a.Transactions), 1)
        
    def testSaveEventSaves(self):
        self.Controller.AutoSave = False
        model1 = self.Controller.Model
        
        # Create an account, don't save.
        self.assertEqual(len(model1.Accounts), 0)
        model1.CreateAccount("Hello!")
        self.assertEqual(len(model1.Accounts), 1)
        
        # Make sure that account doesn't exist on a new model
        shutil.copy("test.db", "test2.db")
        model2 = self.Controller.LoadPath("test2.db")
        self.assertEqual(len(model2.Accounts), 0)
        self.assertNotEqual(model1, model2)
        
        # Save
        Publisher.sendMessage("user.saved")
        
        # Make sure it DOES exist after saving.
        shutil.copy("test.db", "test3.db")
        model3 = self.Controller.LoadPath("test3.db")
        self.assertEqual(len(model3.Accounts), 1)
        self.assertEqual(model1, model3)
        self.assertNotEqual(model2, model3)
        
    def tearDown(self):
        self.Controller.Close()
        if os.path.exists("test.db"):
            os.remove("test.db")
        if os.path.exists(self.ConfigPathBackup):
            os.rename(self.ConfigPathBackup, self.ConfigPath)
            
            
class GUITests:#(unittest.TestCase):
    def setUp(self):
        self.ConfigPath = os.path.expanduser("~/.wxBanker")
        self.ConfigPathBackup = self.ConfigPath + ".backup"
        if os.path.exists("test.db"):
            os.remove("test.db")
        if os.path.exists(self.ConfigPath):
            os.rename(self.ConfigPath, self.ConfigPathBackup)
        
        self.App = wxbanker.init("test.db")
        self.Frame = self.App.TopWindow
        
    def testAutoSaveSetAndSaveDisabled(self):
        self.assertTrue( self.Frame.MenuBar.autoSaveMenuItem.IsChecked() )
        self.assertFalse( self.Frame.MenuBar.saveMenuItem.IsEnabled() )
        
    def testAppHasController(self):
        app = wx.GetApp()
        self.assertTrue( hasattr(app, "Controller") )
    
    def tearDown(self):
        if os.path.exists("test.db"):
            os.remove("test.db")
        if os.path.exists(self.ConfigPathBackup):
            os.rename(self.ConfigPathBackup, self.ConfigPath)
        

if __name__ == '__main__':
    unittest.main()
