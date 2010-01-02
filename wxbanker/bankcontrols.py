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
from wxbanker.smoothsizer import SmoothStaticBoxSizer
from wxbanker import localization


def fixMinWidth(ctrl, values):
    """Set the minimum width of a control to the max of all possible values."""
    # Calculate the width of the button.
    ctrl.Freeze()
    minWidth, minHeight = ctrl.MinSize
    for value in values:
        ctrl.Label = value
        cWidth = ctrl.BestSize[0]
        minWidth = max((minWidth, cWidth))
    ctrl.MinSize = minWidth, minHeight
    ctrl.Thaw()


def DateCtrlFactory(parent, style=wx.DP_DROPDOWN|wx.DP_SHOWCENTURY):
    """
    A function to return a DateCtrl given a parent and style.
    This factory prefers creating a generic (non-native) control as it is more flexible,
    but will return a native if necessary (Windows < wx 2.8.8.0, OSX).
    """
    isGeneric = False
    try:
        DatePickerClass = wx.GenericDatePickerCtrl
        isGeneric = True
    except AttributeError:
        DatePickerClass = wx.DatePickerCtrl

    dateCtrl = DatePickerClass(parent, style=wx.DP_DROPDOWN|wx.DP_SHOWCENTURY)
    dateCtrl.SetToolTipString(_("Date"))
    dateCtrl.customKeyHandler = None

    if isGeneric:
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
            dateCtrl.customKeyHandler = onDateChar
        except Exception:
            print "Unable to bind to dateCtrl's text field, that's odd! Please file a bug: https://bugs.launchpad.net/wxbanker/+filebug"
            
        # date controls seem to need an extra bit of width to be fully visible.
        bestSize = dateCtrl.BestSize
        bestSize[0] += 5
        dateCtrl.SetMinSize(bestSize)

    return dateCtrl


class HyperlinkText(wx.HyperlinkCtrl):
    """A hyper link control with no special visited color, which can accept a click callback function."""
    def __init__(self, parent, id=-1, label='', url='', style=wx.NO_BORDER | wx.HL_ALIGN_CENTRE, onClick=None, *args, **kwargs):
        # By default, disable the right-click "Copy URL" menu.
        wx.HyperlinkCtrl.__init__(self, parent, id, label, url, style=style, *args, **kwargs)

        # Don't show a different color for previously clicked items.
        self.VisitedColour = wx.BLUE

        # Bind to the optional callable.
        if callable:
            self.Bind(wx.EVT_HYPERLINK, onClick)


class CompactableComboBox(wx.ComboBox):
    """A combobox which can be Compact'd to only take up as much space as necessary."""
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
        fixMinWidth(self, [self.BaseLabel % v for v in ldict.values()])
        self.State = self._State

    def GetState(self):
        return self._State

    def SetState(self, state):
        self._State = state
        self.Label = self.BaseLabel % self.LabelDict[state]

    LabelDict = property(GetLabelDict, SetLabelDict)
    State = property(GetState, SetState)


class HintedTextCtrl(wx.SearchCtrl):
    def __init__(self, *args, **kwargs):
        conf = {"hint": "", "icon": None, "handler": None}
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

        self.SetDescriptiveText(conf['hint'])

        try:
            self.Children[0].Bind(wx.EVT_CHAR, self.onChar)
            if conf['handler']:
                self.Children[0].Bind(wx.EVT_KEY_DOWN, conf['handler'])
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
            
            
class GBRow(wx.Window):
    """
    A convenience class for representing a row in a GridBagSizer,
    allowing it to be hidden.
    """
    def __init__(self, parent, row, *args, **kwargs):
        wx.Window.__init__(self, parent, *args, **kwargs)
        self.Hide()
        self.Row = row
        self.Column = 0
        
    def AddNext(self, ctrl, *args, **kwargs):
        if "flag" in kwargs:
            kwargs["flag"] = kwargs["flag"] | wx.ALIGN_CENTER_VERTICAL
        else:
            kwargs["flag"] = wx.ALIGN_CENTER_VERTICAL

        # Add the item.
        self.Parent.Sizer.Add(ctrl, wx.GBPosition(self.Row, self.Column), *args, **kwargs)
        
        # Increment the column count by the number of columns the item spans.
        self.Column += self.Parent.Sizer.GetItemSpan(ctrl)[1]
