#    https://launchpad.net/wxbanker
#    urllib3.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

from cookielib import CookieJar, DefaultCookiePolicy
import urllib2, urllib

def enablecookies():
    cj = CookieJar( DefaultCookiePolicy(rfc2965=True) )
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    urllib2.install_opener(opener)

def read(url, postVars=None):
    try:
        con = urllib2.urlopen(url, postVars)
    except Exception:
        result = None
    else:
        result = con.read()

    return result

def post(url, varDict):
    return read(url, urllib.urlencode(varDict))
