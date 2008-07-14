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
        totals, startDate = self.frame.bank.getTotalsEvery(7)
        self.plotPanel.plotBalance(totals, startDate, 1, "Weeks")


class AccountPlotCanvas(pyplot.PlotCanvas):
    def __init__(self, *args, **kwargs):
        pyplot.PlotCanvas.__init__(self, *args, **kwargs)
        self.pointDates = []
        self.SetEnablePointLabel(True)
        self.SetPointLabelFunc(self.drawPointLabel)

        self.canvas.Bind(wx.EVT_MOTION, self.onMotion)

    def plotBalance(self, totals, startDate, every, xunits="Days"):
        timeDelta = datetime.timedelta( every * {'Days':1, 'Weeks':7, 'Months':30, 'Years':365}[xunits] )
        currentDate = startDate
        pointDates = []

        currentTotal = currentTime = 0
        data = []

        for total in totals:
            currentTotal += total
            data.append((currentTime, currentTotal))
            currentTime += every
            currentDate += timeDelta

            pointDates.append(currentDate.strftime('%m/%d/%Y'))

        #drawPointLabel will need these later
        self.pointDates = pointDates

        line = pyplot.PolyLine(data, width=3, colour="green")
        bestfitline = pyplot.PolyBestFitLine(data, N=2, width=3, colour="blue")
        self.Draw(pyplot.PlotGraphics([line, bestfitline], "Balance Over Time", "Time (%s)"%xunits, "Total ($)"))

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
