#    https://launchpad.net/wxbanker
#    summarytab.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

from wxbanker import localization, bankcontrols, helpers
import wx, datetime
from wx.lib.pubsub import Publisher

class SummaryPanel(wx.Panel):
    def __init__(self, parent, plotFactory, bankController):
        wx.Panel.__init__(self, parent)
        self.bankController = bankController

        self.plotSettings = {'FitDegree': 2, 'Granularity': 100, 'Account': None}
        self.cachedData = None
        self.dateRange = None

        # create the plot panel
        self.plotPanel = plotFactory.createPanel(self, bankController)

        # create the controls at the bottom
        controlSizer = wx.BoxSizer()
        degCtrl = wx.SpinCtrl(self, min=1, max=20, initial=self.plotSettings['FitDegree'])
        # the date range controls
        self.startDate = bankcontrols.DateCtrlFactory(self)
        self.endDate = bankcontrols.DateCtrlFactory(self)

        controlSizer.Add(wx.StaticText(self, label=_("From")), 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(self.startDate, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(wx.StaticText(self, label=_("to")), 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(self.endDate, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(10)
        controlSizer.Add(wx.StaticText(self, label=_("Fit Curve Degree")), 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(degCtrl, 0, wx.ALIGN_CENTER_VERTICAL)
        degCtrl.SetMinSize = (20, -1)

        # put it all together
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.plotPanel, 1, wx.EXPAND)
        self.Sizer.Add(controlSizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 2)

        self.Layout()

        # bind to the spin buttons
        degCtrl.Bind(wx.EVT_SPINCTRL, self.onSpinFitDeg)
        self.Bind(wx.EVT_DATE_CHANGED, self.onDateRangeChanged)
        Publisher.subscribe(self.onAccountSelect, "view.account changed")
        
    def onDateRangeChanged(self, event):
        self.generateData()
    
    def getDateRange(self):
        return [helpers.wxdate2pydate(date) for date in (self.startDate.Value, self.endDate.Value)]

    def onAccountSelect(self, message):
        account = message.data
        self.plotSettings['Account'] = account
        self.generateData()

    def onSpinFitDeg(self, event):
        self.plotSettings['FitDegree'] = event.EventObject.Value
        self.generateData(useCache=True)

    def update(self):
        self.dateRange = self.bankController.Model.GetDateRange()
        self.startDate.Value = helpers.pydate2wxdate(self.dateRange[0])
        self.endDate.Value = helpers.pydate2wxdate(self.dateRange[1])
        self.generateData()

    def generateData(self, useCache=False):
        if useCache and self.cachedData is not None:
            totals = self.cachedData
        else:
            totals = self.bankController.Model.GetXTotals(self.plotSettings['Account'], daterange=self.getDateRange())
            self.cachedData = totals
        self.plotPanel.plotBalance(totals, self.plotSettings)
