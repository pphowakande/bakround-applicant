#!/usr/bin/env python3

# usage ./screen_scrape.py <url>

import sys
import time

sys.path.append('/app')

from bakround_applicant.scraping.browser import Browser

b = Browser(resets_ip = False, uses_tor = False)
b.href = sys.argv[1]
time.sleep(3)
print(b.page_source)

print("LOG:")
for e in b.log_entries:
    print(e['message'])

