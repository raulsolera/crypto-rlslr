# Imports
from datetime import datetime, timedelta
from pytz import timezone
datetime_interval = tuple([datetime, datetime])

# Parameters
# Standard currencies
std_currencies = {
    'EUR': 'Euro',
    'USD': 'Dolar'
}
# Crypto currencies
crypto_currencies = {
    'XBT': 'Bitcoin',
    'ETH': 'Ethereum',
}

# Candle graph
candles_color = {
    -1: 'red',
    0: 'lightslategray',
    1: 'green'}

window_size = {
    '10 sec':  (10,      '10s'),
    '30 sec':  (30,      '30s'),
    '1 min':   (60,     '1min'),
    '2 min':   (60*2,   '2min'),
    '5 min':   (60*5,   '5min'),
    '10 min':  (60*10, '10min'),
    '15 min':  (60*15, '15min'),
}

anchor_time = {
    '-24 hours':  24*60*60,
    '-12 hours':  12*60*60,
    '-6 hours':    6*60*60,
    '-5 hours':    5*60*60,
    '-4 hours':    4*60*60,
    '-3 hours':    3*60*60,
    '-2 hours':    2*60*60,
    '-1 hour':    1*60*60,
    'No anchor':      None}


def utc_to_timezone(_utc: datetime,
                    _tz: datetime.tzinfo = 'Europe/Madrid'
                    ) -> datetime:
    """
    Convert datetime variable from UTC to local time
    parameters:
    - _utc (datetime): datetime to convert
    - _tz (datetime.tzinfo): timezone, default 'Europe/Madrid'
    returns:
    - new_datetime (datetime): datetime in required timezone
    """
    old_timezone = timezone('UTC')
    new_timezone = timezone(_tz)
    return old_timezone.localize(_utc).astimezone(new_timezone)


def get_datime_interval(**kwargs) -> datetime_interval:
    """
    Construct a datetime interval based on window time size,
    number of windows and one of the interval sides
    Parameters:
    - window (int):
      size of the time interval in seconds
    - number of intervalse (int):
      size of the time interval in seconds
    - from_datetime or to_datetime (datetime):
      datetime from or to construct the time interval
      only one required of both are provided to is used
    Returns:
    time_interval (datetime_interval): from datetime to datetime tuple
    """

    try:
        window = kwargs['window']
    except KeyError:
        raise TypeError("Missing required argument: 'window'")

    try:
        number_of_windows = kwargs['number_of_windows']
    except KeyError:
        raise TypeError("Missing required argument: 'number_of_windows'")

    from_datetime = kwargs.get('from_datetime')
    to_datetime = kwargs.get('to_datetime')
    if not(from_datetime or to_datetime):
        raise TypeError("Missing required argument:\
          either 'from_datetime' or 'to_datetime'")
    if from_datetime and to_datetime:
        print("Two endpoints provided only 'to_datetime' is used")

    number_of_seconds = window*number_of_windows
    time_interval = (None, None)
    if to_datetime:
        time_interval = (to_datetime - timedelta(seconds=number_of_seconds),
                         to_datetime)
    elif from_datetime:
        time_interval = (from_datetime,
                         from_datetime + timedelta(seconds=number_of_seconds))
    return time_interval


def get_time_window_start(date_time: datetime, window: int) -> datetime:
    """
    Returns the stadandarize start of a time window
    inmediate before the datetime provided
    such that there are a whole number of time windows
    from the start of the hour
    Parameters:
    - date_time (datetime):
      datetime whose window start want to calculte
    - window (int):
      size of the time interval in seconds
    Returns:
    previous_time (datetime): datetime start of the window
    """
    # get previous hour
    previous_time = date_time.replace(microsecond=0, second=0, minute=0)
    while previous_time < date_time:
        previous_time += timedelta(seconds=window)
    return previous_time - timedelta(seconds=window)
