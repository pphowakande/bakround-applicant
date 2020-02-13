__author__ = "poonam"

from bakround_applicant.all_models.dto import ProfileData,IcimsEmail,IcimsPhone,IcimsJob, ProfileDataSchema, Certification, Education, Experience
from bakround_applicant.ranking.icims import get_score
from ...browser import BrowserFatalError
from ...browser_action import BrowserAction

class ScrapeIcimsData(BrowserAction):
    def go(self,browser):
        self.logger.info("Scraping icims candidate")
        postprocessed = self.postprocess_scrape_results(self.url)
        self.logger.info("Scraped icims candidate at {}".format(self.url))
        if self.on_resume:
            if not self.on_resume(postprocessed, self.url):
                raise BrowserFatalError()

        return (postprocessed, self.url)

    def postprocess_scrape_results(self, url):
        parser_output = get_score.get_people_data(url)

        ## Sanitize the parser output
        profile_data = ProfileData()

        for k, v in parser_output.items():
            if isinstance(v, list) or isinstance(v, dict):
                continue
            setattr(profile_data, k, v)

        # TODO: make these not hardcoded!

        # get icims job data
        icims_job = parser_output.get("icims_job",[])
        profile_data.icims_job = []
        for c in icims_job:
            ic_job = IcimsJob()
            ic_job.value = c.get('value')
            ic_job.id = c.get('id')
            ic_job.job = c.get('job')
            profile_data.icims_job.append(ic_job)

        # get phones data
        icims_phones = parser_output.get('phones',[])
        profile_data.icims_phones = []
        for p in icims_phones:
            phones = IcimsPhone()
            phones.phone_type = p.get('phone_type')
            phones.phone = p.get('phone')
            profile_data.icims_phones.append(phones)

        street_address = parser_output.get('street_address',"")
        profile_data.street_address = street_address

        # get email
        icims_email = parser_output.get('email',"")
        profile_data.icims_email = ""
        emails = IcimsEmail()
        emails.email = icims_email
        profile_data.icims_email = emails

        certifications = parser_output.get('certifications', [])
        profile_data.certifications = []

        for c in certifications:
            certification = Certification()
            certification.certification_name = c.get('certification_name')
            certification.issued_date = c.get('issued_date') # None or "2011-03-01"
            profile_data.certifications.append(certification)

        education = parser_output.get('education', [])
        profile_data.education = []

        for e in education:
            education = Education()
            education.school_name = e.get('school_name')
            education.school_type = e.get('school_type')
            education.city_name = e.get('city_name')
            education.state_code = e.get('state_code')
            education.country_code = e.get('country_code')
            education.degree_name = e.get('degree_name')
            education.degree_date = e.get('degree_date')
            education.degree_major = e.get('degree_major')
            education.degree_type = e.get('degree_type')
            education.start_date = e.get('start_date')
            education.end_date = e.get('end_date')
            profile_data.education.append(education)

        experience = parser_output.get('experience', [])
        profile_data.experience = []

        for e in experience:
            experience = Experience()
            experience.company_name = e.get('company_name')
            experience.job_title = e.get('job_title')
            experience.job_description = e.get('job_description')
            experience.start_date = e.get('start_date')
            experience.end_date = e.get('end_date')
            experience.city_name = e.get('city_name')
            experience.state_code = e.get('state_code')
            experience.country_code = e.get('country_code')
            experience.is_current_position = e.get('is_current_position')
            profile_data.experience.append(experience)

        try:
            sanitized = ProfileDataSchema().dump(profile_data).data
            # print("sanitized : ", sanitized)
        except e:
            self.fail("Failed to postprocess results from {}:\n{}\n\n{}".format(url, str(e), parser_output))

        return sanitized
