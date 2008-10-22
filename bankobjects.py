from wx.lib.pubsub import Publisher
import datetime


def wellFormDate(date):
    """
    Takes a date and returns a valid datetime.date object.
    `date` can be a datetime object, or a string.
    In the case of a string, valid separators are '-' and '/'.
    
    Abbreviated years will be converted into the "intended" year.

    >>> wellFormDate("2008-01-06")
    datetime.date(2008, 1, 6)
    >>> wellFormDate("08-01-06")
    datetime.date(2008, 1, 6)
    >>> wellFormDate("86-01-06")
    datetime.date(1986, 1, 6)
    >>> wellFormDate("11-01-06")
    datetime.date(2011, 1, 6)
    >>> wellFormDate("0-1-6")
    datetime.date(2000, 1, 6)
    >>> wellFormDate("0/1/6")
    datetime.date(2000, 1, 6)
    >>> wellFormDate(datetime.date(2008, 1, 6))
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


class LightweightPropertyObject(object):
    """
    Automatically detects if Setters and/or Getters have been defined,
    and uses them if available when reading and writing parameters.
    """
    def __init__(self):
        object.__init__(self)
        self.freezeCount = 0
            
    def __setattr__(self, attr, value):
        customSetter = 'Set'+attr
        if hasattr(self, customSetter):
            getattr(self, customSetter)(value)
        else:
            object.__setattr__(self, attr, value)

    def __getattr__(self, attr):
        customGetter = 'Get'+attr
        if hasattr(self, customGetter):
            return getattr(self, customGetter)()
        else:
            return object.__getattribute__(self, attr)
        
    def Freeze(self):
        self.freezeCount += 1
        
    def Thaw(self):
        assert self.freezeCount > 0
        self.freezeCount -= 1


class Transaction(object):
    """
    An object which represents a transaction.
    
    Changes to this object get sent out via pubsub,
    typically causing the model to make the change.
    """
    def __init__(self, tid, parent, amount, description, date):
        #import time; t = time.time()
        #LightweightPropertyObject.__init__(self)
        #print time.time() - t; t = time.time()
        #self.Freeze() # Disable dispatching while we initialize.
        self.IsFrozen = True
        #print time.time() - t; t = time.time()
        self.ID = tid
        #print time.time() - t; t = time.time()
        self.Parent = parent
        #print time.time() - t; t = time.time()
        self.Date = date
        #print time.time() - t; t = time.time()
        self.Description = description
        #print time.time() - t; t = time.time()
        self.Amount = amount
        #print time.time() - t; t = time.time()
        
        #self.Thaw() # Allow future parameter changes to dispatch.
        self.IsFrozen = False
        #print time.time() - t; t = time.time()
        
    def GetDate(self):
        return self._Date
        
    def SetDate(self, date):
        self._Date = wellFormDate(date)
            
        if not self.IsFrozen:
            FrozenPublisher.sendMessage("transaction.updated.date", self)
            
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


class TransactionList(LightweightPropertyObject):
    def __init__(self):
        LightweightPropertyObject.__init__(self)
        self._Transactions = {}

    def Add(self, transaction):
        self._Transactions[transaction.ID] = transaction

    def Get(self, tID):
        return self._Transactions[tID]

    def Remove(self, tID):
        del self._Transactions[tID]


class Account(LightweightPropertyObject):
    def __init__(self, name):
        LightweightPropertyObject.__init__(self)
        self.Name = name
        self.Transactions = {}

    def SetName(self, name):
        oldName = self.Name
        object.__setattr__(self, 'Name', name)
        Publisher.sendMessage("ACCOUNT.NAME_CHANGED.%s"%oldName, name)

    def AddTransaction(*args, **kwargs):
        self.Transactions.append(Transaction(*args, **kwargs))

    #def RemoveTransaction(
        
        
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)