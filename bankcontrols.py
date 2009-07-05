#    https://launchpad.net/wxbanker
#    bankcontrols.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

import wx, datetime
from wx.lib.pubsub import Publisher
from smoothsizer import SmoothStaticBoxSizer
import localization


def DateCtrlFactory(parent, style=wx.DP_DROPDOWN|wx.DP_SHOWCENTURY):
    # The date control. We want the Generic control, which is a composite control
    # and allows us to bind to its enter, but on Windows with wxPython < 2.8.8.0,
    # it won't be available.
    doBind = False
    try:
        DatePickerClass = wx.GenericDatePickerCtrl
        doBind = True
    except AttributeError:
        DatePickerClass = wx.DatePickerCtrl

    dateCtrl = DatePickerClass(parent, style=wx.DP_DROPDOWN|wx.DP_SHOWCENTURY)
    dateCtrl.SetToolTipString(_("Date"))

    if doBind:
        def onDateChar(event):
            key = event.GetKeyCode()
            incr = 0
            if key == wx.WXK_DOWN:
                incr = -1
            elif key == wx.WXK_UP:
                incr = 1
            else:
                event.Skip()

            if incr:
                dateCtrl.Value += incr*wx.DateSpan(days=1)

        try:
            dateCtrl.Children[0].Children[0].Bind(wx.EVT_KEY_DOWN, onDateChar)
        except Exception:
            print "Unable to bind to dateCtrl's text field, that's odd! Please file a bug: https://bugs.launchpad.net/wxbanker/+filebug"

    return dateCtrl


class HyperlinkText(wx.HyperlinkCtrl):
    def __init__(self, parent, id=-1, label='', url='', style=wx.NO_BORDER | wx.HL_ALIGN_CENTRE, onClick=None, *args, **kwargs):
        # By default, disable the right-click "Copy URL" menu.
        wx.HyperlinkCtrl.__init__(self, parent, id, label, url, style=style, *args, **kwargs)

        # Don't show a different color for previously clicked items.
        self.VisitedColour = wx.BLUE

        # Bind to the optional callable.
        if callable:
            self.Bind(wx.EVT_HYPERLINK, onClick)


class CompactableComboBox(wx.ComboBox):
    def Compact(self):
        # Calculates and sets the minimum width of the ComboBox.
        # Width is based on the width of the longest string.
        # From the ideas of Mike Rooney, Cody Precord, Robin Dunn and Raffaello.
        comboStrings = self.Strings
        if len(comboStrings) == 0:
            self.SetMinSize(wx.DefaultSize)
        else:
            height = self.Size[1]
            maxTextWidth = max([self.Parent.GetTextExtent(s.strip())[0] for s in comboStrings])
            self.SetMinSize((maxTextWidth + height + 8, height))


class MultiStateButton(wx.Button):
    def __init__(self, parent, id=-1, baseLabel="%s", labelDict=None, state=None, style=0):
        wx.Button.__init__(self, parent, id=id, style=style)
        self.BaseLabel = baseLabel
        self._State = state

        if labelDict is None:
            labelDict = {None: ""}
        self.LabelDict = labelDict
        self.State = state

    def GetLabelDict(self):
        return self._LabelDict

    def SetLabelDict(self, ldict):
        self._LabelDict = ldict

        # Calculate the width of the button.
        self.Freeze()
        minWidth, minHeight = self.MinSize
        for modifier in ldict.values():
            self.Label = self.BaseLabel % modifier
            cWidth = self.BestSize[0]
            minWidth = max((minWidth, cWidth))
        self.MinSize = minWidth, minHeight
        # Restore the original State (and Label)
        self.State = self._State
        self.Thaw()

    def GetState(self):
        return self._State

    def SetState(self, state):
        self._State = state
        self.Label = self.BaseLabel % self.LabelDict[state]

    LabelDict = property(GetLabelDict, SetLabelDict)
    State = property(GetState, SetState)


class HintedTextCtrl(wx.SearchCtrl):
    def __init__(self, *args, **kwargs):
        conf = {"hint": "", "icon": None}
        for kw in conf.keys():
            if kw in kwargs:
                conf[kw] = kwargs[kw]
                del kwargs[kw]

        wx.SearchCtrl.__init__(self, *args, **kwargs)
        self.ShowCancelButton(False)

        if conf['icon'] is None:
            self.ShowSearchButton(False)
        else:
            self.SetSearchBitmap(wx.ArtProvider.GetBitmap(conf['icon']))
            self.ShowSearchButton(True)

        self.SetToolTipString(conf['hint'])
        self.SetDescriptiveText(conf['hint'])

        try:
            self.Children[0].Bind(wx.EVT_CHAR, self.onChar)
        except IndexError:
            # On OSX for example, a SearchCtrl is native and has no Children.
            pass

    def onChar(self, event):
        if event.KeyCode == wx.WXK_TAB:
            if event.ShiftDown():
                self.Navigate(wx.NavigationKeyEvent.IsBackward)
            else:
                self.Navigate()
        else:
            event.Skip()
