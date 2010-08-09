#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    fileservice.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
#    along with wxBanker.  If not, see <http://www.gnu.org/licenses/>.%

import os, sys
try:
    import xdg
    from xdg import BaseDirectory
except ImportError:
    xdg = None


def __getFilePath(filename, xdgListName):
    # Store files in the source directory unless we can do better.
    path = os.path.join(os.path.dirname(__file__), filename)
    if not "--use-local" in sys.argv:
        if xdg:
            base = getattr(BaseDirectory, xdgListName)[0]
            pathdir = os.path.join(base, "wxbanker")
        elif "HOME" in os.environ:
            # We don't have XDG but we are on Unix, perhaps OSX.
            pathdir = os.path.join(os.environ["HOME"], ".wxbanker")
        elif "APPDATA" in os.environ:
            # Windows!
            appdata = os.environ["APPDATA"]
            if type(appdata) != unicode:
                import locale
                appdata = unicode(appdata, locale.getlocale()[1])
            pathdir = os.path.join(appdata, "wxbanker")
        else:
            raise Exception("Unable to find a home for user data!")
        
        # Create the directory if it doesn't exist
        if not os.path.exists(pathdir):
            os.makedirs(pathdir) # mkdirs = mkdir -p, since ~/.config might not exist.
        path = os.path.join(pathdir, filename)
        
    return path

def getDataFilePath(filename):
    return __getFilePath(filename, xdgListName="xdg_data_dirs")
    
def getConfigFilePath(filename):
    return __getFilePath(filename, xdgListName="xdg_config_dirs")

def getSharedFilePath(*pathargs):
    paths = [
        # The COPYRIGHT.txt is one directory up in source.
        os.path.join(os.path.dirname(os.path.dirname(__file__))),
        os.path.join(os.path.dirname(__file__), "data"),
        "/usr/local/share/wxbanker",
        "/usr/share/wxbanker",
    ]
    
    for path in paths:
        potentialLocation = os.path.join(path, *pathargs)
        if os.path.exists(potentialLocation):
            return potentialLocation
        
    raise Exception("Unable to find shared data file '%s'. Looked in %s" % (pathargs, paths))

