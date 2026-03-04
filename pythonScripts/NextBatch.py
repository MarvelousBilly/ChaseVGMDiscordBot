from datetime import datetime, timedelta, time

def get_batch(year, month):
    # first of the month
    first_of_month = datetime(year, month, 1).date()
    
    # first Thursday
    days_until_thursday = (3 - first_of_month.weekday()) % 7
    first_thursday = first_of_month + timedelta(days=days_until_thursday)

    # Saturday before that Thursday
    return first_thursday - timedelta(days=((first_thursday.weekday() - 5) % 7))

def get_next_batch(today=datetime.today().date()):
    
    year, month = today.year, today.month

    def get_next_month(y, m):
        return (y + 1, 1) if m == 12 else (y, m + 1)

    next_year,      next_month =      get_next_month(year,      month)
    next_next_year, next_next_month = get_next_month(next_year, next_month) #next next month xdd
    
    current_batch   = get_batch(year,           month)
    next_batch      = get_batch(next_year,      next_month)
    next_next_batch = get_batch(next_next_year, next_next_month)
        
    if today > current_batch:
        if today > next_batch:
            return next_next_batch
        else:
            return next_batch
    else:
        return current_batch

def print_batch(reference_date=datetime.today().date()):
    nextBatchDT = datetime.combine(get_next_batch(reference_date) + timedelta(days=1), time(3,0,0))
    print(nextBatchDT)
    epochS = int((nextBatchDT  - datetime(1970,1,1)).total_seconds())
    return(f"The next batch reveal will be on <t:{epochS}:F>")

if __name__ == "__main__":
    print(datetime.today().date())
    print(print_batch())