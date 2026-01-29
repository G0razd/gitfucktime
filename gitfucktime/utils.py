import datetime
import random

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

def get_next_work_day(date):
    '''Returns the next work day (Mon-Fri) after the given date.'''
    next_day = date + datetime.timedelta(days=1)
    while not is_work_day(next_day):
        next_day += datetime.timedelta(days=1)
    return next_day

def is_work_day(date):
    '''Returns True if date is Monday-Friday.'''
    return date.weekday() < 5

def generate_work_hours_timestamp(start_date, end_date, max_time=None):
    '''Generates a random timestamp within work hours (09:00-17:00) on a work day.
    
    Args:
        start_date: Start of the date range
        end_date: End of the date range
        max_time: Optional maximum datetime limit (to prevent future commits)
    '''
    total_days = (end_date - start_date).days + 1

    while True:
        random_days = random.randint(0, total_days)
        target_date = start_date + datetime.timedelta(days=random_days)

        if is_work_day(target_date):
            hour = random.randint(9, 16)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            result = target_date.replace(hour=hour, minute=minute, second=second)
            
            # Clamp to max_time if provided and result exceeds it
            if max_time and result > max_time:
                # If this is today, cap at max_time; otherwise try again
                if target_date.date() == max_time.date():
                    # Use max_time's hour/minute/second if we're on the same day
                    result = max_time
                else:
                    # Don't use dates beyond max_time
                    continue
                    
            return result
