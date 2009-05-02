import os, sys

def __getFilePath(filename):
    # Figure out where the bank database file is, and load it.
    #Note: look at wx.StandardPaths.Get().GetUserDataDir() in the future
    path = os.path.join(os.path.dirname(__file__), filename)
    if not '--use-local' in sys.argv and 'HOME' in os.environ:
        # We seem to be on a Unix environment.
        preferredPath = os.path.join(os.environ['HOME'], '.wxbanker', filename)
        if os.path.exists(preferredPath) or not os.path.exists(path):
            path = preferredPath
            # Ensure that the directory exists.
            dirName = os.path.dirname(path)
            if not os.path.exists(dirName):
                os.mkdir(dirName)
    return path
    

def getDateFilePath(filename):
    return __getFilePath(filename)
    
def getConfigFilePath(filename):
    return __getFilePath(filename)

