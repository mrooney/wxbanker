#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    bankobjects.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

from wx.lib.pubsub import Publisher
import datetime, re
from dateutil import rrule
import functools
import bankexceptions, currencies, localization, debug

RECURRING_DAILY = 0
RECURRING_WEEKLY = 1
RECURRING_MONTLY = 2
RECURRING_YEARLY = 3

class InvalidDateRangeException(Exception): pass
class RecurringWeeklyException(Exception): pass

class ORMObject(object):
    ORM_TABLE = None
    ORM_ATTRIBUTES = []
    
    def __init__(self):
        self.IsFrozen = True
        # If the object doesn't have an ID, we need to set one for setattr.
        if not hasattr(self, "ID"):
            self.ID = None
        self.IsFrozen = False
        
    def __setattr__(self, attrname, val):
        object.__setattr__(self, attrname, val)
        if not self.IsFrozen and self.ID is not None:
            if attrname in self.ORM_ATTRIBUTES:
                classname = self.__class__.__name__
                Publisher.sendMessage("ormobject.updated.%s.%s" % (classname, attrname), self)
            
    def getAttrValue(self, attrname):
        value = getattr(self, attrname)
        if isinstance(value, (Account, Transaction)):
            value = value.ID
        elif attrname == "RepeatOn" and value is not None:
            value = ",".join([str(x) for x in value])
        elif attrname == "Date":
            value = "%s/%s/%s"%(self.Date.year, str(self.Date.month).zfill(2), str(self.Date.day).zfill(2))
        return value
            
    def toResult(self):
        result = [self.ID]
        for attr in self.ORM_ATTRIBUTES:
            result.append(self.getAttrValue(attr))
        return result

class BankModel(object):
    def __init__(self, store, accountList):
        self.Store = store
        self.Accounts = accountList

        Publisher().subscribe(self.onCurrencyChanged, "user.currency_changed")

    def GetBalance(self):
        return self.Accounts.Balance
    
    def GetRecurringTransactions(self):
        return self.Accounts.GetRecurringTransactions()

    def GetTransactions(self):
        transactions = []
        for account in self.Accounts:
            transactions.extend(account.Transactions)

        return transactions
    
    def GetDateRange(self):
        """Get the date of the first and last transaction."""
        transactions = self.GetTransactions()
        
        # If there are no transactions, let's go with today.
        if not transactions:
            return datetime.date.today(), datetime.date.today()
        else:
            # Sorting transactions is very important, otherwise the first and last dates are arbitrary!
            transactions.sort()
            return transactions[0].Date, transactions[-1].Date

    def GetXTotals(self, numPoints, account=None, daterange=None):
        """
        Get totals every so many days, optionally within a specific account
        and/or date range. This is particularly useful when we want to
        graph a summary of account balances.
        """
        if account is None:
            transactions = self.GetTransactions()
        else:
            transactions = account.Transactions[:]
        transactions.sort()

        # Don't ever return 0 as the dpp, you can't graph without SOME x delta.
        smallDelta = 1.0/2**32

        # If there aren't any transactions, return 0 for every point and start at today.
        if transactions == []:
            return [0] * 10, datetime.date.today(), smallDelta
        
        startingBalance = 0.0
        # Crop transactions around the date range, if supplied.
        if daterange:
            startDate, endDate = daterange
            starti, endi = None, len(transactions)
            total = 0.0
            for i, t in enumerate(transactions):
                if starti is None and t.Date >= startDate:
                    starti = i
                    startingBalance = total
                if t.Date > endDate:
                    endi = i
                    break
                total += t.Amount
                
            transactions = transactions[starti:endi]
        else:
            # Figure out the actual start and end dates we end up with.
            startDate, endDate = transactions[0].Date, transactions[-1].Date
        
        # If the last transaction was before today, we still want to graph until today.
        today = datetime.date.today()
        if daterange:
            endDate = daterange[1]
        elif today > endDate:
            endDate = today

        # Figure out the fraction of a day that exists between each point.
        distance = (endDate - startDate).days
        daysPerPoint = 1.0 * distance / numPoints
        dppDelta = datetime.timedelta(daysPerPoint)
        
        # Generate all the points.
        points = [startingBalance]
        tindex = 0
        for i in range(numPoints):
            while tindex < len(transactions) and transactions[tindex].Date <= startDate + (dppDelta * (i+1)):
                points[i] += transactions[tindex].Amount
                tindex += 1

            points.append(points[-1])

        return points[:-1], startDate, daysPerPoint or smallDelta

    def CreateAccount(self, accountName):
        return self.Accounts.Create(accountName)

    def RemoveAccount(self, accountName):
        return self.Accounts.Remove(accountName)

    def Search(self, searchString, account=None, matchIndex=1, matchCase=False):
        """
        matchIndex: 0: Amount, 1: Description, 2: Date
        I originally used strings here but passing around and then validating on translated
        strings seems like a bad and fragile idea.
        """
        # Handle case-sensitive option.
        reFlag = {False: re.IGNORECASE, True: 0}[matchCase]

        # Handle account options.
        if account is None:
            potentials = self.GetTransactions()
        else:
            potentials = account.Transactions[:]

        # Find all the matches.
        matches = []
        for trans in potentials:
            potentialStr = unicode((trans.Amount, trans.Description, trans.Date)[matchIndex])
            if re.findall(searchString, potentialStr, flags=reFlag):
                matches.append(trans)
        return matches

    def Save(self):
        self.Store.Save()

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
        for account in self.Accounts:
            account.Currency = currencyIndex
        Publisher().sendMessage("currency_changed", currencyIndex)

    def onCurrencyChanged(self, message):
        currencyIndex = message.data
        self.setCurrency(currencyIndex)

    def __eq__(self, other):
        return self.Accounts == other.Accounts

    def Print(self):
        print "Model: %s" % self.Balance
        for a in self.Accounts:
            print "  %s: %s" % (a.Name, a.Balance)
            for t in a.Transactions:
                print t

    Balance = property(GetBalance)


class AccountList(list):
    def __init__(self, store, accounts):
        list.__init__(self, accounts)
        # Make sure all the items know their parent list.
        for account in self:
            account.Parent = self

        self.Store = store
        
    def GetRecurringTransactions(self):
        allRecurrings = []
        for account in self:
            recurrings = account.GetRecurringTransactions()
            if recurrings:
                allRecurrings.extend(recurrings)
                
        return allRecurrings

    def GetBalance(self):
        return sum([account.Balance for account in self])

    def AccountIndex(self, accountName):
        for i, account in enumerate(self):
            if account.Name == accountName:
                return i
        return -1

    def ThrowExceptionOnInvalidName(self, accountName):
        # First make sure we were given a name!
        if not accountName:
            raise bankexceptions.BlankAccountNameException
        # Now ensure an account by that name doesn't already exist.
        if self.AccountIndex(accountName) >= 0:
            raise bankexceptions.AccountAlreadyExistsException(accountName)

    def Create(self, accountName):
        self.ThrowExceptionOnInvalidName(accountName)

        currency = 0
        if len(self):
            # If the list contains items, the currency needs to be consistent.
            currency = self[-1].Currency

        account = self.Store.CreateAccount(accountName, currency)
        # Make sure this account knows its parent.
        account.Parent = self
        self.append(account)
        Publisher.sendMessage("account.created.%s" % accountName, account)
        return account

    def Remove(self, accountName):
        index = self.AccountIndex(accountName)
        if index == -1:
            raise bankexceptions.InvalidAccountException(accountName)

        account = self.pop(index)
        self.Store.RemoveAccount(account)
        Publisher.sendMessage("account.removed.%s"%accountName, account)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        for leftAccount, rightAccount in zip(self, other):
            if not leftAccount == rightAccount:
                return False

        return True

    Balance = property(GetBalance)


class Account(ORMObject):
    ORM_TABLE = "accounts"
    ORM_ATTRIBUTES = ["Name", "Balance"]
    
    def __init__(self, store, aID, name, currency=0, balance=0.0):
        ORMObject.__init__(self)
        self.IsFrozen = True
        self.Store = store
        self.ID = aID
        self._Name = name
        self._Transactions = None
        self._RecurringTransactions = []
        self._preTransactions = []
        self.Currency = currency
        self.Balance = balance
        self.IsFrozen = False

        Publisher.subscribe(self.onTransactionAmountChanged, "transaction.updated.amount")

    def ParseAmount(self, strAmount):
        """
        Robustly parse an amount. Remove ANY spaces, so they can be used as padding
        or thousands separators. Find the thing intended as a decimal, if any,
        and replace it with a period, removing anything else that may be a thousands sep.
        """
        # Remove any spaces anywhere.
        strAmount = strAmount.replace(" ", "")

        # Iterate over the string in reverse to locate decimal sep.
        decimalPos = None
        for i in range(min(3, len(strAmount))):
            pos = -(i+1)
            char = strAmount[pos]
            if char in ",." and i <= 2:
                decimalPos = pos + 1
                break
        strAmount = strAmount.replace(",", "")
        strAmount = strAmount.replace(".", "")

        if decimalPos:
            strAmount = strAmount[:decimalPos] + "." + strAmount[decimalPos:]

        return float(strAmount)

    def GetSiblings(self):
        return (account for account in self.Parent if account is not self)

    def SetCurrency(self, currency):
        if type(currency) == int:
            self._Currency = currencies.CurrencyList[currency]()
        else:
            self._Currency = currency

    def GetCurrency(self):
        return self._Currency
        
    def GetRecurringTransactions(self):
        return self._RecurringTransactions
        
    def SetRecurringTransactions(self, recurrings):
        self._RecurringTransactions = recurrings

    def GetTransactions(self):
        if self._Transactions is None:
            self._Transactions = self.Store.getTransactionsFrom(self)

            # If transactions were added before this list was pulled, and then an attribute
            # is changed on one of them (Amount/Description/Date), it won't be
            # reflected on the new account at run-time because it has a replacement instance
            # for that transaction. So we need to swap it in.
            if self._preTransactions:
                # Iterate over this first (and thus once) since it is probably larger than _pre.
                for i, newT in enumerate(self._Transactions):
                    for oldT in self._preTransactions:
                        # Compare just IDs otherwise TDD is impossible; new attributes not yet stored
                        # will cause the objects to not be properly replaced and break tests.
                        if oldT.ID == newT.ID:
                            self._Transactions[i] = oldT
                            break

        return self._Transactions

    def GetName(self):
        return self._Name

    def SetName(self, name):
        self.Parent.ThrowExceptionOnInvalidName(name)
        self._Name = name

    def Remove(self):
        self.Parent.Remove(self.Name)

    def AddTransactions(self, transactions, sources=None):
        Publisher.sendMessage("batch.start")
        # If we don't have any sources, we want None for each transaction.
        if sources is None:
            sources = [None for i in range(len(transactions))]
            
        for t, source in zip(transactions, sources):
            self.AddTransaction(transaction=t, source=source)
        Publisher.sendMessage("batch.end")
        
    def AddRecurringTransaction(self, amount, description, date, repeatType, repeatEvery=1, repeatOn=None, endDate=None, source=None):
        # Create the recurring transaction object.
        recurring = RecurringTransaction(None, self, amount, description, date, repeatType, repeatEvery, repeatOn, endDate, source)
        # Store it.
        self.Store.MakeRecurringTransaction(recurring)
        # Add it to our internal list.
        self.RecurringTransactions.append(recurring)
        
        Publisher.sendMessage("recurringtransaction.created", (self, recurring))
        
        return recurring

    def AddTransaction(self, amount=None, description="", date=None, source=None, transaction=None):
        """
        Enter a transaction in this account, optionally making the opposite
        transaction in the source account first.
        """
        Publisher.sendMessage("batch.start")
        
        if transaction:
            # It is "partial" because its ID and parent aren't necessarily correct.
            partialTrans = transaction
            partialTrans.Parent = self
        elif amount is not None:
            # No transaction object was given, we need to make one.
            partialTrans = Transaction(None, self, amount, description, date)
        else:
            raise Exception("AddTransaction: Must provide either transaction arguments or a transaction object.")
        
        if source:
            otherTrans = source.AddTransaction(-1 * partialTrans.Amount, partialTrans._Description, partialTrans.Date)
            
        transaction = self.Store.MakeTransaction(self, partialTrans)

        # If it was a transfer, link them together
        if source:
            transaction.LinkedTransaction = otherTrans
            otherTrans.LinkedTransaction = transaction

        # Don't append if there aren't transactions loaded yet, it is already in the model and will appear on a load. (LP: 347385).
        if self._Transactions is not None:
            self.Transactions.append(transaction)
        else:
            # We will need to do some magic with these later when transactions are loaded.
            self._preTransactions.append(transaction)

        Publisher.sendMessage("transaction.created", (self, transaction))

        # Update the balance.
        self.Balance += transaction.Amount
        Publisher.sendMessage("batch.end")

        if source:
            return transaction, otherTrans
        else:
            return transaction

    def RemoveTransaction(self, transaction):
        return self.RemoveTransactions([transaction])

    def RemoveTransactions(self, transactions):
        Publisher.sendMessage("batch.start")
        # Return the sources, if any, of the removed transactions, in case we are moving for example.
        sources = []
        
        # Accumulate the difference and update the balance just once. Cuts 33% time of removals.
        difference = 0
        # Send the message for all transactions at once, cuts _97%_ of time! OLV is slow here I guess.
        Publisher.sendMessage("transactions.removed", (self, transactions))
        for transaction in transactions:
            if transaction not in self.Transactions:
                raise bankexceptions.InvalidTransactionException("Transaction does not exist in account '%s'" % self.Name)

            # If this transaction was a transfer, delete the other transaction as well.
            if transaction.LinkedTransaction:
                link = transaction.LinkedTransaction
                sources.append(link.Parent)
                # Kill the other transaction's link to this one, otherwise this is quite recursive.
                link.LinkedTransaction = None
                link.Remove()
            else:
                sources.append(None)

            # Now remove this transaction.
            self.Store.RemoveTransaction(transaction)
            transaction.Parent = None
            self.Transactions.remove(transaction)
            difference += transaction.Amount

        # Update the balance.
        self.Balance -= difference
        Publisher.sendMessage("batch.end")
        return sources

    def MoveTransaction(self, transaction, destAccount):
        self.MoveTransactions([transaction], destAccount)

    def MoveTransactions(self, transactions, destAccount):
        Publisher.sendMessage("batch.start")
        sources = self.RemoveTransactions(transactions)
        destAccount.AddTransactions(transactions, sources)
        Publisher.sendMessage("batch.end")

    def onTransactionAmountChanged(self, message):
        transaction, difference = message.data
        if transaction.Parent == self:
            debug.debug("Updating balance by %s because I am %s: %s" % (difference, self.Name, transaction))
            self.Balance += difference
        else:
            debug.debug("Ignoring transaction because I am %s: %s" % (self.Name, transaction))

    def float2str(self, *args, **kwargs):
        return self.Currency.float2str(*args, **kwargs)

    def __cmp__(self, other):
        return cmp(self.Name, other.Name)

    def __eq__(self, other):
        if other is None:
            return False
        
        return (
            self.Name == other.Name and
            self.Balance == other.Balance and
            self.Currency == other.Currency and
            self.Transactions == other.Transactions and
            self.RecurringTransactions == other.RecurringTransactions
        )

    Name = property(GetName, SetName)
    Transactions = property(GetTransactions)
    RecurringTransactions = property(GetRecurringTransactions)
    Currency = property(GetCurrency, SetCurrency)


class TransactionList(list):
    def __init__(self, items=None):
        # list does not understand items=None apparently.
        if items is None:
            items = []

        list.__init__(self, items)

    def __eq__(self, other):
        if not len(self) == len(other):
            return False
        for leftTrans, rightTrans in zip(self, other):
            if not leftTrans == rightTrans:
                return False

        return True


class Transaction(ORMObject):
    """
    An object which represents a transaction.

    Changes to this object get sent out via pubsub,
    typically causing the model to make the change.
    """
    ORM_TABLE = "transactions"
    ORM_ATTRIBUTES = ["Amount", "_Description", "Date", "LinkedTransaction", "RecurringParent"]
    
    def __init__(self, tID, parent, amount, description, date):
        ORMObject.__init__(self)
        self.IsFrozen = True

        self.ID = tID
        self.Parent = parent
        self.Date = date
        self.Description = description
        self.Amount = amount
        self.LinkedTransaction = None
        self.RecurringParent = None

        self.IsFrozen = False

    def GetDate(self):
        return self._Date

    def SetDate(self, date):
        self._Date = self._MassageDate(date)

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
        >>> _MassageData(None) == datetime.date.today()
        True
        """
        if date is None:
            return datetime.date.today()
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
        description = self._Description
        if self.LinkedTransaction:
            parentName = self.LinkedTransaction.Parent.Name
            if self.Amount > 0:
                transferString = _("Transfer from %s") % parentName
            else:
                transferString = _("Transfer to %s") % parentName
                
            if description:
                description = transferString + " (%s)"%description
            else:
                description = transferString
            
        return description

    def SetDescription(self, description):
        """Update the description, ensuring it is a string."""
        self._Description = unicode(description)

    def GetAmount(self):
        return self._Amount

    def SetAmount(self, amount):
        """Update the amount, ensuring it is a float."""
        if hasattr(self, "_Amount"):
            difference = amount - self._Amount

        self._Amount = float(amount)

        if not self.IsFrozen:
            debug.debug("Setting transaction amount: ", self)
            Publisher.sendMessage("transaction.updated.amount", (self, difference))

    def GetLinkedTransaction(self):
        return self._LinkedTransaction

    def SetLinkedTransaction(self, transaction):
        self._LinkedTransaction = transaction

        if not self.IsFrozen:
            Publisher.sendMessage("transaction.updated.link", (self, None))

    def GetLinkedTransactionID(self):
        """
        This exists to make it easy to compare linked transactions in __eq__, where it needs to be done based on ID
        so we don't recurse forever in comparisons.
        """
        if self.LinkedTransaction:
            return self.LinkedTransaction.ID
        else:
            return None

    def Remove(self):
        return self.Parent.RemoveTransaction(self)
    
    def RenderAmount(self):
        return self.Parent.float2str(self.Amount)

    def __str__(self):
        return "%i/%i/%i: %s -- %.2f" % (self.Date.year, self.Date.month, self.Date.day, self.Description, self.Amount)

    def __cmp__(self, other):
        return cmp(
            (self.Date, self.ID),
            (other.Date, other.ID)
        )

    def __eq__(self, other):
        if other is None:
            return False

        assert isinstance(other, Transaction), other
        return (
            self.Date == other.Date and
            self.Description == other.Description and
            self.Amount == other.Amount and
            self.GetLinkedTransactionID() == other.GetLinkedTransactionID() and
            self.ID == other.ID
        )

    Date = property(GetDate, SetDate)
    Description = property(GetDescription, SetDescription)
    Amount = property(GetAmount, SetAmount)
    LinkedTransaction = property(GetLinkedTransaction, SetLinkedTransaction)

class RecurringTransaction(Transaction, ORMObject):
    ORM_TABLE = "recurring_transactions"
    ORM_ATTRIBUTES = ["Amount", "Description", "Date", "RepeatType", "RepeatEvery", "RepeatOn", "EndDate", "Source", "LastTransacted"]
    
    def __init__(self, tID, parent, amount, description, date, repeatType, repeatEvery, repeatOn, endDate, source=None, lastTransacted=None):
        Transaction.__init__(self, tID, parent, amount, description, date)
        ORMObject.__init__(self)
        
        # If the transaction recurs weekly and repeatsOn isn't specified, assume just today.
        if repeatType == RECURRING_WEEKLY and repeatOn is None:
            todaydaynumber = datetime.date.today().weekday()
            repeatOn = [int(i==todaydaynumber) for i in range(7)]
        
        self.IsFrozen = True
        self.RepeatType = repeatType
        self.RepeatEvery = repeatEvery
        self.RepeatOn = repeatOn
        self.EndDate = endDate
        self.Source = source
        self.LastTransacted = lastTransacted
        self.IsFrozen = False
        
    def PerformTransactions(self):
        for date in self.GetUntransactedDates():
            result = self.Parent.AddTransaction(self.Amount, self.Description, date, self.Source)
            if isinstance(result, Transaction):
                result = (result,)
            for transaction in result:
                transaction.RecurringParent = self
        
        self.LastTransacted = datetime.date.today()
        
    def GetRRule(self):
        """Generate the dateutils.rrule for this recurring transaction."""
        # Create some mapping lists.
        rruleDays = [rrule.MO, rrule.TU, rrule.WE, rrule.TH, rrule.FR, rrule.SA, rrule.SU]
        rruleTypes = [rrule.DAILY, rrule.WEEKLY, rrule.MONTHLY, rrule.YEARLY]
        
        func = functools.partial(rrule.rrule, rruleTypes[self.RepeatType], dtstart=self.Date, interval=self.RepeatEvery, wkst=rrule.MO)
        if self.RepeatType == RECURRING_WEEKLY:
            result = func(byweekday=[rruleDays[i] for i, x in enumerate(self.RepeatOn) if x])
        elif self.RepeatType == RECURRING_MONTLY:
            # "a date on the specified day of the month, unless it is beyond the end of month, in which case it will be the last day of the month"
            result = func(bymonthday=(self.Date.day, -1), bysetpos=1)
        else:
            result = func()
            
        return result
    
    def DateToDatetime(self, date):
        """Convert a date to a datetime at the first microsecond of that day."""
        return datetime.datetime(date.year, date.month, date.day)
    
    def GetUntransactedDates(self):
        """Get all due transaction dates."""
        result = self.GetRRule()
        
        today = datetime.date.today()
        
        # Stop at the end date or today, whichever is earlier.
        if self.EndDate:
            end = min(self.EndDate, today)
        else:
            end = today
        
        if self.LastTransacted:
            # Start on the day after the last transaction
            start = self.LastTransacted + datetime.timedelta(days=1)
        else:
            start = self.Date
            
        # Convert dates to datetimes.
        start, end = [self.DateToDatetime(d) for d in (start, end)]
        # Calculate the result.
        result = result.between(start, end, inc=True)
        # Return just the dates, we don't care about datetime.
        return [dt.date() for dt in list(result)]
    
    def GetNext(self):
        """Get the next transaction date that will occur."""
        result = self.GetRRule()
        after = self.LastTransacted or (self.Date - datetime.timedelta(days=1))
        after = self.DateToDatetime(after)
        return result.after(after, inc=False).date()
    
    def SetLastTransacted(self, date):
        if date is None:
            self._LastTransacted = None
        else:
            self._LastTransacted = self._MassageDate(date)
        
    def GetLastTransacted(self):
        return self._LastTransacted
    
    def SetEndDate(self, date):
        if date is None:
            self._EndDate = None
        else:
            self._EndDate = self._MassageDate(date)
        
    def GetEndDate(self):
        return self._EndDate
        
    def __eq__(self, other):
        if other is None:
            return False

        assert isinstance(other, RecurringTransaction), other
        return (
            Transaction.__eq__(self, other) and
            self.RepeatType == other.RepeatType and
            self.RepeatEvery == other.RepeatEvery and
            self.RepeatOn == other.RepeatOn and
            self.EndDate == other.EndDate and
            self.Source == other.Source and
            self.LastTransacted == other.LastTransacted
            )
    
    LastTransacted = property(GetLastTransacted, SetLastTransacted)
    EndDate = property(GetEndDate, SetEndDate)
    
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
