from wx.lib.pubsub import Publisher
import datetime

        
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
    >>> float2str(-12345.67)
    '$-12,345.67'
    >>> float2str(-12345.6)
    '$-12,345.60'
    >>> float2str(-123456)
    '$-123,456.00'
    >>> float2str(.01)
    '$0.01'
    >>> float2str(.01, 8)
    '   $0.01'
    >>> float2str(2.1-2.2+.1) #test to ensure no negative zeroes
    '$0.00'
    """
    numStr = '%.2f' % number
    if numStr == '-0.00': # don't display negative zeroes (LP: 250151)
        numStr = '0.00'
    if len(numStr) > 6 + numStr.find('-') + 1: # remember, $ is not added yet
        numStr = numStr[:len(numStr)-6] + ',' + numStr[len(numStr)-6:]
    return ('$'+numStr).rjust(just)


def str2float(mstr):
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
    >>> str2float('$-12,345.67') == -12345.67
    True
    >>> str2float('$-12,345.6') == -12345.6
    True
    >>> str2float('$-123,456') == -123456
    True
    >>> str2float('$0.01') == 0.01
    True
    >>> str2float('   $0.01') == 0.01
    True
    """
    return float(mstr.strip()[1:].replace(',', ''))


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


class Transaction(LightweightPropertyObject):
    """
    An object which represents a transaction.
    
    Changes to this object get sent out via pubsub,
    typically causing the model to make the change.
    """
    def __init__(self, tid, parent, amount, description, date):
        LightweightPropertyObject.__init__(self)
        self.Freeze() # Disable dispatching while we initialize.
        
        self.tID = tid
        self.Parent = parent # Necessary?
        self.Date = date
        self.Description = description
        self.Amount = amount
        
        self.Thaw() # Allow future parameter changes to dispatch.

    def SetDate(self, date):
        date = wellFormDate(date)
        if not hasattr(self, 'Date') or date != self.Date:
            object.__setattr__(self, 'Date', date)
            
            if not self.freezeCount:
                FrozenPublisher.sendMessage("transaction.updated.date", self)

    def SetDescription(self, description):
        """Update the description, ensuring it is a string."""
        description = str(description)
        if not hasattr(self, 'Description') or description != self.Description:
            object.__setattr__(self, 'Description', description)
            
            if not self.freezeCount:
                Publisher.sendMessage("transaction.updated.description", self)

    def SetAmount(self, amount):
        """Update the amount, ensuring it is a float."""
        amount = float(amount)
        if not hasattr(self, 'Amount') or amount != self.Amount:
            object.__setattr__(self, 'Amount', amount)
            
            if not self.freezeCount:
                Publisher.sendMessage("transaction.updated.amount", self)


class TransactionList(LightweightPropertyObject):
    def __init__(self):
        LightweightPropertyObject.__init__(self)
        self._Transactions = {}

    def Add(self, transaction):
        self._Transactions[transaction.tID] = transaction

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

    #Name = property(GetName, SetName, doc="The name of this account")

    
class BaseModel(object):
    def __init__(self):
        object.__init__(self)
        
        
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)