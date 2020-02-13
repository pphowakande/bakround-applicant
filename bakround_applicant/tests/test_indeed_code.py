__author__ = "tplick"

import pytest

from indeed_html_parser import parse_indeed_html
from django.db import connection

def parse_name(name):
    mapping = {}
    parse_indeed_html.fill_in_name(mapping, name)
    return [mapping.get('first_name'),
            mapping.get('middle_name'),
            mapping.get('last_name')]

def test_parse_name():
    assert parse_name("Smith") == [None, None, "Smith"]
    assert parse_name("   Smith   ") == [None, None, "Smith"]
    assert parse_name("Joe  Smith") == ["Joe", None, "Smith"]
    assert parse_name("Joe J. Smith") == ["Joe", "J.", "Smith"]
    assert parse_name("Joe J. A. Smith") == ["Joe", "J. A.", "Smith"]
    assert parse_name("Joe J.      A. Smith") == ["Joe", "J. A.", "Smith"]
    assert parse_name("") == [None, None, None]
    print ("parse_name function successful")

def test_extract_date():
    extract_date = parse_indeed_html.extract_date

    assert extract_date("February 2010") == '2010-02-01'
    assert extract_date("February 2010", True) == '2010-02-28'
    assert extract_date("February 2012", True) == '2012-02-29'

    assert extract_date("July 2013", True) == '2013-07-31'
    assert extract_date("June 2013", True) == '2013-06-30'
    assert extract_date("Present") == "Present"

    assert extract_date("1997") == '1997-01-01'
    assert extract_date("1997", True) == '1997-06-30'
    assert extract_date("???") is None
    assert extract_date("  February   2010") == '2010-02-01'
    print ("extract_date function successful")

@pytest.mark.django_db
def test_guess_degree_type():
    assert parse_indeed_html.guess_degree_type("BS Nutrition and Dietetics")== "bachelors"
    assert parse_indeed_html.guess_degree_type("ASN") == None
    assert parse_indeed_html.guess_degree_type("B.S. Nutrition and Dietetics")== "bachelors"
    assert parse_indeed_html.guess_degree_type("Bachelor's") == "bachelors"
    assert parse_indeed_html.guess_degree_type("Associate in Applied Science in Nursing") == "associates"
    assert parse_indeed_html.guess_degree_type("Bachelor of Science in Nursing") == "bachelors"
    assert parse_indeed_html.guess_degree_type("BSN") == "bachelors"
    assert parse_indeed_html.guess_degree_type("Associates in Science & Registered Nurse Education") == "associates"
    assert parse_indeed_html.guess_degree_type("BSN, MSN in Nursing") == "bachelors"
    assert parse_indeed_html.guess_degree_type("RN in Nursing") == None
    assert parse_indeed_html.guess_degree_type("  Bachelor    of Science in \n Nursing    ") == "bachelors"#custom
    assert parse_indeed_html.guess_degree_type(" ") == None
    print ("degree type successful")

@pytest.mark.django_db
def test_guess_degree_major():
    assert parse_indeed_html.guess_degree_major("Associate in Applied Science in Nursing")== "Nursing"
    assert parse_indeed_html.guess_degree_major("Associate in Applied Science in Nursing ")== "Nursing"#custom
    assert parse_indeed_html.guess_degree_major("Associates in Science & Registered Nurse Education") == "Education"
    assert parse_indeed_html.guess_degree_major("in Nursing")=="Nursing"
    print ("Major type successful")

