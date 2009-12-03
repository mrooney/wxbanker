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

import localization
import datetime, functools, gettext
from dateutil import rrule

import helpers
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
    
    def __init__(self, tID, parent, amount, description, date, repeatType, repeatEvery=1, repeatOn=None, endDate=None, source=None, lastTransacted=None):
        Transaction.__init__(self, tID, parent, amount, description, date)
        ORMObject.__init__(self)
        
        # If the transaction recurs weekly and repeatsOn isn't specified, use the starting date.
        if repeatType == self.WEEKLY and repeatOn is None:
            todaydaynumber = date.weekday()
            repeatOn = [int(i==todaydaynumber) for i in range(7)]
        
        self.IsFrozen = True
        self.RepeatType = repeatType
        self.RepeatEvery = repeatEvery
        self.RepeatOn = repeatOn
        self.EndDate = endDate
        self.Source = source
        self.LastTransacted = lastTransacted
        self.IsFrozen = False
        
    def IsWeekly(self):
        return self.RepeatType == self.WEEKLY
        
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
    
    def GetRecurrance(self):
        """Generate a string for describing the recurrance, such as "Daily until 2009-10-02"."""
        summary = ""
        repeatType = self.RepeatType
        
        if repeatType == 0:
            summary = gettext.ngettext("Daily", "Every %(num)d days", self.RepeatEvery) % {'num':self.RepeatEvery} 
        elif repeatType == 1:
            if self.RepeatOn == [1,1,1,1,1,0,0]:
                summary = _("Weekly on weekdays")
            elif self.RepeatOn == [0,0,0,0,0,1,1]:
                summary = _("Weekly on weekends")
            elif self.RepeatOn == [1,1,1,1,1,1,1]:
                summary = _("Daily")
            else:
                pluralDayNames = (_("Mondays"), _("Tuesdays"), _("Wednesdays"), _("Thursdays"), _("Fridays"), _("Saturdays"), _("Sundays"))
                repeatDays = tuple(day for i, day in enumerate(pluralDayNames) if self.RepeatOn[i])
                # Figure out the base for this string.
                if self.RepeatEvery == 1:
                    summaryBase = _("Weekly on %s")
                else:
                    summaryBase = _("Every %(num)d weeks on %%s") % {'num':self.RepeatEvery}
                    
                if len(repeatDays) == 0:
                    summary = "Never"
                elif len(repeatDays) == 1:
                    summary = summaryBase % repeatDays[0]
                else:
                    summary = summaryBase % ((", ".join(repeatDays[:-1])) + (_(" and %s") % repeatDays[-1]))
        elif repeatType == 2:
            summary = gettext.ngettext("Monthly", "Every %(num)d months", self.RepeatEvery) % {'num':self.RepeatEvery} 
        elif repeatType == 3:
            summary = gettext.ngettext("Annually", "Every %(num)d years", self.RepeatEvery) % {'num':self.RepeatEvery} 

        # If the recurring ends at some point, add that information to the summary text.
        if self.EndDate:
            summary += " " + _("until %s") % helpers.pydate2wxdate(self.EndDate).FormatISODate()
            
        return summary
    
    def Update(self, rtype, revery, ron, rend):
        """Update our values."""
        self.RepeatType = rtype
        self.RepeatEvery = revery
        self.RepeatOn = ron
        self.EndDate = rend
        
    def UpdateFrom(self, rt):
        """Given a recurring transaction, mirror it in this one."""
        for attr in self.ORM_ATTRIBUTES[:-1]:
            setattr(self, attr, getattr(rt, attr))
        
    def GetStringBase(self):
        return "%s, %s: "  % (self.Description or _("No description"), self.RenderAmount())
    
    def GetDueString(self):
        datelist = ", ".join([str(d) for d in self.GetUntransactedDates()])
        return self.GetStringBase() + datelist
    
    def GetDescriptionString(self):
        return self.GetStringBase() + self.GetRecurrance()
        
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
    