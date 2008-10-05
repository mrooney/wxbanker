#! /usr/bin/python
#
#    https://launchpad.net/wxbanker
#    menubar.py: Copyright 2007, 2008 Mike Rooney <wxbanker@rowk.com>
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

import wx, webbrowser
from wx.lib.wordwrap import wordwrap
import version

class BankMenuBar(wx.MenuBar):
    ID_FAQ = wx.NewId()
    ID_QUESTION = wx.NewId()
    ID_REPORTBUG = wx.NewId()
    
    def __init__(self, *args, **kwargs):
        wx.MenuBar.__init__(self, *args, **kwargs)
        
        helpMenu = wx.Menu()
        
        faqItem = wx.MenuItem(helpMenu, self.ID_FAQ, "View &FAQs", "View Frequently Asked Questions online")
        faqItem.Bitmap = wx.ArtProvider.GetBitmap("wxART_comments")
        helpMenu.AppendItem(faqItem)
        
        questionItem = wx.MenuItem(helpMenu, self.ID_QUESTION, "Ask a &Question", "Ask a question online")
        questionItem.Bitmap = wx.ArtProvider.GetBitmap("wxART_user_comment")
        helpMenu.AppendItem(questionItem)
        
        bugItem = wx.MenuItem(helpMenu, self.ID_REPORTBUG, "&Report a Bug", "Report a bug to the developer online")
        bugItem.Bitmap = wx.ArtProvider.GetBitmap("wxART_bug")
        helpMenu.AppendItem(bugItem)
        
        aboutItem = helpMenu.Append(wx.ID_ABOUT, "&About", "More information about wxBanker")
        
        self.Append(helpMenu, "&Help")
        
        self.Bind(wx.EVT_MENU, self.onClickAbout)
        helpMenu.Bind(wx.EVT_MENU, self.onClickAbout)
        
    def onMenuEvent(self, event):
        handler = {
            self.ID_FAQ: self.onClickFAQs,
            self.ID_QUESTION: self.onClickAskQuestion,
            self.ID_REPORTBUG: self.onClickReportBug,
            wx.ID_ABOUT: self.onClickAbout,
        }[event.Id]
        
        handler(event)
        
    def onClickFAQs(self, event):
        webbrowser.open("https://answers.launchpad.net/wxbanker/+faqs")
        
    def onClickAskQuestion(self, event):
        webbrowser.open("https://launchpad.net/wxbanker/+addquestion")
        
    def onClickReportBug(self, event):
        webbrowser.open("https://launchpad.net/wxbanker/+filebug")
        
    def onClickAbout(self, event):
        info = wx.AboutDialogInfo()
        info.Name = "wxBanker"
        info.Version = str(version.NUMBER)
        info.Copyright = "Copyright 2007, 2008 Mike Rooney (wxbanker@rowk.com)"
        info.Description = "A lightweight personal finance management application."
        info.WebSite = ("https://launchpad.net/wxbanker", "https://launchpad.net/wxbanker")
        info.Developers = ['Mike Rooney (wxbanker@rowk.com)',]
        info.Artists = ['Mark James (www.famfamfam.com/lab/icons/silk/)',]
        info.License = open('gpl.txt').read()
        wx.AboutBox(info)
        