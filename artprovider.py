import wx, os

class BankArtProvider(wx.ArtProvider):
    def __init__(self):
        wx.ArtProvider.__init__(self)
        from art import silk
        self.Catalog = silk.catalog

    def CreateBitmap(self, artid, client, size):
        bmp = self.Catalog[artid].GetBitmap()
        return bmp
    
    
class TestFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)
        
        wx.ArtProvider.Push(BankArtProvider())
        
        self.SetIcon(wx.ArtProvider.GetIcon('coins'))
        
        b = wx.BitmapButton(self)
        b.SetToolTipString("tool tip!")
        

def main():
    app = wx.App(False)
    frame = TestFrame().Show()
    app.MainLoop()
    

if __name__ == "__main__":
    main()