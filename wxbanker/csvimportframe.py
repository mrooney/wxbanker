#    https://launchpad.net/wxbanker
#    csvimportframe.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker.csvimporter import CsvImporter, CsvImporterProfileManager, json
from wxbanker.transactionolv import TransactionOLV

class CsvImportFrame(wx.Frame):
    """
    Window for importing data from a CSV file
    """
    def __init__(self):
        wx.Frame.__init__(self, None, title=_("CSV import"))
        # Necessary to be able to preview imports since OLV looks for this attribute on its GrandParent.
        self.searchActive = False

        self.dateFormats = ['%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']
        self.encodings = ['cp1250', 'iso8859-1', 'iso8859-2', 'utf-8']
        self.profileManager = CsvImporterProfileManager()
        self.transactionContainer = None

        topPanel = wx.Panel(self)
        topHorizontalSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.VERTICAL)

        horizontalSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(horizontalSizer, flag=wx.EXPAND)
        self.initSettingsControls(topPanel, horizontalSizer)
        self.initSettingsProfilesControl(topPanel, horizontalSizer)

        self.initFileAndActionControls(topPanel, topSizer)
        self.initTransactionCtrl(topPanel, topSizer)

        self.initTargetAccountControl(topPanel, topSizer)

        # set default values
        self.initCtrlValuesFromSettings(self.getDefaultSettings())

        # layout sizers
        topPanel.SetSizer(topSizer)
        topPanel.SetAutoLayout(True)
        topSizer.Fit(self)

        self.Show(True)

    def initTargetAccountControl(self, topPanel, topSizer):
        staticBox = wx.StaticBox(topPanel, label=_("Target account"))
        staticBoxSizer = wx.StaticBoxSizer(staticBox, wx.HORIZONTAL)
        topSizer.Add(staticBoxSizer, flag=wx.ALL|wx.EXPAND, border=1)

        try:
            bankModel = wx.GetApp().Controller.Model
            self.accountsDict = dict([(acc.GetName(), acc) for acc in bankModel.Accounts])
            accounts = self.accountsDict.keys()
        except:
            accounts = []

        self.targetAccountCtrl = wx.ComboBox(topPanel, style=wx.CB_READONLY, choices=accounts)
        self.targetAccountCtrl.Bind(wx.EVT_COMBOBOX, self.onTargetAccountChange)
        staticBoxSizer.Add(self.targetAccountCtrl)

        self.importButton = wx.Button(topPanel, label=_("Import"))
        self.importButton.Disable()
        self.importButton.SetToolTipString(_("Import"))
        self.importButton.Bind(wx.EVT_BUTTON, self.onClickImportButton)
        staticBoxSizer.Add(self.importButton, flag=wx.LEFT, border=5)

    def initSettingsControls(self, topPanel, parentSizer):
        # csv columns to wxBanker data mapping

        topSizer = wx.BoxSizer(wx.VERTICAL)
        parentSizer.Add(topSizer, flag=wx.EXPAND, proportion=1)

        staticBox = wx.StaticBox(topPanel, label=_("CSV columns mapping"))
        staticBoxSizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
        topSizer.Add(staticBoxSizer, flag=wx.ALL|wx.EXPAND, border=1)

        sizer = wx.FlexGridSizer(rows=3, cols=4, hgap=15, vgap=0)
        sizer.SetFlexibleDirection(wx.HORIZONTAL)
        staticBoxSizer.Add(sizer, flag=wx.ALL|wx.EXPAND, border=5)

        self.dateColumnCtrl = wx.SpinCtrl(topPanel, size=(40,-1))
        sizer.Add(wx.StaticText(topPanel, label=_('Date')), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.dateColumnCtrl, flag=wx.ALIGN_CENTER_VERTICAL)
        self.dateFormatCtrl = wx.ComboBox(topPanel, choices=self.dateFormats, size=(110,-1))
        sizer.Add(wx.StaticText(topPanel, label=_('Date format')), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.dateFormatCtrl, flag=wx.ALIGN_CENTER_VERTICAL)

        self.amountColumnCtrl = wx.SpinCtrl(topPanel, size=(40,-1))
        self.decimalSeparatorCtrl = wx.TextCtrl(topPanel, size=(20,-1))
        sizer.Add(wx.StaticText(topPanel, label=_('Amount')), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.amountColumnCtrl, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(wx.StaticText(topPanel, label=_('Decimal separator')), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.decimalSeparatorCtrl, flag=wx.ALIGN_CENTER_VERTICAL)

        self.descriptionColumnCtrl = wx.TextCtrl(topPanel)
        sizer.Add(wx.StaticText(topPanel, label=_('Description')), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.descriptionColumnCtrl, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add((0,0))
        sizer.Add((0,0))

        # csv file settings - delimiter, encoding, first line has headers - skipped

        staticBox = wx.StaticBox(topPanel, label=_("CSV file settings"))
        staticBoxSizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
        topSizer.Add(staticBoxSizer, flag=wx.ALL|wx.EXPAND, border=1)

        sizer = wx.FlexGridSizer(rows=3, cols=2, hgap=15, vgap=0)
        sizer.SetFlexibleDirection(wx.HORIZONTAL)
        staticBoxSizer.Add(sizer);

        self.linesToSkipCtrl = wx.SpinCtrl(topPanel, size=(40,-1))
        sizer.Add(wx.StaticText(topPanel, label=_('Lines to skip')), flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.linesToSkipCtrl, flag=wx.ALIGN_CENTER_VERTICAL)

        sizer.Add(wx.StaticText(topPanel, label=_('Encoding')), flag=wx.ALIGN_CENTER_VERTICAL)
        self.fileEncodingCtrl = wx.ComboBox(topPanel, choices=self.encodings, size=(110,-1))
        sizer.Add(self.fileEncodingCtrl, flag=wx.ALIGN_CENTER_VERTICAL)

        sizer.Add(wx.StaticText(topPanel, label=_('Column delimiter')), flag=wx.ALIGN_CENTER_VERTICAL)
        self.delimiterCtrl = wx.TextCtrl(topPanel, size=(30,-1))
        self.delimiterCtrl.SetMaxLength(1)
        sizer.Add(self.delimiterCtrl, flag=wx.ALIGN_CENTER_VERTICAL)

    def initFileAndActionControls(self, topPanel, topSizer):
        # file picker control and import button

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(sizer, flag=wx.EXPAND|wx.ALL, border=5)

        sizer.Add(wx.StaticText(topPanel, label=_('File to import')), flag=wx.ALIGN_CENTER_VERTICAL)
        self.filePickerCtrl = wx.FilePickerCtrl(topPanel)
        self.filePickerCtrl.Bind(wx.EVT_FILEPICKER_CHANGED, self.onFileChange)
        sizer.Add(self.filePickerCtrl, flag=wx.EXPAND|wx.LEFT|wx.RIGHT, proportion=2, border=10)

        self.previewButton = wx.Button(topPanel, label=_("Preview"))
        self.previewButton.Disable()
        self.previewButton.SetToolTipString(_("Preview"))
        self.previewButton.Bind(wx.EVT_BUTTON, self.onClickPreviewButton)
        sizer.Add(self.previewButton)

    def initTransactionCtrl(self, topPanel, topSizer):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(sizer, flag=wx.EXPAND|wx.ALL, proportion=1, border=5)

        self.transactionCtrl = DetachedTransactionOLV(topPanel, None)
        self.transactionCtrl.SetMinSize((-1, 200))
        sizer.Add(self.transactionCtrl, flag=wx.ALL|wx.EXPAND, proportion=1)

    def initSettingsProfilesControl(self, topPanel, topSizer):
        staticBox = wx.StaticBox(topPanel, label=_("CSV profiles"))
        sizer = wx.StaticBoxSizer(staticBox, wx.VERTICAL)
        topSizer.Add(sizer, flag=wx.ALL|wx.EXPAND)

        if not json:
            info = wx.StaticText(topPanel, label=_('Python simplejson library is needed for csv profile loading/saving.'),
                style=wx.ALIGN_CENTER)
            info.Wrap(80)
            sizer.Add(info, flag=wx.ALIGN_CENTER_VERTICAL)
            return

        self.profileCtrl = wx.ComboBox(topPanel, choices=self.profileManager.profiles.keys(), size=(110,-1))
        self.profileCtrl.Bind(wx.EVT_TEXT, self.onProfileCtrlChange)
        sizer.Add(self.profileCtrl, flag=wx.ALIGN_CENTER)

        self.loadProfileButton = wx.Button(topPanel, label=_("Load"))
        self.loadProfileButton.Bind(wx.EVT_BUTTON, self.onClickLoadProfileButton)
        self.loadProfileButton.Disable()
        sizer.Add(self.loadProfileButton, flag=wx.ALIGN_CENTER)

        self.saveProfileButton = wx.Button(topPanel, label=_("Save"))
        self.saveProfileButton.Bind(wx.EVT_BUTTON, self.onClickSaveProfileButton)
        self.saveProfileButton.Disable()
        sizer.Add(self.saveProfileButton, flag=wx.ALIGN_CENTER)

        self.deleteProfileButton = wx.Button(topPanel, label=_("Delete"))
        self.deleteProfileButton.Bind(wx.EVT_BUTTON, self.onClickDeleteProfileButton)
        self.deleteProfileButton.Disable()
        sizer.Add(self.deleteProfileButton, flag=wx.ALIGN_CENTER)

    def initCtrlValuesFromSettings(self, settings):
        self.amountColumnCtrl.Value = settings['amountColumn']
        self.decimalSeparatorCtrl.Value = settings['decimalSeparator']
        self.dateColumnCtrl.Value = settings['dateColumn']
        self.dateFormatCtrl.Value = settings['dateFormat']
        self.descriptionColumnCtrl.Value = settings['descriptionColumns']
        self.delimiterCtrl.Value = settings['delimiter']
        self.linesToSkipCtrl.Value = settings['linesToSkip']
        self.fileEncodingCtrl.Value = settings['encoding']

    def getDefaultSettings(self):
        settings = {}

        settings['amountColumn'] = 2
        settings['decimalSeparator'] = '.'
        settings['dateColumn'] = 1
        settings['dateFormat'] = self.dateFormats[0]
        settings['descriptionColumns'] = "3, 4 (5)"
        settings['delimiter'] = ';'
        settings['linesToSkip'] = 0
        settings['encoding'] = 'utf-8'

        return settings

    def getSettingsFromControls(self):
        settings = {}

        settings['amountColumn'] = self.amountColumnCtrl.Value
        settings['decimalSeparator'] = self.decimalSeparatorCtrl.Value
        settings['dateColumn'] = self.dateColumnCtrl.Value
        settings['dateFormat'] = self.dateFormatCtrl.Value
        settings['descriptionColumns'] = self.descriptionColumnCtrl.Value
        # delimiter must be 1-character string
        settings['delimiter'] = str(self.delimiterCtrl.Value)
        settings['linesToSkip'] = self.linesToSkipCtrl.Value
        settings['encoding'] = self.fileEncodingCtrl.Value

        return settings

    def runPreview(self):
        importer = CsvImporter()
        settings = self.getSettingsFromControls()

        file = self.filePickerCtrl.Path

        try:
            self.transactionContainer = importer.getTransactionsFromFile(file, settings)
            self.transactionCtrl.setAccount(self.transactionContainer)
        except UnicodeDecodeError,e:
            self.showErrorDialog(_("The file encoding does not seem to be '%s'.") % settings['encoding'], e)
        except Exception, e:
            self.showErrorDialog(exc=e)
        finally:
            self.toggleImportButton()

    def showErrorDialog(self, errDetail = '', exc = None):
        errString = _('An error ocurred during the csv file import.')
        errCaption = _('CSV import error')

        dlg = wx.MessageDialog(self, errString + '\n' + errDetail + '\n\n[%s]' % str(exc), errCaption, wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    def importTransactions(self):
        account = self.accountsDict[self.targetAccountCtrl.Value]
        account.AddTransactions(self.transactionContainer.Transactions)

    def toggleImportButton(self):
        self.importButton.Enable(self.targetAccountCtrl.Value != '' and self.transactionContainer is not None)

    def onFileChange(self, event):
        if self.filePickerCtrl.Path != '':
            self.previewButton.Enable()

    def onTargetAccountChange(self, event):
        self.toggleImportButton()

    def onProfileCtrlChange(self, event):
        if self.profileCtrl.Value != '':
            self.saveProfileButton.Enable()
            enabled = self.profileManager.getProfile(self.profileCtrl.Value) != None
            self.loadProfileButton.Enable(enabled)
            self.deleteProfileButton.Enable(enabled)
        else :
            self.loadProfileButton.Disable()
            self.saveProfileButton.Disable()
            self.deleteProfileButton.Disable()

    def onClickPreviewButton(self, event):
        self.runPreview()

    def onClickImportButton(self, event):
        self.importTransactions()

    def initProfileCtrl(self):
        self.profileCtrl.Items = self.profileManager.profiles.keys()
        self.onProfileCtrlChange(None)

    def onClickLoadProfileButton(self, event):
        key = self.profileCtrl.Value
        self.initCtrlValuesFromSettings(self.profileManager.getProfile(key))
        self.initProfileCtrl()

    def onClickSaveProfileButton(self, event):
        key = self.profileCtrl.Value
        if self.profileManager.profiles.has_key(key):
            d = wx.MessageDialog(self,
                    message=_("Profile with the name '%s' exists already. Overwrite it ?")%key,
                    caption=_('Overwrite profile ?'), style=wx.YES_NO)
            if d.ShowModal() != wx.ID_YES:
                return
        self.profileManager.saveProfile(key, self.getSettingsFromControls())
        self.initProfileCtrl()

    def onClickDeleteProfileButton(self, event):
        key = self.profileCtrl.Value
        self.profileManager.deleteProfile(key)
        self.initProfileCtrl()

class DetachedTransactionOLV(TransactionOLV):
    def __init__(self, *args, **kwargs):
        TransactionOLV.__init__(self, *args, **kwargs)
        self.SetEmptyListMsg(_('Select file and click "Preview"'))

    def renderFloat(self, floatVal):
        return floatVal

    def showContextMenu(self, transactions, col):
        TransactionOLV.showContextMenu(self, transactions, col, removeOnly=True)

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = CsvImportFrame()
    app.MainLoop()
