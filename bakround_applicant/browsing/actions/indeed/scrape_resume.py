__author__ = "natesymer"

from ...browser import BrowserFatalError
from ...browser_action import BrowserAction
from bakround_applicant.scraping.models import ScraperJob, ScraperLogin
from bakround_applicant.all_models.dto import ProfileData, ProfileDataSchema, Certification, Education, Experience
from bakround_applicant.scraping.indeed_html_parser import parser

class ScrapeIndeedResume(BrowserAction):
    # BrowserAction
    url = None

    # CONSTANTS
    content_selector = ".rezemp-ResumeViewPage-content"
    error_selector = ".rezemp-ErrorPage-content"

    def go(self, browser):
        self.logger.info("Scraping {} ({} cookies)".format(self.url, "with" if browser.cookies else "without"))
        browser.href = self.url

        # Ensure we have resume content.
        if not browser.selector(self.content_selector, nothrow=True, wait=10):
            msg = "Unknown Indeed error."
            if not browser.selector(self.error_selector, nothrow=True):
                msg_el = browser.selector("{} p".format(self.error_selector), nothrow=True)
                if msg_el:
                    msg = msg_el.get_attribute("textContent")

            self.logger.error("Failing due to scraping error @ `{}`: {}".format(self.url, msg))
            self.fail(msg)
            return None

        src = None
        body = browser.selector("body", nothrow=True)
        if body:
            src = body.get_attribute('outerHTML')

        if not src:
            self.logger.error("Retrying scrape attempt because no resume content was found. ({})".format(self.url))
            self.restart("No resume content found.")

        postprocessed = self.postprocess_scrape_results(src)

        self.logger.info("Scraped resume at {}".format(self.url))

        if self.on_resume:
            if not self.on_resume(postprocessed, self.url):
                raise BrowserFatalError()

        return (postprocessed, self.url)

    def postprocess_scrape_results(self, src):
        parser_output = parser.parse_indeed_html(src)

        ## Sanitize the parser output

        profile_data = ProfileData()

        for k, v in parser_output.items():
            if isinstance(v, list) or isinstance(v, dict):
                continue
            setattr(profile_data, k, v)

        certifications = parser_output.get('certifications', [])
        profile_data.certifications = []

        # TODO: make these not hardcoded!

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
        except e:
            self.fail("Failed to postprocess results from {}:\n{}\n\n{}".format(url, str(e), parser_output))

        return sanitized
