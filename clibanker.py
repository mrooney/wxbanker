#    https://launchpad.net/wxbanker
#    clibanker.py: Copyright 2007, 2008 Mike Rooney <michael@wxbanker.org>
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

import os

def wait():
    raw_input("Press enter to continue...")

def _queryDate():
    date = raw_input("Date (leave blank for today) (MM/DD[/YYYY]): ")
    if len(date.split("/")) == 2:
        # If they didn't include the year, assume the current one.
        date += "/" + str(time.gmtime()[0])
    return date

def _selectAccount(accounts):
    accountlist = sorted(accounts)
    accountnum = input("Account?\n"+"\n".join( [ str(i+1)+". "+account.Name for i, account in enumerate(accountlist)] )+"\n? ")
    account = accountlist[accountnum-1]
    clearScreen()
    return account

def clearScreen():
    os.system(['clear','cls'][os.name == 'nt'])

def main(bankController):
    """
    If we are running the actual file, create a command-line
    interface that the user can use.
    """
    bankmodel = bankController.Model

    choice = -1
    while choice != 0:
        clearScreen()
        print '1. Create an account'
        print '2. Enter a transaction'
        print '3. Enter a transfer'
        print '4. View Balances'
        print '5. View Transactions'
        print '6. Remove Account'
        print '0. Quit'
        choice = input("? ")

        clearScreen()

        if choice == 1:
            accountName = raw_input("Account name: ")
            bankmodel.CreateAccount(accountName)
            #bank.createAccount(accountName)
            #bank.save()
            wait()

        elif choice == 2:
            accountName = _selectAccount(bankmodel.Accounts)
            amount = input("Amount: $")
            desc = raw_input("Description: ")
            date = _queryDate()
            bank.makeTransaction(accountName, amount, desc, date)
            bank.save()
            print 'Transaction successful.'
            wait()

        elif choice == 3:
            print 'From:'
            source = _selectAccount(bankmodel.Accounts)
            print 'To:'
            destination = _selectAccount(bankmodel.Accounts)
            amount = input('Amount: $')
            desc = raw_input('Description (optional): ')

            confirm = -1
            while confirm == -1 or confirm.lower() not in ['y', 'n']:
                confirm = raw_input('Transfer %s from %s to %s? [y/n]: '%( bank.float2str(amount), source, destination ))

            if confirm == 'y':
                date = _queryDate()
                bank.makeTransfer(source, destination, amount, desc, date)
                bank.save()
                print 'Transfer successfully entered.'
            else:
                print 'Transfer cancelled.'
            wait()

        elif choice == 4:
            total = 0.0
            for account in sorted(bankmodel.Accounts):
                balance = account.Balance
                print "%s %s"%( (account.Name+':').ljust(20), account.float2str(balance, 10))
                total += balance
            print "%s %s"%( "Total:".ljust(20), bankmodel.float2str(total, 10))

            wait()

        elif choice == 5:
            account = _selectAccount(bankmodel.Accounts)
            total = 0.0
            for trans in account.Transactions:
                total += trans.Amount
                print "%s - %s  %s %s"%( trans.Date.strftime('%m/%d/%Y'), trans.Description[:25].ljust(25), account.float2str(trans.Amount, 10), account.float2str(total, 10) )
            print "Total: %s"%account.float2str(total)

            wait()

        elif choice == 6:
            account = _selectAccount(bankmodel.Accounts)
            confirm = -1
            while confirm == -1 or confirm.lower() not in ['y', 'n']:
                confirm = raw_input('Permanently remove account "%s"? [y/n]: '%account.Name)
            if confirm == 'y':
                bankmodel.RemoveAccount(account.Name)
                #bank.removeAccount(accountName)
                #bank.save()
                print 'Account successfully removed'
            else:
                print 'Account removal cancelled'
            wait()
            
            
if __name__ == "__main__":
    print "To run the command-line version of wxBanker, run with the --cli argument"
    