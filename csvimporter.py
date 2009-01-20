from banker import Bank
from datetime import date, datetime
import codecs, csv

class CsvImporter:
    """
    Parses a csv file and extracts the data for import into the wxBanker
    data structures
    """
    def __init__(self):
        pass
    
    def importFile(self, account, fileName, settings):
        print settings.delimiter
        csvReader = csv.reader(
            UTF8Recoder(open(fileName, 'rb'), settings.encoding), 
            delimiter=settings.delimiter)
        
        firstLineSkipped = False
        for row in csvReader:
            if settings.skipFirstLine and not firstLineSkipped:
                firstLineSkipped = True
                continue

            amount = float(row[settings.amountColumn].replace(
                settings.decimalSeparator, '.'))
            vals = []
            for column in settings.descriptionColumns:
                vals.append(row[column])
            desc = ' / '.join(vals)
            tdate = datetime.strptime(row[settings.dateColumn],
                settings.dateFormat).strftime('%Y-%m-%d')
                
            print 'Amount:', amount, 'Date:', tdate, 'Description:', desc
                
            #Bank().makeTransaction(account, amount, desc, tdate)

class CsvImporterSettings:
    def __init__(self):
        pass

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
