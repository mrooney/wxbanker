#    https://launchpad.net/wxbanker
#    tagtransactiondialog.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker.bankobjects.tag import Tag, EmptyTagException

class TagTransactionsPanel(wx.Panel):
    def __init__(self, parent, transactions):
        wx.Panel.__init__(self, parent)
        self.Transactions = transactions
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.AddSpacer(6)
        
        introText = wx.StaticText(self, label=_("You can also tag a transaction by putting #tagname anywhere in the description."))
        textCtrlText = wx.StaticText(self, label=_("Tag:"))
        self.textCtrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        removalText = wx.StaticText(self, label=_("To remove this tag later, simply remove it from the description or right-click on the transaction."))
        
        textCtrlSizer = wx.BoxSizer()
        textCtrlSizer.Add(textCtrlText, flag=wx.ALIGN_CENTER_VERTICAL)
        textCtrlSizer.AddSpacer(9)
        textCtrlSizer.Add(wx.StaticText(self, label=Tag.TAG_CHAR), flag=wx.ALIGN_CENTER_VERTICAL)
        textCtrlSizer.Add(self.textCtrl)
        
        # Button sizer
        self.buttonSizer = wx.BoxSizer()
        tagButton = wx.Button(self, label=_("Add Tag"), id=wx.ID_OK)
        cancelButton = wx.Button(self, label=_("Cancel"), id=wx.ID_CANCEL)
        self.buttonSizer.AddStretchSpacer()
        self.buttonSizer.Add(tagButton)
        self.buttonSizer.AddSpacer(6)
        self.buttonSizer.Add(cancelButton)
        self.buttonSizer.AddSpacer(6)
        
         # Main sizer
        self.Sizer.AddSpacer(12)
        self.Sizer.Add(introText)
        self.Sizer.AddSpacer(12)
        self.Sizer.Add(textCtrlSizer)
        self.Sizer.AddSpacer(24)
        self.Sizer.Add(removalText)
        self.Sizer.AddSpacer(12)
        self.Sizer.Add(self.buttonSizer, flag=wx.ALIGN_RIGHT|wx.EXPAND)
        self.Sizer.AddSpacer(6)
        
        for text in (introText, removalText):
            text.Wrap(400)
        
        # Focus the textctrl so the user can just start typing.
        self.textCtrl.SetFocus()
        
        self.textCtrl.Bind(wx.EVT_TEXT_ENTER, self.onTagEnter)
        self.Bind(wx.EVT_BUTTON, self.onButton)
        
    def onTagEnter(self, event):
        self.applyTag()
        # Dialogs auto-close on certain IDs but a text entry is not one of them.
        self.Parent.Destroy()
        
    def onButton(self, event):
        """If the tag button was clicked tag the transactions, and close the dialog in any case (Cancel)."""
        assert event.Id in (wx.ID_OK, wx.ID_CANCEL)
        
        if event.Id == wx.ID_OK:
            self.applyTag()
               
        #self.Parent.Destroy()
        event.Skip()
        
    def applyTag(self):
         # Strip the tag character in case the user was unclear about needing to use it.
        tag = self.textCtrl.Value.strip(Tag.TAG_CHAR)
        
        # If there's no tag, there's no tagging to do.
        if not tag:
            return
        
        # Apply the tag to each transaction selected.
        for transaction in self.Transactions:
            transaction.AddTag(tag)
        
            
class TagTransactionsDialog(wx.Dialog):
    def __init__(self, parent, transactions):
        wx.Dialog.__init__(self, parent, title=_("Add a tag"))
        self.Sizer = wx.BoxSizer()
        tagPanel = TagTransactionsPanel(self, transactions)
        self.Sizer.AddSpacer(6)
        self.Sizer.Add(tagPanel, 1, wx.EXPAND)
        self.Sizer.AddSpacer(6)
        self.Fit()
        