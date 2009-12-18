import wx
from wxbanker.plots import plotfactory

try:
    from enthought.chaco.api import Plot, ArrayPlotData
    from enthought.enable.wx_backend.api import Window as EnWindow
except ImportError:
    raise plotfactory.PlotLibraryImportException('chaco', 'python-chaco')

class ChacoPlotFactory(object):
    def createPanel(self, parent, bankController):
        return ChacoPlotPanel(parent)

class ChacoPlotPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.Sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.plot = Plot()
        win = EnWindow(self, component = self.plot)
        self.Sizer.Add(win.control, 1, wx.EXPAND)
        
    def plotBalance(self, totals, plotSettings):
        # quick hack to show something
        
        days = range(len(totals))
        data = [total[1] for total in totals]

        pd = ArrayPlotData(days=days, totals=data)
        
        self.plot.data = pd
        self.plot.plot(("days", "totals"), type="line")
