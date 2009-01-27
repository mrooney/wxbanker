#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    runtests.py: Copyright 2007-2009 Mike Rooney <michael@wxbanker.org>
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

def main():
    from testhelpers import displayhook
    import sys; sys.displayhook = displayhook
    
    import plotalgo, currencies, bankobjects, controller

    results = []
    for mod in [plotalgo, currencies, bankobjects, controller]:
        result = doctest.testmod(mod)
        results.append(result)

    import pprint
    print "(Successes, Failures):"
    pprint.pprint(results)

if __name__ == "__main__":
    main()
