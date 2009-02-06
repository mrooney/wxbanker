#!/usr/bin/env python
# Copyright 2009 Mike Rooney <mrooney@ubuntu.com>
#
# This work "as-is" we provide.
# No warranty, express or implied.
# We've done our best,
# to debug and test.
# Liability for damages denied.
#
# Permission is granted hereby,
# to copy, share, and modify.
# Use as is fit,
# free or for profit.
# On this notice these rights rely.

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
