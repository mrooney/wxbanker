from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from functools import partial
from StringIO import StringIO
import os.path
import pstats
import sys
import re
import threading
import traceback
import time
import urlparse
import webbrowser

PORT = 4040

def htmlquote(fn):
    return fn.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def shrink(s):
    if len(s) < 40:
        return s
    return s[:20] + '...' + s[-20:]

def formatfunc(func):
    file, line, func_name = func
    return '%s:%s:%s' % (os.path.basename(file), line, htmlquote(shrink(func_name)))

def formatTime(dt):
    return '%.2fs' % dt

def formatTimeAndPercent(dt, total):
    percent = "(%.1f%%)" % (100.0 * dt / total)
    if percent == '(0.0%)':
        percent = ''
    return '%s&nbsp;<font color=#808080>%s</a>' % (formatTime(dt), percent)

def wrapTag(tag, body):
    return '<%s>%s</%s>' % (tag, body, tag)

class MyHandler(BaseHTTPRequestHandler):
    def __init__(self, stats=None, *args, **kw):
        self.stats = stats
        self.stats.stream = StringIO()
        self.stats.calc_callees()
        self.total_time = self.stats.total_tt
        (self.filename,) = self.stats.files
        self.width, self.print_list = self.stats.get_print_list(())

        self.func_to_id = {}
        self.id_to_func = {}

        i = 0
        for func in self.print_list:
            self.id_to_func[i] = func
            self.func_to_id[func] = i
            i += 1

        BaseHTTPRequestHandler.__init__(self, *args, **kw)

    def do_GET(self):
        path, query = urlparse.urlsplit(self.path)[2:4]
        self.query = {}
        for elt in query.split(';'):
            if not elt:
                continue
            key, value = elt.split('=', 1)
            self.query[key] = value
        
        for methodName in dir(self):
            method = getattr(self, methodName)
            if method.__doc__ is None:
                continue
            if method.__doc__.startswith('handle:'):
                handle, path_re = method.__doc__.split(':')
                path_re = path_re.strip()
                mo = re.match(path_re, path)
                if mo is None:
                    #print 'did not handle %s with %s' % (path, path_re)
                    continue
                print 'handling %s with %s (%s)', (path, path_re, mo.groups())
                
                try:
                    temp = StringIO()
                    original_wfile = self.wfile
                    self.wfile = temp
                    try:
                        method(*mo.groups())
                    finally:
                        self.wfile = original_wfile

                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()
                    self.wfile.write(temp.getvalue())
                except Exception:
                    self.send_response(500)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    traceback.print_exc(file=self.wfile)
                return

        print 'no handler for %s' % path
        self.send_response(404)

    def getFunctionLink(self, func):
        _, _, func_name = func
        title = func_name

        return '<a title="%s" href="/func/%s">%s</a>' % (title, self.func_to_id[func], formatfunc(func))

    def index(self):
        'handle: /$'
        table = []

        sort_index = ['cc', 'nc', 'tt', 'ct'].index(self.query.get('sort', 'ct'))
        print 'sort_index', sort_index
        
        self.print_list.sort(
            key=lambda func: self.stats.stats[func][sort_index],
            reverse=True)

        for func in self.print_list:
            file, line, func_name = func
            primitive_calls, total_calls, exclusive_time, inclusive_time, callers = self.stats.stats[func]

            row = wrapTag('tr', ''.join(wrapTag('td', cell) for cell in (
                self.getFunctionLink(func),
                formatTimeAndPercent(exclusive_time, self.total_time),
                formatTimeAndPercent(inclusive_time, self.total_time),
                primitive_calls,
                total_calls,
                formatTime(exclusive_time / primitive_calls),
                formatTime(inclusive_time / primitive_calls))))

            table.append(row)

        data = '''\
<html>
<head>
<style>
</style>
</head>
<body>
<h1>%s</h1>
<ul>
<li>Total time: %s</li>
</ul>
<table>
<tr>
  <th>file:line:function</th>
  <th><a href="?sort=tt">exclusive time</a></th>
  <th><a href="?sort=ct">inclusive time</a></th>
  <th><a href="?sort=cc">primitive calls</a></th>
  <th><a href="?sort=nc">total calls</a></th>
  <th>exclusive per call</th>
  <th>inclusive per call</th>
</tr>
%s
</table>
</body>
</html>
''' % (self.filename, formatTime(self.total_time), '\n'.join(table))
        self.wfile.write(data)

    def func(self, id):
        'handle: /func/(.*)$'
        func_id = int(id)
        func = self.id_to_func[func_id]

        f_cc, f_nc, f_tt, f_ct, callers = self.stats.stats[func]
        callees = self.stats.all_callees[func]

        def sortedByInclusive(items):
            sortable = [(ct, (f, (cc, nc, tt, ct))) for f, (cc, nc, tt, ct) in items]
            return [y for x, y in reversed(sorted(sortable))]

        def buildFunctionTable(items):
            callersTable = []
            for caller, (cc, nc, tt, ct) in sortedByInclusive(items):
                callersTable.append(wrapTag('tr', ''.join(wrapTag('td', cell)
                                                          for cell in (
                    self.getFunctionLink(caller),
                    formatTimeAndPercent(tt, self.total_time),
                    formatTimeAndPercent(ct, self.total_time),
                    cc,
                    nc,
                    formatTime(tt / cc),
                    formatTime(ct / cc)))))
            return '\n'.join(callersTable)
        
        caller_stats = [(c, self.stats.stats[c][:4]) for c in callers]
        callersTable = buildFunctionTable(caller_stats)
        calleesTable = buildFunctionTable(callees.items())

        page = '''\
<html>
<body>
<a href="/">Index</a>
<h1>%s</h1>
<ul>
<li>Primitive calls: %s</li>
<li>Total calls: %s</li>
<li>Exclusive time: %s</li>
<li>Inclusive time: %s</li>
</ul>
<h2>Callers</h2>
<table>
<tr>
<th>Function</th>
<th>Exclusive time</th>
<th>Inclusive time</th>
<th>Primitive calls</th>
<th>Total calls</th>
<th>Exclusive per call</th>
<th>Inclusive per call</th>
</tr>
%s
</table>
<h2>Callees</h2>
<table>
<tr>
<th>Function</th>
<th>Exclusive time</th>
<th>Inclusive time</th>
<th>Primitive calls</th>
<th>Total calls</th>
<th>Exclusive per call</th>
<th>Inclusive per call</th>
</tr>
%s
</table>
</body>
</html>
''' % (formatfunc(func), f_cc, f_nc, f_tt, f_ct, callersTable, calleesTable)

        print >> self.wfile, page
        

def launch_browser(port):
    time.sleep(1)
    webbrowser.open('http://localhost:%s' % port)

def startThread(fn):
    thread = threading.Thread(target=fn)
    thread.setDaemon(True)
    thread.start()
    return thread

def main(argv):
    statsfile  = argv[1]
    port = argv[2:]
    if port == []:
        port = PORT
    else:
        port = int(port[0])
    stats = pstats.Stats(statsfile)
    
    httpd = HTTPServer(
        ('', port),
        lambda *a, **kw: MyHandler(stats, *a, **kw))
    serve_thread  = startThread(httpd.serve_forever)
    launch_thread = startThread(lambda: launch_browser(port))

    while serve_thread.isAlive():
        serve_thread.join(timeout=1)
    

if __name__ == '__main__':
    main(argv=sys.argv)
