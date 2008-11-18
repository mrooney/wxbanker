#!/usr/bin/env python

from distutils.core import setup
import os, glob
import version

#Create an array with all the locale filenames
I18NFILES = []
for filepath in glob.glob("locales/*/LC_MESSAGES/*.mo"):
    targetpath = os.path.dirname(os.path.join("share/", filepath))
    I18NFILES.append((targetpath, [filepath]))

setup(
    version = version.NUMBER,
    name = "wxBanker",
    description = "Lightweight personal finance manager",
    author = "Michael Rooney",
    author_email = "michael@wxbanker.org",
    url = "http://wxbanker.org",
    download_url='https://launchpad.net/wxbanker/+download',
    package_dir = {'wxbanker': ''},
    packages = ["wxbanker", "wxbanker.art"],
    requires = ["wx (>=2.8)"],
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
    ] + I18NFILES

)
