import wx
import datetime
from wxbanker.plots import plotfactory
from wxbanker.summarytab import SummaryHelper

try:
    from wxbanker.cairoplot import cairoplot, series
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
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.data = None
        self.x_labels = None
        
    def plotBalance(self, totals, plotSettings, xunits="Days", fitdegree=2):
        totals, startDate, every = SummaryHelper().getPoints(totals, plotSettings['Granularity'])
        
        self.startDate = startDate
        timeDelta = datetime.timedelta( every * {'Days':1, 'Weeks':7, 'Months':30, 'Years':365}[xunits] )
        pointDates = []

        data = []
        currentTime = 0
        uniquePoints = set()
        for i, total in enumerate(totals):
            data.append((currentTime, total))
            uniquePoints.add("%.2f"%total)
            currentTime += every

            # Don't just += the timeDelta to currentDate, since adding days is all or nothing, ie:
            #   currentDate + timeDelta == currentDate, where timeDelta < 1 (bad!)
            # ...so the date will never advance for timeDeltas < 1, no matter how many adds you do.
            # As such we must start fresh each time and multiply the time delta appropriately.
            currentDate = startDate + (i+1)*timeDelta

            pointDates.append(currentDate.strftime('%Y/%m/%d'))
            
        self.data = {
            _("Balance") : [(i, total) for i, total in enumerate(totals)],
        }
        # The maximum number of X labels (dates) we want to show.
        
        num_dates = 10
        if len(totals) <= num_dates+1:
            labels = pointDates
        else:
            labels = []
            delta = 1.0 * (len(totals)-1) / (num_dates)
            for i in range(num_dates+1):
                labels.append(pointDates[int(i*delta)])
        
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
            series_colors = ["green"],
            series_legend = True,
            x_labels=self.x_labels,
        )

