#!/bin/sh

if [ $# -ne 3 ]
then
    echo "Compare .png files in two directories"
    echo "Usage: ./compare.sh path1 path2 diffdir"
    echo "Example: ./compare.sh . ../other ./diff"
    exit
fi

for dir in $1 $2
do
  for i in $dir/*.png
  do
    convert $i $i.tiff
  done
done

for i in `(cd $1; ls *.tiff)`
do
    perceptualdiff $1/$i $2/$i -output $3/$i.ppm
done
