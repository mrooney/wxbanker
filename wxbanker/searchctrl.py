#    https://launchpad.net/wxbanker
#    searchctrl.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker.lib.pubsub import Publisher


class SearchCtrl(wx.Panel):
    def __init__(self, parent, bankController):
        wx.Panel.__init__(self, parent)
        self.ID_TIMER = wx.NewId()
        self.SearchTimer = wx.Timer(self, self.ID_TIMER)
        
        self.bankController = bankController

        self.searchCtrl = bankcontrols.UpdatableSearchCtrl(self, value="", size=(200, -1), style=wx.TE_PROCESS_ENTER)
        # Try to grab the GTK system icon for clearing a search, otherwise we'll get the wxPython one.
        iconSize = self.searchCtrl.GetClientRect().GetHeight() - 2
        clearBitmap = wx.ArtProvider.GetBitmap('edit-clear', wx.ART_OTHER, [iconSize, iconSize])
        if clearBitmap:
            self.searchCtrl.SetCancelBitmap(clearBitmap)
        self.searchCtrl.ShowCancelButton(True)
        self.searchCtrl.ShowSearchButton(False)
        self.searchCtrl.DescriptiveText = _("Search transactions")
        self.searchCtrl.SetForegroundColour('DARK GRAY')

        # The More/Less button.
        self.moreButton = bankcontrols.MultiStateButton(self, labelDict={True: _("More options"), False: _("Less options")}, state=True)

        self.matchChoices = [_("Amount"), _("Description"), _("Date")]
        self.descriptionSelection = 1
        self.matchBox = bankcontrols.CompactableComboBox(self, value=self.matchChoices[1], choices=self.matchChoices, style=wx.CB_READONLY)

        topSizer = wx.BoxSizer()
        topSizer.Add(self.searchCtrl, 0, wx.ALIGN_CENTER_VERTICAL)
        topSizer.AddSpacer(10)
        topSizer.Add(self.moreButton, 0, wx.ALIGN_CENTER_VERTICAL)

        self.moreSizer = moreSizer = wx.BoxSizer()
        moreSizer.Add(wx.StaticText(self, label=_("Match: ")), 0, wx.ALIGN_CENTER_VERTICAL)
        moreSizer.Add(self.matchBox, 0, wx.ALIGN_CENTER_VERTICAL)

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(topSizer, 0, wx.ALIGN_RIGHT|wx.TOP|wx.BOTTOM, 2)
        self.Sizer.Add(moreSizer, 0, wx.ALIGN_RIGHT|wx.BOTTOM, 2)
        self.matchBox.Compact()
        self.Layout()

        self.searchCtrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.onCancel)
        self.searchCtrl.Bind(wx.EVT_TEXT, self.onText)
        #self.searchCtrl.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.onSearch)
        self.searchCtrl.Bind(wx.EVT_TEXT_ENTER, self.onSearch)
        self.moreButton.Bind(wx.EVT_BUTTON, self.onToggleMore)
        # Bindings to search on settings change automatically.
        self.matchBox.Bind(wx.EVT_COMBOBOX, self.onSearchTrigger)
        self.Bind(wx.EVT_TIMER, self.onSearchTimer)
        
        Publisher.subscribe(self.onExternalSearch, "SEARCH.EXTERNAL")

        # Initially hide the extra search options.
        self.onToggleMore()
        
    def onText(self, event):
        self.SearchTimer.Start(500, wx.TIMER_ONE_SHOT)
        
    def onSearchTimer(self, event):
        self.onSearch()

    def onSearchTrigger(self, event):
        event.Skip()
        self.onSearch()

    def onSearch(self, event=None):
        # Stop any timer that may be active, in the case of a manual search.
        self.SearchTimer.Stop()
        searchString = self.searchCtrl.Value # For a date, should be YYYY-MM-DD.
        matchType = self.matchChoices.index(self.matchBox.Value)

        searchInfo = (searchString, matchType)
        # Consider a blank search as a search cancellation.
        if searchString == "":
            self.onCancel()
        else:
            Publisher.sendMessage("SEARCH.INITIATED", searchInfo)
            self.searchCtrl.SetForegroundColour('BLACK')
            
    def onExternalSearch(self, message):
        # If something else performs a search (such as Tag context menu), update the Value and search.
        tagObj = message.data
        fullTag = str(tagObj)
        # An external search is on description, so set that.
        self.matchBox.Selection = self.descriptionSelection
        self.searchCtrl.UpdateValue(fullTag)
        # A SetValue will trigger a search after the timer, but let's trigger one immediately for responsiveness.
        self.onSearch()

    def onCancel(self, event=None):
        # Don't clear the value if there isn't one, it will trigger an EVT_TEXT, causing an infinite search -> cancel loop.
        if self.searchCtrl.Value:
            self.searchCtrl.Value = ""
        Publisher.sendMessage("SEARCH.CANCELLED")

    def onToggleMore(self, event=None):
        # Show or hide the advanced search options.
        showLess = self.Sizer.IsShown(self.moreSizer)
        self.Sizer.Show(self.moreSizer, not showLess)

        # Update appropriate strings, and make them fully translatable.
        self.moreButton.State = showLess
        if showLess:
            tipActionStr = _("Show advanced search options")
        else:
            tipActionStr = _("Hide advanced search options")
        self.moreButton.SetToolTipString(tipActionStr)

        # Give or take the appropriate amount of space.
        self.Parent.Layout()
        Publisher.sendMessage("SEARCH.MORETOGGLED")
