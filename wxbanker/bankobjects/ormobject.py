#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    ormobject.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

from wx.lib.pubsub import Publisher

class ORMObject(object):
    ORM_TABLE = None
    ORM_ATTRIBUTES = []
    
    def __init__(self):
        self.IsFrozen = True
        # If the object doesn't have an ID, we need to set one for setattr.
        if not hasattr(self, "ID"):
            self.ID = None
        self.IsFrozen = False
        
    def __setattr__(self, attrname, val):
        object.__setattr__(self, attrname, val)
        if not self.IsFrozen and self.ID is not None:
            if attrname in self.ORM_ATTRIBUTES:
                classname = self.__class__.__name__
                Publisher.sendMessage("ormobject.updated.%s.%s" % (classname, attrname), self)
            
    def getAttrValue(self, attrname):
        from account import Account
        from transaction import Transaction
        
        value = getattr(self, attrname)
        if isinstance(value, (Account, Transaction)):
            value = value.ID
        elif attrname == "RepeatOn" and value is not None:
            value = ",".join([str(x) for x in value])
        elif attrname == "Date":
            value = "%s/%s/%s"%(self.Date.year, str(self.Date.month).zfill(2), str(self.Date.day).zfill(2))
        return value
            
    def toResult(self):
        result = [self.ID]
        for attr in self.ORM_ATTRIBUTES:
            result.append(self.getAttrValue(attr))
        return result
