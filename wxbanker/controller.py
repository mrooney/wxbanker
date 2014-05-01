# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    controller.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

from wxbanker.persistentstore import PersistentStore
import wx, os
from wxbanker.lib.pubsub import Publisher
from wxbanker import debug, fileservice

class Controller(object):
    CONFIG_NAME = "wxBanker.cfg"
    DB_NAME = "bank.db"
    
    def __init__(self, path=None):
        self._AutoSave = True
        self._ShowZeroBalanceAccounts = True
        self._ShowCurrencyNick = True
        self.Models = []
        
        self.InitConfig()
        self.LoadPath(path, use=True)

        Publisher.subscribe(self.onAutoSaveToggled, "user.autosave_toggled")
        Publisher.subscribe(self.onShowZeroToggled, "user.showzero_toggled")
        Publisher.subscribe(self.onShowCurrencyNickToggled, "user.show_currency_nick_toggled")
        Publisher.subscribe(self.onSaveRequest, "user.saved")
        
    def MigrateIfFound(self, fromPath, toPath):
        """Migrate a file from fromPath (if it exists) to toPath."""
        if os.path.exists(fromPath):
            import shutil
            try:
                shutil.move(fromPath, toPath)
            except IOError:
                debug.debug("Unable to move %s to %s, attempting a copy instead..." % (fromPath, toPath))
                shutil.copyfile(fromPath, toPath)
            return True

    def InitConfig(self):
        """Initialize our configuration object."""
        # It is only necessary to initialize any default values we
        # have which differ from the default values of the types,
        # so initializing an Int to 0 or a Bool to False is not needed.
        self.wxApp = wx.App(False)
        self.wxApp.SetAppName("wxBanker")
        self.wxApp.Controller = self
        configPath = fileservice.getConfigFilePath(self.CONFIG_NAME)

        # If we support XDG and the config file doesn't exist, it might be time to migrate.
        if fileservice.xdg and not os.path.exists(configPath):
            # If we can find the files at the old locations, we should migrate them.
            oldConfigPath = os.path.expanduser("~/.wxBanker")
            oldBankPath = os.path.expanduser("~/.wxbanker/bank.db")
            self.MigrateIfFound(oldConfigPath, fileservice.getConfigFilePath(self.CONFIG_NAME))
            self.MigrateIfFound(oldBankPath, fileservice.getDataFilePath(self.DB_NAME))
            
        # Okay, now our files are in happy locations, let's go!
        config = wx.FileConfig(localFilename=configPath)
        wx.Config.Set(config)
        if not config.HasEntry("SIZE_X"):
            config.WriteInt("SIZE_X", 960)
            config.WriteInt("SIZE_Y", 720)
        if not config.HasEntry("POS_X"):
            config.WriteInt("POS_X", 100)
            config.WriteInt("POS_Y", 100)
        if not config.HasEntry("SHOW_CALC"):
            config.WriteBool("SHOW_CALC", False)
        if not config.HasEntry("AUTO-SAVE"):
            config.WriteBool("AUTO-SAVE", True)
        if not config.HasEntry("HIDE_ZERO_BALANCE_ACCOUNTS"):
            config.WriteBool("HIDE_ZERO_BALANCE_ACCOUNTS", False)
        if not config.HasEntry("SHOW_CURRENCY_NICK"):
            config.WriteBool("SHOW_CURRENCY_NICK", False)

        # Set the auto-save option as appropriate.
        self.AutoSave = config.ReadBool("AUTO-SAVE")
        self.ShowZeroBalanceAccounts = not config.ReadBool("HIDE_ZERO_BALANCE_ACCOUNTS")
        self.ShowCurrencyNick = config.ReadBool("SHOW_CURRENCY_NICK")

    def onAutoSaveToggled(self, message):
        val = message.data
        self.AutoSave = val
        
    def onShowZeroToggled(self, message):
        val = message.data
        self.ShowZeroBalanceAccounts = val

    def onShowCurrencyNickToggled(self, message):
        val = message.data
        self.ShowCurrencyNick = val
        
    def onSaveRequest(self, message):
        self.Model.Save()

    def GetAutoSave(self):
        return self._AutoSave

    def SetAutoSave(self, val):
        self._AutoSave = val
        wx.Config.Get().WriteBool("AUTO-SAVE", val)
        Publisher.sendMessage("controller.autosave_toggled", val)
        for model in self.Models:
            debug.debug("Setting auto-save to: %s" % val)
            model.Store.AutoSave = val

        # If the user enables auto-save, we want to also save.
        if self.AutoSave:
            Publisher.sendMessage("user.saved")
            
    def GetShowZero(self):
        return self._ShowZeroBalanceAccounts
    
    def SetShowZero(self, val):
        self._ShowZeroBalanceAccounts = val
        wx.Config.Get().WriteBool("HIDE_ZERO_BALANCE_ACCOUNTS", not val)
        Publisher.sendMessage("controller.showzero_toggled", val)

    def GetShowCurrencyNick(self):
        return self._ShowCurrencyNick
    
    def SetShowCurrencyNick(self, val):
        self._ShowCurrencyNick = val
        wx.Config.Get().WriteBool("SHOW_CURRENCY_NICK", val)
        Publisher.sendMessage("controller.show_currency_nick_toggled", val)

    def LoadPath(self, path, use=False):
        if path is None:
            path = fileservice.getDataFilePath(self.DB_NAME)

        store = PersistentStore(path)
        store.AutoSave = self.AutoSave
        model = store.GetModel()

        self.Models.append(model)
        if use:
            self.Model = model

        return model

    def Close(self, model=None):
        if model is None: models = self.Models[:]
        else: models = [model]

        for model in models:
            # We can't use in here, since we need the is operator, not ==
            if not any((m is model for m in self.Models)):
                raise Exception("model not managed by this controller")

            model.Store.Close()
            # Again we can't use remove, different models can be ==
            for i, m in enumerate(self.Models):
                if m is model:
                    self.Models.pop(i)
                    break

    AutoSave = property(GetAutoSave, SetAutoSave)
    ShowZeroBalanceAccounts = property(GetShowZero, SetShowZero)
    ShowCurrencyNick = property(GetShowCurrencyNick, SetShowCurrencyNick)
