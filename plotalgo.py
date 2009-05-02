#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    plotalgo.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

import datetime, bankobjects

def makeTransaction(date, amount):
    """A tiny wrapper to make tests below shorter."""
    return bankobjects.Transaction(None, None, amount, "", date)
    
def get(transactions, numPoints):
    """
    # First, rename the function for convenience
    >>> T = makeTransaction
    >>> today = datetime.date.today()
    >>> one = datetime.timedelta(1)
    >>> result = get([], 10)
    >>> result[0]
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    >>> result[1] == datetime.date.today()
    True
    >>> result[2] < 0.001
    True
    >>> get([T("2008/1/6", 1)], 3)[0]
    [1.0, 1.0, 1.0]
    >>> get([T(today-one, 1), T(today, 2)], 4)[0]
    [1.0, 1.0, 1.0, 3.0]
    >>> result = get([T(today-one, 1), T(today, 2)], 1)
    >>> result[0]
    [3.0]
    >>> result[1] == today - one
    True
    >>> result[2]
    1.0
    >>> get([T(today, 1), T(today+one, 2)], 2)[0]
    [1.0, 3.0]
    >>> get([T(today, 1), T(today+one, 2)], 3)[0]
    [1.0, 1.0, 3.0]
    >>> get([T(today-one*9, 1), T(today, 2)], 10)[0]
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 3.0]
    >>> get([T(today, 1), T(today+one*2, 2), T(today+one*9, 3)], 10)[0]
    [1.0, 1.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 6.0]
    >>> result = get([T(today, 1)], 2)
    >>> result[0]
    [1.0, 1.0]
    >>> result[1] == today
    True
    >>> result[2] != 0
    True
    """
    # Don't ever return 0 as the dpp, you can't graph without SOME x delta.
    smallDelta = 1.0/2**32
    
    if transactions == []:
        return [0] * 10, datetime.date.today(), smallDelta
    
    transactions = list(sorted(transactions))
    
    startDate, endDate = transactions[0].Date, transactions[-1].Date
    today = datetime.date.today()
    if today > endDate:
        endDate = today

    distance = (endDate - startDate).days
    daysPerPoint = 1.0 * distance / numPoints
    dppDelta = datetime.timedelta(daysPerPoint)
    
    points = [0.0]
    tindex = 0
    for i in range(numPoints):
        while tindex < len(transactions) and transactions[tindex].Date <= startDate + (dppDelta * (i+1)):
            points[i] += transactions[tindex].Amount
            tindex += 1
        
        points.append(points[-1])
        
    return points[:-1], startDate, daysPerPoint or smallDelta
    
    
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=1)
    