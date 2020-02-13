
#!/bin/bash

# usage: ./parse_indeed.sh resumes/premium1.html

python3 - <<EOF
import django
django.setup()

import sys
import json
from bakround_applicant.scraping.indeed_html_parser.parser import parse_indeed_html

file_path  = "$1"
with open(file_path, encoding="utf8") as file:
	data = file.read()
	results = parse_indeed_html(data)
	print(json.dumps(results, sort_keys=True,indent=4, separators=(',', ': ')))

EOF
