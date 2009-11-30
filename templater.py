#!/usr/bin/env python
#    https://launchpad.net/wxbanker
#    templater.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

"""
Some strings are displayed dynamically, and so we need to "hard code"
the possibilities here so they get in the templates and translated.
"""
_ = lambda s: s
_("Hide Calculator")
_("Show Calculator")
_("Transact") # Keep this here for now, might want it.


def gentemplate(name="wxbanker.pot"):
    """Generate a .pot template with the given name."""
    translatableFiles = [f for f in os.listdir(".") if f.endswith(".py")]
    subprocess.check_call(["xgettext"] + translatableFiles + ["--output=po/%s"%name])

def compiletranslations():
    poFiles = [f for f in os.listdir("po/") if f.endswith(".po")]
    for poFile in poFiles:
        locale = poFile[:-3]
        path = "locale/%s/LC_MESSAGES/wxbanker.mo" % locale
        if not os.path.exists(path):
            os.makedirs(os.path.split(path)[0])
        try:
            subprocess.check_call(("msgfmt", "-cv", "po/%s"%poFile, "-o", path), stdout=subprocess.PIPE)
        except:
            print "FAILED: ", poFile
    subprocess.check_call(("bzr", "add", "locale/"))
        
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] =="--compile":
        compiletranslations()
    else:
        gentemplate()

