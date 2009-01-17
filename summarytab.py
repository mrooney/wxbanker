#    https://launchpad.net/wxbanker
#    summarytab.py: Copyright 2007, 2008 Mike Rooney <michael@wxbanker.org>
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
import localization
import wx
try:
    import plot as pyplot
except ImportError:
    raise NoNumpyException()

from banker import Bank
import datetime


class SummaryPanel(wx.Panel):
    def __init__(self, parent, bankController):
        wx.Panel.__init__(self, parent)
        self.bankController = bankController
        
        self.plotSettings = {'FitDegree': 2, 'Granularity': 100}
        self.cachedData = None

        # create the plot panel
        self.plotPanel = AccountPlotCanvas(bankController, self)

        # create the controls at the bottom
        controlSizer = wx.BoxSizer()
        granCtrl = wx.SpinCtrl(self, min=10, max=1000, initial=self.plotSettings['Granularity'])
        degCtrl = wx.SpinCtrl(self, min=1, max=20, initial=self.plotSettings['FitDegree'])
        controlSizer.Add(wx.StaticText(self, label=_("Sample Points")), 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.Add(granCtrl)
        controlSizer.AddSpacer(20)
        controlSizer.Add(wx.StaticText(self, label=_("Fit Curve Degree")), 0, wx.ALIGN_CENTER_VERTICAL)
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
        return self.bankController.Model.GetXTotals(numPoints)

class AccountPlotCanvas(pyplot.PlotCanvas):
    def __init__(self, bankController, *args, **kwargs):
        pyplot.PlotCanvas.__init__(self, *args, **kwargs)
        self.bankController = bankController
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

            # Don't just += the timeDelta to currentDate, since adding days is all or nothing, ie:
            #   currentDate + timeDelta == currentDate, where timeDelta < 1 (bad!)
            # ...so the date will never advance for timeDeltas < 1, no matter how many adds you do.
            # As such we must start fresh each time and multiply the time delta appropriately.
            currentDate = startDate + (i+1)*timeDelta

            pointDates.append(currentDate.strftime('%m/%d/%Y'))

        #drawPointLabel will need these later
        self.pointDates = pointDates

        line = pyplot.PolyLine(data, width=2, colour="green", legend=_("Balance"))
        lines = [line]
        if len(uniquePoints) > 1:
            # without more than one unique value, a best fit line doesn't make sense (and also causes freezes!)
            bestfitline = pyplot.PolyBestFitLine(data, N=fitdegree, width=2, colour="blue", legend=_("Trend"))
            lines.append(bestfitline)
        self.Draw(pyplot.PlotGraphics(lines, _("Total Balance Over Time"), _("Date"), _("Balance")))

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
        line1, line2 = self.bankController.Model.float2str(py), str(self.pointDates[mDataDict["pIndex"]])
        x1, y1 = dc.GetTextExtent(line1)
        x2, y2 = dc.GetTextExtent(line2)
        dc.DrawText(line1, sx, sy+1)
        dc.DrawText(line2, sx-(x2-x1)/2, sy+y1+3)

    def _xticks(self, *args):
        ticks = pyplot.PlotCanvas._xticks(self, *args)
        myTicks = []
        lastTick = None
        for tick in ticks:
            floatVal = tick[0]
            stringVal = str(self.startDate + datetime.timedelta(floatVal))
            
            # Don't display this xtick if it isn't different from the last one.
            if stringVal == lastTick:
                stringVal = ""
            else:
                lastTick = stringVal
                
            myTicks.append( (floatVal, stringVal) )
        return myTicks

    def _yticks(self, *args):
        ticks = pyplot.PlotCanvas._yticks(self, *args)
        myTicks = []
        for tick in ticks:
            floatVal = tick[0]
            stringVal = self.bankController.Model.float2str(floatVal)
            if stringVal.endswith('.00'):
                stringVal = stringVal[:-3]
            myTicks.append( (floatVal, stringVal) )
        return myTicks
