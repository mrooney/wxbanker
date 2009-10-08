class PlotFactory(object):
    factories = {
        'wx' : lambda : PlotFactory.__getWxFactory(),
        'cairo' : lambda : PlotFactory.__getCairoFactory(),
    }

    @classmethod
    def getFactory(cls, factoryName=None):
        """
        Get plot factory. Either the one specified in arguments
        or the first one createable.
        """
        if factoryName is not None:
            return cls.__createFactory(cls.factories[factoryName])
        else:
            # return first available factory
            for factory in cls.factories.itervalues():
                factory = cls.__createFactory(factory)
                if factory is not None:
                    return factory
    
    @classmethod
    def getAvailableFactories(cls):
        return cls.factories.keys()
        
    @classmethod
    def __createFactory(cls, method):
        """Execute factory creation method. Handle thrown exception exception."""
        try:
            return method()
        except PlotLibraryImportException as exc:
            print exc.getImportHint()
    
    @staticmethod
    def __getCairoFactory():
        import cairopanel
        return cairopanel.CairoPlotPanelFactory()
        
    @staticmethod
    def __getWxFactory():
        import wxplotpanel
        return wxplotpanel.WxPlotFactory()

class PlotLibraryImportException(Exception):
    def __init__(self, library, module):
        self.library = library
        self.module = module
    
    def getImportHint(self):
        return _("To use '%s' plotting library, install following python modules: %s."%(self.library, self.module))
        