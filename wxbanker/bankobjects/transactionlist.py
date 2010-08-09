#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    transactionlist.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

class TransactionList(list):
    def __init__(self, items=None):
        # list does not understand items=None apparently.
        if items is None:
            items = []

        list.__init__(self, items)

    def __eq__(self, other):
        if not len(self) == len(other):
            return False
        for leftTrans, rightTrans in zip(self, other):
            if not leftTrans == rightTrans:
                return False

        return True