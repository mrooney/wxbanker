#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    wxbanker.py: Copyright 2007, 2008 Mike Rooney <wxbanker@rowk.com>
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

import os

# wxPython
import wx, wx.aui
from wx.lib.pubsub import Publisher

# wxBanker
from bankexceptions import NoNumpyException
from menubar import BankMenuBar
from banker import Bank
import localization
# Tabs
import managetab
try:
    import summarytab
except NoNumpyException:
    summarytab = None
    print _("Warning: Numpy module not available, disabling Summary tab. Install numpy to fix this.")


class BankerFrame(wx.Frame):
    def __init__(self):
        # Load our window settings.
        config = wx.Config.Get()
        size = config.ReadInt('SIZE_X'), config.ReadInt('SIZE_Y')
        pos = config.ReadInt('POS_X'), config.ReadInt('POS_Y')

        wx.Frame.__init__(self, None, title="wxBanker", size=size, pos=pos)
        self.SetIcon(wx.ArtProvider.GetIcon('wxART_coins'))

        self.isSaveLocked = False

        self.notebook = notebook = wx.aui.AuiNotebook(self, style=wx.aui.AUI_NB_TOP)

        self.managePanel = managetab.ManagePanel(notebook)
        notebook.AddPage(self.managePanel, _("Transactions"))

        if summarytab:
            self.summaryPanel = summarytab.SummaryPanel(notebook)
            notebook.AddPage(self.summaryPanel, _("Summary"))

        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGING, self.onTabSwitching)

        Publisher().subscribe(self.onFirstRun, "FIRST RUN")

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        menuBar = BankMenuBar()
        self.SetMenuBar(menuBar)
        #self.CreateStatusBar()
        
        self.Bind(wx.EVT_MENU, menuBar.onMenuEvent)
        self.Show(True)

    def OnMove(self, event):
        config = wx.Config.Get()

        x, y = self.GetPosition()
        config.WriteInt("POS_X", x)
        config.WriteInt("POS_Y", y)

        event.Skip()

    def OnSize(self, event):
        config = wx.Config.Get()

        if not self.IsMaximized():
            x, y = self.GetSize()
            config.WriteInt('SIZE_X', x)
            config.WriteInt('SIZE_Y', y)

        config.WriteBool('IsMaximized', self.IsMaximized())
        event.Skip()

    def OnClose(self, event):
        event.Skip()

    def onTabSwitching(self, event):
        tabIndex = event.Selection
        if tabIndex == 1:
            self.summaryPanel.generateData()

    def onFirstRun(self, message):
        welcomeMsg = _("It looks like this is your first time using wxBanker!")
        welcomeMsg += "\n\n" + _("To get started, add an account using the account control in the top left corner.")
        welcomeMsg += " " + _("The buttons in the account control allow you to add, remove, and rename an account, respectively.")
        welcomeMsg += "\n\n" + _("Once you have created an account you can add transactions to it (such as your initial balance) using the controls below the grid on the bottom right.")
        welcomeMsg += "\n\n" + _("Have fun!")
        #wx.TipWindow(self, welcomeMsg, maxLength=300)
        dlg = wx.MessageDialog(self, welcomeMsg, _("Welcome!"), style=wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    '''
    def onMessage(self, message, data):
        saveWorthyMessages = [
            "FIRST RUN",
            "bank.NEW ACCOUNT",
            "bank.REMOVED ACCOUNT",
            "bank.RENAMED ACCOUNT",
            "bank.NEW TRANSACTION",
            "bank.REMOVED TRANSACTION",
            "bank.UPDATED TRANSACTION",
            ]

        if message in saveWorthyMessages:
            delayedresult.startWorker(self.saveConsumer, self.saveProducer, wargs=(message,))

    def saveProducer(self, message):
        #don't save if another save is pending
        while self.isSaveLocked:
            time.sleep(100)

        self.isSaveLocked = True
        print 'Saving as a result of: %s...'%message,
        Bank().save()

    def saveConsumer(self, delayedResult):
        try:
            result = delayedResult.get()
            print 'Success'
        except:
            print 'Failure'
            import traceback
            traceback.print_exc()

        #allow other threads to save
        self.isSaveLocked = False
    '''

if __name__ == "__main__":
    app = wx.App(False)

    # Initialize our configuration object.
    # It is only necessary to initialize any default values we
    # have which differ from the default values of the types,
    # so initializing an Int to 0 or a Bool to False is not needed.
    wx.Config.Set(wx.Config("wxBanker"))
    config = wx.Config.Get()
    if not config.HasEntry("SIZE_X"):
        config.WriteInt("SIZE_X", 800)
        config.WriteInt("SIZE_Y", 600)
    if not config.HasEntry("POS_X"):
        config.WriteInt("POS_X", 100)
        config.WriteInt("POS_Y", 100)
    if not config.HasEntry("SHOW_CALC"):
        config.WriteBool("SHOW_CALC", True)

    # Figure out where the bank database file is, and load it.
    root = os.path.dirname(__file__)
    bankPath = os.path.join(root, 'bank')
    bank = Bank(bankPath)

    # Push our custom art provider.
    import wx.lib.art.img2pyartprov as img2pyartprov
    from art import silk
    wx.ArtProvider.Push(img2pyartprov.Img2PyArtProvider(silk))

    # Initialize the wxBanker frame!
    frame = BankerFrame()

    # Greet the user if it appears this is their first time using wxBanker.
    firstTime = not config.ReadBool("RUN_BEFORE")
    if firstTime:
        Publisher().sendMessage("FIRST RUN")
        config.WriteBool("RUN_BEFORE", True)

    import sys
    if '--inspect' in sys.argv:
        import wx.lib.inspection
        wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()
