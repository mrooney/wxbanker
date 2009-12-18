import wx
import datetime
from wxbanker.plots import plotfactory, baseplot

try:
    from wxbanker.cairoplot import cairoplot, series
    import wx.lib.wxcairo
except ImportError:
    raise plotfactory.PlotLibraryImportException('cairo', 'pycairo')

class CairoPlotPanelFactory(object):
    def createPanel(self, parent, bankController):
        return CairoPlotPanel(parent)

class CairoPlotPanel(wx.Panel, baseplot.BasePlot):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        baseplot.BasePlot.__init__(self)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.data = None
        self.x_labels = None
        
    def plotBalance(self, totals, plotSettings, xunits="Days", fitdegree=2):
        amounts, dates, strdates, trendable = baseplot.BasePlot.plotBalance(self, totals, plotSettings, xunits, fitdegree)
            
        data = [(i, total) for i, total in enumerate(amounts)]
        self.data = {
            _("Balance") : data,
        }
        
        if trendable:
            fitdata = self.getPolyData(data, N=fitdegree)
            self.data[_("Trend")] = fitdata
        
        # The maximum number of X labels (dates) we want to show.        
        num_dates = 10
        if len(amounts) <= num_dates+1:
            labels = strdates
        else:
            labels = []
            delta = 1.0 * (len(amounts)-1) / (num_dates)
            for i in range(num_dates+1):
                labels.append(strdates[int(i*delta)])
        
        self.x_labels = labels
        self.Refresh()
    
    def OnSize(self, event):
        self.Refresh()
        
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
            series_colors = ["green", "blue"],
            series_legend = True,
            x_labels=self.x_labels,
            x_title=_("Time"),
            y_title=_("Balance"),
        )

