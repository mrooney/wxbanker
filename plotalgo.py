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

import datetime

def get(transactions, numPoints):
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
