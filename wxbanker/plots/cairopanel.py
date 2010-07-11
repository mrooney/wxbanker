import wx
import datetime
from wxbanker.plots import plotfactory

try:
    try:
        from wxbanker.plots import baseplot
    except plotfactory.BasePlotImportException:
        raise plotfactory.PlotLibraryImportException('cairo', 'python-numpy')
    from wxbanker.cairoplot import cairoplot, series
    import wx.lib.wxcairo
except ImportError:
    raise plotfactory.PlotLibraryImportException('cairo', 'pycairo')

class CairoPlotPanelFactory(baseplot.BaseFactory):
    def __init__(self):
        self.Plots = [CairoPlotPanel, CairoPlotPanelMonthly]
    
class BaseCairoPlotPanel(wx.Panel, baseplot.BasePlot):
    def __init__(self, bankController, parent):
        wx.Panel.__init__(self, parent)
        baseplot.BasePlot.__init__(self)
        self.bankController = bankController
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.data = None
        self.x_labels = None
        
    def OnSize(self, event):
        self.Refresh()
        
class CairoPlotPanelMonthly(BaseCairoPlotPanel):
    NAME = _("monthly")
    
    def plotBalance(self, totals, plotSettings):
        model = self.bankController.Model
        transactions = model.GetTransactions()
        earnings = baseplot.BasePlot.plotMonthly(self, transactions)
        self.data = [[e] for e in earnings]
        self.x_labels = [model.float2str(e) for e in earnings]
        
    def OnPaint(self, event):
        if self.data is None:
            return
        
        dc = wx.BufferedPaintDC(self)
        dc.Clear()
        
        cr = wx.lib.wxcairo.ContextFromDC(dc)
        size = self.GetClientSize()
        cairoplot.vertical_bar_plot(
            cr.get_target(),
            data = self.data,
            width = size.width, height = size.height,
            border = 20, 
            #axis = True,
            #dots = 0,
            grid = True,
            colors = ["green"],
            #series_legend = True,
            display_values = True,
            ##y_formatter=lambda s: self.bankController.Model.float2str(s),
            #x_title=_("Earnings"),
            #y_title=_("Month"),
            rounded_corners = True,
            x_labels = self.x_labels
        )
        
class CairoPlotPanel(BaseCairoPlotPanel):
    NAME = _("balance")
    
    def plotBalance(self, totals, plotSettings, xunits="Days"):
        amounts, dates, strdates, trendable = baseplot.BasePlot.plotBalance(self, totals, plotSettings, xunits)
        data = [(i, total) for i, total in enumerate(amounts)]
        self.data = {
            _("Balance") : data,
        }
        if trendable:
            fitdata = self.getPolyData(data, N=plotSettings["FitDegree"])
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
        
    def OnPaint(self, event):
        if self.data is None:
            return
        
        dc = wx.BufferedPaintDC(self)
        dc.Clear()
        
        cr = wx.lib.wxcairo.ContextFromDC(dc)
        size = self.GetClientSize()
        cairoplot.scatter_plot(
            cr.get_target(),
            data = self.data,
            width = size.width, height = size.height,
            border = 20, 
            axis = True,
            dots = 0,
            grid = True,
            series_colors = ["green", "blue"],
            series_legend = True,
            x_labels=self.x_labels,
            y_formatter=lambda s: self.bankController.Model.float2str(s),
            x_title=_("Time"),
            y_title=_("Balance"),
        )
