
#!/bin/bash

# usage: ./parse_indeed.sh resumes/premium1.html

python3 - <<EOF
import django
django.setup()

import sys
import json
from bakround_applicant.ranking.icims.get_score import get_people_data

people_scored = get_people_data()
print(people_scored)


EOF
