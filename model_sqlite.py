#    https://launchpad.net/wxbanker
#    model_sqlite.py: Copyright 2007, 2008 Mike Rooney <wxbanker@rowk.com>
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
This is an implementation of a Bank Model using sqlite3.

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
"""
import os, datetime
import basemodel
from sqlite3 import dbapi2 as sqlite
from wx.lib.pubsub import Publisher

class Model:
    def __init__(self, path):
        self.path = path + os.path.extsep + 'db'
        if not os.path.exists(self.path):
            connection = self.initialize()
        else:
            connection = sqlite.connect(self.path)

        self.dbconn = connection
        
        self.updateCb = lambda message: self.updateTransaction(message.data)
        Publisher.subscribe(self.updateCb, "transaction.updated")

    def initialize(self):
        connection = sqlite.connect(self.path)
        cursor = connection.cursor()

        cursor.execute('CREATE TABLE accounts (id INTEGER PRIMARY KEY, name VARCHAR(255))')
        cursor.execute('CREATE TABLE transactions (id INTEGER PRIMARY KEY, accountId INTEGER, amount FLOAT, description VARCHAR(255), date CHAR(10))')

        return connection

    def result2transaction(self, result):
        """
        This method converts this model's specific implementation
        of a transaction into the Bank's generic one.
        """
        return basemodel.Transaction(*result)

    def transaction2result(self, transObj):
        """
        This method converts the Bank's generic implementation of
        a transaction into this model's specific one.
        """
        dateStr = "%s/%s/%s"%(transObj.Date.year, str(transObj.Date.month).zfill(2), str(transObj.Date.day).zfill(2))
        return [transObj.tID, transObj.Amount, transObj.Description, dateStr]

    def getAccounts(self):
        return sorted([result[1] for result in self.dbconn.cursor().execute("SELECT * FROM accounts").fetchall()])

    def createAccount(self, account):
        self.dbconn.cursor().execute('INSERT INTO accounts VALUES (null, ?)', (account,))
        self.dbconn.commit()
        # ensure there are no orphaned transactions, for accounts removed before #249954 was fixed.
        self.clearAccountTransactions(account)
        
    def clearAccountTransactions(self, account):
        accountId = self.getAccountId(account)
        self.dbconn.cursor().execute('DELETE FROM transactions WHERE accountId=?', (accountId,))
        self.dbconn.commit()
        
    def removeAccount(self, account):
        # remove all the transactions associated with this account
        # this is absolutely necessary to maintain integrity (LP: 249954)
        self.clearAccountTransactions(account)
        self.dbconn.cursor().execute('DELETE FROM accounts WHERE name=?',(account,))
        self.dbconn.commit()

    def renameAccount(self, oldName, newName):
        self.dbconn.cursor().execute("UPDATE accounts SET name=? WHERE name=?", (newName, oldName))
        self.dbconn.commit()

    def getTransactionsFrom(self, account):
        accountId = self.getAccountId(account)
        transactions = []
        for result in self.dbconn.cursor().execute('SELECT * FROM transactions WHERE accountId=?', (accountId,)).fetchall():
            transactions.append(self.result2transaction(result))
        return transactions

    def getAccountId(self, account):
        result = self.dbconn.cursor().execute('SELECT * FROM accounts WHERE name=?', (account,)).fetchone()
        if result is not None:
            return result[0]

    def removeTransaction(self, ID):
        result = self.dbconn.cursor().execute('DELETE FROM transactions WHERE id=?', (ID,)).fetchone()
        self.dbconn.commit()
        #the result doesn't appear to be useful here, it is None regardless of whether the DELETE matched anything
        #the controller already checks for existence of the ID though, so if this doesn't raise an exception, theoretically
        #everything is fine. So just return True, as there we no errors that we are aware of.
        return True

    def getTransactionById(self, ID):
        result = self.dbconn.cursor().execute('SELECT * FROM transactions WHERE id=?', (ID,)).fetchone()
        if result is None:
            return result
        return self.result2transaction(result)

    def updateTransaction(self, transObj):
        result = self.transaction2result(transObj)
        result.append( result.pop(0) ) #move the uid to the back as it is last in the args below
        self.dbconn.cursor().execute('UPDATE transactions SET amount=?, description=?, date=? WHERE id=?', result)
        self.dbconn.commit()

    def makeTransaction(self, transaction):
        result = self.transaction2result(transaction)
        cursor = self.dbconn.cursor()
        cursor.execute('INSERT INTO transactions VALUES (null, ?, ?, ?, ?)', result)
        self.dbconn.commit()
        return cursor.lastrowid

    def close(self):
        self.dbconn.close()

    def save(self):
        self.dbconn.commit()

    def __print__(self):
        cursor = self.dbconn.cursor()

        for account in cursor.execute("SELECT * FROM accounts").fetchall():
            print account[1]
            for trans in cursor.execute("SELECT * FROM transactions WHERE accountId=?", (account[0],)).fetchall():
                print '  -',trans

if __name__ == "__main__":
    import doctest
    doctest.testmod()
