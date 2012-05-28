import wx
import datetime
from wxbanker.plots import plotfactory
from wx.lib.pubsub import Publisher

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
    def __init__(self, bankController, parent, plotSettings=None):
        wx.Panel.__init__(self, parent)
        baseplot.BasePlot.__init__(self)
        self.bankController = bankController
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.data = None
        self.x_labels = None
        self.plotSettings = plotSettings
        
        # watch if there's any currency change to repaint the plot.
        Publisher.subscribe(self.currencyChanged, "controller.show_currency_nick_toggled")
        Publisher.subscribe(self.currencyChanged, "currency_changed")
    
    def currencyChanged(self, message):
        self.Refresh()
        
    def OnSize(self, event):
        self.Refresh()
        
class CairoPlotPanelMonthly(BaseCairoPlotPanel):
    NAME = _("monthly")
    
    def plotBalance(self, totals, plotSettings):
        self.plotSettings = plotSettings
        model = self.bankController.Model
        transactions = model.GetTransactions()
        earnings = baseplot.BasePlot.plotMonthly(self, transactions, plotSettings['Months'])
        self.data, self.x_labels = [], []
        for month, amount in earnings:
            # Add the amount to the data.
            self.data.append([amount])
            # Generate the x_label representing the month.
            year, month = [int(x) for x in month.split(".")]
            x_label = datetime.date(year, month, 1).strftime("%b %Y")
            self.x_labels.append(x_label)
        self.Refresh()
        
    def OnPaint(self, event):
        # I'm not sure when this might happen, but I recall doing it for a reason. Perhaps OnPaint can occur without a plotBalance?
        if self.data is None:
            return
        
        dc = wx.BufferedPaintDC(self)
        dc.Clear()
        
        cr = wx.lib.wxcairo.ContextFromDC(dc)
        size = self.GetClientSize()
        
        # try to format Y axes labels according to the account's currency.
        if self.plotSettings['Account']:
            value_formatter = lambda s: self.plotSettings['Account'].float2str(s)
        else:
            value_formatter = lambda s: self.bankController.Model.float2str(s)
            
        cairoplot.vertical_bar_plot(
            cr.get_target(),
            data = self.data,
            width = size.width, height = size.height,
            border = 20, 
            grid = True,
            colors = ["green"],
            #series_legend = True,
            display_values = True,
            value_formatter = value_formatter,
            #x_title=_("Earnings"),
            #y_title=_("Month"),
            rounded_corners = True,
            x_labels = self.x_labels
        )
        
class CairoPlotPanel(BaseCairoPlotPanel):
    NAME = _("balance")
    
    def plotBalance(self, totals, plotSettings, xunits="Days"):
        self.plotSettings = plotSettings
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
        
         # try to format Y axes labels according to the account's currency.
        if self.plotSettings['Account']:
            y_formatter = lambda s: self.plotSettings['Account'].float2str(s)
        else:
            y_formatter = lambda s: self.bankController.Model.float2str(s)
        
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
            y_formatter=y_formatter,
            x_title=_("Time"),
            y_title=_("Balance"),
        )
