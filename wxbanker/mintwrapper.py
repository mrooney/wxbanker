#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    mintwrapper.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

from wxbanker.csvimporter import CsvImporterProfileManager, CsvImporter
from wxbanker.mint.api import Mint
from wxbanker import bankexceptions, controller
    
def ImportAccounts(model):
    """For each account in Mint, create one in wxBanker with all known transactions."""
    mintSettings = CsvImporterProfileManager().getProfile("mint")
    importer = CsvImporter()
    for mintId, item in Mint.GetAccounts().items():
        accountName, balance = item['name'], item['balance']
        # Create an account, grab the transactions, and add them.
        try:
            account = model.CreateAccount(accountName)
        except bankexceptions.AccountAlreadyExistsException:
            #account = model.CreateAccount("%s (%s)" % (accountName, mintId))
            print "Account '%s' already exists...skipping." % accountName
            continue
        csv = Mint.GetAccountTransactionsCSV(mintId)
        container = importer.getTransactionsFromCSV(csv, mintSettings)
        transactions = container.Transactions
        account.AddTransactions(transactions)
        
        # Now we have to add an initial transaction for the initial balance.
        if transactions:
            firstTransaction = sorted(transactions)[0]
            initialDate = firstTransaction.Date

            initialBalance = balance - account.Balance
            account.AddTransaction(initialBalance, "Initial Balance", initialDate)
        
        print "Imported account %s with %i transactions" % (accountName, len(transactions))
            
            
def doImport():
    import getpass
    bankController = controller.Controller()
    username = raw_input("Mint email: ")
    password = getpass.getpass("Password: ")
    Mint.Login(username, password)
    ImportAccounts(bankController.Model)

if __name__ == "__main__":
    doImport()

