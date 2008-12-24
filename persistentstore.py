#    https://launchpad.net/wxbanker
#    persistentstore.py: Copyright 2007, 2008 Mike Rooney <michael@wxbanker.org>
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
Table: accounts                                v2                 v3
+---------------------------------------------------------------+---------------+
| id INTEGER PRIMARY KEY | name VARCHAR(255) | currency INTEGER | balance FLOAT |
|------------------------+-------------------|------------------|---------------|
| 1                      | "My Account"      | 0                | 0             |
+---------------------------------------------------------------+---------------+

Table: transactions
+-------------------------------------------------------------------------------------------------------+
| id INTEGER PRIMARY KEY | accountId INTEGER | amount FLOAT | description VARCHAR(255) | date CHAR(10)) |
|------------------------+-------------------+--------------+--------------------------+----------------|
| 1                      | 1                 | 100.00       | "Initial Balance"        | "2007/01/06"   |
+-------------------------------------------------------------------------------------------------------+
"""
import sys, os, datetime
import bankobjects
from sqlite3 import dbapi2 as sqlite
import sqlite3
from wx.lib.pubsub import Publisher


DEBUG = "--debug" in sys.argv
def debug(*args):
    if DEBUG:
        for arg in args:
            print arg,
        print ""

class PersistentStore:
    """
    Handles creating the Model (bankobjects) from the store and writing
    back the changes.
    """
    def __init__(self, path):
        self.Version = 3
        self.path = path
        existed = True
        if not os.path.exists(self.path):
            debug('Initializing', path)
            connection = self.initialize()
            existed = False
        else:
            debug('Loading', path)
            connection = sqlite.connect(self.path)

        self.dbconn = connection
        
        self.Meta = self.getMeta()
        debug(self.Meta)
        while self.Meta['VERSION'] < self.Version:
            assert existed # Sanity check to ensure new dbs don't need to be upgraded.
            self.upgradeDb(self.Meta['VERSION'])
            self.Meta = self.getMeta()
            debug(self.Meta)
            
        self.dbconn.commit()
        
        Publisher.subscribe(self.onTransactionUpdated, "transaction.updated")
        Publisher.subscribe(self.onAccountRenamed, "account.renamed")
        
    def GetModel(self):
        debug('Creating model...')
        
        if "--sync-balances" in sys.argv:
            debug("Syncing balances")
            self.syncBalances()
            
        accounts = self.getAccounts()
        accountList = bankobjects.AccountList(self, accounts)
        bankmodel = bankobjects.BankModel(self, accountList)
        
        return bankmodel
    
    def CreateAccount(self, accountName):
        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO accounts VALUES (null, ?, ?, ?)', (accountName, 0, 0.0))
        ID = cursor.lastrowid
        self.dbconn.commit()
        # Ensure there are no orphaned transactions, for accounts removed before #249954 was fixed.
        self.clearAccountTransactions(accountName)
        return bankobjects.Account(self, ID, accountName)
    
    def RemoveAccount(self, accountName):
        # First, remove all the transactions associated with this account.
        # This is necessary to maintain integrity for dbs created at V1 (LP: 249954).
        self.clearAccountTransactions(accountName)
        self.dbconn.cursor().execute('DELETE FROM accounts WHERE name=?',(accountName,))
        self.dbconn.commit()
        
    def MakeTransaction(self, account, transaction):
        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO transactions VALUES (null, ?, ?, ?, ?)', (account.ID, transaction.Amount, transaction.Description, transaction.Date))
        self.dbconn.commit()
        transaction.ID = cursor.lastrowid
        
    def RemoveTransaction(self, transaction):
        result = self.dbconn.cursor().execute('DELETE FROM transactions WHERE id=?', (transaction.ID,)).fetchone()
        self.dbconn.commit()
        # The result doesn't appear to be useful here, it is None regardless of whether the DELETE matched anything
        # the controller already checks for existence of the ID though, so if this doesn't raise an exception, theoretically
        # everything is fine. So just return True, as there we no errors that we are aware of.
        return True

    def initialize(self):
        connection = sqlite.connect(self.path)
        cursor = connection.cursor()

        cursor.execute('CREATE TABLE accounts (id INTEGER PRIMARY KEY, name VARCHAR(255), currency INTEGER, balance FLOAT)')
        cursor.execute('CREATE TABLE transactions (id INTEGER PRIMARY KEY, accountId INTEGER, amount FLOAT, description VARCHAR(255), date CHAR(10))')
        
        cursor.execute('CREATE TABLE meta (id INTEGER PRIMARY KEY, name VARCHAR(255), value VARCHAR(255))')
        cursor.execute('INSERT INTO meta VALUES (null, ?, ?)', ('VERSION', '3'))

        return connection
    
    def getMeta(self):
        try:
            results = self.dbconn.cursor().execute('SELECT * FROM meta').fetchall()
        except sqlite3.OperationalError:
            meta = {'VERSION': 1}
        else:
            meta = {}
            for uid, key, value in results:
                # All values come in as strings but some we want to cast.
                if key == "VERSION":
                    value = int(value)
                    
                meta[key] = value
            
        return meta
    
    def upgradeDb(self, fromVer):
        #TODO: make backup first
        print 'Upgrading db from %i' % fromVer
        cursor = self.dbconn.cursor()
        if fromVer == 1:
            # Add `currency` column to the accounts table with default value 0.
            cursor.execute('ALTER TABLE accounts ADD currency INTEGER not null DEFAULT 0')
            # Add metadata table, with version: 2
            cursor.execute('CREATE TABLE meta (id INTEGER PRIMARY KEY, name VARCHAR(255), value VARCHAR(255))')
            cursor.execute('INSERT INTO meta VALUES (null, ?, ?)', ('VERSION', '2'))
        elif fromVer == 2:
            # Add `total` column to the accounts table.
            cursor.execute('ALTER TABLE accounts ADD balance FLOAT not null DEFAULT 0.0')
            self.syncBalances()
            # Update the meta version number.
            cursor.execute('UPDATE meta SET value=? WHERE name=?', (3, "VERSION"))
        else:
            raise Exception("Cannot upgrade database from version %i"%fromVer)
        
        self.dbconn.commit()
        
    def syncBalances(self):
        for account in self.getAccounts():
            accountTotal = sum([t.Amount for t in self.getTransactionsFrom(account.Name)])
            # Set the correct total.
            self.dbconn.cursor().execute('UPDATE accounts SET balance=? WHERE name=?', (accountTotal, account.Name))
            
    def result2transaction(self, result):
        """
        This method converts this model's specific implementation
        of a transaction into the Bank's generic one.
        """
        return bankobjects.Transaction(*result)

    def transaction2result(self, transObj):
        """
        This method converts the Bank's generic implementation of
        a transaction into this model's specific one.
        """
        dateStr = "%s/%s/%s"%(transObj.Date.year, str(transObj.Date.month).zfill(2), str(transObj.Date.day).zfill(2))
        return [transObj.ID, transObj.Amount, transObj.Description, dateStr]
    
    def result2account(self, result):
        ID, name, currency, balance = result
        return bankobjects.Account(self, ID, name, currency, balance)

    def getAccounts(self):
        return [self.result2account(result) for result in self.dbconn.cursor().execute("SELECT * FROM accounts").fetchall()]
        
    def clearAccountTransactions(self, accountName):
        accountId = self.getAccountId(accountName)
        self.dbconn.cursor().execute('DELETE FROM transactions WHERE accountId=?', (accountId,))
        self.dbconn.commit()
        
    def getAccountId(self, accountName):
        result = self.dbconn.cursor().execute('SELECT * FROM accounts WHERE name=?', (accountName,)).fetchone()
        if result is not None:
            return result[0]
        
    def getTransactionsFrom(self, accountName):
        accountId = self.getAccountId(accountName)
        transactions = []
        for result in self.dbconn.cursor().execute('SELECT * FROM transactions WHERE accountId=?', (accountId,)).fetchall():
            transactions.append(self.result2transaction(result))
        return transactions
    
    def updateTransaction(self, transObj):
        result = self.transaction2result(transObj)
        result.append( result.pop(0) ) # Move the uid to the back as it is last in the args below.
        self.dbconn.cursor().execute('UPDATE transactions SET amount=?, description=?, date=? WHERE id=?', result)
        self.dbconn.commit()
        
    def renameAccount(self, oldName, account):
        self.dbconn.cursor().execute("UPDATE accounts SET name=? WHERE name=?", (account.Name, oldName))
        self.dbconn.commit()
        
    def setCurrency(self, currencyIndex):
        self.dbconn.cursor().execute('UPDATE accounts SET currency=?', (currencyIndex,))
        self.dbconn.commit()
        
    def __print__(self):
        cursor = self.dbconn.cursor()
        for account in cursor.execute("SELECT * FROM accounts").fetchall():
            print account[1]
            for trans in cursor.execute("SELECT * FROM transactions WHERE accountId=?", (account[0],)).fetchall():
                print '  -',trans
                
    def onTransactionUpdated(self, message):
        transaction = message.data
        self.updateTransaction(transaction)
        
    def onAccountRenamed(self, message):
        oldName, account = message.data
        self.renameAccount(oldName, account)
        
    def __del__(self):
        self.dbconn.commit()
        self.dbconn.close()
        
                
if __name__ == "__main__":
    import doctest
    doctest.testmod()
