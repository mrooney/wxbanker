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
import bankexceptions, currencies, localization, debug


class InvalidDateRangeException(Exception): pass


class BankModel(object):
    def __init__(self, store, accountList):
        self.Store = store
        self.Accounts = accountList

        Publisher().subscribe(self.onCurrencyChanged, "user.currency_changed")

    def GetBalance(self):
        return self.Accounts.Balance
    
    def GetRecurringTransactions(self):
        allRecurrings = []
        for account in self.Accounts:
            recurrings = account.GetRecurringTransactions()
            if recurrings:
                allRecurrings.extend(recurrings)
                
        return allRecurrings

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


class Account(object):
    def __init__(self, store, aID, name, currency=0, balance=0.0):
        self.Store = store
        self.ID = aID
        self._Name = name
        self._Transactions = None
        self._RecurringTransactions = []
        self._preTransactions = []
        self.Currency = currency
        self._Balance = balance

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

    def GetBalance(self):
        return self._Balance

    def SetBalance(self, newBalance):
        self._Balance = newBalance
        Publisher.sendMessage("account.balance changed.%s" % self.Name, self)
        
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
        oldName = self._Name
        self._Name = name
        Publisher.sendMessage("account.renamed.%s"%oldName, (oldName, self))

    def Remove(self):
        self.Parent.Remove(self.Name)

    def AddTransactions(self, transactions):
        Publisher.sendMessage("batch.start")
        for t in transactions:
            self.AddTransaction(transaction=t)
        Publisher.sendMessage("batch.end")
        
    def AddRecurringTransaction(self, amount, description, date, repeatType, repeatEvery, repeatOn, endDate, source=None):
        # Create the recurring transaction object.
        recurring = RecurringTransaction(None, self, amount, description, date, repeatType, repeatEvery, repeatOn, endDate, source)
        # Store it.
        self.Store.MakeRecurringTransaction(recurring)
        # Add it to our internal list.
        self.RecurringTransactions.append(recurring)
        
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
            if source:
                if description:
                    description = " (%s)" % description
                otherTrans = source.AddTransaction(-amount, _("Transfer to %s"%self.Name) + description, date)
                description = _("Transfer from %s"%source.Name) + description

            partialTrans = Transaction(None, self, amount, description, date)
        else:
            raise Exception("AddTransaction: Must provide either transaction arguments or a transaction object.")

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
        self.RemoveTransactions([transaction])

    def RemoveTransactions(self, transactions):
        Publisher.sendMessage("batch.start")
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
                # Kill the other transaction's link to this one, otherwise this is quite recursive.
                link.LinkedTransaction = None
                link.Remove()

            # Now remove this transaction.
            self.Store.RemoveTransaction(transaction)
            transaction.Parent = None
            self.Transactions.remove(transaction)
            difference += transaction.Amount

        # Update the balance.
        self.Balance -= difference
        Publisher.sendMessage("batch.end")

    def MoveTransaction(self, transaction, destAccount):
        self.MoveTransactions([transaction], destAccount)

    def MoveTransactions(self, transactions, destAccount):
        Publisher.sendMessage("batch.start")
        self.RemoveTransactions(transactions)
        destAccount.AddTransactions(transactions)
        Publisher.sendMessage("batch.end")

    def onTransactionAmountChanged(self, message):
        transaction, difference = message.data
        if self._Transactions is not None:
            if transaction in self.Transactions:
                #assert transaction.Parent is self, (self.Name, transaction.Parent, transaction.Description, transaction.Amount)
                debug.debug("Updating balance by %s because I am %s: %s" % (difference, self.Name, transaction))
                self.Balance += difference
            else:
                debug.debug("Ignoring transaction because I am %s: %s" % (self.Name, transaction))

    def float2str(self, *args, **kwargs):
        return self.Currency.float2str(*args, **kwargs)

    def __cmp__(self, other):
        return cmp(self.Name, other.Name)

    def __eq__(self, other):
        return (
            self.Name == other.Name and
            self.Balance == other.Balance and
            self.Currency == other.Currency and
            self.Transactions == other.Transactions
        )

    Name = property(GetName, SetName)
    Transactions = property(GetTransactions)
    RecurringTransactions = property(GetRecurringTransactions)
    Balance = property(GetBalance, SetBalance)
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
        self.LinkedTransaction = None

        self.IsFrozen = False

    def GetDate(self):
        return self._Date

    def SetDate(self, date):
        self._Date = self._MassageDate(date)

        if not self.IsFrozen:
            Publisher.sendMessage("transaction.updated.date", (self, None))

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
        return self._Description

    def SetDescription(self, description):
        """Update the description, ensuring it is a string."""
        self._Description = unicode(description)

        if not self.IsFrozen:
            Publisher.sendMessage("transaction.updated.description", (self, None))

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

class RecurringTransaction(Transaction):
    def __init__(self, tID, parent, amount, description, date, repeatType, repeatEvery, repeatOn, endDate, source=None):
        Transaction.__init__(self, tID, parent, amount, description, date)
        self.RepeatType = repeatType
        self.RepeatEvery = repeatEvery
        self.RepeatOn = repeatOn
        self.EndDate = endDate

if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
