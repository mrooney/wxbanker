#!/usr/bin/env python
#    https://launchpad.net/wxbanker
#    templater.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

import os, subprocess

def compiletranslations():
    poBase = "wxbanker/po/"
    poFiles = [f for f in os.listdir(poBase) if f.endswith(".po")]
    failed = []
    for poFile in poFiles:
        locale = poFile[:-3]
        path = "locale/%s/LC_MESSAGES/wxbanker.mo" % locale
        if not os.path.exists(path):
            os.makedirs(os.path.split(path)[0])
        try:
            subprocess.check_call(("msgfmt", "-v", poBase+poFile, "-o", path), stdout=subprocess.PIPE)
        except:
            failed.append(poFile)
    subprocess.check_call(("bzr", "add", "locale/"))
    print "Failed to compile: %s" % failed or None
        
if __name__ == "__main__":
    compiletranslations()
