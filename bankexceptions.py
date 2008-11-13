#    https://launchpad.net/wxbanker
#    bankexceptions.py: Copyright 2007, 2008 Mike Rooney <michael@wxbanker.org>
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

class NoNumpyException(Exception):
    pass

class InvalidAccountException(Exception):
    def __init__(self, account):
        self.account = account

    def __str__(self):
        return "Invalid account '%s' specified."%self.account

class AccountAlreadyExistsException(Exception):
    def __init__(self, account):
        self.account = account

    def __str__(self):
        return "Account '%s' already exists."%self.account

class InvalidTransactionException(Exception):
    def __init__(self, uid):
        self.uid = uid

    def __str__(self):
        return "Unable to find transaction with UID %s"%self.uid
