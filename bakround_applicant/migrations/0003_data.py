# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-10 15:20
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations
from bakround_applicant.utilities.migrations import insert_migration_data

JOB_PAIRING_VIEW = """
DROP VIEW IF EXISTS job_pairing_view;
CREATE VIEW job_pairing_view
AS
WITH RECURSIVE job_pairing AS (
    (SELECT DISTINCT id AS ancestor_job_id, id AS descendant_job_id, 0 AS recursion_level
     FROM job)
    UNION
    (SELECT DISTINCT job_pairing.ancestor_job_id, job.id, job_pairing.recursion_level + 1
     FROM job_pairing INNER JOIN job ON (job.parent_job_id = job_pairing.descendant_job_id)
     WHERE job_pairing.recursion_level < 3)
)
SELECT distinct ancestor_job_id, descendant_job_id
FROM job_pairing
ORDER BY ancestor_job_id, descendant_job_id;
"""

SEARCH_PROFILE_VIEW = """
DROP MATERIALIZED VIEW IF EXISTS search_profile_view;

-- ORDER MATTERS!
CREATE OR REPLACE FUNCTION get_profile_experience_months(r profile_experience)
                           RETURNS float
AS $$
BEGIN
  RETURN
    (CASE WHEN r.start_date IS NOT NULL AND (r.end_date IS NOT NULL OR r.is_current_position)
          THEN EXTRACT(DAYS FROM (COALESCE(r.end_date, now()) - r.start_date)) / 30.0
          ELSE 0.0
          END);
END
$$ LANGUAGE plpgsql;

CREATE MATERIALIZED VIEW search_profile_view
AS
 WITH profile_total_experience AS (
      SELECT profile_1.id AS profile_id,
             sum(get_profile_experience_months(profile_experience.*)) AS total_experience_months
      FROM profile profile_1
           LEFT JOIN profile_experience ON profile_experience.profile_id = profile_1.id
      GROUP BY profile_1.id
    ),
    recent_score AS (
      SELECT DISTINCT ON (score.job_id, profile.id)
          profile.id as profile_id,
          score.job_id AS scored_job_id,
          score.date_created,
          COALESCE(score.date_created, '1970-01-01 00:00:00+00'::timestamp with time zone) AS score_date_non_null,
          score.score_value,
          COALESCE(score.score_value, 0::numeric(20,10)) AS score_value_non_null
      FROM profile
           LEFT JOIN profile_detail ON profile.id = profile_detail.profile_id
           LEFT JOIN score ON score.profile_detail_id = profile_detail.id
      ORDER BY score.job_id, profile.id, profile_detail.id DESC, score.date_created DESC
    )
 SELECT DISTINCT ON (scored_job_id, profile.id)
    recent_score.scored_job_id,
    profile.id,
    profile.first_name,
    profile.middle_name,
    profile.last_name,
    profile.email,
    profile.phone,
    profile.gender,
    profile.city,
    profile.zip_code,
    profile.job_id,
    profile.state_id,
    profile.user_id,
    profile.date_created,
    profile.date_updated,
    profile.street_address,
    profile.linkedin_data,
    profile.last_updated_date,
    profile.queued_for_deletion,
    profile.hide_from_search,
    COALESCE(profile.last_updated_date, '1970-01-01 00:00:00+00'::timestamp with time zone) AS last_updated_date_non_null,
    recent_score.date_created AS score_date,
    COALESCE(recent_score.date_created, '1970-01-01 00:00:00+00'::timestamp with time zone) AS score_date_non_null,
    recent_score.score_value,
    COALESCE(recent_score.score_value, 0::numeric(20,10)) AS score_value_non_null,
    profile_total_experience.total_experience_months,
    lookup_physical_location.latitude,
    lookup_physical_location.longitude
   FROM profile
     LEFT JOIN profile_total_experience ON profile_total_experience.profile_id = profile.id
     LEFT JOIN lookup_physical_location ON profile.city::text = lookup_physical_location.city::text AND
               profile.state_id = lookup_physical_location.state_id
     LEFT JOIN recent_score ON recent_score.profile_id = profile.id
   ORDER BY scored_job_id, profile.id;
"""

# FIXME: this needs to be able to be rolled back
INSERT_DATA = SEARCH_PROFILE_VIEW + """
CREATE UNIQUE INDEX search_profile_view__unique_index ON search_profile_view (scored_job_id, id);
CREATE INDEX search_profile_view__city_index ON search_profile_view (city);
CREATE INDEX search_profile_view__state_index ON search_profile_view (state_id);
CREATE INDEX search_profile_view__latitude_index ON search_profile_view (latitude);
CREATE INDEX search_profile_view__longitude_index ON search_profile_view (longitude);
CREATE INDEX search_profile_view__experience_index ON search_profile_view (total_experience_months);
CREATE INDEX search_profile_view__score_index ON search_profile_view (score_value);
CREATE INDEX search_profile_view__score_not_null_index ON search_profile_view (score_value_non_null);
CREATE INDEX search_profile_view__last_update_index ON search_profile_view (last_updated_date);
CREATE INDEX search_profile_view__last_update_not_null_index ON search_profile_view (last_updated_date_non_null);
CREATE INDEX search_profile_view__job_id ON search_profile_view (job_id);
CREATE INDEX search_profile_view__score_date_non_null_index ON search_profile_view (score_date_non_null);
""".strip()

def update_site_forward(apps, schema_editor):
    """Set site domain and name."""
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={
            'domain': 'bakround.com',
            'name': 'Bakround'
        }
    )


def update_site_backward(apps, schema_editor):
    """Revert site domain and name to default."""
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={
            'domain': 'example.com',
            'name': 'example.com'
        }
    )

class Migration(migrations.Migration):
    dependencies = [
        ('bakround_applicant', '0002_auto_20180707_1351'),
        ('lookup', '0002_data'),
        ('sites', '0002_alter_domain_unique'),
        ('score', '0001_initial'),
        ('onet', '0002_data'),
    ]

    operations = [
        migrations.RunPython(insert_migration_data('bakround_applicant')),
        migrations.RunSQL(INSERT_DATA),
        migrations.RunPython(update_site_forward, update_site_backward),
    ]

