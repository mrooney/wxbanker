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
try:
    import plot as pyplot
except ImportError:
    raise NoNumpyException()

from banker import float2str
import datetime


class SummaryPanel(wx.Panel):
    def __init__(self, parent, frame):
        wx.Panel.__init__(self, parent)
        self.frame = frame
        self.plotSettings = {'FitDegree': 2, 'Granularity': 100}
        self.cachedData = None

        # create the plot panel
        self.plotPanel = AccountPlotCanvas(self)

        # create the controls at the bottom
        controlSizer = wx.BoxSizer()
        granCtrl = wx.SpinCtrl(self, min=10, max=1000, initial=self.plotSettings['Granularity'])
        degCtrl = wx.SpinCtrl(self, min=1, max=20, initial=self.plotSettings['FitDegree'])
        controlSizer.Add(wx.StaticText(self, label="Sample Points"), 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.Add(granCtrl)
        controlSizer.AddSpacer(20)
        controlSizer.Add(wx.StaticText(self, label="Fit Curve Degree"), 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.Add(degCtrl)
        controlSizer.Layout()

        # put it all together
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.plotPanel, 1, wx.EXPAND)
        self.plotPanel.SetShowScrollbars(False)
        self.Sizer.Add(controlSizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 3)
        self.Layout()

        # bind to the spin buttons
        granCtrl.Bind(wx.EVT_SPINCTRL, self.onSpinGran)
        degCtrl.Bind(wx.EVT_SPINCTRL, self.onSpinFitDeg)

    def onSpinGran(self, event):
        self.plotSettings['Granularity'] = event.EventObject.Value
        self.generateData()

    def onSpinFitDeg(self, event):
        self.plotSettings['FitDegree'] = event.EventObject.Value
        self.generateData(useCache=True)

    def generateData(self, useCache=False):
        if useCache and self.cachedData is not None:
            totals, startDate, delta = self.cachedData
        else:
            totals, startDate, delta = self.getPoints(self.plotSettings['Granularity'])
            self.cachedData = totals, startDate, delta

        self.plotPanel.plotBalance(totals, startDate, delta, "Days", fitdegree=self.plotSettings['FitDegree'])

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
            return [0.0 for i in range(numPoints)], datetime.date.today(), 1./100000
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
                if i < (numPoints-1):
                    # average the totals over this period
                    start = i*groupSize
                    end = start + groupSize
                    points = days[start:end]
                    pointSum = sum(points)
                    avgVal = pointSum / float(groupSize)
                    returnPoints.append(total+avgVal)
                    total += pointSum
                else:
                    # this is the last one, so make it the actual total balance!
                    returnPoints.append(sum(days))

        return returnPoints, startDate, delta

class AccountPlotCanvas(pyplot.PlotCanvas):
    def __init__(self, *args, **kwargs):
        pyplot.PlotCanvas.__init__(self, *args, **kwargs)
        self.pointDates = []
        self.startDate = None #TODO: get rid of this and use self.pointDates[0]
        self.SetEnablePointLabel(True)
        self.SetEnableLegend(True)
        self.SetPointLabelFunc(self.drawPointLabel)

        self.canvas.Bind(wx.EVT_MOTION, self.onMotion)

    def plotBalance(self, totals, startDate, every, xunits="Days", fitdegree=2):
        self.startDate = startDate
        timeDelta = datetime.timedelta( every * {'Days':1, 'Weeks':7, 'Months':30, 'Years':365}[xunits] )
        pointDates = []

        data = []
        currentTime = 0
        uniquePoints = set()
        for i, total in enumerate(totals):
            data.append((currentTime, total))
            uniquePoints.add("%.2f"%total)
            currentTime += every

            if i < len(totals)-1:
                # Don't just += the timeDelta to currentDate, since adding days is all or nothing, ie:
                #   currentDate + timeDelta == currentDate, where timeDelta < 1 (bad!)
                # ...so the date will never advance for timeDeltas < 1, no matter how many adds you do.
                # As such we must start fresh each time and multiply the time delta appropriately.
                currentDate = startDate + (i+1)*timeDelta
            else:
                # This is the last point, so make sure the date is set to today.
                # Regardless of the date of the last transaction, the total is still
                # the total as of today, which is what a user expects to see.
                currentDate = datetime.date.today()

            pointDates.append(currentDate.strftime('%m/%d/%Y'))

        #drawPointLabel will need these later
        self.pointDates = pointDates

        line = pyplot.PolyLine(data, width=2, colour="green", legend="Balance")
        lines = [line]
        if len(uniquePoints) > 1:
            # without more than one unique value, a best fit line doesn't make sense (and also causes freezes!)
            bestfitline = pyplot.PolyBestFitLine(data, N=fitdegree, width=2, colour="blue", legend="Trend")
            lines.append(bestfitline)
        self.Draw(pyplot.PlotGraphics(lines, "Total Balance Over Time", "Date", "Balance"))

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

    def _xticks(self, *args):
        ticks = pyplot.PlotCanvas._xticks(self, *args)
        myTicks = []
        for tick in ticks:
            floatVal = tick[0]
            stringVal = str(self.startDate + datetime.timedelta(floatVal))
            myTicks.append( (floatVal, stringVal) )
        return myTicks

    def _yticks(self, *args):
        ticks = pyplot.PlotCanvas._yticks(self, *args)
        myTicks = []
        for tick in ticks:
            floatVal = tick[0]
            stringVal = float2str(floatVal)
            if stringVal.endswith('.00'):
                stringVal = stringVal[:-3]
            myTicks.append( (floatVal, stringVal) )
        return myTicks
