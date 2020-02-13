
__author__ = "tplick"

import pytest
import json
from bakround_applicant.services.buildprofile.service import BuildProfileService
from bakround_applicant.all_models.db import Profile, ProfileExperience, ProfileEducation, ProfileSkill, \
                                             ProfileCertification, Skill, Certification, ProfileResume
from logging import Logger
from django.db import connection

TEST_DATA = r"""
{
  "experience": [
    {
      "city_name": "Sacramento",
      "end_date": "2017-01-25",
      "state_code": "California",
      "job_description": "Deliver fuel to service stations for regional transporter of petroleum products. Oversee refueling to ensure compliance with\nall regulations governing safe handling of flammable and hazardous materials. Maintain comprehensive delivery records and facilitate management of customer accounts by placing\norders, collecting payments, and providing records of\ntransaction.\n\u2022  Maintained consistent on-time delivery record with 90% of all orders arriving ahead of schedule.\n\u2022 Recognized for outstanding professional achievement,\nearning company's Safe Driving Award for three years\nrunning.",
      "country_code": "US",
      "company_name": "CTD Transportation",
      "job_title": "Driver",
      "start_date": "2010-10-01"
    },
    {
      "city_name": "Sacramento",
      "end_date": "2010-09-30",
      "state_code": "California",
      "job_description": "Ensured timely delivery of sand, gravel, and concrete products to numerous local construction sites. Mixed concrete to customer-\nspecified slump levels and assisted contractors in pouring\nfoundations, footing, and slabs. Provided detailed reports on mechanical and equipment condition / failures to facilitate\nmaintenance.",
      "country_code": "US",
      "company_name": "Rock and Sand, Inc",
      "job_title": "Delivery Driver",
      "start_date": "2006-03-01"
    },
    {
      "city_name": "Modesto",
      "end_date": "2006-02-28",
      "state_code": "California",
      "job_description": "Transported raw timber from harvest sites to processing facilities.\nAssisted logging crew and mill foremen in loading and unloading\ntimber from trailer. Tracked and maintained logs in accordance\nwith Hours-of-Service (HOS) regulations. Reported damaged or malfunctioning equipment to company mechanics.\n\nTraining and",
      "country_code": "US",
      "company_name": "Timber Green, Inc",
      "job_title": "Driver",
      "start_date": "2001-02-01"
    }
  ],
  "skills": [
    {
      "experience_months": 6,
      "skill_name": "CDL",
      "last_used_date": null
    },
    {
      "experience_months": 55,
      "skill_name": "CONCRETE",
      "last_used_date": "2010-09-30"
    },
    {
      "experience_months": 76,
      "skill_name": "CUSTOMER ACCOUNTS",
      "last_used_date": "2017-01-25"
    },
    {
      "experience_months": 76,
      "skill_name": "HAZARDOUS MATERIALS",
      "last_used_date": "2017-01-25"
    },
    {
      "experience_months": 61,
      "skill_name": "LOGGING",
      "last_used_date": "2006-02-28"
    },
    {
      "experience_months": 55,
      "skill_name": "MAINTENANCE",
      "last_used_date": "2010-09-30"
    },
    {
      "experience_months": 6,
      "skill_name": "MUNICIPAL",
      "last_used_date": null
    },
    {
      "experience_months": 6,
      "skill_name": "OPERATIONS",
      "last_used_date": null
    },
    {
      "experience_months": 76,
      "skill_name": "PAYMENTS",
      "last_used_date": "2017-01-25"
    },
    {
      "experience_months": 76,
      "skill_name": "PETROLEUM",
      "last_used_date": "2017-01-25"
    },
    {
      "experience_months": 61,
      "skill_name": "TRAINING",
      "last_used_date": "2006-02-28"
    }
  ],
  "city": "Elk Grove",
  "zip_code": "95624",
  "summary": null,
  "middle_name": null,
  "profile_id": 58,
  "email": "earnesttrucker@myisp.com",
  "phone": "(916) 555-3846",
  "last_name": null,
  "state": "California",
  "education": [
    {
      "city_name": "Sacramento",
      "end_date": null,
      "school_type": "trade",
      "start_date": null,
      "degree_major": null,
      "country_code": "US",
      "school_name": "Truck Driving School",
      "degree_date": null,
      "degree_name": "Certificate of Completion",
      "degree_type": "vocational",
      "state_code": "California"
    }
  ],
  "first_name": null,
  "street_address": "113 Evergreen Terrace",
  "certifications": [
    {
      "issued_date": null,
      "certification_name": "CDL with Class A, T&X Endorsements"
    },
    {
      "issued_date": null,
      "certification_name": "Certificate of Completion"
    }
  ]
}
""".strip()


@pytest.mark.django_db
def test_build_profile():
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch")

    for profile_id in (5, 7): # the important thing here is that the code is ran twice.
        profile_resume = ProfileResume(source="indeed",
                                       parser_output=json.loads(TEST_DATA),
                                       url="http://example.com/resume{}".format(profile_id))
        profile_resume.save()

        json_obj = {"profile_resume_id": profile_resume.id}
        service = BuildProfileService(json_obj)
        service.logger = Logger("test")
        service.process_message()

    # We have created two profiles from the same data.  There should be two copies
    # of each row in the Profile... tables, but only one copy of each in Skill and Certification.

    assert ProfileExperience.objects.count() == 3*2
    assert ProfileEducation.objects.count() == 1*2

    assert Certification.objects.count() == 2
    assert ProfileCertification.objects.count() == 2*2

    assert Skill.objects.count() > 0
    assert ProfileSkill.objects.count() == 2 * Skill.objects.count()
