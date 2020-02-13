__author__ = 'natesymer'

import sys
import json
from datetime import timedelta
from dateutil import parser

from django.db import connection
from django.utils import timezone

from bakround_applicant.services.queue import QueueNames
from bakround_applicant.services.base import BaseConsumer
from bakround_applicant.services.verifyingservice.util import collect_contact_info_for_profile, add_contact
from bakround_applicant.score.util import queue_request_icims
from bakround_applicant.all_models.dto import ProfileDataSchema
from bakround_applicant.all_models.db import ProfileExperience, ProfileEducation, ProfileSkill, ProfileCertification, \
                                             Skill, Certification, LookupDegreeType, LookupDegreeName, LookupDegreeMajor, \
                                             LookupCountry, LookupState, ProfileResume, Profile, Job, ProfileEmail, \
                                             ProfilePhoneNumber, ScoreRequest, ProfileReverseLookup, ProfileJobMapping
from bakround_applicant.utilities.helpers.datetime import parse_date_as_utc
from bakround_applicant.utilities.helpers.models import find_levenshtein

class Consumer(BaseConsumer):
    service_name = "BUILD_PROFILE_SVC"
    queue_name = QueueNames.build_profile

    def handle_message(self, body):
        message = json.loads(body)

        name_verify = bool(message.get('name_verify'))
        profile_id = int(message.get('profile_id') or 0) or None
        profile_resume_id = int(message.get('profile_resume_id') or 0) or None
        profile_rl_id = int(message.get('profile_reverse_lookup_id') or 0) or None

        source = message.get('source')
        if not profile_id:
            raise ValueError("Missing profile id")

        # (re)build this profile:
        profile = Profile.objects.get(id=profile_id)

        # Using:

        if profile_resume_id: # a specific resume
            profile_resume = ProfileResume.objects.get(profile_id=profile_id, id=profile_resume_id)
        else: # the most recent resume
            profile_resume = ProfileResume.objects.filter(profile_id=profile_id).order_by('-id').first()

        if profile_rl_id: # a specific profile reverse lookup
            prv = ProfileReverseLookup.objects.get(profile_id=profile_id, id=profile_rl_id)
        else: # the most recent profile reverse lookup.
            prv = ProfileReverseLookup.objects.filter(profile_id=profile_id).order_by('-id').first()

        self.logger.info("Building Profile id {}".format(profile.id))

        # Do the deed

        self.clear_records(profile)

        if profile_resume:
            self.logger.info("Loading data from ProfileResume id {}...".format(profile_resume.id))
            self.build_profile_from_resume(profile, self.load_resume_data(profile_resume), name_verify)

        if prv:
            self.logger.info("Loading data from ProfileReverseLookup id {}...".format(prv.id))
            self.build_profile_from_reverse_lookup(profile, prv, name_verify)

        self.ensure_profile_has_location(profile)

        self.logger.info("Built Profile id {}".format(profile.id))

        mappings = list(ProfileJobMapping.objects.filter(profile_id=profile.id))

        if not mappings:
            self.logger.error("Profile id {} is not mapped to a job. Skipping scoring.".format(profile.id))
            return

        jobs_to_score = []
        for mapping in mappings:
            jobs_to_score = list(Job.objects.filter(job_family_id=mapping.job.job_family_id, accuracy__gte=2))
            for job in jobs_to_score:
                score_request = ScoreRequest(profile_id=profile.id, job_id=job.id)
                score_request.save()
                queue_request_icims(score_request, profile.id, source,profile_resume.id)

    def clear_records(self, profile):
        try: ProfileExperience.objects.filter(profile_id=profile.id).delete()
        except: pass
        try: ProfileEducation.objects.filter(profile_id=profile.id).delete()
        except: pass
        try: ProfileSkill.objects.filter(profile_id=profile.id).delete()
        except: pass
        try: ProfileCertification.objects.filter(profile_id=profile.id).delete()
        except: pass

    #
    # Sanity
    #

    def ensure_profile_has_location(self, profile):
        """Having a city and a state is a hard requirement
           for a profile to show up in search."""
        if profile.state_id and profile.city:
            return

        self.logger.warning("Profile id {} does not have a valid location.".format(profile.id))

        # Attempt to load a Profile's location from either:
        # 1. Where they most recently worked
        # 2. Where they most recently studied
        # We load the most recent of each, and find which is the most recent from
        # each category.

        experience = ProfileExperience.objects.filter(profile_id=profile.id, city__isnull=False, state_id__isnull=False).order_by('-date_created').order_by('-start_date').first()
        education = ProfileEducation.objects.filter(profile_id=profile.id, city__isnull=False, state_id__isnull=False).order_by('-date_created').order_by('-start_date').first()

        tups = []

        if experience:
            date = experience.start_date or experience.date_created
            tups.append((date, experience.city, experience.state_id))

        if education:
            date = education.start_date or education.date_created
            tups.append((date, education.city, education.state_id))

        # Remove date/city/state combos that don't have a valid city and state.
        tups = list(filter(lambda x: x[1] and x[1] and x[2], tups))

        # Sort by date descending
        tups.sort(key=lambda x: x[0], reverse=True)

        if len(tups) > 0:
            tup = tups[0]
            profile.state_id = tup[2]
            profile.city = tup[1]
            profile.save()

            self.logger.info("Updated Profile id {}'s location to {}, {}.".format(profile.id, profile.city, profile.state.state_code if profile.state else "NO STATE"))
        else:
            self.logger.info("Unable to find a location in Profile id {}'s experience or education.".format(profile.id))

    #
    # Build Profile's from ProfileReverseLookup's
    #

    def build_profile_from_reverse_lookup(self, profile, reverse_lookup, name_verify):
        pass

    #
    # Build Profile's from ProfileResume's
    #

    def load_resume_data(self, profile_resume):
        # This is to make up for a past bug in the scraper
        # where resume JSON is saved as a JSON string, rather than a JSON object.
        result = None
        if isinstance(profile_resume.parser_output, str):
            result = ProfileDataSchema().loads(profile_resume.parser_output)
        else:
            result = ProfileDataSchema().load(profile_resume.parser_output)

        if result.errors:
            raise Exception('Deserialization error for ProfileResume id {}.'.format(profile_resume.id))

        return result.data

    def build_profile_from_resume(self, profile, profile_data, name_verify):
        self.update_profile_record_from_resume(profile, profile_data, name_verify)
        self.extract_contact_info_from_resume(profile, profile_data)

        self.populate_experience_from_resume(profile, profile_data)
        self.populate_education_from_resume(profile, profile_data)
        self.populate_skills_from_resume(profile, profile_data)
        self.populate_certs_from_resume(profile, profile_data)

    def update_profile_record_from_resume(self, profile, profile_data, name_verify):
        # This is the date the profile was updated in its datasource
        last_updated_date = None
        if profile_data.last_updated_date is not None:
            try: last_updated_date = parser.parse(profile_data.last_updated_date)
            except: pass

        if last_updated_date:
            self.logger.log("Profile id {} was last updated remotely on {}.".format(profile.id, last_updated_date))
            profile.last_updated_date = last_updated_date or timezone.now()

        profile.summary = profile_data.summary or None

        profile.city = profile_data.city or None
        if profile_data.state_code:
            profile.state = LookupState.objects.filter(state_code=profile_data.state_code).first()
            self.logger.info("Set Profile id {}'s state to {}.".format(profile.id, profile.state.state_code))
        else:
            profile.state = None
            self.logger.warning("Profile id {} does not have an explicit location.".format(profile.id))

        if name_verify:
            if profile_data.first_name == profile.first_name or profile_data.last_name == profile.last_name:
                self.logger.info("Profile id {}: Name verification did not find a new name.".format(profile.id))
            else:
                profile.first_name = profile_data.first_name or None
                profile.middle_name = profile_data.middle_name or None
                profile.last_name = profile_data.last_name or None
                profile.name_verification_completed = True
                self.logger.info("Name verified Profile id {}: {} {} {}".format(profile.id, profile.first_name, profile.middle_name, profile.last_name))
        elif not profile.name_verification_completed:
            profile.first_name = profile.first_name or profile_data.first_name or None
            profile.middle_name = profile.middle_name or profile_data.middle_name or None
            profile.last_name = profile.last_name or profile_data.last_name or None

        profile.save()

        self.logger.info("Updated Profile id {}.".format(profile.id))

    def extract_contact_info_from_resume(self, profile, profile_data):
        collect_contact_info_for_profile(profile)

        # Since this will eventually be moved to its own record,
        # it goes here. The way it's handled will ultimately resemble the email
        # phone number fields below.
        profile.street_address = profile.street_address or profile_data.street_address or None

        for value in profile_data.emails:
            add_contact(ProfileEmail, value, profile.id, True)

        for value in profile_data.phones:
            add_contact(ProfilePhoneNumber, value, profile.id, True)

        self.logger.info("Updated contact information for Profile id {}".format(profile.id))

    def get_state(self, state_code_str):
        state_code = (state_code_str or '').strip().upper() or None
        return LookupState.objects.filter(state_code=state_code).values_list('id', flat=True).first()

    def populate_experience_from_resume(self, profile, profile_data):
        self.logger.debug('saving experience...')

        for ex in (profile_data.experience or []):
            try:
                start_date = parse_date_as_utc(ex.start_date)
                end_date = parse_date_as_utc(ex.end_date)

                if start_date and start_date == end_date:
                    end_date = start_date + timedelta(days=30)

                ProfileExperience(profile_id=profile.id,
                                  company_name=ex.company_name,
                                  position_title=ex.job_title,
                                  position_description=ex.job_description,
                                  start_date=start_date,
                                  end_date=end_date,
                                  city=ex.city_name,
                                  state_id=self.get_state(ex.state_code),
                                  is_current_position=ex.is_current_position).save()
            except:
                self.logger.error("Failed to save experience.", exc_info=True)

    def populate_education_from_resume(self, profile, profile_data):
        self.logger.debug('saving education...')

        for education in (profile_data.education or []):
            try:
                if education.degree_name!="":
                    degree_name_id = find_levenshtein(LookupDegreeName, 'degree_name', education.degree_name)

                    # check for a match with the abbreviation if the name doesn't match
                    if not degree_name_id:
                        # TODO: come up with a better levenshtein max distance.
                        degree_name_id = find_levenshtein(LookupDegreeName, 'degree_abbreviation', education.degree_name, max_distance=0)
                else:
                    degree_name_id = ""

                if education.degree_major != "":
                    degree_major_id = find_levenshtein(LookupDegreeMajor, 'degree_major_name', education.degree_major)
                else:
                    degree_major_id = ""

                if education.degree_type != "":
                    degree_type_id = find_levenshtein(LookupDegreeType, 'degree_type_sovren', education.degree_type, max_distance=0)
                else:
                    degree_type_id = ""

                ProfileEducation(profile_id=profile.id,
                                 school_name=education.school_name,
                                 school_type=education.school_type,
                                 degree_name_id=degree_name_id,
                                 degree_name_other=education.degree_name if degree_name_id is None else None,
                                 degree_major_id=degree_major_id,
                                 degree_major_other=education.degree_major if degree_major_id is None else None,
                                 degree_type_id=degree_type_id,
                                 degree_date=parse_date_as_utc(education.degree_date),
                                 city=education.city_name,
                                 state_id=self.get_state(education.state_code)).save()
            except:
                self.logger.error("Failed to save education.", exc_info=True)

    def populate_skills_from_resume(self, profile, profile_data):
        self.logger.debug('saving skills...')

        for skill in (profile_data.skills or []):
            try:
                if skill.skill_name:
                    skill.skill_name = skill.skill_name.upper().strip() # TODO: preprocess this
                    skill_id = find_levenshtein(Skill, 'skill_name', skill.skill_name)

                    if not skill_id:
                        new_skill = Skill(skill_name=skill.skill_name)
                        new_skill.save()
                        skill_id = new_skill.id

                    ProfileSkill(profile_id=profile.id,
                                 skill_id=skill_id,
                                 skill_name=skill.skill_name,
                                 experience_months=skill.experience_months,
                                 last_used_date=parse_date_as_utc(skill.last_used_date)).save()
            except:
                self.logger.error("Failed to save skill", exc_info=True)

    def populate_certs_from_resume(self, profile, profile_data):
        self.logger.debug('saving certifications...')

        for cert in (profile_data.certifications or []):
            try:
                if cert.certification_name:
                    certification_id = find_levenshtein(Certification, 'certification_name', cert.certification_name)

                    if not certification_id:
                        new_certification = Certification(certification_name=cert.certification_name)
                        new_certification.save()
                        certification_id = new_certification.id

                    ProfileCertification(profile_id=profile.id,
                                         certification_id=certification_id,
                                         certification_name=cert.certification_name,
                                         issued_date=parse_date_as_utc(cert.issued_date)).save()
            except:
                self.logger.error("Failed to save certificate.", exc_info=True)
