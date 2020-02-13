__author__ = "tplick"

from django.db import connection

from bakround_applicant.all_models.db import Job
from bakround_applicant.score.util import queue_job_remap

def perform_remap_to_job(job):
    queue_job_remap(job.id)

def perform_remaps_to_all_jobs():
    for job in Job.remap_queryset:
        perform_remap_to_job(job)

REMAP_COUNT_QUERY = """
    SELECT job.id, count(mapping.*)
    FROM profile_job_mapping mapping
    JOIN job ON job.id=mapping.job_id
    GROUP BY job.id
"""

def get_counts():
    counts = {}
    with connection.cursor() as cursor:
        cursor.execute(REMAP_COUNT_QUERY)
        for (job_id, count) in cursor:
            counts[job_id] = count
    return counts

