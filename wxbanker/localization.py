#    https://launchpad.net/wxbanker
#    localization.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

# Set the locale to the system default.
import locale, os, gettext, sys, wx
locale.setlocale(locale.LC_ALL, '')

# Define the domain and localedir.
APP = 'wxbanker'
# Figure out the directory...
if os.path.exists('/usr/share/locale/es/LC_MESSAGES/wxbanker.mo'):
    DIR = '/usr/share/locale'
elif os.path.exists('/usr/local/share/locale/es/LC_MESSAGES/wxbanker.mo'):
    DIR = '/usr/local/share/locale'
else:
    DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locale')

# Install gettext.
gettext.install(APP, DIR, unicode=True)
wxlang = wx.LANGUAGE_DEFAULT

# Check if the user forced a language with --lang=XX.
larg = '--lang='
for arg in sys.argv[1:]:
    if arg.startswith(larg):
        lang = arg[len(larg):]
        trans = gettext.translation(APP, DIR, languages=[lang])
        trans.install()

        # Attempt to localize wx with this language as well.
        if lang.lower().endswith(".utf8"):
            lang = lang[:-5] # Strip that off for wx.
        pylang = wx.Locale.FindLanguageInfo(lang)
        if pylang:
            wxlang = pylang.Language

        break

def initWxLocale():
    """
    Initialize the wxPython locale so stock strings are translated.
    Call this AFTER the wx.App is initialized to avoid crashes.
    """
    # Store it as a module variable so it doesn't go out of scope!
    global wxlocale
    wxlocale = wx.Locale(wxlang)
