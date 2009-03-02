#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    wxbanker.py: Copyright 2007-2009 Mike Rooney <michael@wxbanker.org>
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
import localization
# Tabs
import managetab
try:
    import summarytab
except NoNumpyException:
    summarytab = None
    print _("Warning: Numpy module not available, disabling Summary tab. Install numpy to fix this.")


class BankerFrame(wx.Frame):
    def __init__(self, bankController):
        # Load our window settings.
        config = wx.Config.Get()
        size = config.ReadInt('SIZE_X'), config.ReadInt('SIZE_Y')
        pos = config.ReadInt('POS_X'), config.ReadInt('POS_Y')

        wx.Frame.__init__(self, None, title="wxBanker", size=size, pos=pos)
        self.SetIcon(wx.ArtProvider.GetIcon('wxART_coins'))

        self.notebook = notebook = wx.aui.AuiNotebook(self, style=wx.aui.AUI_NB_TOP)

        self.managePanel = managetab.ManagePanel(notebook, bankController)
        notebook.AddPage(self.managePanel, _("Transactions"))

        if summarytab:
            self.summaryPanel = summarytab.SummaryPanel(notebook, bankController)
            notebook.AddPage(self.summaryPanel, _("Summary"))

        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGING, self.onTabSwitching)

        Publisher().subscribe(self.onFirstRun, "FIRST RUN")

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOVE, self.OnMove)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        menuBar = BankMenuBar(bankController.AutoSave)
        self.SetMenuBar(menuBar)
        #self.CreateStatusBar()
        
        self.Bind(wx.EVT_MENU, menuBar.onMenuEvent)

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
        # If we are switching to the summary (graph) tab, update it!
        if tabIndex == 1:
            self.summaryPanel.update()

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


def init(path=None):
    import wx, os, sys
    from controller import Controller
    
    bankController = Controller(path)
    
    if '--cli' in sys.argv:
        import clibanker
        clibanker.main(bankController)
    else:
        app = wx.App(False)
        app.Controller = bankController
    
        # Push our custom art provider.
        import wx.lib.art.img2pyartprov as img2pyartprov
        from art import silk
        wx.ArtProvider.Push(img2pyartprov.Img2PyArtProvider(silk))
    
        # Initialize the wxBanker frame!
        frame = BankerFrame(bankController)
    
        # Greet the user if it appears this is their first time using wxBanker.
        firstTime = not wx.Config().ReadBool("RUN_BEFORE")
        if firstTime:
            Publisher().sendMessage("FIRST RUN")
            wx.Config().WriteBool("RUN_BEFORE", True)
    
        return app
    

def main():
    app = init()
    app.TopWindow.Show()
    
    import sys
    if '--inspect' in sys.argv:
        import wx.lib.inspection
        wx.lib.inspection.InspectionTool().Show()
    
    app.MainLoop()


if __name__ == "__main__":
    main()
