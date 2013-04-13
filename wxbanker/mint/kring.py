#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    kring.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

import keyring

class Keyring(object):
    def __init__(self):
        self._name = "wxBanker Mint.com Credentials"
        self._sep = "////////"

    def get_credentials(self):
        creds = keyring.get_password(self._name, "wxbanker")
        if creds is None:
            return creds

        sep_pos = creds.find(self._sep)
        user, passwd = creds[:sep_pos], creds[sep_pos+len(self._sep):]
        return user, passwd

    def set_credentials(self, user, pw):
        # Ensure the arguments are simple strings; it can't handle unicode.
        user, pw = str(user), str(pw)
        
        if self.get_credentials() == (user, pw):
            return
        
        keyring.set_password(self._name, "wxbanker", "%s%s%s" % (user, self._sep, pw))
