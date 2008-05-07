"""
This is an implementation of a Bank Model using sqlite3.
"""
import os, datetime
from sqlite3 import dbapi2 as sqlite

class Model:
    def __init__(self, path):
        self.path = path + os.path.extsep + 'db'
        if not os.path.exists(self.path):
            connection = self.initialize()
        else:
            connection = sqlite.connect(self.path)
        
        self.dbconn = connection

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
        datetup = [int(x) for x in result[4].split('/')]
        if datetup[0] < 10:
            print result
            datetup[0] += 2000
        date = datetime.date(*datetup)
        #print date
        return [result[0], result[2], result[3], date]
    
    def transaction2result(self, transaction):
        """
        This method converts the Bank's generic implementation of
        a transaction into this model's specific one.
        """
        dateStr = "%s/%s/%s"%(transaction[3].year, str(transaction[3].month).zfill(2), str(transaction[3].day).zfill(2))
        return [transaction[0], transaction[1], transaction[2], dateStr]
    
    def getAccounts(self):
        return sorted([result[1] for result in self.dbconn.cursor().execute("SELECT * FROM accounts").fetchall()])
    
    def createAccount(self, account):
        self.dbconn.cursor().execute('INSERT INTO accounts VALUES (null, ?)', (account,))
        self.dbconn.commit()
        
    def removeAccount(self, account):
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
        #the result doesn't appear to be useful here, it is None regardless of whether the DELETE matched anything
        #the controller already checks for existence of the ID though, so if this doesn't raise an exception, theoretically
        #everythin is fine. So just return True.
        return True
    
    def getTransactionById(self, ID):
        result = self.dbconn.cursor().execute('SELECT * FROM transactions WHERE id=?', (ID,)).fetchone()
        if result is None:
            return result
        return self.result2transaction(result)
    
    def updateTransaction(self, transaction):
        result = self.transaction2result(transaction)
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
