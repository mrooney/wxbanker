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