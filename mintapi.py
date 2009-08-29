#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    mintapi.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

import urllib3, re, getpass, datetime
from csvimporter import CsvImporterProfileManager, CsvImporter
import bankexceptions
urllib3.enablecookies()

class MintLoginException(Exception): pass


class MintDotCom:
    def __init__(self, user, passwd):
        self._username = user
        self._passwd = passwd
        self._cachedSummary = None

    def Login(self):
        result = urllib3.post("https://wwws.mint.com/loginUserSubmit.xevent", {"username": self._username, "password": self._passwd, "task": "L", "nextPage": ""})
        if "forgot your password?" in result.lower():
            raise MintLoginException("Invalid credentials")
        self._cachedSummary = result

    def ListAccounts(self):
        if self._cachedSummary is None:
            self.Login()

        accountsRegex = """<a class="" href="transaction.event\?accountId=([0-9]+)">([^<]+)</a></h4><h6><span class="last-updated">[^<]+</span>([^<]+)</h6>"""
        mintAccounts = []
        for account in re.findall(accountsRegex, self._cachedSummary):
            aid = account[0]
            name = "%s %s" % (account[1], account[2])
            mintAccounts.append((name.decode("utf-8"), aid))

        mintAccounts.sort()
        return mintAccounts

    def GetAccountBalance(self, accountid):
        accountPage = urllib3.read("https://wwws.mint.com/transaction.event?accountId=%s" % accountid)
        balRegex = """<th>Balance</th><td class="money[^>]+>([^<]+)</td>"""
        balance = re.findall(balRegex, accountPage)[0]
        balance = balance.replace("–", "-") # Mint uses a weird negative sign!
        for char in ",$":
            balance = balance.replace(char, "")
        return float(balance)

    def GetAccountTransactionsCSV(self, accountid):
        return urllib3.read("https://wwws.mint.com/transactionDownload.event?accountId=%s&comparableType=8&offset=0" % accountid)
    
    def ImportAccounts(self, model):
        """For each account in Mint, create one in wxBanker with all known transactions."""
        mintSettings = CsvImporterProfileManager().getProfile("mint")
        importer = CsvImporter()
        for accountName, mintId in self.ListAccounts():
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
    import controller
    bankController = controller.Controller()
    
    username = raw_input("Mint email: ")
    passwd = getpass.getpass("Password: ")
    
    mint = MintDotCom(username, passwd)
    mint.ImportAccounts(bankController.Model)

def main():
    import pprint
    username = raw_input("Username: ")
    password = getpass.getpass("Password: ")

    mint = MintDotCom(username, password)
    accounts = mint.ListAccounts()
    pprint.pprint(accounts)

    for account in accounts:
        print account[0], mint.GetAccountBalance(account[1])

    print mint.GetAccountTransactionsCSV(account[1])
        
    
if __name__ == "__main__":
    import sys
    if "--import" in sys.argv:
        doImport()
    else:
        main()
