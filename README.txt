Hello, and thanks for using wxBanker! If you have any questions,
comments, or suggestions, please don't hesitate to email me at
mrooney@ubuntu.com. If you find a bug, please file it at
https://bugs.launchpad.net/wxbanker.

== UPGRADING ==

If you are upgrading from wxBanker 0.4 or later, there
is nothing special that you need to do. If you are upgrading
from a release of wxBanker 0.3 OR EARLIER, please see UPGRADING.txt
for simple instructions. It's easy, I promise!


== REQUIREMENTS ==
 - Python >= 2.5
 - wxPython >= 2.8.8.0

== INSTALLING ==
 - Ubuntu
   - sudo apt-get install wxbanker
 - Fedora
   - su -c 'yum install wxPython'
   - sudo easy_install pip && pip install -r pip_requirements.txt
   - sudo python setup.py install (optional, creates binary and shortcut)
 - Mac OSX (PPC or Intel)
   - install wxPython (cocoa, not carbon): http://wxpython.org/download.php
   - sudo easy_install pip && pip install -r pip_requirements.txt
 - Windows 2000/XP/Vista/7:
   - install python: http://python.org/download/
   - install wxPython (unicode) from: http://www.wxpython.org/download.php
   - install setuptools: http://pypi.python.org/pypi/setuptools
   - c:\Python2x\Scripts\easy_install pip (replace Python2x with your version)
   - c:\Python2x\Scripts\pip install -r pip_requirements.txt
      
== RUNNING ==
Use python to run main.py wherever it is located. On Windows,
and usually elsewhere, this simply means double-clicking main.py.

Otherwise, at a terminal (assuming wxBanker is in your home directory):
 - python ~/wxBanker/main.py
