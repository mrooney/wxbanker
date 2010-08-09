#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    accountlist.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

from wx.lib.pubsub import Publisher
from wxbanker import bankexceptions

class AccountList(list):
    def __init__(self, store):
        list.__init__(self, store.GetAccounts())
        # Make sure all the items know their parent list.
        for account in self:
            account.Parent = self

        self.Store = store
        self.sort()
        
        Publisher.subscribe(self.onAccountRenamed, "ormobject.updated.Account.Name")
        
    def GetRecurringTransactions(self):
        allRecurrings = []
        for account in self:
            recurrings = account.GetRecurringTransactions()
            if recurrings:
                allRecurrings.extend(recurrings)
                
        return allRecurrings

    def GetBalance(self):
        return sum([account.Balance for account in self])
    
    def GetById(self, theId):
        for account in self:
            if account.ID == theId:
                return account

    def AccountIndex(self, accountName):
        for i, account in enumerate(self):
            if account.Name == accountName:
                return i
        return -1

    def ThrowExceptionOnInvalidName(self, accountName):
        # First make sure we were given a name!
        if not accountName:
            raise bankexceptions.BlankAccountNameException
        # Now ensure an account by that name doesn't already exist.
        if self.AccountIndex(accountName) >= 0:
            raise bankexceptions.AccountAlreadyExistsException(accountName)

    def Create(self, accountName):
        self.ThrowExceptionOnInvalidName(accountName)

        currency = 0
        if len(self):
            # If the list contains items, the currency needs to be consistent.
            currency = self[-1].Currency

        account = self.Store.CreateAccount(accountName, currency)
        # Make sure this account knows its parent.
        account.Parent = self
        self.append(account)
        self.sort()
        Publisher.sendMessage("account.created.%s" % accountName, account)
        return account

    def Remove(self, accountName):
        index = self.AccountIndex(accountName)
        if index == -1:
            raise bankexceptions.InvalidAccountException(accountName)

        account = self.pop(index)
        # Remove all the transactions associated with this account.
        account.Purge()
        
        Publisher.sendMessage("account.removed.%s"%accountName, account)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for leftAccount, rightAccount in zip(self, other):
            if not leftAccount == rightAccount:
                return False

        return True
    
    def onAccountRenamed(self, message):
        self.sort()

    Balance = property(GetBalance)