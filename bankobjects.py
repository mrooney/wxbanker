from wx.lib.pubsub import Publisher
import datetime


class Transaction(object):
    """
    An object which represents a transaction.
    
    Changes to this object get sent out via pubsub,
    typically causing the model to make the change.
    """
    def __init__(self, tid, parent, amount, description, date):
        self.IsFrozen = True
        
        self.ID = tid
        self.Parent = parent
        self.Date = date
        self.Description = description
        self.Amount = amount
        
        self.IsFrozen = False
        
    def GetDate(self):
        return self._Date
        
    def SetDate(self, date):
        self._Date = self._MassageDate(date)
            
        if not self.IsFrozen:
            FrozenPublisher.sendMessage("transaction.updated.date", self)
            
    def _MassageDate(self, date):
        """
        Takes a date and returns a valid datetime.date object.
        `date` can be a datetime object, or a string.
        In the case of a string, valid separators are '-' and '/'.
        
        Abbreviated years will be converted into the "intended" year.
    
        >>> _MassageData = Transaction(None, None, 0, "", '2001/01/01')._MassageDate
        >>> _MassageData("2008-01-06")
        datetime.date(2008, 1, 6)
        >>> _MassageData("08-01-06")
        datetime.date(2008, 1, 6)
        >>> _MassageData("86-01-06")
        datetime.date(1986, 1, 6)
        >>> _MassageData("11-01-06")
        datetime.date(2011, 1, 6)
        >>> _MassageData("0-1-6")
        datetime.date(2000, 1, 6)
        >>> _MassageData("0/1/6")
        datetime.date(2000, 1, 6)
        >>> _MassageData(datetime.date(2008, 1, 6))
        datetime.date(2008, 1, 6)
        """
        # The maximum number of years you can refer to in the future, using an abbreviation.
        # Ex: If it is 2008 and MAX_FUTURE_ABBR is 10, years 9-18 will become 2009-2018,
        # while 19-99 will become 1919-1999.
        MAX_FUTURE_ABBR = 10
        date = str(date) #if it is a datetime.date object, make it a Y-M-D string.
        date = date.replace('/', '-') # '-' is our standard assumed separator
        year, m, d = [int(x) for x in date.split("-")]
        if year < 100:
            currentYear = datetime.date.today().year
            currentAbr = currentYear % 100
            currentBase = currentYear / 100
            if year <= currentAbr + MAX_FUTURE_ABBR: #allow the user to reasonably refer to future years
                year += currentBase * 100
            else:
                year += (currentBase-1) * 100
        return datetime.date(year, m, d)
            
    def GetDescription(self):
        return self._Description

    def SetDescription(self, description):
        """Update the description, ensuring it is a string."""
        self._Description = str(description)
        
        if not self.IsFrozen:
            Publisher.sendMessage("transaction.updated.description", self)
            
    def GetAmount(self):
        return self._Amount

    def SetAmount(self, amount):
        """Update the amount, ensuring it is a float."""
        self._Amount = float(amount)
        
        if not self.IsFrozen:
            Publisher.sendMessage("transaction.updated.amount", self)
            
    Date = property(GetDate, SetDate)
    Description = property(GetDescription, SetDescription)
    Amount = property(GetAmount, SetAmount)


class TransactionList(object):
    def __init__(self):
        self.Transactions = {}

    def Add(self, transaction):
        self.Transactions[transaction.ID] = transaction

    def Get(self, tID):
        return self.Transactions[tID]

    def Remove(self, tID):
        del self.Transactions[tID]
        

class AccountList(list):
    def __init__(self, accounts):
        list.__init__(self)
        self.extend(accounts)


class Account(object):
    def __init__(self, name, currency, total=0.0):
        self._Name = name
        self._Transactions = None
        self.Currency = currency
        self.Total = 0.0
        
    def GetTransactions(self):
        if self._Transactions is None:
            # Fetch them into self._Transactions
            pass
        
        return self._Transactions
        
    def GetName(self):
        return self._Name

    def SetName(self, name):
        oldName = self._Name
        self._Name = name
        Publisher.sendMessage("account.renamed.%s"%oldName, name)

    def AddTransaction(self, *args, **kwargs):
        self.TransactionList.Add(Transaction(*args, **kwargs))

    def RemoveTransaction(self, *args, **kwargs):
        self.TransactionList.Remove(*args, **kwargs)
        
    def __cmp__(self, other):
        return cmp(self.Name, other.Name)
    
    Name = property(GetName, SetName)
    Transactions = property(GetTransactions)
        
        
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)