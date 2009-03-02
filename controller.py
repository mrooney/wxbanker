# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    controller.py: Copyright 2007, 2008 Mike Rooney <michael@wxbanker.org>
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

"""
Doctests, which ensure the Bank contains all the functionality expected,
including failing when it should.

First, set up a generic event subscriber to make sure that events
are getting published when they should be.

>>> from testhelpers import Subscriber
>>> messages = Subscriber()
>>> len(messages)
0

# Ensure that we have a clean, fresh bank by removing a test one
# if it already exists.

>>> import os, datetime
>>> if os.path.exists("test.db"): os.remove("test.db")
>>> controller = Controller("test.db")
>>> model = controller.Model
>>> model.Accounts
[]
>>> model.Balance == 0
True

# Now test that the appropriate exceptions are thrown.

>>> model.RemoveAccount("My Account")
Traceback (most recent call last):
  ...
InvalidAccountException: Invalid account 'My Account' specified.

>>> len(messages)
1

# Now test valid account and transaction manipulation.

>>> a1 = model.CreateAccount("My Account")
>>> len(messages)
2
>>> messages[0][1].Name
'My Account'

>>> model.CreateAccount("My Account")
Traceback (most recent call last):
  ...
AccountAlreadyExistsException: Account 'My Account' already exists.
>>> len(messages)
2
>>> len(model.Accounts) == 1
True
>>> a = model.Accounts[0]
>>> a == a1
True
>>> a is a1
True
>>> a.Name
'My Account'
>>> a.Balance
0.0
>>> t1 = a.AddTransaction(100.27, "Initial Balance")
>>> len(a.Transactions)
1
>>> len(messages)
4
>>> messages[1] == (('transaction', 'created'), (a, t1))
True
>>> messages[0] == (('account', 'balance changed', 'My Account'), a)
True
>>> a.Balance
100.27
>>> model.Balance
100.27
>>> t2 = a.AddTransaction(-10, "ATM Withdrawal", datetime.date(2007, 1, 6))
>>> t2.Amount
-10.0
>>> t2.Description
u'ATM Withdrawal'
>>> t2.Date
datetime.date(2007, 1, 6)
>>> len(messages)
6
>>> model.float2str(model.Balance)
'$90.27'

#testRenameAccount
>>> a.Name = "My Renamed Account"
>>> len(messages)
7
>>> messages[0] == (('account', 'renamed', 'My Account'), ('My Account', a))
True
>>> len(model.Accounts)
1
>>> model.Accounts[0].Name
'My Renamed Account'
>>> model.RemoveAccount("My Account")
Traceback (most recent call last):
  ...
InvalidAccountException: Invalid account 'My Account' specified.

#testTransactionUpdating
>>> t1.Amount = -101
>>> len(messages)
9
>>> t1.Amount == -101
True
>>> model.float2str(model.Balance)
'-$111.00'
>>> t1.Description = "Updated description"
>>> len(messages)
10
>>> t1.Description
u'Updated description'
>>> t1.Date = datetime.date(1986, 1, 6)
>>> len(messages)
11
>>> t1.Date == datetime.date(1986, 1, 6)
True

#testSecondAccount
>>> a2 = model.CreateAccount("Another Account")
>>> len(model.Accounts)
2
>>> [x.Name for x in sorted(model.Accounts)]
['Another Account', 'My Renamed Account']

>>> t = a2.AddTransaction(-5000.01)
>>> a2.float2str(a2.Balance)
'-$5,000.01'
>>> model.float2str(model.Balance)
'-$5,111.01'

#testTransfer
>>> amount = 1.02
>>> oldB2, oldB = a2.Balance, a.Balance
>>> oldTotal = model.Balance
>>> t1, t2 = a2.AddTransaction(amount, "Why not?", source=a)
>>> t1.Amount
1.02
>>> t2.Amount
-1.02
>>> model.Balance == oldTotal
True
>>> a2.Balance == oldB2 + amount
True
>>> a.Balance == oldB - amount
True

#testRemoveAccount
>>> oldBalance = a.Balance
>>> len(model.Accounts)
2
>>> a2 in model.Accounts
True
>>> a2.Remove()
>>> len(model.Accounts)
1
>>> a2 in model.Accounts
False
>>> a = model.Accounts[0]
>>> a.Name
'My Renamed Account'

>>> a.Balance == oldBalance
True
>>> a.Balance == model.Balance
True

>>> a3 = model.CreateAccount("Fresh New Account")
>>> a3.Balance
0.0
>>> a3.Transactions
[]

>>> t1 in a.Transactions
False
>>> t1.Parent == a
False
>>> t2 in a.Transactions
True
>>> t2.Parent == a
True
>>> a.RemoveTransaction(t1)
Traceback (most recent call last):
  ...
InvalidTransactionException: Transaction does not exist in account 'My Renamed Account'

>>> t1.Description = u'\xef\xbf\xa5'
>>> t1.Description == u'\xef\xbf\xa5'
True

#>>> model.Search(u'\xef\xbf\xa5') == [t1]
#True

#auto-save
>>> controller.AutoSave = False
>>> controller.AutoSave
False
>>> import shutil; shutil.copy("test.db", "test2.db")
>>> t.Description = "Modified! Did you save?"
>>> model3 = controller.LoadPath("test2.db")
>>> model == model3
False

"""
"""
#*ensure no commits on a store init if not upgrading
"""

from persistentstore import PersistentStore
import wx, os, sys
from wx.lib.pubsub import Publisher
import debug


class Controller(object):
    def __init__(self, path=None, autoSave=True):
        self._AutoSave = autoSave
        self.Models = []
        
        self.LoadPath(path)
        self.InitConfig()
        
        Publisher.subscribe(self.onAutoSaveToggled, "user.autosave_toggled")
        
    def InitConfig(self):
        # Initialize our configuration object.
        # It is only necessary to initialize any default values we
        # have which differ from the default values of the types,
        # so initializing an Int to 0 or a Bool to False is not needed.
        wx.Config.Set(wx.Config("wxBanker"))
        config = wx.Config.Get()
        if not config.HasEntry("SIZE_X"):
            config.WriteInt("SIZE_X", 800)
            config.WriteInt("SIZE_Y", 600)
        if not config.HasEntry("POS_X"):
            config.WriteInt("POS_X", 100)
            config.WriteInt("POS_Y", 100)
        if not config.HasEntry("SHOW_CALC"):
            config.WriteBool("SHOW_CALC", False)
        if not config.HasEntry("AUTO-SAVE"):
            config.WriteBool("AUTO-SAVE", True)
            
        # Set the auto-save option as appropriate.
        self.AutoSave = config.ReadBool("AUTO-SAVE")
        
    def onAutoSaveToggled(self, message):
        val = message.data
        self.AutoSave = val
        
    def GetAutoSave(self):
        return self._AutoSave
    
    def SetAutoSave(self, val):
        self._AutoSave = val
        wx.Config.Get().WriteBool("AUTO-SAVE", val)
        Publisher.sendMessage("controller.autosave_toggled", val)
        for model in self.Models:
            debug.debug("Setting auto-save to: %s" % val)
            model.Store.AutoSave = val
            
    def LoadPath(self, path):
        if path is None:
            # Figure out where the bank database file is, and load it.
            #Note: look at wx.StandardPaths.Get().GetUserDataDir() in the future
            path = os.path.join(os.path.dirname(__file__), 'bank.db')
            if not '--use-local' in sys.argv and 'HOME' in os.environ:
                # We seem to be on a Unix environment.
                preferredPath = os.path.join(os.environ['HOME'], '.wxbanker', 'bank.db')
                if os.path.exists(preferredPath) or not os.path.exists(path):
                    path = preferredPath
                    # Ensure that the directory exists.
                    dirName = os.path.dirname(path)
                    if not os.path.exists(dirName):
                        os.mkdir(dirName)
        
        store = PersistentStore(path)
        store.AutoSave = self.AutoSave
        
        self.Model = store.GetModel()
        self.Models.append(self.Model)
        
        return self.Model
    
    def Close(self, model):
        if not model in self.Models:
            raise Exception("model not managed by this controller")
        
        self.Models.remove(model)
        del model
        
    AutoSave = property(GetAutoSave, SetAutoSave)
    