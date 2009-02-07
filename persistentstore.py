#    https://launchpad.net/wxbanker
#    persistentstore.py: Copyright 2007-2009 Mike Rooney <michael@wxbanker.org>
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
import bankobjects, debug
from sqlite3 import dbapi2 as sqlite
import sqlite3
from wx.lib.pubsub import Publisher


class PersistentStore:
    """
    Handles creating the Model (bankobjects) from the store and writing
    back the changes.
    """
    def __init__(self, path, autoSave=True):
        self.Version = 3
        self.Path = path
        self.AutoSave = autoSave
        existed = True
        if not os.path.exists(self.Path):
            debug.debug('Initializing', self.Path)
            connection = self.initialize()
            existed = False
        else:
            debug.debug('Loading', self.Path)
            connection = sqlite.connect(self.Path)

        self.dbconn = connection
        
        self.Meta = self.getMeta()
        debug.debug(self.Meta)
        while self.Meta['VERSION'] < self.Version:
            if not existed:
                raise Exception("New databases should not need an upgrade, but one was attempted!\nPlease file a bug at https://bugs.launchpad.net/wxbanker/+filebug")
            self.upgradeDb(self.Meta['VERSION'])
            self.Meta = self.getMeta()
            debug.debug(self.Meta)
            
        self.commitIfAppropriate()
        
        Publisher.subscribe(self.onTransactionUpdated, "transaction.updated")
        Publisher.subscribe(self.onAccountRenamed, "account.renamed")
        Publisher.subscribe(self.onAccountBalanceChanged, "account.balance changed")
        
    def GetModel(self):
        debug.debug('Creating model...')
        
        if "--sync-balances" in sys.argv:
            self.syncBalances()
            
        accounts = self.getAccounts()
        accountList = bankobjects.AccountList(self, accounts)
        bankmodel = bankobjects.BankModel(self, accountList)
        
        return bankmodel
    
    def CreateAccount(self, accountName):
        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO accounts VALUES (null, ?, ?, ?)', (accountName, 0, 0.0))
        ID = cursor.lastrowid
        self.commitIfAppropriate()
        
        account = bankobjects.Account(self, ID, accountName)
        
        # Ensure there are no orphaned transactions, for accounts removed before #249954 was fixed.        
        self.clearAccountTransactions(account)
        
        return account
    
    def RemoveAccount(self, account):
        # First, remove all the transactions associated with this account.
        # This is necessary to maintain integrity for dbs created at V1 (LP: 249954).
        self.clearAccountTransactions(account)
        self.dbconn.cursor().execute('DELETE FROM accounts WHERE id=?',(account.ID,))
        self.commitIfAppropriate()
        
    def MakeTransaction(self, account, transaction):
        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO transactions VALUES (null, ?, ?, ?, ?)', (account.ID, transaction.Amount, transaction.Description, transaction.Date))
        self.commitIfAppropriate()
        transaction.ID = cursor.lastrowid
        
    def RemoveTransaction(self, transaction):
        result = self.dbconn.cursor().execute('DELETE FROM transactions WHERE id=?', (transaction.ID,)).fetchone()
        self.commitIfAppropriate()
        # The result doesn't appear to be useful here, it is None regardless of whether the DELETE matched anything
        # the controller already checks for existence of the ID though, so if this doesn't raise an exception, theoretically
        # everything is fine. So just return True, as there we no errors that we are aware of.
        return True
    
    def commitIfAppropriate(self):
        if self.AutoSave:
            debug.debug("Committing db!")
            self.dbconn.commit()

    def initialize(self):
        connection = sqlite.connect(self.Path)
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
        # Make a backup
        source = self.Path
        dest = self.Path + ".backup-v%i-%s" % (fromVer, datetime.date.today().strftime("%Y-%m-%d"))
        debug.debug("Making backup to %s" % dest)
        import shutil
        try:
            shutil.copyfile(source, dest)
        except IOError:
            import traceback; traceback.print_exc()
            raise Exception("Unable to make backup before proceeding with database upgrade...bailing.")
            
        debug.debug('Upgrading db from %i' % fromVer)
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
        
        self.commitIfAppropriate()
        
    def syncBalances(self):
        debug.debug("Syncing balances...")
        for account in self.getAccounts():
            accountTotal = sum([t.Amount for t in self.getTransactionsFrom(account)])
            # Set the correct total.
            self.dbconn.cursor().execute('UPDATE accounts SET balance=? WHERE name=?', (accountTotal, account.Name))

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
        
    def clearAccountTransactions(self, account):
        self.dbconn.cursor().execute('DELETE FROM transactions WHERE accountId=?', (account.ID,))
        self.commitIfAppropriate()
        
    def getTransactionsFrom(self, account):
        transactions = bankobjects.TransactionList()
        for result in self.dbconn.cursor().execute('SELECT * FROM transactions WHERE accountId=?', (account.ID,)).fetchall():
            tid, pid, amount, description, date = result
            transactions.append(bankobjects.Transaction(tid, account, amount, description, date))
        return transactions
    
    def updateTransaction(self, transObj):
        result = self.transaction2result(transObj)
        result.append( result.pop(0) ) # Move the uid to the back as it is last in the args below.
        self.dbconn.cursor().execute('UPDATE transactions SET amount=?, description=?, date=? WHERE id=?', result)
        self.commitIfAppropriate()
        
    def renameAccount(self, oldName, account):
        self.dbconn.cursor().execute("UPDATE accounts SET name=? WHERE name=?", (account.Name, oldName))
        self.commitIfAppropriate()
        
    def setCurrency(self, currencyIndex):
        self.dbconn.cursor().execute('UPDATE accounts SET currency=?', (currencyIndex,))
        self.commitIfAppropriate()
        
    def __print__(self):
        cursor = self.dbconn.cursor()
        for account in cursor.execute("SELECT * FROM accounts").fetchall():
            print account[1]
            for trans in cursor.execute("SELECT * FROM transactions WHERE accountId=?", (account[0],)).fetchall():
                print '  -',trans
                
    def onTransactionUpdated(self, message):
        transaction, previousValue = message.data
        debug.debug("Persisting transaction change: %s" % transaction)
        self.updateTransaction(transaction)
        
    def onAccountRenamed(self, message):
        oldName, account = message.data
        self.renameAccount(oldName, account)
        
    def onAccountBalanceChanged(self, message):
        account = message.data
        self.dbconn.cursor().execute("UPDATE accounts SET balance=? WHERE id=?", (account.Balance, account.ID))
        self.commitIfAppropriate()
        
    def __del__(self):
        self.commitIfAppropriate()
        self.dbconn.close()
        
                
if __name__ == "__main__":
    import doctest
    doctest.testmod()
