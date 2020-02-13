# tplick, 26 January 2017
# Walk through all the template files and make sure that the {% static %} tag
#      is never called with an argument beginning with a slash.

import os
import os.path
from django.conf import settings
import re


def test_template_calls_to_static_tag():
    template_directory = os.path.join(str(settings.APPS_DIR), "templates")
    assert os.path.exists(template_directory)

    for (dirpath, dirname, filenames) in os.walk(template_directory):
        for filename in filenames:
            if filename.endswith(".html") or filename.endswith(".txt"):
                assert file_does_not_contain_bad_static_tag(os.path.join(dirpath, filename))


def file_does_not_contain_bad_static_tag(filename):
    pattern = r"""\{%\s*static\s*(|'|")\s*/"""

    with open(filename) as file:
        return re.search(pattern, file.read()) is None
