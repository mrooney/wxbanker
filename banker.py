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

"""
Doctests, which ensure the Bank contains all the functionality expected,
including failing when it should.

First, set up a generic event subscriber to make sure that events
are getting published when they should be.

>>> import sys; sys.displayhook = displayhook
>>> messages = Subscriber()

# Ensure that we have a clean, fresh bank by removing a test one
# if it already exists.

>>> import os
>>> if os.path.exists("test.db"): os.remove("test.db")
>>> b = Bank("test.db")
>>> b.getAccountNames()
[]
>>> b.getAllTransactions()
[]

# Now test that the appropriate exceptions are thrown.

>>> print b.getAccountId("My Account")
Traceback (most recent call last):
  ...
InvalidAccountException: Invalid account 'My Account' specified.
>>> b.renameAccount("My Account", "My Renamed Account")
Traceback (most recent call last):
  ...
InvalidAccountException: Invalid account 'My Account' specified.
>>> b.removeAccount("My Account") #should this be an exception?
Traceback (most recent call last):
  ...
InvalidAccountException: Invalid account 'My Account' specified.
>>> b.makeTransaction("My Account", 1, "Initial Balance")
Traceback (most recent call last):
  ...
InvalidAccountException: Invalid account 'My Account' specified.
>>> len(messages) == 0
True

# Now test valid account and transaction manipulation.

>>> b.createAccount("My Account")
>>> len(messages) == 1
True
>>> messages[0]
(('bank', 'NEW ACCOUNT'), 'My Account')
>>> b.createAccount("My Account")
Traceback (most recent call last):
  ...
AccountAlreadyExistsException: Account 'My Account' already exists.
>>> len(messages) == 1
True
>>> b.getAccountNames()
[u'My Account']
>>> myId = b.getAccountId("My Account")
>>> b.getBalanceOf("My Account")
0.0
>>> tId = b.makeTransaction("My Account", 100.27, "Initial Balance")
>>> len(messages) == 2
True
>>> messages[0]
(('bank', 'NEW TRANSACTION'), None)
>>> b.getBalanceOf("My Account")
100.27
>>> tId = b.makeTransaction("My Account", -10, "ATM Withdrawal", datetime.date(2007, 1, 6))
>>> len(messages) == 3
True
>>> messages[0]
(('bank', 'NEW TRANSACTION'), None)
>>> balance = b.getBalanceOf("My Account")
>>> b.float2str(balance)
'$90.27'
>>> b.renameAccount("My Account", "My Renamed Account")
>>> len(messages) == 4
True
>>> messages[0]
(('bank', 'RENAMED ACCOUNT'), ('My Account', 'My Renamed Account'))
>>> b.getAccountNames()
[u'My Renamed Account']
>>> b.updateTransaction(tId, amount=-101)
>>> len(messages) == 5
True
>>> balance = b.getBalanceOf("My Renamed Account")
>>> b.float2str(balance)
'-$0.73'
>>> b.createAccount("Another Account")
>>> sorted(b.getAccountNames()) == sorted([u'My Renamed Account', u'Another Account'])
True
>>> tId = b.makeTransaction("Another Account", -5000.01)
>>> balance = b.getBalanceOf("Another Account")
>>> b.float2str(balance)
'-$5,000.01'
>>> tId1, tId2 = b.makeTransfer("Another Account", "My Renamed Account", 1.02, "Why not?")
>>> trans = b.getTransactionByID(tId1)
>>> trans.Amount, trans.Description
(-1.02, 'Transfer to My Renamed Account (Why not?)')
>>> trans.Date == datetime.date.today()
True
>>> trans = b.getTransactionByID(tId2)
>>> trans.Amount, trans.Description
(1.02, 'Transfer from Another Account (Why not?)')
>>> trans.Date == datetime.date.today()
True
>>> b.float2str(b.getBalanceOf("My Renamed Account"))
'$0.29'
>>> b.float2str(b.getBalanceOf("Another Account"))
'-$5,001.03'
>>> balance = b.getTotalBalance()
>>> b.float2str(balance)
'-$5,000.74'
>>> b.removeAccount("Another Account")
>>> b.getAccountNames()
[u'My Renamed Account']
>>> b.getBalanceOf("Another Account")
Traceback (most recent call last):
  ...
InvalidAccountException: Invalid account 'Another Account' specified.
>>> b.float2str(b.getTotalBalance())
'$0.29'
>>> b.createAccount("Fresh New Account")
>>> b.getBalanceOf("Fresh New Account")
0.0
>>> b.getTransactionsFrom("Fresh New Account")
[]
>>> b.removeTransaction(tId1) #doctest: +ELLIPSIS
Traceback (most recent call last):
  ...
InvalidTransactionException: Unable to find transaction with UID ...
>>> b.removeTransaction(tId2)
True
>>> b.getTransactionByID('FakeID')
Traceback (most recent call last):
  ...
InvalidTransactionException: Unable to find transaction with UID FakeID
>>> b.removeTransaction('FakeID')
Traceback (most recent call last):
  ...
InvalidTransactionException: Unable to find transaction with UID FakeID
>>> b.close()
>>> os.remove('test.db')
"""

import time, os, datetime, re, decimal
from model_sqlite import Model
import  bankobjects
from wx.lib.pubsub import Publisher
import localization, currencies
from testhelpers import displayhook, Subscriber
from bankexceptions import AccountAlreadyExistsException, InvalidAccountException, InvalidTransactionException


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
        balance = decimal.Decimal("0.00")
        for transaction in self.getTransactionsFrom(account):
            balance += transaction.Amount
        return balance

    def getTotalBalance(self):
        total = decimal.Decimal("0.00")
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
        total = grandTotal = decimal.Decimal("0.00")

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
        transaction = message.data
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


#command-line view methods
def wait():
    raw_input("Press enter to continue...")

def _queryDate():
    date = raw_input("Date (leave blank for today) (MM/DD[/YYYY]): ")
    if date == '':
        #cdate = time.gmtime()
        #date = [ cdate[1], cdate[2], cdate[0] ]
        date = datetime.date.today()
    else:
        date = [ int(x) for x in date.split("/") ]
        if len(date) == 2: #if they didn't include the year, assume the current one
            date.append( time.gmtime()[0] )
        date = datetime.date(date[2], date[0], date[1])
    return date

def _selectAccount(accountNames):
    accountlist = {}
    for i, x in enumerate(sorted(accountNames)):
        accountlist[i] = x
    accountnum = input("Account?\n"+"\n".join( [ str(i+1)+". "+accountlist[i] for i in accountlist] )+"\n? ")
    accountname = accountlist[accountnum-1]
    clearScreen()
    return accountname

def clearScreen():
    os.system(['clear','cls'][os.name == 'nt'])

def main():
    """
    If we are running the actual file, create a command-line
    interface that the user can use.
    """
    bank = Bank()

    choice = -1
    while choice != 0:
        clearScreen()
        print '1. Create an account'
        print '2. Enter a transaction'
        print '3. Enter a transfer'
        print '4. View Balances'
        print '5. View Transactions'
        print '6. Remove Account'
        print '0. Quit'
        choice = input("? ")

        clearScreen()

        if choice == 1:
            accountName = raw_input("Account name: ")
            bank.createAccount(accountName)
            bank.save()
            wait()

        elif choice == 2:
            accountName = _selectAccount(bank.getAccountNames())
            amount = input("Amount: $")
            desc = raw_input("Description: ")
            date = _queryDate()
            bank.makeTransaction(accountName, amount, desc, date)
            bank.save()
            print 'Transaction successful.'
            wait()

        elif choice == 3:
            print 'From:'
            source = _selectAccount(bank.getAccountNames())
            print 'To:'
            destination = _selectAccount(bank.getAccountNames())
            amount = input('Amount: $')
            desc = raw_input('Description (optional): ')

            confirm = -1
            while confirm == -1 or confirm.lower() not in ['y', 'n']:
                confirm = raw_input('Transfer %s from %s to %s? [y/n]: '%( bank.float2str(amount), source, destination ))

            if confirm == 'y':
                date = _queryDate()
                bank.makeTransfer(source, destination, amount, desc, date)
                bank.save()
                print 'Transfer successfully entered.'
            else:
                print 'Transfer cancelled.'
            wait()

        elif choice == 4:
            total = 0
            for account in sorted(bank.getAccountNames()):
                balance = bank.getBalanceOf(account)
                print "%s %s"%( (account+':').ljust(20), bank.float2str(balance, 10))
                total += balance
            print "%s %s"%( "Total:".ljust(20), bank.float2str(total, 10))

            wait()

        elif choice == 5:
            accountname = _selectAccount(bank.getAccountNames())
            total = 0.0
            for transaction in bank.getTransactionsFrom(accountname):
                uid, amount, desc, date = transaction
                total += amount
                print "%s - %s  %s %s"%( date.strftime('%m/%d/%Y'), desc[:25].ljust(25), bank.float2str(amount, 10), bank.float2str(total, 10) )
            print "Total: %s"%bank.float2str(total)

            wait()

        elif choice == 6:
            accountName = _selectAccount(bank.getAccountNames())
            confirm = -1
            while confirm == -1 or confirm.lower() not in ['y', 'n']:
                confirm = raw_input('Permanently remove account "%s"? [y/n]: '%accountName)
            if confirm == 'y':
                bank.removeAccount(accountName)
                bank.save()
                print 'Account successfully removed'
            else:
                print 'Account removal cancelled'
            wait()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        v = True
        if len(sys.argv) == 3 and sys.argv[2] == 'quiet':
            v = False
        import doctest
        doctest.testmod(verbose=v)
    else:
        main()

