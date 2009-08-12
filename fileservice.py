#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    fileservice.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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
    if xdg and "--use-local" not in sys.argv:
        base = getattr(BaseDirectory, xdgListName)[0]
        pathdir = os.path.join(base, "wxbanker")
        path = os.path.join(pathdir, filename)
        # Create the directory if it doesn't exist
        if not os.path.exists(pathdir):
            os.mkdir(pathdir)
    else:
        path = os.path.join(os.path.dirname(__file__), filename)
    return path

def getDataFilePath(filename):
    return __getFilePath(filename, xdgListName="xdg_data_dirs")
    
def getConfigFilePath(filename):
    return __getFilePath(filename, xdgListName="xdg_config_dirs")
