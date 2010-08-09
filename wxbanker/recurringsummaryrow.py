#    https://launchpad.net/wxbanker
#    recurringsummaryrow.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

import wx
from wxbanker import bankcontrols

class RecurringSummaryText(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(wx.BLACK)

        self.contentPanel = wx.Panel(self)
        self.contentPanel.SetBackgroundColour(wx.Color(224,238,238))
        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(self.contentPanel, 1, wx.EXPAND|wx.ALL, 1)

        self.summaryText = wx.StaticText(self.contentPanel, label="Summary", name="RecurringSummaryText")
        self.contentPanel.Sizer = wx.BoxSizer()
        self.contentPanel.Sizer.Add(self.summaryText, 0, wx.ALIGN_CENTER|wx.ALL, 2)

    def SetLabel(self, text):
        self.summaryText.Label = text

class RecurringSummaryRow(bankcontrols.GBRow):
    def __init__(self, parent, row):
        bankcontrols.GBRow.__init__(self, parent, row)
        
        self.summaryText = RecurringSummaryText(parent)

        self.AddNext(wx.StaticText(parent, label=_("Summary:")))
        self.AddNext(self.summaryText, span=(1,3))
        
    def UpdateSummary(self, recurringObj):
        self.summaryText.SetLabel(recurringObj.GetRecurrance())
