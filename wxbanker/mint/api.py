#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    mint.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker.mint import web
web.enablecookies()
from BeautifulSoup import BeautifulSoup

try:
    from wxbanker.mint.keyring import Keyring
except ImportError:
    print "[WARNING] Unable to import keyring module, Mint.com integration isn't possible."
    import traceback; traceback.print_exc()
    Keyring = None

class MintLoginException(Exception):
    """Thrown on invalid credentials or login error."""
    pass

class MintConnection:
    """A MintConnection represents a static connection to Mint.com."""
    _shared_state = {}
    
    def __init__(self):
        self.__dict__ = self._shared_state
        if not hasattr(self, "_CachedSummary"):
            self._CachedSummary = None

    def Login(self, username, password, notify=True):
        # If we are already logged in, this is a no-op. Use Refresh if you want updated data.
        if self._CachedSummary:
            return
        
        postArgs = {"username": username, "password": password, "task": "L", "nextPage": ""}
        result = web.post("https://wwws.mint.com/loginUserSubmit.xevent", postArgs)
        if "your password?" in result.lower():
            raise MintLoginException("Invalid credentials")
        
        self._CachedSummary = result
        
        if notify:
            Publisher.sendMessage("mint.updated")
        
    def GetSummary(self):
        if self._CachedSummary is None:
            raise Exception("Please call Login(username, password) first.")
        
        return self._CachedSummary
        

class Mint:
    """A collection of methods for interfacing with a MintConnection."""
    _CachedAccounts = None
    
    @staticmethod
    def IsLoggedIn():
        return MintConnection()._CachedSummary is not None
    
    @staticmethod
    def Login(username, password, notify=True):
        return MintConnection().Login(username, password, notify)

    @staticmethod
    def LoginFromKeyring(notify=True):
        if Keyring is None:
            raise Exception("Keyring was unable to be imported")

        keyring = Keyring()
        if not keyring.has_credentials():
            raise Exception("Keyring does not have Mint.com credentials")

        user, passwd = keyring.get_credentials()
        return Mint.Login(user, passwd, notify)
        
    @staticmethod
    def GetAccounts():
        """Returns a dictionary like {account_id: {'name': name, 'balance': balance}}"""
        if Mint._CachedAccounts is None:
            summary = MintConnection().GetSummary()
            soup = BeautifulSoup(summary)
            mintAccounts = {}
            
            for li in soup.findAll("li", "account"):
                h4 = li.find("h4")
                h6 = li.find("h6")
                balanceStr = h4.find("span").contents[0]
                balanceStr = balanceStr.replace("–".decode("utf-8"), "-") # Mint uses a weird negative sign!
                for char in ",$":
                    balanceStr = balanceStr.replace(char, "")
                    
                aid = int(li.get("id").split("-")[1])
                balance = float(balanceStr)
                bankName = h4.find("a").contents[0]
                accountName = h6.contents[1]
                name = bankName + ' ' + accountName
                mintAccounts[aid] = {'name': name, 'balance': balance}
                
            Mint._CachedAccounts = mintAccounts
             
        return Mint._CachedAccounts

    @staticmethod
    def GetAccount(accountid):
        accounts = Mint.GetAccounts()
        account = accounts.get(accountid, None)
        if account is None:
            raise Exception("No such account with ID: %r. Valid accounts: %s" % (accountid, accounts))
        return account
        
    @staticmethod
    def GetAccountBalance(accountid):
        return Mint.GetAccount(accountid)['balance']

    @staticmethod
    def GetAccountTransactionsCSV(accountid):
        return web.read("https://wwws.mint.com/transactionDownload.event?accountId=%s&comparableType=8&offset=0" % accountid)


def main():
    import pprint, getpass
    username = raw_input("Username: ")
    password = getpass.getpass("Password: ")

    #Mint.LoginFromKeyring()
    Mint.Login(username, password)
    accounts = Mint.GetAccounts()
    pprint.pprint(accounts)

    for account in accounts:
        print account, accounts[account]
    
if __name__ == "__main__":
    main()
