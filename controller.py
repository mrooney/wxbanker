#    https://launchpad.net/wxbanker
#    controller.py: Copyright 2007, 2008 Mike Rooney <michael@wxbanker.org>
#
#    This file is part of wxBanker.
#
#    wxBanker is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    wxBanker is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with wxBanker.  If not, see <http://www.gnu.org/licenses/>.

from persistentstore import PersistentStore
import os, sys

class Controller(object):
    def __init__(self, path=None):
        if path is None:
            # Figure out where the bank database file is, and load it.
            #Note: look at wx.StandardPaths.Get().GetUserDataDir() in the future
            path = os.path.join(os.path.dirname(__file__), 'bank.db')
            if not '--use-local' in sys.argv and 'HOME' in os.environ:
                # We seem to be on a Unix environment.
                preferredPath = os.path.join(os.environ['HOME'], '.wxbanker', 'bank.db')
                if os.path.exists(preferredPath) or not os.path.exists(path):
                    path = preferredPath
                    # Ensure that the directory exists.
                    dirName = os.path.dirname(path)
                    if not os.path.exists(dirName):
                        os.mkdir(dirName)
        
        store = PersistentStore(path)
        self.Model = store.GetModel()