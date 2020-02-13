
__author__ = "tplick"

import os
import os.path
from django.conf import settings
import re


def test_that_all_static_assets_are_loaded_using_static_tags():
    template_directory = os.path.join(str(settings.APPS_DIR), "templates")
    assert os.path.exists(template_directory)

    for (dirpath, dirname, filenames) in os.walk(template_directory):
        for filename in filenames:
            if filename.endswith(".html") or filename.endswith(".txt"):
                assert file_does_not_contain_static_asset_loaded_without_static_tag(
                                os.path.join(dirpath, filename))


def file_does_not_contain_static_asset_loaded_without_static_tag(filename):
    patterns = [r"""<img[^>]+src\s*=\s*(|'|")/+static/""",
                r"""<script[^>]+src\s*=\s*(|'|")/+static/""",
                r"""<link[^>]+href\s*=\s*(|'|")/+static/"""]

    with open(filename) as file:
        file_contents = file.read()
        return all(re.search(pattern, file_contents) is None
                   for pattern in patterns)
