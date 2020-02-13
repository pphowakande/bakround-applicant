__author__ = "natesymer"

import sys
from django.db import connection

def find_levenshtein(model_cls, attr, value, max_distance=5, field="id"):
    exact = model_cls.objects.filter(**({attr: value})).order_by('id').values_list(field, flat=True).first()
    if exact:
        return exact

    if max_distance <= 0:
        return None

    if len(value) > 255 or len(value) <= max_distance:
        return None

    query = """
SELECT
  {},
  levenshtein(lower({}::text), lower(%s::text)) as distance
FROM {}
WHERE length({}) <= 255
ORDER BY distance ASC LIMIT 1
    """.format(field, attr, model_cls._meta.db_table, attr)

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (value, ))
        
            for (ID, distance) in cursor:
                if distance <= max_distance:
                    return ID
                return None
    except:
        print("find_levenshtein(): failed to calculate, returning None.", sys.exc_info())
        return None

