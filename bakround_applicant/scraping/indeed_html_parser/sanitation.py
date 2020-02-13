#!/usr/bin/env python3
import sys
import re
import calendar
from bakround_applicant.all_models.db import LookupState, LookupDegreeMajor
from django.db.models import Q


class Sanitation():

    def __init__(self):
        self.__degree_majors = None

        self.DEGREE_NAME_PATTERNS = [("bachelors", ["bachelor", "bs ", "ba ", "b.s.", "b.a.", "bs/", "ba/", "bsn"]), ("masters", ["masters", "master ", "ms"]), ("associates", [
            "associate", "aa ", "as ", "adn "]), ("doctorate", ["doctor", "m.d.", "md ", "ph.d", "phd ","juris"]), ("highschool", ["high school", "g.e.d.", "ged"]), ("certification", ["cna ", "cma "]), ]

    def extract_city_and_state(self, location):
        if ", " in location:
            city, state_string = location.split(", ", 1)
            # TODO: Use python-Levenshtein or fuzzystrmatch PG extension
            # to make this more accurate
            state = LookupState.objects.filter(Q(state_code=state_string) | Q(state_name=state_string)).first()
            return city, state
        else:
            return None, None

    def guess_degree_type(self, degree_name):
        degree_name = degree_name.lower().strip()

        for (degree_type, prefixes) in self.DEGREE_NAME_PATTERNS:
            for prefix in prefixes:
                if degree_name.startswith(prefix):
                    return degree_type

        return None

    def degree_majors(self):
        global __degree_majors
        if not self.__degree_majors:
            __degree_majors = list(map(lambda x: x.strip(), LookupDegreeMajor.objects.all(
            ).values_list("degree_major_name", flat=True)))
        return __degree_majors

    def guess_degree_major(self, degree_name):
        degree_name = degree_name.lower().strip()
        for major in self.degree_majors():
            if degree_name.endswith(major.lower()) or (" in " + major.lower() + " in ") in degree_name:
                return major

        return None

    def extract_degree_info(self, degree_name):
        if ' in' in degree_name:
            ps = degree_name.rsplit(" in ", 1)
        else:
            ps = degree_name.rsplit(" ", 1)
        if len(ps) == 2:
            typ, major = ps
            major = major.strip().title()
            typ = self.guess_degree_type(typ)
            return major, typ

        return None, None

    def extract_date(self, string, use_last_day=False):
        string = string.strip()
        string = re.sub(r" +", " ", string)

        if string == "Present":
            return "Present"

        elif " " in string:
            month_name, year = string.split(" ", 1)
            year = int(year)

            if month_name and month_name in calendar.month_name:
                month = list(calendar.month_name).index(month_name)
            else:
                month = None

            if month and use_last_day:
                day = calendar.monthrange(year, month)[1]
            else:
                day = 1

            return '{}-{:02}-{:02}'.format(year, month, day)

        elif len(string) == 4 and string.isdigit():  # the given date is just a year
            if use_last_day:
                return '{}-06-30'.format(string)
            else:
                return '{}-01-01'.format(string)

        else:
            return None

    def prepare_phn_number(self, number):
        return number.replace('-', '').replace('(', '').replace(')', '')
