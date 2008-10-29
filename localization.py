# Localization
import locale
locale.setlocale(locale.LC_ALL, '')

import os
APP = 'wxbanker'
DIR = os.path.join(os.path.dirname(__file__), 'locales')

import gettext
gettext.install(APP, DIR)
lang = gettext.translation(APP, DIR, languages=['sl'])
#lang.install()
