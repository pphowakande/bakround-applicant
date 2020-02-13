#!/usr/bin/env python3

__author__ = "tplick"

import django
django.setup()

import bakround_applicant.scheduler.tasks
import bakround_applicant.scheduler.util

def main():
    bakround_applicant.scheduler.tasks.create_tasks()
    bakround_applicant.scheduler.util.scheduler_loop()

if __name__ == '__main__':
    main()
