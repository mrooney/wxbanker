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

import re, getpass
from wxbanker.mint import web
web.enablecookies()

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

    def Login(self, username, password):
        postArgs = {"username": username, "password": password, "task": "L", "nextPage": ""}
        result = web.post("https://wwws.mint.com/loginUserSubmit.xevent", postArgs)
        if "your password?" in result.lower():
            raise MintLoginException("Invalid credentials")
        self._CachedSummary = result
        
    def GetSummary(self):
        if self._CachedSummary is None:
            if Keyring:
                Mint.LoginFromKeyring()
            else:
                raise Exception("Please call Login(username, password) first.")
        
        return self._CachedSummary
        

class Mint:
    """A collection of methods for interfacing with a MintConnection."""
    AccountBalances = {}
    
    @staticmethod
    def Login(username, password):
        MintConnection().Login(username, password)

    @staticmethod
    def LoginFromKeyring():
        if Keyring is None:
            raise Exception("Keyring was unable to be imported")

        keyring = Keyring()
        if not keyring.has_credentials():
            raise Exception("Keyring does not have Mint.com credentials")

        user, passwd = keyring.get_credentials()
        Mint.Login(user, passwd)
        
    @staticmethod
    def GetAccounts():
        """Returns a dictionary like {account_id: (account_name, account_balance)}"""
        summary = MintConnection().GetSummary()
        print summary
        accountsRegex = """accountId=([0-9]+)">([^<]+)</a></h4><h6><span class="last-updated">[^<]+</span>([^<]+)</h6>"""
        balancesRegex = """balance[^>]+>([^<]+)"""
        accounts = re.findall(accountsRegex, summary)
        balances = re.findall(balancesRegex, summary)
        # Ignore the first balance; it is the total.
        balances = balances[1:]

        mintAccounts = {}
        for account, balanceStr in zip(accounts, balances):
            balanceStr = balanceStr.decode("utf-8").replace(u"\u2013", "-") # Mint uses a weird negative sign!
            balanceStr = balanceStr.replace("–".decode("utf-8"), "-") # Mint uses a weird negative sign!
            for char in ",$":
                balanceStr = balanceStr.replace(char, "")
            balance = float(balanceStr)
            aid = account[0]
            name = ("%s %s" % (account[1], account[2])).decode("utf-8")
            mintAccounts[aid] = (name, balance)
        print mintAccounts
        return mintAccounts

    @staticmethod
    def GetAccountBalance(accountid):
        return Mint.GetAccounts()[accountid][1]

    @staticmethod
    def GetAccountTransactionsCSV(accountid):
        return web.read("https://wwws.mint.com/transactionDownload.event?accountId=%s&comparableType=8&offset=0" % accountid)


def main():
    import pprint
    username = raw_input("Username: ")
    password = getpass.getpass("Password: ")

    Mint.Login(username, password)
    accounts = Mint.GetAccounts()
    pprint.pprint(accounts)

    for account in accounts:
        print account, accounts[account]
    
if __name__ == "__main__":
    main()
