#    https://launchpad.net/wxbanker
#    pubsub.py: Copyright 2007, 2008 Mike Rooney <wxbanker@rowk.com>
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

class Publisher:
    subscribers = {"": []}

    def subscribe(self, callable, message=""):
        if self.subscribers.has_key(message):
            self.subscribers[message].append(callable)
        else:
            self.subscribers[message] = [callable]

    def sendMessage(self, message, data=None):
        specificSubs = self.subscribers.get(message, [])
        genericSubs = self.subscribers[""]
        #iterate over all the subscribers, but don't duplicate
        for subscriber in set(specificSubs + genericSubs):
            try:
                subscriber(message, data)
            except:
                import traceback
                traceback.print_exc()