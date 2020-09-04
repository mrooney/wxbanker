# -*- coding: iso-8859-15 -*-
#
#    https://launchpad.net/wxbanker
#    menubar.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker.lib.pubsub import Publisher

from wxbanker import version, localization, debug, fileservice, brandedframe
from wxbanker.currencies import CurrencyStrings
from wxbanker.csvimportframe import CsvImportFrame
from wxbanker.csvexporter import CsvExporter
from wxbanker.xmlexporter import XmlExporter
from wxbanker.xmlimporter import XmlImporter

class BankMenuBar(wx.MenuBar):
    ID_AUTOSAVE = wx.NewId()
    ID_VIEW_ALLACCOUNTS = wx.NewId()
    ID_VIEW_PREVACCOUNT = wx.NewId()
    ID_VIEW_NEXTACCOUNT = wx.NewId()
    ID_SHOWZERO = wx.NewId()
    ID_FAQ = wx.NewId()
    ID_QUESTION = wx.NewId()
    ID_REPORTBUG = wx.NewId()
    ID_REQUESTFEATURE = wx.NewId()
    ID_TRANSLATE = wx.NewId()
    IDS_CURRENCIES = [wx.NewId() for i in range(len(CurrencyStrings))]
    ID_SHOWCURRENCYNICK = wx.NewId()
    ID_MINTINTEGRATION = wx.NewId()
    ID_REQUESTCURRENCY = wx.NewId()
    ID_IMPORT_CSV = wx.NewId()
    ID_EXPORT_CSV = wx.NewId()
    ID_IMPORT_XML = wx.NewId()
    ID_EXPORT_XML = wx.NewId()

    def __init__(self, bankController, *args, **kwargs):
        wx.MenuBar.__init__(self, *args, **kwargs)
        self.bankController = bankController
        autosave = bankController.AutoSave
        showZero = bankController.ShowZeroBalanceAccounts
        showcurrnick = bankController.ShowCurrencyNick
        self.currencyStrings = CurrencyStrings[:]

        # File menu.
        fileMenu = wx.Menu()
        self.saveMenuItem = fileMenu.Append(wx.ID_SAVE)
        self.autoSaveMenuItem = fileMenu.AppendCheckItem(self.ID_AUTOSAVE, _("Auto-save"), _("Automatically save changes"))
        fileMenu.AppendSeparator()
        importCsvMenu = fileMenu.Append(self.ID_IMPORT_CSV, _("Import from CSV"), _("Import transactions from a CSV file"))
        exportCsvMenu = fileMenu.Append(self.ID_EXPORT_CSV, _("Export to CSV"), _("Export transactions to a CSV file"))
        importXmlMenu = fileMenu.Append(self.ID_IMPORT_XML, _("Import from XML"), _("Import transactions from a XML file"))
        exportXmlMenu = fileMenu.Append(self.ID_EXPORT_XML, _("Export to XML"), _("Export transactions to a XML file"))
        fileMenu.AppendSeparator()
        quitItem = fileMenu.Append(wx.ID_EXIT)
        
        # View menu.
        viewMenu = wx.Menu()
        viewMenu.Append(self.ID_VIEW_PREVACCOUNT, _("Previous account")+"\tCtrl+J")
        viewMenu.Append(self.ID_VIEW_NEXTACCOUNT, _("Next account")+"\tCtrl+K")
        viewMenu.Append(self.ID_VIEW_ALLACCOUNTS, _("All accounts")+"\tCtrl+T") 
        viewMenu.AppendSeparator()
        self.showZeroMenuItem = viewMenu.AppendCheckItem(self.ID_SHOWZERO, _("Show zero-balance accounts")+"\tCtrl+B", _("When disabled, accounts with a balance of $0.00 will be hidden from the list"))
        
        # Use the initial show-zero setting.
        self.showZeroMenuItem.Check(showZero)

        # Settings menu.
        settingsMenu = wx.Menu()

        ## TRANSLATORS: Put the ampersand (&) before the letter to use as the Alt shortcut.
        currencyMenu = wx.MenuItem(settingsMenu, -1, _("Base &currency"), _("Select currency for the 'All Accounts' balance"))
        currencyMenu.SetBitmap(wx.ArtProvider.GetBitmap("wxART_money"))

        # Add an entry for each available currency.
        currencies = wx.Menu()
        # Place the local detected one first, then the rest sorted.
        currencies.Append(self.IDS_CURRENCIES[0], self.currencyStrings[0])
        currencies.AppendSeparator()
        for i, cstr in enumerate(sorted(self.currencyStrings[1:])):
            idIndex = self.currencyStrings.index(cstr)
            item = wx.MenuItem(currencies, self.IDS_CURRENCIES[idIndex], cstr)
            currencies.AppendItem(item)
        # Add an entry to request a new currency.
        requestCurrencyItem = wx.MenuItem(currencies, self.ID_REQUESTCURRENCY, _("Request a Currency"))
        requestCurrencyItem.Bitmap = wx.ArtProvider.GetBitmap("wxART_lightning")
        currencies.AppendSeparator()
        currencies.AppendItem(requestCurrencyItem)
        currencyMenu.SetSubMenu(currencies)

        settingsMenu.AppendItem(currencyMenu)
        
        self.showCurrencyNickItem = settingsMenu.AppendCheckItem(self.ID_SHOWCURRENCYNICK, _("Show currency names"), _("Show currency names with amounts"))

        self.mintEnabledItem = settingsMenu.AppendCheckItem(self.ID_MINTINTEGRATION, _("Integrate with Mint.com"), _("Sync account balances with an existing Mint.com account"))

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

        self.toggleAutoSave(autosave)
        self.toggleShowCurrencyNick(showcurrnick)
        Publisher.subscribe(self.onAutoSaveToggled, "controller.autosave_toggled")
        Publisher.subscribe(self.onShowZeroToggled, "controller.showzero_toggled")
        Publisher.subscribe(self.onShowCurrencyNickToggled, "controller.show_currency_nick_toggled")
        # Subscribe to a Mint update event, which tells us the checkbox should be enabled after startup.
        Publisher.subscribe(self.onMintUpdate, "mint.updated")

    def onMenuEvent(self, event):
        ID = event.Id

        if ID in self.IDS_CURRENCIES:
            self.onSelectCurrency(self.IDS_CURRENCIES.index(ID))
        else:
            handler = {
                wx.ID_SAVE: self.onClickSave,
                self.ID_AUTOSAVE: self.onClickAutoSave,
                self.ID_VIEW_ALLACCOUNTS: self.onClickViewAll,
                self.ID_VIEW_PREVACCOUNT: self.onClickPrevAccount,
                self.ID_VIEW_NEXTACCOUNT: self.onClickNextAccount,
                self.ID_SHOWZERO: self.onClickShowZero,
                wx.ID_EXIT: self.onClickQuit,
                self.ID_FAQ: self.onClickFAQs,
                self.ID_QUESTION: self.onClickAskQuestion,
                self.ID_REPORTBUG: self.onClickReportBug,
                self.ID_REQUESTFEATURE: self.onClickRequestFeature,
                self.ID_TRANSLATE: self.onClickTranslate,
                self.ID_IMPORT_CSV: self.onClickImportCsv,
                self.ID_EXPORT_CSV: self.onClickExportCsv,
                self.ID_IMPORT_XML: self.onClickImportXml,
                self.ID_EXPORT_XML: self.onClickExportXml,
                wx.ID_ABOUT: self.onClickAbout,
                self.ID_REQUESTCURRENCY: self.onClickRequestCurrency,
                self.ID_SHOWCURRENCYNICK: self.onClickShowCurrencyNick,
                self.ID_MINTINTEGRATION: self.onClickMintIntegration,
            }.get(ID, lambda e: e.Skip())

            handler(event)
            
    def onMintUpdate(self, message):
        self.toggleMintEnabled(True)

    def onAutoSaveToggled(self, message):
        self.toggleAutoSave(message.data)
        
    def onShowZeroToggled(self, message):
        self.toggleShowZero(message.data)

    def toggleAutoSave(self, autosave):
        self.autoSaveMenuItem.Check(autosave)
        self.saveMenuItem.Enable(not autosave)
        
    def toggleShowZero(self, showzero):
        self.showZeroMenuItem.Check(showzero)

    def onShowCurrencyNickToggled(self, message):
        self.toggleShowCurrencyNick(message.data)

    def toggleShowCurrencyNick(self, showcurr):
        self.showCurrencyNickItem.Check(showcurr)
        
    def toggleMintEnabled(self, enabled):
        self.mintEnabledItem.Check(enabled)

    def onClickSave(self, event):
        Publisher.sendMessage("user.saved")

    def onClickAutoSave(self, event):
        Publisher.sendMessage("user.autosave_toggled", event.Checked())
        
    def onClickPrevAccount(self, event):
        Publisher.sendMessage("user.previous account")
        
    def onClickNextAccount(self, event):
        Publisher.sendMessage("user.next account")
        
    def onClickViewAll(self, event):
        Publisher.sendMessage("user.account changed", None)
        
    def onClickShowZero(self, event):
        Publisher.sendMessage("user.showzero_toggled", event.Checked())
        
    def onClickQuit(self, event):
        Publisher.sendMessage("quit")

    def onSelectCurrency(self, currencyIndex):
        Publisher.sendMessage("user.global_currency_changed", currencyIndex)

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
        
    def onClickShowCurrencyNick(self, event):
        Publisher.sendMessage("user.show_currency_nick_toggled", event.Checked())

    def onClickMintIntegration(self, event):
        Publisher.sendMessage("user.mint.toggled", event.Checked())

    def onClickAbout(self, event):
        info = wx.AboutDialogInfo()
        info.Name = "wxBanker"
        info.Version = str(version.NUMBER)
        #info.Icon = brandedframe.getIcon()
        info.Copyright = _("Copyright") + " 2007-2010 Mike Rooney (mrooney@ubuntu.com)"
        info.Description = _("Simple personal finance.")
        info.WebSite = ("https://launchpad.net/wxbanker", "https://launchpad.net/wxbanker")

        info.Developers = [
            'Mike Rooney (mrooney@ubuntu.com)',
            'Karel Kolman (kolmis@gmail.com)',
            'Evgenii Sopov (mrseakg@gmail.com)',
        ]
        info.Artists = [
            'Mark James (www.famfamfam.com/lab/icons/silk/)',
        ]
        translators = [
            "sl: Primo� Jer�e <jerse@inueni.com>",
            "es: Diego J. Romero L�pez <diegojromerolopez@gmail.com>",
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

    def onClickExportCsv(self, event):
        dlg = wx.FileDialog(None, style=wx.FD_SAVE, wildcard=_("CSV Files (*.csv)|*.csv"))
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            csvpath = dlg.GetPath()
            CsvExporter.Export(self.bankController.Model, csvpath)

    def onClickImportXml(self, event):
        dlg = wx.FileDialog(None, style=wx.FD_OPEN, message=_("Import from XML"), wildcard=_("XML Files (*.xml)|*.xml"))
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            xmlpath = dlg.GetPath()
            dlgConfirm = wx.MessageDialog(None, style=wx.YES_NO, caption=_("Attention"), message=_("Will be removed all current transactions. Are you agree?"))
            resultConfirm = dlgConfirm.ShowModal()
            if resultConfirm == wx.ID_YES:
                XmlImporter.Import(self.bankController.Model, xmlpath)

    def onClickExportXml(self, event):
        dlg = wx.FileDialog(None, style=wx.FD_SAVE, message=_("Export to XML"),wildcard=_("XML Files (*.xml)|*.xml"))
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            xmlpath = dlg.GetPath()
            if not os.path.isfile(xmlpath):
			    XmlExporter.Export(self.bankController.Model, xmlpath)
            else:
                msg = _("Are you sure that rewrite file?\n%(filename)s") % {'filename': xmlpath }
                dlgConfirm = wx.MessageDialog(None, style=wx.YES_NO, caption=_("File already exists"), message=msg)
                resultConfirm = dlgConfirm.ShowModal()
                if resultConfirm == wx.ID_YES:
                    XmlExporter.Export(self.bankController.Model, xmlpath)
