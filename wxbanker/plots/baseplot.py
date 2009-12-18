#    https://launchpad.net/wxbanker
#    baseplot.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker.plots.plotfactory import BasePlotImportException

# Needs Numeric or numarray or NumPy
try:
    import numpy.oldnumeric as _Numeric
except:
    try:
        import numarray as _Numeric  #if numarray is used it is renamed Numeric
    except:
        try:
            import Numeric as _Numeric
        except:
            _Numeric = None
if not hasattr(_Numeric, 'polyfit'):
    raise BasePlotImportException()

class BasePlot(object):
    def getPoints(self, totals, numPoints):
       
        # Don't ever return 0 as the dpp, you can't graph without SOME x delta.
        smallDelta = 1.0/2**32
        
        # If there aren't any transactions, return 0 for every point and start at today.
        if totals == []:
            return [0] * 10, datetime.date.today(), smallDelta
        
        startDate = totals[0][0]
        endDate = totals[-1][0]

        # Figure out the fraction of a day that exists between each point.
        distance = (endDate - startDate).days
        daysPerPoint = 1.0 * distance / numPoints
        dppDelta = datetime.timedelta(daysPerPoint)
        
        # Generate all the points.
        tindex = 0
        points = [totals[0][1]]

        for i in range(numPoints):
            while tindex < len(totals) and totals[tindex][0] <= startDate + (dppDelta * (i+1)):
                points[i] = totals[tindex][1]
                tindex += 1
            points.append(points[-1])

        return points[:-1], startDate, daysPerPoint or smallDelta
    
    def plotBalance(self, totals, plotSettings, xunits):
        totals, startDate, every = self.getPoints(totals, plotSettings['Granularity'])
        
        self.startDate = startDate
        timeDelta = datetime.timedelta( every * {'Days':1, 'Weeks':7, 'Months':30, 'Years':365}[xunits] )

        dates = []
        strdates = []
        currentTime = 0
        uniquePoints = set()
        for i, total in enumerate(totals):
            dates.append(currentTime)
            uniquePoints.add("%.2f"%total)
            currentTime += every

            # Don't just += the timeDelta to currentDate, since adding days is all or nothing, ie:
            #   currentDate + timeDelta == currentDate, where timeDelta < 1 (bad!)
            # ...so the date will never advance for timeDeltas < 1, no matter how many adds you do.
            # As such we must start fresh each time and multiply the time delta appropriately.
            currentDate = startDate + (i+1)*timeDelta

            strdates.append(currentDate.strftime('%Y/%m/%d'))
            
        # Is this data trendable? In other words, at least two different points.
        trendable = bool(len(uniquePoints))
        
        return totals, dates, strdates, trendable
    
    def getPolyData(self, points, N=1):
        xs = tuple((p[0] for p in points))
        ys = tuple((p[1] for p in points))

        coefficients = _Numeric.polyfit(xs, ys, N)

        bestFitPoints = []
        for x in xs:
            newY = 0.0
            power = len(coefficients)-1
            for coefficient in coefficients:
                newY += coefficient*(x**power)
                power -= 1
            bestFitPoints.append((int(x), float(newY)))
        return bestFitPoints