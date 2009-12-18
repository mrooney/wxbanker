#!/usr/bin/env python
'''Cairoplot installation script.'''

from distutils.core import setup
import os

setup(
    description='Cairoplot',
    license='GNU LGPL 2.1',
    long_description='''
        Using Python and PyCairo to develop a module to plot graphics in an
        easy and intuitive way, creating beautiful results for presentations.
        ''',
    name='Cairoplot',
    py_modules=['cairoplot','series'],
    url='http://linil.wordpress.com/2008/09/16/cairoplot-11/',
    version='1.1',
    )

