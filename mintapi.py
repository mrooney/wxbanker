#    https://launchpad.net/wxbanker
#    mintapi.py: Copyright 2007-2009 Mike Rooney <michael@wxbanker.org>
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

import urllib3, re
import pprint, getpass

def main():
    urllib3.enablecookies()

    username = raw_input("Username: ")
    password = getpass.getpass("Password: ")
    
    result = urllib3.post("https://wwws.mint.com/loginUserSubmit.xevent", {"username": username, "password": password, "task": "L", "nextPage": ""})
    #open("output.html", "w").write(result)
    #result = open("output.html").read()
    if "forgot your password?" in result.lower():
        raise Exception("Mint.com login failed!")

    accountsRegex = """<a class="" href="transaction.event\?accountId=([0-9]+)">([^<]+)</a></h4><h6><span class="last-updated">[^<]+</span>([^<]+)</h6>"""
    mintAccounts = []
    for account in re.findall(accountsRegex, result):
        aid = account[0]
        name = "%s %s" % (account[1], account[2])
        mintAccounts.append((name, aid))
        
    mintAccounts.sort()
    #pprint.pprint(mintAccounts)
    
    for name, aid in mintAccounts:
        accountPage = urllib3.read("https://wwws.mint.com/transaction.event?accountId=%s" % aid)
        balRegex = """<th>Available [^<]+</th><td class="money">([^<]+)</td>"""
        balance = re.findall(balRegex, accountPage)[0]
        print name, balance
        """https://wwws.mint.com/transactionDownload.event?accountId=223615&comparableType=8&offset=0"""
    
if __name__ == "__main__":
    main()