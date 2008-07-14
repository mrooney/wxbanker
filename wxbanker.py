#! /usr/bin/python
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

"""
A GUI layer on top of banker.py

#TODO: a summary tab for viewing graphs and stats like inflow, outflow, net cashflow, etc
#TODO: metadata info, such as FIXED, UNEXPECTED
"""
import wx, wx.aui, wx.lib.delayedresult as delayedresult
import time, os
from bankexceptions import NoNumpyException

#tabs
import managetab
summary = True
try:
    import summarytab
except NoNumpyException:
    summary = False
    print "Numpy not available, disabling Summary tab..."

from banker import Bank
import pubsub


class BankerFrame(wx.Frame):
    def __init__(self, bank):
        #load our window settings
        config = wx.Config.Get()
        size = config.ReadInt('SIZE_X'), config.ReadInt('SIZE_Y')
        pos = config.ReadInt('POS_X'), config.ReadInt('POS_Y')

        wx.Frame.__init__(self, None, title="wxBanker", size=size, pos=pos)
        self.isSaveLocked = False
        self.bank = bank

        self.notebook = notebook = wx.aui.AuiNotebook(self)

        self.managePanel = managetab.ManagePanel(notebook, self)
        notebook.AddPage(self.managePanel, "Transactions")

        if summary:
            self.summaryPanel = summarytab.SummaryPanel(notebook, self)
            notebook.AddPage(self.summaryPanel, "Summary")

        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGING, self.onTabSwitching)

        pubsub.Publisher().subscribe(self.onFirstRun, "FIRST RUN")

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        #self.Fit()
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

    def onFirstRun(self, message, data):
        welcomeMsg = "It looks like this is your first time using wxBanker!"
        welcomeMsg += " To\nget started, add an account using the account\ncontrol in the top left corner."
        welcomeMsg += "\n\nThe buttons in the account control allow you to add,\nremove, and rename an account, respectively."
        welcomeMsg += "\n\nOnce you have an account, you can add transactions\nto it (such as your initial balance) using the controls\nbelow the grid on the bottom right."
        welcomeMsg += "\n\nHave fun!"
        #wx.TipWindow(self, welcomeMsg, maxLength=300)
        dlg = wx.MessageDialog(self, welcomeMsg, "Welcome!", style=wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    '''
    def onMessage(self, message, data):
        saveWorthyMessages = [
            "FIRST RUN",
            "NEW ACCOUNT",
            "REMOVED ACCOUNT",
            "RENAMED ACCOUNT",
            "NEW TRANSACTION",
            "REMOVED TRANSACTION",
            "UPDATED TRANSACTION",
            ]

        if message in saveWorthyMessages:
            delayedresult.startWorker(self.saveConsumer, self.saveProducer, wargs=(message,))

    def saveProducer(self, message):
        #don't save if another save is pending
        while self.isSaveLocked:
            time.sleep(100)

        self.isSaveLocked = True
        print 'Saving as a result of: %s...'%message,
        self.bank.save()

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

    #initialize our configuration object
    wx.Config.Set(wx.Config("wxBanker"))
    config = wx.Config.Get()
    if not config.HasEntry("SIZE_X"):
        config.WriteInt("SIZE_X", 800)
        config.WriteInt("SIZE_Y", 600)
    if not config.HasEntry("POS_X"):
        config.WriteInt("POS_X", 100)
        config.WriteInt("POS_Y", 100)

    import sys
    root = os.path.split(sys.argv[0])[0]
    if root: #we may already be in the directory
        os.chdir(root)
    #bankPath = os.path.join(root, 'bank')
    bankPath = 'bank'

    bank = Bank(bankPath)
    frame = BankerFrame(bank)

    #greet the user if it appears this is their first time
    firstTime = not config.ReadBool("RUN_BEFORE")
    if firstTime:
        pubsub.Publisher().sendMessage("FIRST RUN")
        config.WriteBool("RUN_BEFORE", True)

    app.MainLoop()
