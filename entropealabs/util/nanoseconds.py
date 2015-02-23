import time
import nanotime
import datetime

def last_day():
    now = nanotime.timestamp(time.time())
    yesterday = datetime.datetime.utcnow()-datetime.timedelta(days=1)
    yesterday = nanotime.datetime(yesterday)
    return "{}-{}".format(yesterday.nanoseconds(), now.nanoseconds())

def since(since):
    since = nanotime.datetime(since)
    now = nanotime.timestamp(time.time())
    return "{}-{}".format(since.nanoseconds(), now.nanoseconds())
