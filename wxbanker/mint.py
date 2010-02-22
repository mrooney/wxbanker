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
from BeautifulSoup import BeautifulSoup
from wxbanker.csvimporter import CsvImporterProfileManager, CsvImporter
from wxbanker import bankexceptions, urllib3
urllib3.enablecookies()

class MintLoginException(Exception): pass


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
        postArgs = {"username": username, "password": self.password, "task": "L", "nextPage": ""}
        result = urllib3.post("https://wwws.mint.com/loginUserSubmit.xevent", postArgs)
        if "forgot your password?" in result.lower():
            raise MintLoginException("Invalid credentials")
        self._CachedSummary = result
        
    def GetSummary(self):
        if self._CachedSummary is None:
            raise Exception("Please call Login(username, password) first.")
        
        return self._CachedSummary
        

class MintDotCom:
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
    def GetAccountBalance(accountid):
        return 1
        accountPage = urllib3.read("https://wwws.mint.com/transaction.event?accountId=%s" % accountid)
        soup = BeautifulSoup(accountPage)
        balanceStr = soup.find("div", id="account-summary").find("tbody").find("td").contents[0]
        balanceStr = balanceStr.replace("–".decode("utf-8"), "-") # Mint uses a weird negative sign!
        for char in ",$":
            balanceStr = balanceStr.replace(char, "")
        balance = float(balanceStr)
        return balance

    @staticmethod
    def GetAccountTransactionsCSV(accountid):
        return urllib3.read("https://wwws.mint.com/transactionDownload.event?accountId=%s&comparableType=8&offset=0" % accountid)
    
    @staticmethod
    def ImportAccounts(model):
        """For each account in Mint, create one in wxBanker with all known transactions."""
        mintSettings = CsvImporterProfileManager().getProfile("mint")
        importer = CsvImporter()
        for accountName, mintId in self.GetAccounts():
            # Create an account, grab the transactions, and add them.
            try:
                account = model.CreateAccount(accountName)
            except bankexceptions.AccountAlreadyExistsException:
                account = model.CreateAccount("%s (%s)" % (accountName, mintId))
            csv = self.GetAccountTransactionsCSV(mintId)
            container = importer.getTransactionsFromCSV(csv, mintSettings)
            transactions = container.Transactions
            account.AddTransactions(transactions)
            
            # Now we have to add an initial transaction for the initial balance.
            if transactions:
                firstTransaction = sorted(transactions)[0]
                initialDate = firstTransaction.Date

                balance = self.GetAccountBalance(mintId)
                initialBalance = balance - account.Balance
                account.AddTransaction(initialBalance, "Initial Balance", initialDate)
            
            print "Imported account %s with %i transactions" % (accountName, len(transactions))
            
            
def doImport():
    from wxbanker import controller
    bankController = controller.Controller()
    
    username = raw_input("Mint email: ")
    password = getpass.getpass("Password: ")
    
    MintDotCom.Login(username, password)
    MintDotCom.ImportAccounts(bankController.Model)

def main():
    import pprint
    username = raw_input("Username: ")
    password = getpass.getpass("Password: ")

    MintDotCom.Login(username, password)
    accounts = MintDotCom.GetAccounts()
    pprint.pprint(accounts)

    for account in accounts:
        print account[0], MintDotCom.GetAccountBalance(account[1])

    print MintDotCom.GetAccountTransactionsCSV(account[1])
        
    
if __name__ == "__main__":
    import sys
    if "--import" in sys.argv:
        doImport()
    else:
        main()
