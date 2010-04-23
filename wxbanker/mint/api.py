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

import re, getpass, datetime
import web
web.enablecookies()

class MintLoginException(Exception):
    pass

class MintConnection:
    """
    A MintConnection represents a static connection to Mint.com, implementing the Borg pattern.
    """
    _shared_state = {}
    
    def __init__(self):
        self.__dict__ = self._shared_state

        if not hasattr(self, "_Initialized"):
            self._CachedSummary = None
            self._Username = None
            self._Password = None
            self._Initialized = True

    def Login(self, username, password):
        postArgs = {"username": username, "password": password, "task": "L", "nextPage": ""}
        result = web.post("https://wwws.mint.com/loginUserSubmit.xevent", postArgs)
        if "forgot your password?" in result.lower():
            raise MintLoginException("Invalid credentials")
        self._CachedSummary = result
        
    def GetSummary(self):
        if self._CachedSummary is None:
            raise Exception("Please call Login(username, password) first.")
        
        return self._CachedSummary
        

class Mint:
    AccountBalances = {}
    
    @staticmethod
    def Login(username, password):
        MintConnection().Login(username, password)
        
    @staticmethod
    def GetAccounts():
        summary = MintConnection().GetSummary()
        accountsRegex = """<a class="" href="transaction.event\?accountId=([0-9]+)">([^<]+)</a></h4><h6><span class="last-updated">[^<]+</span>([^<]+)</h6>"""
        mintAccounts = []
        for account in re.findall(accountsRegex, summary):
            aid = account[0]
            name = "%s %s" % (account[1], account[2])
            mintAccounts.append((name.decode("utf-8"), aid))

        mintAccounts.sort()
        return mintAccounts

    @staticmethod
    def CacheAccountBalance(accountid):
        # Ensure we are logged in.
        summary = MintConnection().GetSummary()
        from BeautifulSoup import BeautifulSoup
        accountPage = web.read("https://wwws.mint.com/transaction.event?accountId=%s" % accountid)
        soup = BeautifulSoup(accountPage)
        balanceStr = soup.find("div", id="account-summary").find("tbody").find("td").contents[0]
        balanceStr = balanceStr.replace("–".decode("utf-8"), "-") # Mint uses a weird negative sign!
        for char in ",$":
            balanceStr = balanceStr.replace(char, "")
        balance = float(balanceStr)
        
        Mint.AccountBalances[accountid] = balance
        
    @staticmethod
    def GetAccountBalance(accountid):
        return Mint.AccountBalances[accountid]

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
        print account[0], Mint.GetAccountBalance(account[1])
    
if __name__ == "__main__":
    main()
