import datetime


def milliseconds_to_datetime(ms):
    # return datetime.datetime.fromtimestamp(ms / 1000.0, tz=datetime.timezone.utc)
    return datetime.datetime.utcfromtimestamp(ms / 1000.0)
