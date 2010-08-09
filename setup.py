#!/usr/bin/env python
#    https://launchpad.net/wxbanker
#    setup.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

from distutils.core import setup
import os, glob
from wxbanker import version

#Create an array with all the locale filenames
I18NFILES = []
for filepath in glob.glob("locale/*/LC_MESSAGES/*.mo"):
    targetpath = os.path.dirname(os.path.join("share/", filepath))
    I18NFILES.append((targetpath, [filepath]))

setup(
    version = version.NUMBER,
    name = "wxBanker",
    description = "Simple personal finance.",
    author = "Michael Rooney",
    author_email = "mrooney@ubuntu.com",
    url = "https://launchpad.net/wxbanker",
    download_url='https://launchpad.net/wxbanker/+download',
    packages = ["wxbanker", "wxbanker.art", "wxbanker.bankobjects",
        "wxbanker.plots", "wxbanker.tests", "wxbanker.mint",
        "wxbanker.cairoplot", "wxbanker.ObjectListView"],
    license='GNU GPL',
    platforms='linux',
    scripts = ['bin/wxbanker'],
    data_files = [
        ("share/applications", ["bin/wxbanker.desktop"]),
        ('share/icons/hicolor/16x16/apps', ['images/16/wxbanker.png']),
        ('share/icons/hicolor/24x24/apps', ['images/24/wxbanker.png']),
        ('share/icons/hicolor/32x32/apps', ['images/32/wxbanker.png']),
        ('share/icons/hicolor/48x48/apps', ['images/48/wxbanker.png']),
        ('share/icons/hicolor/256x256/apps', ['images/256/wxbanker.png']),
        ('share/pixmaps', ['images/48/wxbanker.png']),
        ('share/wxbanker', glob.glob("*.txt")),
        ('share/wxbanker', glob.glob("wxbanker/data/*.*")),
        ('share/wxbanker/fixtures', glob.glob("wxbanker/data/fixtures/*.*")),
    ] + I18NFILES
)
