#    https://launchpad.net/wxbanker
#    summarytab.py: Copyright 2007, 2008 Mike Rooney <wxbanker@rowk.com>
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

from bankexceptions import NoNumpyException
import wx
#import wx.lib.plot as pyplot
try:
    import plot as pyplot
except ImportError:
    raise NoNumpyException()

from banker import float2str
import datetime

# TODO: sliders for granularity (getPoints(100)), and trend degree (N=2)

class SummaryPanel(wx.Panel):
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent)
        self.frame = frame

        self.plotPanel = AccountPlotCanvas(self)

        sizer = wx.BoxSizer()
        sizer.Add(self.plotPanel, 1, wx.EXPAND)

        self.Sizer = sizer
        sizer.Layout()

    def generateData(self):
        totals, startDate, delta = self.getPoints(100)
        self.plotPanel.plotBalance(totals, startDate, delta, "Days")

    def getPoints(self, numPoints):
        """
        A function to turn the daily balances into numPoints number of values,
        spanning the balances if there are not enough and averaging balances
        together if there are too many.
        """
        days, startDate = self.frame.bank.getTotalsEvery(1)
        numDays = len(days)
        delta = float(numDays) / numPoints
        returnPoints = []

        if numDays == 0:
            return [0.0 for i in range(numPoints)], datetime.date.today(), 1
        elif numDays <= numPoints:
            span = numPoints / numDays
            mod = numPoints % numDays
            total = 0
            for val in days:
                total += val
                for i in range(span):
                    returnPoints.append(total)
            for i in range(mod):
                returnPoints.append(total)
        else: # we have too much data, we need to average
            groupSize = numDays / numPoints
            total = 0
            for i in range(numPoints):
                start = i*groupSize
                end = start + groupSize
                points = days[start:end]

                if i == (numPoints-1): # this is the last one, throw in the rest
                    points.extend(days[end:])
                    groupSize += numDays % numPoints # to make avg accurate!

                pointSum = sum(points)
                avgVal = pointSum / float(groupSize)
                returnPoints.append(total+avgVal)
                total += pointSum

        return returnPoints, startDate, delta

class AccountPlotCanvas(pyplot.PlotCanvas):
    def __init__(self, *args, **kwargs):
        pyplot.PlotCanvas.__init__(self, *args, **kwargs)
        self.pointDates = []
        self.SetEnablePointLabel(True)
        self.SetEnableLegend(True)
        self.SetPointLabelFunc(self.drawPointLabel)

        self.canvas.Bind(wx.EVT_MOTION, self.onMotion)

    def plotBalance(self, totals, startDate, every, xunits="Days"):
        timeDelta = datetime.timedelta( every * {'Days':1, 'Weeks':7, 'Months':30, 'Years':365}[xunits] )
        pointDates = []

        data = []
        currentTime = 0
        uniquePoints = set()
        for i, total in enumerate(totals):
            data.append((currentTime, total))
            uniquePoints.add("%.2f"%total)
            currentTime += every

            # don't just += the timeDelta to currentDate, since adding days is all or nothing, ie:
            #   currentDate + timeDelta == currentDate, where timeDelta < 1
            # so the date will never advance for timeDeltas < 1.
            # as such we must start fresh each time and multiple the time delta appropriately.
            currentDate = startDate + (i+1)*timeDelta

            pointDates.append(currentDate.strftime('%m/%d/%Y'))

        #drawPointLabel will need these later
        self.pointDates = pointDates

        line = pyplot.PolyLine(data, width=2, colour="green", legend="Balance")
        lines = [line]
        if len(uniquePoints) > 1:
            # without more than one unique value, a best fit line doesn't make sense (and also causes freezes!)
            bestfitline = pyplot.PolyBestFitLine(data, N=2, width=2, colour="blue", legend="Trend")
            lines.append(bestfitline)
        self.Draw(pyplot.PlotGraphics(lines, "Balance Over Time", "Time (%s)"%xunits, "Total ($)"))

    def onMotion(self, event):
        #show closest point (when enbled)
        if self.GetEnablePointLabel() == True:
            #make up dict with info for the pointLabel
            #I've decided to mark the closest point on the closest curve
            dlst = self.GetClosestPoint( self._getXY(event), pointScaled= True)
            if dlst != []: #returns [] if none
                curveNum, legend, pIndex, pointXY, scaledXY, distance = dlst
                #make up dictionary to pass to my user function (see DrawPointLabel)
                mDataDict= {"pointXY":pointXY, "scaledXY":scaledXY, "pIndex": pIndex}
                #pass dict to update the pointLabel
                self.UpdatePointLabel(mDataDict)
        event.Skip() #go to next handler

    def drawPointLabel(self, dc, mDataDict):
        """
        This is the fuction that defines how the pointLabels are plotted
        dc - DC that will be passed
        mDataDict - Dictionary of data that you want to use for the pointLabel

        This just displays the total in a nicely-formatted money string.
        """
        #print mDataDict
        #if mDataDict['legend'] != 'Balance':
        #    return False

        dc.SetPen(wx.Pen(wx.BLACK))
        dc.SetBrush(wx.Brush( wx.BLACK, wx.SOLID ))

        sx, sy = mDataDict["scaledXY"] #scaled x,y of closest point
        dc.DrawRectangle(sx-5, sy-5, 10, 10)  #10by10 square centered on point
        px, py = mDataDict["pointXY"]
        #make a string to display
        line1, line2 = float2str(py), str(self.pointDates[mDataDict["pIndex"]])
        x1, y1 = dc.GetTextExtent(line1)
        x2, y2 = dc.GetTextExtent(line2)
        dc.DrawText(line1, sx, sy+1)
        dc.DrawText(line2, sx-(x2-x1)/2, sy+y1+3)
