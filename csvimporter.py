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
from bankobjects import Transaction
from wx.lib.pubsub import Publisher
import codecs, csv, os, re
import fileservice as fs
try:
    import simplejson as json
except:
    json = None

class CsvImporter:
    """
    Parses a csv file and extracts the data for import into the wxBanker
    data structures
    """
    def __init__(self):
        pass

    def getTransactionsFromFile(self, fileName, settings):
        csvReader = csv.reader(
            UTF8Recoder(open(fileName, 'rb'), settings['encoding']),
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
        self.configFile = fs.getConfigFilePath('csvImportProfiles.json')
        self.loadProfiles()

    def getProfile(self, key):
        return self.profiles.get(key, None)

    def saveProfile(self, key, settings):
        self.profiles[key] = settings
        self.saveProfiles()

    def deleteProfile(self, key):
        del self.profiles[key]

    def loadProfiles(self):
        self.profiles = {}
        try:
            file = open(self.configFile, 'r')
            try:
                self.profiles = json.load(file)
            finally:
                file.close()
        except Exception, e:
            print "Failed to read CSV profiles file:", e

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
