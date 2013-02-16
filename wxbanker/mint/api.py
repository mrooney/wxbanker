#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    mint.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

from wxbanker.lib.mint import api as mintapi

try:
    from wxbanker.mint.keyring import Keyring
except ImportError:
    print "[WARNING] Unable to import keyring module, Mint.com integration isn't possible."
    import traceback; traceback.print_exc()
    Keyring = None

class Mint:
    """A collection of methods for interfacing with a MintConnection."""
    _CachedAccounts = None

    @classmethod
    def IsLoggedIn(cls):
        return cls._CachedAccounts is not None
    
    @classmethod
    def Login(cls, username, password, notify=True):
        if cls.IsLoggedIn():
            return

        accounts = {}
        for account in mintapi.get_accounts(username, password):
            account['balance'] = account['value'] # convert to wxBanker speak
            accounts[account['accountId']] = account
        cls._CachedAccounts = accounts

        if notify:
            Publisher.sendMessage("mint.updated")

    @classmethod
    def LoginFromKeyring(cls, notify=True):
        if Keyring is None:
            raise Exception("Keyring was unable to be imported")

        keyring = Keyring()
        if not keyring.has_credentials():
            raise Exception("Keyring does not have Mint.com credentials")

        user, passwd = keyring.get_credentials()
        return cls.Login(user, passwd, notify)
        
    @classmethod
    def GetAccounts(cls):
        """Returns a dictionary like {account_id: {'name': name, 'balance': balance}}"""
        return cls._CachedAccounts

    @classmethod
    def GetAccount(cls, accountid):
        account = cls.GetAccounts().get(accountid)
        if account is None:
            raise Exception("No such account with ID: %r. Valid accounts: %s" % (accountid, accounts))
        return account
        
    @classmethod
    def GetAccountBalance(cls, accountid):
        return cls.GetAccount(accountid)['balance']

    @staticmethod
    def GetAccountTransactionsCSV(accountid):
        #TODO: update for new Mint.
        return web.read("https://wwws.mint.com/transactionDownload.event?accountId=%s&comparableType=8&offset=0" % accountid)


def main():
    import pprint, getpass
    username = raw_input("Username: ")
    password = getpass.getpass("Password: ")

    #Mint.LoginFromKeyring()
    Mint.Login(username, password)
    accounts = Mint.GetAccounts()

    for account in accounts:
        print account, accounts[account]

if __name__ == "__main__":
    main()
