#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    keyring.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

# The internet claims this is needed but, it doesn't seem to be?
#import gobject
#gobject.set_application_name("wxBanker")
import gnomekeyring as gkey

class Keyring(object):
    def __init__(self):
        self._name = "wxBanker Mint.com Credentials"
        self._server = "mint.com"
        self._type = gkey.ITEM_GENERIC_SECRET
        self._keyring = gkey.get_default_keyring_sync()

    def has_credentials(self):
        try:
            attrs = {"server": self._server}
            items = gkey.find_items_sync(self._type, attrs)
            return len(items) > 0
        except gkey.DeniedError:
            return False
        except gkey.NoMatchError:
            return False

    def get_credentials(self):
        attrs = {"server": self._server}
        items = gkey.find_items_sync(self._type, attrs)
        return (items[0].attributes["user"], items[0].secret)

    def set_credentials(self, user, pw):
        # Ensure the arguments are simple strings; it can't handle unicode.
        user, pw = str(user), str(pw)
        
        if self.has_credentials() and self.get_credentials() == (user, pw):
            return
        
        attrs = {"user": user, "server": self._server}
        gkey.item_create_sync(gkey.get_default_keyring_sync(), self._type, self._name, attrs, pw, True)
