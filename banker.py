"""
Table: accounts
+--------------------------------------------+
| id INTEGER PRIMARY KEY | name VARCHAR(255) |
|------------------------+-------------------|
| 1                      | "My Account"      |
+--------------------------------------------+

Table: transactions
+-------------------------------------------------------------------------------------------------------+
| id INTEGER PRIMARY KEY | accountId INTEGER | amount FLOAT | description VARCHAR(255) | date CHAR(10)) |
|------------------------+-------------------+--------------+--------------------------+----------------|
| 1                      | 1                 | 100.00       | "Initial Balance"        | "2007/01/06"   |
+-------------------------------------------------------------------------------------------------------+

>>> import os
>>> if os.path.exists("test.db"): os.remove("test.db")
>>> b = Bank("test")
>>> b.getAccountNames()
[]
>>> b.getAllTransactions()
[]
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
>>> b.createAccount("My Account")
>>> b.createAccount("My Account")
Traceback (most recent call last):
  ...
AccountAlreadyExistsException: Account 'My Account' already exists.
>>> b.getAccountNames()
[u'My Account']
>>> myId = b.getAccountId("My Account")
>>> b.getBalanceOf("My Account")
0.0
>>> tId = b.makeTransaction("My Account", 100.27, "Initial Balance")
>>> b.getBalanceOf("My Account")
100.27
>>> tId = b.makeTransaction("My Account", -10, "ATM Withdrawal", datetime.date(2007, 1, 6))
>>> balance = b.getBalanceOf("My Account")
>>> float2str(balance)
'$90.27'
>>> b.renameAccount("My Account", "My Renamed Account")
>>> b.getAccountNames()
[u'My Renamed Account']
>>> b.updateTransaction(tId, amount=-101)
>>> balance = b.getBalanceOf("My Renamed Account")
>>> float2str(balance)
'$-0.73'
>>> b.createAccount("Another Account")
>>> sorted(b.getAccountNames()) == sorted([u'My Renamed Account', u'Another Account'])
True
>>> tId = b.makeTransaction("Another Account", -5000.01)
>>> balance = b.getBalanceOf("Another Account")
>>> float2str(balance)
'$-5,000.01'
>>> tId1, tId2 = b.makeTransfer("Another Account", "My Renamed Account", 1.02, "Why not?")
>>> trans = b.getTransactionByID(tId1)
>>> trans[:-1] #doctest: +ELLIPSIS
[..., -1.02, u'Transfer to My Renamed Account (Why not?)']
>>> trans[-1] == datetime.date.today()
True
>>> trans = b.getTransactionByID(tId2)
>>> trans[:-1] #doctest: +ELLIPSIS
[..., 1.02, u'Transfer from Another Account (Why not?)']
>>> trans[-1] == datetime.date.today()
True
>>> float2str(b.getBalanceOf("My Renamed Account"))
'$0.29'
>>> float2str(b.getBalanceOf("Another Account"))
'$-5,001.03'
>>> balance = b.getTotalBalance()
>>> float2str(balance)
'$-5,000.74'
>>> b.removeAccount("Another Account")
>>> b.getAccountNames()
[u'My Renamed Account']
>>> b.getBalanceOf("Another Account")
Traceback (most recent call last):
  ...
InvalidAccountException: Invalid account 'Another Account' specified.
>>> float2str(b.getTotalBalance())
'$0.29'
>>> b.close()
>>> os.remove('test.db')

"""
import time, os, datetime
from model_sqlite import Model

def float2str(number, just=0):
    """
    Converts a float to a pleasing "money string".
    
    >>> float2str(1)
    '$1.00'
    >>> float2str(-2.1)
    '$-2.10'
    >>> float2str(-10.17)
    '$-10.17'
    >>> float2str(-777)
    '$-777.00'
    >>> float2str(12345.67)
    '$12,345.67'
    >>> float2str(12345)
    '$12,345.00'
    >>> float2str(.01)
    '$0.01'
    >>> float2str(.01, 8)
    '   $0.01'
    """
    numStr = '%.2f' % number
    if len(numStr) > 6 + numStr.find('-') + 1: #$ is not added yet
        numStr = numStr[:len(numStr)-6] + ',' + numStr[len(numStr)-6:]
    return ('$'+numStr).rjust(just)

def str2float(str):
    """
    Converts a pleasing "money string" to a float.
    
    >>> str2float('$1.00') == 1.0
    True
    >>> str2float('$-2.10') == -2.1
    True
    >>> str2float('$-10.17') == -10.17
    True
    >>> str2float('$-777.00') == -777
    True
    >>> str2float('$12,345.67') == 12345.67
    True
    >>> str2float('$12,345.00') == 12345
    True
    >>> str2float('$0.01') == 0.01
    True
    >>> str2float('   $0.01') == 0.01
    True
    """
    return float(str.strip()[1:].replace(',', ''))


class InvalidAccountException(Exception):
    def __init__(self, account):
        self.account = account
        
    def __str__(self):
        return "Invalid account '%s' specified."%self.account
    
class AccountAlreadyExistsException(Exception):
    def __init__(self, account):
        self.account = account
        
    def __str__(self):
        return "Account '%s' already exists."%self.account
    
class InvalidTransactionException(Exception):
    def __init__(self, uid):
        self.uid = uid
        
    def __str__(self):
        return "Unable to find transaction with UID %s"%self.uid


class Bank(object):
    def __init__(self, path=None):
        if path is None:
            path = 'bank'
            
        self.model = Model(path)
    
    def getBalanceOf(self, account):
        balance = 0.0
        for transaction in self.getTransactionsFrom(account):
            balance += transaction[1]
        return balance
    
    def getTotalBalance(self):
        total = 0.0
        for account in self.getAccountNames():
            total += self.getBalanceOf(account)
        return total
        
    def getAllTransactions(self):
        transactions = []
        for accountName in self.getAccountNames():
            transactions.extend(self.getTransactionsFrom(accountName))

        return sorted(transactions, cmp=lambda l,r: cmp(l[3], r[3]))
            
    def getTotalsEvery(self, days):
        offset = datetime.timedelta(days)
        transactions = self.getAllTransactions()
        startDate = currentDate = transactions[0][3]
        #lastMonth = currentDate.month

        totals = []
        total = grandTotal = 0.0
        
        for trans in transactions:
            if trans[3] < currentDate + offset:
                #if trans[3].month == lastMonth:
                #print '---%.2f'%trans[0]
                total += trans[1]
            else:
                #print currentDate, total
                totals.append(total)
                total = trans[1]
                currentDate += offset
                #lastMonth = trans[3].month
            grandTotal += trans[1]
        totals.append(total) #append whatever is left over
        
        assert float2str(grandTotal) == float2str(self.getTotalBalance()), (grandTotal, self.getTotalBalance())

        return totals, startDate
        
    def makeTransfer(self, source, destination, amount, desc="", date=None):
        if desc:
            desc = ' (%s)'%desc #add parens around the description if they entered one, otherwise we add a blank string which is fine
        tId1 = self.makeTransaction(source, -amount, ('Transfer to %s'%destination)+desc, date)
        tId2 = self.makeTransaction(destination, amount, ('Transfer from %s'%source)+desc, date)
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

    def removeAccount(self, account):
        if account not in self.getAccountNames():
            raise InvalidAccountException(account)
            
        self.model.removeAccount(account)
        
    def renameAccount(self, oldName, newName):
        #this will return false if an account is renamed to another one, or to the same thing as it was
        currentAccounts = self.getAccountNames()
        if oldName not in currentAccounts:
            raise InvalidAccountException(oldName)
        if newName in currentAccounts:
            raise AccountAlreadyExistsException(newName)
            
        self.model.renameAccount(oldName, newName)
        
    def getTransactionsFrom(self, account):
        if account not in self.getAccountNames():
            raise InvalidAccountException(account)
        
        transactions = self.model.getTransactionsFrom(account)
        return sorted(transactions, cmp=lambda l,r: cmp(l[3], r[3]))
    
    def removeTransaction(self, ID):
        success = self.model.removeTransaction(ID)
        if not success:
            raise InvalidTransactionException(ID)
        
    def getTransactionByID(self, ID):
        transaction = self.model.getTransactionById(ID)
        if transaction is None:
            raise InvalidTransactionException(ID)
        
        return transaction
    
    def updateTransaction(self, uid, amount=None, desc=None, date=None):
        trans = self.model.getTransactionById(uid)

        if amount is not None:
            trans[1] = amount
        if desc is not None:
            trans[2] = desc
        if date is not None:
            trans[3] = date
            
        self.model.updateTransaction(trans)
    
    def makeTransaction(self, account, amount, desc="", date=None):
        """
        Enter a transaction into the specified account.
        
        If no date is specified, the current date will be assumed.
        """
        accountId = self.getAccountId(account)
        
        if date is None:
            date = datetime.date.today()
            
        transaction = (accountId, amount, desc, date)
        return self.model.makeTransaction(transaction)
    
    def close(self):
        self.model.close()

    def save(self, path=None):
        #write out the changes
        self.model.save()


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
    os.system('cls')
    return accountname
    

def main():
    """
    If we are running the actual file, create a command-line
    interface that the user can use.
    """
    bank = Bank()

    choice = -1
    while choice != 0:
        os.system('cls')
        print '1. Create an account'
        print '2. Enter a transaction'
        print '3. Enter a transfer'
        print '4. View Balances'
        print '5. View Transactions'
        print '6. Remove Account'
        print '0. Quit'
        choice = input("? ")

        #TODO: this doesn't work on linux
        os.system('cls')

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
                confirm = raw_input('Transfer %s from %s to %s? [y/n]: '%( float2str(amount), source, destination ))

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
                print "%s %s"%( (account+':').ljust(20), float2str(balance, 10))
                total += balance
            print "%s %s"%( "Total:".ljust(20), float2str(total, 10))

            wait()

        elif choice == 5:
            accountname = _selectAccount(bank.getAccountNames())
            total = 0.0
            for transaction in bank.getTransactionsFrom(accountname):
                uid, amount, desc, date = transaction
                total += amount
                print "%s - %s  %s %s"%( date.strftime('%m/%d/%Y'), desc[:25].ljust(25), float2str(amount, 10), float2str(total, 10) )
            print "Total: %s"%float2str(total)

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
    import doctest
    doctest.testmod()
    #main()

