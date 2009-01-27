#    https://launchpad.net/wxbanker
#    banker.py: Copyright 2007, 2008 Mike Rooney <michael@wxbanker.org>
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


#import time, os, datetime, re
import os
from wx.lib.pubsub import Publisher
import localization, currencies
from testhelpers import displayhook, Subscriber
import bankexceptions, controller
#from bankexceptions import AccountAlreadyExistsException, InvalidAccountException, InvalidTransactionException


class Bank(object):
    """
    Implements the Borg pattern (http://code.activestate.com/recipes/66531/)
    to share state and act as a Singleton in ways, but without caring about
    identity.
    """
    __shared_state = {}
    def __init__(self, path=None):
        self.__dict__ = self.__shared_state
        
        if self.__dict__ == {}:
            assert path is not None
            self.model = Model(path)
            
            index = self.model.getCurrency()
            self.Currency = currencies.CurrencyList[index]()
            
            Publisher().subscribe(self.onCurrencyChanged, "user.currency_changed")
        
        Publisher.subscribe(self.onTransactionUpdated, "transaction.updated")
        Publisher.subscribe(self.onMakeTransfer, "user.transfer")
        Publisher.subscribe(self.onMakeTransaction, "user.transaction")
        
    def float2str(self, flt):
        return self.Currency.float2str(flt)
    
    def str2float(self, moneystr):
        return self.Currency.str2float(moneystr)

    def getBalanceOf(self, account):
        balance = 0.0
        for transaction in self.getTransactionsFrom(account):
            balance += transaction.Amount
        return balance

    def getTotalBalance(self):
        total = 0.0
        for account in self.getAccountNames():
            total += self.getBalanceOf(account)
        return total

    def getAllTransactions(self, sortCmp=None):
        transactions = []
        for accountName in self.getAccountNames():
            transactions.extend(self.getTransactionsFrom(accountName))

        if sortCmp is None:
            sortCmp = lambda l,r: cmp(l.Date, r.Date)
        return sorted(transactions, cmp=sortCmp)

    def getTotalsEvery(self, days):
        transactions = self.getAllTransactions()
        if len(transactions) == 0:
            return [], None

        startDate = currentDate = transactions[0].Date
        #lastMonth = currentDate.month
        offset = datetime.timedelta(days)

        totals = []
        total = grandTotal = 0.0

        for trans in transactions:
            if trans.Date < currentDate + offset:
                #if trans[3].month == lastMonth:
                #print '---%.2f'%trans[0]
                total += trans.Amount
            else:
                #print currentDate, total
                totals.append(total)
                total = trans.Amount
                currentDate += offset
                #lastMonth = trans[3].month
            grandTotal += trans.Amount
        totals.append(total) #append whatever is left over

        assert self.float2str(grandTotal) == self.float2str(self.getTotalBalance()), (grandTotal, self.getTotalBalance())

        return totals, startDate

    def makeTransfer(self, source, destination, amount, desc="", date=None):
        if desc:
            desc = ' (%s)'%desc #add parens around the description if they entered one, otherwise we add a blank string which is fine
        tId1 = self.makeTransaction(source, -amount, (_('Transfer to %s')%destination)+desc, date)
        tId2 = self.makeTransaction(destination, amount, (_('Transfer from %s')%source)+desc, date)
        return (tId1, tId2)

    def getAccountId(self, account):
        ID = self.model.getAccountId(account)
        if ID is None:
            raise InvalidAccountException(account)

        return ID

    def getAccountNames(self):
        return self.model.getAccounts()

    def createAccount(self, account):
        if account in self.getAccountNames():
            raise AccountAlreadyExistsException(account)

        self.model.createAccount(account)
        Publisher().sendMessage("bank.NEW ACCOUNT", account)

    def removeAccount(self, account):
        if account not in self.getAccountNames():
            raise InvalidAccountException(account)

        self.model.removeAccount(account)
        Publisher().sendMessage("bank.REMOVED ACCOUNT", account)

    def renameAccount(self, oldName, newName):
        #this will return false if an account is renamed to another one, or to the same thing as it was
        currentAccounts = self.getAccountNames()
        if oldName not in currentAccounts: #this should never happen
            raise InvalidAccountException(oldName)
        if newName in currentAccounts:
            raise AccountAlreadyExistsException(newName)

        self.model.renameAccount(oldName, newName)
        Publisher().sendMessage("bank.RENAMED ACCOUNT", (oldName, newName))

    def getTransactionsFrom(self, account):
        if account not in self.getAccountNames():
            raise InvalidAccountException(account)

        transactions = self.model.getTransactionsFrom(account)
        return sorted(transactions, cmp=lambda l,r: cmp(l.Date, r.Date))

    def removeTransaction(self, ID):
        if self.model.getTransactionById(ID) is None:
            raise InvalidTransactionException(ID)

        self.model.removeTransaction(ID)
        Publisher().sendMessage("bank.REMOVED TRANSACTION", ID)
        return True

    def getTransactionByID(self, ID):
        transaction = self.model.getTransactionById(ID)
        if transaction is None:
            raise InvalidTransactionException(ID)

        return transaction

    def updateTransaction(self, transaction):
        ##transaction = self.model.getTransactionById(uid)
        self.model.updateTransaction(transaction)
        ##Publisher().sendMessage("bank.UPDATED TRANSACTION")

    def makeTransaction(self, account, amount, desc="", date=None):
        """
        Enter a transaction into the specified account.

        If no date is specified, the current date will be assumed.
        """
        accountId = self.getAccountId(account)

        if date is None:
            date = datetime.date.today()

        lastRowId = self.model.makeTransaction(accountId, amount, desc, date)
        Publisher().sendMessage("bank.NEW TRANSACTION")
        return lastRowId

    def searchTransactions(self, searchString, accountName=None, matchIndex=1, matchCase=False):
        """
        matchIndex: 0: Amount, 1: Description, 2: Date
        I originally used strings here but passing around and then validating on translated
        strings seems like a bad and fragile idea.
        """
        # Handle case-sensitive option.
        reFlag = {False: re.IGNORECASE, True: 0}[matchCase]

        # Handle account options.
        if accountName is None:
            potentials = self.getAllTransactions()
        else:
            potentials = self.getTransactionsFrom(accountName)

        # Find all the matches.
        matches = []
        for potential in potentials:
            potentialStr = str(potential[matchIndex+1]) # +1 as ID is 0
            if re.findall(searchString, potentialStr, flags=reFlag):
                matches.append(potential)
        return matches

    def close(self):
        self.model.close()

    def save(self, path=None):
        #write out the changes
        self.model.save()
        
    def onTransactionUpdated(self, message):
        transaction, previousValue = message.data
        self.updateTransaction(transaction)
        
    def onMakeTransfer(self, message):
        args = message.data
        print 'xfering..'
        self.makeTransfer(*args)
        
    def onMakeTransaction(self, message):
        args = message.data
        print 'xacting..'
        self.makeTransaction(*args)
        
    def setCurrency(self, currencyIndex):
        self.model.setCurrency(currencyIndex)
        self.Currency = currencies.CurrencyList[currencyIndex]()
        Publisher().sendMessage("model.currency_changed", currencyIndex)
        
    def onCurrencyChanged(self, message):
        currencyIndex = message.data
        self.setCurrency(currencyIndex)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        v = True
        if len(sys.argv) == 3 and sys.argv[2] == 'quiet':
            v = False
        import doctest
        doctest.testmod(verbose=v)
    else:
        print "To run the doctests, run banker.py with --test [quiet]"
        print "To run the command line version, run wxbanker.py --cli"
