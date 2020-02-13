__author__ = "natesymer"

import phonenumbers

def format_phone_number(v, country_code='US', strict=False):
    try:
        return phonenumbers.format_number(phonenumbers.parse(v, country_code), phonenumbers.PhoneNumberFormat.NATIONAL)
    except:
        if strict:
            raise
        else:
            return v

