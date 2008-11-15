Hello, and thanks for using wxBanker! If you have any questions,
comments, or suggestions, please don't hesitate to email me at
michael@wxbanker.org. If you find a bug, please file it at
https://bugs.launchpad.net/wxbanker.

== UPGRADING ==

If you are upgrading from a previous release, please see UPGRADING.txt
for simple instructions. It's easy, I promise!


== REQUIREMENTS ==
 - Python >= 2.5
 - wxPython >= 2.8
 * numpy >= 1.04 (completely optional; enables graphing capabilities)

See "INSTALLING" below for instructions on installing these
dependencies on your specific operating system.


== INSTALLING ==
 - Windows 2000/XP/Vista:
   - Download and install python from:
      http://www.python.org/ftp/python/2.5.2/python-2.5.2.msi
   - Download and install wxPython from:
      http://downloads.sourceforge.net/wxpython/wxPython2.8-win32-unicode-2.8.8.1-py25.exe
   - Optionally, for graphing capabilities, download and install
      numpy-1.1.0-win32-superpack-python2.5.exe from:
      http://sourceforge.net/project/showfiles.php?group_id=1369&package_id=175103

 - Ubuntu/Debian
   - sudo apt-get install python2.5 python-wxgtk2.8 python-numpy
 
 - Fedora
   - su -c 'yum install python wxPython numpy'

 - Mac OSX (PPC or Intel)
   - If you are using Leopard 10.5 or newer, you already have Python 2.5 installed.
     Otherwise, download and install python from:
      http://www.python.org/ftp/python/2.5.2/python-2.5.2-macosx.dmg
   - Download and install wxPython from:
      http://downloads.sourceforge.net/wxpython/wxPython2.8-osx-unicode-2.8.8.1-universal-py2.5.dmg
   - Optionally (10.5 only), for graphing capabilities, download and install
      numpy-1.1.0-py2.5-macosx10.5.dmg from:
      http://sourceforge.net/project/showfiles.php?group_id=1369&package_id=175103

Once you have installed Python, wxPython, and optionally numpy
using the instructions above, you are set. There is no need to
"install" wxBanker, it just runs from wherever it is located.

See the below section "RUNNING" for instructions on running wxBanker.


== RUNNING ==
Use python to run wxbanker.py wherever it is located. On Windows,
and usually elsewhere, this simply means double-clicking wxbanker.py.

Otherwise, at a terminal (assuming wxBanker is in your home directory):

Example: "python ~/wxBanker/wxbanker.py"

In many cases running wxbanker.py itself should work as well, as long as Python is installed as expected.

Example: "~/wxBanker/wxbanker.py"
