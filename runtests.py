#!/usr/bin/env python
#
#    https://launchpad.net/wxbanker
#    runtests.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

import doctest, wxbanker

def main():
    from testhelpers import displayhook
    import sys; sys.displayhook = displayhook

    import plotalgo, currencies, bankobjects, controller, currconvert
    mods = [plotalgo, currencies, bankobjects, controller, currconvert]

    #TODO: remove *.pyc first

    results = {}
    for mod in mods:
        result = doctest.testmod(mod)
        results[mod.__name__] = result

    import pprint
    print "(Failures, Total):"
    pprint.pprint(results)
    failures = sum([v[0] for v in results.values()])
    tests = sum([v[1] for v in results.values()])

    print "\n%i total failures out of %i total tests in %i modules." % (failures, tests, len(mods))
    if failures:
        print "TESTS FAILED."
    else:
        print "TESTS PASSED."

    from tests import alltests
    alltests.main()



if __name__ == "__main__":
    main()
