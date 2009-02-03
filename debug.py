import sys

def debug(*args):
    if "--debug" in sys.argv:
        for a in args:
            print a,
        print ""