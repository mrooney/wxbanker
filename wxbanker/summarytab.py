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

class SummaryPanel(wx.Panel):
    def __init__(self, parent, plotFactory, bankController):
        wx.Panel.__init__(self, parent)
        self.bankController = bankController
        self.helper = SummaryHelper()

        self.plotSettings = {'FitDegree': 2, 'Granularity': 100, 'Account': None}
        self.cachedData = None
        self.dateRange = None

        # create the plot panel
        self.plotPanel = plotFactory.createPanel(self, bankController)

        # create the controls at the bottom
        controlSizer = wx.BoxSizer()
        self.accountList = wx.ComboBox(self, style=wx.CB_READONLY)
        ##granCtrl = wx.SpinCtrl(self, min=10, max=1000, initial=self.plotSettings['Granularity'])
        degCtrl = wx.SpinCtrl(self, min=1, max=20, initial=self.plotSettings['FitDegree'])
        # the date range controls
        self.startDate = bankcontrols.DateCtrlFactory(self)
        self.endDate = bankcontrols.DateCtrlFactory(self)

        controlSizer.Add(wx.StaticText(self, label=_("Account")), 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(self.accountList, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(10)
        controlSizer.Add(wx.StaticText(self, label=_("From")), 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(self.startDate, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(wx.StaticText(self, label=_("to")), 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(self.endDate, 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(10)
        ##controlSizer.Add(wx.StaticText(self, label=_("Sample Points")), 0, wx.ALIGN_CENTER_VERTICAL)
        ##controlSizer.Add(granCtrl)
        ##controlSizer.AddSpacer(10)
        controlSizer.Add(wx.StaticText(self, label=_("Fit Curve Degree")), 0, wx.ALIGN_CENTER_VERTICAL)
        controlSizer.AddSpacer(5)
        controlSizer.Add(degCtrl, 0, wx.ALIGN_CENTER_VERTICAL)
        degCtrl.SetMinSize = (20, -1)

        # put it all together
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.plotPanel, 1, wx.EXPAND)
        self.Sizer.Add(controlSizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 2)

        # fill in the accounts
        self.updateAccountList(layout=False)

        self.Layout()

        # bind to the spin buttons
        ##granCtrl.Bind(wx.EVT_SPINCTRL, self.onSpinGran)
        degCtrl.Bind(wx.EVT_SPINCTRL, self.onSpinFitDeg)
        self.accountList.Bind(wx.EVT_COMBOBOX, self.onAccountSelect)
        self.Bind(wx.EVT_DATE_CHANGED, self.onDateRangeChanged)
        
    def onDateRangeChanged(self, event):
        self.generateData()
    
    def getDateRange(self):
        return [helpers.wxdate2pydate(date) for date in (self.startDate.Value, self.endDate.Value)]

    def onAccountSelect(self, event):
        index = event.Int
        if index == 0:
            account = None
        else:
            account = self.accountList.GetClientData(index)

        self.plotSettings['Account'] = account
        self.generateData()

    def onSpinGran(self, event):
        self.plotSettings['Granularity'] = event.EventObject.Value
        self.generateData()

    def onSpinFitDeg(self, event):
        self.plotSettings['FitDegree'] = event.EventObject.Value
        self.generateData(useCache=True)

    def update(self):
        self.dateRange = self.bankController.Model.GetDateRange()
        self.startDate.Value = helpers.pydate2wxdate(self.dateRange[0])
        self.endDate.Value = helpers.pydate2wxdate(self.dateRange[1])
        
        self.updateAccountList()
        self.generateData()

    def updateAccountList(self, layout=True):
        self.accountList.Clear()

        setToAll = True

        self.accountList.Append(_("All accounts"))
        for i, account in enumerate(self.bankController.Model.Accounts):
            self.accountList.Append(account.Name, account)
            if account is self.plotSettings['Account']:
                self.accountList.SetSelection(i+1) # +1 since All accounts
                setToAll = False

        if setToAll:
            self.accountList.SetSelection(0)
            # Make sure to set this, in case it was set to a deleted account.
            self.plotSettings['Account'] = None

    def generateData(self, useCache=False):
        if useCache and self.cachedData is not None:
            totals = self.cachedData
        else:
            totals = self.bankController.Model.GetXTotals(self.plotSettings['Account'], daterange=self.getDateRange())
            self.cachedData = totals
        self.plotPanel.plotBalance(totals, self.plotSettings)

class SummaryHelper(object):
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
    
