#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    transaction.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
import datetime

from wxbanker.bankobjects.ormobject import ORMObject
from wxbanker import debug

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