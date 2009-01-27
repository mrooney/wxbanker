import datetime, bankobjects

def makeTransaction(date, amount):
    """A tiny wrapper to make tests below shorter."""
    return bankobjects.Transaction(None, None, amount, "", date)
    
def get(transactions, numPoints):
    """
    # First, rename the function for convenience
    >>> T = makeTransaction
    >>> today = datetime.date.today()
    >>> one = datetime.timedelta(1)
    >>> result = get([], 10)
    >>> result[0]
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    >>> result[1] == datetime.date.today()
    True
    >>> result[2] < 0.001
    True
    >>> get([T("2008/1/6", 1)], 3)[0]
    [1.0, 1.0, 1.0]
    >>> get([T(today-one, 1), T(today, 2)], 4)[0]
    [1.0, 1.0, 1.0, 3.0]
    >>> result = get([T(today-one, 1), T(today, 2)], 1)
    >>> result[0]
    [3.0]
    >>> result[1] == today - one
    True
    >>> result[2]
    1.0
    >>> get([T(today, 1), T(today+one, 2)], 2)[0]
    [1.0, 3.0]
    >>> get([T(today, 1), T(today+one, 2)], 3)[0]
    [1.0, 1.0, 3.0]
    >>> get([T(today-one*9, 1), T(today, 2)], 10)[0]
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 3.0]
    >>> get([T(today, 1), T(today+one*2, 2), T(today+one*9, 3)], 10)[0]
    [1.0, 1.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 6.0]
    >>> result = get([T(today, 1)], 2)
    >>> result[0]
    [1.0, 1.0]
    >>> result[1] == today
    True
    >>> result[2] != 0
    True
    """
    # Don't ever return 0 as the dpp, you can't graph without SOME x delta.
    smallDelta = 1.0/2**32
    
    if transactions == []:
        return [0] * 10, datetime.date.today(), smallDelta
    
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
        
    return points[:-1], startDate, daysPerPoint or smallDelta
    
    
if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=1)
    