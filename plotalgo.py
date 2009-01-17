import datetime, bankobjects

def makeTransaction(date, amount):
    """A tiny wrapper to make tests below shorter."""
    return bankobjects.Transaction(None, None, amount, "", date)
    
def get(transactions, numPoints):
    """
    # First, rename the function for convenience
    >>> T = makeTransaction
    >>> result = get([], 10)
    >>> result[0]
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    >>> result[1] == datetime.date.today()
    True
    >>> result[2] < 0.001
    True
    >>> get([T("2008/1/6", 1)], 3)[0]
    [1.0, 1.0, 1.0]
    >>> get([T("2008/1/6", 1), T("2008/1/7", 2)], 4)[0]
    [1.0, 1.0, 1.0, 3.0]
    >>> get([T("2008/1/6", 1), T("2008/1/7", 2)], 1)
    ([3.0], datetime.date(2008, 1, 6), 1.0)
    >>> get([T("2008/1/6", 1), T("2008/1/7", 2)], 2)[0]
    [1.0, 3.0]
    >>> get([T("2008/1/6", 1), T("2008/1/7", 2)], 3)[0]
    [1.0, 1.0, 3.0]
    >>> get([T("2008/1/1", 1), T("2008/1/10", 2)], 10)[0]
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 3.0]
    >>> get([T("2008/1/1", 1), T("2008/1/3", 2), T("2008/1/10", 3)], 10)[0]
    [1.0, 1.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 6.0]
    """
    if transactions == []:
        # In this case, the delta we return is a very small number instead of
        # zero because for plotting you need SOME delta.
        return [0] * 10, datetime.date.today(), 1.0/2**32
    
    transactions = list(sorted(transactions))
    
    startDate, endDate = transactions[0].Date, transactions[-1].Date
    today = datetime.date.today()
    if today > endDate:
        endDate = today

    distance = (endDate - startDate).days
    daysPerPoint = 1.0 * distance / numPoints
    dppDelta = datetime.timedelta(daysPerPoint)
    
    points = [0.0]
    tindex = 0
    for i in range(numPoints):
        while tindex < len(transactions) and transactions[tindex].Date <= startDate + (dppDelta * (i+1)):
            points[i] += transactions[tindex].Amount
            tindex += 1
        
        points.append(points[-1])
        
    return points[:-1], startDate, daysPerPoint
    
    
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=1)
    