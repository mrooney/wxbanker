#    https://launchpad.net/wxbanker
#    persistentstore.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

Table: transactions                                                                                       v4
+-------------------------------------------------------------------------------------------------------+----------------+
| id INTEGER PRIMARY KEY | accountId INTEGER | amount FLOAT | description VARCHAR(255) | date CHAR(10)) | linkId INTEGER |
|------------------------+-------------------+--------------+--------------------------+----------------|----------------|
| 1                      | 1                 | 100.00       | "Initial Balance"        | "2007/01/06"   | null           |
+-------------------------------------------------------------------------------------------------------+----------------+
"""
import sys, os, datetime
import bankobjects, currencies, debug
from sqlite3 import dbapi2 as sqlite
import sqlite3
from wx.lib.pubsub import Publisher


class PersistentStore:
    """
    Handles creating the Model (bankobjects) from the store and writing
    back the changes.
    """
    def __init__(self, path, autoSave=True):
        self.Version = 5
        self.Path = path
        self.AutoSave = False
        self.Dirty = False
        self.BatchDepth = 0
        self.cachedModel = None
        existed = False

        if not os.path.exists(self.Path):
            debug.debug('Initializing', self.Path)
            connection = self.initialize()
        else:
            debug.debug('Loading', self.Path)
            connection = sqlite.connect(self.Path)
            existed = True
        self.dbconn = connection

        self.Meta = self.getMeta()
        debug.debug(self.Meta)
        while self.Meta['VERSION'] < self.Version:
            # If we are creating a new db, we don't need to backup each iteration.
            self.upgradeDb(self.Meta['VERSION'], backup=existed)
            self.Meta = self.getMeta()
            debug.debug(self.Meta)

        self.AutoSave = autoSave
        self.commitIfAppropriate()

        self.Subscriptions = (
            (self.onTransactionUpdated, "transaction.updated"),
            (self.onAccountRenamed, "account.renamed"),
            (self.onAccountBalanceChanged, "account.balance changed"),
            (self.onBatchEvent, "batch"),
            (self.onExit, "exiting"),
        )
        
        for callback, topic in self.Subscriptions:
            Publisher.subscribe(callback, topic)
            
        

    def GetModel(self, useCached=True):
        if self.cachedModel is None or not useCached:
            debug.debug('Creating model...')

            # Syncronize cached account balances with the actual. If this needs to be used a bug exists, file it!
            if "--sync-balances" in sys.argv:
                self.syncBalances()

            accounts = self.getAccounts()
            accountList = bankobjects.AccountList(self, accounts)
            self.cachedModel = bankobjects.BankModel(self, accountList)

        return self.cachedModel

    def CreateAccount(self, accountName, currency=0):
        if isinstance(currency, currencies.BaseCurrency):
            currency = currencies.GetCurrencyInt(currency)

        if type(currency) != int or currency < 0:
            raise Exception("Currency code must be int and >= 0")

        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO accounts VALUES (null, ?, ?, ?)', (accountName, currency, 0.0))
        ID = cursor.lastrowid
        self.commitIfAppropriate()

        account = bankobjects.Account(self, ID, accountName, currency)

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
        cursor.execute('INSERT INTO transactions VALUES (null, ?, ?, ?, ?, ?)', [account.ID] + self.transaction2result(transaction)[1:])
        self.commitIfAppropriate()
        transaction.ID = cursor.lastrowid
        return transaction

    def RemoveTransaction(self, transaction):
        result = self.dbconn.cursor().execute('DELETE FROM transactions WHERE id=?', (transaction.ID,)).fetchone()
        self.commitIfAppropriate()
        # The result doesn't appear to be useful here, it is None regardless of whether the DELETE matched anything
        # the controller already checks for existence of the ID though, so if this doesn't raise an exception, theoretically
        # everything is fine. So just return True, as there we no errors that we are aware of.
        return True

    def Save(self):
        import time; t = time.time()
        self.dbconn.commit()
        debug.debug("Committed in %s seconds" % (time.time()-t))
        self.Dirty = False

    def Close(self):
        self.dbconn.close()
        for callback, topic in self.Subscriptions:
            Publisher.unsubscribe(callback)

    def onBatchEvent(self, message):
        batchType = message.topic[1].lower()
        if batchType == "start":
            self.BatchDepth += 1
        elif batchType == "end":
            if self.BatchDepth == 0:
                raise Exception("Cannot end a batch that has not started.")

            self.BatchDepth -= 1
            # If the batching is over, perhaps we should save.
            if self.BatchDepth == 0 and self.Dirty:
                self.commitIfAppropriate()
        else:
            raise Exception("Expected batch type of 'start' or 'end', got '%s'" % batchType)

    def commitIfAppropriate(self):
        # Don't commit if there is a batch in progress.
        if self.AutoSave and not self.BatchDepth:
            self.Save()
        else:
            self.Dirty = True

    def initialize(self):
        connection = sqlite.connect(self.Path)
        cursor = connection.cursor()

        cursor.execute('CREATE TABLE accounts (id INTEGER PRIMARY KEY, name VARCHAR(255), currency INTEGER)')
        cursor.execute('CREATE TABLE transactions (id INTEGER PRIMARY KEY, accountId INTEGER, amount FLOAT, description VARCHAR(255), date CHAR(10))')

        cursor.execute('CREATE TABLE meta (id INTEGER PRIMARY KEY, name VARCHAR(255), value VARCHAR(255))')
        cursor.execute('INSERT INTO meta VALUES (null, ?, ?)', ('VERSION', '2'))

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

    def upgradeDb(self, fromVer, backup=True):
        if backup:
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
        metaVer = None

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
            metaVer = 3
        elif fromVer == 3:
            # Add `linkId` column to transactions for transfers.
            cursor.execute('ALTER TABLE transactions ADD linkId INTEGER')
            metaVer = 4
        elif fromVer == 4:
            # Add recurring transactions table.
            transactionBase = "id INTEGER PRIMARY KEY, accountId INTEGER, amount FLOAT, description VARCHAR(255), date CHAR(10)"
            recurringExtra = "repeatType INTEGER, repeatEvery INTEGER, repeatsOn VARCHAR(255), endDate CHAR(10)"
            cursor.execute('CREATE TABLE recurring_transactions (%s, %s)' % (transactionBase, recurringExtra))
            metaVer = 5
        else:
            raise Exception("Cannot upgrade database from version %i"%fromVer)

        # Update the meta version if appropriate.
        if metaVer:
            cursor.execute('UPDATE meta SET value=? WHERE name=?', (metaVer, "VERSION"))

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
        return [transObj.ID, transObj.Amount, transObj.Description, dateStr, transObj.GetLinkedTransactionID()]

    def result2account(self, result):
        ID, name, currency, balance = result
        return bankobjects.Account(self, ID, name, currency, balance)

    def getAccounts(self):
        return [self.result2account(result) for result in self.dbconn.cursor().execute("SELECT * FROM accounts").fetchall()]

    def clearAccountTransactions(self, account):
        self.dbconn.cursor().execute('DELETE FROM transactions WHERE accountId=?', (account.ID,))
        self.commitIfAppropriate()

    def result2transaction(self, result, linkedTransaction=None):
        tid, pid, amount, description, date, linkId = result
        t = bankobjects.Transaction(tid, pid, amount, description, date)

        # Handle linked transactions.
        if linkedTransaction:
            t.LinkedTransaction = linkedTransaction
        elif linkId:
            t.LinkedTransaction = self.getTransactionById(linkId, linked=t)

        return t

    def getTransactionsFrom(self, account):
        transactions = bankobjects.TransactionList()
        for result in self.dbconn.cursor().execute('SELECT * FROM transactions WHERE accountId=?', (account.ID,)).fetchall():
            t = self.result2transaction(result)
            transactions.append(t)
        return transactions

    def getTransactionById(self, id, linked=None):
        result = self.dbconn.cursor().execute('SELECT * FROM transactions WHERE id=? LIMIT 1', (id,)).fetchone()
        transaction = self.result2transaction(result, linkedTransaction=linked)
        return transaction

    def updateTransaction(self, transObj):
        result = self.transaction2result(transObj)
        result.append( result.pop(0) ) # Move the uid to the back as it is last in the args below.
        self.dbconn.cursor().execute('UPDATE transactions SET amount=?, description=?, date=?, linkId=? WHERE id=?', result)
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

    def onExit(self, message):
        if self.Dirty:
            Publisher.sendMessage("warning.dirty exit", message.data)

    def __del__(self):
        self.commitIfAppropriate()
        self.Close()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
