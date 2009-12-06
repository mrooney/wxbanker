#!/usr/bin/env python
# -*- coding: utf-8 -*-
#    https://launchpad.net/wxbanker
#    csvimporter.py: Copyright 2007-2009 Mike Rooney <mrooney@ubuntu.com>
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

from datetime import date, datetime
from wx.lib.pubsub import Publisher
import codecs, csv, os, re
from cStringIO import StringIO

from wxbanker.bankobjects.transaction import Transaction
from wxbanker import fileservice, debug

try:
    import simplejson as json
except:
    json = None
    
shippedProfiles = {
    "mint": {
        "amountColumn": 4,
        "dateColumn": 1,
        "dateFormat": "%m/%d/%Y",
        "decimalSeparator": ".",
        "delimiter": ",",
        "descriptionColumns": "2",
        "encoding": "utf-8",
        "skipFirstLine": True
    },
    "Sparkasse": {
        "amountColumn": 9,
        "dateColumn": 2,
        "dateFormat": "%d.%m.%y",
        "decimalSeparator": ",",
        "delimiter": ";",
        "descriptionColumns": "6, 5 , 4",
        "encoding": "utf-8",
        "skipFirstLine": True
     }
}


class CsvImporter:
    """
    Parses a csv file and extracts the data for import into the wxBanker data structures.
    """
    
    def getTransactionsFromFile(self, filename, settings):
        contents = open(filename, 'rb').read()
        return self.getTransactionsFromCSV(contents, settings)

    def getTransactionsFromCSV(self, csvdata, settings):
        csvdata = StringIO(csvdata)
        csvReader = csv.reader(
            UTF8Recoder(csvdata, settings['encoding']),
            delimiter=settings['delimiter'])

        transactions = []

        firstLineSkipped = False
        for row in csvReader:
            if settings['skipFirstLine'] and not firstLineSkipped:
                firstLineSkipped = True
                continue

            # convert to python unicode strings
            row = [unicode(s, "utf-8") for s in row]

            amount = self.parseAmount(row[settings['amountColumn'] - 1], settings['decimalSeparator'])
            # Properly parse amounts from mint.
            if settings == shippedProfiles['mint'] and row[4] == "debit":
                amount *=-1
                
            desc = re.sub('\d+', lambda x: row[int(x.group(0)) - 1], settings['descriptionColumns'])
            tdate = datetime.strptime(row[settings['dateColumn'] -1],
                settings['dateFormat']).strftime('%Y-%m-%d')

            transactions.append(Transaction(None, None, amount, desc, tdate))

        return TransactionContainer(transactions)

    def parseAmount(self, val, decimalSeparator):
        amountStr = ""
        for char in val:
            if char in "-1234567890"+decimalSeparator:
                amountStr += char

        amountStr = amountStr.replace(decimalSeparator, '.')
        return float(amountStr)

class TransactionContainer(object):
    def __init__(self, transactions):
        self.Name = "#CSVIMPORT"
        self.Transactions = transactions

    def RemoveTransactions(self, transactions):
        for t in transactions:
            self.Transactions.remove(t)
        Publisher.sendMessage("transactions.removed", (self, transactions))

class CsvImporterProfileManager:
    def __init__(self):
        self.configFile = fileservice.getConfigFilePath('csvImportProfiles.json')
        self.loadProfiles()

    def getProfile(self, key):
        return self.profiles.get(key, None)

    def saveProfile(self, key, settings):
        self.profiles[key] = settings
        self.saveProfiles()

    def deleteProfile(self, key):
        del self.profiles[key]

    def loadProfiles(self):
        self.profiles = shippedProfiles
        try:
            contents = open(self.configFile, 'r')
            storedProfiles = json.load(contents)
        except Exception, e:
            debug.debug("Unable to read CSV profiles file:", e)
        else:
            self.profiles.update(storedProfiles)

    def saveProfiles(self):
        file = open(self.configFile, 'w')
        try:
            json.dump(self.profiles, file, sort_keys=True, indent=4)
        finally:
            file.close()

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    see http://docs.python.org/library/csv.html
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")
