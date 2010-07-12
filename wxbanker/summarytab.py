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
        self.plotFactory = plotFactory
        self.bankController = bankController

        self.plotSettings = {'FitDegree': 2, 'Granularity': 100, 'Account': None, 'Months': 12}
        self.plotLabels = [_("Trend Degree"), _("Months")]
        self.currentPlotIndex = 0
        self.cachedData = None
        self.dateRange = None
        self.isActive = False

        # create the plot panel
        self.plotPanel = plotFactory.createPanel(self, bankController)

        # create the controls at the bottom
        controlSizer = wx.BoxSizer()
        self.graphChoice = wx.Choice(self, choices=[plot.NAME for plot in plotFactory.Plots])
        self.optionCtrl = wx.SpinCtrl(self, min=1, max=24, initial=self.plotSettings['FitDegree'])
        # the date range controls
        self.startDate = bankcontrols.DateCtrlFactory(self)
        self.endDate = bankcontrols.DateCtrlFactory(self)

        self.optionText = wx.StaticText(self, label=self.plotLabels[0])
        self.fromText = wx.StaticText(self, label=_("From"))
        self.toText = wx.StaticText(self, label=_("to"))
        controlSizer.Add(wx.StaticText(self, label=_("Graph")), 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(self.graphChoice, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(10)
        controlSizer.Add(self.fromText, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(self.startDate, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(self.toText, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(self.endDate, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(10)
        controlSizer.Add(self.optionText, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(self.optionCtrl, 0, wx.ALIGN_CENTER_VERTICAL)
        self.optionCtrl.SetMinSize = (20, -1)

        # put it all together
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.plotPanel, 1, wx.EXPAND)
        self.Sizer.Add(controlSizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 6)

        self.Layout()

        # bind to the spin buttons
        self.graphChoice.Bind(wx.EVT_CHOICE, self.onGraphChoice)
        self.optionCtrl.Bind(wx.EVT_SPINCTRL, self.onOptionSpin)
        self.Bind(wx.EVT_DATE_CHANGED, self.onDateRangeChanged)
        Publisher.subscribe(self.onAccountSelect, "view.account changed")
        
    def onGraphChoice(self, event):
        index = self.graphChoice.GetSelection()
        # Replace the graph
        newPlot = self.plotFactory.createPanel(self, self.bankController, index)
        self.Sizer.Replace(self.plotPanel, newPlot)
        self.plotPanel = newPlot
        self.currentPlotIndex = index
        self.generateData(useCache=True)
        
        # Update the controls
        self.optionText.Label = self.plotLabels[index]
        self.optionCtrl.Value = self.plotSettings[self.getOptionKey(index)]
        for ctrl in (self.fromText, self.toText, self.startDate, self.endDate):
            ctrl.Show(index == 0)
        
        # A replace does not Layout, and we have made some changes.
        self.Layout()
        
    def onDateRangeChanged(self, event):
        self.generateData()
        
    def getOptionKey(self, index):
        return ['FitDegree', 'Months'][index]
    
    def getDateRange(self):
        return [helpers.wxdate2pydate(date) for date in (self.startDate.Value, self.endDate.Value)]

    def onAccountSelect(self, message):
        account = message.data
        self.plotSettings['Account'] = account
        # If this tab isn't being viewed, no need to generate anything just yet.
        if self.isActive:
            self.generateData()

    def onOptionSpin(self, event):
        self.plotSettings[self.getOptionKey(self.currentPlotIndex)] = event.EventObject.Value
        self.generateData(useCache=True)

    def onEnter(self):
        self.isActive = True
        self.dateRange = self.bankController.Model.GetDateRange()
        self.startDate.Value = helpers.pydate2wxdate(self.dateRange[0])
        self.endDate.Value = helpers.pydate2wxdate(self.dateRange[1])
        self.generateData()
        
    def onExit(self):
        self.isActive = False

    def generateData(self, useCache=False):
        if useCache and self.cachedData is not None:
            totals = self.cachedData
        else:
            totals = self.bankController.Model.GetXTotals(self.plotSettings['Account'], daterange=self.getDateRange())
            self.cachedData = totals
        self.plotPanel.plotBalance(totals, self.plotSettings)
