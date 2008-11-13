#!/usr/bin/env python

from distutils.core import setup

setup(
    name = "wxBanker",
    description = "Lightweight personal finance manager",
    author = "Michael Rooney",
    author_email = "michael@wxbanker.org",
    url = "http://wxbanker.org",
    package_dir = {'wxbanker': ''},
    packages = ["wxbanker", "wxbanker.art"],
    requires = ["wx>=2.8",], ## correct?
    data_files = [
        ("locales", "locales/*"), ## probably not that easy?
        (desktopfileLocation, "wxbanker.desktop"), ##
        ("/usr/bin", "wxbanker"), ## usr/bin is right?
    ]

)
