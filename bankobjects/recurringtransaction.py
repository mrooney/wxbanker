#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    recurringtransaction.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

import datetime, functools
from dateutil import rrule
from bankobjects.transaction import Transaction
from bankobjects.ormobject import ORMObject

class InvalidDateRangeException(Exception): pass
class RecurringWeeklyException(Exception): pass

class RecurringTransaction(Transaction, ORMObject):
    ORM_TABLE = "recurring_transactions"
    ORM_ATTRIBUTES = ["Amount", "Description", "Date", "RepeatType", "RepeatEvery", "RepeatOn", "EndDate", "Source", "LastTransacted"]
    DAILY = 0
    WEEKLY = 1
    MONTLY = 2
    YEARLY = 3
    
    def __init__(self, tID, parent, amount, description, date, repeatType, repeatEvery, repeatOn, endDate, source=None, lastTransacted=None):
        Transaction.__init__(self, tID, parent, amount, description, date)
        ORMObject.__init__(self)
        
        # If the transaction recurs weekly and repeatsOn isn't specified, assume just today.
        if repeatType == self.WEEKLY and repeatOn is None:
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
        if self.RepeatType == self.WEEKLY:
            result = func(byweekday=[rruleDays[i] for i, x in enumerate(self.RepeatOn) if x])
        elif self.RepeatType == self.MONTLY:
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
    