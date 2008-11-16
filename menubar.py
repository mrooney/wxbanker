# -*- coding: iso-8859-15 -*-
#
#    https://launchpad.net/wxbanker
#    menubar.py: Copyright 2007, 2008 Mike Rooney <michael@wxbanker.org>
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

import wx, webbrowser, os
from wx.lib.wordwrap import wordwrap
from wx.lib.pubsub import Publisher

import version, localization
from currencies import CurrencyStrings

class BankMenuBar(wx.MenuBar):
    ID_FAQ = wx.NewId()
    ID_QUESTION = wx.NewId()
    ID_REPORTBUG = wx.NewId()
    IDS_CURRENCIES = [wx.NewId() for i in range(len(CurrencyStrings))]
    
    def __init__(self, *args, **kwargs):
        wx.MenuBar.__init__(self, *args, **kwargs)
        
        settingsMenu = wx.Menu()
        
        ## TRANSLATORS: Put the ampersand (&) before the letter to use as the Alt shortcut.
        currencyMenu = wx.Menu() #(settingsMenu, self.ID_FAQ, _("&Currency"), _("Select currency to display"))
        currencyMenu.Bitmap = wx.ArtProvider.GetBitmap("wxART_money")
        settingsMenu.AppendMenu(wx.NewId(), "&Currency", currencyMenu)
        
        # Add an entry for each available currency.
        for i, cstr in enumerate(CurrencyStrings):
            item = wx.MenuItem(currencyMenu, self.IDS_CURRENCIES[i], cstr)
            currencyMenu.AppendItem(item)
        
        helpMenu = wx.Menu()
        
        ## TRANSLATORS: Put the ampersand (&) before the letter to use as the Alt shortcut.
        faqItem = wx.MenuItem(helpMenu, self.ID_FAQ, _("View &FAQs"), _("View Frequently Asked Questions online"))
        faqItem.Bitmap = wx.ArtProvider.GetBitmap("wxART_comments")
        helpMenu.AppendItem(faqItem)
        
        ## TRANSLATORS: Put the ampersand (&) before the letter to use as the Alt shortcut.
        questionItem = wx.MenuItem(helpMenu, self.ID_QUESTION, _("Ask a &Question"), _("Ask a question online"))
        questionItem.Bitmap = wx.ArtProvider.GetBitmap("wxART_user_comment")
        helpMenu.AppendItem(questionItem)
        
        ## TRANSLATORS: Put the ampersand (&) before the letter to use as the Alt shortcut.
        bugItem = wx.MenuItem(helpMenu, self.ID_REPORTBUG, _("&Report a Bug"), _("Report a bug to the developer online"))
        bugItem.Bitmap = wx.ArtProvider.GetBitmap("wxART_bug")
        helpMenu.AppendItem(bugItem)
        
        ## TRANSLATORS: Put the ampersand (&) before the letter to use as the Alt shortcut.
        aboutItem = helpMenu.Append(wx.ID_ABOUT, _("&About"), _("More information about wxBanker"))
        
        # Add everything to the main menu.
        self.Append(settingsMenu, _("&Settings"))
        self.Append(helpMenu, _("&Help"))
        
        self.Bind(wx.EVT_MENU, self.onClickAbout)
        helpMenu.Bind(wx.EVT_MENU, self.onClickAbout)
        
    def onMenuEvent(self, event):
        ID = event.Id
        
        if ID in self.IDS_CURRENCIES:
            self.onSelectCurrency(self.IDS_CURRENCIES.index(ID))
        else:
            handler = {
                self.ID_FAQ: self.onClickFAQs,
                self.ID_QUESTION: self.onClickAskQuestion,
                self.ID_REPORTBUG: self.onClickReportBug,
                wx.ID_ABOUT: self.onClickAbout,
            }[ID]
            
            handler(event)
            
    def onSelectCurrency(self, currencyIndex):
        Publisher().sendMessage("user.currency_changed", currencyIndex)
        
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
        info.Copyright = _("Copyright") + " 2007, 2008 Mike Rooney (michael@wxbanker.org)"
        info.Description = _("A lightweight personal finance management application.")
        info.WebSite = ("https://launchpad.net/wxbanker", "https://launchpad.net/wxbanker")

        info.Developers = [
            'Mike Rooney (michael@wxbanker.org)',
        ]
        info.Artists = [
            'Mark James (www.famfamfam.com/lab/icons/silk/)',
        ]
        translators = [
            'sl: Primož Jerše (jerse@inueni.com)',
            'es: Diego J. Romero López (diegojromerolopez@gmail.com)',
            'hi: Ankur Kachru (ankurkachru@gmail.com)',
        ]
        info.Translators = [unicode(s, 'iso-8859-15') for s in translators]
        
        licenseDir = os.path.dirname(__file__)
        info.License = open(os.path.join(licenseDir, 'gpl.txt')).read()

        wx.AboutBox(info)
        