import wx
import datetime
import plotfactory

try:
    from cairoplot import cairoplot, series
    import wx.lib.wxcairo
except ImportError:
    raise plotfactory.PlotLibraryImportException('cairo', 'pycairo')

class CairoPlotPanelFactory(object):
    def createPanel(self, parent, bankController):
        return CairoPlotPanel(parent)

class CairoPlotPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.data = None
        self.x_labels = None
        
    #def plotBalance(self, totals, startDate, every, xunits="Days", fitdegree=2):
    def plotBalance(self, totals, *args, **kwargs):
        # quick hack to show something
        self.data = {
            _("Balance") : [(i, total) for i, total in enumerate(totals)],
        }
        self.Update()
        
    def OnPaint(self, event):
        
        if self.data is None:
            return
        
        dc = wx.BufferedPaintDC(self)
        dc.Clear()
        
        cr = wx.lib.wxcairo.ContextFromDC(dc)
        size = self.GetClientSize()
        
        cairoplot.scatter_plot(
            cr.get_target(), data = self.data,
            width = size.width, height = size.height,
            border = 20, 
            axis = True,
            dots = 1,
            grid = True,
            series_colors = ["red"],
            series_legend = True
        )
                
