__author__ = 'ajaynayak'

import re

def get_if_exists(dict_obj, array_of_keys, default_value=None, return_as_list=False):
    if not dict_obj or not array_of_keys or len(array_of_keys) == 0:
        return default_value

    obj = dict_obj
    for i in range(len(array_of_keys)):
        key = array_of_keys[i]
        if isinstance(obj, dict) and key in obj:
            if i == len(array_of_keys) - 1:
                if not return_as_list or isinstance(obj[key], list):
                    return obj[key]
                else:
                    return [obj[key]]
            else:
                obj = obj[key]
        else:
            return default_value

    return default_value


def get_first_matching(dict_obj, lookup_key, lookup_value, return_key, approximate_match=False):
    
    if not dict_obj or lookup_value is None:
        return None

    if approximate_match:
        pattern = re.compile(r'[\s+\.\,\+\-\!\*\<\>\?\@\/\'\"\_\:\#\^\\\|\;\%\$\&]')
        lookup_value = re.sub(pattern, '', lookup_value)
        row = next((row for row in dict_obj
                    if (lookup_key in row and re.sub(pattern, '', row[lookup_key])).lower() == lookup_value.lower()), None)
    else:
        row = next((row for row in dict_obj if (lookup_key in row and row[lookup_key] == lookup_value)), None)

    if row is not None and return_key in row:
        return row[return_key]

    return None
