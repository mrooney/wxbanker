import wx

class BankArtProvider(wx.ArtProvider):
    def __init__(self):
        wx.ArtProvider.__init__(self)
        from art import silk
        self.Catalog = silk.catalog

    def CreateBitmap(self, artid, client, size):
        bmp = self.Catalog[artid].GetBitmap()
        return bmp


class ArtFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Available Icons")
        panel = wx.Panel(self)
        self.Sizer = wx.BoxSizer()
        self.Sizer.Add(panel, 1, wx.EXPAND)

        bankArt = BankArtProvider()
        wx.ArtProvider.Push(bankArt)

        panel.Sizer = wx.FlexGridSizer(cols=40, vgap=2, hgap=2)
        iconNames = sorted(bankArt.Catalog.keys())
        self.SetIcon(wx.ArtProvider.GetIcon(iconNames[0]))
        for iconName in iconNames:
            bmp = wx.StaticBitmap(panel, bitmap=wx.ArtProvider.GetBitmap(iconName))
            bmp.SetToolTipString(iconName)
            panel.Sizer.Add(bmp)

        self.Layout()
        self.Fit()


def main():
    app = wx.App(False)
    frame = ArtFrame().Show()
    app.MainLoop()


if __name__ == "__main__":
    main()