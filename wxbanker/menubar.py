# -*- coding: iso-8859-15 -*-
#
#    https://launchpad.net/wxbanker
#    menubar.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

from wxbanker import version, localization, debug, fileservice
from wxbanker.currencies import CurrencyStrings
from wxbanker.csvimportframe import CsvImportFrame

class BankMenuBar(wx.MenuBar):
    ID_AUTOSAVE = wx.NewId()
    ID_SHOWZERO = wx.NewId()
    ID_FAQ = wx.NewId()
    ID_QUESTION = wx.NewId()
    ID_REPORTBUG = wx.NewId()
    ID_REQUESTFEATURE = wx.NewId()
    ID_TRANSLATE = wx.NewId()
    IDS_CURRENCIES = [wx.NewId() for i in range(len(CurrencyStrings))]
    ID_REQUESTCURRENCY = wx.NewId()
    ID_IMPORT_CSV = wx.NewId()

    def __init__(self, bankController, *args, **kwargs):
        wx.MenuBar.__init__(self, *args, **kwargs)
        autosave = bankController.AutoSave
        showZero = bankController.ShowZeroBalanceAccounts

        # File menu.
        fileMenu = wx.Menu()
        self.saveMenuItem = fileMenu.Append(wx.ID_SAVE)
        self.autoSaveMenuItem = fileMenu.AppendCheckItem(self.ID_AUTOSAVE, _("Auto-save"), _("Automatically save changes"))
        fileMenu.AppendSeparator()
        importCsvMenu = fileMenu.Append(self.ID_IMPORT_CSV, _("Import from CSV"), _("Import transactions from a CSV file"))
        fileMenu.AppendSeparator()
        quitItem = fileMenu.Append(wx.ID_EXIT)
        
        # View menu.
        viewMenu = wx.Menu()
        viewMenu.AppendSeparator()
        self.showZeroMenuItem = viewMenu.AppendCheckItem(self.ID_SHOWZERO, _("Show zero-balance accounts"), _("When disabled, accounts with a balance of $0.00 will be hidden from the list"))
        
        # Use the initial show-zero setting.
        self.showZeroMenuItem.Check(showZero)

        # Settings menu.
        settingsMenu = wx.Menu()

        ## TRANSLATORS: Put the ampersand (&) before the letter to use as the Alt shortcut.
        currencyMenu = wx.MenuItem(settingsMenu, -1, _("&Currency"), _("Select currency to display"))
        currencyMenu.SetBitmap(wx.ArtProvider.GetBitmap("wxART_money"))

        currencies = wx.Menu()
        # Add an entry for each available currency.
        for i, cstr in enumerate(CurrencyStrings):
            item = wx.MenuItem(currencies, self.IDS_CURRENCIES[i], cstr)
            currencies.AppendItem(item)
        # Add an entry to request a new currency.
        requestCurrencyItem = wx.MenuItem(currencies, self.ID_REQUESTCURRENCY, _("Request a Currency"))
        requestCurrencyItem.Bitmap = wx.ArtProvider.GetBitmap("wxART_lightning")
        currencies.AppendItem(requestCurrencyItem)
        currencyMenu.SetSubMenu(currencies)

        settingsMenu.AppendItem(currencyMenu)

        # Help menu.
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
        featureItem = wx.MenuItem(helpMenu, self.ID_REQUESTFEATURE, _("Request a Fea&ture"), _("Request a new feature to be implemented"))
        featureItem.Bitmap = wx.ArtProvider.GetBitmap("wxART_lightbulb")
        helpMenu.AppendItem(featureItem)

        ## TRANSLATORS: Put the ampersand (&) before the letter to use as the Alt shortcut.
        translateItem = wx.MenuItem(helpMenu, self.ID_TRANSLATE, _("Tran&slate wxBanker"), _("Translate wxBanker to another language"))
        translateItem.Bitmap = wx.ArtProvider.GetBitmap("wxART_flag_blue")
        helpMenu.AppendItem(translateItem)

        helpMenu.AppendSeparator()

        ## TRANSLATORS: Put the ampersand (&) before the letter to use as the Alt shortcut.
        aboutItem = helpMenu.Append(wx.ID_ABOUT, _("&About"), _("More information about wxBanker"))

        # Add everything to the main menu.
        self.Append(fileMenu, _("&File"))
        self.Append(viewMenu, _("&View"))
        self.Append(settingsMenu, _("&Settings"))
        self.Append(helpMenu, _("&Help"))

        self.Bind(wx.EVT_MENU, self.onClickAbout)
        helpMenu.Bind(wx.EVT_MENU, self.onClickAbout)

        self.toggleAutoSave(autosave)
        Publisher.subscribe(self.onAutoSaveToggled, "controller.autosave_toggled")
        Publisher.subscribe(self.onShowZeroToggled, "controller.showzero_toggled")

    def onMenuEvent(self, event):
        ID = event.Id

        if ID in self.IDS_CURRENCIES:
            self.onSelectCurrency(self.IDS_CURRENCIES.index(ID))
        else:
            handler = {
                wx.ID_SAVE: self.onClickSave,
                self.ID_AUTOSAVE: self.onClickAutoSave,
                self.ID_SHOWZERO: self.onClickShowZero,
                wx.ID_EXIT: self.onClickQuit,
                self.ID_FAQ: self.onClickFAQs,
                self.ID_QUESTION: self.onClickAskQuestion,
                self.ID_REPORTBUG: self.onClickReportBug,
                self.ID_REQUESTFEATURE: self.onClickRequestFeature,
                self.ID_TRANSLATE: self.onClickTranslate,
                self.ID_IMPORT_CSV: self.onClickImportCsv,
                wx.ID_ABOUT: self.onClickAbout,
                self.ID_REQUESTCURRENCY: self.onClickRequestCurrency,
            }.get(ID, lambda e: e.Skip())

            handler(event)

    def onAutoSaveToggled(self, message):
        self.toggleAutoSave(message.data)
        
    def onShowZeroToggled(self, message):
        self.toggleShowZero(message.data)

    def toggleAutoSave(self, autosave):
        self.autoSaveMenuItem.Check(autosave)
        self.saveMenuItem.Enable(not autosave)
        
    def toggleShowZero(self, showzero):
        self.showZeroMenuItem.Check(showzero)

    def onClickSave(self, event):
        Publisher.sendMessage("user.saved")

    def onClickAutoSave(self, event):
        Publisher.sendMessage("user.autosave_toggled", event.Checked())
        
    def onClickShowZero(self, event):
        Publisher.sendMessage("user.showzero_toggled", event.Checked())
        
    def onClickQuit(self, event):
        Publisher.sendMessage("quit")

    def onSelectCurrency(self, currencyIndex):
        Publisher.sendMessage("user.currency_changed", currencyIndex)

    def onClickFAQs(self, event):
        webbrowser.open("https://answers.launchpad.net/wxbanker/+faqs")

    def onClickAskQuestion(self, event):
        webbrowser.open("https://launchpad.net/wxbanker/+addquestion")

    def onClickReportBug(self, event):
        webbrowser.open("https://launchpad.net/wxbanker/+filebug")

    def onClickRequestFeature(self, event):
        webbrowser.open("https://blueprints.launchpad.net/wxbanker")

    def onClickTranslate(self, event):
        webbrowser.open("https://translations.launchpad.net/wxbanker")

    def onClickRequestCurrency(self, event):
        webbrowser.open("https://answers.launchpad.net/wxbanker/+faq/477")

    def onClickAbout(self, event):
        info = wx.AboutDialogInfo()
        info.Name = "wxBanker"
        info.Version = str(version.NUMBER)
        info.Copyright = _("Copyright") + " 2007-2009 Mike Rooney (mrooney@ubuntu.com)"
        info.Description = _("A lightweight personal finance management application.")
        info.WebSite = ("https://launchpad.net/wxbanker", "https://launchpad.net/wxbanker")

        info.Developers = [
            'Mike Rooney (mrooney@ubuntu.com)',
            'Karel Kolman (kolmis@gmail.com)',
        ]
        info.Artists = [
            'Mark James (www.famfamfam.com/lab/icons/silk/)',
        ]
        translators = [
            "sl: Primož Jerše <jerse@inueni.com>",
            "es: Diego J. Romero López <diegojromerolopez@gmail.com>",
            "hi: Ankur Kachru <ankurkachru@gmail.com>",
            "pl: Tomasz 'Zen' Napierala <tomasz@napierala.org>",
            "fr: Steve Dodier <steve.dodier@gmail.com>",
            "de: Patrick Eigensatz <patrick.eigensatz@gmail.com>",
        ]
        info.Translators = [unicode(s, 'iso-8859-15') for s in translators]

        info.License = open(fileservice.getSharedFilePath("COPYING.txt")).read()

        wx.AboutBox(info)

    def onClickImportCsv(self, event):
        CsvImportFrame()
