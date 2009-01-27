#!/usr/bin/env python
import doctest

def main():
    from testhelpers import displayhook
    import sys; sys.displayhook = displayhook
    
    import plotalgo, currencies, banker

    results = []
    for mod in [plotalgo, currencies, banker]:
        result = doctest.testmod(mod)
        results.append(result)

    import pprint
    print "(Successes, Failures):"
    pprint.pprint(results)

if __name__ == "__main__":
    main()
