#!/bin/sh
DIRNAME=`dirname $0`
(cd $DIRNAME/..; python -m timeit -n 1 -v "import seriestests")
