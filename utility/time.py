# UTILITY/TIME.PY

# ## PYTHON IMPORTS
import time
import logging
import datetime

# ## LOCAL IMPORTS
from .data import set_precision


# ## FUNCTIONS

# #### Timeval functions

def datetime_from_epoch(timestamp):
    return _normalize_time(datetime.datetime.fromtimestamp(timestamp))


def local_datetime_utcoffset():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo.utcoffset(None)


def local_datetime_to_utc(timeval):
    return timeval - local_datetime_utcoffset()


def process_utc_timestring(timestring):
    try:
        return _normalize_time(datetime.datetime.fromisoformat(timestring.replace('Z', '+00:00')).replace(tzinfo=None))
    except Exception:
        logging.error('Failed parse datetime string')


def get_current_time_local():
    return _normalize_time(datetime.datetime.now())


def get_current_time_zulu():
    return _normalize_time(datetime.datetime.utcnow())


def add_days(timeval, days):
    return timeval + datetime.timedelta(days=days)


def add_hours(timeval, hours):
    return timeval + datetime.timedelta(hours=hours)


def days_ago(days):
    return add_days(get_current_time_zulu(), -days)


def days_from_now(days):
    return add_days(get_current_time_zulu(), days)


def hours_ago(hours):
    return add_hours(get_current_time_zulu(), -hours)


def hours_from_now(hours):
    return add_hours(get_current_time_zulu(), hours)


def minutes_from_now(minutes):  # Unused
    return get_current_time_zulu() + datetime.timedelta(minutes=minutes)


def minutes_ago(minutes):
    return get_current_time_zulu() - datetime.timedelta(minutes=minutes)


def seconds_from_now_local(seconds):
    return _normalize_time(datetime.datetime.now() + datetime.timedelta(seconds=seconds))


def get_date(timeval):
    return timeval.strftime("%Y-%m-%d")


def average_timedelta(timedeltas):
    return sum(timedeltas, datetime.timedelta(0)) / len(timedeltas)


def humanized_timedelta(delta, precision=2):
    precision_str = "%%.%df " % precision
    if delta.days == 0:
        if delta.seconds < 60:
            return "%d seconds" % delta.seconds
        if delta.seconds < 3600:
            return (precision_str + "minutes") % set_precision(delta.seconds / 60, precision)
        return (precision_str + "hours") % set_precision(delta.seconds / 3600, precision)
    days = delta.days + (delta.seconds / 86400)
    if days < 7:
        return (precision_str + "days") % set_precision(days, precision)
    if days < 30:
        return (precision_str + "weeks") % set_precision(days / 7, precision)
    if days < 365:
        return (precision_str + "months") % set_precision(days / 30, precision)
    return (precision_str + "years") % set_precision(days / 365, precision)


def time_ago(timeval, precision=2):
    delta = get_current_time_zulu() - timeval
    if delta < datetime.timedelta(0):
        return "not yet"
    return humanized_timedelta(delta, precision) + " ago"


def time_from_now(timeval, precision=2):
    delta = timeval - get_current_time_zulu()
    if delta < datetime.timedelta(0):
        return "already past"
    return humanized_timedelta(delta, precision) + " from now"


# #### Timestamp functions

def get_current_timestamp():
    return datetime.datetime.now().timestamp()


def get_current_timestamp_zulu():
    return datetime.datetime.utcnow().timestamp()


def months_to_seconds(intime):
    return (intime * 60 * 60 * 24 * 30)


def weeks_to_seconds(intime):
    return (intime * 60 * 60 * 24 * 7)


def days_to_seconds(intime):
    return (intime * 60 * 60 * 24)


def hours_to_seconds(intime):
    return (intime * 60 * 60)


def seconds_to_months(intime):
    return intime / (60 * 60 * 24 * 30)


def seconds_to_weeks(intime):
    return intime / (60 * 60 * 24 * 7)


def seconds_to_days(intime):
    return intime / (60 * 60 * 24)


def seconds_to_hours(intime):
    return intime / (60 * 60)


def has_month_passed(starttime, endtime, num=1):
    return (((starttime - endtime) / months_to_seconds(num)) > 1.0)


def has_week_passed(starttime, endtime, num=1):
    return (((starttime - endtime) / weeks_to_seconds(num)) > 1.0)


def has_day_passed(starttime, endtime, num=1):
    return (((starttime - endtime) / days_to_seconds(num)) > 1.0)


def has_hour_passed(starttime, endtime, num=1):
    return (((starttime - endtime) / hours_to_seconds(num)) > 1.0)


def within_one_second(starttime, endtime):
    return ((abs(starttime - endtime)) < 1.0)


# #### Timestring functions

def add_days_str(timestring, days):
    timestamp = time.gmtime(time.mktime(time.strptime(timestring, "%Y-%m-%d")))
    return time.strftime("%Y-%m-%d", timestamp + days_to_seconds(days))


def get_date_str(epochtime):
    return time.strftime("%Y-%m-%d", time.gmtime(epochtime))


# ## Private

def _normalize_time(timeval):
    return timeval - datetime.timedelta(microseconds=timeval.microsecond)
