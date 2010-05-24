#!/usr/bin/env python
# -*- coding: utf-8 -*-

import persistentstore, csv

class CsvExporter:
    """Iterate through the list of transactions for an account and
    exort to a CSV file."""
    
    def __init__(self, dbPath):
        """Initialize the exporter by connecting to the database."""
        try:
            self.db = persistentstore.PersistentStore(dbPath)
        except:
            print "Database file not found"
    
    def SetOptions(self, exportPath, delimiter=',', quotechar="'"):
        """Set the options for the exporter."""
        self.exportPath = exportPath
        self.delimiter = delimiter
        self.quotechar = quotechar
    
    def Export(self, accountId):
        """Iterate through the database and write the transactions
        to a CSV file."""
        
        #Open the CSV file for writing, write headers
        exportFile = open(self.exportPath, 'w')
        writer = csv.writer(exportFile, delimiter=self.delimiter,
            quotechar=self.quotechar)
        
        writer.writerow(['Description', 'Amount', 'Date'])

        #Iterate through transaction list, write rows
        transactions = self.db.getAccounts()[accountId].GetTransactions()
        for item in transactions:
            writer.writerow([item.GetDescription(), item.GetAmount(),
                item.GetDate()])
        self.db.Close() #Close the database cleanly
        
        #Close CSV file
        exportFile.close()
