from wx.lib.pubsub import Publisher
import datetime
import bankexceptions, currencies


class BankModel(object):
    def __init__(self, store, accountList):
        self.Store = store
        self.Accounts = accountList
        
        Publisher().subscribe(self.onCurrencyChanged, "user.currency_changed")
        
    def GetAccount(self, accountName):
        return self.Accounts.Get(accountName)
        
    def CreateAccount(self, accountName):
        return self.Accounts.Create(accountName)
    
    def RemoveAccount(self, accountName):
        return self.Accounts.Remove(accountName)
        
    def float2str(self, *args, **kwargs):
        """
        Handle representing floats as strings for non
        account-specific amounts, such as totals.
        """
        if len(self.Accounts) == 0:
            currency = currencies.CurrencyList[0]()
        else:
            currency = self.Accounts[0].Currency
            
        return currency.float2str(*args, **kwargs)
        
    def setCurrency(self, currencyIndex):
        self.Store.setCurrency(currencyIndex)
        #self.Currency = currencies.CurrencyList[currencyIndex]()
        Publisher().sendMessage("currency_changed", currencyIndex)
        
    def onCurrencyChanged(self, message):
        currencyIndex = message.data
        self.setCurrency(currencyIndex)


class AccountList(list):
    def __init__(self, store, accounts):
        list.__init__(self, accounts)
        # Make sure all the items know their parent list.
        for account in self:
            account.Parent = self
            
        self.Store = store
        
    def AccountIndex(self, accountName):
        for i, account in enumerate(self):
            if account.Name == accountName:
                return i
            
        return -1
    
    def Get(self, accountName):
        index = self.AccountIndex(accountName)
        if index == -1:
            raise bankexceptions.InvalidAccountException(accountName)
        
        return self[index]
        
    def Create(self, accountName):
        # First, ensure an account by that name doesn't already exist.
        if self.AccountIndex(accountName) >= 0:
            raise bankexceptions.AccountAlreadyExistsException(accountName)
        
        account = self.Store.CreateAccount(accountName)
        # Make sure this account knows its parent.
        account.Parent = self
        self.append(account)
        
    def Remove(self, accountName):
        index = self.AccountIndex(accountName)
        if index == -1:
            raise bankexceptions.InvalidAccountException(accountName)
        
        self.Store.RemoveAccount(accountName)
        account = self.pop(index)
        Publisher.sendMessage("account.removed.%s"%accountName, account)


class Account(object):
    def __init__(self, store, aID, name, currency=0, balance=0.0):
        self.Store = store
        self.ID = aID
        self._Name = name
        self._Transactions = None
        self.Currency = currencies.CurrencyList[currency]()
        self.Balance = balance
        
        Publisher.sendMessage("account.created.%s"%name, self)
        
    def GetTransactions(self):
        if self._Transactions is None:
            self._Transactions = self.Store.getTransactionsFrom(self.Name)
        
        return self._Transactions
        
    def GetName(self):
        return self._Name

    def SetName(self, name):
        index = self.Parent.AccountIndex(name)
        if index != -1:
            raise bankexceptions.AccountAlreadyExistsException(name)
    
        oldName = self._Name
        self._Name = name
        Publisher.sendMessage("account.renamed.%s"%oldName, (oldName, self))
        
    def Remove(self):
        self.Parent.Remove(self.Name)

    def AddTransaction(self, amount, description, date, source=None):
        partialTrans = Transaction(None, self, amount, description, date)
        self.Store.MakeTransaction(self, partialTrans)
        transaction = partialTrans
        self._Transactions.append(transaction)
        
        # Update the balance
        self.Balance += transaction.Amount
        # FIXME: send pubsub transaction.created somewhere

    def RemoveTransaction(self, transaction):
        self.Store.RemoveTransaction(transaction)
        Publisher.sendMessage("transaction.removed.%s"%self.Name, transaction)
        self.Transactions.remove(transaction)
        
    def float2str(self, *args, **kwargs):
        return self.Currency.float2str(*args, **kwargs)
        
    def __cmp__(self, other):
        return cmp(self.Name, other.Name)
    
    Name = property(GetName, SetName)
    Transactions = property(GetTransactions)
        

class Transaction(object):
    """
    An object which represents a transaction.
    
    Changes to this object get sent out via pubsub,
    typically causing the model to make the change.
    """
    def __init__(self, tID, parent, amount, description, date):
        self.IsFrozen = True
        
        self.ID = tID
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
               
        
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)