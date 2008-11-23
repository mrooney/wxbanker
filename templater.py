#!/usr/bin/env python
#    https://launchpad.net/wxbanker
#    templater.py: Copyright 2007, 2008 Mike Rooney <michael@wxbanker.org>
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

"""
Some strings are displayed dynamically, and so we need to "hard code"
the possibilities here so they get in the templates and translated.
"""
_ = lambda s: s
_("Hide Calculator")
_("Show Calculator")

import commands

translatableFiles = [
    "wxbanker.py",
    "summarytab.py",
    "menubar.py",
    "managetab.py",
    "bankcontrols.py",
    "banker.py",
    "currencies.py",
    "localization.py",
    "version.py",
    "calculator.py",
    "templater.py",
]



def gentemplate(name="wxbanker.pot"):
    #run command, to `name`
    command = "xgettext %s" % " ".join(translatableFiles) + " --output=%s"%name
    print commands.getstatusoutput(command)

if __name__ == "__main__":
    gentemplate()
