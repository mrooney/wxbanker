#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    runtests.py: Copyright 2007-2010 Mike Rooney <mrooney@ubuntu.com>
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

import doctest
from wxbanker.tests import testbase
from wxbanker import controller
from wxbanker.testhelpers import displayhook
from wxbanker.tests import alltests

def main():
    import sys; sys.displayhook = displayhook
    # Run the legacy controller doctests and display the results.
    print "DOCTESTS:", doctest.testmod(controller)
    # Run all of the unit tests.
    alltests.main()
    
    incomplete = testbase.INCOMPLETE_TESTS
    if incomplete:
        print "Incomplete tests: %i!" % incomplete

if __name__ == "__main__":
    main()
