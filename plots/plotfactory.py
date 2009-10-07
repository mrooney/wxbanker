import cairopanel
import summarytab

class PlotFactory(object):
    @staticmethod
    def getFactory(framework=None):
        if framework == 'cairo':
            return cairopanel.CairoPlotPanelFactory()
        elif framework == 'wx':
            return summarytab.WxPlotFactory()
        else:
            return None

