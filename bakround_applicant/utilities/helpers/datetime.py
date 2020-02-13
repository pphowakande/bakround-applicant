__author__ = 'ajaynayak'

import pytz
import six
from django.utils.dateparse import date_re
from datetime import datetime, date, time
import calendar


# This function was modified from django.utils.parse_date to handle dates like
# 2008-06-31, where the day is past the end of the month.
def parse_date_leniently(value):
    """Parses a string and return a datetime.date.

    Raises ValueError if the input is well formatted but not a valid date.
    Returns None if the input isn't well formatted.
    """
    match = date_re.match(value)
    if match:
        kw = {k: int(v) for k, v in six.iteritems(match.groupdict())}
        try:
            return date(**kw)
        except ValueError:
            kw['day'] = number_of_days_in_month(kw['year'], kw['month'])
            return date(**kw)


def parse_date_as_utc(date_string):
        if date_string is None or date_string is '':
            return None

        parsed_date = parse_date_leniently(date_string)

        return datetime.combine(parsed_date, time(tzinfo=pytz.UTC)) \
            if parsed_date is not None \
            else None


def number_of_days_in_month(year, month):
    return calendar.monthrange(year, month)[1]
