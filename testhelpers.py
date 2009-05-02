#    https://launchpad.net/wxbanker
#    testhelpers.py: Copyright 2007, 2008 Mike Rooney <mrooney@ubuntu.com>
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

def displayhook(value):
    """
    Override the default sys.displayhook so
    _ doesn't get stomped over, which gettext needs.
    """
    if value is not None:
        print repr(value)

class Subscriber(list):
    """
    This class subscribes to all pubsub messages.
    It is used by the unit tests to ensure proper
    underlying messaging exists.
    """
    def __init__(self):
        list.__init__(self)
        Publisher().subscribe(self.onMessage)

    def onMessage(self, message):
        self.insert(0, (message.topic, message.data))
