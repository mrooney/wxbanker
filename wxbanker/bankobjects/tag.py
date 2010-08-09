#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    tag.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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
from wxbanker import bankexceptions

class Tag(object):
    TAG_CHAR = "#"
    
    def __init__(self, name):
        self.Name = name
        
    def __str__(self):
        return "%s%s" % (self.TAG_CHAR, self.Name)
    
    def __eq__(self, other):
        return isinstance(other, Tag) and self.Name == other.Name
    
    def __cmp__(self, other):
        if not isinstance(other, Tag):
            return 1
        return cmp(self.Name, other.Name)
    
    def __hash__(self):
        return hash(self.Name)