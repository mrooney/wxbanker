#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import date, datetime
from bankobjects import Transaction
from wx.lib.pubsub import Publisher
import codecs, csv, os, re
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
            
            amount = self.parseAmount(row[settings['amountColumn'] - 1], settings)
            desc = re.sub('\d+', lambda x: row[int(x.group(0)) - 1], settings['descriptionColumns'])
            tdate = datetime.strptime(row[settings['dateColumn'] -1],
                settings['dateFormat']).strftime('%Y-%m-%d')

            transactions.append(Transaction(None, None, amount, desc, tdate))
        
        return TransactionContainer(transactions)
        
    def parseAmount(self, val, settings):
        val = val.replace(settings['decimalSeparator'], '.')
        amountStr = ""
        for char in val:
            if char.isdigit() or char in "-.":
                amountStr += char
                
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
        configFile = 'csvImportProfiles.json'
        
        # copied from wxbanker.py
        defaultPath = os.path.join(os.path.dirname(__file__), configFile)
        if 'HOME' in os.environ:
            # We seem to be on a Unix environment.
            preferredPath = os.path.join(os.environ['HOME'], '.config', 'wxBanker', configFile)
            if os.path.exists(preferredPath) or not os.path.exists(defaultPath):
                defaultPath = preferredPath
                # Ensure that the directory exists.
                dirName = os.path.dirname(defaultPath)
                if not os.path.exists(dirName):
                    os.mkdir(dirName)
        
        self.configFile = defaultPath
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
